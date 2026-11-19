"""A closed seller with a successor gets 301s to it; one without keeps its archive page (queue block 46, 19 Nov 2026).
Run: python3 tools/test_successors.py"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build as b  # noqa: E402


class Chains(unittest.TestCase):
    def test_closed_with_successor(self):
        self.assertEqual(b.resolve_successors([("enhance-md", "everprime")]), {"enhance-md": "everprime"})

    def test_closed_without_successor_is_not_moved(self):
        self.assertEqual(b.resolve_successors([("gone-clinic", None), ("x", "")]), {})

    def test_successor_that_is_closed_goes_to_the_last_open_one(self):
        self.assertEqual(b.resolve_successors([("a", "b"), ("b", "c")]), {"a": "c", "b": "c"})

    def test_loop_never_reaches_an_open_seller(self):
        self.assertEqual(b.resolve_successors([("a", "b"), ("b", "a")]), {})
        self.assertEqual(b.resolve_successors([("a", "a")]), {})


class Moves(unittest.TestCase):
    LIVE = {"/sellers/enhance-md/", "/sellers/enhance-md/tirzepatide/", "/sellers/enhance-md/semaglutide/",
            "/compare/alan-meds-vs-enhance-md/", "/compare/enhance-md-vs-zealthy/", "/compare/enhance-md-vs-everprime/",
            "/sellers/everprime/", "/sellers/enhanced-chems/"}
    BUILT = {"/sellers/everprime/", "/sellers/everprime/tirzepatide/", "/compare/alan-meds-vs-everprime/", "/sellers/enhanced-chems/"}

    def moves(self):
        with mock.patch.object(b, "SUCCESSORS", {"enhance-md": "everprime"}):
            return b.successor_moves(self.LIVE, lambda p: p in self.BUILT)

    def test_seller_page_and_offer_twins(self):
        m = self.moves()
        self.assertEqual(m["/sellers/enhance-md/"], "/sellers/everprime/")
        self.assertEqual(m["/sellers/enhance-md/tirzepatide/"], "/sellers/everprime/tirzepatide/")
        self.assertEqual(m["/sellers/enhance-md/semaglutide/"], "/sellers/everprime/")  # no twin built

    def test_compare_twins_in_alphabetical_order(self):
        m = self.moves()
        self.assertEqual(m["/compare/alan-meds-vs-enhance-md/"], "/compare/alan-meds-vs-everprime/")
        self.assertEqual(m["/compare/enhance-md-vs-zealthy/"], "/sellers/everprime/")  # no twin built
        self.assertEqual(m["/compare/enhance-md-vs-everprime/"], "/sellers/everprime/")  # the pair with itself

    def test_other_sellers_untouched(self):
        m = self.moves()
        self.assertNotIn("/sellers/enhanced-chems/", m)
        self.assertNotIn("/sellers/everprime/", m)

    def test_closed_without_successor_keeps_archive(self):
        with mock.patch.object(b, "SUCCESSORS", {}):
            self.assertEqual(b.successor_moves(self.LIVE, lambda p: p in self.BUILT), {})


if __name__ == "__main__":
    unittest.main()
