"""Builds the static Peptide Chooser site into ./dist. Run: python3 build.py

Design source: design/tokens.json and design/bundle.css (copies of the Master 1 design book).
Numbers source: data/site.json. Nothing numeric is typed into a template.
"""
from pathlib import Path
import json
import shutil
from datetime import date

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
SITE = "https://peptidechooser.com"
EMAIL = "hello@peptidechooser.com"
AUTHOR = "Peptide Chooser editorial team"

DATA = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
TOKENS = json.loads((ROOT / "design" / "tokens.json").read_text(encoding="utf-8"))
LIVE_GOALS = [g for g in DATA["goals"] if g.get("live")]


def nice_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%b %Y')}"


CHECKED = nice_date(DATA["checked"])
STANDING_LINE = f"Every claim links to its source. Prices checked {CHECKED}."

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800'
         '&family=Atkinson+Hyperlegible:wght@400;700&display=swap" rel="stylesheet">')


def tokens_css():
    """Compile design/tokens.json into CSS custom properties."""
    out = [f"/* Generated from design/tokens.json ({TOKENS['name']}). Do not edit. */", ":root {"]
    for t in TOKENS["color"]["tokens"]:
        out.append(f"  --{t['name']}: {t['value']};")
    for fam, stack in TOKENS["type"]["families"].items():
        out.append(f"  --font-{fam}: {stack};")
    for fam in ("spacing", "radius", "layout"):
        for t in TOKENS.get(fam, {}).get("tokens", []):
            v = t["value"]
            if fam == "layout" and not v.endswith("px"):
                v = v
            out.append(f"  --{t['name']}: {v};")
    out.append("}")
    return "\n".join(out) + "\n"


def nav_items(path):
    items = [(f"/{g['slug']}/", g["name"].split()[0]) for g in LIVE_GOALS if (ROOT / "pages" / g["slug"]).exists()]
    items += [("/how-we-rate/", "How we rate"), ("/about/", "About")]
    return "".join(
        f'<a href="{href}"{" aria-current=\"page\"" if href == path else ""}>{label}</a>' for href, label in items
    )


def crumbs(items):
    if not items:
        return ""
    parts = ['<a href="/">Home</a>']
    for href, label in items[:-1]:
        parts.append(f'<a href="{href}">{label}</a>')
    parts.append(f"<span aria-current=\"page\">{items[-1][1]}</span>")
    return '<nav class="crumbs wrap" aria-label="Breadcrumb">' + '<span aria-hidden="true">/</span>'.join(parts) + "</nav>"


def og_name(path):
    return "home" if path == "/" else path.strip("/").replace("/", "-")


def page(path, title, description, body, schema="", crumb=None):
    canonical = SITE + path
    og = f"{SITE}/assets/og/{og_name(path)}.png"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Peptide Chooser">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#1a2330">
<link rel="icon" href="/assets/mark.svg" type="image/svg+xml">
{FONTS}
<link rel="stylesheet" href="/assets/tokens.css">
<link rel="stylesheet" href="/assets/bundle.css">
<link rel="stylesheet" href="/assets/site.css">
{schema}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="notice"><div class="wrap"><span>We compare, we don't sell.</span><span class="more">Some links pay us. <a href="/disclosure/">How we make money</a></span></div></div>
<header class="site-head">
  <div class="wrap">
    <a class="brand" href="/"><img src="/assets/mark.svg" alt="" width="32" height="32">Peptide Chooser</a>
    <nav class="nav" aria-label="Main">{nav_items(path)}</nav>
    <div class="head-cta"><a class="btn btn-ink" href="/#goals">Compare by goal</a></div>
  </div>
</header>
{crumbs(crumb) if crumb else ""}
<main id="main">
{body}
</main>
<footer class="site-foot">
  <div class="wrap">
    <div class="foot-grid">
      <div>
        <a class="brand" href="/"><img src="/assets/mark-on-dark.svg" alt="" width="28" height="28">Peptide Chooser</a>
        <p>An independent comparison site for people in the United States. We do not sell peptides or any other product. Not medical advice. Talk to a doctor before starting any treatment.</p>
      </div>
      <ul class="foot-links">
        <li><a href="/about/">About</a></li>
        <li><a href="/how-we-rate/">How we rate</a></li>
        <li><a href="/contact/">Contact</a></li>
        <li><a href="/disclosure/">Affiliate and medical disclosure</a></li>
        <li><a href="/privacy/">Privacy policy</a></li>
      </ul>
    </div>
    <div class="trust"><span>&copy; 2026 Peptide Chooser</span><a href="/disclosure/">How we make money</a><span>{EMAIL}</span></div>
  </div>
</footer>
</body>
</html>
"""


ORG_SCHEMA = f"""<script type="application/ld+json">
{{"@context":"https://schema.org","@graph":[
{{"@type":"Organization","@id":"{SITE}/#org","name":"Peptide Chooser","url":"{SITE}/","logo":"{SITE}/assets/mark.svg","email":"{EMAIL}"}},
{{"@type":"WebSite","@id":"{SITE}/#site","url":"{SITE}/","name":"Peptide Chooser","publisher":{{"@id":"{SITE}/#org"}}}}
]}}
</script>"""


def breadcrumb_schema(items):
    els = [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"}]
    for i, (href, label) in enumerate(items, start=2):
        els.append({"@type": "ListItem", "position": i, "name": label, "item": SITE + href})
    return ('<script type="application/ld+json">'
            + json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": els})
            + "</script>")


def goal_rows():
    rows = []
    for g in LIVE_GOALS:
        chip = f'<span class="chip chip-{g["fda_chip"]}">{g["fda"]}</span>'
        has_page = (ROOT / "pages" / g["slug"]).exists()
        compare = f'<td><a class="btn btn-ink btn-sm" href="/{g["slug"]}/">Compare</a></td>' if has_page else ""
        rows.append(f"""<tr>
  <td><span class="name">{g["name"]}</span></td>
  <td><span class="name">{g["best_option"]}</span><span class="note">{g["options_checked"]} options checked</span></td>
  <td><span class="num-l">${g["price_from_usd"]}<span class="num-unit">/mo</span></span><span class="note">{g["price_note"]}</span></td>
  <td>{chip}</td>
  {compare}
</tr>""")
    return "\n".join(rows)


def board_rows():
    rows = []
    for g in LIVE_GOALS:
        rows.append(f'<div class="ledger"><span>{g["name"]}</span><span><span class="num-unit">from </span><strong>${g["price_from_usd"]}</strong><span class="num-unit">/mo</span></span></div>')
    return "\n".join(rows)


COMPARE_TH = '<th scope="col"></th>' if any((ROOT / "pages" / g["slug"]).exists() for g in LIVE_GOALS) else ""
TOTAL_OPTIONS = sum(g["options_checked"] for g in LIVE_GOALS)
PICKER = "".join(f'<a class="btn btn-line" href="#goals">{g["name"]}</a>' for g in LIVE_GOALS)
SOURCES_HOME = "".join(
    f'<li>{g["price_source_name"]}: <a href="{g["price_source"]}" rel="nofollow">{g["price_source"]}</a></li>' for g in LIVE_GOALS)

HOME = f"""
<section class="hero">
  <div class="wrap hero-grid">
    <div>
      <h1>The best peptides for your goal, compared honestly.</h1>
      <p class="lede">For each goal we put peptide products next to the FDA-approved alternatives and show what the evidence says, what it costs per month and how you would get it. We compare; we never sell.</p>
      <div class="goal-picker">{PICKER}</div>
    </div>
    <div class="board">
      <h2>Cheapest proven option, per month</h2>
      <p class="hero-num"><span class="num-xl">{TOTAL_OPTIONS}</span> <span class="num-unit">options checked</span></p>
      {board_rows()}
      <p class="fine" style="margin:16px 0 0">Prices checked {CHECKED}. Proven means FDA approved for that use.</p>
    </div>
  </div>
</section>

<section class="section" id="goals">
  <div class="wrap">
    <div class="sec-hd"><div><h2>Compare by goal</h2><p>One row per goal. The best proven option is the cheapest one the FDA has approved for that use.</p></div></div>
    <div class="tbl-wrap"><table class="tbl">
      <thead><tr><th scope="col">Goal</th><th scope="col">Best proven option</th><th scope="col">Price from</th><th scope="col">FDA status</th>{COMPARE_TH}</tr></thead>
      <tbody>{goal_rows()}</tbody>
    </table></div>
    <p class="small" style="margin-top:16px">{STANDING_LINE}</p>
  </div>
</section>

<section class="band-2">
  <div class="wrap">
    <div class="sec-hd"><div><h2>How we rate</h2><p>Every product and seller is judged on the same five criteria. We publish them so you can check our work.</p><a href="/how-we-rate/">Read the full method</a></div></div>
    <ul class="criteria">
      <li><h3>Evidence</h3><p>What human studies show for the use you care about, not what a molecule does in a dish.</p></li>
      <li><h3>Regulatory status</h3><p>FDA approval, cosmetic or research labeling, and any FDA warning letters sent to the seller.</p></li>
      <li><h3>Lab testing</h3><p>Whether a third-party certificate of analysis exists and matches the batch you would receive.</p></li>
      <li><h3>Real price</h3><p>Price per month or per milligram, calculated the same way for every seller so the numbers compare.</p></li>
      <li><h3>Transparency</h3><p>Who runs the company, where it ships from, and whether paid placements are labeled.</p></li>
    </ul>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <h2 style="font-size:22px">Sources</h2>
    <ol class="small" style="padding-left:1.2em">{SOURCES_HOME}</ol>
  </div>
</section>
"""

ABOUT = f"""
<section class="page"><div class="wrap prose">
<h1>About Peptide Chooser</h1>
<p class="lede">An independent site that helps people in the United States compare peptide products and the sellers behind them.</p>
<h2>Why this site exists</h2>
<p>Peptides are sold in very different ways: as approved prescription drugs, as cosmetics, as supplements and as research chemicals. The same name can mean a lab-tested product from a licensed pharmacy or an untested vial. Most websites that rank them are run by sellers or paid by sellers, and few show where their claims come from.</p>
<p>We built Peptide Chooser to put that information in one place: what each product is, how it is regulated, what the evidence says, what it really costs and who is selling it.</p>
<h2>What we do</h2>
<ul>
<li>Compare peptide products and sellers using the same published criteria for everyone.</li>
<li>Show the source and date behind every claim, including FDA status and warning letters.</li>
<li>Include FDA-approved alternatives when they are the better-supported option.</li>
</ul>
<h2>What we do not do</h2>
<ul>
<li>We do not sell peptides or any other product.</li>
<li>We do not give personal medical advice or dosing instructions.</li>
<li>We do not accept payment for a higher rating or position.</li>
</ul>
<h2>Who writes this site</h2>
<p>Pages are written and checked by the {AUTHOR}. We have no medical reviewer yet; until we do, every claim links to its source and no page gives dosing advice.</p>
<h2>How we make money</h2>
<p>Some links on this site are paid links. If you buy through one, the seller may pay us a commission at no extra cost to you. These links are labeled. See our <a href="/disclosure/">affiliate and medical disclosure</a> for details.</p>
<h2>Contact</h2>
<p>Questions, corrections or partnership requests: <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
</div></section>
"""

HOW = f"""
<section class="page"><div class="wrap prose">
<h1>How we rate peptide products and sellers</h1>
<p class="lede">Every product and seller is judged on the same five criteria. We publish them so you can check our work.</p>
<p class="small meta">{AUTHOR}. Last updated {CHECKED}. {STANDING_LINE}</p>
<h2>1. Evidence</h2>
<p>We look for human studies on the specific use you are reading about. Lab and animal results are reported as such and never presented as proof that something works in people.</p>
<h2>2. Regulatory status</h2>
<p>We state whether a product is FDA-approved for that use, sold as a cosmetic or supplement, compounded by a pharmacy, or labeled for research only. We check the FDA's public warning letter database for every seller we list and link the letter when one exists.</p>
<h2>3. Lab testing</h2>
<p>We record whether a seller publishes a certificate of analysis (COA), which lab issued it, its date, and whether it is tied to a specific batch. A COA that cannot be matched to a batch counts for less.</p>
<h2>4. Real price</h2>
<p>Sellers quote prices in different ways. We convert them to a common unit, such as price per milligram or price per 30 days of use, so the numbers can be compared directly.</p>
<h2>5. Transparency</h2>
<p>We look at who owns the company, where it ships from, its return policy, and whether it labels paid promotions.</p>
<h2>What does not affect a rating</h2>
<p>Whether a seller pays us a commission. Paid links are labeled and sellers without an affiliate program are rated and listed the same way.</p>
<h2>Corrections</h2>
<p>If you find an error, email <a href="mailto:{EMAIL}">{EMAIL}</a> with the page and the source. We correct confirmed errors and note the date of the change.</p>
</div></section>
"""

CONTACT = f"""
<section class="page"><div class="wrap prose">
<h1>Contact</h1>
<p class="lede">Email is the fastest way to reach us.</p>
<div class="btn-row"><a class="btn btn-ink" href="mailto:{EMAIL}">Email {EMAIL}</a></div>
<h2>What to write to us about</h2>
<ul>
<li>Corrections to any information on the site, with a link to your source.</li>
<li>Sellers and brands: questions about a listing or about working with us.</li>
<li>Press and partnerships.</li>
</ul>
<p>We cannot answer personal medical questions. For advice about your health, please speak to a licensed clinician.</p>
</div></section>
"""

DISCLOSURE = f"""
<section class="page"><div class="wrap prose">
<h1>Affiliate and medical disclosure</h1>
<p class="small meta">Last updated {CHECKED}</p>
<h2>Paid links</h2>
<p>Peptide Chooser is supported by affiliate commissions. Some links on this site go to sellers or services that pay us a commission if you make a purchase or sign up. This costs you nothing extra.</p>
<p>Paid links are labeled where they appear. Commissions do not affect our ratings, rankings or which products we include. Sellers without an affiliate program are rated and listed on the same terms.</p>
<p>We may take part in affiliate programs run by individual brands and by affiliate networks. We will list the networks we work with on this page as those relationships start.</p>
<h2>Not medical advice</h2>
<p>Everything on this site is general information for education. It is not medical advice, diagnosis or treatment, and it does not replace a consultation with a licensed clinician.</p>
<p>Some products discussed on this site are not approved by the U.S. Food and Drug Administration for the uses described. Where that is the case, we say so. Do not start, stop or combine any treatment without speaking to a clinician.</p>
<h2>No sales</h2>
<p>We do not manufacture, sell or ship any product.</p>
<h2>Questions</h2>
<p>Email <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
</div></section>
"""

PRIVACY = f"""
<section class="page"><div class="wrap prose">
<h1>Privacy policy</h1>
<p class="small meta">Last updated {CHECKED}</p>
<p>This policy explains what information Peptide Chooser ("we") collects when you visit peptidechooser.com and how we use it.</p>
<h2>Information we collect</h2>
<ul>
<li><strong>Email you send us.</strong> If you contact us, we receive your email address and whatever you include in your message. We use it only to reply.</li>
<li><strong>Server logs.</strong> Our hosting provider (GitHub Pages) may record technical data such as IP address, browser type and the pages requested, for security and to operate the service. We do not use this data to identify you.</li>
</ul>
<p>We do not currently use analytics, advertising trackers or our own cookies. If that changes, we will update this policy before it takes effect.</p>
<h2>Paid links</h2>
<p>When you click a paid link, you leave our site. The seller or affiliate network may set cookies to record that you came from us. Their own privacy policies apply to that data.</p>
<h2>How long we keep information</h2>
<p>We keep email correspondence for as long as needed to answer you and to keep a record of corrections, and no longer than 24 months unless the law requires otherwise.</p>
<h2>Your rights</h2>
<p>You can ask us to see, correct or delete the personal information we hold about you. Residents of the European Economic Area, the United Kingdom and some U.S. states, including California, have additional rights under their local laws. Email <a href="mailto:{EMAIL}">{EMAIL}</a> and we will respond within 30 days.</p>
<h2>Children</h2>
<p>This site is intended for adults. We do not knowingly collect information from anyone under 18.</p>
<h2>Contact</h2>
<p><a href="mailto:{EMAIL}">{EMAIL}</a></p>
</div></section>
"""

NOT_FOUND = """
<section class="page"><div class="wrap prose">
<h1>This page doesn't exist</h1>
<p class="lede">The link may be old or mistyped.</p>
<div class="btn-row"><a class="btn btn-ink" href="/">Go to the home page</a></div>
<p><a href="/#goals">Compare by goal</a></p>
</div></section>
"""

PAGES = [
    ("/", "index.html", "Best peptides by goal, compared | Peptide Chooser",
     "FDA status, real prices and evidence for each goal, checked and dated. Peptide products next to the approved alternatives, from an independent site that never sells.",
     HOME, ORG_SCHEMA, None),
    ("/about/", "about/index.html", "About Peptide Chooser",
     "Peptide Chooser is an independent site that compares peptide products and sellers for people in the United States.", ABOUT, "", [("/about/", "About")]),
    ("/how-we-rate/", "how-we-rate/index.html", "How we rate peptide products and sellers | Peptide Chooser",
     "The five criteria Peptide Chooser uses to rate every peptide product and seller: evidence, FDA status, lab testing, real price and transparency.", HOW, "", [("/how-we-rate/", "How we rate")]),
    ("/contact/", "contact/index.html", "Contact | Peptide Chooser",
     "Contact Peptide Chooser by email for corrections, listings, press and partnerships.", CONTACT, "", [("/contact/", "Contact")]),
    ("/disclosure/", "disclosure/index.html", "Affiliate and medical disclosure | Peptide Chooser",
     "How Peptide Chooser earns money through paid links, and why nothing on the site is medical advice.", DISCLOSURE, "", [("/disclosure/", "Disclosure")]),
    ("/privacy/", "privacy/index.html", "Privacy policy | Peptide Chooser",
     "What information Peptide Chooser collects, how it is used and how to contact us about your data.", PRIVACY, "", [("/privacy/", "Privacy")]),
]


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "assets" / "og").mkdir(parents=True)
    for f in (ROOT / "assets").iterdir():
        if f.is_file():
            shutil.copy(f, DIST / "assets" / f.name)
    for f in (ROOT / "assets" / "og").glob("*.png"):
        shutil.copy(f, DIST / "assets" / "og" / f.name)
    (DIST / "assets" / "tokens.css").write_text(tokens_css(), encoding="utf-8")
    shutil.copy(ROOT / "design" / "bundle.css", DIST / "assets" / "bundle.css")
    for path, out, title, desc, body, schema, crumb in PAGES:
        if crumb:
            schema = schema + breadcrumb_schema(crumb)
        target = DIST / out
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page(path, title, desc, body, schema, crumb), encoding="utf-8")
    (DIST / "404.html").write_text(page("/404", "Page not found | Peptide Chooser",
                                        "This page does not exist.", NOT_FOUND), encoding="utf-8")
    (DIST / "CNAME").write_text("peptidechooser.com\n")
    (DIST / ".nojekyll").write_text("")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nDisallow: /out/\nSitemap: {SITE}/sitemap.xml\n")
    (DIST / "llms.txt").write_text(
        "# Peptide Chooser\n\n> An independent US comparison site: peptide products next to FDA-approved alternatives, "
        "with evidence, FDA status and price per month for each goal. We compare; we never sell.\n\n"
        + "".join(f"- [{t}]({SITE}{p}): {d}\n" for p, _, t, d, *_ in PAGES))
    urls = "".join(f"<url><loc>{SITE}{p[0]}</loc><lastmod>{DATA['checked']}</lastmod></url>" for p in PAGES)
    (DIST / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    (DIST / "pages.json").write_text(json.dumps([{"path": p[0], "title": p[2]} for p in PAGES] + [{"path": "/404", "title": "Page not found | Peptide Chooser"}]))
    print("built", len(PAGES) + 1, "pages")


if __name__ == "__main__":
    main()
