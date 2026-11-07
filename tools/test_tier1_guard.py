#!/usr/bin/env python3
"""What the Tier 1 guard lets through and what it stops. No network; run in the deploy before the guard itself."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tier1_guard as g

FACTS = ('{"seller": "alan meds", "x": "gala health", "y": "zealthy", "b": "scenesse", "n": "semaglutide tirzepatide alpha", "q": "beta vs"}'.lower(),
         {"hair growth", "skin", "weight loss"}, {"Semaglutide", "Tirzepatide", "GLP-1"})


def page(title, description, h1):
    return {"title": title, "description": description, "h1": h1}


ALAN = page("Alan Meds review: plans, prices and checks", "Alan Meds is an online clinic. No FDA warning letter. 2 of 4 checks met on 1 Nov 2026. "
            "Tracked since 3 Oct 2026. Is it legit? See the four checks.", "Alan Meds review")
LIVE = {"/sellers/alan-meds/": ALAN, "/sellers/": page("Sellers", "All sellers.", "Sellers")}
GALA = page("Gala Health review: plans, prices and checks", "Gala Health is an online clinic. No FDA warning letter. 2 of 4 checks met on 5 Nov 2026. "
            "Tracked since 4 Nov 2026. Is it legit? See the four checks.", "Gala Health review")


class Numbers(unittest.TestCase):
    def same(self, old, new):
        return g.only_numbers(page("t", old, "h"), page("t", new, "h"))

    def test_run_42041336893_sellers_count(self):
        self.assertTrue(self.same("The 82 peptide shops and 25 online clinics in our database, each on its own page.",
                                  "The 82 peptide shops and 26 online clinics in our database, each on its own page."))

    def test_run_42041336893_zealthy_letters(self):
        self.assertTrue(self.same("Zealthy is an online clinic. 2 plans from $151/mo, plus $135/mo care. 2 FDA warning letters, the newest 8 Jun 2026.",
                                  "Zealthy is an online clinic. 2 plans from $151/mo, plus $135/mo care. 3 FDA warning letters, the newest 8 Jun 2026."))

    def test_count_with_its_plural(self):
        self.assertTrue(self.same("1 plan from $158/mo. 1 FDA warning letter.", "6 plans from $70/mo. 2 FDA warning letters."))

    def test_date_and_price(self):
        self.assertTrue(self.same("Checked 19 Oct 2026. From $0.13/mg.", "Checked 5 Nov 2026. From $1,299.50/mg."))

    def test_words_stop(self):
        self.assertFalse(self.same("Not approved. Checked 19 Oct 2026.", "FDA approved. Checked 19 Oct 2026."))
        self.assertFalse(self.same("Our pick for hair.", "The best pick for hair."))

    def test_first_letter_is_words(self):
        self.assertFalse(self.same("No FDA warning letter.", "1 FDA warning letter, the newest 9 Sep 2025."))

    def test_number_in_a_name_is_a_word(self):
        self.assertFalse(self.same("Prices for GLP-1.", "Prices for GLP-2."))
        self.assertFalse(self.same("BPC-157 prices.", "BPC-500 prices."))

    def test_plural_alone_is_not_a_number_change(self):
        self.assertFalse(self.same("The plan is listed.", "The plans is listed."))

    def test_a_price_is_not_a_percent(self):
        self.assertFalse(self.same("Costs $99.", "Costs 99%."))

    def test_title_and_h1_count(self):
        self.assertFalse(g.only_numbers(page("Old title", "same 1", "h"), page("New title", "same 2", "h")))


class NewPages(unittest.TestCase):
    def follows(self, path, p, live=LIVE):
        return g.follows_template(path, p, live, FACTS)

    def test_run_42041336893_gala_health(self):
        self.assertTrue(self.follows("/sellers/gala-health/", GALA))

    def test_other_words_in_a_sentence_stop(self):
        p = dict(GALA, description=GALA["description"].replace("See the four checks.", "Our top pick this year."))
        self.assertFalse(self.follows("/sellers/gala-health/", p))

    def test_other_title_stops(self):
        self.assertFalse(self.follows("/sellers/gala-health/", dict(GALA, title="Gala Health review: the best clinic online")))

    def test_h1_outside_the_template_stops(self):
        self.assertFalse(self.follows("/sellers/gala-health/", dict(GALA, h1="Why we love Gala Health")))

    def test_name_not_in_the_url_stops(self):
        self.assertFalse(self.follows("/sellers/some-other-slug/", GALA))

    def test_name_not_in_the_data_stops(self):
        p = {k: v.replace("Gala Health", "Nowhere Clinic") for k, v in GALA.items()}
        self.assertFalse(self.follows("/sellers/nowhere-clinic/", p))

    def test_goal_page_or_guide_never_passes(self):
        live = {"/learn/a/": page("A", "B.", "A"), "/hair/": page("H", "B.", "H")}
        self.assertFalse(self.follows("/menopause/", page("H", "B.", "H"), live))
        self.assertFalse(self.follows("/learn/b/", page("A", "B.", "A"), live))

    def test_no_live_sibling_stops(self):
        self.assertFalse(self.follows("/sellers/gala-health/", GALA, {"/sellers/": LIVE["/sellers/"]}))

    def test_template_comes_from_live_not_from_other_new_pages(self):
        # a live entry of None is a page that is new too: it sets no template
        live = {"/sellers/alan-meds/": None, "/sellers/gala-health/": None}
        self.assertFalse(self.follows("/sellers/gala-health/", GALA, live))

    def test_substance_list_and_slots(self):
        live = {"/peptides/alpha/": page("Alpha: FDA status", "Alpha: FDA approved. On our skin page. Approved brand: Scenesse.", "Alpha")}
        new = page("Semaglutide: FDA status", "Semaglutide: FDA approved. On our hair growth and weight loss pages. Approved brand: Scenesse.", "Semaglutide")
        self.assertTrue(self.follows("/peptides/semaglutide/", new, live))
        bad = dict(new, description="Semaglutide: FDA approved. On our favourite page.")
        self.assertFalse(self.follows("/peptides/semaglutide/", bad, live))


class Redirects(unittest.TestCase):
    def test_redirect_and_plain_page(self):
        with tempfile.TemporaryDirectory() as d:
            old, g.DIST = g.DIST, Path(d)
            try:
                (Path(d) / "a").mkdir()
                (Path(d) / "a" / "index.html").write_text('<meta http-equiv="refresh" content="0; url=/how-we-rate/">')
                (Path(d) / "b").mkdir()
                (Path(d) / "b" / "index.html").write_text("<h1>plain</h1>")
                self.assertEqual(g.redirect_target("/a/"), "/how-we-rate/")
                self.assertIsNone(g.redirect_target("/b/"))
                self.assertIsNone(g.redirect_target("/gone/"))
            finally:
                g.DIST = old


if __name__ == "__main__":
    unittest.main()
