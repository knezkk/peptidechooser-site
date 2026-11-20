"""A live clinic comparison the build no longer makes gets a 301 (owner, 20 Nov 2026: Good Life Meds' six comparisons).
Run: python3 tools/test_gone_compare.py"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build as b  # noqa: E402

CLINICS = {"alloy": "alloy", "good-life-meds": "good-life-meds", "mochi-health": "mochi-health"}
BUILT = {"/sellers/alloy/", "/sellers/good-life-meds/", "/sellers/mochi-health/", "/compare/", "/compare/alloy-vs-mochi-health/"}


def moves(live, built=BUILT, compared=("alloy", "mochi-health")):
    return b.gone_compare_moves(set(live), lambda p: p in built, CLINICS, set(compared))


class Gone(unittest.TestCase):
    def test_goes_to_the_side_that_left_every_pair(self):
        self.assertEqual(moves({"/compare/alloy-vs-good-life-meds/", "/compare/good-life-meds-vs-mochi-health/"}),
                         {"/compare/alloy-vs-good-life-meds/": "/sellers/good-life-meds/",
                          "/compare/good-life-meds-vs-mochi-health/": "/sellers/good-life-meds/"})

    def test_a_built_pair_stays(self):
        self.assertEqual(moves({"/compare/alloy-vs-mochi-health/"}), {})

    def test_a_substance_pair_is_left_alone(self):
        self.assertEqual(moves({"/compare/semaglutide-vs-tirzepatide/"}), {})

    def test_no_seller_page_falls_back_to_compare(self):
        self.assertEqual(moves({"/compare/alloy-vs-good-life-meds/"}, BUILT - {"/sellers/good-life-meds/"}),
                         {"/compare/alloy-vs-good-life-meds/": "/compare/"})

    def test_nothing_built_moves_nothing(self):
        self.assertEqual(moves({"/compare/alloy-vs-good-life-meds/"}, set()), {})


if __name__ == "__main__":
    unittest.main()
