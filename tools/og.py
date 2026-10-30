"""Draws one og:image per page from its title (design book: Pages and buttons, Share image).
Run after build.py: python3 tools/og.py   -> writes assets/og/<name>.png (1200x630), then rebuild.
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
pages = json.loads((ROOT / "dist" / "pages.json").read_text())
tokens = json.loads((ROOT / "design" / "tokens.json").read_text())
col = {t["name"]: t["value"] for t in tokens["color"]["tokens"]}
mark = (ROOT / "assets" / "mark.svg").read_text()

TEMPLATE = """<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,800&family=Atkinson+Hyperlegible:wght@400;700&display=swap" rel="stylesheet">
<style>
body{{margin:0;width:1200px;height:630px;background:{paper};color:{ink};font-family:"Atkinson Hyperlegible",Arial,sans-serif;display:flex;flex-direction:column;justify-content:space-between;padding:64px;box-sizing:border-box;border-bottom:16px solid {mark}}}
.t{{font:800 64px/1.05 "Bricolage Grotesque",Arial,sans-serif;letter-spacing:-0.02em;max-width:1000px;overflow-wrap:anywhere}}
.b{{display:flex;align-items:center;gap:16px;font:700 32px "Bricolage Grotesque",Arial,sans-serif}}
.b svg{{width:56px;height:56px}}
.s{{font-size:22px;color:{ink2};margin-top:16px}}
</style></head><body>
<div class="b">{svg}<span>Peptide Chooser</span></div>
<div><div class="t">{title}</div><div class="s">We compare, we don't sell.</div></div>
</body></html>"""

out = ROOT / "assets" / "og"
out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1200, "height": 630})
    for item in pages:
        name = "home" if item["path"] == "/" else item["path"].strip("/").replace("/", "-")
        title = item["title"].split(" | ")[0]
        pg.set_content(TEMPLATE.format(paper=col["paper"], ink=col["ink"], ink2=col["ink-2"], mark=col["mark"], svg=mark, title=title))
        pg.wait_for_timeout(600)
        pg.screenshot(path=str(out / f"{name}.png"))
        print("og", name)
    b.close()
