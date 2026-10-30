"""Builds the static Peptide Chooser site into ./dist. Run: python3 build.py"""
from pathlib import Path
import shutil

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
SITE = "https://peptidechooser.com"
UPDATED = "October 30, 2026"
EMAIL = "hello@peptidechooser.com"

NAV = [("/", "Home"), ("/about/", "About"), ("/how-we-rate/", "How we rate"), ("/contact/", "Contact")]

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,600;12..96,700'
         '&family=Literata:opsz,wght@7..72,400;7..72,500&display=swap" rel="stylesheet">')


def page(path, title, description, body, schema=""):
    nav = "".join(
        f'<a href="{href}"{" aria-current=\"page\"" if href == path else ""}>{label}</a>'
        for href, label in NAV
    )
    canonical = SITE + path
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
<meta name="theme-color" content="#10262a">
<link rel="icon" href="/assets/mark.svg" type="image/svg+xml">
{FONTS}
<link rel="stylesheet" href="/assets/style.css">
{schema}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-head">
  <div class="wrap">
    <a class="brand" href="/"><img src="/assets/mark.svg" alt="" width="30" height="30">Peptide Chooser</a>
    <nav class="nav" aria-label="Main">{nav}</nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-foot">
  <div class="wrap foot-grid">
    <div>
      <p><strong>Peptide Chooser</strong> compares peptide products, sellers and proven alternatives for people in the United States.</p>
      <p>Information on this site is general education, not medical advice. Talk to a licensed clinician before starting, stopping or combining any treatment.</p>
      <p>Some links on this site may earn us a commission. Commissions never change how we rate or rank anything. <a href="/disclosure/">Read our disclosure</a>.</p>
    </div>
    <div>
      <ul class="foot-links">
        <li><a href="/about/">About</a></li>
        <li><a href="/how-we-rate/">How we rate</a></li>
        <li><a href="/contact/">Contact</a></li>
        <li><a href="/disclosure/">Affiliate and medical disclosure</a></li>
        <li><a href="/privacy/">Privacy policy</a></li>
      </ul>
      <p style="margin-top:16px">&copy; 2026 Peptide Chooser</p>
    </div>
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

HOME = f"""
<section class="hero">
  <div class="wrap hero-grid">
    <div>
      <h1>Peptides for hair growth, compared honestly.</h1>
      <p class="lede">Peptide Chooser puts peptide products, the sellers behind them and the FDA-approved alternatives side by side. You see what each option is, what the evidence says and how you would get it, before you spend anything.</p>
      <div class="hero-actions">
        <a class="btn btn-primary" href="/how-we-rate/">See how we rate</a>
        <a class="btn btn-quiet" href="/about/">About Peptide Chooser</a>
      </div>
    </div>
    <div class="routes">
      <table>
        <caption>Three routes people take for thinning hair
          <span class="caption-note">Status for treating hair loss in the US, as of {UPDATED}.</span>
        </caption>
        <thead>
          <tr><th scope="col">Route</th><th scope="col">FDA status for hair loss</th><th scope="col">Human hair evidence</th></tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">Minoxidil and finasteride<small>Topical over the counter; finasteride by prescription, men only</small></th>
            <td data-label="FDA status for hair loss"><span class="status status-strong">Approved</span></td>
            <td data-label="Human hair evidence"><span class="status status-strong">Strong, many trials</span></td>
          </tr>
          <tr>
            <th scope="row">Copper peptide serums<small>GHK-Cu and similar, sold as cosmetics</small></th>
            <td data-label="FDA status for hair loss"><span class="status status-limited">Not approved; cosmetic</span></td>
            <td data-label="Human hair evidence"><span class="status status-limited">Limited, mostly lab studies</span></td>
          </tr>
          <tr>
            <th scope="row">Injectable peptides<small>Research-labeled or compounded vials</small></th>
            <td data-label="FDA status for hair loss"><span class="status status-none">Not approved</span></td>
            <td data-label="Human hair evidence"><span class="status status-none">Little to none</span></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</section>

<section class="band">
  <div class="wrap split">
    <div>
      <h2>What we check before we recommend anything</h2>
      <p>Most "best peptide" lists rank whoever pays the most. We publish our criteria and show the source and date behind every claim.</p>
      <p><a href="/how-we-rate/">Read the full method</a></p>
    </div>
    <ul class="criteria">
      <li><h3>Evidence</h3><p>What human studies show for the use you care about, not what a molecule does in a dish.</p></li>
      <li><h3>Regulatory status</h3><p>FDA approval, cosmetic or research labeling, and any FDA warning letters sent to the seller.</p></li>
      <li><h3>Lab testing</h3><p>Whether a third-party certificate of analysis exists and matches the batch you would actually receive.</p></li>
      <li><h3>Real price</h3><p>Price per milligram or per month, calculated the same way for every seller so the numbers compare.</p></li>
      <li><h3>Transparency</h3><p>Who runs the company, where it ships from, and whether paid placements are labeled.</p></li>
    </ul>
  </div>
</section>

<section class="band band-mist">
  <div class="wrap">
    <h2>Guides we are publishing first</h2>
    <p>We are starting with hair, then expanding to skin, recovery and weight loss. These guides are in progress.</p>
    <div class="queue">
      <article><h3>Best peptides for hair growth</h3><p>Which peptide products are worth trying, compared with minoxidil and finasteride.</p></article>
      <article><h3>GHK-Cu for hair</h3><p>What copper peptides can and cannot do for thinning hair, and how to read a serum label.</p></article>
      <article><h3>Peptides for hair: before and after</h3><p>Realistic timelines, and how to judge photos you see online.</p></article>
      <article><h3>Hair loss treatment online</h3><p>Telehealth services that prescribe hair loss treatment, compared on price and what is included.</p></article>
    </div>
    <p class="note">We are an independent comparison site. We do not sell peptides or any other product. When a seller pays us a commission, the link is labeled, and it does not affect where that seller appears.</p>
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
<h2>How we make money</h2>
<p>Some links on this site are affiliate links. If you buy through one, the seller may pay us a commission at no extra cost to you. These links are labeled. See our <a href="/disclosure/">affiliate and medical disclosure</a> for details.</p>
<h2>Contact</h2>
<p>Questions, corrections or partnership requests: <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
</div></section>
"""

HOW = f"""
<section class="page"><div class="wrap prose">
<h1>How we rate peptide products and sellers</h1>
<p class="lede">Every product and seller is judged on the same five criteria. We publish them so you can check our work.</p>
<p class="updated">Last updated {UPDATED}</p>
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
<p>Whether a seller pays us a commission. Affiliate links are labeled and sellers without an affiliate program are rated and listed the same way.</p>
<h2>Corrections</h2>
<p>If you find an error, email <a href="mailto:{EMAIL}">{EMAIL}</a> with the page and the source. We correct confirmed errors and note the date of the change.</p>
</div></section>
"""

CONTACT = f"""
<section class="page"><div class="wrap prose">
<h1>Contact</h1>
<p class="lede">Email is the fastest way to reach us.</p>
<p><a class="btn btn-primary" href="mailto:{EMAIL}">Email {EMAIL}</a></p>
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
<p class="updated">Last updated {UPDATED}</p>
<h2>Affiliate links</h2>
<p>Peptide Chooser is supported by affiliate commissions. Some links on this site go to sellers or services that pay us a commission if you make a purchase or sign up. This costs you nothing extra.</p>
<p>Affiliate links are labeled where they appear. Commissions do not affect our ratings, rankings or which products we include. Sellers without an affiliate program are rated and listed on the same terms.</p>
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
<p class="updated">Last updated {UPDATED}</p>
<p>This policy explains what information Peptide Chooser ("we") collects when you visit peptidechooser.com and how we use it.</p>
<h2>Information we collect</h2>
<ul>
<li><strong>Email you send us.</strong> If you contact us, we receive your email address and whatever you include in your message. We use it only to reply.</li>
<li><strong>Server logs.</strong> Our hosting provider (GitHub Pages) may record technical data such as IP address, browser type and the pages requested, for security and to operate the service. We do not use this data to identify you.</li>
</ul>
<p>We do not currently use analytics, advertising trackers or our own cookies. If that changes, we will update this policy before it takes effect.</p>
<h2>Affiliate links</h2>
<p>When you click an affiliate link, you leave our site. The seller or affiliate network may set cookies to record that you came from us. Their own privacy policies apply to that data.</p>
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
<h1>This page does not exist</h1>
<p class="lede">The link may be old or mistyped.</p>
<p><a class="btn btn-primary" href="/">Go to the home page</a></p>
</div></section>
"""

PAGES = [
    ("/", "index.html", "Peptide Chooser: compare peptides for hair growth honestly",
     "Compare peptide products, sellers and FDA-approved alternatives for hair growth. Evidence, FDA status, lab testing and real prices in one place.", HOME, ORG_SCHEMA),
    ("/about/", "about/index.html", "About Peptide Chooser",
     "Peptide Chooser is an independent site that compares peptide products and sellers for people in the United States.", ABOUT, ""),
    ("/how-we-rate/", "how-we-rate/index.html", "How we rate peptide products and sellers | Peptide Chooser",
     "The five criteria Peptide Chooser uses to rate every peptide product and seller: evidence, FDA status, lab testing, real price and transparency.", HOW, ""),
    ("/contact/", "contact/index.html", "Contact | Peptide Chooser",
     "Contact Peptide Chooser by email for corrections, listings, press and partnerships.", CONTACT, ""),
    ("/disclosure/", "disclosure/index.html", "Affiliate and medical disclosure | Peptide Chooser",
     "How Peptide Chooser earns money through affiliate links, and why nothing on the site is medical advice.", DISCLOSURE, ""),
    ("/privacy/", "privacy/index.html", "Privacy policy | Peptide Chooser",
     "What information Peptide Chooser collects, how it is used and how to contact us about your data.", PRIVACY, ""),
]


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "assets").mkdir(parents=True)
    for f in (ROOT / "assets").iterdir():
        shutil.copy(f, DIST / "assets" / f.name)
    for path, out, title, desc, body, schema in PAGES:
        target = DIST / out
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page(path, title, desc, body, schema), encoding="utf-8")
    (DIST / "404.html").write_text(page("/404", "Page not found | Peptide Chooser",
                                        "This page does not exist.", NOT_FOUND), encoding="utf-8")
    (DIST / "CNAME").write_text("peptidechooser.com\n")
    (DIST / ".nojekyll").write_text("")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    urls = "".join(f"<url><loc>{SITE}{p[0]}</loc><lastmod>2026-10-30</lastmod></url>" for p in PAGES)
    (DIST / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    print("built", len(PAGES) + 1, "pages")


if __name__ == "__main__":
    main()
