"""The "Legit?" rating (rating.py; queue block 59, owner decisions 21 Nov 2026), on the five sellers the owner named, with
their checks as the database held them on 22 Nov 2026. Run: python3 tools/test_rating.py"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import rating as R  # noqa: E402

SHOP = [("score_lab_testing", "Lab reports"), ("score_no_fda_letter", "No FDA letter"), ("score_registered_company", "State registry"),
        ("score_legal_pages", "Legal pages"), ("score_fresh_prices", "Fresh prices")]
CLINIC = SHOP[1:]


def prof(lab, letter, registry, legal, fresh, kind="S2_GLP1_TELEHEALTH", last=None):
    return {"score_lab_testing": lab, "score_no_fda_letter": letter, "score_registered_company": registry,
            "score_legal_pages": legal, "score_fresh_prices": fresh, "seller_kind": kind, "last_fda_letter_date": last}


class Rating(unittest.TestCase):
    def test_peptideplugs_research_use_with_five_checks(self):
        x = R.seller_rating(prof(True, True, True, True, True, "S1_RUO"), [], SHOP, True)
        self.assertEqual((x["key"], x["label"]), ("lab", "Lab-use only"))

    def test_dudemeds_registry_never_lowers(self):
        x = R.seller_rating(prof(False, True, False, True, True, "S3_RX_CLINIC_PHARMACY"), [], CLINIC, False)
        self.assertEqual(x["label"], "Legit")
        self.assertEqual(x["notes"], [R.REGISTRY_NOTE])

    def test_direct_meds_open_letter_is_caution(self):
        letters = [{"letter_date": "2025-09-09", "closed_on": None}]
        x = R.seller_rating(prof(False, False, False, True, True, last="2025-09-09"), letters, CLINIC, False)
        self.assertEqual(x["label"], "Caution")
        self.assertIn("FDA letter 2025-09-09, not closed out", x["reason"])

    def test_swiss_chems_letter_still_lab_use_only(self):
        letters = [{"letter_date": "2024-12-10", "closed_on": None}]
        x = R.seller_rating(prof(True, False, False, True, True, "S1_RUO", "2024-12-10"), letters, SHOP, True)
        self.assertEqual(x["label"], "Lab-use only")

    def test_rocky_mountain_compounds_lab_use_only(self):
        x = R.seller_rating(prof(True, True, False, True, True, "S1_RUO"), [], SHOP, True)
        self.assertEqual(x["label"], "Lab-use only")

    def test_closed_out_letter_is_a_gap(self):
        letters = [{"letter_date": "2024-01-02", "closed_on": "2025-03-04"}]
        x = R.seller_rating(prof(False, False, True, True, True), letters, CLINIC, False)
        self.assertEqual(x["label"], "Legit, with gaps")
        self.assertIn("closed out 2025-03-04", x["reason"])

    def test_one_missing_check_is_a_gap_two_are_caution(self):
        self.assertEqual(R.seller_rating(prof(False, True, True, False, True), [], CLINIC, False)["label"], "Legit, with gaps")
        self.assertEqual(R.seller_rating(prof(False, True, True, False, False, "S4_SUPPLEMENT_COSMETIC"), [], SHOP, False)["label"], "Caution")

    def test_fresh_prices_never_counts(self):
        """Owner, 22 Nov 2026 (block 59 fix): fresh prices is our data's freshness, not the seller's."""
        x = R.seller_rating(prof(False, True, True, True, False), [], CLINIC, False)
        self.assertEqual((x["label"], x["reason"]), ("Legit", "Every check we rate on is met."))
        self.assertEqual(R.seller_rating(prof(False, True, True, False, False), [], CLINIC, False)["label"], "Legit, with gaps")

    def test_supplement_shop_lab_reports_count(self):
        x = R.seller_rating(prof(False, True, True, True, True, "S4_SUPPLEMENT_COSMETIC"), [], SHOP, False)
        self.assertEqual((x["label"], x["reason"]), ("Legit, with gaps", "Missing: Lab reports."))


if __name__ == "__main__":
    unittest.main()
