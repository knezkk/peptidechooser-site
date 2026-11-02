"""Builds the static Peptide Chooser site into ./dist. Run: python3 build.py

Design source: design/tokens.json and design/bundle.css (copies of the Master 1 design book).
Numbers source: data/site.json. Nothing numeric is typed into a template.
"""
from pathlib import Path
import json
import re
from html import escape
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
COLOR = {t["name"]: t["value"] for t in TOKENS["color"]["tokens"]}


def nice_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%b %Y')}"


CHECKED = nice_date(DATA["checked"])
GA4_ID = DATA.get("ga4_id", "")

# Google Analytics 4 with Consent Mode v2. Everything starts denied; the cookie notice (design book,
# Pages and buttons, item 6) flips analytics_storage to granted only after "Accept". The choice is kept
# in localStorage under "pc-consent" so the bar is shown once.
ANALYTICS = f"""<script>
window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}
gtag('consent','default',{{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',analytics_storage:'denied',wait_for_update:500}});
try{{if(localStorage.getItem('pc-consent')==='yes'){{gtag('consent','update',{{analytics_storage:'granted'}});}}}}catch(e){{}}
gtag('js',new Date());gtag('config','{GA4_ID}',{{anonymize_ip:true}});
</script>
<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>""" if GA4_ID else ""

COOKIE_BAR = """<div class="cookie" id="cookie" hidden role="region" aria-label="Cookie notice">
  <div class="wrap">
    <p>We use Google Analytics to count visits<span class="cookie-long"> and see which pages help</span>. No ads, no selling of data. <a href="/privacy/">Privacy policy</a></p>
    <div class="cookie-btns"><button class="btn btn-ink btn-sm" type="button" data-consent="yes">Accept</button><button class="btn btn-line btn-sm" type="button" data-consent="no">Reject</button></div>
  </div>
</div>
<script>
(function(){var b=document.getElementById('cookie'),s=null;try{s=localStorage.getItem('pc-consent');}catch(e){}
if(!s){b.hidden=false;}
b.addEventListener('click',function(e){var v=e.target.getAttribute('data-consent');if(!v)return;
try{localStorage.setItem('pc-consent',v);}catch(e){}
if(v==='yes'&&window.gtag){gtag('consent','update',{analytics_storage:'granted'});}
b.hidden=true;});})();
</script>""" if GA4_ID else ""
STANDING_LINE = f"Every claim links to its source. Prices checked {CHECKED}."

# Design book, Motion. The head script marks the page for motion only when the visitor allows it; CSS then
# pre-hides what will be revealed. If GSAP has not started within 3 s, the mark is removed and everything shows.
# With JavaScript off or reduced motion on, nothing is ever hidden.
MOTION_HEAD = """<script>
(function(d){if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;d.classList.add('motion');
setTimeout(function(){if(!window.pcMotion)d.classList.remove('motion');},3000);})(document.documentElement);
</script>"""
# Design book, Every page, Header: up to 900px the nav sits behind "Menu". The head script marks the page before it
# paints, so the closed menu never flashes; with JavaScript off the mark is missing and the links show as a wrapped row.
NAV_HEAD = "<script>document.documentElement.classList.add('nav-js');</script>"
NAV_JS = """<script>
(function(){var b=document.querySelector('.nav-toggle'),n=document.getElementById('site-nav');if(!b||!n)return;
function set(o){n.classList.toggle('open',o);b.setAttribute('aria-expanded',o?'true':'false');}
b.addEventListener('click',function(){set(!n.classList.contains('open'));});
n.addEventListener('click',function(e){if(e.target.closest('a'))set(false);});
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&n.classList.contains('open')){set(false);b.focus();}});})();
(function(){var w=document.querySelector('.nav-goals'),b=w&&w.querySelector('.nav-goals-btn');if(!b)return;
function set(o){w.classList.toggle('open',o);b.setAttribute('aria-expanded',o?'true':'false');}
b.addEventListener('click',function(){set(!w.classList.contains('open'));});
w.addEventListener('click',function(e){if(e.target.closest('a'))set(false);});
document.addEventListener('click',function(e){if(w.classList.contains('open')&&!w.contains(e.target))set(false);});
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&w.classList.contains('open')){set(false);b.focus();}});})();
</script>"""
GSAP = "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5"
MOTION_JS = f"""<script defer src="{GSAP}/gsap.min.js"></script>
<script defer src="{GSAP}/ScrollTrigger.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded',function(){{
var d=document.documentElement;if(!d.classList.contains('motion')||!window.gsap||!window.ScrollTrigger)return;
window.pcMotion=true;gsap.registerPlugin(ScrollTrigger);
var css=getComputedStyle(d),ms=function(n){{return parseFloat(css.getPropertyValue('--motion-'+n))/1000;}};
var rise=parseFloat(css.getPropertyValue('--motion-rise'));
ScrollTrigger.batch('.sec-hd, .tbl tbody tr, .criteria li, .creators li',{{start:'top 92%',once:true,
onEnter:function(els){{gsap.fromTo(els,{{opacity:0,y:rise}},{{opacity:1,y:0,duration:ms('reveal'),ease:'power2.out',stagger:ms('stagger'),overwrite:true}});}}}});
}});
</script>"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">')


def tokens_css():
    """Compile design/tokens.json into CSS custom properties."""
    out = [f"/* Generated from design/tokens.json ({TOKENS['name']}). Do not edit. */", ":root {"]
    for t in TOKENS["color"]["tokens"]:
        out.append(f"  --{t['name']}: {t['value']};")
    for fam, stack in TOKENS["type"]["families"].items():
        out.append(f"  --font-{fam}: {stack};")
    for g in TOKENS["type"]["groups"]:
        for s in g["styles"]:
            out.append(f"  --{s['name']}-size: {s['fontSize']};")
            out.append(f"  --{s['name']}-lh: {s['lineHeight']};")
            out.append(f"  --{s['name']}-weight: {s['fontWeight']};")
            if "letterSpacing" in s:
                out.append(f"  --{s['name']}-ls: {s['letterSpacing']};")
    for fam in ("spacing", "radius", "border", "layout", "motion"):
        for t in TOKENS.get(fam, {}).get("tokens", []):
            out.append(f"  --{t['name']}: {t['value']};")
    out.append("}")
    return "\n".join(out) + "\n"


def goal_href(g):
    return f'/{g["slug"]}/' if g.get("page") else f'/#goals-{g["slug"]}'


def goals_strip(heading, skip=None):
    """The goals strip (pages.md, Category and Letters; owner task 2 Nov 2026): a heading and one row of btn-line links to
    the goal pages, each labelled with the goal's `label`; a goal page leaves itself out (`skip`)."""
    links = "".join(f'<a class="btn btn-line btn-sm" href="/{g["slug"]}/">{g["label"]}</a>'
                    for g in ALL_GOALS if g.get("page") and g["slug"] != skip)
    return f"""
<section class="section goals-strip" id="other-goals">
  <div class="wrap">
    <h2 class="h-sources">{heading}</h2>
    <div class="btn-row">{links}</div>
  </div>
</section>""" if links else ""


def nav_items(path):
    # Design book, Pages and buttons, Header (owner, 1 Nov 2026): "Peptides by goal" (a menu of the seven goals: a goal
    # with its own page links there, the others to Home with the goal chosen, /#goals-<slug>), then Legal status, FDA
    # letters (the letters page once it exists, else Home's section), How we rate, About. Learn comes back when guides exist.
    current = ' aria-current="page"'
    goals = "".join(f'<li><a href="{goal_href(g)}">{g["label"]}</a></li>' for g in ALL_GOALS)
    # "Sellers" after "Peptides by goal" once the seller pages exist (pages.md, Seller; owner task 2 Nov 2026)
    items = [("/sellers/", "Sellers")] if PROFILES else []
    items += [("/#legal", "Legal status"), (LETTERS_URL, "FDA letters"), ("/how-we-rate/", "How we rate"), ("/about/", "About")]
    return (f'<div class="nav-goals"><button type="button" class="nav-goals-btn" aria-expanded="false" aria-controls="goal-menu">Peptides by goal</button>'
            f'<span class="nav-group">Peptides by goal</span><ul class="goal-menu" id="goal-menu">{goals}</ul></div>'
            + "".join(f'<a href="{href}"{current if href == path else ""}>{label}</a>' for href, label in items))


def crumbs(items):
    if not items:
        return ""
    parts = ['<a href="/">Home</a>']
    for href, label in items[:-1]:
        parts.append(f'<a href="{href}">{label}</a>')
    parts.append(f"<span aria-current=\"page\">{items[-1][1]}</span>")
    return '<nav class="crumbs wrap" aria-label="Breadcrumb">' + '<span aria-hidden="true">/</span>'.join(parts) + "</nav>"


def og_name(path):
    name = "home" if path == "/" else path.strip("/").replace("/", "-")
    # a seller added to the database after tools/og.py last ran shares the /sellers/ image until og.py runs again
    if path.startswith("/sellers/") and not (ROOT / "assets" / "og" / f"{name}.png").exists():
        return "sellers"
    return name


FEED_LINK = '\n<link rel="alternate" type="application/rss+xml" title="FDA warning letters to peptide sellers" href="/fda-warning-letters/feed.xml">'


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
<link rel="canonical" href="{canonical}">{FEED_LINK if LETTERS_ALL and path in ("/", "/fda-warning-letters/") else ""}
<meta property="og:type" content="website">
<meta property="og:site_name" content="Peptide Chooser">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#1a2330">
<link rel="icon" href="/assets/favicon-32.png" sizes="32x32" type="image/png">
<link rel="icon" href="/assets/favicon-16.png" sizes="16x16" type="image/png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png" sizes="180x180">
<link rel="manifest" href="/site.webmanifest">
{FONTS}
<link rel="stylesheet" href="/assets/tokens.css">
<link rel="stylesheet" href="/assets/bundle.css">
<link rel="stylesheet" href="/assets/site.css">
{schema}
{MOTION_HEAD}
{NAV_HEAD}
{ANALYTICS}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="notice"><div class="wrap"><span>We compare, we don't sell.</span><span class="more">Some links pay us. <a href="/disclosure/">How we make money</a></span></div></div>
<header class="site-head">
  <div class="wrap">
    <a class="brand" href="/"><img src="/assets/logo.svg" alt="" width="50" height="20">Peptide Chooser</a>
    <nav class="nav" id="site-nav" aria-label="Main">{nav_items(path)}</nav>
    <div class="head-cta"><a class="btn btn-ink" href="/#goals">Compare by goal</a></div>
    <button type="button" class="btn btn-line btn-sm nav-toggle" aria-expanded="false" aria-controls="site-nav">Menu</button>
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
        <a class="brand" href="/"><img src="/assets/logo-dark.svg" alt="" width="50" height="20">Peptide Chooser</a>
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
{COOKIE_BAR}
{NAV_JS}
{MOTION_JS}
</body>
</html>
"""


ORG_SCHEMA = f"""<script type="application/ld+json">
{{"@context":"https://schema.org","@graph":[
{{"@type":"Organization","@id":"{SITE}/#org","name":"Peptide Chooser","url":"{SITE}/","logo":"{SITE}/assets/icon-512.png","email":"{EMAIL}"}},
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


def visit(g, small=False):
    """The paid Visit button for a goal: a sponsored /out/ link with "Paid link" under it once data/site.json has the
    goal's affiliate url, until then a disabled span (no link, no rel) with "No paid link yet" under it."""
    size = " btn-sm" if small else ""
    a = g.get("affiliate") or {}
    if a.get("url") and a.get("name"):
        return (f'<a class="btn btn-action{size}" href="/out/{a["name"]}/" rel="sponsored">Online clinic</a>'
                f'<span class="paid">Paid link</span>')
    return f'<span class="btn btn-action{size}" role="button" aria-disabled="true">Online clinic</span><span class="paid">No paid link yet</span>'


def top_pick(g):
    """The goal's best proven option: the first FDA-approved one in its options (or its chooser options when it has
    no comparison page), else the one marked best. Returns (name, status chip html, option) or None."""
    if g.get("options"):
        items = [(o, o["name"], o["fda"], status_chip(o, "fda_chip", "fda")) for o in g["options"]]
    else:
        items = [(p, p["name"].replace(" (proven alternative)", ""), p["status"], status_chip(p)) for p in g["peptides"]]
    # top_pick: false keeps an option out (e.g. tesamorelin: approved, but not for the goal's use)
    rows = [(name, status, item.get("best"), chip, item) for item, name, status, chip in items if item.get("top_pick", True)]
    pick = next((r for r in rows if r[1].startswith("FDA approved")), None) or next((r for r in rows if r[2]), None)
    return (pick[0], pick[3], pick[4]) if pick else None


def sold_peptide(g):
    """For a goal with no top pick: its most asked-about peptide, the first not-approved option (database chip when
    there is one) that research-use shops sell, since the card says so. Returns (name, status chip html) or None."""
    for item in g.get("options") or g["peptides"]:
        s = db_status(item["substance"]) if item.get("substance") else None
        chip = s["chip"] if s else item.get("chip", item.get("fda_chip"))
        if chip == "neutral" and "research-use" in (item.get("does", "") + " " + item.get("how", "")).lower():
            return item["name"], status_chip(item) if "chip" in item else status_chip(item, "fda_chip", "fda")
    return None


def goal_rows():
    """"Compare by goal" (owner, 1 Nov 2026: one table for all seven goals, replacing "Top pick per goal"): the goal,
    its best proven option (the top-pick rule), the price where a priced option or plan exists, the FDA status chip,
    "Compare" for a goal with its own page, and Visit for a goal with an approved option."""
    rows = []
    for g in ALL_GOALS:
        pick = top_pick(g)
        if pick:
            option, chip = f'<span class="name">{pick[0]}</span>', pick[1]
        else:
            sold = sold_peptide(g)
            option = '<span class="note">No FDA-approved option</span>' + (f'<span class="name">{sold[0]}</span><span class="note">Sold by research-use shops; we do not link to them.</span>' if sold else "")
            chip = sold[1] if sold else ""
        price = ""
        if g["slug"] in PRICE_REF:
            n = PRICE_REF[g["slug"]]
            price = (f'<span class="num-l">${g["price_from_usd"]}<span class="num-unit">/mo</span></span>'
                     f'<sup><a class="ref" href="#src-price-{g["slug"]}" aria-label="Source {n}">{n}</a></sup><span class="note">{g["price_note"]}</span>')
        elif pick and opt_price(pick[2], g["slug"]):
            price = opt_price(pick[2], g["slug"])
        price += plan_line(g, "note")
        compare = f'<a class="btn btn-ink btn-sm" href="/{g["slug"]}/">Compare</a>' if g.get("page") else ""
        act = f'<span class="pick-act">{visit(g, small=True)}</span>' if pick else ""
        rows.append(f"""<tr>
  <td>{f'<a class="name" href="/{g["slug"]}/">{g["label"]}</a>' if g.get("page") else f'<span class="name">{g["label"]}</span>'}</td>
  <td>{option}</td>
  <td>{price}</td>
  <td>{chip}</td>
  <td class="act">{compare}</td>
  <td class="act">{act}</td>
</tr>""")
    return "\n".join(rows)


COMPARE_TH = '<th scope="col"><span class="vh">Compare</span></th><th scope="col"><span class="vh">Online clinic</span></th>'
ALL_GOALS = DATA["goals"]
LEGAL = DATA["legal"]
CREATORS = DATA["creators"]
SOURCES_HOME = "".join(
    f'<li id="src-{s["n"]}">{s["text"]}: <a href="{s["url"]}" rel="nofollow">{s["url"]}</a></li>' for s in LEGAL["sources"]
) + "".join(f'<li id="src-price-{g["slug"]}">{g["price_source_name"]}: <a href="{g["price_source"]}" rel="nofollow">{g["price_source"]}</a></li>' for g in LIVE_GOALS)
# Price sources follow the legal ones in the same numbered list, so a price's footnote number is its place there.
PRICE_REF = {g["slug"]: len(LEGAL["sources"]) + i + 1 for i, g in enumerate(LIVE_GOALS)}
# An option can carry its own price source (data: price_source with name, url, checked); those come last.
OPT_SOURCES = [p for g in ALL_GOALS for p in g["peptides"] if p.get("price_source")]
SOURCES_HOME += "".join(f'<li id="src-opt-{i + 1}">{p["price_source"]["name"]}, {nice_date(p["price_source"]["checked"])}: '
                        f'<a href="{p["price_source"]["url"]}" rel="nofollow">{p["price_source"]["url"]}</a></li>' for i, p in enumerate(OPT_SOURCES))
OPT_REF = {id(p): (len(LEGAL["sources"]) + len(LIVE_GOALS) + i + 1, f"opt-{i + 1}") for i, p in enumerate(OPT_SOURCES)}

# Online-clinic plans from the database (site.plan_prices, tools/pull_data.py). A goal's substances are the `substance`
# of its options; its plan line shows the cheapest monthly plan among them, with the plan page as its footnote source and
# the day we last saw that price. A goal with no plan row shows nothing (owner, 31 Oct 2026). Compounded plans are left
# out: the line sits under an FDA-approved option, and a pharmacy-made copy is not that product (owner, 31 Oct 2026).
PLANS = DATA.get("plans") or []


def cheapest_plan(g):
    subs = {p["substance"] for p in g["peptides"] if p.get("substance")}
    found = [r for r in PLANS if r["substance_slug"] in subs and r.get("price_monthly") is not None
             and r.get("product_kind") != "compounded"]
    return min(found, key=lambda r: (float(r["price_monthly"]), r["seller_name"])) if found else None


GOAL_PLANS = {g["slug"]: cheapest_plan(g) for g in ALL_GOALS}
GOAL_PLANS = {k: v for k, v in GOAL_PLANS.items() if v}
_n0 = len(LEGAL["sources"]) + len(LIVE_GOALS) + len(OPT_SOURCES)
PLAN_REF = {slug: _n0 + i + 1 for i, slug in enumerate(GOAL_PLANS)}
seller_base = lambda name: re.sub(r"\s*\(.*\)", "", name).strip()  # "Strut Health (Strut Health, LLC)" -> "Strut Health"
SOURCES_HOME += "".join(f'<li id="src-plan-{slug}">{seller_base(r["seller_name"])}, {r["plan_name"]}, {nice_date(r["last_seen"])}: '
                        f'<a href="{r["pricing_url"]}" rel="nofollow">{r["pricing_url"]}</a></li>' for slug, r in GOAL_PLANS.items())


def usd(v):
    """$60, $149.50, $74.99: whole dollars without cents."""
    v = float(v)
    return f"${v:,.0f}" if v == int(v) else f"${v:,.2f}"


# A goal's clinic plans (pages.md, Category, weight loss; owner task 2 Nov 2026): the rows of site.plan_prices whose
# substance is one of the goal's `clinic_plans.substances`, and, with `programs`, the plans that name no medication.
BRANDED = ("branded", "oral_branded")


def clinic_plans(g):
    cp = g.get("clinic_plans")
    if not cp:
        return []
    rows = [r for r in PLANS if r.get("price_monthly") is not None
            and (r["substance_slug"] in cp["substances"] or (r["substance_slug"] is None and cp.get("programs")))]
    return sorted(rows, key=lambda r: (float(r["price_monthly"]), r["seller_name"], r["plan_name"]))


def other_use(g, r):
    """A brand plan whose brand is approved for another use (`clinic_plans.other_use`, e.g. Ozempic: diabetes), or ""."""
    return next((use for brand, use in (g.get("clinic_plans") or {}).get("other_use", {}).items()
                 if r.get("product_kind") in BRANDED and r["plan_name"].split()[0] == brand), "")


def row_plan(g, p):
    """The plan behind an option row's "Online clinics from" line on a goal with clinic plans: an FDA-approved row, the
    cheapest brand plan (branded or oral_branded) of its substance; the compounded row (`plan_kind`), the cheapest
    compounded plan of the goal's approved substances. None for other rows."""
    rows = clinic_plans(g)
    if p.get("plan_kind") == "compounded":
        subs = {x["substance"] for x in g["peptides"] if x.get("substance") and x["status"].startswith("FDA approved")}
        found = [r for r in rows if r.get("product_kind") == "compounded" and r["substance_slug"] in subs]
    elif p.get("substance") and p["status"].startswith("FDA approved"):
        found = [r for r in rows if r["substance_slug"] == p["substance"] and r.get("product_kind") in BRANDED
                 and not other_use(g, r)]
    else:
        return None
    return found[0] if found else None


# Plans shown on a row or a price pad that are not a goal's GOAL_PLANS plan get their own source after the plan sources.
plan_key = lambda r: f'{r["seller_slug"]}-{r["plan_slug"]}'
EXTRA_PLANS = {}
for _g in ALL_GOALS:
    _rows = clinic_plans(_g)
    for _r in [row_plan(_g, _p) for _p in _g["peptides"]] + _rows[:1]:
        if _r and _r is not GOAL_PLANS.get(_g["slug"]):
            EXTRA_PLANS.setdefault(plan_key(_r), _r)
_n1 = _n0 + len(GOAL_PLANS)
EXTRA_REF = {k: _n1 + i + 1 for i, k in enumerate(EXTRA_PLANS)}
SOURCES_HOME += "".join(f'<li id="src-plan-{k}">{seller_base(r["seller_name"])}, {r["plan_name"]}, {nice_date(r["last_seen"])}: '
                        f'<a href="{r["pricing_url"]}" rel="nofollow">{r["pricing_url"]}</a></li>' for k, r in EXTRA_PLANS.items())


def plan_ref(g, r):
    """The source id and number of a plan row."""
    if r is GOAL_PLANS.get(g["slug"]):
        return f"src-plan-{g['slug']}", PLAN_REF[g["slug"]]
    return f"src-plan-{plan_key(r)}", EXTRA_REF[plan_key(r)]


def plan_line(g, cls, r=None):
    """"Online clinics from $25/mo (Strut Health)" with its footnote: the goal's plan, or the plan row given; "" when
    there is none."""
    r = r or GOAL_PLANS.get(g["slug"])
    if not r:
        return ""
    sid, n = plan_ref(g, r)
    return (f'<span class="{cls}">Online clinics from {usd(r["price_monthly"])}/mo ({seller_base(r["seller_name"])})'
            f'<sup><a class="ref" href="#{sid}" aria-label="Source {n}">{n}</a></sup></span>')

# Numbers from the database (tools/pull_data.py writes these keys when SITE_DATABASE_URL is set). Without them the
# page renders the hand-written statuses and dates above, unchanged.
DB = DATA.get("db")
LEGAL_DB = DATA.get("legal_db")
APPROVED_DB = DATA.get("approved_db") or []
_plan_seen = max((r["last_seen"] for r in GOAL_PLANS.values()), default="")
_prices_on = DB.get("prices_checked_on", "") if DB else ""
STAMP_CHECKED = nice_date(max(_prices_on, _plan_seen)) if (_prices_on or _plan_seen) else CHECKED
# The one lookup from a database status to what the page shows: (regime, status_value) -> (rank, chip, label, sentence).
# Lower rank wins when a substance has several open statuses. Statuses not listed here (shortage, not_listed) are
# not legal statuses and are skipped.
DB_STATUS = {
    ("fda_approval", "approved"): (0, "ok", "FDA approved", "an FDA-approved product exists"),
    ("fda_cat2_safety", "category_2"): (1, "neutral", "Not approved", "on the FDA list of substances that may be unsafe to compound"),
    ("fda_503a_category", "category_2"): (2, "neutral", "Not approved", "the FDA found safety concerns; pharmacies may not compound it"),
    ("fda_503a_category", "category_3"): (3, "neutral", "Not approved", "nominated for compounding without enough data; pharmacies may not compound it"),
    ("fda_nomination_withdrawn", "withdrawn"): (4, "neutral", "Not approved", "its nomination for pharmacy compounding was withdrawn"),
    ("fda_503a_category", "category_1"): (5, "warn", "Pharmacy-made", "pharmacies may compound it while the FDA reviews it; no approved product"),
}


def brand_base(name):
    """"Mounjaro (Autoinjector)" and "Mounjaro Kwikpen" are both Mounjaro: the first word, without the bracket, title case."""
    words = [w for w in re.sub(r"\(.*?\)", "", name).split() if w.upper() not in ("MEN'S", "WOMEN'S")]
    return words[0].title()


def db_status(slug):
    """The substance's winning open status from the database, or None."""
    rows = [(DB_STATUS[(r["regime"], r["status_value"])], r) for r in LEGAL_DB or []
            if r["substance_slug"] == slug and (r["regime"], r["status_value"]) in DB_STATUS]
    if not rows:
        return None
    (rank, chip, label, sentence), row = min(rows, key=lambda x: x[0][0])
    # generic products carry the substance's own name as their brand; those are not brands (Finasteride -> Propecia, Proscar)
    generic = row["canonical_name"].split()[0].title()
    brands = sorted({brand_base(a["brand_name"]) for a in APPROVED_DB if a["substance_slug"] == slug and a.get("brand_name")} - {generic})[:4]
    name = row["canonical_name"] + (f' ({", ".join(brands)})' if brands and chip == "ok" else "")
    return {"chip": chip, "label": label, "sentence": sentence, "name": name, "url": row["source_url"],
            "seen": row["first_seen_by_us"]}


def status_chip(item, chip_key="chip", label_key="status"):
    """An option's status chip: the database's when it has a row for the substance, else the hand-written one. A cosmetic
    product (hand chip "info") keeps its own chip: the database status is for the substance as a drug, e.g. injectable
    GHK-Cu, not for a serum sold as a cosmetic (owner, 31 Oct 2026)."""
    s = db_status(item["substance"]) if item.get("substance") and item.get(chip_key) != "info" else None
    return f'<span class="chip chip-{s["chip"]}">{s["label"]}</span>' if s else f'<span class="chip chip-{item[chip_key]}">{item[label_key]}</span>'


def refs(item, goal, price=True):
    """Footnote links for the numbers in an option's copy (rulebook: no number without its source). price=False leaves
    out the price sources, for a row whose price pad links its own."""
    ns = [(n, n) for n in item.get("src", [])]
    if price:
        ns += ([(PRICE_REF[goal], "price-" + goal)] if item.get("price") in PRICE_REF else []) + ([OPT_REF[id(item)]] if id(item) in OPT_REF else [])
    return (" <sup>" + ", ".join(f'<a href="#src-{a}">{n}</a>' for n, a in ns) + "</sup>") if ns else ""


def plain_status(item, drop_price=False):
    """The plain status line. A price written in the copy is shown only when its source is on the page, and is left out
    when the row's price pad already shows it (drop_price)."""
    s = item["status_plain"]
    if "$" in s and (drop_price or not (item.get("price") or item.get("price_source"))):
        s = " ".join(part for part in s.replace(". ", ".\n").split("\n") if "$" not in part)
    return s

# The body figure is our own drawing (design book: no stock art): a front view, eight heads tall, in a 240 x 480
# box. The right half is listed and mirrored, then smoothed. Each goal shades its body area and has a pin.
def body_path():
    r = [(128, 52), (130, 74), (146, 80), (164, 88), (175, 100), (178, 118), (179, 150), (181, 182), (185, 214), (188, 244),
         (192, 262), (191, 280), (185, 288), (179, 284), (176, 266), (172, 248), (167, 216), (162, 184), (158, 150), (154, 128),
         (151, 150), (146, 192), (150, 224), (155, 250), (155, 284), (150, 322), (145, 348), (147, 378), (142, 416), (138, 446),
         (146, 462), (142, 472), (126, 472), (124, 458), (125, 440), (124, 404), (126, 378), (125, 350), (126, 316), (122, 276)]
    pts = r + [(120, 270)] + [(240 - x, y) for x, y in reversed(r)]
    f = lambda v: ("%.1f" % v).rstrip("0").rstrip(".")
    d = "M%s %s" % (f(pts[0][0]), f(pts[0][1]))
    for i in range(len(pts)):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % len(pts)], pts[(i + 2) % len(pts)]
        c = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6, p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6, *p2)
        d += " C%s %s %s %s %s %s" % tuple(map(f, c))
    return d + "Z"


BODY_D = body_path()
HEAD = '<ellipse cx="120" cy="34" rx="21" ry="27"'
# Body area per goal: shaded ellipses (cx, cy, rx, ry), clipped to the body, and where its pin sits.
REGIONS = {
    "hair": ([(120, 14, 24, 12)], (120, 13)),
    "skin": ([(120, 40, 17, 15)], (120, 42)),
    "muscle": ([(168, 128, 13, 26), (72, 128, 13, 26)], (72, 126)),
    "longevity": ([(131, 134, 13, 12)], (131, 134)),
    "weight-loss": ([(120, 204, 28, 24)], (120, 204)),
    "libido": ([(120, 258, 22, 12)], (120, 258)),
    "recovery": ([(136, 352, 13, 14), (104, 352, 13, 14)], (136, 352)),
}


def figure_svg():
    regions, pins = [], []
    for i, g in enumerate(ALL_GOALS):
        shapes, (px, py) = REGIONS[g["slug"]]
        on = "true" if i == 0 else "false"
        cls = " on" if i == 0 else ""
        regions += [f'<ellipse class="region{cls}" data-goal="{g["slug"]}" cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}"/>' for cx, cy, rx, ry in shapes]
        pins.append(f'<g class="pin{cls}" data-goal="{g["slug"]}" role="button" tabindex="0" aria-pressed="{on}" aria-label="{g["label"]}">'
                    f'<circle class="pin-hit" cx="{px}" cy="{py}" r="24"/><circle class="pin-ring" cx="{px}" cy="{py}" r="9"/>'
                    f'<circle class="pin-dot" cx="{px}" cy="{py}" r="4.5"/></g>')
    # The neck's top edge sits inside the head; the mask keeps it from drawing a line across the chin.
    return (f'<svg class="fig" viewBox="0 0 240 480" role="group" aria-label="Choose a goal on the body">'
            f'<defs><clipPath id="body-clip"><path d="{BODY_D}"/>{HEAD}/></clipPath>'
            f'<mask id="no-head"><rect x="-10" y="-10" width="260" height="500" fill="#fff"/>{HEAD} fill="#000"/></mask></defs>'
            f'<g class="body"><path d="{BODY_D}"/>{HEAD}/></g>'
            f'<g clip-path="url(#body-clip)">{"".join(regions)}</g>'
            f'<g class="contour"><path pathLength="1" mask="url(#no-head)" d="{BODY_D}"/>{HEAD} pathLength="1"/></g>'
            f'{"".join(pins)}</svg>')


# Research-use sellers per substance (site.products and site.sellers, tools/pull_data.py keeps each seller's cheapest
# listing, ten per substance). The seller window (pages.md, Home) shows them with their background check; seller names
# are plain text and nothing in the window links to a seller (owner, 31 Oct 2026; tools/check.py enforces it).
PRODUCTS = DATA.get("products") or []
SELLERS = {r["seller_slug"]: r for r in DATA.get("sellers") or []}
# Seller pages (pages.md, Seller): one per seller in site.seller_profile, through tools/pull_data.py
PROFILES = {r["seller_slug"]: r for r in DATA.get("seller_profiles") or []}


def clean(t):
    """Sellers' product names as text the site may show: no em or en dashes, single spaces."""
    return " ".join(str(t).replace("\u2014", "-").replace("\u2013", "-").split())


def money(v):
    return f"${v:,.2f}"


def month_year(iso):
    d = date.fromisoformat(iso)
    return d.strftime("%b %Y")


def substance_name(slug):
    """The window heading: the name readers already see for the substance (owner, 31 Oct 2026), never the slug: the
    "Is it legal today?" row for that substance alone, else the database's name for it, else the shortest option name
    that carries it."""
    row = next((r["peptide"] for r in LEGAL["rows"] if r.get("substances") == [slug]), None)
    db = next((r["canonical_name"] for r in LEGAL_DB or [] if r["substance_slug"] == slug), None)
    opts = [p["name"] for g in ALL_GOALS for p in g["peptides"] if slug in subs_of(p)]
    return row or db or min(opts, key=len)


def seller_rows(slug):
    """The listings for one substance, one per seller (its cheapest by price per mg, blends and unknown amounts last).
    The rows are sorted by the seller's score, high first, then by how many products it lists, more first, then by name
    (owner, 2 Nov 2026); a seller without a score goes last."""
    key = lambda r: (r.get("price_per_mg") is None, r.get("price_per_mg") or 0, r.get("price_usd") or 0, r["seller_slug"])
    best = {}
    for r in sorted((r for r in PRODUCTS if r["substance_slug"] == slug), key=key):
        best.setdefault(r["seller_slug"], r)
    def order(r):
        s = SELLERS.get(r["seller_slug"], {})
        return (-(s.get("score") if s.get("score") is not None else -1), -(s.get("product_count") or 0),
                clean(s.get("seller_name") or r["seller_name"]).lower())
    return sorted(best.values(), key=order)


# The seller score (pages.md, Seller window, owner 2 Nov 2026): five yes/no checks from site.sellers, in this order, with
# the short name each mark carries. Facts we hold about the seller, never a safety or quality grade.
SCORE_CHECKS = [("score_lab_testing", "Lab reports"), ("score_no_fda_letter", "No FDA letter"),
                ("score_registered_company", "Company found"), ("score_legal_pages", "Legal pages"),
                ("score_fresh_prices", "Fresh prices")]


def score_line(r):
    """"N of 5 checks" with the five checks as small marks in one line: met chip-ok, not met chip-neutral with a dashed
    ink-muted border, so the state never rests on colour alone (owner answer Q1 a, 2 Nov 2026; it is also spoken).
    Nothing when the seller has no score yet."""
    s = SELLERS.get(r["seller_slug"], {})
    if s.get("score") is None:
        return ""
    marks = "".join(f'<span class="chip chip-{"ok" if s.get(k) else "neutral"} mark-{"yes" if s.get(k) else "no"}">{t}'
                    f'<span class="vh">: {"yes" if s.get(k) else "no"}</span></span>' for k, t in SCORE_CHECKS)
    return (f'<span class="score"><span class="score-n"><span class="num">{s["score"]}</span> of {len(SCORE_CHECKS)} checks</span>'
            f'<span class="score-marks">{marks}</span></span>')


def check_chips(r):
    """The six-point background check of one seller row: a chip each, never a blank."""
    s = SELLERS.get(r["seller_slug"], {})
    chip = lambda k, t: f'<span class="chip chip-{k}">{t}</span>'
    coa = chip("ok", f"This product: COA yes ({r.get('coa_count') or 0})") if r.get("has_coa") else chip("warn", "This product: no COA")
    n = s.get("fda_letter_count")
    letters = chip("neutral", "FDA warning letters: unknown") if n is None else (
        chip("ok", "FDA warning letters: none") if n == 0 else chip("warn", f"FDA warning letters: {n}"))
    company = (chip("ok", "Company: " + ", ".join(x for x in (s.get("legal_entity_name"), s.get("registry_state")) if x))
               if s.get("legal_entity_name") else chip("neutral", "Company: not verified"))
    st = r.get("seller_status")
    status = chip("ok" if st == "active" else "neutral", f"Status: {st or 'unknown'}")
    first = chip("neutral", f"First seen: {month_year(s['first_seen']) if s.get('first_seen') else 'unknown'}")
    seen = r.get("price_observed_at") or r.get("last_seen")
    checked = chip("neutral", f"Price checked: {nice_date(seen) if seen else 'unknown'}")
    return f'<span class="chips">{coa}{letters}{company}{status}{first}{checked}</span>'


def seller_table(slug):
    """One substance's sellers as a table, its source lines and its newest last_seen. No link to a seller."""
    rows = seller_rows(slug)
    newest = max((r["last_seen"] for r in rows if r.get("last_seen")), default="")
    scored = max((SELLERS.get(r["seller_slug"], {}).get("score_checked_on") or "" for r in rows), default="")
    trs, src = [], []
    for r in rows:
        name = clean(r["product_name"])
        variant = clean(r["variant_title"]) if r.get("variant_title") and r["variant_title"] != "Default Title" else ""
        if variant and variant.lower() not in name.lower():
            name += f", {variant}"
        size = f'{r["amount_mg"]:g} mg' if r.get("amount_mg") else "size unknown"
        price = money(r["price_usd"]) if r.get("price_usd") is not None else "unknown"
        ppm = (f'{money(r["price_per_mg"])}/mg' if r.get("price_per_mg") is not None else "blend" if r.get("is_blend") else "unknown")
        seller = clean(SELLERS.get(r["seller_slug"], {}).get("seller_name") or r["seller_name"])
        # the name opens our page on the seller when it has one (owner task 2 Nov 2026); never the seller's own site
        name_html = (f'<a class="name" href="/sellers/{r["seller_slug"]}/">{seller}</a>' if r["seller_slug"] in PROFILES
                     else f'<span class="name">{seller}</span>')
        trs.append(f'<tr><td>{name_html}</td><td data-l="Product">{name}<span class="sub">{size}</span></td>'
                   f'<td data-l="Price"><span class="num">{price}</span></td><td data-l="Per mg"><span class="num">{ppm}</span></td>'
                   f'<td class="checks">{score_line(r)}{check_chips(r)}</td></tr>')
        seen = r.get("price_observed_at") or r.get("last_seen")
        src.append(f'<li>{seller}, {name}{", " + nice_date(seen) if seen else ""}: {r["product_url"]}</li>')
    table = (f'<div class="tbl-wrap"><table class="tbl"><thead><tr><th scope="col">Seller</th><th scope="col">Product</th>'
             f'<th scope="col">Price</th><th scope="col">Per mg</th><th scope="col">Background check</th></tr></thead>'
             f'<tbody>{"".join(trs)}</tbody></table></div>')
    return table, src, newest, scored


def subs_of(p):
    """An option's substances for the seller window: its `substance`, or its `substances` list (a row that stands for
    several research-use peptides, e.g. "Injectable peptides sold for hair"; owner, 1 Nov 2026)."""
    return [p["substance"]] if p.get("substance") else list(p.get("substances") or [])


def window_key(p):
    return "sellers-" + "-".join(s for s in subs_of(p) if seller_rows(s))


def seller_window(p):
    """One seller window for an option row (a dialog; a plain section with JavaScript off). One substance: its table
    under the substance name. Several: the option's name as the heading and one table per substance under the
    substance name as a sub-heading. No Visit, no link to a seller."""
    subs = [s for s in subs_of(p) if seller_rows(s)]
    key = window_key(p)
    parts, src, newest, scored = [], [], "", ""
    for s in subs:
        table, lines, seen, sc = seller_table(s)
        parts.append((f'<h3 class="dlg-sub">{substance_name(s)}</h3>' if len(subs) > 1 else "") + table)
        src += lines
        newest, scored = max(newest, seen), max(scored, sc)
    title = substance_name(subs[0]) if p.get("substance") else p["name"]
    checked = f" Prices checked {nice_date(newest)}." if newest else ""
    return f"""<dialog class="sellers-dlg" id="{key}" aria-labelledby="{key}-h"><div class="dlg-in">
  <div class="dlg-hd"><h2 id="{key}-h">{title}</h2><form method="dialog"><button class="btn btn-line btn-sm" type="submit">Close</button></form></div>
  <p class="dlg-lede">Research-use sellers. We do not link to them.{checked}</p>
  {"".join(parts)}
  <p class="dlg-foot">Price per mg is price divided by the stated amount; blends have no per-mg price.</p>
  {f'<p class="dlg-foot dlg-score">Checks are facts we hold about the seller, not a safety or quality grade. Checked {nice_date(scored)}.</p>' if scored else ""}
  <ol class="dlg-src">{"".join(src)}</ol>
</div></dialog>"""


def approved_row(p):
    """An FDA-approved option (hand status or database status). Its row gets no seller window: we do not send people
    from an approved medicine to research-use sellers (owner, 31 Oct 2026)."""
    s = db_status(p["substance"]) if p.get("substance") else None
    return p["status"].startswith("FDA approved") or bool(s and s["label"] == "FDA approved")


def has_window(p):
    return not approved_row(p) and any(seller_rows(s) for s in subs_of(p))


# One window per distinct set of substances (two rows for the same substance share it).
SELLER_WINDOWS = "".join({window_key(p): seller_window(p) for g in ALL_GOALS for p in g["peptides"] if has_window(p)}.values())


def sellers_button(p):
    """"Prices at N shops" on a research-use option row with listings, N the distinct sellers across its substances;
    a link to the window without JS. FDA-approved rows never get it."""
    if not has_window(p):
        return ""
    n = len({r["seller_slug"] for s in subs_of(p) for r in seller_rows(s)})
    key = window_key(p)
    return (f'<a class="btn btn-line btn-sm sellers-open" href="#{key}" data-dlg="{key}">'
            f'Prices at {n} shop{"s" if n != 1 else ""}</a>')


def opt_price(p, slug):
    """The price on an option row, only where its price has a source in data/site.json (the goal's price source for the
    option marked price, or the option's own price_source with price_from_usd), with its footnote. Returns html or ""."""
    if p.get("price") in PRICE_REF:
        g = next(x for x in LIVE_GOALS if x["slug"] == p["price"])
        usd, n, href = g["price_from_usd"], PRICE_REF[p["price"]], f"#src-price-{slug}"
    elif p.get("price_source") and p.get("price_from_usd") is not None and id(p) in OPT_REF:
        usd, n, href = p["price_from_usd"], OPT_REF[id(p)][0], f"#src-{OPT_REF[id(p)][1]}"
    else:
        return ""
    # the source and its check date are in the numbered list under the page; the footnote links there (owner, 31 Oct 2026)
    return f'<span class="price-pad">from ${usd}/mo</span><sup><a class="ref" href="{href}" aria-label="Source {n}">{n}</a></sup>'


def price_sentence(p, pad):
    """The option's price as a sentence for its "how" line, with the footnote of its source: the price sentence of
    `status_plain` when the copy has one ("From $10/mo (generic, pharmacy coupon)."), else "From $X/mo."."""
    if not pad:
        return ""
    sup = re.search(r"<sup>.*</sup>", pad).group(0)
    said = " ".join(x for x in p["status_plain"].replace(". ", ".\n").split("\n") if "$" in x).strip()
    if not said:
        said = re.search(r"from \$[\d.,]+/mo", pad).group(0).capitalize() + "."
    return f" {said}{sup}"


def alt_chip(p):
    """"Proven alternative" (chip-info) after the status chip, for an option that is not a peptide but is in the list
    as the proven choice (`proven_alternative` in data/site.json); "Not a peptide" (chip-neutral) for one sold
    alongside peptides that is not one (`not_peptide`) (owner, 1 Nov 2026)."""
    if p.get("proven_alternative"):
        return '<span class="chip chip-info">Proven alternative</span>'
    return '<span class="chip chip-neutral">Not a peptide</span>' if p.get("not_peptide") else ""


def option_rows(g):
    """One goal's step 2 option rows (pages.md, Home, step 2; also /hair/): name and chips; opened, the does, status
    and how lines, the price and plan line ending the how line; "Prices at N shops" for research-use rows, "Online clinic" on
    every FDA-approved row."""
    slug = g["slug"]
    # Each option: name and what it does; status chip and status in plain words; price pad and how you get it
    # (docs/copy-home-2026-10-30.md): one line on wide screens, three short lines on phones.
    # Every FDA-approved option (not marked top_pick: false) gets the goal's "Online clinic" button on its own row, so
    # each approved medicine shows where to get it (owner, 1 Nov 2026).
    approved = [p for p in g["peptides"] if p["status"].startswith("FDA approved") and p.get("top_pick", True)]
    rows = []
    for p in g["peptides"]:
        pad = opt_price(p, slug)
        # The price and the goal's cheapest online-clinic plan are the last items of the "how" line, with their
        # footnotes; the right side of the row keeps only the button (owner, 1 Nov 2026).
        plan = GOAL_PLANS.get(slug)
        # a goal with clinic plans (weight loss) gives each row its own plan (row_plan); the others keep the goal's one plan
        rp = row_plan(g, p) if g.get("clinic_plans") else (plan if plan and p.get("substance") == plan["substance_slug"] else None)
        cost = price_sentence(p, pad) + (" " + plan_line(g, "plan-in", rp).replace(")<sup>", ").<sup>", 1) if rp else "")
        sb = sellers_button(p)
        act = (f'<span class="pick-act">{sb}{visit(g, small=True)}</span>' if p in approved else
               f'<span class="pick-act">{sb}</span>' if sb else
               # a row with no button says why in one grey line where the button would be (owner, 1 Nov 2026)
               f'<span class="pick-act"><span class="paid no-link">{p["no_link"]}</span></span>' if p.get("no_link") else "")
        rows.append(f'<li class="opt"><details class="opt-more"><summary class="opt-sum"><span class="name">{p["name"]}</span>'
                    f'<span class="opt-chips">{status_chip(p)}{alt_chip(p)}</span></summary>'
                    f'<div class="opt-body"><p class="opt-does">{p["does"]}{refs(p, slug, price=not pad)}</p>'
                    f'<p class="opt-status">{plain_status(p, drop_price=bool(pad))}</p><p class="opt-how">{p["how"]}{cost}</p></div></details>{act}</li>')
    return rows


def rail():
    """The flow (design book, pages.md, Home): the goal rows, then per goal the option list, where the top pick's row
    carries the Visit button. Every goal's options are in the page; only the first goal's show until another is chosen."""
    chips, compare = [], []
    for i, g in enumerate(ALL_GOALS):
        slug, hide = g["slug"], "" if i == 0 else " hidden"
        chips.append(f'<button type="button" class="goal-item" data-goal="{slug}" aria-pressed="{"true" if i == 0 else "false"}" '
                     f'aria-controls="opts-{slug}"><span>{g["label"]}</span><span class="small">{len(g["peptides"])} options</span></button>')
        rows = option_rows(g)
        link = (f'<a class="btn btn-ink" href="/{slug}/">Compare {g["short"].lower()} options</a>' if g.get("page") else
                '<p class="small">Full comparison for this goal is not published yet. The legal status above is current as of ' + CHECKED + '.</p>')
        compare.append(f'<div class="step-panel" id="opts-{slug}" data-goal="{slug}" data-title="{g["panel_title"]}"{hide}><p class="goal-for">{g["for"]}</p>'
                       f'<p class="goal-intro" tabindex="0" title="{g["intro"]}">{g["intro"]}</p>'
                       f'<ul class="opts">{"".join(rows)}</ul>'
                       f'{link}</div>')
    # The chosen goal's panel title follows the step name in the step 2 heading (ODOBRENO SEO 30 Oct 2026, copy doc
    # section 2); the page carries the first goal's, the goal switch puts in the next one.
    return "".join(chips), "".join(compare), f'<span class="goal-t">: {ALL_GOALS[0]["panel_title"]}</span>'


def legal_rows(only=None):
    """"Is it legal today?": each hand-written row, or, when the database has a status for its substances, one row per
    substance from the database with its own source link and the date we first saw that status. `only` keeps the rows
    for those substances (a goal page shows the rows for its own options)."""
    keep = lambda slugs: only is None or bool(set(slugs) & only)
    hand = lambda r: (f'<tr><td><span class="name">{r["peptide"]}</span></td><td><span class="chip chip-{r["chip"]}">{r["status"]}</span></td>'
                      f'<td>{r["note"]} <a class="ref" href="#src-{r["src"]}" aria-label="Source {r["src"]}"><sup>{r["src"]}</sup></a></td></tr>')
    out, seen = [], []
    for r in LEGAL["rows"]:
        if not keep(r.get("substances", [])):
            continue
        found = [db_status(slug) for slug in r.get("substances", [])] if LEGAL_DB else []
        if not found or not all(found):
            if not r.get("db_only"):  # a db_only row (finasteride, minoxidil) is shown only from the database
                out.append(hand(r))  # a row switches to the database only when every substance in it has a status there
            continue
        for slug, s in zip(r["substances"], found):
            if not keep([slug]):
                continue
            seen.append(s["seen"])
            # A row marked note_with_db keeps its hand-written note (e.g. the July 2026 PCAC proposal) as a second sentence.
            n = r.get("note_each", r.get("note", ""))  # the note for one substance when a grouped row splits ("them" -> "it")
            note = (f'. {n[0].upper() + n[1:]}. <a class="ref" href="#src-{r["src"]}" aria-label="Source {r["src"]}">'
                    f'<sup>{r["src"]}</sup></a>') if r.get("note_with_db") else ""
            out.append(f'<tr><td><span class="name">{s["name"]}</span></td><td><span class="chip chip-{s["chip"]}">{s["label"]}</span></td>'
                       f'<td>{s["sentence"]}{" " + r["use"] if r.get("use") else ""} <a class="ref" href="{s["url"]}" rel="nofollow">FDA source</a>, {nice_date(s["seen"])}{note}</td></tr>')
    # Every other substance with a database status gets its own row (owner, 1 Nov 2026: the table lists every substance
    # the database has a status for, plus the hand rows it lacks), then all rows are sorted by name.
    shown = {slug for r in LEGAL["rows"] for slug in r.get("substances", [])
             if all(db_status(x) for x in r.get("substances", [])) and LEGAL_DB}
    for slug in sorted({r["substance_slug"] for r in LEGAL_DB or []} - shown):
        s = db_status(slug)
        if not s or not keep([slug]):
            continue
        seen.append(s["seen"])
        out.append(f'<tr><td><span class="name">{s["name"]}</span></td><td><span class="chip chip-{s["chip"]}">{s["label"]}</span></td>'
                   f'<td>{s["sentence"]} <a class="ref" href="{s["url"]}" rel="nofollow">FDA source</a>, {nice_date(s["seen"])}</td></tr>')
    out.sort(key=lambda row: re.sub(r"<[^>]+>", "", row.split("</td>")[0]).strip().lower())
    checked = nice_date(max(seen)) if seen else nice_date(LEGAL["checked"])
    return out, checked


LEGAL_LIST, LEGAL_CHECKED = legal_rows()
LEGAL_NOTE = ("Approved means the FDA approved a product containing it for a stated use. Not approved means no approved product "
              "exists; buying it for yourself is not a crime in the US, but nobody has checked what is in the vial.")
# The first 12 rows show; the rest carry class "more" and stay hidden until "Show all N" (only with JavaScript).
LEGAL_ROWS = "".join(r if i < 12 else r.replace("<tr>", '<tr class="more">', 1) for i, r in enumerate(LEGAL_LIST))

# Latest FDA warning letters (pages.md, Home, after "Is it legal today?"): from site.seller_enforcement through
# tools/pull_data.py (site.fda_letters), newest first. Without `letters` in site.json the section is not drawn (never drawn empty).
LETTERS = DATA.get("letters") or []
LETTERS_ALL = DATA.get("letters_all") or []
LETTERS_URL = "/fda-warning-letters/" if LETTERS_ALL else "/#letters"
# Under Home's letters table (pages.md, Home, owner answer Q2 a, 2 Nov 2026): with the letters page, "See all N letters"
# and then "M of them went to sellers in our database."; without it, the old count line alone.
LETTERS_FOOT = (f'<p class="letters-all"><a class="btn btn-line" href="/fda-warning-letters/">See all {len(LETTERS_ALL)} letters</a></p>'
                + (f'<p class="small" style="margin-top:12px">{DATA["letters_total"]} of them went to sellers in our database.</p>' if DATA.get("letters_total") else "")
                if LETTERS_ALL else
                f'<p class="small" style="margin-top:16px">{DATA["letters_total"]} letters to sellers in our database since {nice_date(DATA["letters_oldest"])}.</p>'
                if DATA.get("letters_total") and DATA.get("letters_oldest") else "")
LETTER_ROWS = "".join(
    f'<tr><td class="num">{nice_date(r["letter_date"])}</td><td><span class="name">{escape(r["seller_name"])}</span>'
    f'<span class="sub-phone">{escape(r["letter_subject"]).replace("/", "/<wbr>")}</span></td><td class="subj">{escape(r["letter_subject"])}</td><td><a href="{escape(r["letter_url"])}" rel="nofollow">FDA letter</a></td></tr>' for r in LETTERS)
LETTERS_SECTION = f"""
<section class="section" id="letters">
  <div class="wrap">
    <div class="sec-hd"><div><h2>Latest FDA warning letters</h2><p>Letters the FDA sent to sellers in our database. Checked {nice_date(DATA["pulled_at"][:10])}.</p></div></div>
    <div class="tbl-wrap"><table class="tbl tbl-letters">
      <thead><tr><th scope="col">Date</th><th scope="col">Seller</th><th scope="col" class="subj">Subject</th><th scope="col">Source</th></tr></thead>
      <tbody>{LETTER_ROWS}</tbody>
    </table></div>
    {LETTERS_FOOT}
  </div>
</section>
""" if LETTERS else ""

# The letters page (pages.md, Letters, owner 1 Nov 2026): every letter in `letters_all` (site.fda_letters_all through
# tools/pull_data.py: peptide-related or sent to a seller we know), newest first. With JavaScript, a company filter and one
# chip per year above the table, and the first 25 rows until "Show all N"; without it, the whole table. Not built without
# `letters_all` (never drawn empty); the nav's "FDA letters" then keeps pointing at Home's section.
FDA_ABOUT_LETTERS = "https://www.fda.gov/inspections-compliance-enforcement-and-criminal-investigations/warning-letters/about-warning-and-close-out-letters"
LETTERS_FIRST = 25


def office(t):
    """The issuing office as the FDA writes it, one spelling per office ("Center for ... | CDER" reads "(CDER)")."""
    return re.sub(r"\s*\|\s*([A-Z]+)$", r" (\1)", clean(t or ""))


def office_cell(t):
    """The Office column (owner, 2 Nov 2026): the short form in brackets at the end of the name ("CDER"), the full name
    as its title; the full name alone when it has no bracket."""
    full = office(t)
    m = re.search(r"\(([^()]+)\)$", full)
    return f'<td class="office" title="{escape(full)}">{escape(m.group(1))}</td>' if m else f'<td class="office">{escape(full)}</td>'


def letters_all_rows():
    out, more = [], ' class="more"'
    for i, r in enumerate(LETTERS_ALL):
        seller = f'<span class="co-seller">In our database: {escape(clean(r["seller_name"]))}</span>' if r.get("seller_slug") and r.get("seller_name") else ""
        subj = escape(clean(r["letter_subject"]))
        out.append(
            f'<tr{more if i >= LETTERS_FIRST else ""} data-year="{r["letter_date"][:4]}"><td class="num">{nice_date(r["letter_date"])}</td>'
            f'<td><span class="name">{escape(clean(r["company_name"]))}</span>{seller}<span class="sub-phone">{subj.replace("/", "/<wbr>")}</span></td>'
            f'<td class="subj">{subj.replace("/", "/<wbr>")}</td>{office_cell(r.get("issuing_office"))}'
            f'<td><a href="{escape(r["letter_url"])}" rel="nofollow">FDA letter</a></td></tr>')
    return "".join(out)


LETTERS_YEARS = sorted({r["letter_date"][:4] for r in LETTERS_ALL}, reverse=True)
YEAR_CHIPS = "".join(
    f'<button type="button" class="year-chip" data-year="{y}" aria-pressed="false">{y} <span>{sum(r["letter_date"][:4] == y for r in LETTERS_ALL)}<span class="vh"> letters</span></span></button>'
    for y in LETTERS_YEARS)
LETTERS_PAGE_JS = """<script>
(function(){var tb=document.getElementById('letters-table');if(!tb)return;var f=document.querySelector('.letters-filter'),q=document.getElementById('letters-q'),
c=document.getElementById('letters-clear'),m=document.querySelector('.letters-more'),all=document.getElementById('letters-all'),n=document.getElementById('letters-n'),
chips=[].slice.call(document.querySelectorAll('.year-chip')),rows=[].slice.call(tb.tBodies[0].rows),open=false;
function draw(){var s=q.value.trim().toLowerCase(),ys=chips.filter(function(x){return x.getAttribute('aria-pressed')==='true';}).map(function(x){return x.getAttribute('data-year');}),k=0;
rows.forEach(function(r){var hit=(!s||r.cells[1].textContent.toLowerCase().indexOf(s)>=0)&&(!ys.length||ys.indexOf(r.getAttribute('data-year'))>=0);
r.hidden=!hit||(!open&&!s&&!ys.length&&r.classList.contains('more'));if(hit)k++;});
if(m)m.hidden=open||!!s||ys.length>0;n.textContent=(s||ys.length)?k+' of '+rows.length+' letters match.':'';}
f.hidden=false;if(m)m.hidden=false;q.addEventListener('input',draw);
chips.forEach(function(x){x.addEventListener('click',function(){x.setAttribute('aria-pressed',x.getAttribute('aria-pressed')==='true'?'false':'true');draw();});});
c.addEventListener('click',function(){q.value='';chips.forEach(function(x){x.setAttribute('aria-pressed','false');});draw();q.focus();});
if(all)all.addEventListener('click',function(){open=true;draw();});draw();})();
</script>"""
# Get new letters (pages.md, Letters, owner 2 Nov 2026): one white card under the explanation line with the RSS feed and a
# plain form that posts to Buttondown (double opt-in, set in the Buttondown account). Not drawn while
# `newsletter.buttondown` in data/site.json is empty (never drawn empty).
BUTTONDOWN = (DATA.get("newsletter") or {}).get("buttondown", "")
FEED_PATH = "/fda-warning-letters/feed.xml"
FEED_N = 50
SUBSCRIBE_BOX = f"""<section class="subscribe" aria-labelledby="sub-h">
      <h2 id="sub-h">Get new letters</h2>
      <p>New FDA warning letters to peptide sellers, by email or RSS. No ads, no selling of data.</p>
      <form class="sub-form" action="https://buttondown.com/api/emails/embed-subscribe/{escape(BUTTONDOWN)}" method="post" target="_blank">
        <label for="sub-email">Your email</label>
        <div class="sub-row"><input class="input" type="email" id="sub-email" name="email" autocomplete="email" required><button class="btn btn-ink" type="submit">Subscribe</button><a class="btn btn-line" href="{FEED_PATH}">RSS feed</a></div>
      </form>
      <p class="small">Double opt-in. Unsubscribe in one click.</p>
    </section>""" if BUTTONDOWN else ""


def rss_date(iso):
    d = date.fromisoformat(iso)
    return d.strftime("%a, %d %b %Y 00:00:00 +0000")


def letters_feed():
    """RSS 2.0 of the newest FEED_N letters on the letters page (owner, 2 Nov 2026): title "<company>: <subject>", the link
    and guid are the letter on fda.gov, the description holds the date, company, subject, office and our seller match."""
    items = []
    for r in LETTERS_ALL[:FEED_N]:
        company, subj = clean(r["company_name"]), clean(r["letter_subject"])
        desc = f"{nice_date(r['letter_date'])}. {company}. {subj}. {office(r.get('issuing_office'))}."
        if r.get("seller_slug") and r.get("seller_name"):
            desc += f" In our database: {clean(r['seller_name'])}."
        items.append(f"<item><title>{escape(company)}: {escape(subj)}</title><link>{escape(r['letter_url'])}</link>"
                     f"<guid isPermaLink=\"true\">{escape(r['letter_url'])}</guid><pubDate>{rss_date(r['letter_date'])}</pubDate>"
                     f"<description>{escape(desc)}</description></item>")
    built = rss_date(DATA["pulled_at"][:10]) if DATA.get("pulled_at") else rss_date(LETTERS_ALL[0]["letter_date"])
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>'
            f'<title>FDA warning letters to peptide sellers (Peptide Chooser)</title><link>{SITE}/fda-warning-letters/</link>'
            f'<atom:link href="{SITE}{FEED_PATH}" rel="self" type="application/rss+xml"/>'
            '<description>New FDA warning letters to peptide sellers, compounders and online clinics, with a link to each letter on fda.gov.</description>'
            f'<language>en-us</language><lastBuildDate>{built}</lastBuildDate>{"".join(items)}</channel></rss>\n')


LETTERS_PAGE = f"""
<section class="section letters-hd">
  <div class="wrap">
    <h1>FDA warning letters to peptide sellers and online clinics</h1>
    <p class="lede">A warning letter is the FDA's formal notice that it found what it believes are significant violations of the law; the company is asked to reply within 15 business days. It is public record. <a href="{FDA_ABOUT_LETTERS}" rel="nofollow">What the FDA says about warning letters</a></p>
    <p class="letters-stamp"><span class="stamp">Checked {nice_date(DATA["pulled_at"][:10]) if DATA.get("pulled_at") else ""}</span><span class="small">{len(LETTERS_ALL)} letters since {nice_date(DATA["letters_all_oldest"]) if DATA.get("letters_all_oldest") else ""}, newest first. Each links to the letter on fda.gov.</span></p>
    {SUBSCRIBE_BOX}
  </div>
</section>
<section class="band-2" id="letters-list">
  <div class="wrap">
    <div class="letters-filter" hidden>
      <div class="legal-filter"><label for="letters-q">Filter by company</label><input class="input" id="letters-q" type="text" autocomplete="off"><button type="button" class="btn btn-line btn-sm" id="letters-clear">Clear</button></div>
      <div class="year-chips" role="group" aria-labelledby="letters-years"><span id="letters-years">Year</span>{YEAR_CHIPS}</div>
      <p class="small" id="letters-n" aria-live="polite"></p>
    </div>
    <div class="tbl-wrap"><table class="tbl tbl-letters tbl-letters-all" id="letters-table"><caption class="vh">FDA warning letters, newest first</caption>
      <thead><tr><th scope="col">Date</th><th scope="col">Company</th><th scope="col" class="subj">Subject</th><th scope="col" class="office">Office</th><th scope="col">Source</th></tr></thead>
      <tbody>{letters_all_rows()}</tbody>
    </table></div>
    {f'<p class="letters-more" hidden><button type="button" class="btn btn-line" id="letters-all">Show all {len(LETTERS_ALL)}</button></p>' if len(LETTERS_ALL) > LETTERS_FIRST else ""}
    <p class="small" style="margin-top:16px">Company names are as the FDA lists them. "In our database" names the seller we matched the letter to.</p>
  </div>
</section>{goals_strip("Compare peptides by goal")}
{LETTERS_PAGE_JS}
""" if LETTERS_ALL else ""
FIGURE = figure_svg()
GOAL_CHIPS, STEP_COMPARE, GOAL_TITLES = rail()
def chip_title(t):
    return f'<span class="chip chip-{t["chip"]}">{t["term"]}</span>' if t.get("chip") else t["term"]


# Each label's title carries the chip the option rows use for that status (`chip` in data/site.json); "Is it safe?" has none.
GLOSSARY = "".join(
    f'<div><dt>{chip_title(t)}</dt><dd>{t["text"]}</dd></div>' for t in DATA["glossary"])

CREATOR_ROWS = "".join(
    f'<li><a href="{c["url"]}" rel="nofollow noopener">{c["name"]}</a><span class="small">{c["what"]}</span></li>' for c in CREATORS["rows"])

# "Is it legal today?" (pages.md, Home): with JavaScript, a name filter above the table and only the first 12 rows until
# "Show all N"; typing shows every matching row. Without JavaScript the whole table shows and the controls stay hidden.
LEGAL_JS = """<script>
(function(){var tb=document.getElementById('legal-table');if(!tb)return;var f=document.querySelector('.legal-filter'),q=document.getElementById('legal-q'),
c=document.getElementById('legal-clear'),m=document.querySelector('.legal-more'),all=document.getElementById('legal-all'),rows=[].slice.call(tb.tBodies[0].rows),open=false;
function draw(){var s=q.value.trim().toLowerCase();rows.forEach(function(r){var name=r.cells[0].textContent.toLowerCase();
r.hidden=s?name.indexOf(s)<0:(!open&&r.classList.contains('more'));});if(m)m.hidden=open||!!s;}
f.hidden=false;if(m)m.hidden=false;q.addEventListener('input',draw);
c.addEventListener('click',function(){q.value='';draw();q.focus();});
if(all)all.addEventListener('click',function(){open=true;draw();});draw();})();
</script>"""

# The seller window (pages.md, Home): with JavaScript the windows hide until "Compare N sellers" opens one as a modal
# dialog (Esc and "Close" are the dialog's own; a click on the dimmed area outside closes it; focus returns to the button).
SELLERS_JS = """<script>
(function(){if(!window.HTMLDialogElement)return;document.documentElement.classList.add('sellers-js');
document.addEventListener('click',function(e){var b=e.target.closest('.sellers-open');if(b){var d=document.getElementById(b.getAttribute('data-dlg'));
if(d){e.preventDefault();d.showModal();}return;}
var d=e.target.closest('.sellers-dlg');if(d&&e.target===d)d.close();});})();
</script>"""

# The goal switch (design book, pages.md, Home, the three steps): chips and pins are one control. Steps 2 and 3
# cross-fade (GSAP, motion-swap) only while motion is on; otherwise they swap at once. The stamp lands once.
MAP_JS = """<script>
(function(){var root=document.getElementById('goals');if(!root)return;
var chips=[].slice.call(root.querySelectorAll('.goal-item')),cur=chips[0].getAttribute('data-goal');
var swapS=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--motion-swap'))/1000||0.2;
root.addEventListener('animationend',function(e){if(e.target.classList.contains('stamp'))root.classList.add('landed');});
function show(k){root.querySelectorAll('.step-panel').forEach(function(x){x.hidden=x.getAttribute('data-goal')!==k;if(!x.hidden)root.querySelector('.goal-t').textContent=': '+x.getAttribute('data-title');});
if(!window.pcMotion)return;var on=root.querySelectorAll('.step-panel[data-goal="'+k+'"]');
gsap.fromTo(on,{opacity:0},{opacity:1,duration:swapS,ease:'power1.out'});
gsap.fromTo(root.querySelectorAll('.step-panel[data-goal="'+k+'"] .opt'),{opacity:0,y:4},{opacity:1,y:0,duration:swapS,ease:'power1.out',stagger:0.04});}
function pick(k){if(k===cur)return;cur=k;
root.querySelectorAll('.goal-item,.pin,.region').forEach(function(x){var on=x.getAttribute('data-goal')===k;
if(x.hasAttribute('aria-pressed'))x.setAttribute('aria-pressed',on?'true':'false');x.classList.toggle('on',on);});
var old=root.querySelectorAll('.step-panel:not([hidden])');
if(window.pcMotion&&old.length){gsap.killTweensOf(old);gsap.to(old,{opacity:0,duration:swapS/2,ease:'power1.in',onComplete:function(){gsap.set(old,{opacity:1});if(cur===k)show(k);}});}else{show(k);}}
function hover(k){root.querySelectorAll('.region,.pin').forEach(function(x){x.classList.toggle('hov',x.getAttribute('data-goal')===k);});}
root.addEventListener('click',function(e){var b=e.target.closest('.goal-item,.pin');if(b)pick(b.getAttribute('data-goal'));});
root.addEventListener('mouseover',function(e){var b=e.target.closest('.goal-item,.pin');hover(b?b.getAttribute('data-goal'):null);});
root.addEventListener('mouseleave',function(){hover(null);});
root.addEventListener('keydown',function(e){var t=e.target;
if(t.classList&&t.classList.contains('pin')&&(e.key==='Enter'||e.key===' ')){e.preventDefault();pick(t.getAttribute('data-goal'));return;}
// Arrow keys move to the next or previous chip and choose it (Tab, Enter and Space work as on any button).
var i=chips.indexOf(t);if(i<0)return;var d={ArrowRight:1,ArrowDown:1,ArrowLeft:-1,ArrowUp:-1}[e.key];if(!d)return;
e.preventDefault();var n=chips[(i+d+chips.length)%chips.length];n.focus();pick(n.getAttribute('data-goal'));});
// /#goals-<slug> (the header's goal menu) chooses that goal on load and when the hash changes.
function fromHash(){var m=location.hash.match(/^#goals-([a-z0-9-]+)$/);
if(m&&root.querySelector('.goal-item[data-goal="'+m[1]+'"]')){pick(m[1]);root.scrollIntoView();}}
fromHash();window.addEventListener('hashchange',fromHash);})();
</script>"""

HOME = f"""
<section class="hero hero-clinic">
  <div class="wrap">
    <h1 class="hero-h1">The best peptides for your goal, compared honestly.</h1>
    <div class="chooser flow" id="goals">
      <div class="flow-hd fh-goal"><span class="step-n" aria-hidden="true">1</span><h2 id="step-goal">Choose a goal</h2></div>
      <div class="figure">{FIGURE}</div>
      <div class="goal-list" role="group" aria-labelledby="step-goal">{GOAL_CHIPS}</div>
      <div class="flow-hd fh-compare"><span class="step-n" aria-hidden="true">2</span><h2>Compare the options{GOAL_TITLES}</h2><a class="step-legal" href="#legal"><strong>Is it legal today?</strong></a></div>
      <div class="flow-compare">{STEP_COMPARE}</div>
    </div>
  </div>
</section>
<section class="hero-more">
  <div class="wrap">
    <div class="hero-pair">
    <p class="what-is"><strong>What is a peptide?</strong> A short chain of amino acids. Some are approved medicines (semaglutide, bremelanotide), some are cosmetics in creams, and many are sold online with no approval and no testing. This site tells you which is which, what it costs, and what the proven alternative is.</p>
    <p class="lede hero-after">For each goal we put peptide products next to the FDA-approved alternatives and show what the evidence says, what it costs per month and how you would get it. We compare; we never sell.</p>
    </div>
    <section class="glossary" aria-labelledby="glossary-h">
      <h2 id="glossary-h">What the labels mean</h2>
      <dl class="glossary-list">{GLOSSARY}</dl>
    </section>
    <section class="rate-strip" aria-labelledby="rate-h">
      <div class="rate-hd"><h2 id="rate-h">How we rate</h2><p>Every product and seller is judged on the same five criteria. We publish them so you can check our work.</p><a href="/how-we-rate/">Read the full method</a></div>
      <ul class="criteria">
        <li><h3>Evidence</h3><p>What human studies show for the use you care about, not what a molecule does in a dish.</p></li>
        <li><h3>Regulatory status</h3><p>FDA approval, cosmetic or research labeling, and any FDA warning letters sent to the seller.</p></li>
        <li><h3>Lab testing</h3><p>Whether a third-party certificate of analysis exists and matches the batch you would receive.</p></li>
        <li><h3>Real price</h3><p>Price per month or per milligram, calculated the same way for every seller so the numbers compare.</p></li>
        <li><h3>Transparency</h3><p>Who runs the company, where it ships from, and whether paid placements are labeled.</p></li>
      </ul>
      <nav class="trust-links" aria-label="How we work"><a href="/disclosure/">How we make money</a><a href="/about/">Who checks our facts</a><a href="/corrections/">Mistakes we fixed</a><a href="#sources">Sources</a></nav>
    </section>
  </div>
</section>

<section class="section" id="compare">
  <div class="wrap">
    <div class="sec-hd"><div><h2>Compare by goal</h2><p>One row per goal. The best proven option is the cheapest one the FDA has approved for that use.</p></div></div>
    <div class="tbl-wrap"><table class="tbl">
      <thead><tr><th scope="col">Goal</th><th scope="col">Best proven option</th><th scope="col">Price from</th><th scope="col">FDA status</th>{COMPARE_TH}</tr></thead>
      <tbody>{goal_rows()}</tbody>
    </table></div>
    <p class="small" style="margin-top:16px">{STANDING_LINE}</p>
  </div>
</section>

<section class="band-2" id="legal">
  <div class="wrap">
    <div class="sec-hd"><div><h2>Is it legal today?</h2><p>FDA status of the peptides people ask about most, each with its source. Checked {LEGAL_CHECKED}.</p></div></div>
    <div class="legal-filter" hidden><label for="legal-q">Filter by name</label><input class="input" id="legal-q" type="text" autocomplete="off"><button type="button" class="btn btn-line btn-sm" id="legal-clear">Clear</button></div>
    <div class="tbl-wrap"><table class="tbl tbl-legal" id="legal-table">
      <thead><tr><th scope="col">Peptide</th><th scope="col">Status</th><th scope="col">What that means</th></tr></thead>
      <tbody>{LEGAL_ROWS}</tbody>
    </table></div>
    {f'<p class="legal-more" hidden><button type="button" class="btn btn-line btn-sm" id="legal-all">Show all {len(LEGAL_LIST)}</button></p>' if len(LEGAL_LIST) > 12 else ""}
    <p class="small" style="margin-top:16px">{LEGAL_NOTE}</p>
  </div>
</section>

{LETTERS_SECTION}

<section class="section" id="learn">
  <div class="wrap">
    <div class="sec-hd"><div><h2>Who to follow</h2><p>{CREATORS["note"]}</p></div></div>
    <ul class="creators">{CREATOR_ROWS}</ul>
    <p class="small" style="margin-top:16px">Reviewed {nice_date(CREATORS["checked"])}. Links open YouTube; we earn nothing from them.</p>
  </div>
</section>

<div class="wrap sellers-all">{SELLER_WINDOWS}</div>

<section class="section" id="sources">
  <div class="wrap">
    <h2 class="h-sources">Sources</h2>
    <ol class="small sources" style="padding-left:1.2em">{SOURCES_HOME}</ol>
  </div>
</section>
{MAP_JS}
{SELLERS_JS}
{LEGAL_JS}
"""

CORRECTIONS = f"""
<section class="page"><div class="wrap prose">
<h1>Mistakes we fixed</h1>
<p class="lede">Every factual error we correct is listed here with the date, what was wrong and what we changed.</p>
<p>No corrections have been needed yet. The site went live in October 2026. If you find an error, email <a href="mailto:{EMAIL}">{EMAIL}</a> with a source; we check within a few days and list the fix here.</p>
<p class="small">Last checked {CHECKED}.</p>
</div></section>
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

# The newsletter paragraph (owner, 2 Nov 2026; Tier 1): only while the subscribe box exists.
PRIVACY_NEWSLETTER = ('<li><strong>Email alerts, only if you sign up.</strong> If you sign up for new FDA warning letters, we ask only for your email '
                      'address. Buttondown, our email provider, stores it and sends the emails on our behalf; when you sign up it also records '
                      'technical data such as your IP address, under its own <a href="https://buttondown.com/legal/privacy" rel="nofollow noopener">privacy policy</a>. '
                      'You get a confirmation email first, and nothing is sent until you confirm (double opt-in). Every email has a link to '
                      'unsubscribe in one click; after that we send nothing more. We never sell or share the list.</li>\n') if BUTTONDOWN and LETTERS_ALL else ""
PRIVACY = f"""
<section class="page"><div class="wrap prose">
<h1>Privacy policy</h1>
<p class="small meta">Last updated {CHECKED}</p>
<p>This policy explains what information Peptide Chooser ("we") collects when you visit peptidechooser.com and how we use it.</p>
<h2>Information we collect</h2>
<ul>
<li><strong>Email you send us.</strong> If you contact us, we receive your email address and whatever you include in your message. We use it only to reply.</li>
<li><strong>Server logs.</strong> Our hosting provider (GitHub Pages) may record technical data such as IP address, browser type and the pages requested, for security and to operate the service. We do not use this data to identify you.</li>
<li><strong>Analytics, only if you accept.</strong> We use Google Analytics 4 to count visits and see which pages people find useful. It runs only after you press "Accept" on the cookie notice. If you press "Reject", no analytics cookie is set and nothing is sent to Google. Google processes this data under its own <a href="https://policies.google.com/privacy" rel="nofollow noopener">privacy policy</a>. We do not use advertising trackers, and we do not sell or share visitor data.</li>
{PRIVACY_NEWSLETTER}</ul>
<h2>Cookies</h2>
<p>The site sets one small value in your browser to remember your cookie choice. Google Analytics sets its own cookies (named _ga and similar) only after you accept. You can change your mind by clearing the site's data in your browser; the notice will then appear again.</p>
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

def page_sources(rows_html, own):
    """The Home source entries an option row on another page links to (price, option and plan sources), kept under
    their Home numbers so a footnote reads the same everywhere. A row may not link a number the page uses itself."""
    used = list(dict.fromkeys(re.findall(r'href="#(src-[^"]+)"[^>]*>(?:<sup>)?(\d+)', rows_html)))
    clash = {i for i, _ in used} & own
    assert not clash, f"option rows link sources that this page numbers differently: {clash}"
    out = []
    for sid, n in sorted(used, key=lambda x: int(x[1])):
        m = re.search(rf'<li id="{sid}">(.*?)</li>', SOURCES_HOME)
        if m:
            out.append(f'<li value="{n}" id="{sid}">{m.group(1)}</li>')
    return "".join(out)


def peptide_table(g):
    """"Every option, side by side" for a goal with no hand-checked `options` table: its step 2 rows, each with the three
    lay lines (does; status chip and status_plain; how). No evidence or price column: those need checked data that the
    goal does not have yet, and nothing is typed into the page to fill them (pages.md, Category)."""
    rows = []
    for p in g["peptides"]:
        rows.append(f"""<tr>
  <td><span class="name">{p["name"]}</span>{alt_chip(p)}<span class="opt-does">{p["does"]}{refs(p, g["slug"])}</span></td>
  <td>{status_chip(p)}<span class="opt-status">{plain_status(p)}</span></td>
  <td>{p["how"]}</td>
</tr>""")
    return ('<thead><tr><th scope="col">Option</th><th scope="col">FDA status</th><th scope="col">How you get it</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody>')


def category_page(g):
    if not g.get("options"):
        return category_body(g, peptide_table(g), f"{len(g['peptides'])} options, each with its FDA status and how you get it.")
    rows = []
    for o in g["options"]:
        src_refs = (" <sup>" + ", ".join(f'<a href="#src-{n}">{n}</a>' for n in o["sources"]) + "</sup>") if o["sources"] else ""
        price = (f'<span class="num-l">{o["price"]}<span class="num-unit">{o["price_unit"]}</span></span><span class="note">{o["price_note"]}</span>'
                 if o["price"] else f'<span class="note">{o["price_note"]}</span>')
        rows.append(f"""<tr>
  <td><span class="name">{o["name"]}{src_refs}</span><span class="note">{o["kind"]}</span><span class="opt-does">{o["does"]}</span></td>
  <td>{status_chip(o, "fda_chip", "fda")}<span class="opt-status">{o["status_plain"]}</span></td>
  <td><span class="chip chip-{o["evidence_chip"]}">{o["evidence"]}</span></td>
  <td>{price}</td>
  <td>{o["how_plain"]}</td>
</tr>""")
    table = ('<thead><tr><th scope="col">Option</th><th scope="col">FDA status for hair loss</th><th scope="col">Evidence in people</th><th scope="col">Price from</th><th scope="col">How you get it</th></tr></thead>\n'
             f'      <tbody>{"".join(rows)}</tbody>')
    return category_body(g, table, f'{g["options_checked"]} options checked on the same five criteria. Rows that are not approved for human use carry no price and no seller.')


KIND_CHIP = {"brand": ("ok", "Brand"), "compounded": ("warn", "Compounded"), "program": ("neutral", "Program")}


def plan_chip(g, r):
    """What a plan is, as a chip: "Brand, diabetes" (chip-info) for a brand approved for another use (owner answer Q1 a,
    2 Nov 2026: Ozempic is approved for diabetes, not weight loss), else the KIND_CHIP of its kind."""
    use = other_use(g, r)
    chip, label = ("info", f"Brand, {use}") if use else KIND_CHIP[plan_kind(r)]
    return f'<span class="chip chip-{chip}">{label}</span>'


def plan_kind(r):
    """"program" for a plan that names no medication, "brand" for branded or oral_branded, else "compounded"."""
    return "program" if not r["substance_slug"] else "brand" if r.get("product_kind") in BRANDED else "compounded"


def care_note(r):
    """"+ $99/mo care" when the plan adds a monthly membership, "all-in" when it adds none, "care fee not known" when the
    data has no fee (owner answer Q3 b, 2 Nov 2026)."""
    fee = r.get("membership_fee_monthly")
    return "care fee not known" if fee is None else "all-in" if float(fee) == 0 else f"+ {usd(fee)}/mo care"


CLINICS_FIRST = 10
# With JavaScript the clinic table is clipped on phones (CSS hides tr.more under .clip) and "Show all N" opens it; without
# JavaScript every row shows and the button stays hidden.
CLINICS_JS = """<script>(function(){var s=document.getElementById('clinics'),m=s&&s.querySelector('.clinics-more');if(!m)return;
s.classList.add('clip');m.hidden=false;document.getElementById('clinics-all').addEventListener('click',function(){s.classList.remove('clip');m.hidden=true;});})();</script>"""


def clinic_section(g, rows):
    """"Online clinic prices" (pages.md, Category, weight loss; owner task 2 Nov 2026): one row per plan, cheapest first;
    the clinic in plain text (no link to any clinic site), its FDA letter linking to our letters page, and the disabled
    "Online clinic" button until a paid link exists per seller. Stacked cards on phones (bundle.css, Clinic table)."""
    if not rows:
        return ""
    newest = max(r["last_seen"] for r in rows)
    trs = []
    for i, r in enumerate(rows):
        care = care_note(r)
        n = r.get("fda_letter_count") or 0
        letter = (f'<a class="chip chip-warn chip-link" href="{LETTERS_URL}">FDA letter {nice_date(r["last_fda_letter_date"])}</a>'
                  if n and r.get("last_fda_letter_date") else '<span class="no-letter">none</span>')
        # on phones the first CLINICS_FIRST rows show until "Show all N" (owner answer Q2 a, 2 Nov 2026; bundle.css, Clinic table)
        more = ' class="more"' if i >= CLINICS_FIRST else ""
        trs.append(f'<tr{more}><td><span class="name">{seller_base(r["seller_name"])}</span></td><td data-l="Plan">{r["plan_name"]}</td>'
                   f'<td>{plan_chip(g, r)}</td>'
                   f'<td data-l="Per month"><span class="num">{usd(r["price_monthly"])}</span>{f"<span class=sub>{care}</span>" if care else ""}</td>'
                   f'<td data-l="FDA letter">{letter}</td>'
                   f'<td class="act"><span class="pick-act"><span class="btn btn-action btn-sm" role="button" aria-disabled="true">Online clinic</span>'
                   f'<span class="paid">No paid link yet</span></span></td></tr>')
    return f"""
<section class="band-2" id="clinics">
  <div class="wrap">
    <div class="sec-hd"><div><h2>Online clinic prices</h2><p>{len(rows)} plans at the online clinics we track, cheapest first.</p></div></div>
    <div class="tbl-wrap"><table class="tbl tbl-cards tbl-clinics">
      <thead><tr><th scope="col">Clinic</th><th scope="col">Plan</th><th scope="col">What it is</th><th scope="col">Per month</th><th scope="col">FDA letter</th><th scope="col"><span class="vh">Online clinic</span></th></tr></thead>
      <tbody>{"".join(trs)}</tbody>
    </table></div>
    {f'<p class="clinics-more" hidden><button type="button" class="btn btn-line" id="clinics-all">Show all {len(rows)}</button></p>{CLINICS_JS}' if len(rows) > CLINICS_FIRST else ""}
    <p class="small" style="margin-top:16px">Prices are the clinics' published monthly prices on {nice_date(newest)}; "from" prices are the lowest shown. A clinic with an FDA warning letter is still listed; the letter is public record.</p>
  </div>
</section>"""


def category_body(g, table, table_lede):
    srcs = "".join(f'<li id="src-{s["n"]}">{s["text"]}: <a href="{s["url"]}" rel="nofollow">{s["url"]}</a></li>' for s in g.get("sources", []))
    # The Clinic intake look (owner, 31 Oct 2026): Home's parts on the goal page. Title, H1, description and URL stay as
    # they are (Search Console impressions); the hero keeps the price pad with its Checked stamp, the step 2 option rows
    # follow, the options table sits in the grey band.
    opt_html = "".join(option_rows(g))
    # "Is it legal today?" on the page (pages.md, Category; a goal with `legal_section`): Home's rows for the substances
    # of this goal's options, with Home's line under them; the heading line in the flow then links here.
    subs = {x for p in g["peptides"] for x in subs_of(p)}
    legal, legal_checked = legal_rows(subs) if g.get("legal_section") else ([], "")
    legal_html = f"""
<section class="section" id="legal">
  <div class="wrap">
    <div class="sec-hd"><div><h2>Is it legal today?</h2><p>FDA status of the peptides on this page, each with its source. Checked {legal_checked}.</p></div></div>
    <div class="tbl-wrap"><table class="tbl tbl-legal">
      <thead><tr><th scope="col">Peptide</th><th scope="col">Status</th><th scope="col">What that means</th></tr></thead>
      <tbody>{"".join(legal)}</tbody>
    </table></div>
    <p class="small" style="margin-top:16px">{LEGAL_NOTE}</p>
  </div>
</section>""" if legal else ""
    plans = clinic_plans(g)
    # the pad's clinic plan (a goal with clinic plans and no hand-checked price): the cheapest, with its source
    pad_plan = plans[0] if plans and not g.get("price_source") else None
    pad_sid, pad_n = plan_ref(g, pad_plan) if pad_plan else ("", 0)
    pad_ref = f'<sup><a class="ref" href="#{pad_sid}" aria-label="Source {pad_n}">{pad_n}</a></sup>' if pad_plan else ""
    own = {f'src-{s["n"]}' for s in g.get("sources", [])}
    srcs += page_sources(opt_html + legal_html + pad_ref, own)
    if plans:
        # no link to any clinic site on a page with clinic plans: the plan sources show their address as plain text
        srcs = re.sub(r'(<li value="\d+" id="src-plan-[^"]+">.*?)<a href="([^"]+)" rel="nofollow">\2</a>', r"\1\2", srcs)
    # Sources only when the page links one (never an empty heading; e.g. /muscle/, whose rows carry no footnote)
    sources_html = f"""<section class="section" id="sources">
  <div class="wrap">
    <h2 class="h-sources">Sources</h2>
    <ol class="small sources" style="padding-left:1.2em">{srcs}</ol>
  </div>
</section>""" if srcs else ""
    # The price pad only for a goal with a priced proven option and its source (skin and recovery have none yet).
    pad = f"""
      <div class="board rx" aria-label="Price pad">
        <div class="rx-head"><span class="rx-mark" aria-hidden="true">&#8478;</span><h2>Cheapest proven option, per month</h2></div>
        <p class="hero-num"><span class="num-xl">${g["price_from_usd"]}</span> <span class="num-unit">/mo from</span></p>
        <div class="ledger"><span>{g["best_option"]}</span></div>
        <div class="rx-foot"><span class="stamp">Checked {STAMP_CHECKED}</span><span class="fine">{g["price_note"]}. Not a prescription.</span></div>
      </div>""" if g.get("price_from_usd") is not None and g.get("price_source") else ""
    if pad_plan:
        # The pad shows a clinic plan when the goal has no hand-checked generic price (pages.md, Category; owner task 2 Nov 2026).
        r = pad_plan
        what = {"brand": "FDA-approved brand", "compounded": "Compounded, not FDA approved", "program": "A program; the medicine is not named"}[plan_kind(r)]
        care = care_note(r)
        pad = f"""
      <div class="board rx" aria-label="Price pad">
        <div class="rx-head"><span class="rx-mark" aria-hidden="true">&#8478;</span><h2>Cheapest clinic plan, per month</h2></div>
        <p class="hero-num"><span class="num-xl">{usd(r["price_monthly"])}</span> <span class="num-unit">/mo from</span>{pad_ref}</p>
        <div class="ledger"><span>{r["plan_name"]}, {seller_base(r["seller_name"])}</span></div>
        <div class="rx-foot"><span class="stamp">Checked {nice_date(max(x["last_seen"] for x in plans))}</span><span class="fine">{what}{", " + care if care else ""}. Not a prescription.</span></div>
      </div>"""
    windows = "".join({window_key(p): seller_window(p) for p in g["peptides"] if has_window(p)}.values())
    return f"""
<section class="hero hero-goal">
  <div class="wrap">
    <div class="hero-grid{"" if pad else " hero-solo"}">
      <div>
        <h1>{g["h1"]}</h1>
        <p class="small meta">{AUTHOR}. Last updated {CHECKED}. Every claim links to its source. Prices checked {STAMP_CHECKED}.</p>
        <p class="intro">{g["short_answer"]}</p>
      </div>{pad}
    </div>
    <div class="chooser flow flow-solo">
      <div class="flow-hd fh-compare"><h2>Compare the options</h2><a class="step-legal" href="{"#legal" if legal else "/#legal"}"><strong>Is it legal today?</strong></a></div>
      <div class="flow-compare"><div class="step-panel"><p class="goal-for">{g["for"]}</p><ul class="opts">{opt_html}</ul></div></div>
    </div>
  </div>
</section>
<section class="band-2" id="options">
  <div class="wrap">
    <div class="sec-hd"><div><h2>Every option, side by side</h2><p>{table_lede}</p></div></div>
    <div class="tbl-wrap"><table class="tbl">
      {table}
    </table></div>
  </div>
</section>{legal_html}{clinic_section(g, plans)}{goals_strip("Compare other goals", g["slug"])}
{sources_html}
<div class="wrap sellers-all">{windows}</div>
{SELLERS_JS}
"""


# Seller pages (pages.md, Sellers and Seller; owner task, phase 4d, 2 Nov 2026): /sellers/ lists every seller in
# site.seller_profile; /sellers/<slug>/ is one seller's profile. Built only from `seller_profiles` (never drawn empty).
# Nothing on them links to a seller's site (tools/check.py enforces it); every sentence comes from a field, and a missing
# field drops its sentence.
SELLER_SUBS = {}
for _r in DATA.get("seller_substances") or []:
    SELLER_SUBS.setdefault(_r["seller_slug"], []).append(_r)
SELLER_LETTERS = {}
for _r in DATA.get("seller_letters") or []:
    if _r.get("match_kind") == "domain_or_address":  # a name-only match is left out, as on Home's letters
        SELLER_LETTERS.setdefault(_r["seller_slug"], []).append(_r)
# seller_kind in plain words: in the short answer, in the index's Kind column, and the line under the check card
KIND_WORDS = {"S1_RUO": ("research-use peptide shop", "Research-use shop", "Research-use seller. We do not link to it."),
              "S4_SUPPLEMENT_COSMETIC": ("supplement and cosmetics shop", "Supplement and cosmetics shop",
                                         "Supplement and cosmetics seller. We do not link to it.")}
STATES = dict(x.split(":") for x in (
    "AL:Alabama AK:Alaska AZ:Arizona AR:Arkansas CA:California CO:Colorado CT:Connecticut DE:Delaware DC:Washington, DC "
    "FL:Florida GA:Georgia HI:Hawaii ID:Idaho IL:Illinois IN:Indiana IA:Iowa KS:Kansas KY:Kentucky LA:Louisiana ME:Maine "
    "MD:Maryland MA:Massachusetts MI:Michigan MN:Minnesota MS:Mississippi MO:Missouri MT:Montana NE:Nebraska NV:Nevada "
    "NH:New_Hampshire NJ:New_Jersey NM:New_Mexico NY:New_York NC:North_Carolina ND:North_Dakota OH:Ohio OK:Oklahoma "
    "OR:Oregon PA:Pennsylvania RI:Rhode_Island SC:South_Carolina SD:South_Dakota TN:Tennessee TX:Texas UT:Utah "
    "VT:Vermont VA:Virginia WA:Washington WV:West_Virginia WI:Wisconsin WY:Wyoming").replace("Washington, DC", "Washington,_DC").split())
STATES = {k: v.replace("_", " ") for k, v in STATES.items()}
EVIDENCE_WORDS = {"registry": "state registry", "fda_letter": "named in an FDA letter", "site": "the seller's own pages"}
SELLERS_FIRST = 25


def shown_company(r):
    """A company name we show: one from a state registry or an FDA letter, never one read off the seller's own pages."""
    return bool(r.get("entity_name")) and r.get("entity_evidence") in ("registry", "fda_letter")


def kind_words(r):
    k = r.get("seller_kind") or ""
    if k in KIND_WORDS:
        return KIND_WORDS[k]
    if "CLINIC" in k or "TELEHEALTH" in k:
        return ("online clinic", "Online clinic", "")
    if "PHARMACY" in k:
        return ("pharmacy", "Pharmacy", "Pharmacy. We do not link to it.")
    return ("seller", "Seller", "We do not link to it.")


def is_clinic(r):
    return kind_words(r)[0] == "online clinic"


def per_mg(v):
    """A price per mg as people read it: cents from $0.10 up, else two significant figures ($0.019)."""
    return f"${v:,.2f}" if v >= 0.1 else f"${v:.2g}"


def per_mg_range(lo, hi):
    if lo is None:
        return "unknown"
    return per_mg(lo) if hi is None or per_mg(lo) == per_mg(hi) else f"{per_mg(lo)} to {per_mg(hi)}"


def plural(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"


def sub_label(slug):
    """A substance's own name (not an option's): the database's name for it, else the "Is it legal today?" row for it
    alone, else the slug in readable case."""
    db = next((r["canonical_name"] for r in LEGAL_DB or [] if r["substance_slug"] == slug), None)
    row = next((r["peptide"] for r in LEGAL["rows"] if r.get("substances") == [slug]), None)
    if db or row:
        return db or row
    parts = [p.upper() if (any(c.isdigit() for c in p) or len(p) <= 3) else p for p in slug.split("-")]
    return "-".join(parts)[:1].upper() + "-".join(parts)[1:]


# a substance links to the first goal page whose options carry it
SUB_GOAL = {}
for _g in ALL_GOALS:
    if _g.get("page"):
        for _p in _g["peptides"]:
            for _s in subs_of(_p):
                SUB_GOAL.setdefault(_s, _g)


def seller_name(r):
    return clean(r["seller_name"])


def newest_letter(r):
    return max((x["letter_date"] for x in SELLER_LETTERS.get(r["seller_slug"], [])), default=r.get("last_fda_letter_date"))


def short_answer(r):
    """The short answer (pages.md, Seller; Tier 1 template): one sentence per field, a missing field drops its sentence."""
    name, (kind, _, _) = seller_name(r), kind_words(r)
    state = STATES.get(r.get("entity_state") or "") if shown_company(r) else ""  # the state of a company we show
    out = [f"{name} is a {kind}{' in ' + state if state else ''}."]
    if r.get("product_count") is not None and r.get("substance_count") is not None:
        # no "prices from" under $0.01/mg: those minimums are data errors until the database fixes them (owner answer Q6 a)
        low = r.get("price_per_mg_min")
        price = f"; prices from {per_mg(low)}/mg" if low is not None and low >= 0.01 else ""
        out.append(f"It lists {plural(r['product_count'], 'product')} across {plural(r['substance_count'], 'substance')}{price}.")
    if r.get("score_lab_testing") and r.get("coa_count") and r.get("newest_coa_date"):
        out.append(f"Lab reports: {r['coa_count']}, the newest dated {nice_date(r['newest_coa_date'])}.")
    elif r.get("score_lab_testing") is not None:
        out.append("No lab reports found in the last 12 months.")
    n = r.get("fda_letter_count")
    if n == 0:
        out.append("No FDA warning letter.")
    elif n:
        out.append(f"{plural(n, 'FDA warning letter')}, the newest on {nice_date(newest_letter(r))}.")
    # "Registered company" only with a registry match; a name from an FDA letter says so; a name from the seller's own
    # pages is not shown (owner answer Q4 a, 2 Nov 2026)
    state = STATES.get(r.get("entity_state") or "")
    if shown_company(r) and r.get("entity_evidence") == "registry":
        out.append(f"Registered company: {clean(r['entity_name'])}{' (' + state + ')' if state else ''}.")
    elif shown_company(r) and r.get("entity_evidence") == "fda_letter":
        out.append(f"Company named in an FDA letter: {clean(r['entity_name'])}.")
    else:
        out.append("No registered company found.")
    return out


def seller_title(r):
    """Title (Tier 1): the full pattern, shortened step by step to the 60 characters tools/check.py allows."""
    name = seller_name(r)
    for t in (f"{name} review: prices, lab reports, FDA letters | Peptide Chooser",
              f"{name} review: prices, lab reports, FDA letters",
              f"{name} review: prices and lab reports", f"{name} review | Peptide Chooser", f"{name} review"):
        if len(t) <= 60:
            return t
    return t


def seller_description(r):
    """Meta description: the short answer's first two sentences; a third, fourth... joins while the text is under the
    110 characters tools/check.py asks for and stays within 160."""
    out = ""
    for s in short_answer(r):
        nxt = f"{out} {s}".strip()
        if out and (len(out) >= 110 or len(nxt) > 160) and out.count(".") >= 2:
            break
        out = nxt
    return out


def check_lines(r):
    """One plain line per check for the Background check card, each with its date."""
    lab = (f"{plural(r['coa_count'], 'lab report')}, the newest dated {nice_date(r['newest_coa_date'])}."
           if r.get("score_lab_testing") and r.get("newest_coa_date") else
           f"No lab report in the last 12 months; the newest is dated {nice_date(r['newest_coa_date'])}."
           if r.get("newest_coa_date") else "No lab report found.")
    n = r.get("fda_letter_count") or 0
    letter = ("No FDA warning letter to this seller." if r.get("score_no_fda_letter") else
              f"{plural(n, 'FDA warning letter')}, the newest on {nice_date(newest_letter(r))}." if n else "FDA warning letter found.")
    company = (f"{clean(r['entity_name'])}, {STATES.get(r.get('entity_state') or '', r.get('entity_state') or '')}: "
               f"{r['registry_status']} in the state registry on {nice_date(r['registry_checked_on'])}."
               if r.get("score_registered_company") and r.get("entity_name") and r.get("registry_status") and r.get("registry_checked_on")
               else "Not found in a state registry.")
    pages = [(k, t) for k, t in (("terms", "Terms"), ("privacy", "Privacy"), ("refund", "Refund"))]
    seen = [r.get(f"{k}_seen") for k, _ in pages]
    legal = ("Terms, privacy and refund pages found." if r.get("score_legal_pages") else
             "Terms, privacy and refund pages: not checked yet." if all(s is None for s in seen) else
             "Missing: " + ", ".join(t.lower() for (k, t), s in zip(pages, seen) if not s) + " page.")
    seen_on = r.get("price_updated_at")
    fresh = (f"Prices checked {nice_date(seen_on)}." if r.get("score_fresh_prices") and seen_on else
             f"No recent price; the newest is from {nice_date(seen_on)}." if seen_on else "No price seen.")
    return dict(zip([k for k, _ in SCORE_CHECKS], (lab, letter, company, legal, fresh)))


def check_card(r):
    """Background check card (pages.md, Seller): right of the H1 like the price pad, without the ℞ mark."""
    lines = check_lines(r)
    rows = "".join(
        f'<li><span class="chip chip-{"ok" if r.get(k) else "neutral"} mark-{"yes" if r.get(k) else "no"}">{t}'
        f'<span class="vh">: {"yes" if r.get(k) else "no"}</span></span><span class="check-line">{lines[k]}</span></li>'
        for k, t in SCORE_CHECKS)
    if is_clinic(r):
        foot = '<p class="check-act"><span class="btn btn-action" role="button" aria-disabled="true">Online clinic</span><span class="paid">No paid link yet</span></p>'
    else:
        foot = f'<p class="check-nolink">{kind_words(r)[2]}</p>'
    return f"""
      <div class="board check-card" aria-labelledby="check-h">
        <div class="check-head"><h2 id="check-h">Background check</h2><p class="check-n"><span class="num-xl">{r["score"]}</span> <span class="num-unit">of {len(SCORE_CHECKS)} checks</span></p></div>
        <ul class="check-list">{rows}</ul>
        <div class="rx-foot"><span class="stamp">Checked {nice_date(r["score_checked_on"])}</span><span class="fine">Checks are facts we hold about the seller, not a safety or quality grade.</span></div>
        {foot}
      </div>"""


def seller_subs_section(r):
    rows = SELLER_SUBS.get(r["seller_slug"], [])
    if not rows:
        return ""
    trs = []
    for s in rows:
        g = SUB_GOAL.get(s["substance_slug"])
        label = escape(sub_label(s["substance_slug"]))
        name = f'<a class="name" href="/{g["slug"]}/">{label}</a>' if g else f'<span class="name">{label}</span>'
        coa = '<span class="chip chip-ok">Yes</span>' if s.get("has_coa") else '<span class="chip chip-neutral">No</span>'
        seen = s.get("newest_price_observed_at")
        trs.append(f'<tr><td>{name}</td><td class="num" data-l="Listings">{s["listing_count"]}</td>'
                   f'<td class="num" data-l="Per mg">{per_mg_range(s.get("price_per_mg_min"), s.get("price_per_mg_max"))}</td>'
                   f'<td data-l="Lab report">{coa}</td><td class="num" data-l="Price checked">{nice_date(seen[:10]) if seen else "unknown"}</td></tr>')
    total = r.get("substance_count") or len(rows)
    lede = (f"The {len(rows)} substances with the most listings, of {total}." if total > len(rows)
            else f"Every substance it lists, {plural(len(rows), 'substance')}.")
    return f"""
<section class="band-2" id="sells">
  <div class="wrap">
    <div class="sec-hd"><div><h2>What it sells</h2><p>{lede} A substance with a goal page links to it. We do not link to the products.</p></div></div>
    <div class="tbl-wrap"><table class="tbl tbl-cards tbl-sells">
      <thead><tr><th scope="col">Substance</th><th scope="col">Listings</th><th scope="col">Per mg</th><th scope="col">Lab report</th><th scope="col">Price checked</th></tr></thead>
      <tbody>{"".join(trs)}</tbody>
    </table></div>
    <p class="small" style="margin-top:16px">Per mg is the price divided by the stated amount; blends and listings without an amount have none.</p>
  </div>
</section>"""


def seller_letters_section(r):
    rows = SELLER_LETTERS.get(r["seller_slug"], [])
    if not rows:
        return ""
    trs = "".join(f'<tr><td class="num">{nice_date(x["letter_date"])}</td><td>{escape(clean(x["letter_subject"]))}</td>'
                  f'<td><a href="{escape(x["letter_url"])}" rel="nofollow">FDA letter</a></td></tr>' for x in rows)
    more = '<p class="small" style="margin-top:16px"><a href="/fda-warning-letters/">Every FDA warning letter to peptide sellers</a></p>' if LETTERS_ALL else ""
    return f"""
<section class="section" id="letters">
  <div class="wrap">
    <div class="sec-hd"><div><h2>FDA warning letters</h2><p>Letters the FDA sent to this seller, matched by its web address or street address.</p></div></div>
    <div class="tbl-wrap"><table class="tbl tbl-letters">
      <thead><tr><th scope="col">Date</th><th scope="col">Subject</th><th scope="col">Source</th></tr></thead>
      <tbody>{trs}</tbody>
    </table></div>
    {more}
  </div>
</section>"""


def company_source(r):
    """The company's source: the FDA letter as a nofollow link; the state registry as plain text. Names from the
    seller's own pages are not shown (owner answer Q4 a), so the seller is never a source here."""
    url = r.get("entity_source_url") or ""
    host = re.sub(r"^[a-z]+://", "", url).split("/")[0].lower()
    if url.startswith("https://www.fda.gov/"):
        return f'<a href="{escape(url)}" rel="nofollow">The FDA warning letter</a>'
    if host.endswith("floridados.gov"):
        return "Florida Department of State, Division of Corporations, corporate data file"
    return ""


def seller_company_section(r):
    if not shown_company(r):
        return ""
    rows = [("Name", escape(clean(r["entity_name"])))]
    if r.get("entity_state"):
        rows.append(("State", STATES.get(r["entity_state"], r["entity_state"])))
    if r.get("entity_evidence") in EVIDENCE_WORDS:
        rows.append(("Found in", EVIDENCE_WORDS[r["entity_evidence"]][:1].upper() + EVIDENCE_WORDS[r["entity_evidence"]][1:]))
    if r.get("registry_status"):
        rows.append(("Registry status", f'{r["registry_status"][:1].upper() + r["registry_status"][1:]}'
                     + (f', checked {nice_date(r["registry_checked_on"])}' if r.get("registry_checked_on") else "")))
    src = company_source(r)
    if src:
        rows.append(("Source", src))
    led = "".join(f'<div class="ledger"><span>{k}</span><span>{v}</span></div>' for k, v in rows)
    return f"""
<section class="section" id="company">
  <div class="wrap">
    <div class="sec-hd"><div><h2>Company</h2><p>The company behind the shop, and where we found it.</p></div></div>
    <div class="company-ledger">{led}</div>
  </div>
</section>"""


def similar_sellers(r, n=3):
    """Three sellers of the same kind with the closest score, then the most products, then by name."""
    same = [x for x in PROFILES.values() if x["seller_slug"] != r["seller_slug"] and x.get("seller_kind") == r.get("seller_kind")]
    same.sort(key=lambda x: (abs((x.get("score") or 0) - (r.get("score") or 0)), -(x.get("product_count") or 0), seller_name(x).lower()))
    return same[:n]


def similar_section(r):
    cards = "".join(
        f'<li class="panel-line"><a class="name" href="/sellers/{x["seller_slug"]}/">{seller_name(x)}</a>'
        f'<span class="small">{x["score"]} of {len(SCORE_CHECKS)} checks</span><span class="small">{plural(x.get("product_count") or 0, "product")}</span></li>'
        for x in similar_sellers(r))
    return f"""
<section class="section" id="other-sellers">
  <div class="wrap">
    <h2 class="h-sources">Compare other sellers</h2>
    <ul class="seller-cards">{cards}</ul>
    <p class="small" style="margin-top:16px"><a href="/sellers/">All sellers we track</a></p>
  </div>
</section>""" if cards else ""


def seller_page(r):
    answer = " ".join(short_answer(r))
    seen = r.get("price_updated_at")
    meta = (f'{AUTHOR}. Tracked since {nice_date(r["first_seen"])}.' if r.get("first_seen") else f"{AUTHOR}.") + \
           (f" Prices checked {nice_date(seen[:10])}." if seen else "")
    return f"""
<section class="hero hero-goal seller-pg">
  <div class="wrap">
    <div class="hero-grid">
      <div>
        <h1>{seller_name(r)}: prices, checks and what we found.</h1>
        <p class="small meta">{meta}</p>
        <p class="intro">{answer}</p>
      </div>{check_card(r)}
    </div>
  </div>
</section>{seller_subs_section(r)}{seller_letters_section(r)}{seller_company_section(r)}{similar_section(r)}
"""


def sellers_order(x):
    return (-(x.get("score") if x.get("score") is not None else -1), -(x.get("product_count") or 0), seller_name(x).lower())


SELLERS_INDEX_JS = """<script>
(function(){var tb=document.getElementById('sellers-table');if(!tb)return;var f=document.querySelector('.sellers-filter'),q=document.getElementById('sellers-q'),
c=document.getElementById('sellers-clear'),m=document.querySelector('.sellers-more'),all=document.getElementById('sellers-all'),n=document.getElementById('sellers-n'),
rows=[].slice.call(tb.tBodies[0].rows),open=false;
function draw(){var s=q.value.trim().toLowerCase(),k=0;rows.forEach(function(r){var hit=!s||r.cells[0].textContent.toLowerCase().indexOf(s)>=0;
r.hidden=!hit||(!open&&!s&&r.classList.contains('more'));if(hit)k++;});if(m)m.hidden=open||!!s;n.textContent=s?k+' of '+rows.length+' sellers match.':'';}
f.hidden=false;if(m)m.hidden=false;q.addEventListener('input',draw);
c.addEventListener('click',function(){q.value='';draw();q.focus();});
if(all)all.addEventListener('click',function(){open=true;draw();});draw();})();
</script>"""


def sellers_index():
    rows, more_cls = sorted(PROFILES.values(), key=sellers_order), ' class="more"'
    trs = "".join(
        f'<tr{more_cls if i >= SELLERS_FIRST else ""}><td><a class="name" href="/sellers/{r["seller_slug"]}/">{seller_name(r)}</a></td>'
        f'<td data-l="Kind">{kind_words(r)[1]}</td><td class="num" data-l="Checks">{r["score"]} of {len(SCORE_CHECKS)}</td>'
        f'<td class="num" data-l="Products">{r.get("product_count") or 0}</td><td class="num" data-l="Substances">{r.get("substance_count") or 0}</td>'
        f'<td class="num" data-l="FDA letters">{r.get("fda_letter_count") or 0}</td></tr>'
        for i, r in enumerate(rows))
    checked = max((r["score_checked_on"] for r in rows if r.get("score_checked_on")), default="")
    more = (f'<p class="legal-more sellers-more" hidden><button type="button" class="btn btn-line" id="sellers-all">Show all {len(rows)}</button></p>'
            if len(rows) > SELLERS_FIRST else "")
    return f"""
<section class="section letters-hd">
  <div class="wrap">
    <h1>Peptide sellers we track</h1>
    <p class="lede">Every shop in our database that sells peptides online, with its five checks, how many products and substances it lists, and its FDA warning letters. Each name opens our page on the seller; we do not link to the shops.</p>
    <p class="letters-stamp">{f'<span class="stamp">Checked {nice_date(checked)}</span>' if checked else ""}<span class="small">{len(rows)} sellers, most checks first, then most products.</span></p>
  </div>
</section>
<section class="band-2" id="sellers-list">
  <div class="wrap">
    <div class="legal-filter sellers-filter" hidden><label for="sellers-q">Filter by name</label><input class="input" id="sellers-q" type="text" autocomplete="off"><button type="button" class="btn btn-line btn-sm" id="sellers-clear">Clear</button><p class="small" id="sellers-n" aria-live="polite"></p></div>
    <div class="tbl-wrap"><table class="tbl tbl-cards tbl-sellers" id="sellers-table"><caption class="vh">Sellers, most checks first</caption>
      <thead><tr><th scope="col">Seller</th><th scope="col">Kind</th><th scope="col">Checks</th><th scope="col">Products</th><th scope="col">Substances</th><th scope="col">FDA letters</th></tr></thead>
      <tbody>{trs}</tbody>
    </table></div>
    {more}
    <p class="small" style="margin-top:16px">Checks are facts we hold about the seller, not a safety or quality grade. <a href="/how-we-rate/">How we rate</a></p>
  </div>
</section>
{SELLERS_INDEX_JS}
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
     "FDA status, real prices and evidence for each goal, checked and dated. Peptides next to the approved alternatives, from a site that never sells.",
     HOME, ORG_SCHEMA, None),
    ("/about/", "about/index.html", "About Peptide Chooser",
     "Peptide Chooser is an independent site that compares peptide products and sellers for people in the United States.", ABOUT, "", [("/about/", "About")]),
    ("/how-we-rate/", "how-we-rate/index.html", "How we rate peptide products and sellers | Peptide Chooser",
     "The five criteria Peptide Chooser uses to rate every peptide product and seller: evidence, FDA status, lab testing, real price and transparency.", HOW, "", [("/how-we-rate/", "How we rate")]),
    ("/contact/", "contact/index.html", "Contact | Peptide Chooser",
     "Email Peptide Chooser for corrections with a source, questions about a listing, press and partnerships. We cannot answer personal medical questions.", CONTACT, "", [("/contact/", "Contact")]),
    ("/disclosure/", "disclosure/index.html", "Affiliate and medical disclosure | Peptide Chooser",
     "How Peptide Chooser earns money through labeled paid links, why commissions never change a rating, and why nothing on the site is medical advice.", DISCLOSURE, "", [("/disclosure/", "Disclosure")]),
    ("/privacy/", "privacy/index.html", "Privacy policy | Peptide Chooser",
     "What information Peptide Chooser collects when you visit or email us, how long we keep it, your rights, and how to contact us about your data.", PRIVACY, "", [("/privacy/", "Privacy")]),
    ("/corrections/", "corrections/index.html", "Mistakes we fixed | Peptide Chooser",
     "Every factual error Peptide Chooser has corrected, with the date, what was wrong and what changed. Send corrections with a source and we list the fix here.", CORRECTIONS, "", [("/corrections/", "Corrections")]),
]

if LETTERS_ALL:
    _d = DATA["pulled_at"][:10]
    PAGES.append(("/fda-warning-letters/", "fda-warning-letters/index.html", "FDA warning letters to peptide sellers | Peptide Chooser",
                  f"Every FDA warning letter to peptide sellers, compounders and online clinics in our database, with its date, subject and fda.gov link. Checked {nice_date(_d)}.",
                  LETTERS_PAGE, "", [("/fda-warning-letters/", "FDA warning letters")]))

for _g in ALL_GOALS:
    if _g.get("page"):
        PAGES.append((f"/{_g['slug']}/", f"{_g['slug']}/index.html", _g["title"], _g["description"],
                      category_page(_g), "", [(f"/{_g['slug']}/", _g["name"])]))

if PROFILES:
    PAGES.append(("/sellers/", "sellers/index.html", "Peptide sellers and their checks | Peptide Chooser",
                  f"Every peptide seller in our database, {len(PROFILES)} in all, with five background checks, product and "
                  "substance counts and FDA warning letters. We never link to them.",
                  sellers_index(), "", [("/sellers/", "Sellers")]))
    for _r in sorted(PROFILES.values(), key=lambda x: x["seller_slug"]):
        PAGES.append((f"/sellers/{_r['seller_slug']}/", f"sellers/{_r['seller_slug']}/index.html", seller_title(_r),
                      seller_description(_r), seller_page(_r), "",
                      [("/sellers/", "Sellers"), (f"/sellers/{_r['seller_slug']}/", seller_name(_r))]))


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
                                        "This page does not exist on Peptide Chooser. Go to the home page or compare peptide options by goal; the link may be old or mistyped.", NOT_FOUND), encoding="utf-8")
    if LETTERS_ALL:
        (DIST / "fda-warning-letters" / "feed.xml").write_text(letters_feed(), encoding="utf-8")
    # Web app manifest (design book, README, Logo): the name and the icons drawn from the mark by tools/og.py.
    (DIST / "site.webmanifest").write_text(json.dumps({
        "name": "Peptide Chooser", "short_name": "Peptide Chooser", "start_url": "/", "display": "browser",
        "background_color": COLOR["white"], "theme_color": COLOR["white"],
        "icons": [{"src": "/assets/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"},
                  {"src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png"}]}, indent=2) + "\n")
    (DIST / "CNAME").write_text("peptidechooser.com\n")
    (DIST / ".nojekyll").write_text("")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nDisallow: /out/\nSitemap: {SITE}/sitemap.xml\n")
    (DIST / "llms.txt").write_text(
        "# Peptide Chooser\n\n> An independent US comparison site: peptide products next to FDA-approved alternatives, "
        "with evidence, FDA status and price per month for each goal. We compare; we never sell.\n\n"
        + "".join(f"- [{t}]({SITE}{p}): {d}\n" for p, _, t, d, *_ in PAGES))
    # lastmod: the newest data date of this build, the database pull when connected, else the hand-checked date (owner, Q1 a, 2 Nov 2026)
    lastmod = max(DATA["checked"], (DATA.get("pulled_at") or "")[:10])
    urls = "".join(f"<url><loc>{SITE}{p[0]}</loc><lastmod>{lastmod}</lastmod></url>" for p in PAGES)
    (DIST / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    (DIST / "pages.json").write_text(json.dumps([{"path": p[0], "title": p[2]} for p in PAGES] + [{"path": "/404", "title": "Page not found | Peptide Chooser"}]))
    print("built", len(PAGES) + 1, "pages")


if __name__ == "__main__":
    main()
