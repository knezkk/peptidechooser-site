"""Draws one og:image per page from its title (design book: Pages and buttons, Share image), and the favicons from the
logo mark (design book: README, Logo).
Run after build.py: python3 tools/og.py   -> writes assets/og/<name>.png (1200x630) and assets/favicon-16.png,
favicon-32.png, apple-touch-icon.png (180), icon-512.png, then rebuild.
python3 tools/og.py --missing draws only the pages that have no image yet and leaves the favicons (--missing --count
prints how many); the deploy runs it, so a page born from new data gets its image there (owner answer Q1 a, 3 Nov 2026).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
arg = lambda n: sys.argv[sys.argv.index(n) + 1] if n in sys.argv else None
# --pages FILE and --out DIR draw a given list (sample pages of a type the site does not have yet) somewhere else.
pages = json.loads(Path(arg("--pages") or ROOT / "dist" / "pages.json").read_text())
tokens = json.loads((ROOT / "design" / "tokens.json").read_text())
col = {t["name"]: t["value"] for t in tokens["color"]["tokens"]}
mark = (ROOT / "assets" / "logo.svg").read_text()

TEMPLATE = """<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,800&family=Public+Sans:wght@800&family=Atkinson+Hyperlegible:wght@400;700&display=swap" rel="stylesheet">
<style>
body{{margin:0;width:1200px;height:630px;background:{paper};color:{ink};font-family:"Atkinson Hyperlegible",Arial,sans-serif;display:flex;flex-direction:column;justify-content:space-between;padding:64px;box-sizing:border-box;border-bottom:16px solid {mark}}}
.t{{font:800 64px/1.05 "Bricolage Grotesque",Arial,sans-serif;letter-spacing:-0.02em;max-width:1000px;overflow-wrap:anywhere}}
.b{{display:flex;align-items:center;gap:16px;font:800 32px "Public Sans",Arial,sans-serif;letter-spacing:-0.015em}}
.b svg{{height:32px;width:auto}}
.s{{font-size:22px;color:{ink2};margin-top:16px}}
.k{{font-size:26px;font-weight:700;color:{ink2};margin-bottom:14px}}
.r{{display:flex;align-items:flex-end;justify-content:space-between;gap:48px}}
.i{{flex:none;display:flex;align-items:center;justify-content:center;width:220px;height:220px;border-radius:20px;background:{paper2}}}
.i svg{{width:132px;height:132px;fill:none;stroke:{ink};stroke-width:2.4;stroke-linecap:round}}
</style></head><body>
<div class="b">{svg}<span>Peptide Chooser</span></div>
<div class="r"><div>{kind}<div class="t">{title}</div><div class="s">We compare, we don't sell.</div></div>{icon}</div>
</body></html>"""

# The new page types (design/pages/new-types.md, group.md) say what they are above the title; a group page also shows
# its line drawing (assets/art.svg, group-<slug>) on a paper-2 panel. Every other page keeps the plain card.
GROUPS = {"fda-approved", "prescription", "supplements", "topical", "injections", "bioregulators"}
KINDS = [(r"^/(" + "|".join(GROUPS) + r")/$", "Substance group"), (r"^/peptides/[^/]+/[^/]+/$", "Brand"),
         (r"^/sellers/[^/]+/[^/]+/$", "Seller offer"), (r"^/labs/[^/]+/$", "Lab reports"),
         (r"^/fda-warning-letters/[^/]+/$", "FDA warning letters"), (r"^/tools/[^/]+/$", "Tool")]
ART = (ROOT / "assets" / "art.svg").read_text()


def kind_icon(path):
    kind = next((k for rx, k in KINDS if re.match(rx, path)), None)
    slug = path.strip("/")
    sym = re.search(rf'<symbol id="group-{re.escape(slug)}"[^>]*>(.*?)</symbol>', ART, re.S) if slug in GROUPS else None
    icon = f'<div class="i"><svg viewBox="0 0 56 56">{sym.group(1)}</svg></div>' if sym else ""
    return (f'<div class="k">{kind}</div>' if kind else ""), icon

out = Path(arg("--out") or ROOT / "assets" / "og")
out.mkdir(parents=True, exist_ok=True)
missing = "--missing" in sys.argv
og_name = lambda item: "home" if item["path"] == "/" else item["path"].strip("/").replace("/", "-")
if missing:
    pages = [i for i in pages if not (out / f"{og_name(i)}.png").exists()]
    print(len(pages) if "--count" in sys.argv else f"og: {len(pages)} missing")
    if not pages or "--count" in sys.argv:
        sys.exit(0)
from playwright.sync_api import sync_playwright  # noqa: E402 (not needed to count)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1200, "height": 630})
    for item in pages:
        name = og_name(item)
        title = item["title"].split(" | ")[0]
        kind, icon = kind_icon(item["path"])
        pg.set_content(TEMPLATE.format(paper=col["paper"], paper2=col["paper-2"], ink=col["ink"], ink2=col["ink-2"], mark=col["mark"],
                                       svg=mark, title=title, kind=kind, icon=icon))
        pg.wait_for_timeout(600)
        pg.screenshot(path=str(out / f"{name}.png"))
        print("og", name)
    if missing or arg("--pages"):
        b.close()
        sys.exit(0)
    # Favicons (README, Logo): the mark alone. 16 and 32 on a clear background, filling the 56 grid; the apple touch icon
    # (180) and the manifest icon (512) on white with half the mark's height as clear space on every side.
    icons = [("favicon-16.png", 16, "1 1 54 54", "transparent"), ("favicon-32.png", 32, "1 1 54 54", "transparent"),
             ("apple-touch-icon.png", 180, "-7 -7 70 70", col["white"]), ("icon-512.png", 512, "-7 -7 70 70", col["white"])]
    for name, size, vb, bg in icons:
        pg = b.new_page(viewport={"width": size, "height": size})
        svg = mark.replace('viewBox="3 18 50 20"', f'viewBox="{vb}" width="{size}" height="{size}" style="display:block"')
        pg.set_content(f'<body style="margin:0;background:{bg}">{svg}</body>')
        pg.screenshot(path=str(ROOT / "assets" / name), omit_background=bg == "transparent")
        print("icon", name)
    b.close()
