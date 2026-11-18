"""Tests for the plan deep links (queue block 44, 18 Nov 2026): paid.deep_links and the checks around it.
Run: python3 tools/test_deep_links.py"""
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import paid  # noqa: E402

AWIN = {"seller_slug": "curex", "out_path": "/out/curex/", "network": "awin",
        "tracking_url": "https://www.awin1.com/cread.php?awinmid=1&awinaffid=2"}
FP = {"seller_slug": "vitals-vault", "out_path": "/out/vitals-vault/", "network": "firstpromoter",
      "tracking_url": "https://vitalsvault.com?fpr=code-1"}
KAT = {"seller_slug": "strut-health", "out_path": "/out/strut-health/", "network": "katalys",
       "tracking_url": "https://track.revoffers.com/aff_c?offer_id=384&aff_id=9"}
CJ = {"seller_slug": "arsynl-rx", "out_path": "/out/arsynl-rx/", "network": "cj",
      "tracking_url": "https://www.anrdoezrs.net/click-1-2"}
REDIRECTS = [AWIN, FP, KAT, CJ]
PROFILES = {"curex": {"paid_url": "/out/curex/", "domain": "getcurex.com"},
            "vitals-vault": {"paid_url": "/out/vitals-vault/", "domain": "vitalsvault.com"},
            "strut-health": {"paid_url": "/out/strut-health/", "domain": "struthealth.com"},
            "arsynl-rx": {"paid_url": "/out/arsynl-rx/", "domain": "arsynl.com"},
            "free": {"domain": "free.com"}}


def plan(seller, slug, url):
    return {"seller_slug": seller, "plan_slug": slug, "pricing_url": url}


class Networks(unittest.TestCase):
    def test_awin_ued(self):
        self.assertEqual(paid.deep_url(AWIN, "https://getcurex.com/cl/glp"),
                         "https://www.awin1.com/cread.php?awinmid=1&awinaffid=2&ued=https%3A%2F%2Fgetcurex.com%2Fcl%2Fglp")

    def test_awin_never_twice(self):
        self.assertIsNone(paid.deep_url({**AWIN, "tracking_url": AWIN["tracking_url"] + "&ued=x"}, "https://getcurex.com/a"))

    def test_firstpromoter_code_on_target(self):
        self.assertEqual(paid.deep_url(FP, "https://www.vitalsvault.com/treatments/care-semaglutide"),
                         "https://www.vitalsvault.com/treatments/care-semaglutide?fpr=code-1")

    def test_firstpromoter_keeps_target_query_and_replaces_fpr(self):
        self.assertEqual(paid.deep_url(FP, "https://vitalsvault.com/t?a=1&fpr=old"), "https://vitalsvault.com/t?a=1&fpr=code-1")

    def test_katalys_only_confirmed_offers(self):
        self.assertIsNone(paid.deep_url(KAT, "https://www.struthealth.com/hair-loss"))
        with mock.patch.dict(paid.KATALYS_DEEP, {"384": "2026-11-18"}):
            self.assertEqual(paid.deep_url(KAT, "https://www.struthealth.com/hair-loss"),
                             KAT["tracking_url"] + "&url=https%3A%2F%2Fwww.struthealth.com%2Fhair-loss")

    def test_cj_none(self):
        self.assertIsNone(paid.deep_url(CJ, "https://arsynl.com/products/x/"))


class Targets(unittest.TestCase):
    def test_own_domain_www_aside(self):
        self.assertTrue(paid.deep_target_ok("https://www.getcurex.com/cl/glp", "getcurex.com"))

    def test_other_domain(self):
        self.assertFalse(paid.deep_target_ok("https://galahealth.co/nad", "galaglp1.com"))
        self.assertFalse(paid.deep_target_ok("https://getcurex.com.evil.com/x", "getcurex.com"))

    def test_home_page_missing_or_http(self):
        self.assertFalse(paid.deep_target_ok("https://www.tryeden.com/", "tryeden.com"))
        self.assertFalse(paid.deep_target_ok("https://tryeden.com", "tryeden.com"))
        self.assertFalse(paid.deep_target_ok(None, "tryeden.com"))
        self.assertFalse(paid.deep_target_ok("http://getcurex.com/cl/glp", "getcurex.com"))


class Links(unittest.TestCase):
    def links(self, plans):
        return paid.deep_links(plans, PROFILES, REDIRECTS)

    def test_one_page_per_seller_and_target(self):
        got = self.links([plan("curex", "a", "https://getcurex.com/cl/glp"), plan("curex", "b", "https://getcurex.com/cl/glp")])
        self.assertEqual(got[("curex", "a")]["out_path"], "/out/curex/cl-glp/")
        self.assertIs(got[("curex", "a")], got[("curex", "b")])

    def test_fallbacks_left_out(self):
        got = self.links([plan("strut-health", "s", "https://www.struthealth.com/hair-loss"),  # offer not confirmed
                          plan("arsynl-rx", "c", "https://arsynl.com/products/x/"),          # CJ
                          plan("curex", "h", "https://getcurex.com/"),                       # home page
                          plan("curex", "o", "https://other.com/cl/glp"),                    # off domain
                          plan("free", "f", "https://free.com/p"),                           # no paid link
                          plan("curex", None, "https://getcurex.com/x")])                    # no plan slug
        self.assertEqual(got, {})

    def test_same_slug_other_target_gets_number(self):
        got = self.links([plan("curex", "a", "https://getcurex.com/cl/glp"), plan("curex", "b", "https://getcurex.com/cl/glp?x=1")])
        self.assertEqual(got[("curex", "b")]["out_path"], "/out/curex/cl-glp-2/")

    def test_page_holds_the_deep_address(self):
        v = self.links([plan("curex", "a", "https://getcurex.com/cl/glp")])[("curex", "a")]
        html = paid.out_page("Curex", v["url"], v["network"])
        self.assertIn('content="0;url=https://www.awin1.com/cread.php?awinmid=1&amp;awinaffid=2&amp;ued=https%3A%2F%2Fgetcurex.com%2Fcl%2Fglp"', html)
        self.assertIn('content="noindex,nofollow"', html)


class Check(unittest.TestCase):
    def test_bad_target_falls_back_and_is_listed(self):
        links = paid.deep_links([plan("curex", "a", "https://getcurex.com/cl/glp"),
                                 plan("vitals-vault", "v", "https://vitalsvault.com/t")], PROFILES, REDIRECTS)
        asked = []
        kept, dropped = paid.checked_deep_links(links, problem=lambda t: asked.append(t) or ("404" if "curex" in t else None), pause=0)
        self.assertEqual(list(kept), [("vitals-vault", "v")])
        self.assertEqual(dropped, [("/out/curex/cl-glp/", "https://getcurex.com/cl/glp", "404")])
        self.assertEqual(len(asked), 2)

    def test_problem_reasons(self):
        class R:
            def __init__(self, url): self.url = url
            def geturl(self): return self.url
            def __enter__(self): return self
            def __exit__(self, *a): return False
        self.assertIsNone(paid.target_problem("https://getcurex.com/cl/glp", lambda req, timeout: R("https://www.getcurex.com/cl/glp")))
        self.assertEqual(paid.target_problem("https://getcurex.com/cl/glp", lambda req, timeout: R("https://other.com/")), "redirects to other.com")

        def gone(req, timeout):
            raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, None)
        self.assertEqual(paid.target_problem("https://getcurex.com/x", gone), "404")

        def slow(req, timeout):
            raise TimeoutError()
        self.assertEqual(paid.target_problem("https://getcurex.com/x", slow), "TimeoutError")


if __name__ == "__main__":
    unittest.main()
