"""Pre-publish checks (rulebook 11.12): words, seo, schema, parts. Run after build.py:
    python3 tools/check.py          # all
    python3 tools/check.py words    # one
Exit code 1 on any failure. A failed check gets fixed; the rule is never lowered.
"""
import collections
import json
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
SITE = "https://peptidechooser.com"

BANNED_WORDS = [
    r"\bcures?\b", r"\bguaranteed\b", r"\bmiracle\b", r"\bbreakthrough\b", r"#1\b", r"\bworld'?s first\b",
    r"\brevolutionary\b", r"\bclinically proven\b", r"\bdoctor[- ]approved\b", r"\brisk[- ]free\b",
    r"\bunlock\b", r"\bsupercharge\b", r"\bgame[- ]changer\b", r"\bdelve\b", r"\bcrucial\b", r"\bleverage\b",
    r"\bcomprehensive\b", r"\bensure\b", r"\butili[sz]e\b", r"\bin order to\b", r"\baffiliate link\b",
    r"\blegit\b",
    r"\bcoming soon\b",
]
BANNED_CHARS = {"—": "em dash", "–": "en dash"}


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.skip = [], 0
        self.h, self.title, self.meta, self.canonical, self.links, self.og = [], "", {}, "", [], ""
        self.jsonld, self._in_ld, self._in_title, self._in_h, self.styles = [], False, False, None, []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style"):
            self.skip += 1
            if tag == "script" and a.get("type") == "application/ld+json":
                self._in_ld = True
        if tag == "title":
            self._in_title = True
        if tag in ("h1", "h2", "h3", "h4"):
            self._in_h = tag
            self.h.append([tag, ""])
        if tag == "meta":
            if a.get("name") == "description":
                self.meta["description"] = a.get("content", "")
            if a.get("name") == "robots":
                self.meta["robots"] = a.get("content", "")
            if a.get("property") == "og:image":
                self.og = a.get("content", "")
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href", "")
        if tag == "a":
            self.links.append(a)
        if "style" in a:
            self.styles.append(a["style"])

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1
            self._in_ld = False
        if tag == "title":
            self._in_title = False
        if tag in ("h1", "h2", "h3", "h4"):
            self._in_h = None

    def handle_data(self, d):
        if self._in_ld:
            self.jsonld.append(d)
            return
        if self._in_title:
            self.title += d
        if self._in_h:
            self.h[-1][1] += d
        if not self.skip:
            self.parts.append(d)


# The six things a peptide page can carry beyond its status (pages.md, Peptide, Thin pages), as the page shows them.
PEP_SIGNALS = {"goal page": r'id="evidence"', "shop table": r'class="tbl (?:tbl-compact )?tbl-cards tbl-sold">.*?<tbody><tr>',
               "clinic plan": r'class="tbl (?:tbl-compact )?tbl-cards tbl-clinics">.*?<tbody><tr', "FDA letter": r'tbl-pep-letters">.*?<tbody><tr>',
               "guide": r'id="guides-h"', "approved brand": r"<li><span>Approved brands</span>"}
AUTHOR_LINE = re.compile(r'<p class="small meta"><a href="/about/">Peptide Chooser editorial team</a>\. Checked \d{1,2} [A-Z][a-z]{2,8} \d{4}\.</p>')


def page_path(name):
    return "/" if name == "index.html" else "/404" if name == "404.html" else "/" + name.replace("index.html", "")


def pages():
    out = {}
    for f in sorted(DIST.rglob("*.html")):
        if 'http-equiv="refresh"' in f.read_text(encoding="utf-8"):
            continue  # a redirect page (data/redirects.json), checked in check_parts
        p = Text()
        p.feed(f.read_text(encoding="utf-8"))
        out[str(f.relative_to(DIST))] = p
    return out


# The one exception to the banned "legit" (owner decision 2 Nov 2026; pages.md, Rules that apply to every page): on a
# /sellers/<slug>/ page, the H2 "Is <Name> legit? What we can check" and the fixed closing sentence under it.
LEGIT_H2 = re.compile(r"Is [^<>]{1,80} legit\? What we can check")
LEGIT_CLOSE = "These are the facts we hold; we do not call any seller legit or safe, and we never link to the shop."
LEGIT_CLOSE_CLINIC = ("These are the facts we hold; we do not call any seller legit or safe. We do not link to the clinic "
                      "until it has a paid link, and we say so when it does.")


def legit_allowed(name, text, h2s):
    """`text` with the allowed "legit" uses removed: only on a seller page, only the H2s that match exactly, and the
    closing sentence."""
    if not (name.startswith("sellers/") and name != "sellers/index.html"):
        return text
    for h in h2s:
        if LEGIT_H2.fullmatch(h.strip()):
            text = text.replace(h.strip(), " ")
    return text.replace(LEGIT_CLOSE, " ").replace(LEGIT_CLOSE_CLINIC, " ")


def legit_cases():
    """The exception's own test cases, run with every check: allowed in the H2 on a seller page, banned anywhere else."""
    errs = []
    bad = lambda name, text, h2s: bool(re.search(r"\blegit\b", legit_allowed(name, text, h2s), re.I))
    h = "Is Iron Aminos legit? What we can check"
    for name, text, h2s, want in (
            ("sellers/iron-aminos/index.html", f"{h} Met: 192 lab reports.", [h], False),       # the H2 on a seller page
            ("sellers/iron-aminos/index.html", f"x {LEGIT_CLOSE}", [], False),                  # the closing sentence
            ("sellers/iron-aminos/index.html", "Iron Aminos is legit.", [], True),              # a claim in the text
            ("sellers/iron-aminos/index.html", "Is it legit? Yes.", ["Is it legit? Yes."], True),  # another H2 wording
            ("hair/index.html", h, [h], True),                                                  # the H2 off a seller page
            ("sellers/index.html", h, [h], True)):                                              # the sellers index
        if bad(name, text, h2s) != want:
            errs.append(f"legit exception test failed: {name}: {text!r}")
    return errs


def check_words(P):
    errs = legit_cases()
    for name, p in P.items():
        text = legit_allowed(name, " ".join(p.parts), [t for tag, t in p.h if tag == "h2"])
        for pat in BANNED_WORDS:
            for m in re.finditer(pat, text, re.I):
                errs.append(f"{name}: banned word '{m.group(0)}'")
        for ch, label in BANNED_CHARS.items():
            if ch in text:
                errs.append(f"{name}: {label}")
        for m in re.finditer(r"\[[^\]]{1,40}\]", text):
            errs.append(f"{name}: placeholder '{m.group(0)}'")
    return errs


def check_seo(P):
    errs, titles, descs = [], {}, {}
    sitemap = (DIST / "sitemap.xml").read_text()
    for name, p in P.items():
        path = "/" if name == "index.html" else "/" + name.replace("index.html", "")
        if name == "404.html":
            path = "/404"
        h1 = [h for h in p.h if h[0] == "h1"]
        if len(h1) != 1:
            errs.append(f"{name}: {len(h1)} h1")
        level = 1
        for tag, _ in p.h:
            n = int(tag[1])
            if n > level + 1:
                errs.append(f"{name}: heading order jumps to {tag}")
            level = n
        t = p.title.strip()
        if not (20 <= len(t) <= 60):
            errs.append(f"{name}: title length {len(t)} ('{t}')")
        if t in titles:
            errs.append(f"{name}: title duplicates {titles[t]}")
        titles[t] = name
        d = p.meta.get("description", "")
        if not (110 <= len(d) <= 160):
            errs.append(f"{name}: description length {len(d)}")
        if d in descs:
            errs.append(f"{name}: description duplicates {descs[d]}")
        descs[d] = name
        if name != "404.html" and p.canonical != SITE + path:
            errs.append(f"{name}: canonical {p.canonical} != {SITE + path}")
        if not p.og:
            errs.append(f"{name}: no og:image")
        elif not (DIST / p.og.replace(SITE + "/", "")).exists():
            errs.append(f"{name}: og:image file missing {p.og}")
        noindex = "noindex" in p.meta.get("robots", "")
        if name != "404.html" and not noindex and f"<loc>{SITE}{path}</loc>" not in sitemap:
            errs.append(f"{name}: not in sitemap")
        if noindex and f"<loc>{SITE}{path}</loc>" in sitemap:
            errs.append(f"{name}: noindex page in the sitemap")
        for a in p.links:
            href = a.get("href", "")
            rel = a.get("rel", "")
            if href.startswith("/out/") and "sponsored" not in rel:
                errs.append(f"{name}: /out/ link without rel=sponsored ({href})")
            if href.startswith("http") and SITE not in href and "nofollow" not in rel and "sponsored" not in rel \
                    and "fonts.googleapis" not in href:
                errs.append(f"{name}: external link without rel ({href})")
            if href.startswith("/") and not href.startswith("//") and "#" not in href and not href.startswith("/out/"):
                target = DIST / href.split("?")[0].strip("/")  # /compare/?a=... is the /compare/ page
                if not (target / "index.html").exists() and not target.exists():
                    errs.append(f"{name}: internal link to missing page {href}")
    return errs


def check_schema(P):
    errs = []
    for name, p in P.items():
        for block in p.jsonld:
            try:
                data = json.loads(block)
            except json.JSONDecodeError as e:
                errs.append(f"{name}: invalid JSON-LD ({e})")
                continue
            graph = data.get("@graph", [data])
            for node in graph:
                t = node.get("@type")
                if t == "BreadcrumbList":
                    for el in node["itemListElement"]:
                        rel = el["item"].replace(SITE, "")
                        target = DIST / rel.strip("/")
                        if rel != "/" and not (target / "index.html").exists():
                            errs.append(f"{name}: breadcrumb to missing {rel}")
                if t not in ("Organization", "WebSite", "BreadcrumbList", "Article", "ItemList"):
                    errs.append(f"{name}: schema type {t} not in the allowed list (6.3)")
                if t == "Article" and not all(node.get(k) for k in ("headline", "datePublished", "author")):
                    errs.append(f"{name}: Article without headline, datePublished or author")
                if t == "ItemList" and not node.get("itemListElement"):
                    errs.append(f"{name}: ItemList without items")
        # The type each page needs (owner task 2 Nov 2026): Organization on Home, BreadcrumbList on every inner page,
        # Article on every guide, ItemList on /sellers/ and the letters page.
        found = set()
        for block in p.jsonld:
            try:
                data = json.loads(block)
            except json.JSONDecodeError:
                continue
            found |= {n.get("@type") for n in data.get("@graph", [data])}
        need = {"Organization"} if name == "index.html" else set() if name == "404.html" else {"BreadcrumbList"}
        if re.fullmatch(r"learn/[^/]+/index\.html", name):
            need.add("Article")
        if name in ("sellers/index.html", "fda-warning-letters/index.html"):
            need.add("ItemList")
        for t in sorted(need - found):
            errs.append(f"{name}: no {t} JSON-LD")
    return errs


DOSE = re.compile(r"\b\d+(?:\.\d+)?\s?(?:mg|mcg|µg|iu|units?|ml)\b\s*(?:per|a|an|/|every|each|once|twice)\s*"
                  r"(?:day|daily|week|weekly|dose|kg|injection|night|morning)\b|\b(?:take|inject)\s+\d", re.I)


def window_errs(name, html):
    """The seller window rules (owner, 31 Oct 2026): no <a> to a seller's domain, no Visit inside it, no clinic in a
    price window, and no verdict words."""
    errs = []
    for m in re.finditer(r'<dialog class="sellers-dlg"[^>]*>(.*?)</dialog>', html, re.S):
        for href in re.findall(r'<a\b[^>]*href="([^"]*)"', m.group(1)):
            host = re.sub(r"^www\.", "", re.sub(r"^[a-z]+://", "", href).split("/")[0].lower())
            if host and any(host == d or host.endswith("." + d) for d in seller_domains()):
                errs.append(f"{name}: seller window links to a seller ({href})")
        if "btn-action" in m.group(1):
            errs.append(f"{name}: Visit button inside the seller window")
        # A price window lists shops only (pages.md, Rules that apply to every page): no clinic in it.
        for slug in clinic_slugs():
            if f"/sellers/{slug}/" in m.group(1) or f'data-seller="{slug}"' in m.group(1):
                errs.append(f"{name}: clinic {slug} inside a price window")
        # The seller score is facts, never a verdict (owner, 2 Nov 2026): no "safe", "trusted" or "best" in the window.
        for w in re.findall(r"\b(safe|trusted|best)\b", re.sub(r"<[^>]+>", " ", m.group(1)), re.I):
            errs.append(f"{name}: seller window says '{w}'")
    return errs


def check_parts(P):
    errs = []
    css = (ROOT / "assets" / "site.css").read_text()
    for m in re.finditer(r"#[0-9a-fA-F]{3,8}\b", css):
        errs.append(f"site.css: hard-coded colour {m.group(0)}")
    for m in re.finditer(r"font-family\s*:(?!\s*var\()", css):
        errs.append("site.css: font-family not from a token")
    for name, p in P.items():
        for s in p.styles:
            if re.search(r"color|font|background|border-radius", s):
                errs.append(f"{name}: inline style sets look ({s})")
        html = (DIST / name).read_text(encoding="utf-8")
        for m in re.finditer(r'class="([^"]*)"', html):
            cls = m.group(1).split()
            if "btn" in cls and not any(c in cls for c in ("btn-ink", "btn-action", "btn-line", "btn-mark", "btn-wait")):
                errs.append(f"{name}: button without a design-book kind ({cls})")
        # The paid button: an <a> to /out/ with rel=sponsored and "Paid link" right under it. Before a paid link exists
        # there is no green button at all, and no page says "No paid link yet" (Home v2, 3 Nov 2026).
        if "No paid link yet" in html:
            errs.append(f"{name}: says 'No paid link yet'")
        for m in re.finditer(r'<(\w+)([^>]*class="btn btn-action[^"]*"[^>]*)>[^<]*</\1>(<span class="paid">([^<]*)</span>)?', html):
            tag, attrs, under = m.group(1), m.group(2), m.group(4)
            if 'aria-disabled="true"' in attrs:
                errs.append(f"{name}: a disabled green button (use btn-wait to our own page until a paid link exists)")
            else:
                if tag != "a" or 'href="/out/' not in attrs or "sponsored" not in attrs:
                    errs.append(f"{name}: green button not an /out/ link with rel=sponsored")
                if under != "Paid link":
                    errs.append(f"{name}: green button without 'Paid link' under it")
        errs += window_errs(name, html)
    # A clinic page closes its legit list with the clinic sentence, never the shops' "we never link to the shop" (owner
    # UX audit, 3 Nov 2026).
    for slug in clinic_slugs():
        f = DIST / "sellers" / slug / "index.html"
        if f.exists() and "we never link to the shop" in f.read_text(encoding="utf-8"):
            errs.append(f"sellers/{slug}/index.html: clinic page says 'we never link to the shop'")
    # The Legal pages line on a seller page (owner task 3 Nov 2026; pages.md, Seller): only the five states' wordings, in
    # the Background check card (the fact alone) and in the legit list ("<state>: <fact>").
    date = r"(?: \(\d{1,2} [A-Z][a-z]{2} \d{4}\))?"
    could = rf"Could not check: the site (?:blocks our crawler|did not answer){date}\."
    missing = r"Missing: [a-z, ]+ page\."
    legal_ok = re.compile(rf"(?:Met: )?Terms, privacy and refund pages found\.|(?:Not met: )?{missing}|{could}"
                          r"|Terms, privacy and refund pages: not checked yet\.|Not checked yet: Terms, privacy and refund pages\.")
    for name in P:
        if not re.match(r"sellers/[^/]+/index\.html$", name):
            continue
        html = (DIST / name).read_text(encoding="utf-8")
        for m in re.finditer(r'>Legal pages(?:<span class="vh">[^<]*</span>)?</span><span class="check-line">([^<]*)</span>', html):
            if not legal_ok.fullmatch(m.group(1)):
                errs.append(f"{name}: Legal pages line not one of the five states: {m.group(1)!r}")
    # Every footnote on a goal page lands on an entry of that page's Sources list with the same number (owner UX audit A13,
    # 3 Nov 2026: footnotes are numbered per page, 1 to N in the order the page cites them).
    goals = [g["slug"] for g in json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))["goals"] if g.get("page")]
    for slug in goals:
        name = f"{slug}/index.html"
        if name not in P:
            continue
        html = re.sub(r"<dialog.*?</dialog>", "", (DIST / name).read_text(encoding="utf-8"), flags=re.S)
        entries = dict((sid, n) for n, sid in re.findall(r'<li value="(\d+)" id="(src-[^"]+)"', html))
        cited = re.findall(r'<a\b[^>]*href="#(src-[^"]+)"[^>]*>(?:<sup>)?(\d+)(?:</sup>)?</a>', html)
        for sid, n in cited:
            if entries.get(sid) != n:
                errs.append(f"{name}: footnote {n} ({sid}) has no entry {n} in the page's Sources")
        if [int(n) for n in dict.fromkeys(n for _, n in cited)] != list(range(1, len(set(n for _, n in cited)) + 1)):
            errs.append(f"{name}: footnotes not numbered 1 to N in reading order")
    # A status chip is never followed by its own last word ("FDA approved approved"; owner UX audit A23, 3 Nov 2026).
    for name in P:
        for m in re.finditer(r'<span class="chip[^"]*">([^<]+)</span>\s*([A-Za-z]+)', (DIST / name).read_text(encoding="utf-8")):
            if m.group(1).split()[-1].lower() == m.group(2).lower():
                errs.append(f"{name}: chip '{m.group(1)}' followed by '{m.group(2)}'")
    # A trust page's counts are Home's counts (owner UX audit A25, 3 Nov 2026): each "N shops", "N online clinics",
    # "N substances" and "N FDA warning letters" on /about/ equals the number Home's hero gives.
    if "index.html" in P and "about/index.html" in P:
        words = ("shops", "online clinics", "substances", "FDA warning letters")
        grab = lambda t: {w: m.group(1) for w in words for m in [re.search(rf"\b(\d+) {w}\b", t)] if m}
        home = grab(re.sub(r"<[^>]+>", "", (DIST / "index.html").read_text(encoding="utf-8")))
        about = grab(re.sub(r"<[^>]+>", "", (DIST / "about" / "index.html").read_text(encoding="utf-8")))
        for w, n in about.items():
            if w in home and home[w] != n:
                errs.append(f"about/index.html: {n} {w}, Home says {home[w]} (a count must come from the same data)")
    # Substance pages (pages.md, Peptide; owner task 3 Nov 2026): the status line and "Where to get it" (or the cosmetic
    # line) on every one; the first seller shown has the most checks among the page's shops.
    for name in P:
        if not re.match(r"peptides/[^/]+/index\.html$", name):
            continue
        html = (DIST / name).read_text(encoding="utf-8")
        if 'class="pep-status"' not in html:
            errs.append(f"{name}: no status line")
        if "Where to get it" not in html:
            errs.append(f"{name}: no Where to get it block")
        where = re.search(r'<ul class="where-list">(.*?)</ul>', html, re.S)
        table = re.search(r'<table class="tbl[^"]*tbl-sold".*?</table>', html, re.S)
        if where and table:
            first = re.search(r"(\d) of 5 checks", where.group(1))
            best = max((int(n) for n in re.findall(r'<span class="num">(\d)</span> of 5 checks', table.group(0))), default=None)
            if first and best is not None and int(first.group(1)) < best:
                errs.append(f"{name}: the first shop shown has {first.group(1)} of 5 checks, the table's best has {best}")
    # Home's windows load on demand from dist/windows/<key>.json (owner UX audit, 3 Nov 2026): the same rules apply.
    for f in sorted((DIST / "windows").glob("*.json")) if (DIST / "windows").exists() else []:
        errs += window_errs(f"windows/{f.name}", json.loads(f.read_text(encoding="utf-8"))["html"])
    for name, p in P.items():
        html = (DIST / name).read_text(encoding="utf-8")
        # Home's "Prices at N shops" buttons point at a window file that exists
        for src in re.findall(r'data-src="/(windows/[^"]+)"', html):
            if not (DIST / src).exists():
                errs.append(f"{name}: window file {src} missing")
    # The letters page (pages.md, Letters): every row has a date, a company, a subject and its fda.gov letter; the only
    # links leaving the site go to fda.gov, so no seller domain is linked anywhere on the page.
    if "fda-warning-letters/index.html" in P:
        name = "fda-warning-letters/index.html"
        html = (DIST / name).read_text(encoding="utf-8")
        for a in P[name].links:
            href = a.get("href", "")
            host = re.sub(r"^www\.", "", re.sub(r"^[a-z]+://", "", href).split("/")[0].lower()) if href.startswith("http") else ""
            if host and host not in ("fda.gov", "fonts.googleapis.com"):
                errs.append(f"{name}: link leaves for {host}, only fda.gov is allowed ({href})")
            if host and any(host == d or host.endswith("." + d) for d in seller_domains()):
                errs.append(f"{name}: links to a seller ({href})")
        body = re.search(r'<table[^>]*id="letters-table".*?<tbody>(.*?)</tbody>', html, re.S)
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", body.group(1), re.S) if body else []
        if not rows:
            errs.append(f"{name}: no letter rows")
        for i, r in enumerate(rows, 1):
            cells = re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)
            text = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
            if len(cells) < 4 or not text[0] or not text[1] or not text[2]:
                errs.append(f"{name}: row {i} without a date, a company or a subject")
            elif not re.search(r'href="https://www\.fda\.gov/[^"]+"[^>]*rel="nofollow"', cells[-1]):
                errs.append(f"{name}: row {i} without its nofollow fda.gov letter")
        # the subject once and no Office column (owner UX audit A27, 3 Nov 2026)
        if body and ("sub-phone" in body.group(1) or 'class="office"' in body.group(1)):
            errs.append(f"{name}: the subject repeated in the company cell or an Office column")
    # The seller pages (pages.md, Sellers and Seller; owner task 2 Nov 2026): no link to any seller's site; every profile
    # carries the five check marks and the note; the facts are never a verdict.
    for name in (n for n in P if n.startswith("sellers/")):
        html = (DIST / name).read_text(encoding="utf-8")
        for a in P[name].links:
            href = a.get("href", "")
            host = re.sub(r"^www\.", "", re.sub(r"^[a-z]+://", "", href).split("/")[0].lower()) if "://" in href else ""
            if host and any(host == d or host.endswith("." + d) for d in seller_domains()):
                errs.append(f"{name}: links to a seller ({href})")
        main = re.search(r'<main id="main">(.*?)</main>', html, re.S)
        text = re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>", "", main.group(1) if main else "", flags=re.S))
        text = legit_allowed(name, text, [t for tag, t in P[name].h if tag == "h2"])
        for w in re.findall(r"\b(safe|trusted|best|legit)\b", text, re.I):
            errs.append(f"{name}: seller page says '{w}'")
        if name != "sellers/index.html":
            # the seller page in one screen (owner task 3 Nov 2026): the five marks once, in the card, with no date in
            # its rows; the five facts once, in the legit list; H1 "<Name> review" opening the unchanged title; the
            # letters section at #fda-letters
            card = re.search(r'<div class="board check-card".*?<ul class="check-chips">(.*?)</ul>', html, re.S)
            if not card or len(re.findall(r'class="chip chip-(?:ok|neutral) mark-(?:yes|no)"', card.group(1))) != 5:
                errs.append(f"{name}: Background check card without its five marks")
            elif re.search(r"\d{1,2} [A-Z][a-z]{2} \d{4}", re.sub(r"<[^>]+>", " ", card.group(1))):
                errs.append(f"{name}: a date in the Background check card's check rows")
            if len(re.findall(r'class="chip chip-(?:ok|neutral) mark-(?:yes|no)"', main.group(1) if main else "")) != 5:
                errs.append(f"{name}: the check marks appear outside the card")
            legit = re.search(r'<ul class="check-list legit-list">(.*?)</ul>', html, re.S)
            if not legit or len(re.findall(r'<span class="check-key">', legit.group(1))) != 5 \
                    or len(re.findall(r'class="check-line"', html)) != 5:
                errs.append(f"{name}: the five facts not once, in the legit list")
            h1 = [t.strip() for tag, t in P[name].h if tag == "h1"]
            if not h1 or not h1[0].endswith(" review") or not P[name].title.strip().startswith(h1[0][:-7]):
                errs.append(f"{name}: H1 not '<Name> review' or the title does not start with the name ({h1})")
            if 'href="https://www.fda.gov/' in html and "FDA letter</a>" in html and 'id="fda-letters"' not in html:
                errs.append(f"{name}: FDA letters without id=\"fda-letters\"")
            if "Checks are facts we hold about the seller, not a safety or quality grade." not in html:
                errs.append(f"{name}: no note that the checks are facts, not a grade")
        else:
            # Filters on /sellers/ (pages.md, Sellers; owner task 2 Nov 2026): without JavaScript the controls stay hidden
            # and every seller page in the build has its row, none hidden; the script and the filter's options name
            # only sellers and substances that are in the build's rows.
            built = {n.split("/")[1] for n in P if n.startswith("sellers/") and n != "sellers/index.html"}
            trs = re.findall(r"<tr( [^>]*)?><td><a class=\"name\" href=\"/sellers/([^\"/]+)/\"", html)
            if {s for _, s in trs} != built:
                errs.append(f"{name}: the tables do not list every seller page in the build")
            # two tabs, clinics first (owner task w2, 3 Nov 2026): each seller in exactly one table, the clinics table
            # first in the HTML, the lede's counts and the tab labels equal to the rows, no old jargon chip label
            def tbl_rows(tid):
                m = re.search(rf'<table[^>]*id="{tid}".*?<tbody>(.*?)</tbody>', html, re.S)
                return re.findall(r'<tr[^>]*><td><a class="name" href="/sellers/([^"/]+)/"', m.group(1)) if m else []
            cl, sh = tbl_rows("clinics-table"), tbl_rows("sellers-table")
            if len(cl + sh) != len(set(cl + sh)):
                errs.append(f"{name}: a seller has a row in both tables or twice in one")
            if cl and sh and html.index('id="clinics-table"') > html.index('id="sellers-table"'):
                errs.append(f"{name}: the clinics table does not come first")
            lede = re.search(r'<p class="lede">([^<]*)</p>', html)
            want = ([f"{len(cl)} online clinic"] if cl else []) + [f"{len(sh)} research-use shop"]
            if not lede or not all(w in lede.group(1) for w in want):
                errs.append(f"{name}: the lede's counts are not the rows ({len(cl)} clinics, {len(sh)} shops)")
            if cl and sh and (f"Online clinics ({len(cl)})" not in html or f"Research-use shops ({len(sh)})" not in html):
                errs.append(f"{name}: a tab label's count is not its rows")
            for old in ("Lab report in 12 months", "Fresh prices<", "Legal pages <"):
                if old in re.sub(r"<script.*?</script>", "", html, flags=re.S).split('class="year-chips"', 1)[-1].split("</div>", 1)[0]:
                    errs.append(f"{name}: an old jargon chip label ({old.strip('<').strip()})")
            if any(re.search(r"\bhidden\b", a or "") for a, _ in trs):
                errs.append(f"{name}: a seller row is hidden without JavaScript")
            for cls in ("sellers-filter", "sellers-tabs"):
                m = re.search(rf'<div class="[^"]*\b{cls}\b[^"]*"([^>]*)>', html)
                if m and "hidden" not in m.group(1):
                    errs.append(f"{name}: the {cls} block shows without JavaScript")
            subs = {s for a, _ in trs for s in re.findall(r'data-subs="([^"]*)"', a or "")[0:1] for s in s.split()}
            sel = re.search(r'<select class="input" id="sellers-sub">(.*?)</select>', html, re.S)
            for v in re.findall(r'<option value="([^"]+)"', sel.group(1) if sel else ""):
                if v not in subs:
                    errs.append(f"{name}: the substance filter offers {v}, which no row carries")
            for s in re.findall(r"/sellers/([^\"'/#]+)/", "".join(re.findall(r"<script>(.*?)</script>", html, re.S))):
                if s not in built:
                    errs.append(f"{name}: a script names /sellers/{s}/, which is not in the build")
            opts = set(re.findall(r'<option value="([^"]+)"', sel.group(1) if sel else ""))
            for pn in (n for n in P if n.startswith("peptides/")):
                for s in re.findall(r'href="/sellers/#substance=([^"]+)"', (DIST / pn).read_text(encoding="utf-8")):
                    if s not in opts:
                        errs.append(f"{pn}: links to /sellers/#substance={s}, which the sellers filter does not offer")
    # Search and Compare any two (pages.md, Every page, Header, Search; Search; Compare; owner task 2 Nov 2026): the index
    # parses, stays under 150 KB and every entry has its five fields and a page that exists; /search/ is noindex; neither
    # page nor the index links to a seller's site.
    idx_file = DIST / "search-index.json"
    if not idx_file.exists():
        errs.append("search-index.json: missing")
    else:
        if idx_file.stat().st_size > 150_000:
            errs.append(f"search-index.json: {idx_file.stat().st_size} bytes, over 150 KB")
        try:
            idx = json.loads(idx_file.read_text(encoding="utf-8"))
        except ValueError as e:
            errs.append(f"search-index.json: does not parse ({e})")
            idx = []
        for e in idx:
            if set(e) != {"type", "name", "aliases", "url", "line"} or e.get("type") not in ("Goal", "Peptide", "Seller", "Clinic", "Comparison", "Guide", "Page") \
                    or not e.get("name") or not e.get("line"):
                errs.append(f"search-index.json: bad entry {e}")
                continue
            url = e["url"].split("#")[0]
            if not url.startswith("/") or not ((DIST / url.strip("/") / "index.html").exists() or url == "/"):
                errs.append(f"search-index.json: {e['name']} points to a missing page {e['url']}")
            if "://" in e["url"]:
                errs.append(f"search-index.json: {e['name']} links off the site")
    if "search/index.html" in P and "noindex" not in P["search/index.html"].meta.get("robots", ""):
        errs.append("search/index.html: not noindex")
    # Peptide pages (pages.md, Peptide; owner task 2 Nov 2026): every page opens with the status and its source link (the
    # status line since the substance page v2, 3 Nov 2026), and no page on the site says a dose (an amount with how often or per what, or "take/inject N").
    for name in P:
        if name.startswith("peptides/") and name != "peptides/index.html":
            html = (DIST / name).read_text(encoding="utf-8")
            if not re.search(r'<p class="pep-status">.*?<a href="https?://[^"]+" rel="nofollow">(FDA source|Source)</a></p>', html):
                errs.append(f"{name}: no status source link in the short answer")
        text = " ".join(P[name].parts)
        m = DOSE.search(text)
        if m:
            errs.append(f"{name}: says a dose ({m.group(0)})")
    # Comparison pages (pages.md, Compare pairs; owner task 2 Nov 2026): both sides link to their page on our site, a
    # substance pair carries each status source, and the sitemap holds every pair once (never b-vs-a beside a-vs-b).
    pairs = [n for n in P if re.fullmatch(r"compare/[a-z0-9-]+-vs-[a-z0-9-]+/index.html", n)]
    for name in pairs:
        html = (DIST / name).read_text(encoding="utf-8")
        heads = re.findall(r'<th scope="col"><a class="name" href="(/(?:peptides|sellers)/[^"/]+/)"', html)
        if len(heads) != 2 or any(f'href="{h}"' not in html.split('id="compare-two"', 1)[-1].split("cmp-link")[0].split("</table>")[-1] for h in heads):
            errs.append(f"{name}: does not link both sides to their pages")
        if all(h.startswith("/peptides/") for h in heads) and len(re.findall(r'rel="nofollow">(?:FDA source|Source)</a>', html)) < 2:
            errs.append(f"{name}: a substance without its status source")
    sm = (DIST / "sitemap.xml").read_text(encoding="utf-8") if (DIST / "sitemap.xml").exists() else ""
    seen = set()
    for loc in re.findall(r"<loc>[^<]*/compare/([a-z0-9-]+)-vs-([a-z0-9-]+)/</loc>", sm):
        key = frozenset(loc)
        if key in seen:
            errs.append(f"sitemap.xml: the pair {loc[0]} and {loc[1]} appears twice")
        seen.add(key)
    for name in ("search/index.html", "compare/index.html", *(n for n in P if n.startswith("peptides/") or n in pairs)):
        if name not in P:
            continue
        html = (DIST / name).read_text(encoding="utf-8")
        for href in [a.get("href", "") for a in P[name].links] + re.findall(r'href=\\?"([^"\\]+)', html):
            host = re.sub(r"^www\.", "", re.sub(r"^[a-z]+://", "", href).split("/")[0].lower()) if "://" in href else ""
            if host and any(host == d or host.endswith("." + d) for d in seller_domains()):
                errs.append(f"{name}: links to a seller ({href})")
    if "compare/index.html" in P:
        html = (DIST / "compare/index.html").read_text(encoding="utf-8")
        # the facts load from /compare/data.json after the page (design/site-polish, 2 Nov 2026)
        src = DIST / "compare" / "data.json"
        try:
            data = json.loads(src.read_text(encoding="utf-8")) if src.exists() else {}
        except ValueError:
            data = {}
            errs.append("compare/data.json: comparison data does not parse")
        if not data:
            errs.append("compare/index.html: no plans or sellers to compare")
        for k, v in data.items():
            if v.get("k") == "seller" and f'href="/sellers/{k[2:]}/"' not in v.get("h", ""):
                errs.append(f"compare/index.html: seller {k} does not link to its page")
    # Thin pages (pages.md, Peptide; owner task 2 Nov 2026): a /peptides/<slug>/ page is indexed only when it shows at
    # least three of the six, each read off the page as built; otherwise it is noindex (and so out of the sitemap).
    for name in P:
        if name.startswith("peptides/") and name != "peptides/index.html":
            html = (DIST / name).read_text(encoding="utf-8")
            has = [k for k, pat in PEP_SIGNALS.items() if re.search(pat, html, re.S)]
            noindex = "noindex" in P[name].meta.get("robots", "")
            if len(has) >= 3 and noindex:
                errs.append(f"{name}: noindex but shows {len(has)} of the six ({', '.join(has)})")
            if len(has) < 3 and not noindex:
                errs.append(f"{name}: thin ({', '.join(has) or 'status only'}) but indexed")
    # Orphans (pages.md, Rules that apply to every page): every page in the sitemap is linked from another page of the
    # build (not the sitemap or llms.txt, which are not pages).
    sm = (DIST / "sitemap.xml").read_text(encoding="utf-8") if (DIST / "sitemap.xml").exists() else ""
    linked = set()
    for name, p in P.items():
        own = page_path(name)
        for a in p.links:
            h = re.sub(r"[?#].*", "", a.get("href", "").replace(SITE, ""))
            if h.startswith("/") and h != own:
                linked.add(h)
    for loc in re.findall(rf"<loc>{re.escape(SITE)}([^<]*)</loc>", sm):
        if loc != "/" and loc not in linked:
            errs.append(f"sitemap.xml: {loc} is linked from no other page")
    # The author line (pages.md, Rules that apply to every page): every goal, seller, peptide, compare, guide and letters
    # page carries the one line "<team>. Checked <date>." with the same class, exactly once.
    goals = {f'{g["slug"]}/index.html' for g in json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))["goals"] if g.get("page")}
    for name in P:
        inner = (name in goals or name == "fda-warning-letters/index.html"
                 or re.match(r"(sellers|peptides|compare|learn)/[^/]+/index\.html$", name))
        if inner:
            n = len(AUTHOR_LINE.findall((DIST / name).read_text(encoding="utf-8")))
            if n != 1:
                errs.append(f"{name}: {n} author lines (want one: '<team>. Checked <date>.' in p.small.meta)")
    # Home v2 (pages.md, Home; owner task 3 Nov 2026): each section under the hero ends with its one action (at most one
    # btn-ink and one btn-line outside its tables: the letters section's pair is the most); the page stays under 60 KB
    # (the price windows load on demand); "we do not link" is said once, in the label legend.
    if "index.html" in P:
        home = (DIST / "index.html").read_text(encoding="utf-8")
        for m in re.finditer(r'<section class="[^"]*home-sec[^"]*" id="([^"]+)">(.*?)</section>', home, re.S):
            body = re.sub(r"<table.*?</table>", "", m.group(2), flags=re.S)
            for kind in ("btn-ink", "btn-line", "btn-wait", "btn-action"):
                n = len(re.findall(rf'class="btn {kind}\b', body))
                if n > (0 if kind in ("btn-wait", "btn-action") else 1):
                    errs.append(f"index.html: section #{m.group(1)} has {n} {kind} buttons outside its tables")
        # every source link on Home, in the page and in the goal panels it loads, lands on an id on /sources/ (owner answer
        # Q3 a, 3 Nov 2026)
        panels = "".join(json.loads(f.read_text(encoding="utf-8"))["html"] for f in sorted((DIST / "windows").glob("goal-*.json")))
        src_page = (DIST / "sources" / "index.html").read_text(encoding="utf-8") if (DIST / "sources" / "index.html").exists() else ""
        for sid in sorted(set(re.findall(r'href="/sources/#([^"]+)"', home + panels))):
            if f'id="{sid}"' not in src_page:
                errs.append(f"index.html: source link /sources/#{sid} lands on no id on /sources/")
        for sid in sorted(set(re.findall(r'href="#(src-[^"]+)"', home + panels))):
            errs.append(f"index.html: source link #{sid} points into Home, which lists no sources")
        size = len(home.encode("utf-8"))
        if size > 60 * 1024:
            errs.append(f"index.html: {size // 1024} KB, over the 60 KB limit")
        text = re.sub(r"<dialog.*?</dialog>|<script.*?</script>|<[^>]+>", " ", home, flags=re.S)
        said = re.findall(r"\b[Ww]e (?:do not|don't|never) link\b", text)
        legend = re.search(r'<dl class="glossary-list">(.*?)</dl>', home, re.S)
        in_legend = len(re.findall(r"\b[Ww]e (?:do not|don't|never) link\b", legend.group(1))) if legend else 0
        if len(said) != 1 or in_legend != 1:
            errs.append(f"index.html: 'we do not link' said {len(said)} times ({in_legend} in the label legend); want once, in the legend")
    # "We do not link" once per page (owner decision C1, 3 Nov 2026; audit C12): the phrase family ("we do not link", "we
    # never link", ...) only where the rules require it: Home's label legend, a seller page's closing sentence under "Is
    # <Name> legit?", and /how-we-rate/ and /disclosure/, where the policy is explained. Text and meta tags of every page
    # and price window count; the count per page is printed; any other occurrence fails.
    nolink = re.compile(r"\b[Ww]e (?:do not|don't|never) link\b")
    texts = [(n, (DIST / n).read_text(encoding="utf-8")) for n in P]
    texts += [(f"windows/{f.name}", json.loads(f.read_text(encoding="utf-8")).get("html", ""))
              for f in sorted((DIST / "windows").glob("*.json"))] if (DIST / "windows").exists() else []
    counts = {}
    for name, html in texts:
        t = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
        said = len(nolink.findall(re.sub(r"<[^>]+>", " ", t))) + sum(len(nolink.findall(c)) for c in re.findall(r'<meta[^>]+content="([^"]*)"', t))
        if not said:
            continue
        counts[name] = said
        if name in ("how-we-rate/index.html", "disclosure/index.html"):
            ok = said
        elif name == "index.html":
            legend = re.search(r'<dl class="glossary-list">(.*?)</dl>', t, re.S)
            ok = min(1, len(nolink.findall(legend.group(1)))) if legend else 0
        elif re.fullmatch(r"sellers/[^/]+/index\.html", name):
            ok = sum(len(nolink.findall(x)) for x in re.findall(r'<p class="small legit-close">(.*?)</p>', t, re.S))
        else:
            ok = 0
        if said > ok:
            errs.append(f"{name}: 'we do not link' said {said} times, {said - ok} outside the allowed places")
    shown = collections.Counter(re.sub(r"^sellers/[^/]+/", "sellers/*/", n) for n in counts)
    print("  we-do-not-link per page: " + (", ".join(f"{n.replace('index.html', '') or '/'} {counts.get(n, '1 each on ' + str(c))}"
                                              for n, c in sorted(shown.items())) or "none"))
    # A footnote right after "(<Seller>)" links that seller's own source: its line in Sources starts with the name (owner
    # UX audit, 3 Nov 2026: /hair/ looked as if Keeps and Strut were swapped), or our own database.
    sellers = seller_names()
    for name in P:
        html = (DIST / name).read_text(encoding="utf-8")
        for m in re.finditer(r'\((?:<a [^>]*>)?([^()<>]{2,80}?)(?:</a>)?\)\.?<sup><a class="ref" href="#(src-[^"]+)"', html):
            who = re.split(r"[,;]", m.group(1))[0].strip()
            li = re.search(rf'<li (?:value="\d+" )?id="{re.escape(m.group(2))}">(.*?)</li>', html, re.S)
            src = re.sub(r"<[^>]+>", "", li.group(1)).strip() if li else ""
            # our own database (the shop prices in a guide) is a source for every shop
            if who in sellers and li and not src.startswith((who, "Peptide Chooser database")):
                errs.append(f"{name}: footnote {m.group(2)} after ({who}) is not that seller's source")
    # Goal pages v2 (pages.md, Category; owner task 3 Nov 2026): the decision cards (at most three, one button each, every
    # number on a card also elsewhere in the page's data), no "Every option, side by side", the clinic table's first row a
    # brand plan when the table has one, and the H1 and title of every goal exactly as data/site.json has them.
    for g in json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))["goals"]:
        name = f'{g["slug"]}/index.html'
        if not g.get("page") or name not in P:
            continue
        html = (DIST / name).read_text(encoding="utf-8")
        if "Every option, side by side" in html:
            errs.append(f"{name}: still has 'Every option, side by side'")
        m = re.search(r'<ul class="decide">(.*?)</ul>', html, re.S)
        if m:
            cards = re.findall(r'<li class="panel-line decide-card">(.*?)</li>(?=<li class="panel-line decide-card">|$)', m.group(1), re.S)
            if len(cards) > 3:
                errs.append(f"{name}: {len(cards)} decision cards (at most three)")
            rest = html.replace(m.group(0), "")
            for c in cards:
                if len(re.findall(r'class="btn ', c)) != 1:
                    errs.append(f"{name}: a decision card without exactly one button")
                for num in set(re.findall(r"\$[\d,]+(?:\.\d+)?", re.sub(r"<[^>]+>", " ", c))):
                    if num not in rest:
                        errs.append(f"{name}: decision card number {num} is nowhere else on the page")
        t = re.search(r'<table class="tbl tbl-compact tbl-cards tbl-clinics">.*?<tbody>(.*?)</tbody>', html, re.S)
        if t and "chip-ok\">Brand<" in t.group(1).replace('"', '\"') and not re.match(r'\s*<tr[^>]*data-k="brand"', t.group(1)):
            errs.append(f"{name}: the clinic table's first row is not a brand plan")
        if P[name].title != g["title"]:
            errs.append(f"{name}: title is not the goal's title in data/site.json")
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
        if not h1 or re.sub(r"<[^>]+>", "", h1.group(1)).strip() != g["h1"]:
            errs.append(f"{name}: H1 is not the goal's h1 in data/site.json")
    # The letters feed (pages.md, Letters): it parses as XML and every item links to the letter on fda.gov.
    feed = DIST / "fda-warning-letters" / "feed.xml"
    if feed.exists():
        import xml.etree.ElementTree as ET
        try:
            items = ET.parse(feed).getroot().findall("./channel/item")
        except ET.ParseError as e:
            errs.append(f"feed.xml: not valid XML ({e})")
            items = []
        if feed.exists() and not items and not any(e.startswith("feed.xml") for e in errs):
            errs.append("feed.xml: no items")
        for it in items:
            link, guid = it.findtext("link") or "", it.findtext("guid") or ""
            if not link.startswith("https://www.fda.gov/") or guid != link or not it.findtext("title") or not it.findtext("pubDate"):
                errs.append(f"feed.xml: item without its fda.gov link, title or date ({link})")
    # Header categories (pages.md, Every page, Header; owner task 3 Nov 2026): a nav link never points at a section of
    # Home or of the page itself, and every one opens a built page (with its #id there, for a link into a page).
    ids = {}
    for name in P:
        html = (DIST / name).read_text(encoding="utf-8")
        m = re.search(r'<nav class="nav" id="site-nav"[^>]*>(.*?)</nav>', html, re.S)
        if not m:
            errs.append(f"{name}: no header nav")
            continue
        for href in re.findall(r'href="([^"]*)"', m.group(1)):
            path, _, frag = href.partition("#")
            if href.startswith(("#", "/#")) or not path.startswith("/"):
                errs.append(f"{name}: nav link {href} is an anchor, not a page")
                continue
            target = path.strip("/") + "/index.html" if path != "/" else "index.html"
            if not (DIST / target).exists():
                errs.append(f"{name}: nav link {href} opens no built page")
            elif frag:
                if target not in ids:
                    ids[target] = set(re.findall(r'\sid="([^"]+)"', (DIST / target).read_text(encoding="utf-8")))
                if frag not in ids[target]:
                    errs.append(f"{name}: nav link {href}: no id {frag} on that page")
    # Header cards (pages.md, Every page, Header; owner task 3 Nov 2026): every panel is a card, never a full-width
    # strip (no container class, no width:100%); the count sentence under "Start here" matches the build.
    sellers = len([d for d in (DIST / "sellers").iterdir() if (d / "index.html").exists()]) if (DIST / "sellers").exists() else 0
    peps = len([d for d in (DIST / "peptides").iterdir() if (d / "index.html").exists()]) if (DIST / "peptides").exists() else 0
    lp = DIST / "fda-warning-letters" / "index.html"
    letters = len(re.findall(r"<tr[ >]", re.search(r'id="letters-table".*?<tbody>(.*?)</tbody>', lp.read_text(encoding="utf-8"), re.S).group(1))) if lp.exists() else 0
    for name in P:
        html = (DIST / name).read_text(encoding="utf-8")
        for m in re.finditer(r'<div class="(nav-panel[^"]*)"[^>]*>(.*?)</div></li>', html, re.S):
            if "nav-card" not in m.group(1).split():
                errs.append(f"{name}: header panel without the card class")
            if re.search(r'class="[^"]*\bwrap\b|width:\s*100%', m.group(0)):
                errs.append(f"{name}: header panel is a full-width strip (container class or width:100%)")
        for cnt in set(re.findall(r'<p class="nav-count">([^<]*)</p>', html)):
            want = {"seller": sellers, "substance": peps, "FDA letter": letters}
            for num, word in re.findall(r"(\d+) (seller|substance|FDA letter)s?\b", cnt):
                if int(num) != want[word]:
                    errs.append(f"{name}: header count '{num} {word}' but the build has {want[word]}")
    # Guides and /learn/ (pages.md, Learn, Guide; owner task w2, 3 Nov 2026): the short answer opens with a sentence
    # under 160 characters; "What to do next" links at least one built page; no /learn/ group is empty; no guide title
    # twice. A redirect page (data/redirects.json) is noindex, carries its canonical and points at a built page.
    titles = {}
    for name in (n for n in P if re.fullmatch(r"learn/[^/]+/index\.html", n)):
        html = (DIST / name).read_text(encoding="utf-8")
        sa = re.search(r'<section class="short-answer".*?<p>(.*?)</p>', html, re.S)
        text = re.sub(r"<[^>]+>", "", re.sub(r"<sup>.*?</sup>", "", sa.group(1))) if sa else ""
        first = re.split(r"(?<=[.?!])\s", text.strip(), 1)[0]
        if not first or len(first) >= 160:
            errs.append(f"{name}: the short answer's first sentence is {len(first)} characters (under 160)")
        nxt = re.search(r"<h2>What to do next</h2>(.*?)(?:<section|</div></article>)", html, re.S)
        hrefs = re.findall(r'href="(/[^"#?]*)', nxt.group(1)) if nxt else []
        if not any((DIST / h.strip("/") / "index.html").exists() or h == "/" for h in hrefs):
            errs.append(f"{name}: 'What to do next' links no built page")
        t = P[name].title.strip()
        if t in titles:
            errs.append(f"{name}: guide title {t!r} also on {titles[t]}")
        titles[t] = name
    if "learn/index.html" in P:
        html = (DIST / "learn" / "index.html").read_text(encoding="utf-8")
        for topic, block in re.findall(r'<h2 class="learn-topic" id="([^"]+)">.*?<ul class="guide-list">(.*?)</ul>', html, re.S):
            if "<li>" not in block:
                errs.append(f"learn/index.html: the {topic} group is empty")
        cards = re.findall(r'<ul class="guide-list">.*?</ul>', html, re.S)
        h3 = re.findall(r"<h3><a [^>]*>([^<]+)</a></h3>", "".join(cards))
        for t in {x for x in h3 if h3.count(x) > 1}:
            errs.append(f"learn/index.html: guide {t!r} listed twice")
    for f in sorted(DIST.rglob("*.html")):
        html = f.read_text(encoding="utf-8")
        if 'http-equiv="refresh"' in html:
            m = re.search(r'url=(/[^"]*)"', html)
            if 'content="noindex"' not in html or 'rel="canonical"' not in html or not m or not (DIST / m.group(1).strip("/") / "index.html").exists():
                errs.append(f"{f.relative_to(DIST)}: redirect page without noindex, canonical or a built target")
    # Compare (pages.md, Compare any two, Compare pairs; owner task w2, 3 Nov 2026): a pair page's verdict states two
    # facts or is left out, never one; no "Not shown" row; the tool's pickers offer both sides of every built pair.
    tool = (DIST / "compare" / "index.html").read_text(encoding="utf-8") if (DIST / "compare" / "index.html").exists() else ""
    offered = set(re.findall(r'<option value="([^"]+)"', tool.split('id="cmp-b"')[0])) if tool else set()
    for name in (n for n in P if re.fullmatch(r"compare/[^/]+-vs-[^/]+/index\.html", n)):
        html = (DIST / name).read_text(encoding="utf-8")
        for m in re.finditer(r'class="cmp-verdict"[^>]*data-facts="(\d+)"', html):
            if int(m.group(1)) < 2:
                errs.append(f"{name}: a verdict with {m.group(1)} fact (two or none)")
        if "cmp-verdict" in html and not re.search(r'class="cmp-verdict"[^>]*data-facts="\d+"', html):
            errs.append(f"{name}: a verdict without its fact count")
        if re.search(r"<td>Not shown\b", html):
            errs.append(f"{name}: a 'Not shown' row")
        head = re.search(r"<thead>(.*?)</thead>", html, re.S)
        for kind, slug in re.findall(r'href="/(peptides|sellers)/([^/"]+)/"', head.group(1) if head else ""):
            ok = f"u.{slug}" in offered if kind == "peptides" else any(v.startswith(f"p.{slug}.") for v in offered)
            if tool and not ok:
                errs.append(f"{name}: the tool's pickers do not offer {slug}")
    # /sources/ (pages.md, Sources): every group shown has at least one source
    src = DIST / "sources" / "index.html"
    if src.exists():
        for sec in re.findall(r'<section class="src-group"[^>]*>(.*?)</section>', src.read_text(encoding="utf-8"), re.S):
            if "<li>" not in sec:
                errs.append("sources/index.html: a group with no source")
    return errs


def clinic_slugs():
    """The online clinics site.json knows: seller pages with no products (peptide-data decision 26)."""
    d = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
    return {r["seller_slug"] for r in d.get("seller_profiles") or [] if not (r.get("product_count") or 0)}


def seller_names():
    """Every seller and clinic name site.json knows, as the pages write it (without the company in brackets)."""
    d = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
    rows = (d.get("plans") or []) + (d.get("seller_profiles") or []) + (d.get("sellers") or [])
    return {re.sub(r"\s*\(.*\)", "", r["seller_name"]).strip() for r in rows if r.get("seller_name")}


def seller_domains():
    """Every seller domain site.json knows: the sellers' own and the hosts of their product pages."""
    d = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
    hosts = {r.get("domain") for r in (d.get("sellers") or []) + (d.get("seller_profiles") or [])}
    hosts |= {re.sub(r"^[a-z]+://", "", r.get("product_url") or "").split("/")[0] for r in d.get("products") or []}
    return {re.sub(r"^www\.", "", h.lower()) for h in hosts if h}


def check_data(P):
    # Rulebook 11.8: no number without a date and a source. When the database statuses are in site.json
    # (tools/pull_data.py), every one of them must carry its source link and a date.
    errs = []
    d = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
    for r in d.get("legal_db") or []:
        name = r.get("substance_slug", "?")
        if not r.get("source_url"):
            errs.append(f"legal_db {name} ({r.get('regime')}): no source_url")
        if not (r.get("first_seen_by_us") or r.get("valid_from")):
            errs.append(f"legal_db {name} ({r.get('regime')}): no date")
    if d.get("letters") and not d.get("pulled_at"):
        errs.append("letters without pulled_at: the section's Checked date comes from it")
    for r in d.get("letters") or []:
        if not (r.get("letter_url") or "").startswith("https://www.fda.gov/"):
            errs.append(f"letters {r.get('seller_slug')}: no fda.gov source")
        if not r.get("letter_date") or not r.get("seller_name") or not r.get("letter_subject"):
            errs.append(f"letters {r.get('seller_slug')}: no date, seller name or subject")
    for r in d.get("letters_all") or []:
        if not (r.get("letter_url") or "").startswith("https://www.fda.gov/"):
            errs.append(f"letters_all {r.get('company_name')}: no fda.gov source")
        if not r.get("letter_date") or not r.get("company_name") or not r.get("letter_subject"):
            errs.append(f"letters_all {r.get('letter_url')}: no date, company or subject")
    if d.get("letters_all") and len(d["letters_all"]) != d.get("letters_all_total"):
        errs.append("letters_all_total does not match the rows in letters_all")
    return errs


CHECKS = {"words": check_words, "seo": check_seo, "schema": check_schema, "parts": check_parts, "data": check_data}

# Plan names against their form (owner task w2, 3 Nov 2026): a clinic's own plan name can name another form than the
# plan's `dosage_form` ("Ozempic Pill" for a pen). The site cannot change data, so this only warns, never fails, and the
# data agent fixes the name at the source.
FORM_WORDS = [(r"\b(pill|tablet|oral|capsule)s?\b", {"tablet", "capsule"}),
              (r"\b(pen|kwikpen|injection|injectable|vial)s?\b", {"pen", "injection_vial"}),
              (r"\b(spray|solution|topical|cream|foam)s?\b", {"topical"})]


def plan_form_warnings():
    src = Path(os.environ["SITE_JSON"]) if os.environ.get("SITE_JSON") else ROOT / "data" / "site.json"
    out = []
    for p in json.loads(src.read_text(encoding="utf-8")).get("plans") or []:
        form, name = p.get("dosage_form"), p.get("plan_name") or ""
        if not form:
            continue
        for rx, forms in FORM_WORDS:
            if re.search(rx, name, re.I) and form not in forms:
                out.append(f"{p.get('seller_name')}: plan {name!r} says {re.search(rx, name, re.I).group(0)!r} but its dosage_form is {form!r}")
    return out


if __name__ == "__main__":
    which = sys.argv[1:] or list(CHECKS)
    for w in plan_form_warnings():
        print("  warning (data):", w)
    P = pages()
    failed = 0
    for k in which:
        errs = CHECKS[k](P)
        print(f"check-{k}: {'ok' if not errs else str(len(errs)) + ' problem(s)'} ({len(P)} pages)")
        for e in errs:
            print("  -", e)
        failed += len(errs)
    sys.exit(1 if failed else 0)
