"""Per-order plan rows in price tables (queue block 51, 20 Nov 2026; design/pages/seller.md, Per-order plans).
Run: python3 tools/test_order_rows.py"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build as b  # noqa: E402
import check as c  # noqa: E402


def plan(seller, name, price, fee=None, qty="2 vials", days=None, subs=("kpv",)):
    return {"seller_slug": seller, "seller_name": seller.title(), "plan_name": name, "price_per_order": price,
            "fee_per_order": fee, "order_quantity": qty, "order_supply_days": days, "substance_slug": subs[0],
            "substance_slugs": list(subs), "last_seen": "2026-11-20", "product_kind": "compounded", "dosage_form": "capsule"}


class Price(unittest.TestCase):
    def test_plain_order(self):
        self.assertEqual(b.order_price(plan("a", "KPV", 299.99)), '<span class="num">$299.99 per order</span><span class="sub">2 vials</span>')

    def test_fee_joins_the_price_and_supply_shows(self):
        html = b.order_price(plan("a", "BPC", 80, 54, "1 vial (15 mg)", 35))
        self.assertIn("$80 + $54 fee per order", html)
        self.assertIn("1 vial (15 mg),<br>35-day supply", html)

    def test_zero_fee_is_not_said(self):
        self.assertNotIn("fee", b.order_price(plan("a", "MOTS-c", 249, 0)))

    def test_a_long_quantity_breaks_before_its_bracket(self):
        self.assertIn("30 capsules<br>(500 mcg BPC-157 + 500 mcg KPV)", b.order_price(plan("a", "x", 135, 54, "30 capsules (500 mcg BPC-157 + 500 mcg KPV)")))

    def test_never_monthly(self):
        for r in (plan("a", "x", 80, 54, "1 vial", 30), plan("a", "y", 299.99)):
            self.assertIsNone(c.MONTHLY_WORDS.search(b.order_price(r)))


class Rows(unittest.TestCase):
    ROWS = [plan("a", "dear", 299.99), plan("b", "fee", 67.5, 54), plan("a", "cheap", 100)]

    def test_cheapest_order_first_fee_included(self):
        self.assertEqual([r["plan_name"] for r in b.order_sort(self.ROWS)], ["cheap", "fee", "dear"])

    def test_seller_rows_are_its_own(self):
        with mock.patch.object(b, "PER_ORDER_PLANS", self.ROWS):
            self.assertEqual([r["plan_name"] for r in b.seller_order_rows({"seller_slug": "a"})], ["cheap", "dear"])

    def test_a_goal_with_its_own_clinic_plans_gets_none(self):
        with mock.patch.object(b, "PER_ORDER_PLANS", self.ROWS), mock.patch.object(b, "clinic_plans", lambda g: [1]):
            self.assertEqual(b.goal_order_plans({}), [])


class Check(unittest.TestCase):
    TABLE = '<table class="tbl" data-per-order><tbody><tr><td>{}</td></tr></tbody></table>'

    def page(self, cell, head=True):
        return (f'{b.ORDER_H}<div class="tbl-wrap">' if head else '<div class="tbl-wrap">') + self.TABLE.format(cell)

    def test_good_table_passes(self):
        self.assertEqual(c.per_order_errs("p", self.page("$80 + $54 fee per order")), [])

    def test_monthly_word_fails(self):
        self.assertTrue(c.per_order_errs("p", self.page("$80/mo")))
        self.assertTrue(c.per_order_errs("p", self.page("Per month")))

    def test_table_without_heading_fails(self):
        self.assertTrue(c.per_order_errs("p", self.page("$80 per order", head=False)))


if __name__ == "__main__":
    unittest.main()
