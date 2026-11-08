"""Test the pure MV request helpers without initializing login/config services."""
import ast
from pathlib import Path
import re
import unittest
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import httpx
import m3u8

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "backend/providers/applemusicdecrypt/applemusicdecrypt/mv.py"


class MVAccessKeyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        names = {"_inherit_media_access_key", "_parse_media_playlist", "_find_map_url", "_redact_media_http_error"}
        module = ast.Module(body=[node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names], type_ignores=[])
        scope = dict(urljoin=urljoin, urlsplit=urlsplit, urlunsplit=urlunsplit, parse_qsl=parse_qsl, urlencode=urlencode, re=re, m3u8=m3u8, httpx=httpx)
        exec(compile(module, str(SOURCE), "exec"), scope)
        cls.helpers = scope

    def inherit(self, uri, parent=None):
        return self.helpers["_inherit_media_access_key"](uri, parent or "https://cdn.example.test/path/video.m3u8?accessKey=test%2Bsignature%3D&unused=private")

    def test_relative_segment_inherits_only_media_authorization(self):
        result = self.inherit("chunk.m4s")
        self.assertEqual(result, "https://cdn.example.test/path/chunk.m4s?accessKey=test%2Bsignature%3D")
        self.assertNotIn("unused", result)

    def test_child_query_and_fragment_are_preserved(self):
        self.assertEqual(self.inherit("chunk.m4s?range=1%2F2#part"), "https://cdn.example.test/path/chunk.m4s?range=1%2F2&accessKey=test%2Bsignature%3D#part")

    def test_explicit_child_authorization_wins_including_empty_value(self):
        for value in ("child%2Bkey", ""):
            with self.subTest(value=value):
                self.assertEqual(self.inherit("chunk.m4s?accessKey=" + value), "https://cdn.example.test/path/chunk.m4s?accessKey=" + value)

    def test_authorization_does_not_cross_origin_or_downgrade_https(self):
        for uri in ("https://other.example.test/chunk.m4s", "http://cdn.example.test/chunk.m4s", "https://cdn.example.test:444/chunk.m4s"):
            with self.subTest(uri=uri):
                self.assertEqual(self.inherit(uri), uri)

    def test_unsigned_playlist_stays_unsigned(self):
        self.assertEqual(self.inherit("chunk.m4s", "https://cdn.example.test/path/video.m3u8"), "https://cdn.example.test/path/chunk.m4s")

    def test_playlist_and_init_segment_resolve_authorized_urls(self):
        parent = "https://cdn.example.test/path/video.m3u8?accessKey=parent"
        text = '#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXT-X-MAP:URI="init.mp4"\n#EXTINF:6,\nchunk0.m4s\n#EXTINF:6,\nchunk1.m4s?accessKey=own\n#EXT-X-ENDLIST\n'
        media = self.helpers["_parse_media_playlist"](text, parent)
        self.assertEqual(media.segments[0].absolute_uri, "https://cdn.example.test/path/chunk0.m4s?accessKey=parent")
        self.assertEqual(media.segments[1].absolute_uri, "https://cdn.example.test/path/chunk1.m4s?accessKey=own")
        self.assertEqual(self.helpers["_find_map_url"](text, parent), "https://cdn.example.test/path/init.mp4?accessKey=parent")

    def test_missing_init_is_reported(self):
        with self.assertRaisesRegex(RuntimeError, "no #EXT-X-MAP"):
            self.helpers["_find_map_url"]("#EXTM3U", "https://cdn.example.test/list.m3u8")

    def test_http_error_retains_status_without_disclosing_access_key(self):
        request = httpx.Request("GET", "https://cdn.example.test/segment.m4s?accessKey=private-test-secret")
        response = httpx.Response(403, request=request)
        with self.assertRaises(httpx.HTTPStatusError) as caught:
            response.raise_for_status()
        error = caught.exception
        self.helpers["_redact_media_http_error"](error)
        self.assertNotIn("private-test-secret", str(error))
        self.assertNotIn("private-test-secret", str(error.request.url))
        self.assertEqual(error.response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
