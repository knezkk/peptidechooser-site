"""A live page the sitemap leaves out (a noindex,follow comparison, queue block 60) still counts as live, from the live
/pages.json (LIVE_PAGES), so its comparison pair stays in the build (23 Nov 2026). Run: python3 tools/test_published.py"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build as b  # noqa: E402


class Published(unittest.TestCase):
    def test_live_pages_file(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "live-pages.json"
            f.write_text(json.dumps([{"path": "/compare/a-vs-b/", "title": "A vs B"}, {"path": "/404", "title": "x"}]))
            with mock.patch.dict(os.environ, {"LIVE_PAGES": str(f)}):
                self.assertEqual(b.published_paths(), {"/compare/a-vs-b/"})

    def test_unreadable_file_is_empty(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "live-pages.json"
            f.write_text("<html>")
            with mock.patch.dict(os.environ, {"LIVE_PAGES": str(f)}):
                self.assertEqual(b.published_paths(), set())

    def test_live_paths_include_published(self):
        with mock.patch.object(b, "_PUBLISHED", {"/compare/a-vs-b/"}):
            self.assertIn("/compare/a-vs-b/", b.live_paths())


if __name__ == "__main__":
    unittest.main()
