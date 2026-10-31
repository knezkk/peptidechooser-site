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
        if name != "404.html" and f"<loc>{SITE}{path}</loc>" not in sitemap:
            errs.append(f"{name}: not in sitemap")
        for a in p.links:
            href = a.get("href", "")
            rel = a.get("rel", "")
            if href.startswith("/out/") and "sponsored" not in rel:
                errs.append(f"{name}: /out/ link without rel=sponsored ({href})")
            if href.startswith("http") and SITE not in href and "nofollow" not in rel and "sponsored" not in rel \
                    and "fonts.googleapis" not in href:
                errs.append(f"{name}: external link without rel ({href})")
            if href.startswith("/") and not href.startswith("//") and "#" not in href and not href.startswith("/out/"):
                target = DIST / href.strip("/")
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
                if t not in ("Organization", "WebSite", "BreadcrumbList", "Article"):
                    errs.append(f"{name}: schema type {t} not in the allowed list (6.3)")
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
    return errs


def seller_domains():
    """Every seller domain site.json knows: the sellers' own and the hosts of their product pages."""
    d = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
    hosts = {r.get("domain") for r in d.get("sellers") or []}
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
