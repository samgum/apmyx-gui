# Queue layout and music-video request fixes

Queue titles, artist names and status text use single-line elision with full text
available in tooltips. The queue rows no longer depend on height-for-width layout,
avoiding the recursive resize/layout path observed with Qt 6.11. Plain text also
prevents metadata from being interpreted as rich text.

The bundled AppleMusicDecrypt provider now carries an MV playlist's `accessKey`
to its same-origin HTTPS media and initialization requests. Explicit child
authorization is preserved, unrelated query parameters are not copied, and keys
are not sent to a different host, port or HTTP URL. Missing authorization caused
the CDN to reject otherwise valid video fragments with HTTP 403. Signed-query
details are removed from propagated HTTP errors.

Validation includes URL authorization boundary tests, queue resizing/progress
tests and a local native-Windows Qt 6.11.2 stress run. The fixed frozen GUI backend
also completed a 4K MV download, followed by successful full audio/video decoding.
No account credentials, signed URLs, media files or patched executable binaries
are part of these source changes.

Run the regression tests with the project's dependencies installed:

```shell
python -m unittest discover -s tests -p test_mv_access_key.py
python -m unittest discover -s tests -p test_queue_layout.py
```
