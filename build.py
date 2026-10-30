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
    <p>We use Google Analytics to count visits and see which pages help. No ads, no selling of data. <a href="/privacy/">Privacy policy</a></p>
    <div class="cookie-btns"><button class="btn btn-ink" type="button" data-consent="yes">Accept</button><button class="btn btn-line" type="button" data-consent="no">Reject</button></div>
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
GSAP = "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5"
MOTION_JS = f"""<script defer src="{GSAP}/gsap.min.js"></script>
<script defer src="{GSAP}/ScrollTrigger.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded',function(){{
var d=document.documentElement;if(!d.classList.contains('motion')||!window.gsap||!window.ScrollTrigger)return;
window.pcMotion=true;gsap.registerPlugin(ScrollTrigger);
var css=getComputedStyle(d),ms=function(n){{return parseFloat(css.getPropertyValue('--motion-'+n))/1000;}};
var rise=parseFloat(css.getPropertyValue('--motion-rise'));
var fig=document.querySelector('.figure');
if(fig){{var tl=gsap.timeline({{paused:true}});
tl.to(fig.querySelectorAll('.contour > *'),{{strokeDashoffset:0,duration:ms('draw'),ease:'power1.inOut'}})
.to(fig.querySelector('.body'),{{opacity:1,duration:ms('reveal')*2,ease:'power1.out'}},ms('draw')*0.45);
ScrollTrigger.create({{trigger:fig,start:'top 85%',once:true,onEnter:function(){{tl.play();}}}});}}
ScrollTrigger.batch('.sec-hd, .tbl tbody tr, .criteria li, .creators li, .trust-row li',{{start:'top 92%',once:true,
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


def nav_items(path):
    # Design book, Pages and buttons: one item per section of the site. An item appears only when
    # its section exists; Where to buy and Compare prices join once vendor and compare pages are live.
    items = [("/#goals", "Peptides"), ("/#legal", "Safety and legal"), ("/#learn", "Learn"),
             ("/how-we-rate/", "How we rate"), ("/about/", "About")]
    current = ' aria-current="page"'
    return "".join(
        f'<a href="{href}"{current if href == path else ""}>{label}</a>' for href, label in items
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
{MOTION_HEAD}
{ANALYTICS}
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
{COOKIE_BAR}
{MOTION_JS}
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
        has_page = bool(g.get("page"))
        compare = f'<td class="act"><a class="btn btn-ink btn-sm" href="/{g["slug"]}/">Compare</a></td>' if has_page else ""
        rows.append(f"""<tr>
  <td><span class="name">{g["name"]}</span></td>
  <td><span class="name">{g["best_option"]}</span><span class="note">{g["options_checked"]} options checked</span></td>
  <td><span class="num-l">${g["price_from_usd"]}<span class="num-unit">/mo</span></span><span class="note">{g["price_note"]}</span></td>
  <td>{chip}</td>
  {compare}
</tr>""")
    return "\n".join(rows)


COMPARE_TH = '<th scope="col"></th>' if any(g.get("page") for g in LIVE_GOALS) else ""
ALL_GOALS = DATA["goals"]
LEGAL = DATA["legal"]
CREATORS = DATA["creators"]
SOURCES_HOME = "".join(
    f'<li id="src-{s["n"]}">{s["text"]}: <a href="{s["url"]}" rel="nofollow">{s["url"]}</a></li>' for s in LEGAL["sources"]
) + "".join(f'<li>{g["price_source_name"]}: <a href="{g["price_source"]}" rel="nofollow">{g["price_source"]}</a></li>' for g in LIVE_GOALS)

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
        regions += [f'<ellipse class="region" data-goal="{g["slug"]}" cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}"/>' for cx, cy, rx, ry in shapes]
        pins.append(f'<g class="pin" data-goal="{g["slug"]}" role="button" tabindex="0" aria-pressed="{on}" aria-label="{g["label"]}">'
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


def body_map():
    items, panels = [], []
    for i, g in enumerate(ALL_GOALS):
        on = ' aria-pressed="true"' if i == 0 else ' aria-pressed="false"'
        items.append(f'<button type="button" class="goal-item" data-goal="{g["slug"]}"{on}><span>{g["label"]}</span><span class="small">{len(g["peptides"])} options</span></button>')
        peps = "".join(f'<li><span class="name">{p["name"]}</span><span class="chip chip-{p["chip"]}">{p["status"]}</span></li>' for p in g["peptides"])
        if g.get("live"):
            # The answer: the price pad's words, now inside the goal's panel (design book, pages.md, Home).
            answer = (f'<div class="answer"><p class="answer-k">Cheapest proven option, per month</p>'
                      f'<p class="hero-num"><span class="num-xl">${g["price_from_usd"]}</span> <span class="num-unit">/mo</span></p>'
                      f'<p class="hero-what"><strong>{g["name"]}:</strong> {g["best_option"]}'
                      f'<span class="small">{g["options_checked"]} options checked <span class="stamp">Checked {CHECKED}</span></span></p></div>')
            foot = '<p class="fine">Proven means FDA approved for that use. Not a prescription.</p>'
        else:
            answer, foot = "", ""
        link = f'<div class="btn-row"><a class="btn btn-ink" href="/{g["slug"]}/">Compare {g["label"].lower()} options</a><a class="btn btn-line" href="#legal">Legal status</a></div>' if g.get("page") else '<p class="small">Full comparison for this goal is not published yet. The legal status above is current as of ' + CHECKED + '.</p>'
        panels.append(f'<div class="goal-panel" id="goal-{g["slug"]}" data-goal="{g["slug"]}"{"" if i == 0 else " hidden"}>'
                      f'<span class="rx-mark" aria-hidden="true">&#8478;</span><h3>Peptides for {g["label"].lower()}</h3>{answer}'
                      f'<p class="goal-intro">{g["intro"]}</p><ul class="pep-list">{peps}</ul>{link}{foot}</div>')
    return figure_svg(), "".join(items), "".join(panels)


FIGURE, GOAL_ITEMS, GOAL_PANELS = body_map()

LEGAL_ROWS = "".join(
    f'<tr><td><span class="name">{r["peptide"]}</span></td><td><span class="chip chip-{r["chip"]}">{r["status"]}</span></td>'
    f'<td>{r["note"]} <a class="ref" href="#src-{r["src"]}" aria-label="Source {r["src"]}"><sup>{r["src"]}</sup></a></td></tr>'
    for r in LEGAL["rows"])

CREATOR_ROWS = "".join(
    f'<li><a href="{c["url"]}" rel="nofollow noopener">{c["name"]}</a><span class="small">{c["what"]}</span></li>' for c in CREATORS["rows"])

MAP_JS = """<script>
(function(){var root=document.getElementById('goals');if(!root)return;
function show(k){var old=root.querySelector('.goal-panel:not([hidden])'),next=root.querySelector('.goal-panel[data-goal="'+k+'"]');
if(!next||old===next)return;
function swap(){if(old)old.hidden=true;next.hidden=false;
if(window.pcMotion){gsap.fromTo(next,{opacity:0,y:6},{opacity:1,y:0,duration:0.22,ease:'power1.out'});}}
if(window.pcMotion&&old){gsap.to(old,{opacity:0,duration:0.12,ease:'power1.in',onComplete:function(){gsap.set(old,{opacity:1});swap();}});}else{swap();}}
function pick(k){root.querySelectorAll('[data-goal]').forEach(function(x){var on=x.getAttribute('data-goal')===k;
if(x.hasAttribute('aria-pressed'))x.setAttribute('aria-pressed',on?'true':'false');x.classList.toggle('on',on);
if(x.classList.contains('pin')){x.classList.remove('pulse');if(on){void x.getBoundingClientRect();x.classList.add('pulse');}}});show(k);}
function hover(k){root.querySelectorAll('.region,.pin').forEach(function(x){x.classList.toggle('hov',x.getAttribute('data-goal')===k);});}
root.addEventListener('click',function(e){var b=e.target.closest('.goal-item,.pin');if(b)pick(b.getAttribute('data-goal'));});
root.addEventListener('mouseover',function(e){var b=e.target.closest('.goal-item,.pin');hover(b?b.getAttribute('data-goal'):null);});
root.addEventListener('mouseleave',function(){hover(null);});
root.addEventListener('keydown',function(e){var t=e.target;
if(t.classList&&t.classList.contains('pin')&&(e.key==='Enter'||e.key===' ')){e.preventDefault();pick(t.getAttribute('data-goal'));return;}
// Arrow keys move through the goal list (Tab, Enter and Space work as on any button).
if(e.key!=='ArrowDown'&&e.key!=='ArrowUp')return;var items=[].slice.call(root.querySelectorAll('.goal-item')),i=items.indexOf(t);
if(i<0)return;e.preventDefault();items[(i+(e.key==='ArrowDown'?1:items.length-1))%items.length].focus();});
pick(root.querySelector('.goal-item[aria-pressed="true"]').getAttribute('data-goal'));})();
</script>"""

HOME = f"""
<section class="hero hero-clinic">
  <div class="wrap">
    <div class="hero-intro">
      <h1>The best peptides for your goal, compared honestly.</h1>
      <p class="lede">For each goal we put peptide products next to the FDA-approved alternatives and show what the evidence says, what it costs per month and how you would get it. We compare; we never sell.</p>
    </div>
    <section class="chooser" id="goals" aria-labelledby="goals-h">
      <div class="chooser-hd"><h2 id="goals-h">Start with what you want to change</h2><p>Tap the body or pick from the list. Every goal shows what is approved, what is not, and the proven alternative.</p></div>
      <div class="figure">{FIGURE}</div>
      <div class="goal-list" role="group" aria-label="Goals">{GOAL_ITEMS}</div>
      <div class="goal-panels" aria-live="polite">{GOAL_PANELS}</div>
    </section>
  </div>
</section>

<section class="section" id="compare">
  <div class="wrap">
    <div class="sec-hd"><div><h2>Compare by goal</h2><p>One row per published goal. The best proven option is the cheapest one the FDA has approved for that use.</p></div></div>
    <div class="tbl-wrap"><table class="tbl">
      <thead><tr><th scope="col">Goal</th><th scope="col">Best proven option</th><th scope="col">Price from</th><th scope="col">FDA status</th>{COMPARE_TH}</tr></thead>
      <tbody>{goal_rows()}</tbody>
    </table></div>
    <p class="small" style="margin-top:16px">{STANDING_LINE}</p>
  </div>
</section>

<section class="band-2" id="legal">
  <div class="wrap">
    <div class="sec-hd"><div><h2>Is it legal today?</h2><p>FDA status of the peptides people ask about most, each with its source. Checked {nice_date(LEGAL["checked"])}.</p></div></div>
    <div class="tbl-wrap"><table class="tbl">
      <thead><tr><th scope="col">Peptide</th><th scope="col">Status</th><th scope="col">What that means</th></tr></thead>
      <tbody>{LEGAL_ROWS}</tbody>
    </table></div>
    <p class="small" style="margin-top:16px">Approved means the FDA approved a product containing it for a stated use. Not approved means no approved product exists; buying it for yourself is not a crime in the US, but nobody has checked what is in the vial.</p>
  </div>
</section>

<section class="section">
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

<section class="section" id="learn">
  <div class="wrap">
    <div class="sec-hd"><div><h2>Who to follow</h2><p>{CREATORS["note"]}</p></div></div>
    <ul class="creators">{CREATOR_ROWS}</ul>
    <p class="small" style="margin-top:16px">Reviewed {nice_date(CREATORS["checked"])}. Links open YouTube; we earn nothing from them.</p>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <ul class="trust-row">
      <li><a href="/how-we-rate/">How we rate</a><span>Five public criteria, the same for every product and seller.</span></li>
      <li><a href="/disclosure/">How we make money</a><span>Some links pay us when you buy. It never changes a rating.</span></li>
      <li><a href="/about/">Who checks our facts</a><span>Every medical claim links to the FDA page, label or study it comes from.</span></li>
      <li><a href="/corrections/">Mistakes we fixed</a><span>Every correction, dated and public.</span></li>
    </ul>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <h2 class="h-sources">Sources</h2>
    <ol class="small sources" style="padding-left:1.2em">{SOURCES_HOME}</ol>
  </div>
</section>
{MAP_JS}
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
</ul>
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

def category_page(g):
    rows = []
    for o in g["options"]:
        refs = (" <sup>" + ", ".join(f'<a href="#src-{n}">{n}</a>' for n in o["sources"]) + "</sup>") if o["sources"] else ""
        price = (f'<span class="num-l">{o["price"]}<span class="num-unit">{o["price_unit"]}</span></span><span class="note">{o["price_note"]}</span>'
                 if o["price"] else f'<span class="note">{o["price_note"]}</span>')
        rows.append(f"""<tr>
  <td><span class="name">{o["name"]}{refs}</span><span class="note">{o["kind"]}</span></td>
  <td><span class="chip chip-{o["fda_chip"]}">{o["fda"]}</span></td>
  <td><span class="chip chip-{o["evidence_chip"]}">{o["evidence"]}</span></td>
  <td>{price}</td>
  <td>{o["how"]}</td>
</tr>""")
    srcs = "".join(f'<li id="src-{s["n"]}">{s["text"]}: <a href="{s["url"]}" rel="nofollow">{s["url"]}</a></li>' for s in g["sources"])
    return f"""
<section class="hero">
  <div class="wrap hero-grid">
    <div>
      <h1>{g["h1"]}</h1>
      <p class="small meta">{AUTHOR}. Last updated {CHECKED}. {STANDING_LINE}</p>
      <p class="intro">{g["short_answer"]}</p>
    </div>
    <div class="board rx" aria-label="Price pad">
      <div class="rx-head"><span class="rx-mark" aria-hidden="true">&#8478;</span><h2>Cheapest proven option, per month</h2></div>
      <p class="hero-num"><span class="num-xl">${g["price_from_usd"]}</span> <span class="num-unit">/mo from</span></p>
      <div class="ledger"><span>{g["best_option"]}</span></div>
      <div class="rx-foot"><span class="stamp">Checked {CHECKED}</span><span class="fine">{g["price_note"]}. Not a prescription.</span></div>
    </div>
  </div>
</section>
<section class="section" id="options">
  <div class="wrap">
    <div class="sec-hd"><div><h2>Every option, side by side</h2><p>{g["options_checked"]} options checked on the same five criteria. Rows that are not approved for human use carry no price and no seller.</p></div></div>
    <div class="tbl-wrap"><table class="tbl">
      <thead><tr><th scope="col">Option</th><th scope="col">FDA status for hair loss</th><th scope="col">Evidence in people</th><th scope="col">Price from</th><th scope="col">How you get it</th></tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table></div>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <h2 class="h-sources">Sources</h2>
    <ol class="small" style="padding-left:1.2em">{srcs}</ol>
  </div>
</section>
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

for _g in LIVE_GOALS:
    if _g.get("page"):
        PAGES.append((f"/{_g['slug']}/", f"{_g['slug']}/index.html", _g["title"], _g["description"],
                      category_page(_g), "", [(f"/{_g['slug']}/", _g["name"])]))


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
