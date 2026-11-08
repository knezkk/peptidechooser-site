#!/usr/bin/env python3
"""Tier 1 guard (CLAUDE.md rule 2; design/pages/every-page.md, Tier 1 guard; owner answer to #94 Q2, 5 Nov 2026).

Run in the deploy after the last build: every built page's <title>, meta description and first H1 against the same page on
the live site. Words stop the deploy; numbers and data-born pages pass and are listed (owner answer, 5 Nov 2026):
- a page that differs only in digits, dates, prices or counts (the same words with other numbers) passes;
- a new page under /sellers/, /compare/ or /peptides/ passes when its title and H1 are ones a live page of that section already
  has and every sentence of its description is one a live page of that section already uses, names, numbers and substances aside;
- a page that left the build passes when its URL is now a redirect to a page that is built;
- a seller page's meta description passes by rule when both the live and the built text are made only of the build's fixed
  description sentences (build.py, clinic_description) for the same seller, and they differ only in the data slots: the
  medicine list, the plan count, the price, the care fee, the letter count and the checks-met count, with their dates (owner,
  5 Nov 2026; ODOBRENO PRAVILA - Karlo - 5. 11. 2026). The comparison blanks those slots in the template, not a word list.
  A sentence the build does not write that way is hand-written and stops; the title and H1 must still be the same words.
Anything else stops the deploy, unless the owner approved exactly that new text: under a line with the phrase
ODOBRENO SEO - Karlo - <date>, in the commit message or in data/tier1-approved.txt, a line "<path> <hash>" as this script prints
it. The hash is of the new text, so an approval covers that text and nothing later. When in doubt the guard stops: a text it
cannot place is a change of words.

Live pages, not a committed snapshot: the live site is what readers and Google have, and it cannot drift. A snapshot would need
a deploy that writes back to the repo, and it would be wrong after a failed deploy or a re-run. A page that cannot be read
after three tries stops the deploy too (it says so): the guard never passes on what it did not see.

Usage: python3 tools/tier1_guard.py       TIER1_LIVE=<url> reads another site, for tests.
"""
import hashlib
import json
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
SITE_DATA = ROOT / "data" / "site.json"
APPROVED = ROOT / "data" / "tier1-approved.txt"
LIVE = os.environ.get("TIER1_LIVE", "https://peptidechooser.com").rstrip("/")
PHRASE = re.compile(r"ODOBRENO SEO(?: and ODOBRENO \w+)? - Karlo - \d{1,2}\.\s?\d{1,2}\.\s?\d{4}")
LINE = re.compile(r"^(/\S*)\s+([0-9a-f]{12})\s*$")
FIELDS = ("title", "description", "h1")
GONE = {"title": "", "description": "", "h1": ""}

MONTH = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|January|February|March|April|June|July|August|September|October|November|December)"
DATE = re.compile(rf"\b(?:\d{{1,2}} {MONTH},? \d{{4}}|{MONTH} \d{{1,2}},? \d{{4}}|\d{{1,2}} {MONTH}|{MONTH} \d{{4}}|\d{{4}}-\d{{2}}-\d{{2}})\b")
PRICE = re.compile(r"\$\d[\d,]*(?:\.\d+)?")
# A number on its own: the 1 in GLP-1 or the 157 in BPC-157 is part of a name, and a change there is a change of words.
COUNT = re.compile(r"(?<![\w.,$-])\d[\d,]*(?:\.\d+)?(?![\w-])")
# "1 plan" and "2 plans" are the same words; the noun may stand up to two words after the number ("3 FDA warning letters").
PLURAL = re.compile(r"(<n>(?: [\w-]+){0,2}? (?:plan|product|substance|shop|clinic|seller|letter|check|page|guide|listing|form|goal|peptide|brand|source|option))s\b")
STATES = {"Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
          "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
          "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina",
          "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas",
          "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"}
SECTIONS = {"sellers": re.compile(r"^(?P<name>.+) review$"), "compare": re.compile(r"^(?P<name>.+) vs (?P<other>.+)$"),
            "peptides": re.compile(r"^(?P<name>.+?)(?: \((?P<other>.+)\))?$")}


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
    if "<sitemapindex" in xml:  # one file per page type since task 23 (8 Nov 2026): read each
        parts = []
        for loc in re.findall(r"<loc>([^<]+)</loc>", xml):
            status, child = fetch(re.sub(r"^https?://[^/]+", LIVE, loc))
            if status != 200:
                return None
            parts.append(child)
        xml = "".join(parts)
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


def numbers_masked(text):
    text = PRICE.sub("<price>", DATE.sub("<date>", text))
    return PLURAL.sub(r"\1", COUNT.sub("<n>", text))


def only_numbers(old, new):
    """The same words with other numbers."""
    return all(numbers_masked(old[k]) == numbers_masked(new[k]) for k in FIELDS)


# The seller description's fixed sentences (build.py, clinic_description), in the order the build writes them. Each holds data
# slots, blanked to the slot's name; the name in the first sentence must stay the same seller. The build drops facts from the
# end to fit 160 characters, so a template may lose or gain a later sentence; it never writes one out of order.
_D = rf"(?:{DATE.pattern})"
DESCRIPTION_TEMPLATE = (
    ("clinic", re.compile(r"(?P<name>.+?) is an online clinic(?: that prescribes (?:\d+ medicines|[^.]+?))?\.")),
    ("plans", re.compile(r"\d+ plans? from \$[\d,.]+/mo, (?:care fee not known|no care fee|plus \$[\d,.]+/mo care)\.")),
    ("letters", re.compile(rf"(?:No FDA warning letter|\d+ FDA warning letters?, the newest {_D})\.")),
    ("checks", re.compile(rf"\d+ of \d+ checks met(?: on {_D})?\.")),
    ("since", re.compile(rf"Tracked since {_D}\.")),
)


def description_slots(text):
    """(seller name, the template's slots in order) when every sentence is one of the fixed description sentences; else None."""
    kinds, name, at = [], None, 0
    for sentence in re.findall(r".+?\.(?=\s+[A-Z0-9]|$)", text):
        sentence = sentence.strip()
        for i, (kind, pat) in enumerate(DESCRIPTION_TEMPLATE[at:], at):
            m = pat.fullmatch(sentence)
            if m:
                if kind == "clinic":
                    name = m.group("name")
                kinds.append(kind)
                at = i + 1
                break
        else:
            return None
    return (name, kinds) if kinds and kinds[0] == "clinic" else None


def data_description(path, old, new):
    """A seller page whose description changed only in the template's data slots, title and H1 the same words."""
    if section_of(path)[0] != "sellers" or not all(numbers_masked(old[k]) == numbers_masked(new[k]) for k in ("title", "h1")):
        return False
    a, b = description_slots(old["description"]), description_slots(new["description"])
    return bool(a and b and a[0] == b[0])


def slugged(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower().replace("+", " plus ")).strip("-")


def section_of(path):
    """The section of a data-born page: /sellers/<slug>/ and its like. Goal pages, guides and the rest are written by hand."""
    m = re.fullmatch(r"/(\w+)/([^/]+)/", path)
    return (m.group(1), m.group(2)) if m and m.group(1) in SECTIONS else (None, None)


def page_names(path, page, known):
    """The names in a page's H1, or None when they do not come from the data: each stands in the data, the first in the URL too."""
    section, slug = section_of(path)
    m = SECTIONS[section].fullmatch(page["h1"]) if section else None
    if not m:
        return None
    names = [n for n in m.groups() if n]
    if not all(n.lower() in known for n in names):
        return None
    urlnames = names if section == "compare" else names[:1]
    if not all(f"-{slugged(n)}-" in f"-{slug}-" for n in urlnames):
        return None
    return names


def slot_masked(sentence, known, goals):
    """The places in a template that hold data: a goal, an approved brand, a US state. Only a value the data holds is masked."""
    m = re.fullmatch(r"On our (.+?) pages?\.", sentence)
    if m and (m.group(1).lower() in goals or all(g.lower() in goals for g in m.group(1).split(" and "))):
        return "On our <goal> page."
    m = re.fullmatch(r"Approved brands?: (.+)\.", sentence)
    if m and all(b.lower() in known for b in m.group(1).split(", ")):
        return "Approved brand: <brand>."
    m = re.search(r" in ([A-Z][a-z]+(?: [A-Z][a-z]+)?)\.$", sentence)
    if m and m.group(1) in STATES:
        return sentence[: m.start()] + " in <state>."
    return sentence


def word_masked(text, names, substances):
    for n in sorted(names, key=len, reverse=True):
        text = re.sub(rf"(?<![\w-]){re.escape(n)}(?![\w-])", "<name>", text)
    if substances:
        alt = "|".join(re.escape(x) for x in sorted(substances, key=len, reverse=True))
        text = re.sub(rf"(?<![\w-])(?:compounded )?(?:{alt})(?![\w-])", "<s>", text, flags=re.I)
        text = re.sub(r"<s>(?:, <s>)*(?:,? and <s>)?", "<s>", text)
    return numbers_masked(text)


def sentences(text):
    return [x for x in re.split(r"(?<=[.?!])\s+", text) if x]


def shape(path, page, facts):
    """A page's words without its names and numbers: (title, H1, the sentences of its description); None when its names are not data."""
    known, goals, substances = facts
    names = page_names(path, page, known)
    if names is None:
        return None
    return (word_masked(page["title"], names, substances), word_masked(page["h1"], names, substances),
            [word_masked(slot_masked(x, known, goals), names, substances) for x in sentences(page["description"])])


def follows_template(path, page, live, facts):
    """A new page passes only on what is live already: its section's other pages, as readers see them today, set the template."""
    section, _ = section_of(path)
    mine = shape(path, page, facts)
    if mine is None or not mine[2]:
        return False
    titles, h1s, said = set(), set(), set()
    for other, old in live.items():
        if other == path or section_of(other)[0] != section or not isinstance(old, dict):
            continue
        theirs = shape(other, old, facts)
        if theirs:
            titles.add(theirs[0])
            h1s.add(theirs[1])
            said.update(theirs[2])
    if mine[0] not in titles or mine[1] not in h1s:
        return False
    if all(x in said for x in mine[2]):
        return True
    # A new seller page's description may name medicines no live page names yet (a brand in brackets, "Tadalafil (Cialis)"):
    # it passes when every sentence is one of the fixed description sentences and the name is the page's own.
    slots = description_slots(page["description"]) if section == "sellers" else None
    return bool(slots and slots[0] in page_names(path, page, facts[0]))


def substance_names(pages):
    """Every substance the site has a page for, from those pages' H1s; the brackets are other names of the same substance."""
    out = set()
    for path, page in pages.items():
        if section_of(path)[0] == "peptides":
            m = SECTIONS["peptides"].fullmatch(page["h1"])
            out.update(n for n in (m.groups() if m else ()) if n)
    return out


def load_facts(pages):
    """(the data as lower-case text, the goal names, the substances); no data file means no facts, so no new page passes."""
    if not SITE_DATA.exists():
        return "", set(), set()
    text = SITE_DATA.read_text(encoding="utf-8")
    goals = {str(g.get("name", "")).lower() for g in json.loads(text).get("goals", [])}
    return text.lower(), goals, substance_names(pages)


def redirect_target(path):
    """Where a built redirect at this URL points; None when the URL is not a redirect in this build."""
    f = DIST / path.lstrip("/") / "index.html" if path.endswith("/") else DIST / path.lstrip("/")
    if not f.exists():
        return None
    html = f.read_text(encoding="utf-8")
    m = re.search(r'http-equiv="refresh"[^>]*?url=([^"\']+)', html)
    return m.group(1).strip() if m else None


def main():
    pages = built()
    with ThreadPoolExecutor(8) as pool:
        live = dict(pool.map(live_page, pages))
    paths = live_paths()
    unread = sorted(p for p, v in live.items() if v == "unread")
    gone = sorted(paths - set(pages)) if paths is not None else []
    ok = approvals()
    facts = load_facts(pages)
    changes = []
    for path, page in pages.items():
        old = live[path]
        if old == "unread" or old == page:
            continue
        if old is None:
            passes = "follows its section's template" if follows_template(path, page, live, facts) else None
            changes.append((path, "new page", GONE, page, passes))
        else:
            why = "numbers only" if only_numbers(old, page) else "data slots of the seller description" if data_description(path, old, page) else None
            changes.append((path, "changed", old, page, why))
    for path in gone:
        old = live_page(path)[1]
        target = redirect_target(path)
        passes = f"redirects to {target}" if target in pages else None
        changes.append((path, "left the build", old if isinstance(old, dict) else GONE, GONE, passes))
    state = {c[0]: f"passes, {c[4]}" if c[4] else "approved" if (c[0], stamp(c[3])) in ok else "NOT APPROVED" for c in changes}
    open_ = [c for c in changes if state[c[0]] == "NOT APPROVED"]
    passed = sum(1 for c in changes if c[4])

    report = [f"Tier 1 guard: {len(pages)} pages against {LIVE}: {len(changes)} changes, {passed} pass by rule, "
              f"{len(changes) - len(open_) - passed} approved, {len(open_)} not approved."]
    for path, what, old, new, _ in changes:
        report.append(f"\n{path} ({what}, {state[path]})")
        for k in FIELDS:
            if old[k] != new[k]:
                report.append(f"  {k}\n    old: {old[k] or '(none)'}\n    new: {new[k] or '(none)'}")
    if open_:
        report.append("\nTo approve after the owner's phrase, put these lines under it, in the commit message or in data/tier1-approved.txt:")
        report.append("ODOBRENO SEO - Karlo - <date>")
        report += [f"{path} {stamp(new)}" for path, _, _, new, _ in open_]
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
