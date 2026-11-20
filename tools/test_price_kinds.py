"""Kinds of price shown honestly (queue block 48, 20 Nov 2026; peptide-data spec 0036).
Run: python3 tools/test_price_kinds.py"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build as b  # noqa: E402
import check as c  # noqa: E402


def plan(price, **kw):
    r = {"seller_slug": "a", "plan_slug": "p", "seller_name": "A", "plan_name": "P", "price_monthly": price,
         "price_medicine": price, "membership_fee_monthly": None, "substance_slug": "semaglutide"}
    r.update(kw)
    return r


class Notes(unittest.TestCase):
    def test_intro_names_the_standard_price(self):
        self.assertEqual(b.price_kind_notes(plan(349, price_first_month=199, intro_months=2)), ["$199 first 2 months, then $349/mo"])

    def test_one_month_intro(self):
        self.assertEqual(b.price_kind_notes(plan(349, price_first_month=199)), ["$199 first month, then $349/mo"])

    def test_an_ended_intro_is_not_shown(self):
        self.assertEqual(b.price_kind_notes(plan(349, price_first_month=199, intro_ends_on="2020-01-01")), [])

    def test_sale_with_and_without_end(self):
        self.assertEqual(b.price_kind_notes(plan(299, promo_price=69)), ["$69 sale, then $299/mo"])
        self.assertEqual(b.price_kind_notes(plan(299, promo_price=69, promo_ends_on="2099-11-30")),
                         ["$69 sale until Nov 30, 2099, then $299/mo"])

    def test_care_fee_joins_intro_and_sale(self):
        r = plan(424, price_medicine=349, membership_fee_monthly=75, price_first_month=199, promo_price=99)
        self.assertEqual(b.price_kind_notes(r), ["$274 first month, then $424/mo", "$174 sale, then $424/mo"])

    def test_four_weeks_commitment_list_and_membership(self):
        r = plan(161.96, billing_cycle="4_weeks", price_per_cycle=149.5, commitment_months=12, price_basis="list",
                 membership_required=True)
        self.assertEqual(b.price_kind_notes(r), ["billed $149.50 every 4 weeks", "on a 12\u2011month plan", b.LIST_PRICE_NOTE,
                                                 b.MEMBERSHIP_UNKNOWN])

    def test_month_to_month_says_nothing(self):
        self.assertEqual(b.price_kind_notes(plan(99, commitment_months=1, billing_cycle="month", price_basis="clinic")), [])

    def test_care_note_for_a_membership_of_unknown_amount(self):
        self.assertEqual(b.care_note(plan(99, membership_required=True)), b.MEMBERSHIP_UNKNOWN)
        self.assertEqual(b.care_note(plan(99)), "care fee not known")


class Elsewhere(unittest.TestCase):
    def test_reads_the_view_and_the_other_plans_intro(self):
        other = plan(349, seller_slug="nc", plan_slug="w", price_first_month=199, intro_months=2)
        row = {"seller_slug": "a", "plan_slug": "p", "other_seller_slug": "nc", "other_seller_name": "NovoCare",
               "other_plan_slug": "w", "other_comparable_monthly": 349}
        with mock.patch.object(b, "ELSEWHERE", {("a", "p"): row}), mock.patch.object(b, "PLANS", [other]):
            e = b.cheapest_elsewhere(plan(650))
            self.assertEqual((e["seller_slug"], e["price"], e["notes"]), ("nc", 349.0, ["$199 first 2 months, then $349/mo"]))
            self.assertIsNone(b.cheapest_elsewhere(plan(650, plan_slug="q")))


class Check(unittest.TestCase):
    def test_intro_or_sale_alone_fails(self):
        self.assertTrue(c.price_kind_errs("p", "Wegovy Pen $199 first 2 months at NovoCare"))
        self.assertTrue(c.price_kind_errs("p", "SnagRx $69 sale"))

    def test_with_the_standard_price_passes(self):
        self.assertEqual(c.price_kind_errs("p", "$199 first 2 months, then $349/mo and $69 sale until Nov 30, 2026, then $299/mo"), [])
        self.assertEqual(c.price_kind_errs("p", b.first_month_note(plan(349, price_first_month=199))), [])


if __name__ == "__main__":
    unittest.main()
