import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from ui.download_job_widget import DownloadJobWidget, ElidedLabel


class QueueLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_narrow_queue_progress_does_not_enable_height_for_width(self):
        root = QWidget()
        layout = QVBoxLayout(root)
        data = {"albumData": {"attributes": {"name": "A long album title " * 12, "artistName": "日本語・中文 artist " * 12}}, "tracks": [{}]}
        row = DownloadJobWidget(1, data, root, "ALAC", root)
        layout.addWidget(row)
        root.show()
        try:
            for width in list(range(40, 401, 15)) + list(range(400, 39, -17)):
                root.resize(width, 160)
                text = "Downloading " + str(width) + "% " + "long progress details " * 8
                row.update_progress(text, 50, 50)
                self.app.processEvents()
                self.assertFalse(row.layout().hasHeightForWidth())
                self.assertEqual(row.status_label.toolTip(), text)
        finally:
            root.close()
            root.deleteLater()
            self.app.processEvents()

    def test_elision_preserves_full_plain_text(self):
        full = "<live> 日本語 & 中文 " * 20
        label = ElidedLabel(full)
        label.resize(90, 30)
        label.show()
        try:
            self.app.processEvents()
            self.assertEqual(label.textFormat(), Qt.TextFormat.PlainText)
            self.assertEqual(label.toolTip(), full)
            self.assertNotEqual(label.text(), full)
            self.assertTrue(label.text())
        finally:
            label.close()
            label.deleteLater()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
