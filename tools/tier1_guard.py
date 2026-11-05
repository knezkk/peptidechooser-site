#!/usr/bin/env python3
"""Tier 1 guard (CLAUDE.md rule 2; design/pages/every-page.md, Tier 1 guard; owner answer to #94 Q2, 5 Nov 2026).

Run in the deploy after the last build: every built page's <title>, meta description and first H1 against the same page on
the live site. A difference, a new page or a page that left the build stops the deploy, unless the owner approved exactly that
new text: under a line with the phrase ODOBRENO SEO - Karlo - <date>, in the commit message or in data/tier1-approved.txt, a
line "<path> <hash>" as this script prints it. The hash is of the new text, so an approval covers that text and nothing later.

Live pages, not a committed snapshot: the live site is what readers and Google have, and it cannot drift. A snapshot would need
a deploy that writes back to the repo, and it would be wrong after a failed deploy or a re-run. A page that cannot be read
after three tries stops the deploy too (it says so): the guard never passes on what it did not see.

Usage: python3 tools/tier1_guard.py       TIER1_LIVE=<url> reads another site, for tests.
"""
import hashlib
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
APPROVED = ROOT / "data" / "tier1-approved.txt"
LIVE = os.environ.get("TIER1_LIVE", "https://peptidechooser.com").rstrip("/")
PHRASE = re.compile(r"ODOBRENO SEO(?: and ODOBRENO \w+)? - Karlo - \d{1,2}\.\s?\d{1,2}\.\s?\d{4}")
LINE = re.compile(r"^(/\S*)\s+([0-9a-f]{12})\s*$")
FIELDS = ("title", "description", "h1")
GONE = {"title": "", "description": "", "h1": ""}


class Head(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title, self.description, self.h1, self.now, self.h1_done = "", "", "", None, False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self.now = "title"
        elif tag == "h1" and not self.h1_done:
            self.now = "h1"
        elif tag == "meta" and a.get("name") == "description":
            self.description = a.get("content") or ""

    def handle_endtag(self, tag):
        if tag == "h1" and self.now == "h1":
            self.h1_done = True
        if tag in ("title", "h1"):
            self.now = None

    def handle_data(self, data):
        if self.now == "title":
            self.title += data
        elif self.now == "h1":
            self.h1 += data


def read(html):
    p = Head()
    p.feed(html)
    return {k: " ".join(getattr(p, k).split()) for k in FIELDS}


def is_redirect(html):
    return 'http-equiv="refresh"' in html


def built():
    out = {}
    for f in sorted(DIST.rglob("*.html")):
        html = f.read_text(encoding="utf-8")
        if not is_redirect(html):
            name = str(f.relative_to(DIST))
            out["/" + name[: -len("index.html")] if name.endswith("index.html") else "/" + name] = read(html)
    return out


def fetch(url):
    """(status, text); status 0 when the page could not be read after three tries."""
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "peptidechooser-tier1-guard"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 404, ""
        except OSError:
            pass
        time.sleep(2 * (i + 1))
    return 0, ""


def live_page(path):
    status, html = fetch(LIVE + path)
    if status == 200 and not is_redirect(html):
        return path, read(html)
    return path, None if status == 404 or status == 200 else "unread"


def live_paths():
    """The live sitemap's pages, for a page that left the build. Unread means the guard cannot say, so it stops."""
    status, xml = fetch(LIVE + "/sitemap.xml")
    if status != 200:
        return None
    return {re.sub(r"^https?://[^/]+", "", u) or "/" for u in re.findall(r"<loc>([^<]+)</loc>", xml)}


def stamp(page):
    return hashlib.sha256("\0".join(page[k] for k in FIELDS).encode("utf-8")).hexdigest()[:12]


def approvals():
    """{(path, hash)} under a phrase line, in the commit message and in the approval file."""
    texts = [APPROVED.read_text(encoding="utf-8") if APPROVED.exists() else ""]
    try:
        texts.append(subprocess.run(["git", "log", "-1", "--format=%B"], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
    except (OSError, subprocess.CalledProcessError):
        pass
    ok = set()
    for text in texts:
        on = False
        for line in text.splitlines():
            if PHRASE.search(line):
                on = True
            m = LINE.match(line.strip())
            if m and on:
                ok.add(m.groups())
    return ok


def main():
    pages = built()
    with ThreadPoolExecutor(8) as pool:
        live = dict(pool.map(live_page, pages))
    paths = live_paths()
    unread = sorted(p for p, v in live.items() if v == "unread")
    gone = sorted(paths - set(pages)) if paths is not None else []
    ok = approvals()
    changes = []
    for path, page in pages.items():
        old = live[path]
        if old == "unread" or old == page:
            continue
        changes.append((path, "new page" if old is None else "changed", old or GONE, page))
    for path in gone:
        changes.append((path, "left the build", live_page(path)[1] or GONE, GONE))
    open_ = [c for c in changes if (c[0], stamp(c[3])) not in ok]

    report = [f"Tier 1 guard: {len(pages)} pages against {LIVE}: {len(changes)} changes, {len(changes) - len(open_)} approved, {len(open_)} not approved."]
    for path, what, old, new in changes:
        state = "approved" if (path, stamp(new)) in ok else "NOT APPROVED"
        report.append(f"\n{path} ({what}, {state})")
        for k in FIELDS:
            if old[k] != new[k]:
                report.append(f"  {k}\n    old: {old[k] or '(none)'}\n    new: {new[k] or '(none)'}")
    if open_:
        report.append("\nTo approve after the owner's phrase, put these lines under it, in the commit message or in data/tier1-approved.txt:")
        report.append("ODOBRENO SEO - Karlo - <date>")
        report += [f"{path} {stamp(new)}" for path, _, _, new in open_]
    if unread:
        report.append(f"\nCould not read {len(unread)} live page(s), so the guard cannot say what changed: " + ", ".join(unread[:20]))
    if paths is None:
        report.append("\nCould not read the live sitemap, so the guard cannot say which pages left the build.")
    text = "\n".join(report)
    print(text)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("```\n" + text + "\n```\n")
    return 1 if open_ or unread or paths is None else 0


if __name__ == "__main__":
    sys.exit(main())
