"""Plan names as paid links (queue block 47, 19 Nov 2026): tools/check.py plan_link_errs, README rule 6.
Run: python3 tools/test_plan_links.py"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check  # noqa: E402

BUTTON = ('<span class="pick-act"><a class="btn btn-action btn-sm" href="/out/found/" data-ev="paid_link_click" data-ev-seller="found"'
          ' target="_blank" rel="sponsored noopener">Visit Found</a><span class="paid">Paid link</span></span>')
NAME = ('<a href="/out/found/wegovy/" data-ev="paid_link_click" data-ev-seller="found" data-ev-placement="plan-name"'
        ' target="_blank" rel="sponsored nofollow noopener">Wegovy Pen</a>')


class PlanLinks(unittest.TestCase):
    def test_plan_name_with_the_sellers_labelled_button_passes(self):
        self.assertEqual(check.plan_link_errs("p", BUTTON + NAME), [])

    def test_button_in_a_table_with_the_label_inside_passes(self):
        inside = BUTTON.replace('Visit Found</a><span class="paid">Paid link</span>', 'Visit Found<span class="paid">Paid link</span></a>')
        self.assertEqual(check.plan_link_errs("p", inside + NAME), [])

    def test_plan_name_without_the_sellers_button_fails(self):
        self.assertTrue(check.plan_link_errs("p", NAME))
        self.assertTrue(check.plan_link_errs("p", BUTTON.replace('"found"', '"other"') + NAME))

    def test_other_text_link_fails(self):
        self.assertTrue(check.plan_link_errs("p", BUTTON + NAME.replace("plan-name", "seller page")))

    def test_rel_icon_and_label(self):
        self.assertTrue(check.plan_link_errs("p", BUTTON + NAME.replace("sponsored nofollow noopener", "sponsored noopener")))
        self.assertTrue(check.plan_link_errs("p", BUTTON + NAME.replace("Wegovy Pen", '<svg></svg>Wegovy Pen')))
        self.assertTrue(check.plan_link_errs("p", BUTTON + NAME.replace("Wegovy Pen", "Wegovy Pen Paid link")))

    def test_buttons_are_not_text_links(self):
        self.assertEqual(check.plan_link_errs("p", BUTTON), [])


if __name__ == "__main__":
    unittest.main()
