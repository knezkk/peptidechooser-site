"""Pre-publish checks (rulebook 11.12): words, seo, schema, parts. Run after build.py:
    python3 tools/check.py          # all
    python3 tools/check.py words    # one
Exit code 1 on any failure. A failed check gets fixed; the rule is never lowered.
"""
import json
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


def pages():
    out = {}
    for f in sorted(DIST.rglob("*.html")):
        p = Text()
        p.feed(f.read_text(encoding="utf-8"))
        out[str(f.relative_to(DIST))] = p
    return out


def check_words(P):
    errs = []
    for name, p in P.items():
        text = " ".join(p.parts)
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
            if "btn" in cls and not any(c in cls for c in ("btn-ink", "btn-action", "btn-line", "btn-mark")):
                errs.append(f"{name}: button without a design-book kind ({cls})")
        # The paid button: a live one is an <a> to /out/ with rel=sponsored and "Paid link" right under it; a disabled one
        # (before the affiliate url exists) is a span with aria-disabled, no href or rel, and "No paid link yet" under it.
        for m in re.finditer(r'<(\w+)([^>]*class="btn btn-action[^"]*"[^>]*)>[^<]*</\1>(<span class="paid">([^<]*)</span>)?', html):
            tag, attrs, under = m.group(1), m.group(2), m.group(4)
            if 'aria-disabled="true"' in attrs:
                if tag != "span" or "href=" in attrs or "rel=" in attrs or 'role="button"' not in attrs:
                    errs.append(f"{name}: disabled Visit must be a span role=button without href or rel")
                if under != "No paid link yet":
                    errs.append(f"{name}: disabled Visit without 'No paid link yet' under it")
            else:
                if tag != "a" or 'href="/out/' not in attrs or "sponsored" not in attrs:
                    errs.append(f"{name}: green button not an /out/ link with rel=sponsored")
                if under != "Paid link":
                    errs.append(f"{name}: green button without 'Paid link' under it")
        # The seller window links to no seller (owner, 31 Oct 2026): no <a> to a seller's domain, no Visit inside it.
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
            if len(cells) < 5 or not text[0] or not text[1] or not text[2]:
                errs.append(f"{name}: row {i} without a date, a company or a subject")
            elif not re.search(r'href="https://www\.fda\.gov/[^"]+"[^>]*rel="nofollow"', cells[4]):
                errs.append(f"{name}: row {i} without its nofollow fda.gov letter")
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
        for w in re.findall(r"\b(safe|trusted|best|legit)\b", text, re.I):
            errs.append(f"{name}: seller page says '{w}'")
        if name != "sellers/index.html":
            card = re.search(r'<div class="board check-card".*?<ul class="check-list">(.*?)</ul>', html, re.S)
            if not card or len(re.findall(r'class="chip chip-(?:ok|neutral) mark-(?:yes|no)"', card.group(1))) != 5:
                errs.append(f"{name}: Background check card without its five marks")
            if "Checks are facts we hold about the seller, not a safety or quality grade." not in html:
                errs.append(f"{name}: no note that the checks are facts, not a grade")
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
            if set(e) != {"type", "name", "aliases", "url", "line"} or e.get("type") not in ("Goal", "Peptide", "Seller", "Clinic", "Page") \
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
    # Peptide pages (pages.md, Peptide; owner task 2 Nov 2026): every page opens its short answer with the status and its
    # source link, and no page on the site says a dose (an amount with how often or per what, or "take/inject N").
    for name in P:
        if name.startswith("peptides/") and name != "peptides/index.html":
            html = (DIST / name).read_text(encoding="utf-8")
            if not re.search(r'<p class="intro">[^<]+\. <a href="https?://[^"]+" rel="nofollow">(FDA source|Source)</a>', html):
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
    return errs


def clinic_slugs():
    """The online clinics site.json knows: seller pages with no products (peptide-data decision 26)."""
    d = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
    return {r["seller_slug"] for r in d.get("seller_profiles") or [] if not (r.get("product_count") or 0)}


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

if __name__ == "__main__":
    which = sys.argv[1:] or list(CHECKS)
    P = pages()
    failed = 0
    for k in which:
        errs = CHECKS[k](P)
        print(f"check-{k}: {'ok' if not errs else str(len(errs)) + ' problem(s)'} ({len(P)} pages)")
        for e in errs:
            print("  -", e)
        failed += len(errs)
    sys.exit(1 if failed else 0)
