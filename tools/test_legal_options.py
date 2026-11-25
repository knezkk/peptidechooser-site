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


class SameGoal(unittest.TestCase):
    """No row for the substance: the goal's plan, a paid clinic first, then the lowest price (queue block 58)."""
    G = {"name": "Weight loss", "peptides": []}

    def line(self, plans):
        with mock.patch.object(b, "LEGAL_ALTERNATIVES", {}), mock.patch.object(b, "goal_legal_plan", lambda g: plans):
            return b.legal_option_line(ROW, self.G)

    def test_goal_plan(self):
        out = self.line({"seller_slug": "zz-none", "seller_name": "Rx Clinic", "plan_name": "Weekly Shot", "price_monthly": 49})
        self.assertIn("Legal option for weight loss: Weekly Shot from", out)
        self.assertIn("$49/mo", out)
        self.assertNotIn(b.NO_LEGAL_OPTION, out)

    def test_no_goal_plan(self):
        self.assertIn(b.NO_LEGAL_OPTION, self.line(None))

    def test_paid_first(self):
        g = {"slug": "zz", "name": "Zz", "peptides": [], "clinic_plans": None}
        cheap = {"seller_slug": "a", "seller_name": "A", "plan_name": "x", "price_monthly": 10}
        paid = {"seller_slug": "b", "seller_name": "B", "plan_name": "y", "price_monthly": 90}
        with mock.patch.object(b, "clinic_plans", lambda g: [cheap, paid]), mock.patch.object(b, "CLINIC_PROFILES", {"a": {}, "b": {}}), \
                mock.patch.object(b, "has_paid", lambda s: s == "b"):
            self.assertIs(b.goal_legal_plan(g), paid)


class ShopPage(unittest.TestCase):
    """A research-use shop's page: the legal option of its most-listed substance, no button; none: no line (block 59 Q2 B)."""
    SHOP = {"seller_slug": "zz-shop"}
    SUBS = {"zz-shop": [{"seller_slug": "zz-shop", "substance_slug": "ghk-cu", "listing_count": 3},
                        {"seller_slug": "zz-shop", "substance_slug": "bpc-157", "listing_count": 9}]}

    def line(self, rows):
        with mock.patch.object(b, "SELLER_SUBS", self.SUBS), mock.patch.object(b, "LEGAL_ALTERNATIVES", {r["substance_slug"]: r for r in rows}):
            return b.shop_legal_line(self.SHOP)

    def test_most_listed(self):
        out = self.line([alt(), alt(substance_slug="ghk-cu", option_name="GHK-Cu")])
        self.assertIn("Legal option: BPC-157 on prescription at", out)
        self.assertIn(", from <span class=\"num\">$199/mo</span>", out)
        self.assertNotIn("Paid link", out)

    def test_no_button_with_paid_link(self):
        with mock.patch.object(b, "has_paid", lambda s: True):
            self.assertNotIn("btn-action", self.line([alt(has_paid_link=True)]))

    def test_price_from_the_plan_row(self):
        """Block 59 fix (23 Nov 2026): the plan's current price, and its commitment when the "from" rate needs one."""
        plan = {"seller_slug": "zz-none", "plan_slug": "p", "price_monthly": 129.0, "price_standard": 199.0, "lowest_commitment_months": 12}
        with mock.patch.object(b, "PLANS", [plan]):
            out = self.line([alt(lowest_monthly=150)])
        self.assertIn("Legal option: BPC-157 on prescription at", out)
        self.assertIn(", from <span class=\"num\">$129/mo</span> on a 12\u2011month plan (<span class=\"num\">$199/mo</span> month to month)", out)
        with mock.patch.object(b, "PLANS", [dict(plan, price_monthly=160.0, price_standard=None)]):
            out = self.line([alt(lowest_monthly=185)])
        self.assertTrue(out.endswith(", from <span class=\"num\">$160/mo</span>"), out)

    def test_top_substance_without_option_has_no_line(self):
        self.assertEqual(self.line([alt(substance_slug="ghk-cu", option_name="GHK-Cu")]), "")


class Registry(unittest.TestCase):
    """A missed state registry: "Not met · not used in the rating" in the card and on the seller page's Missing line."""
    R = {"seller_slug": "zz-none", "score": 3, "score_lab_testing": True, "score_no_fda_letter": True,
         "score_registered_company": False, "score_legal_pages": True, "score_fresh_prices": True}

    def test_state(self):
        self.assertEqual(b.check_state("score_registered_company", self.R), "Not met \u00b7<br>not used in the rating")
        self.assertEqual(b.check_state("score_legal_pages", dict(self.R, score_legal_pages=False)), "Not met")

    def test_missing_line(self):
        self.assertIn("Missing: State registry \u00b7<br>not used in the rating", b.missing_line(self.R, page=True))
        self.assertNotIn("not used", b.missing_line(self.R))


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
