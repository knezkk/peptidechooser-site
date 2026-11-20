"""Per-order plans in the "<Peptide> on prescription" sentence (queue block 49, 19 Nov 2026; spec 0023).
Run: python3 tools/test_order_plans.py"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build as b  # noqa: E402


def plan(seller, name, price, fee=None, subs=("kpv",), qty="2 vials"):
    return {"seller_slug": seller, "seller_name": seller.title(), "plan_name": name, "price_per_order": price,
            "fee_per_order": fee, "order_quantity": qty, "substance_slug": subs[0], "substance_slugs": list(subs),
            "last_seen": "2026-11-19"}


class OrderPlans(unittest.TestCase):
    ROWS = [plan("a", "KPV", 299.99), plan("b", "KPV caps", 67.5, 54), plan("b", "BPC-157 + KPV", 50, 0, ("bpc-157", "kpv")),
            plan("gone", "KPV", 10)]

    def order_plans(self, group="not"):
        with mock.patch.object(b, "PER_ORDER_PLANS", self.ROWS), \
                mock.patch.object(b, "PROFILES", {"a": {}, "b": {}}), \
                mock.patch.object(b, "pep_group", lambda s: group), mock.patch.object(b, "pep_status", lambda s: {}):
            return b.pep_order_plans("kpv")

    def test_fee_is_in_the_order_price(self):
        self.assertEqual(b.order_cost(self.ROWS[1]), 121.5)
        self.assertEqual(b.order_cost(self.ROWS[0]), 299.99)

    def test_cheapest_first_one_medicine_only_sellers_with_a_page(self):
        self.assertEqual([r["plan_name"] for r in self.order_plans()], ["KPV caps", "KPV"])

    def test_an_approved_drug_gets_none(self):
        self.assertEqual(self.order_plans("approved"), [])

    def test_words_never_monthly(self):
        with mock.patch.object(b, "clinic_link", lambda slug, name, inline=False: name):
            self.assertEqual(b.order_words(self.ROWS[1]), "$121.50 for 2 vials at B, fees included")
            self.assertEqual(b.order_words(self.ROWS[0]), "$299.99 for 2 vials at A")
            self.assertNotIn("/mo", b.order_words(self.ROWS[0]))


if __name__ == "__main__":
    unittest.main()
