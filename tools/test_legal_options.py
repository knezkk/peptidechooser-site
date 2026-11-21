"""The research-use row's legal option and the FDA letter in place of "Missing: No FDA letter" (queue block 56, 20 Nov 2026;
peptide-data spec 0040). Run: python3 tools/test_legal_options.py"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build as b  # noqa: E402

ROW = {"name": "Peptides sold for hair growth", "substances": ["bpc-157", "ghk-cu"]}


def alt(**kw):
    r = {"substance_slug": "bpc-157", "substance_name": "BPC-157", "option_kind": "clinic_plan", "option_name": "Compounded BPC-157",
         "seller_slug": "zz-none", "seller_name": "Rx Clinic", "plan_slug": "p", "lowest_monthly": 199, "has_paid_link": False}
    r.update(kw)
    return r


class Legal(unittest.TestCase):
    def line(self, *rows):
        with mock.patch.object(b, "LEGAL_ALTERNATIVES", {r["substance_slug"]: r for r in rows}):
            return b.legal_option_line(ROW)

    def test_no_row(self):
        self.assertIn(b.NO_LEGAL_OPTION, self.line())

    def test_monthly_plan(self):
        out = self.line(alt())
        self.assertIn("Legal option: Compounded BPC-157 from", out)
        self.assertIn("$199/mo", out)
        self.assertIn("at Rx Clinic", out)
        self.assertNotIn("Paid link", out)

    def test_per_order(self):
        self.assertIn("Legal option: Compounded BPC-157 at Rx Clinic, priced per order", self.line(alt(lowest_monthly=None)))

    def test_approved_drug(self):
        r = alt(substance_slug="ghk-cu", substance_name="GHK-Cu", option_kind="fda_approved_drug", option_name="Brandix",
                seller_slug=None, seller_name=None, lowest_monthly=None)
        self.assertIn("Legal option: Brandix (GHK-Cu), FDA approved, on prescription", self.line(r))

    def test_same_clinic_and_price_on_one_line(self):
        out = self.line(alt(), alt(substance_slug="ghk-cu", option_name="GHK-Cu"))
        self.assertEqual(out.count("Legal option:"), 1)
        self.assertIn("Compounded BPC-157 and GHK-Cu from", out)


class Letter(unittest.TestCase):
    def test_letter_instead_of_missing(self):
        r = {"seller_slug": "zz-none", "score": 3, "score_lab_testing": True, "score_no_fda_letter": False,
             "score_registered_company": True, "score_legal_pages": True, "score_fresh_prices": True,
             "last_fda_letter_date": "2026-02-20"}
        out = b.missing_line(r)
        self.assertIn("FDA letter, Feb 20, 2026", out)
        self.assertNotIn("Missing", out)


if __name__ == "__main__":
    unittest.main()
