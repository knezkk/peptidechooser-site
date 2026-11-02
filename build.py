"""Builds the static Peptide Chooser site into ./dist. Run: python3 build.py

Design source: design/tokens.json and design/bundle.css (copies of the Master 1 design book).
Numbers source: data/site.json. Nothing numeric is typed into a template.
"""
from pathlib import Path
import json
import os
import sys
import re
from html import escape
import shutil
from datetime import date

import guides

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
SITE = "https://peptidechooser.com"
EMAIL = "hello@peptidechooser.com"
AUTHOR = "Peptide Chooser editorial team"

# SITE_JSON points at another data file (a local preview with database rows); the deploy always reads data/site.json.
DATA = json.loads(Path(os.environ.get("SITE_JSON") or ROOT / "data" / "site.json").read_text(encoding="utf-8"))
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
# Google's script loads only after "Accept" (now or on an earlier visit), so nothing reaches Google before consent, as the
# privacy policy says; consent mode alone still sent cookieless pings (design/site-polish, 2 Nov 2026).
ANALYTICS = f"""<script>
window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}
gtag('consent','default',{{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',analytics_storage:'denied'}});
window.pcLoadGA=function(){{if(window.pcGA)return;window.pcGA=1;gtag('consent','update',{{analytics_storage:'granted'}});
gtag('js',new Date());gtag('config','{GA4_ID}',{{anonymize_ip:true}});var s=document.createElement('script');s.async=true;
s.src='https://www.googletagmanager.com/gtag/js?id={GA4_ID}';document.head.appendChild(s);}};
try{{if(localStorage.getItem('pc-consent')==='yes')pcLoadGA();}}catch(e){{}}
</script>""" if GA4_ID else ""

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
if(v==='yes'&&window.pcLoadGA){pcLoadGA();}
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
// opening the menu moves focus to its first visible link: the links come before the button in the page, so Tab alone
// would skip them (design/site-polish, 2 Nov 2026)
b.addEventListener('click',function(){var o=!n.classList.contains('open');set(o);if(o){var f=[].filter.call(n.querySelectorAll('a,button,input'),function(x){return x.offsetParent;})[0];if(f)f.focus();}});
n.addEventListener('click',function(e){if(e.target.closest('a'))set(false);});
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&n.classList.contains('open')){set(false);b.focus();}});})();
(function(){var w=document.querySelector('.nav-goals'),b=w&&w.querySelector('.nav-goals-btn');if(!b)return;
function set(o){w.classList.toggle('open',o);b.setAttribute('aria-expanded',o?'true':'false');}
b.addEventListener('click',function(){set(!w.classList.contains('open'));});
w.addEventListener('click',function(e){if(e.target.closest('a'))set(false);});
document.addEventListener('click',function(e){if(w.classList.contains('open')&&!w.contains(e.target))set(false);});
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&w.classList.contains('open')){set(false);b.focus();}});})();
</script>"""
# Design book, Every page, Header, Search (owner task 2 Nov 2026): a plain field right of the links on wide screens, the first
# item inside the phone Menu. Typing filters /search-index.json in the page (no library): at most 8 results under the field,
# arrow keys move, Enter opens the chosen one (none chosen: the form goes to /search/), Escape closes. With JavaScript off
# the form submits to /search/?q=... . window.pcSearch is shared with the /search/ page.
SEARCH_FORM = ('<form class="head-search" role="search" action="/search/" method="get">'
               '<label class="vh" for="hs-q">Search a peptide or seller</label>'
               '<input class="input" id="hs-q" name="q" type="search" placeholder="Search a peptide or seller" autocomplete="off" '
               'role="combobox" aria-expanded="false" aria-controls="hs-list" aria-autocomplete="list">'
               '<ul class="search-list" id="hs-list" role="listbox" aria-label="Search results" hidden></ul></form>')
SEARCH_JS = """<script>
(function(){var idx=null,wait=[],ORDER={Goal:0,Peptide:1,Seller:2,Page:3};
function load(cb){if(idx)return cb(idx);wait.push(cb);if(wait.length>1)return;
fetch('/search-index.json').then(function(r){return r.json();}).then(function(d){idx=d;var w=wait;wait=[];w.forEach(function(f){f(d);});}).catch(function(){wait=[];});}
function c(s){return String(s||'').toLowerCase().replace(/[^a-z0-9]+/g,'');}
function score(f,k){var cf=c(f);if(cf.indexOf(k)===0)return 3;var ws=String(f).toLowerCase().split(/[^a-z0-9]+/).filter(Boolean);
for(var i=1;i<ws.length;i++){if(c(ws.slice(i).join('')).indexOf(k)===0)return 2;}return cf.indexOf(k)>=0?1:0;}
function find(d,q,n){var k=c(q);if(!k)return[];var out=[];
d.forEach(function(e){var s=score(e.name,k)*2;(e.aliases||[]).forEach(function(a){s=Math.max(s,score(a,k)*2-1);});if(s>0)out.push([s,e]);});
out.sort(function(x,y){return y[0]-x[0]||ORDER[x[1].type]-ORDER[y[1].type]||x[1].name.length-y[1].name.length||(x[1].name<y[1].name?-1:1);});
return out.slice(0,n).map(function(x){return x[1];});}
function row(e,tab){var li=document.createElement('li'),a=document.createElement('a');a.href=e.url;if(!tab)a.tabIndex=-1;
[['search-name',e.name],['chip chip-neutral',e.type],['search-line',e.line]].forEach(function(p){var s=document.createElement('span');s.className=p[0];s.textContent=p[1];a.appendChild(s);});
li.appendChild(a);return li;}
window.pcSearch={load:load,find:find,row:row};
var f=document.querySelector('.head-search');if(!f)return;var inp=f.querySelector('input'),list=f.querySelector('.search-list'),res=[],act=-1;
function close(){list.hidden=true;inp.setAttribute('aria-expanded','false');inp.removeAttribute('aria-activedescendant');act=-1;}
function draw(){var v=inp.value.trim();if(!v){close();return;}load(function(d){if(inp.value.trim()!==v)return;res=find(d,v,8);list.textContent='';act=-1;
inp.removeAttribute('aria-activedescendant');
if(!res.length){var li=document.createElement('li');li.className='search-none';li.textContent='No match. Press Enter to search every page.';list.appendChild(li);}
res.forEach(function(e,i){var li=row(e);li.id='hs-o'+i;li.setAttribute('role','option');li.setAttribute('aria-selected','false');list.appendChild(li);});
list.hidden=false;inp.setAttribute('aria-expanded','true');});}
function mark(i){var o=list.querySelectorAll('[role=option]');if(!o.length)return;act=(i+o.length)%o.length;
for(var j=0;j<o.length;j++)o[j].setAttribute('aria-selected',j===act?'true':'false');inp.setAttribute('aria-activedescendant',o[act].id);o[act].scrollIntoView({block:'nearest'});}
inp.addEventListener('input',draw);inp.addEventListener('focus',function(){load(function(){});if(inp.value.trim())draw();});
inp.addEventListener('keydown',function(e){if(e.key==='ArrowDown'){e.preventDefault();if(list.hidden)draw();else mark(act+1);}
else if(e.key==='ArrowUp'){e.preventDefault();if(!list.hidden)mark(act-1);}
else if(e.key==='Enter'&&!list.hidden&&act>=0&&res[act]){e.preventDefault();location.href=res[act].url;}
else if(e.key==='Escape'&&!list.hidden){e.preventDefault();e.stopPropagation();close();}});
document.addEventListener('click',function(e){if(!f.contains(e.target))close();});})();
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
// table rows rise only in tables of up to 25 rows; a long data table (letters, sellers, legal) shows at once, since one
// trigger per row cost seconds of layout on phones (design/site-polish, 2 Nov 2026). Without :has the rows are not pre-hidden.
var sel='.sec-hd, .criteria li, .creators li';try{{if(document.querySelector('.tbl tbody:not(:has(> tr:nth-child(26))) > tr'))sel+=', .tbl tbody:not(:has(> tr:nth-child(26))) > tr';}}catch(e){{}}
ScrollTrigger.batch(sel,{{start:'top 92%',once:true,
onEnter:function(els){{gsap.fromTo(els,{{opacity:0,y:rise}},{{opacity:1,y:0,duration:ms('reveal'),ease:'power2.out',stagger:ms('stagger'),overwrite:true}});}}}});
}});
</script>"""

# Public Sans served from our own site (owner answer Q1 a, 2 Nov 2026; SIL Open Font License, assets/fonts/OFL.txt): one
# variable file per character set, the Latin one preloaded, so the first paint waits on no other server.
FONT_FACE = "".join(
    f"@font-face{{font-family:'Public Sans';font-style:normal;font-weight:100 900;font-display:swap;"
    f"src:url(/assets/fonts/public-sans-{sub}.woff2) format('woff2');unicode-range:{rng}}}"
    for sub, rng in (("latin-ext", "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C4, U+2113, U+2C60-2C7F, U+A720-A7FF"), ("latin", "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD")))
FONTS = ('<link rel="preload" href="/assets/fonts/public-sans-latin.woff2" as="font" type="font/woff2" crossorigin>'
         f'<style>{FONT_FACE}</style>')


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
    # letters (the letters page once it exists, else Home's section), How we rate, About; Learn (/learn/, the guides; owner task 2 Nov 2026) after FDA letters.
    current = ' aria-current="page"'
    goals = "".join(f'<li><a href="{goal_href(g)}">{g["label"]}</a></li>' for g in ALL_GOALS)
    # "Sellers" after "Peptides by goal" once the seller pages exist (pages.md, Seller; owner task 2 Nov 2026)
    items = [("/sellers/", "Sellers")] if PROFILES else []
    items += [("/#legal", "Legal status"), (LETTERS_URL, "FDA letters"), ("/learn/", "Learn"), ("/how-we-rate/", "How we rate"), ("/about/", "About")]
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
<meta name="description" content="{description}">{'<meta name="robots" content="noindex">' if path in NOINDEX else ""}
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
    <nav class="nav" id="site-nav" aria-label="Main">{SEARCH_FORM}{nav_items(path)}</nav>
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
      {foot_browse()}
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
{SEARCH_JS}
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


def item_list_schema(name, items):
    """ItemList JSON-LD (owner task 2 Nov 2026: on the letters page, and on /sellers/ once it exists): items are (name, url)."""
    els = [{"@type": "ListItem", "position": i, "name": n, "url": u} for i, (n, u) in enumerate(items, start=1)]
    return ('<script type="application/ld+json">'
            + json.dumps({"@context": "https://schema.org", "@type": "ItemList", "name": name,
                          "numberOfItems": len(els), "itemListElement": els}) + "</script>")


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
    return (f'<span class="{cls}">Online clinics from {usd(r["price_monthly"])}/mo ({clinic_link(r["seller_slug"], seller_base(r["seller_name"]), True)})'
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
    # the FDA's own wording for the substance, when the database has it (fda_listing; shown in small, never required)
    listing = next((r.get("fda_listing") for r in LEGAL_DB or [] if r["substance_slug"] == slug and r.get("fda_listing")), "")
    return {"chip": chip, "label": label, "sentence": sentence, "name": name, "url": row["source_url"],
            "seen": row["first_seen_by_us"], "listing": listing}


def listing_html(s):
    """The FDA's own wording for a substance in small under its status, when the database has it (fda_listing)."""
    return f'<span class="listing">FDA listing: "{escape(s["listing"])}"</span>' if s and s.get("listing") else ""


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
# Shops and clinics (peptide-data decision 26; pages.md, Rules that apply to every page): a shop lists products
# (product_count > 0), a clinic only plans (product_count 0). Every list of shops takes SHOPS; a clinic is never in one.
SHOPS = {k: r for k, r in PROFILES.items() if (r.get("product_count") or 0) > 0}
CLINIC_PROFILES = {k: r for k, r in PROFILES.items() if k not in SHOPS}


def clinic_link(seller_slug, name, inline=False):
    """A clinic's name as a link to its page on our site when it has one, else plain text; never the clinic's own site.
    `inline` for a name inside a line of text (no name style)."""
    if seller_slug in PROFILES:
        return f'<a href="/sellers/{seller_slug}/">{name}</a>' if inline else f'<a class="name" href="/sellers/{seller_slug}/">{name}</a>'
    return name if inline else f'<span class="name">{name}</span>'



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
    for r in sorted((r for r in PRODUCTS if r["substance_slug"] == slug and r["seller_slug"] not in CLINIC_PROFILES), key=key):
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
        trs.append(f'<tr data-seller="{r["seller_slug"]}"><td>{name_html}</td><td data-l="Product">{name}<span class="sub">{size}</span></td>'
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


# Peptide pages (pages.md, Peptide; owner task 2 Nov 2026): one page per substance with a status, from the database or
# from its own hand-written "Is it legal today?" row. Defined here because the legal tables link each name to its page.
def hand_legal(slug):
    """The hand-written legal row that carries the substance and a status (not a db_only row), or None."""
    return next((r for r in LEGAL["rows"] if slug in (r.get("substances") or []) and r.get("status") and not r.get("db_only")), None)


PEPTIDE_SLUGS = sorted({r["substance_slug"] for r in LEGAL_DB or [] if db_status(r["substance_slug"])}
                       | {s for r in LEGAL["rows"] for s in r.get("substances") or [] if not db_status(s) and hand_legal(s)})


def legal_name(slugs, name):
    """A legal table's name cell: a link to the substance's page when the row is one substance with a page."""
    if len(slugs) == 1 and slugs[0] in PEPTIDE_SLUGS:
        return f'<a class="name" href="/peptides/{slugs[0]}/">{name}</a>'
    return f'<span class="name">{name}</span>'


ALL_SUBSTANCES = '<a href="/peptides/">All substances</a>'


def legal_rows(only=None):
    """"Is it legal today?": each hand-written row, or, when the database has a status for its substances, one row per
    substance from the database with its own source link and the date we first saw that status. `only` keeps the rows
    for those substances (a goal page shows the rows for its own options)."""
    keep = lambda slugs: only is None or bool(set(slugs) & only)
    hand = lambda r: (f'<tr><td>{legal_name(r.get("substances") or [], r["peptide"])}</td><td><span class="chip chip-{r["chip"]}">{r["status"]}</span></td>'
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
            out.append(f'<tr><td>{legal_name([slug], s["name"])}</td><td><span class="chip chip-{s["chip"]}">{s["label"]}</span></td>'
                       f'<td>{s["sentence"]}{" " + r["use"] if r.get("use") else ""} <a class="ref" href="{s["url"]}" rel="nofollow">FDA source</a>, {nice_date(s["seen"])}{note}{listing_html(s)}</td></tr>')
    # Every other substance with a database status gets its own row (owner, 1 Nov 2026: the table lists every substance
    # the database has a status for, plus the hand rows it lacks), then all rows are sorted by name.
    shown = {slug for r in LEGAL["rows"] for slug in r.get("substances", [])
             if all(db_status(x) for x in r.get("substances", [])) and LEGAL_DB}
    for slug in sorted({r["substance_slug"] for r in LEGAL_DB or []} - shown):
        s = db_status(slug)
        if not s or not keep([slug]):
            continue
        seen.append(s["seen"])
        out.append(f'<tr><td>{legal_name([slug], s["name"])}</td><td><span class="chip chip-{s["chip"]}">{s["label"]}</span></td>'
                   f'<td>{s["sentence"]} <a class="ref" href="{s["url"]}" rel="nofollow">FDA source</a>, {nice_date(s["seen"])}{listing_html(s)}</td></tr>')
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
# Which substances each letter names (site.letter_substances; owner task 2 Nov 2026): per substance its letters, newest first,
# one row per letter, and per letter its substances. Only letters on the letters page count.
LETTER_SUBS_ON = "letter_substances" in DATA
_on_page = {r["letter_url"] for r in LETTERS_ALL}
LETTER_SUBS, SUBS_OF_LETTER = {}, {}
for _r in sorted(DATA.get("letter_substances") or [], key=lambda r: (r["letter_date"] or "", r["letter_url"]), reverse=True):
    if _r["letter_url"] not in _on_page:
        continue
    if all(x["letter_url"] != _r["letter_url"] for x in LETTER_SUBS.get(_r["substance_slug"], [])):
        LETTER_SUBS.setdefault(_r["substance_slug"], []).append(_r)
    SUBS_OF_LETTER.setdefault(_r["letter_url"], []).append(_r["substance_slug"])
LETTER_CO = {r["letter_url"]: r["company_name"] for r in LETTERS_ALL}
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
            f'<tr{more if i >= LETTERS_FIRST else ""} data-year="{r["letter_date"][:4]}" data-subs="{" ".join(SUBS_OF_LETTER.get(r["letter_url"], []))}"><td class="num">{nice_date(r["letter_date"])}</td>'
            f'<td><span class="name">{escape(clean(r["company_name"]))}</span>{seller}<span class="sub-phone">{subj.replace("/", "/<wbr>")}</span></td>'
            f'<td class="subj">{subj.replace("/", "/<wbr>")}</td>{office_cell(r.get("issuing_office"))}'
            f'<td><a href="{escape(r["letter_url"])}" rel="nofollow">FDA letter</a></td></tr>')
    return "".join(out)


LETTERS_YEARS = sorted({r["letter_date"][:4] for r in LETTERS_ALL}, reverse=True)
# The substance filter (pages.md, Letters; owner task 2 Nov 2026): every substance a letter names, most letters first
SUB_NAME = {r["substance_slug"]: clean(r["substance_name"] or r["substance_slug"]) for r in DATA.get("letter_substances") or []}
SUB_COUNTS = sorted(((slug, len(v)) for slug, v in LETTER_SUBS.items()), key=lambda x: (-x[1], SUB_NAME[x[0]].lower()))
SUB_SELECT = ('<div class="legal-filter sub-filter"><label for="letters-sub">Substance</label><select class="input" id="letters-sub">'
              '<option value="">Any substance</option>'
              + "".join(f'<option value="{slug}">{escape(SUB_NAME[slug])} ({n})</option>' for slug, n in SUB_COUNTS)
              + "</select></div>") if SUB_COUNTS else ""
YEAR_CHIPS = "".join(
    f'<button type="button" class="year-chip" data-year="{y}" aria-pressed="false">{y} <span>{sum(r["letter_date"][:4] == y for r in LETTERS_ALL)}<span class="vh"> letters</span></span></button>'
    for y in LETTERS_YEARS)
LETTERS_PAGE_JS = """<script>
(function(){var tb=document.getElementById('letters-table');if(!tb)return;var f=document.querySelector('.letters-filter'),q=document.getElementById('letters-q'),
c=document.getElementById('letters-clear'),m=document.querySelector('.letters-more'),all=document.getElementById('letters-all'),n=document.getElementById('letters-n'),
chips=[].slice.call(document.querySelectorAll('.year-chip')),rows=[].slice.call(tb.tBodies[0].rows),open=false,sb=document.getElementById('letters-sub');
var P=new URLSearchParams(location.search);if(sb&&P.get('sub')&&sb.querySelector('option[value="'+P.get('sub')+'"]'))sb.value=P.get('sub');if(P.get('q'))q.value=P.get('q');
function draw(){var s=q.value.trim().toLowerCase(),u=sb?sb.value:'',ys=chips.filter(function(x){return x.getAttribute('aria-pressed')==='true';}).map(function(x){return x.getAttribute('data-year');}),k=0;
rows.forEach(function(r){var hit=(!s||r.cells[1].textContent.toLowerCase().indexOf(s)>=0)&&(!ys.length||ys.indexOf(r.getAttribute('data-year'))>=0)
&&(!u||(' '+r.getAttribute('data-subs')+' ').indexOf(' '+u+' ')>=0);
r.hidden=!hit||(!open&&!s&&!u&&!ys.length&&r.classList.contains('more'));if(hit)k++;});
if(m)m.hidden=open||!!s||!!u||ys.length>0;n.textContent=(s||u||ys.length)?k+' of '+rows.length+' letters match.':'';}
f.hidden=false;if(m)m.hidden=false;q.addEventListener('input',draw);if(sb)sb.addEventListener('change',draw);
chips.forEach(function(x){x.addEventListener('click',function(){x.setAttribute('aria-pressed',x.getAttribute('aria-pressed')==='true'?'false':'true');draw();});});
c.addEventListener('click',function(){q.value='';if(sb)sb.value='';chips.forEach(function(x){x.setAttribute('aria-pressed','false');});draw();q.focus();});
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
      {SUB_SELECT}
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

# What we track (owner task 2 Nov 2026): the counts the trust pages and Home's sellers card show, all from site.json;
# each line is drawn only when its data is there (never a placeholder).
N_SELLERS = len(SHOPS)
N_CLINIC_PAGES = len(CLINIC_PROFILES)
N_CLINICS = len({r["seller_slug"] for r in PLANS})
N_LETTERS = DATA.get("letters_all_total") or len(LETTERS_ALL)
N_STATUS = len({r["substance_slug"] for r in LEGAL_DB or []})
PULLED = nice_date(DATA["pulled_at"][:10]) if DATA.get("pulled_at") else ""
SCORE_ON = max((r["score_checked_on"] for r in SHOPS.values() if r.get("score_checked_on")), default="")
# Home's hero counts (pages.md, Home; owner task 2 Nov 2026): one sentence, only when every count and the pull date are there.
# owner answer Q1 c (2 Nov 2026): shops and online clinics counted apart, as on /sellers/
_ns, _nc = len(SHOPS), len(CLINIC_PROFILES)
HERO_COUNTS = (f" {_ns} shop{'' if _ns == 1 else 's'}, {f'{_nc} online clinic' + ('' if _nc == 1 else 's') + ', ' if _nc else ''}"
               f"{len(PEPTIDE_SLUGS)} substances and {N_LETTERS} FDA warning letters, checked {PULLED}."
               if SHOPS and PEPTIDE_SLUGS and N_LETTERS and PULLED else "")

# Sellers we track (pages.md, Home, under "Latest FDA warning letters"): the letters block's look, one line and
# btn-line "See all sellers". No seller names on Home.
SELLERS_HOME = f"""
<section class="section" id="sellers-home">
  <div class="wrap home-cards">
    <div class="home-card">
    <div class="sec-hd"><div><h2>Sellers we track</h2><p>{N_SELLERS} shops that sell peptides online, each with five background checks.{f" Checked {nice_date(SCORE_ON)}." if SCORE_ON else ""}</p></div></div>
    <p class="letters-all"><a class="btn btn-line" href="/sellers/">See all sellers</a></p>
    </div><!--compare-card-->
  </div>
</section>
""" if SHOPS else ""

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
    <p class="lede hero-after">For each goal we put peptide products next to the FDA-approved alternatives and show what the evidence says, what it costs per month and how you would get it. We compare; we never sell.{HERO_COUNTS}</p>
    </div>
    <section class="glossary" aria-labelledby="glossary-h">
      <h2 id="glossary-h">What the labels mean</h2>
      <dl class="glossary-list">{GLOSSARY}</dl>
    </section>
    {guides.home_card()}
    <section class="rate-strip" aria-labelledby="rate-h">
      <div class="rate-hd"><h2 id="rate-h">How we rate</h2><p>Every seller gets the same five checks, in this order. They are facts we hold about the seller, not a safety grade.</p><a href="/how-we-rate/">Read the full method</a></div>
      <ul class="criteria">
        <li><h3>Lab reports</h3><p>A lab report dated in the last 12 months.</p></li>
        <li><h3>No FDA letter</h3><p>No FDA warning letter matched to its web or street address.</p></li>
        <li><h3>Company found</h3><p>The business behind the shop found in a state registry.</p></li>
        <li><h3>Legal pages</h3><p>A terms page and a privacy or refund page, seen in the last 30 days.</p></li>
        <li><h3>Fresh prices</h3><p>A price per milligram seen in the last 30 days.</p></li>
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
    <div class="sec-hd"><div><h2>Is it legal today?</h2><p>FDA status of the peptides people ask about most, each with its source. Checked {LEGAL_CHECKED}.</p></div>{ALL_SUBSTANCES}</div>
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
{SELLERS_HOME}
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

# What we track (pages.md, Trust pages, About; owner task 2 Nov 2026): one line per count that site.json holds.
_track = [f'<li><a href="/sellers/">{N_SELLERS} shops</a> that sell peptides online, each with its five checks.</li>' if N_SELLERS else "",
          (f'<li><a href="/sellers/#clinics">{N_CLINICS} online clinics</a> with plan prices, each with its five checks.</li>' if N_CLINIC_PAGES
           else f"<li>{N_CLINICS} online clinics with plan prices.</li>") if N_CLINICS else "",
          (f'<li><a href="/fda-warning-letters/">{N_LETTERS} FDA warning letters</a> to peptide sellers, compounders and online clinics.</li>'
           if LETTERS_ALL else f"<li>{N_LETTERS} FDA warning letters to peptide sellers, compounders and online clinics.</li>") if N_LETTERS else "",
          f"<li>{N_STATUS} substances with an FDA status, each with its source.</li>" if N_STATUS else ""]
ABOUT_TRACK = (f"""<h2>What we track</h2>
<ul>
{"".join(x + chr(10) for x in _track if x)}</ul>
<p>{f"Last data pull: {PULLED}. " if PULLED else ""}The data comes from the sellers' public pages, the FDA and state business registries, read by our own crawler. Items marked for review are checked by a person before they are published.</p>
""" if any(_track) else "")

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
{ABOUT_TRACK}<h2>What we do not do</h2>
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

# How we rate (pages.md, Trust pages; owner task 2 Nov 2026): the five seller checks exactly as the seller pages and
# the price windows show them (site.sellers in peptide-data), then the goal page rule. URL, title and H1 unchanged.
HOW = f"""
<section class="page"><div class="wrap prose">
<h1>How we rate peptide products and sellers</h1>
<p class="lede">We judge every seller by the same five checks and build every goal page by the same rule. The checks are facts we hold about a seller, not a safety grade.</p>
<p class="small meta">{AUTHOR}. Last updated {STAMP_CHECKED}. Every claim links to its source. Prices checked {STAMP_CHECKED}.</p>
<h2>The five seller checks</h2>
<p>{f'We track <a href="/sellers/">{N_SELLERS} shops{f" and {N_CLINIC_PAGES} online clinics" if N_CLINIC_PAGES else ""}</a>. ' if N_SELLERS else ""}Every seller page and every price window shows a line such as "3 of 5 checks". These are the five, in the order the seller page shows them. We recompute all five each time we pull our data, and the seller page shows the date as "Checked" and a date{f"; the last pull was on {PULLED}" if PULLED else ""}.</p>
<h3>Lab reports</h3>
<p>Met when the seller has published at least one lab report (a certificate of analysis) dated in the last 12 months, for any of its products. We read the reports on the seller's own pages. A miss means we found no report from the last 12 months; it does not mean a product failed a test. A lab report shows what one batch contained on the day it was tested, not that a product is safe or that it works.</p>
<h3>No FDA letter</h3>
<p>Met when the FDA's public list of warning letters holds no letter matched to the seller by its web address or street address. A letter that only shares a company name is not counted, because names repeat. A miss means the FDA sent the seller at least one warning letter; the seller page links each one.{f' We keep every letter to peptide sellers, compounders and online clinics, {N_LETTERS} so far, on our <a href="/fda-warning-letters/">FDA warning letters</a> page.' if LETTERS_ALL and N_LETTERS else ""}</p>
<h3>Company found</h3>
<p>Met when we find the business behind the shop in a state business registry, matched with high confidence. A miss means we did not find it. We do not search every state's registry yet, so a real company can still show as not found. When an FDA letter names the company, the seller page says so, but that alone does not meet this check.</p>
<h3>Legal pages</h3>
<p>Met when the seller's site has a terms page and a privacy or refund page, seen by our crawler in the last 30 days. A miss means we did not see those pages in that time. Having them says nothing about what they promise.</p>
<h3>Fresh prices</h3>
<p>Met when our own price crawl saw at least one price per milligram on the seller's site in the last 30 days. A miss means our prices for this seller are older than that, so read them with care.</p>
<h3>What the score does not tell you</h3>
<p>A seller with 5 of 5 can still sell a product that is not approved for any use. A seller with 0 of 5 is one where we found none of the five facts, not one where we found five problems; only a missed "No FDA letter" check means we found something against the seller. Read the checks one by one.</p>
<h2>How a goal page is built</h2>
<ul>
<li>When the FDA has approved a treatment for the goal, it is listed first.</li>
<li>Research-use peptides are shown with one sentence on their FDA status. We never link to a research-use seller: the price window lists the shops by name, and each name opens our page on that seller.</li>
<li>Online clinics get a grey "Online clinic" button with "No paid link yet" under it until we have a paid link with that clinic. A paid link is a green button with "Paid link" under it.</li>
<li>Every price shows the date we checked it, and every claim links to its source.</li>
</ul>
<h2>What does not change a check</h2>
<p>Paid links, partnership requests and a seller asking us. A seller with a paid link is checked the same way as one without, and no one can buy a higher score or a better place on a page.</p>
<h2>Corrections</h2>
<p>If you find an error, email <a href="mailto:{EMAIL}">{EMAIL}</a> with the page and the source. We correct confirmed errors, note the date of the change and list it on our <a href="/corrections/">corrections page</a>.</p>
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
    return category_body(g, table, f'{g["options_checked"]} options checked on the same rule. Rows that are not approved for human use carry no price and no seller.')


KIND_CHIP = {"brand": ("ok", "Brand"), "compounded": ("warn", "Compounded"), "program": ("neutral", "Program"),
             # owner task 2 Nov 2026: "other" (a membership or a bundle) is never called compounded; "generic" (an approved
             # medicine under its own name) renders once the data side sends it
             "other": ("neutral", "Other"), "generic": ("ok", "Generic")}
KIND_NOTE = {"other": "a membership or a bundle, see the clinic's page"}


def plan_chip(g, r):
    """What a plan is, as a chip: "Brand, diabetes" (chip-info) for a brand approved for another use (owner answer Q1 a,
    2 Nov 2026: Ozempic is approved for diabetes, not weight loss), else the KIND_CHIP of its kind."""
    use = other_use(g, r)
    chip, label = ("info", f"Brand, {use}") if use else KIND_CHIP[plan_kind(r)]
    note = KIND_NOTE.get(plan_kind(r), "") if not use else ""
    return f'<span class="chip chip-{chip}">{label}</span>' + (f'<span class="sub">{note}</span>' if note else "")


def plan_kind(r):
    """"program" for a plan that names no medication, "brand" for branded or oral_branded, "other" and "generic" as the
    data names them, else "compounded"."""
    k = r.get("product_kind")
    if k in ("other", "generic"):  # the data's own kind first: Ivim's membership names no medicine and is still "other"
        return k
    if not r["substance_slug"]:
        return "program"
    return "brand" if k in BRANDED else "compounded"


def care_note(r):
    """"+ $99/mo care" when the plan adds a monthly membership, "all-in" when it adds none, "care fee not known" when the
    data has no fee (owner answer Q3 b, 2 Nov 2026)."""
    fee = r.get("membership_fee_monthly")
    return "care fee not known" if fee is None else "all-in" if float(fee) == 0 else f"+ {usd(fee)}/mo care"


CLINICS_FIRST = 10
# "Compare any two" (btn-line) under the clinic table and under the sellers table; /compare/ is built when plans or sellers exist
COMPARE_LINK = ('<p class="cmp-link"><a class="btn btn-line" href="/compare/">Compare any two</a></p>'
                if DATA.get("plans") or DATA.get("seller_profiles") else "")
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
        trs.append(f'<tr{more}><td>{clinic_link(r["seller_slug"], seller_base(r["seller_name"]))}</td><td data-l="Plan">{r["plan_name"]}</td>'
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
    {COMPARE_LINK}
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
    <div class="sec-hd"><div><h2>Is it legal today?</h2><p>FDA status of the peptides on this page, each with its source. Checked {legal_checked}.</p></div>{ALL_SUBSTANCES}</div>
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
        what = {"brand": "FDA-approved brand", "compounded": "Compounded, not FDA approved", "program": "A program; the medicine is not named",
                "other": "A membership or a bundle", "generic": "FDA-approved generic"}[plan_kind(r)]
        care = care_note(r)
        pad = f"""
      <div class="board rx" aria-label="Price pad">
        <div class="rx-head"><span class="rx-mark" aria-hidden="true">&#8478;</span><h2>Cheapest clinic plan, per month</h2></div>
        <p class="hero-num"><span class="num-xl">{usd(r["price_monthly"])}</span> <span class="num-unit">/mo from</span>{pad_ref}</p>
        <div class="ledger"><span>{r["plan_name"]}, {clinic_link(r["seller_slug"], seller_base(r["seller_name"]), True)}</span></div>
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
    if r["seller_slug"] in CLINIC_PROFILES:
        base = re.sub(r"\s*\(.*\)", "", name).strip()
        for t in (f"{name} review: plans, prices and checks | Peptide Chooser", f"{base} review: plans, prices and checks | Peptide Chooser",
                  f"{base} review: plans, prices and checks", f"{base} review | Peptide Chooser"):
            if len(t) <= 60:
                return t
        return f"{base} review"
    for t in (f"{name} review: prices, lab reports, FDA letters | Peptide Chooser",
              f"{name} review: prices, lab reports, FDA letters",
              f"{name} review: prices and lab reports", f"{name} review | Peptide Chooser", f"{name} review"):
        if len(t) <= 60:
            return t
    return t


def clinic_description(r):
    """Clinic meta description (owner task 2 Nov 2026: 150 to 160 characters), from data. Facts in a fixed order (the
    clinic and every medicine it prescribes, the lowest monthly price with its care fee, the FDA letters, the check date,
    the tracking date); the first version from 150 to 160 characters wins, trying the clinic's short name and "N medicines"
    before dropping facts from the end. Never a partial list of medicines."""
    plans, base = clinic_plan_rows(r), seller_base(seller_name(r))
    subs = sorted({sub_label(p["substance_slug"]) for p in plans if p["substance_slug"]}, key=str.lower)
    n = r.get("fda_letter_count") or 0
    letters = "No FDA warning letter." if not n else f"{plural(n, 'FDA warning letter')}, the newest {nice_date(newest_letter(r))}."
    fee = plans[0].get("membership_fee_monthly") if plans else None
    care = "care fee not known" if fee is None else "no care fee" if float(fee) == 0 else f"plus {usd(fee)}/mo care"
    price = f"{plural(len(plans), 'plan')} from {usd(plans[0]['price_monthly'])}/mo, {care}." if plans else ""
    on = nice_date(r["score_checked_on"]) if r.get("score_checked_on") else ""
    score = f"{r['score']} of {len(SCORE_CHECKS)} checks met on {on}." if on else ""
    checked = f"{r['score']} of {len(SCORE_CHECKS)} checks met." if on else ""
    since = f"Tracked since {nice_date(r['first_seen'])}." if r.get("first_seen") else ""
    whats = ([subs[0] if len(subs) == 1 else ", ".join(subs[:-1]) + " and " + subs[-1], f"{len(subs)} medicines"] if len(subs) > 1
             else [subs[0]] if subs else [""])
    tries = []
    for what in whats:
        for name in (seller_name(r), base):
            first = f"{name} is an online clinic{' that prescribes ' + what if what else ''}."
            for parts in ((first, price, letters, score, since), (first, price, letters, checked, since), (first, price, letters, score),
                          (first, price, letters, since), (first, price, letters, checked), (first, price, letters)):
                tries.append(" ".join(x for x in parts if x))
    return next((t for t in tries if 150 <= len(t) <= 160), next((t for t in tries if len(t) <= 160), tries[-1]))


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
    lab = "None found." if r["seller_slug"] in CLINIC_PROFILES else (f"{plural(r['coa_count'], 'lab report')}, the newest dated {nice_date(r['newest_coa_date'])}."
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


CLINIC_LAB_LINE = '<p class="check-nolab">Online clinics prescribe; they do not publish lab reports, so a clinic meets at most 4 of the 5 checks.</p>'


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
        <ul class="check-list">{rows}</ul>{CLINIC_LAB_LINE if r["seller_slug"] in CLINIC_PROFILES else ""}
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
    group = CLINIC_PROFILES if r["seller_slug"] in CLINIC_PROFILES else SHOPS
    same = [x for x in group.values() if x["seller_slug"] != r["seller_slug"] and x.get("seller_kind") == r.get("seller_kind")]
    same.sort(key=lambda x: (abs((x.get("score") or 0) - (r.get("score") or 0)), -(x.get("product_count") or 0), seller_name(x).lower()))
    return same[:n]


def card_count(x):
    """A card's second line: "61 products" for a shop, "6 plans from $70/mo" for a clinic."""
    if x["seller_slug"] in CLINIC_PROFILES:
        plans = clinic_plan_rows(x)
        low = min((float(p["price_monthly"]) for p in plans if p.get("price_monthly") is not None), default=None)
        return plural(len(plans), "plan") + (f" from {usd(low)}/mo" if low is not None else "")
    return plural(x.get("product_count") or 0, "product")


def similar_section(r):
    cards = "".join(
        f'<li class="panel-line"><a class="name" href="/sellers/{x["seller_slug"]}/">{seller_name(x)}</a>'
        f'<span class="small">{x["score"]} of {len(SCORE_CHECKS)} checks</span><span class="small">{card_count(x)}</span></li>'
        for x in similar_sellers(r))
    return f"""
<section class="section" id="other-sellers">
  <div class="wrap">
    <h2 class="h-sources">Compare other {"clinics" if r["seller_slug"] in CLINIC_PROFILES else "sellers"}</h2>
    <ul class="seller-cards">{cards}</ul>
    <p class="small" style="margin-top:16px"><a href="/sellers/">All sellers we track</a></p>
  </div>
</section>""" if cards else ""


# Clinic profile (pages.md, Seller, clinics; owner task 2 Nov 2026): the Seller page type for a seller with plans and no
# products. Plans from site.plan_prices; no price per mg anywhere; the lab-report check is never met (clinics publish none).
def clinic_plan_rows(r):
    return sorted((p for p in PLANS if p["seller_slug"] == r["seller_slug"] and p.get("price_monthly") is not None),
                  key=lambda p: (float(p["price_monthly"]), p["plan_name"]))


def plan_goal(p):
    """The goal whose clinic plans carry the plan's medication (for the "Brand, diabetes" chip), else {}."""
    return next((g for g in ALL_GOALS if p["substance_slug"] in ((g.get("clinic_plans") or {}).get("substances") or [])), {})


def care_words(p):
    fee = p.get("membership_fee_monthly")
    return "care fee not known" if fee is None else "no separate care fee" if float(fee) == 0 else f"plus {usd(fee)} a month for care"


def cheapest_elsewhere(p):
    """The lowest monthly price for the same medication and kind at another clinic, or None."""
    if not p["substance_slug"]:
        return None
    rows = [x for x in PLANS if x["seller_slug"] != p["seller_slug"] and x["substance_slug"] == p["substance_slug"]
            and plan_kind(x) == plan_kind(p) and x.get("price_monthly") is not None]
    return min(rows, key=lambda x: (float(x["price_monthly"]), x["seller_name"]), default=None)


def clinic_answer(r):
    """The clinic short answer (Tier 1 template): one sentence per field, a missing field drops its sentence."""
    plans, name = clinic_plan_rows(r), seller_name(r)
    subs = sorted({sub_label(p["substance_slug"]) for p in plans if p["substance_slug"]}, key=str.lower)
    what = (subs[0] if len(subs) == 1 else ", ".join(subs[:-1]) + " and " + subs[-1]) if subs else ""
    out = [f"{name} is an online clinic{' that prescribes ' + what if what else ''}."]
    if plans:
        low = plans[0]
        out.append(f"It has {plural(len(plans), 'plan')} on its price page; the lowest is {usd(low['price_monthly'])} a month "
                   f"({clean(low['plan_name'])}), {care_words(low)}." if len(plans) > 1 else
                   f"It has one plan on its price page, {clean(low['plan_name'])}, at {usd(low['price_monthly'])} a month, {care_words(low)}.")
    n = r.get("fda_letter_count")
    if n == 0:
        out.append("No FDA warning letter.")
    elif n:
        out.append(f"{plural(n, 'FDA warning letter')}, the newest on {nice_date(newest_letter(r))}.")
    if shown_company(r) and r.get("entity_evidence") == "registry":
        out.append(f"Registered company: {clean(r['entity_name'])}.")
    elif shown_company(r) and r.get("entity_evidence") == "fda_letter":
        out.append(f"Company named in an FDA letter: {clean(r['entity_name'])}.")
    else:
        out.append("No registered company found.")
    return out


def clinic_plans_section(r):
    plans = clinic_plan_rows(r)
    if not plans:
        return ""
    trs = []
    for p in plans:
        other = cheapest_elsewhere(p)
        elsewhere = (f'<span class="num">{usd(other["price_monthly"])}</span><span class="sub">{clinic_link(other["seller_slug"], seller_base(other["seller_name"]))}</span>'
                     if other else '<span class="sub">no other clinic</span>' if p["substance_slug"] else '<span class="sub">no medication named</span>')
        fee = p.get("membership_fee_monthly")
        trs.append(f'<tr><td><span class="name">{clean(p["plan_name"])}</span></td><td data-l="What it is">{plan_chip(plan_goal(p), p)}</td>'
                   f'<td class="num" data-l="Per month">{usd(p["price_monthly"])}</td>'
                   f'<td data-l="Care fee">{"not known" if fee is None else "none" if float(fee) == 0 else usd(fee) + "/mo"}</td>'
                   f'<td data-l="Cheapest elsewhere">{elsewhere}</td>'
                   f'<td data-l="Prices checked">{nice_date(p["last_seen"])}</td></tr>')
    return f"""
<section class="band-2" id="plans">
  <div class="wrap">
    <div class="sec-hd"><div><h2>Plans and prices</h2><p>Every plan on the clinic's price page, cheapest first, with the lowest price for the same medication and kind at another clinic we track.</p></div></div>
    <div class="tbl-wrap"><table class="tbl tbl-cards tbl-clinics tbl-plans">
      <thead><tr><th scope="col">Plan</th><th scope="col">What it is</th><th scope="col">Per month</th><th scope="col">Care fee</th><th scope="col">Cheapest elsewhere</th><th scope="col">Prices checked</th></tr></thead>
      <tbody>{"".join(trs)}</tbody>
    </table></div>
    <p class="small" style="margin-top:16px">Per month is the clinic's published monthly price for the plan; the care fee is its monthly membership, when it shows one.</p>
    <p class="cmp-link"><a class="btn btn-ink" href="/compare/?a=p.{r["seller_slug"]}.{plans[0]["plan_slug"]}">Compare with another clinic</a></p>
  </div>
</section>"""


LEGIT_CLOSE = "These are the facts we hold; we do not call any seller legit or safe, and we never link to the shop."


def legit_heading(r):
    """The one place the site may write "legit" (owner decision 2 Nov 2026; pages.md, Rules that apply to every page):
    this question, as the H2 of a seller page. tools/check.py allows the word nowhere else."""
    return f"Is {seller_base(seller_name(r))} legit? What we can check"


LEGIT_TAIL = " Is it legit? See the five checks."


def legit_description(d):
    """A seller page's description under 150 characters gets LEGIT_TAIL (owner task 2 Nov 2026), when it still fits
    in the 160 characters tools/check.py allows."""
    return d + LEGIT_TAIL if len(d) < 150 and len(d) + len(LEGIT_TAIL) <= 160 else d


def legit_section(r):
    """"Is <Name> legit? What we can check" (pages.md, Seller; owner task 2 Nov 2026): right after the short answer, the five
    checks in the seller page's order, each "Met:" or "Not met:" with the check card's fact, then the closing sentence."""
    lines = check_lines(r)
    # a check that has not run yet says so, not "Not met" (owner answer Q3 b, 2 Nov 2026): today the legal pages, while
    # terms, privacy and refund are all unknown
    unrun = {"score_legal_pages": "Terms, privacy and refund pages."} if all(
        r.get(f"{x}_seen") is None for x in ("terms", "privacy", "refund")) and not r.get("score_legal_pages") else {}
    state = lambda k: "Not checked yet" if k in unrun else "Met" if r.get(k) else "Not met"
    items = "".join(
        f'<li><span class="chip chip-{"ok" if r.get(k) else "neutral"} mark-{"yes" if r.get(k) else "no"}">{t}</span>'
        f'<span class="check-line">{state(k)}: {unrun.get(k, lines[k])}</span></li>'
        for k, t in SCORE_CHECKS)
    return f"""
<section class="section legit" id="legit">
  <div class="wrap">
    <h2>{legit_heading(r)}</h2>
    <ul class="check-list legit-list">{items}</ul>
    <p class="small legit-close">{LEGIT_CLOSE}</p>
  </div>
</section>"""


def seller_page(r):
    clinic = r["seller_slug"] in CLINIC_PROFILES
    answer = " ".join(clinic_answer(r) if clinic else short_answer(r))
    seen = r.get("price_updated_at")
    meta = (f'{AUTHOR}. Tracked since {nice_date(r["first_seen"])}.' if r.get("first_seen") else f"{AUTHOR}.") + \
           (f" Prices checked {nice_date(seen[:10])}." if seen else "")
    return f"""
<section class="hero hero-goal seller-pg">
  <div class="wrap">
    <div class="hero-grid">
      <div>
        <h1>{seller_name(r)}: prices, checks and what we found.</h1>
        <p class="seller-kind"><span class="chip chip-neutral">{kind_words(r)[1]}</span></p>
        <p class="small meta">{meta}</p>
        <p class="intro">{answer}</p>
      </div>{check_card(r)}
    </div>
  </div>
</section>{legit_section(r)}{clinic_plans_section(r) if clinic else seller_subs_section(r)}{seller_letters_section(r)}{seller_company_section(r)}{similar_section(r)}
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
    rows, more_cls = sorted(SHOPS.values(), key=sellers_order), ' class="more"'
    trs = "".join(
        f'<tr{more_cls if i >= SELLERS_FIRST else ""}><td><a class="name" href="/sellers/{r["seller_slug"]}/">{seller_name(r)}</a></td>'
        f'<td data-l="Kind">{kind_words(r)[1]}</td><td class="num" data-l="Checks">{r["score"]} of {len(SCORE_CHECKS)}</td>'
        f'<td class="num" data-l="Products">{r.get("product_count") or 0}</td><td class="num" data-l="Substances">{r.get("substance_count") or 0}</td>'
        f'<td class="num" data-l="FDA letters">{r.get("fda_letter_count") or 0}</td></tr>'
        for i, r in enumerate(rows))
    checked = max((r["score_checked_on"] for r in PROFILES.values() if r.get("score_checked_on")), default="")
    clinics = sorted(CLINIC_PROFILES.values(), key=lambda r: (-(r.get("score") or 0), seller_name(r).lower()))
    counts = f"{plural(len(rows), 'shop')}{' and ' + plural(len(clinics), 'online clinic') if clinics else ''}"
    more = (f'<p class="legal-more sellers-more" hidden><button type="button" class="btn btn-line" id="sellers-all">Show all {len(rows)}</button></p>'
            if len(rows) > SELLERS_FIRST else "")
    return f"""
<section class="section letters-hd">
  <div class="wrap">
    <h1>Peptide sellers we track</h1>
    <p class="lede">{counts}: every shop in our database that sells peptides online, with its five checks, how many products and substances it lists, and its FDA warning letters{", then the online clinics with their plans" if clinics else ""}. Each name opens our page on the seller; we do not link to the shops or the clinics.</p>
    <p class="letters-stamp">{f'<span class="stamp">Checked {nice_date(checked)}</span>' if checked else ""}<span class="small">Shops: most checks first, then most products.</span></p>
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
    {COMPARE_LINK}
    <p class="small" style="margin-top:16px">Checks are facts we hold about the seller, not a safety or quality grade. <a href="/how-we-rate/">How we rate</a></p>
  </div>
</section>{clinics_directory(clinics)}
{SELLERS_INDEX_JS}
"""


def clinics_directory(clinics):
    """"Online clinics" on /sellers/ (pages.md, Sellers; owner task 2 Nov 2026): one row per clinic page, under the shops."""
    if not clinics:
        return ""
    trs = []
    for r in clinics:
        plans = clinic_plan_rows(r)
        low = min((float(p["price_monthly"]) for p in plans), default=None)
        trs.append(f'<tr><td><a class="name" href="/sellers/{r["seller_slug"]}/">{seller_name(r)}</a></td>'
                   f'<td class="num" data-l="Plans">{len(plans)}</td><td class="num" data-l="From">{usd(low) + "/mo" if low is not None else "unknown"}</td>'
                   f'<td class="num" data-l="Checks">{r["score"]} of {len(SCORE_CHECKS)}</td><td class="num" data-l="FDA letters">{r.get("fda_letter_count") or 0}</td>'
                   f'<td class="num" data-l="Checked">{nice_date(r["score_checked_on"]) if r.get("score_checked_on") else "unknown"}</td></tr>')
    return f"""
<section class="section" id="clinics">
  <div class="wrap">
    <div class="sec-hd"><div><h2>Online clinics</h2><p>{plural(len(clinics), 'online clinic')} with plan prices, most checks first. Clinics prescribe and publish no lab reports, so a clinic meets at most 4 of the 5 checks.</p></div></div>
    <div class="tbl-wrap"><table class="tbl tbl-cards tbl-sellers" id="clinics-table"><caption class="vh">Online clinics, most checks first</caption>
      <thead><tr><th scope="col">Clinic</th><th scope="col">Plans</th><th scope="col">From</th><th scope="col">Checks</th><th scope="col">FDA letters</th><th scope="col">Checked</th></tr></thead>
      <tbody>{"".join(trs)}</tbody>
    </table></div>
  </div>
</section>"""


# 404 (pages.md, 404; owner task 2 Nov 2026): the goal pages, then the sections that exist, and the search line.
_NF_MORE = [("/sellers/", "Sellers we track", PROFILES), ("/peptides/", "Peptides A to Z", PEPTIDE_SLUGS), ("/learn/", "Guides", True)]
NOT_FOUND = f"""
<section class="page"><div class="wrap prose">
<h1>This page doesn't exist</h1>
<p class="lede">The link may be old or mistyped. Try the search above.</p>
<div class="btn-row"><a class="btn btn-ink" href="/">Go to the home page</a></div>
<ul class="nf-links">{"".join(f'<li><a href="{goal_href(g)}">{g["label"]}</a></li>' for g in ALL_GOALS)}</ul>
<ul class="nf-links">{"".join(f'<li><a href="{u}">{t}</a></li>' for u, t, ok in _NF_MORE if ok)}</ul>
</div></section>
"""

PAGES = [
    ("/", "index.html", "Best peptides by goal, compared | Peptide Chooser",
     "FDA status, real prices and evidence for each goal, checked and dated. Peptides next to the approved alternatives, from a site that never sells.",
     HOME, ORG_SCHEMA, None),
    ("/about/", "about/index.html", "About Peptide Chooser",
     "Peptide Chooser is an independent site that compares peptide products and sellers for people in the United States.", ABOUT, "", [("/about/", "About")]),
    ("/how-we-rate/", "how-we-rate/index.html", "How we rate peptide products and sellers | Peptide Chooser",
     "The five checks Peptide Chooser runs on every peptide seller (lab reports, FDA letters, company, legal pages, fresh prices) and how each goal page is built.", HOW, "", [("/how-we-rate/", "How we rate")]),
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
                  LETTERS_PAGE, item_list_schema("FDA warning letters to peptide sellers and online clinics",
                                                 [(f'{clean(r["company_name"])}: {clean(r["letter_subject"])}', r["letter_url"]) for r in LETTERS_ALL]),
                  [("/fda-warning-letters/", "FDA warning letters")]))

for _g in ALL_GOALS:
    if _g.get("page"):
        PAGES.append((f"/{_g['slug']}/", f"{_g['slug']}/index.html", _g["title"], _g["description"],
                      category_page(_g), "", [(f"/{_g['slug']}/", _g["name"])]))

if PROFILES:
    PAGES.append(("/sellers/", "sellers/index.html", "Peptide sellers and their checks | Peptide Chooser",
                  (f"The {len(SHOPS)} peptide shops and {len(CLINIC_PROFILES)} online clinics in our database, each with five background "
                   "checks, products or plans and FDA warning letters. We never link to them.") if CLINIC_PROFILES else
                  (f"Every peptide seller in our database, {len(PROFILES)} in all, with five background checks, product and "
                   "substance counts and FDA warning letters. We never link to them."),
                  sellers_index(),
                  # ItemList (owner task 2 Nov 2026): one item per seller page on our site, never the seller's own domain
                  item_list_schema("Peptide sellers and their checks",
                                   [(seller_name(r), f"{SITE}/sellers/{r['seller_slug']}/") for r in sorted(PROFILES.values(), key=lambda x: x["seller_slug"])]),
                  [("/sellers/", "Sellers")]))
    for _r in sorted(PROFILES.values(), key=lambda x: x["seller_slug"]):
        PAGES.append((f"/sellers/{_r['seller_slug']}/", f"sellers/{_r['seller_slug']}/index.html", seller_title(_r),
                      legit_description(clinic_description(_r) if _r["seller_slug"] in CLINIC_PROFILES else seller_description(_r)), seller_page(_r), "",
                      [("/sellers/", "Sellers"), (f"/sellers/{_r['seller_slug']}/", seller_name(_r))]))


# Site search and "Compare any two" (pages.md, Every page, Header, Search; Search; Compare; owner task 2 Nov 2026).
# /search-index.json holds one entry per page, substance with a database status and seller; the header field and /search/
# filter it in the page. /compare/ puts two clinic plans or two sellers side by side from data embedded in the page.
NOINDEX = {"/search/"}
TYPE_ORDER = {"Goal": 0, "Peptide": 1, "Seller": 2, "Clinic": 3, "Page": 4}


def search_index():
    """{type, name, aliases, url, line} per page we have (not /search/ or the seller pages, which are Seller entries), per
    substance with a database status and per seller page. `line` is one plain line: the goal page, the substance's status,
    the seller's kind and "N of 5 checks"."""
    out = []
    goal_pages = {f"/{g['slug']}/": g for g in ALL_GOALS if g.get("page")}
    for path, _, title, desc, *_ in PAGES:
        if path in NOINDEX or path.startswith("/sellers/") and path != "/sellers/" or path.startswith("/peptides/") and path != "/peptides/":
            continue
        g = goal_pages.get(path)
        if g:
            out.append({"type": "Goal", "name": g["label"], "aliases": sorted({g["name"], g["short"], g["slug"].replace("-", " ")} - {g["label"]}),
                        "url": path, "line": f"Goal page: {plural(len(g['peptides']), 'option')} with FDA status and prices"})
        else:
            out.append({"type": "Page", "name": "Home" if path == "/" else title.replace(" | Peptide Chooser", ""), "aliases": [],
                        "url": path, "line": desc.split(". ")[0].rstrip(".") + "."})
    for slug in PEPTIDE_SLUGS:  # a substance goes to its own page (owner task 2 Nov 2026)
        s = pep_status(slug)
        names = {r["peptide"] for r in LEGAL["rows"] if slug in (r.get("substances") or [])}
        names |= {p["name"] for g in ALL_GOALS for p in g["peptides"] if subs_of(p) == [slug]}
        names |= {sub_label(slug), slug.replace("-", " ")}
        out.append({"type": "Peptide", "name": s["name"], "aliases": sorted(names - {s["name"]}),
                    "url": f"/peptides/{slug}/", "line": f"{s['label']}: {s['sentence']}"
                    + (f' FDA listing: "{s["listing"]}".' if s.get("listing") else "")})
    for r in sorted(CLINIC_PROFILES.values(), key=sellers_order):
        out.append({"type": "Clinic", "name": seller_name(r), "aliases": [r["domain"]] if r.get("domain") else [],
                    "url": f"/sellers/{r['seller_slug']}/", "line": f"Online clinic, {card_count(r)}, {r['score']} of {len(SCORE_CHECKS)} checks"})
    for r in sorted(SHOPS.values(), key=sellers_order):
        out.append({"type": "Seller", "name": seller_name(r), "aliases": [r["domain"]] if r.get("domain") else [],
                    "url": f"/sellers/{r['seller_slug']}/", "line": f"{kind_words(r)[1]}, {r['score']} of {len(SCORE_CHECKS)} checks"})
    return sorted(out, key=lambda e: (TYPE_ORDER[e["type"]], e["name"].lower()))


SEARCH_PAGE_JS = """<script>
document.addEventListener('DOMContentLoaded',function(){var S=window.pcSearch,f=document.getElementById('sp-form'),inp=document.getElementById('sp-q'),
ol=document.getElementById('sp-results'),st=document.getElementById('sp-status');if(!S||!f)return;f.querySelector('.search-js').hidden=false;
inp.value=new URLSearchParams(location.search).get('q')||'';
function draw(){var v=inp.value.trim();S.load(function(d){var r=S.find(d,v,50);ol.textContent='';r.forEach(function(e){ol.appendChild(S.row(e,true));});
st.textContent=!v?'Type a peptide, a goal or a seller.':r.length?r.length+(r.length===1?' result':' results')+' for "'+v+'".':'Nothing found for "'+v+'". Browse by goal instead.';});}
inp.addEventListener('input',draw);
f.addEventListener('submit',function(e){e.preventDefault();history.replaceState(null,'','/search/'+(inp.value.trim()?'?q='+encodeURIComponent(inp.value.trim()):''));draw();});
draw();});
</script>"""


def search_page():
    return f"""
<section class="section letters-hd search-pg">
  <div class="wrap">
    <h1>Search</h1>
    <form class="search-form" id="sp-form" action="/search/" method="get" role="search">
      <label for="sp-q">Search a peptide, a goal or a seller</label>
      <div class="search-row"><input class="input" id="sp-q" name="q" type="search" autocomplete="off"><button class="btn btn-ink" type="submit">Search</button></div>
      <div class="search-js" hidden><p class="small" id="sp-status" aria-live="polite"></p><ol class="search-results" id="sp-results"></ol></div>
      <noscript><p class="search-nojs">Search needs JavaScript; browse by goal instead.</p></noscript>
    </form>
  </div>
</section>{goals_strip("Browse by goal")}
{SEARCH_PAGE_JS}
"""


def plan_other_use(r):
    return next((u for g in ALL_GOALS for u in [other_use(g, r)] if u), "")


def compare_plan(r):
    """One clinic plan's column: the head and the six rows (pages.md, Compare)."""
    seller = escape(seller_base(r["seller_name"]))
    who = (f'<a class="name" href="/sellers/{r["seller_slug"]}/">{seller}</a>' if r["seller_slug"] in PROFILES
           else f'<span class="name">{seller}</span>')
    use = plan_other_use(r)
    chip, label = ("info", f"Brand, {use}") if use else KIND_CHIP[plan_kind(r)]
    n = r.get("fda_letter_count") or 0
    letter = (f'<a class="chip chip-warn chip-link" href="{LETTERS_URL}">FDA letter {nice_date(r["last_fda_letter_date"])}</a>'
              if n and r.get("last_fda_letter_date") else "None")
    fee = r.get("membership_fee_monthly")
    care = "Not known" if fee is None else "None, all-in" if float(fee) == 0 else f"{usd(fee)}/mo"
    return {"k": "plan", "h": f'{who}<span class="cmp-sub">{escape(r["plan_name"])}</span>', "c": [
        ("Per month", f'<span class="num">{usd(r["price_monthly"])}/mo</span>'),
        ("Care fee", care),
        ("What it is", f'<span class="chip chip-{chip}">{label}</span>'
                       + (f'<span class="cmp-sub">{KIND_NOTE[plan_kind(r)]}</span>' if not use and plan_kind(r) in KIND_NOTE else "")),
        ("Substance", escape(sub_label(r["substance_slug"])) if r.get("substance_slug") else "Names no medication"),
        ("FDA letter", letter),
        ("Prices checked", nice_date(r["last_seen"]))]}


PPM_LOW, PPM_HIGH = 0.01, 100


def compare_ppm(r):
    """The seller's price per mg range from listings between $0.01 and $100/mg: its own lowest and highest, and those of
    its top substances; a value outside the band is a misread unit until the database fixes it (owner, 2 Nov 2026, the
    seller pages' Q6 a rule widened to the top). (None, None) when nothing is left."""
    vals = [r.get("price_per_mg_min"), r.get("price_per_mg_max")]
    vals += [x.get(k) for x in SELLER_SUBS.get(r["seller_slug"], []) for k in ("price_per_mg_min", "price_per_mg_max")]
    vals = [v for v in vals if v is not None and PPM_LOW <= v <= PPM_HIGH]
    return (min(vals), max(vals)) if vals else (None, None)


def compare_seller(r):
    """One seller's column: the head (a link to its page) and the seven rows (pages.md, Compare)."""
    marks = "".join(f'<span class="chip chip-{"ok" if r.get(k) else "neutral"} mark-{"yes" if r.get(k) else "no"}">{t}'
                    f'<span class="vh">: {"yes" if r.get(k) else "no"}</span></span>' for k, t in SCORE_CHECKS)
    ppm = per_mg_range(*compare_ppm(r))
    ppm = ppm[:1].upper() + ppm[1:]
    n = r.get("fda_letter_count")
    letters = ("None" if n == 0 else "Unknown" if n is None else
               f"{n}, the newest on {nice_date(newest_letter(r))}" if newest_letter(r) else str(n))
    state = STATES.get(r.get("entity_state") or "", r.get("entity_state") or "")
    company = ("No registered company found" if not shown_company(r) else
               f'{escape(clean(r["entity_name"]))}{", " + state if state else ""}'
               f'<span class="cmp-sub">{"State registry" if r["entity_evidence"] == "registry" else "Named in an FDA letter"}</span>')
    return {"k": "seller", "h": f'<a class="name" href="/sellers/{r["seller_slug"]}/">{escape(seller_name(r))}</a><span class="cmp-sub">{kind_words(r)[1]}</span>', "c": [
        ("Checks", f'<span class="score"><span class="score-n"><span class="num">{r["score"]}</span> of {len(SCORE_CHECKS)} checks</span>'
                   f'<span class="score-marks">{marks}</span></span>'),
        ("Products", str(r.get("product_count") or 0)),
        ("Substances", str(r.get("substance_count") or 0)),
        ("Per mg", ppm),
        ("FDA letters", letters),
        ("Company", company),
        ("Tracked since", nice_date(r["first_seen"]) if r.get("first_seen") else "Unknown")]}


def compare_items():
    """Every priced clinic plan ("<clinic>: <plan>", by clinic) and every seller page (by name), keyed for the URL."""
    plans = sorted((r for r in PLANS if r.get("price_monthly") is not None),
                   key=lambda r: (seller_base(r["seller_name"]).lower(), r["plan_name"].lower()))
    sellers = sorted(SHOPS.values(), key=lambda r: seller_name(r).lower())
    return ([(f'p.{r["seller_slug"]}.{r["plan_slug"]}', f'{seller_base(r["seller_name"])}: {r["plan_name"]}', compare_plan(r)) for r in plans],
            [(f's.{r["seller_slug"]}', seller_name(r), compare_seller(r)) for r in sellers])


COMPARE_JS = """<script>
(function(){var D={},f=document.getElementById('cmp-form'),a=f.elements.a,b=f.elements.b,
out=document.getElementById('cmp-out'),p=new URLSearchParams(location.search);
function draw(){var x=D[a.value],y=D[b.value];if(!x||!y){out.innerHTML='<p class="cmp-note">Choose two to see them side by side.</p>';return;}
if(x.k!==y.k){out.innerHTML='<p class="cmp-note">Choose two clinic plans or two sellers: a plan and a seller do not share the same facts.</p>';return;}
var h='<table class="cmp"><caption class="vh">'+a.options[a.selectedIndex].text+' and '+b.options[b.selectedIndex].text+'</caption><thead><tr><td></td><th scope="col">'+x.h+'</th><th scope="col">'+y.h+'</th></tr></thead><tbody>';
x.c.forEach(function(c,i){h+='<tr><th scope="row">'+c[0]+'</th><td>'+c[1]+'</td><td>'+y.c[i][1]+'</td></tr>';});
out.innerHTML=h+'</tbody></table>';}
f.addEventListener('submit',function(e){e.preventDefault();history.replaceState(null,'','/compare/?a='+encodeURIComponent(a.value)+'&b='+encodeURIComponent(b.value));draw();});
out.hidden=false;out.innerHTML='<p class="cmp-note">Loading the plans and sellers.</p>';
// the facts load once, after the page (/compare/data.json, about 90 KB), so the page itself stays small (design/site-polish)
fetch('/compare/data.json').then(function(r){return r.json();}).then(function(d){D=d;
if(D[p.get('a')])a.value=p.get('a');if(D[p.get('b')])b.value=p.get('b');draw();})
.catch(function(){out.innerHTML='<p class="cmp-note">The comparison could not load. Open each seller from <a href="/sellers/">the sellers we track</a>.</p>';});})();
</script>"""


COMPARE_DATA = ""


def compare_page():
    plans, sellers = compare_items()
    data = {k: v for k, _, v in plans + sellers}
    opts = lambda items: "".join(f'<option value="{k}">{escape(label)}</option>' for k, label, _ in items)
    groups = ((f'<optgroup label="Clinic plans">{opts(plans)}</optgroup>' if plans else "")
              + (f'<optgroup label="Sellers">{opts(sellers)}</optgroup>' if sellers else ""))
    select = lambda name, label: (f'<div class="cmp-field"><label for="cmp-{name}">{label}</label><select class="input" id="cmp-{name}" name="{name}">'
                                  f'<option value="">Choose a plan or seller</option>{groups}</select></div>')
    checked = max([r["last_seen"] for r in PLANS if r.get("last_seen")] + [r["score_checked_on"] for r in PROFILES.values() if r.get("score_checked_on")], default="")
    global COMPARE_DATA
    COMPARE_DATA = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"""
<section class="section letters-hd">
  <div class="wrap">
    <h1>Compare any two plans or sellers</h1>
    <p class="lede">Pick two online clinic plans or two peptide sellers and see them side by side: price and care fee for a plan; the five checks, products, price per mg and FDA letters for a seller. Seller names open our page on the seller; we do not link to the shops.</p>
    <p class="letters-stamp">{f'<span class="stamp">Checked {nice_date(checked)}</span>' if checked else ""}<span class="small">{plural(len(plans), "clinic plan")} and {plural(len(sellers), "seller")}.</span></p>
  </div>
</section>
<section class="band-2" id="compare-two">
  <div class="wrap">
    <form class="cmp-form" id="cmp-form" action="/compare/" method="get">
      {select("a", "First")}{select("b", "Second")}
      <button class="btn btn-ink" type="submit">Compare</button>
    </form>
    <noscript><p class="cmp-note">The side by side view needs JavaScript. Without it, open each seller from <a href="/sellers/">the sellers we track</a>.</p></noscript>
    <div class="cmp-out" id="cmp-out" aria-live="polite" hidden></div>
    <p class="small" style="margin-top:16px">Checks are facts we hold about the seller, not a safety or quality grade. <a href="/how-we-rate/">How we rate</a></p>
  </div>
</section>
{COMPARE_JS}
"""


PAGES.append(("/search/", "search/index.html", "Search | Peptide Chooser",
              "Search Peptide Chooser for a peptide, a goal or a seller: FDA status, background checks and prices from our data, each with a link to its page.",
              search_page(), "", [("/search/", "Search")]))
if PLANS or PROFILES:
    PAGES.append(("/compare/", "compare/index.html", "Compare any two plans or sellers | Peptide Chooser",
                  "Put two online clinic plans or two peptide sellers side by side: monthly price, care fee, five background checks and FDA warning letters, from our data.",
                  compare_page(), "", [("/compare/", "Compare any two")]))


# Peptide pages (pages.md, Peptide and Peptides; owner task 2 Nov 2026): /peptides/ and one page per substance in
# PEPTIDE_SLUGS, everything from data; a missing fact drops its block. No dose anywhere, no link to a shop or a clinic.
REGIME_WORDS = {"fda_approval": "Drugs@FDA", "fda_503a_category": "503A list", "fda_cat2_safety": "Category 2 list",
                "fda_nomination_withdrawn": "503A nomination", "fda_shortage": "Shortage list"}
VALUE_WORDS = {"approved": "approved", "category_1": "category 1", "category_2": "category 2", "category_3": "category 3",
               "withdrawn": "withdrawn", "in_shortage": "in shortage", "to_be_discontinued": "to be discontinued"}
# forms read off the shops' product names and the clinics' plan forms (only words we find; nothing is guessed)
FORM_WORDS = [("nasal spray", "nasal spray"), ("spray", "spray"), ("capsule", "capsule"), ("serum", "serum"), ("cream", "cream"),
              ("tablet", "tablet"), ("powder", "powder"), ("vial", "vial"), ("pen", "pen")]
PLAN_FORMS = {"injection_vial": "vial", "pen": "pen", "tablet": "tablet", "capsule": "capsule", "topical": "topical", "solution": "topical"}


def pep_status(slug):
    """The substance's status as the legal tables show it: the database's, else its own hand-written row, with the
    source url and the date. None without either."""
    s = db_status(slug)
    if s:
        return dict(s, hand=False)
    r = hand_legal(slug)
    if not r:
        return None
    src = next(x for x in LEGAL["sources"] if x["n"] == r["src"])
    name = re.sub(r"\s*\(.*\)", "", r["peptide"]) if r.get("substances") == [slug] else substance_name(slug)
    return {"chip": r["chip"], "label": r["status"], "sentence": r["note"], "name": name, "url": src["url"],
            "seen": LEGAL["checked"], "hand": True}


def pep_name(slug):
    """The page's name: the database's name for the substance, else the hand row's (without its brands)."""
    s = pep_status(slug)
    db = next((r["canonical_name"] for r in LEGAL_DB or [] if r["substance_slug"] == slug), None)
    return db or s["name"]


def pep_short(slug):
    """The name for titles: without a bracket ("TB-500 (thymosin beta-4 fragment 17-23)" -> "TB-500")."""
    return re.sub(r"\s*\(.*\)", "", pep_name(slug)).strip()


def pep_group(s):
    return "approved" if s["label"] == "FDA approved" else "cosmetic" if s["chip"] == "info" else "not"


def pep_goals(slug):
    """(goal, option) for every option row on a goal page that carries the substance, in the goals' order."""
    return [(g, p) for g in ALL_GOALS if g.get("page") for p in g["peptides"] if slug in subs_of(p)]


def pep_shops(slug):
    """The window's rows (shops only, the same ten), never for an FDA-approved substance (no window there)."""
    s = pep_status(slug)
    return [] if pep_group(s) == "approved" else seller_rows(slug)


def pep_low_shop(slug):
    """The lowest price per mg among the shops shown, within the /compare/ band ($0.01 to $100/mg), or None."""
    rows = [r for r in pep_shops(slug) if r.get("price_per_mg") is not None and PPM_LOW <= r["price_per_mg"] <= PPM_HIGH]
    return min(rows, key=lambda r: (r["price_per_mg"], r["seller_slug"]), default=None)


def pep_plans(slug):
    return sorted((r for r in PLANS if r["substance_slug"] == slug and r.get("price_monthly") is not None),
                  key=lambda r: (float(r["price_monthly"]), r["seller_name"], r["plan_name"]))


def pep_low_plan(slug):
    """The cheapest plan that is not compounded: a pharmacy-made copy is not the approved product (the goal pages' rule,
    owner 31 Oct 2026). None without one."""
    return next((r for r in pep_plans(slug) if r.get("product_kind") != "compounded"), None)


def pep_forms(slug):
    names = [clean(f'{r["product_name"]} {r.get("variant_title") or ""}').lower() for r in pep_shops(slug)]
    found = []
    for n in names:
        for word, form in FORM_WORDS:
            if word in n and form not in found and not (form == "spray" and "nasal spray" in found):
                found.append(form)
                break
    found += [PLAN_FORMS[r["dosage_form"]] for r in pep_plans(slug) if PLAN_FORMS.get(r.get("dosage_form") or "")]
    return list(dict.fromkeys(found))


def pep_rx(slug, s):
    """Prescription needed, from the status: an approved medicine needs one unless the goal page sells it over the counter."""
    group = pep_group(s)
    if group == "approved":
        otc = any("over the counter" in p["how"].lower() for _, p in pep_goals(slug) if subs_of(p) == [slug])
        return ("No, sold over the counter", "Over the counter") if otc else ("Yes", "Prescription")
    if group == "cosmetic":
        return "No, sold as a cosmetic", ""
    if s["label"] == "Pharmacy-made":
        return "Yes, when a pharmacy compounds it", "Prescription"
    return "Not applicable: not approved for use in people", "Research-use"


def pep_db_rows(slug):
    return [r for r in LEGAL_DB or [] if r["substance_slug"] == slug]


def pep_answer(slug):
    """The short answer, one sentence per fact, each with its link; a missing fact drops its sentence."""
    s = pep_status(slug)
    host = "FDA source" if "fda.gov" in s["url"] else "Source"
    out = [f'{s["label"]}: {s["sentence"]}. <a href="{escape(s["url"])}" rel="nofollow">{host}</a>, {nice_date(s["seen"])}.']
    goals = list(dict.fromkeys(g["slug"] for g, _ in pep_goals(slug)))
    if goals:
        gs = [next(g for g in ALL_GOALS if g["slug"] == x) for x in goals]
        links = [f'<a href="/{g["slug"]}/">{g["name"].lower()}</a>' for g in gs]
        joined = links[0] if len(links) == 1 else ", ".join(links[:-1]) + " and " + links[-1]
        out.append(f'Our {joined} page{"s list" if len(links) > 1 else " lists"} it.')
    low = pep_low_shop(slug)
    if low:
        n = len({r["seller_slug"] for r in pep_shops(slug)})
        seen = low.get("price_observed_at") or low.get("last_seen")
        out.append(f'The lowest price at the {plural(n, "shop")} shown below is {per_mg(low["price_per_mg"])}/mg '
                   f'({clinic_link(low["seller_slug"], clean(SELLERS.get(low["seller_slug"], {}).get("seller_name") or low["seller_name"]), True)})'
                   f'{", checked " + nice_date(seen) if seen else ""}.')
    n = len(LETTER_SUBS.get(slug, []))
    if n:  # the count of letters that name it (owner task 2 Nov 2026), linking the section below
        out.append(f'<a href="#letters">{plural(n, "FDA warning letter")}</a> name{"s" if n == 1 else ""} it.')
    p = pep_low_plan(slug) if pep_group(s) == "approved" else None
    if p:
        out.append(f'The lowest monthly plan that is not compounded, at the online clinics we track, is {usd(p["price_monthly"])} '
                   f'({clinic_link(p["seller_slug"], seller_base(p["seller_name"]), True)}, {clean(p["plan_name"])}), checked {nice_date(p["last_seen"])}.')
    return out


def pep_checked(slug):
    s = pep_status(slug)
    dates = [s["seen"]] + [r.get("price_observed_at") or r.get("last_seen") or "" for r in pep_shops(slug)]
    dates += [r["last_seen"] for r in pep_plans(slug)] if pep_group(s) == "approved" else []
    return max(d for d in dates if d)


def pep_title(slug):
    n = pep_short(slug)
    for t in (f"{n}: FDA status, prices and where it is sold | Peptide Chooser", f"{n}: FDA status, prices and where it is sold",
              f"{n}: FDA status and prices | Peptide Chooser", f"{n}: FDA status and prices"):
        if len(t) <= 60:
            return t
    return n


def pep_description(slug):
    """110 to 160 characters from the same facts: status, the price, the goal pages, the check date."""
    s, n = pep_status(slug), pep_short(slug)
    parts = [f'{n}: {s["label"]}, {s["sentence"]}.']
    low = pep_low_shop(slug)
    plan = pep_low_plan(slug) if pep_group(s) == "approved" else None
    if low:
        parts.append(f'Lowest shop price {per_mg(low["price_per_mg"])}/mg.')
    elif plan:
        parts.append(f'Online clinic plans from {usd(plan["price_monthly"])} a month.')
    goals = list(dict.fromkeys(g["name"].lower() for g, _ in pep_goals(slug)))
    if goals:
        parts.append(f'On our {" and ".join(goals[:2])} page{"s" if len(goals[:2]) > 1 else ""}.')
    brands = sorted({brand_base(a["brand_name"]) for a in APPROVED_DB if a["substance_slug"] == slug and a.get("brand_name")}
                    - {n.split()[0].title()})
    if brands and pep_group(s) == "approved":
        parts.append(f'Approved brand{"s" if len(brands) > 1 else ""}: {", ".join(brands[:3])}.')
    parts.append(f"Checked {nice_date(pep_checked(slug))}.")
    parts.append("We compare and never sell.")
    out = parts[0]
    for x in parts[1:]:
        if len(out) + 1 + len(x) <= 160:
            out += " " + x
    return out


def pep_chips(slug, s):
    rx = pep_rx(slug, s)[1]
    rx = f'<span class="chip chip-neutral">{rx}</span>' if rx else ""
    return (f'<p class="pep-chips"><span class="chip chip-{s["chip"]}">{s["label"]}</span>{rx}'
            f'<span class="stamp">Checked {nice_date(pep_checked(slug))}</span></p>')


def pep_facts(slug, s):
    """The facts ledger in the Background check card's frame: FDA status and every open list entry in the database's
    words, the approved brands, forms, prescription needed, first seen by us."""
    rows = [("FDA status", f'<span class="chip chip-{s["chip"]}">{s["label"]}</span>')]
    for r in sorted(pep_db_rows(slug), key=lambda r: r["regime"]):
        if r["regime"] not in REGIME_WORDS:
            continue
        v = VALUE_WORDS.get(r["status_value"], r["status_value"].replace("_", " "))
        scope = f' ({r["scope"]})' if r.get("scope") and r["regime"] != "fda_approval" else ""
        since = f', since {nice_date(r["valid_from"])}' if r.get("valid_from") else ""
        rows.append((REGIME_WORDS[r["regime"]], f'{v}{scope}{since}'))
    brands = sorted({brand_base(a["brand_name"]) for a in APPROVED_DB if a["substance_slug"] == slug and a.get("brand_name")}
                    - {pep_short(slug).split()[0].title()})
    if brands and pep_group(s) == "approved":
        rows.append(("Approved brands", ", ".join(brands)))
    forms = pep_forms(slug)
    if forms:
        rows.append(("Forms sold", ", ".join(forms)))
    rows.append(("Prescription needed", pep_rx(slug, s)[0]))
    first = min((r["first_seen_by_us"] for r in pep_db_rows(slug) if r.get("first_seen_by_us")), default=None)
    if first:
        rows.append(("First seen by us", nice_date(first)))
    li = "".join(f'<li><span>{k}</span><span>{v}</span></li>' for k, v in rows)
    return f"""
      <aside class="board check-card facts-card" aria-labelledby="facts-h">
        <div class="check-head"><h2 id="facts-h">Facts</h2></div>
        <ul class="facts-list">{li}</ul>
        <p class="check-nolink">Facts from the FDA lists and our data. Not medical advice.</p>
      </aside>"""


class PepSources:
    """The page's numbered sources: the status source first, then each outside source the evidence rows use."""
    def __init__(self):
        self.items = []

    def n(self, text, url):
        key = (text, url)
        if key not in self.items:
            self.items.append(key)
        return self.items.index(key) + 1

    def ref(self, text, url):
        k = self.n(text, url)
        return f'<a class="ref" href="#src-{k}" aria-label="Source {k}"><sup>{k}</sup></a>'

    def html(self):
        return "".join(f'<li id="src-{i}">{escape(t)}: <a href="{escape(u)}" rel="nofollow">{escape(u)}</a></li>'
                       for i, (t, u) in enumerate(self.items, start=1))


def pep_evidence(slug, src):
    """One row per goal page option that carries the substance: the goal, the option, its evidence chip (from the goal's
    checked options table when it has one) and the line that page shows for it, with that page's sources."""
    trs = []
    for g, p in pep_goals(slug):
        o = next((o for o in g.get("options") or [] if o["name"] == p["name"] or o.get("substance") == slug and subs_of(p) == [slug]
                  or subs_of(p) == [slug] and sub_label(slug).lower().split()[0] in o["name"].lower()), None)
        chip = f'<span class="chip chip-{o["evidence_chip"]}">{o["evidence"]}</span>' if o else '<span class="small">Not rated</span>'
        refs_ = [(x["text"], x["url"]) for x in g.get("sources", []) if o and x["n"] in o["sources"]]
        refs_ += [(x["text"], x["url"]) for x in LEGAL["sources"] if x["n"] in (p.get("src") or [])]
        sup = "".join(src.ref(t, u) for t, u in refs_)
        trs.append(f'<tr><td><a class="name" href="/{g["slug"]}/">{g["name"]}</a><span class="note">{p["name"]}</span></td>'
                   f'<td data-l="Evidence in people">{chip}</td><td data-l="What the goal page says">{p["does"]}{sup}</td></tr>')
    if not trs:
        return ""
    return f"""
<section class="band-2" id="evidence">
  <div class="wrap">
    <div class="sec-hd"><div><h2>Evidence by goal</h2><p>What each goal page that lists it says, word for word, with its sources. The evidence rating comes from a goal page's checked options table; a goal without one shows "Not rated".</p></div></div>
    <div class="tbl-wrap"><table class="tbl tbl-cards tbl-evidence">
      <thead><tr><th scope="col">Goal</th><th scope="col">Evidence in people</th><th scope="col">What the goal page says</th></tr></thead>
      <tbody>{"".join(trs)}</tbody>
    </table></div>
  </div>
</section>"""


def pep_shops_section(slug):
    rows = pep_shops(slug)
    if not rows:
        return ""
    trs, newest = [], ""
    for r in rows:
        seller = clean(SELLERS.get(r["seller_slug"], {}).get("seller_name") or r["seller_name"])
        name = clinic_link(r["seller_slug"], seller)
        size = f'{r["amount_mg"]:g} mg' if r.get("amount_mg") else "unknown"
        price = money(r["price_usd"]) if r.get("price_usd") is not None else "unknown"
        ppm = (f'{money(r["price_per_mg"])}/mg' if r.get("price_per_mg") is not None else "blend" if r.get("is_blend") else "unknown")
        seen = r.get("price_observed_at") or r.get("last_seen") or ""
        newest = max(newest, seen)
        trs.append(f'<tr><td>{name}</td><td class="num" data-l="Size">{size}</td><td class="num" data-l="Price">{price}</td>'
                   f'<td class="num" data-l="Per mg">{ppm}</td><td data-l="Checks">{score_line(r) or "not checked yet"}</td></tr>')
    return f"""
<section class="section" id="sold">
  <div class="wrap">
    <div class="sec-hd"><div><h2>Where it is sold</h2><p>The {plural(len(rows), "shop")} in the price window on our goal pages, each with its cheapest listing by price per mg, most checks first. Research-use sellers; we do not link to them.{" Prices checked " + nice_date(newest) + "." if newest else ""}</p></div></div>
    <div class="tbl-wrap"><table class="tbl tbl-cards tbl-sold">
      <thead><tr><th scope="col">Shop</th><th scope="col">Size</th><th scope="col">Price</th><th scope="col">Per mg</th><th scope="col">Checks</th></tr></thead>
      <tbody>{"".join(trs)}</tbody>
    </table></div>
    <p class="small" style="margin-top:16px">Price per mg is the price divided by the stated amount. Checks are facts we hold about the seller, not a safety or quality grade. <a href="/how-we-rate/">How we rate</a></p>
  </div>
</section>"""


def pep_plans_section(slug):
    """An approved medicine: the clinic table of the goal page whose plans carry it (Category, weight loss), filtered to
    the substance; else the clinic plans of the substance in the same table."""
    rows = pep_plans(slug)
    if not rows:
        return ""
    g = next((g for g in ALL_GOALS if slug in ((g.get("clinic_plans") or {}).get("substances") or [])), None) or SUB_GOAL.get(slug) or {}
    return clinic_section(g, rows).replace('id="clinics"', 'id="sold"', 1)


PEP_LETTERS_SHOWN = 10


def quote_text(q):
    """A letter's first mention as the site shows it: clean spacing, and the FDA's own short bracket marks without their
    brackets ("eye[,]" -> "eye,", "[GLP-1]" -> "GLP-1"), which the placeholder check would read as a template gap."""
    return re.sub(r"\[([^\[\]]{1,40})\]", r"\1", clean(q))


def pep_letters_section(slug):
    """FDA warning letters that name the substance (site.letter_substances; pages.md, Peptide): the count, then up to ten
    newest as the letters page's table (date, company, the first mention in small, the letter on fda.gov), and the link
    to the letters page filtered to the substance. Without the data: the link to the letters page alone."""
    if not LETTERS_ALL:
        return ""
    name = pep_short(slug)
    if not LETTER_SUBS_ON:
        return f"""
<section class="section" id="letters">
  <div class="wrap">
    <div class="sec-hd"><div><h2>FDA warning letters</h2><p>Our letters list is by company, not by substance. The letters page lists all {len(LETTERS_ALL)}, each with its subject and a link to fda.gov; filter it by a company name.</p></div><a href="/fda-warning-letters/">FDA warning letters</a></div>
  </div>
</section>"""
    rows = LETTER_SUBS.get(slug, [])
    if not rows:
        return f"""
<section class="section" id="letters">
  <div class="wrap">
    <div class="sec-hd"><div><h2>FDA warning letters</h2><p>No FDA warning letter we track names {escape(name)}.</p></div><a href="/fda-warning-letters/">FDA warning letters</a></div>
  </div>
</section>"""
    trs = "".join(
        f'<tr><td class="num">{nice_date(r["letter_date"])}</td><td><span class="name">{escape(clean(LETTER_CO.get(r["letter_url"], "")))}</span>'
        + (f'<span class="sub-quote">"{escape(quote_text(r["first_mention"]))}"</span>' if r.get("first_mention") else "")
        + f'</td><td><a href="{escape(r["letter_url"])}" rel="nofollow">FDA letter</a></td></tr>' for r in rows[:PEP_LETTERS_SHOWN])
    shown = (f" The {PEP_LETTERS_SHOWN} newest are below." if len(rows) > PEP_LETTERS_SHOWN else "")
    return f"""
<section class="section" id="letters">
  <div class="wrap">
    <div class="sec-hd"><div><h2>FDA warning letters</h2><p>{plural(len(rows), "FDA warning letter")} name{"s" if len(rows) == 1 else ""} {escape(name)}.{shown} Each quote is where the letter first names it.</p></div></div>
    <div class="tbl-wrap"><table class="tbl tbl-letters tbl-pep-letters">
      <thead><tr><th scope="col">Date</th><th scope="col">Company</th><th scope="col">Source</th></tr></thead>
      <tbody>{trs}</tbody>
    </table></div>
    <p class="small" style="margin-top:16px"><a href="/fda-warning-letters/?sub={slug}">See all on the letters page</a></p>
  </div>
</section>"""


def pep_guides(slug):
    words = {pep_short(slug).lower(), slug.replace("-", " ")}
    found = [g for g in guides.GUIDES if any(w in g["title"].lower() for w in words)]
    if not found:
        return ""
    items = "".join(f'<li><a href="/learn/{g["slug"]}/">{g["title"]}</a></li>' for g in found)
    return (f'<section class="related" aria-labelledby="guides-h"><h2 id="guides-h" class="h-sources">Guides</h2>'
            f'<ul>{items}</ul></section>')


def pep_page(slug):
    s = pep_status(slug)
    src = PepSources()
    src.n(f'{"FDA" if "fda.gov" in s["url"] else "Source"}, status of {pep_short(slug)}, {nice_date(s["seen"])}', s["url"])
    evidence = pep_evidence(slug, src)
    sold = pep_plans_section(slug) if pep_group(s) == "approved" else pep_shops_section(slug)
    return f"""
<section class="hero hero-goal seller-pg pep-pg">
  <div class="wrap">
    <div class="hero-grid">
      <div>
        <h1>{escape(pep_name(slug))}</h1>
        {pep_chips(slug, s)}
        <p class="small meta"><a href="/about/">{AUTHOR}</a>. {STANDING_LINE.replace(CHECKED, nice_date(pep_checked(slug)))}</p>
        <p class="intro">{" ".join(pep_answer(slug))}</p>{f'<p class="small pep-listing">FDA listing: "{escape(s["listing"])}"</p>' if s.get("listing") else ""}
      </div>{pep_facts(slug, s)}
    </div>
  </div>
</section>{evidence}{sold}{pep_letters_section(slug)}
<section class="section pep-foot">
  <div class="wrap">
    {pep_guides(slug)}
    <section class="pep-sources" aria-labelledby="sources-h"><h2 id="sources-h" class="h-sources">Sources</h2>
    <ol class="small sources">{src.html()}</ol></section>
  </div>
</section>
"""


PEP_GROUPS = [("approved", "FDA approved", "Approved medicines: an FDA-approved product exists for a stated use."),
              ("not", "Not approved", "No approved product; research-use shops sell most of them, and some may be made by pharmacies."),
              ("cosmetic", "Cosmetic", "Sold in creams and serums; cosmetics do not need FDA approval.")]


def pep_low(slug):
    s = pep_status(slug)
    low = pep_low_shop(slug)
    if low:
        return f'{per_mg(low["price_per_mg"])}/mg'
    plan = pep_low_plan(slug) if pep_group(s) == "approved" else None
    return f'{usd(plan["price_monthly"])}/mo' if plan else "none shown"


def peptides_index():
    sections = []
    for key, label, line in PEP_GROUPS:
        slugs = sorted((x for x in PEPTIDE_SLUGS if pep_group(pep_status(x)) == key), key=lambda x: pep_name(x).lower())
        if not slugs:
            continue
        trs = "".join(
            f'<tr><td><a class="name" href="/peptides/{x}/">{escape(pep_name(x))}</a></td>'
            f'<td data-l="Status"><span class="chip chip-{pep_status(x)["chip"]}">{pep_status(x)["label"]}</span></td>'
            f'<td data-l="What that means">{pep_status(x)["sentence"]}</td><td class="num" data-l="Lowest price">{pep_low(x)}</td></tr>'
            for x in slugs)
        sections.append(f"""
    <div class="sec-hd pep-group"><div><h2 id="g-{key}">{label}</h2><p>{plural(len(slugs), "substance")}. {line}</p></div></div>
    <div class="tbl-wrap"><table class="tbl tbl-cards tbl-peptides" aria-labelledby="g-{key}">
      <thead><tr><th scope="col">Substance</th><th scope="col">Status</th><th scope="col">What that means</th><th scope="col">Lowest price</th></tr></thead>
      <tbody>{trs}</tbody>
    </table></div>""")
    checked = max(pep_checked(x) for x in PEPTIDE_SLUGS)
    return f"""
<section class="section letters-hd">
  <div class="wrap">
    <h1>Peptides and their FDA status</h1>
    <p class="lede">Every peptide and approved alternative we track, {len(PEPTIDE_SLUGS)} in all, with its FDA status, its source and the lowest price we show. Each name opens its page; we do not link to shops or clinics.</p>
    <p class="letters-stamp"><span class="stamp">Checked {nice_date(checked)}</span><span class="small">Lowest price: per mg at the shops we show, or per month at the online clinics for an approved medicine.</span></p>
  </div>
</section>
<section class="band-2" id="peptides-list">
  <div class="wrap">{"".join(sections)}
  </div>
</section>
"""


if PEPTIDE_SLUGS:
    PAGES.append(("/peptides/", "peptides/index.html", "Peptides A to Z: FDA status and prices | Peptide Chooser",
                  (f"Every peptide and approved alternative we track, {len(PEPTIDE_SLUGS)} in all, grouped FDA approved, not "
                   "approved and cosmetic, with its source and the lowest price we show."),
                  peptides_index(), item_list_schema("Peptides and their FDA status",
                                                     [(pep_name(x), f"{SITE}/peptides/{x}/") for x in PEPTIDE_SLUGS]),
                  [("/peptides/", "Peptides")]))
    for _x in PEPTIDE_SLUGS:
        PAGES.append((f"/peptides/{_x}/", f"peptides/{_x}/index.html", pep_title(_x), pep_description(_x), pep_page(_x), "",
                      [("/peptides/", "Peptides"), (f"/peptides/{_x}/", pep_short(_x))]))


# Comparison pages (pages.md, Compare `/compare/<a>-vs-<b>/`; owner task 2 Nov 2026): static, indexable pairs from the
# data /compare/ uses, built after every other page so the "Compared with" lines and "Popular comparisons" can be added
# to /compare/, the /peptides/ pages and the clinic pages here. Substance pairs: every two substances with a page that
# share a goal page. Clinic pairs: every two clinics with a compounded plan of the same substance. One page per pair
# (a-vs-b in alphabetical order, never b-vs-a); no shop pairs; no link to a shop or a clinic.
CMP_CLINIC_SUBS = ("semaglutide", "tirzepatide")
CMP_MAX = 40
CMP_POPULAR = 12


def cmp_slugify(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def cmp_sub_pairs():
    """{(a, b): [goals they share]} for every two substances with a page on one goal page and the same kind of status
    (both FDA approved, both not approved, or both cosmetic; owner answer Q1 b, 2 Nov 2026), a < b."""
    out = {}
    for g in ALL_GOALS:
        if not g.get("page"):
            continue
        subs = sorted({s for p in g["peptides"] for s in subs_of(p) if s in PEPTIDE_SLUGS})
        for i, a in enumerate(subs):
            for b in subs[i + 1:]:
                if pep_group(pep_status(a)) == pep_group(pep_status(b)):
                    out.setdefault((a, b), []).append(g)
    return out


def cmp_clinic_plan(clinic, sub):
    """The clinic's cheapest compounded plan of the substance, or None."""
    rows = [r for r in PLANS if r["seller_slug"] == clinic and r["substance_slug"] == sub
            and r.get("product_kind") == "compounded" and r.get("price_monthly") is not None]
    return min(rows, key=lambda r: (float(r["price_monthly"]), r["plan_name"]), default=None)


def cmp_clinic_name(slug):
    return seller_base(PROFILES[slug]["seller_name"])


def cmp_clinic_pairs():
    """{(a, b): [substances]} for every two clinic pages that both have a compounded plan of a substance in
    CMP_CLINIC_SUBS, keyed by the clinics' URL names in alphabetical order. Over CMP_MAX pairs, only pairs where both
    clinics meet 2 or more of the 5 checks are kept (owner task 2 Nov 2026), then the first CMP_MAX."""
    out = {}
    for sub in CMP_CLINIC_SUBS:
        clinics = sorted({r["seller_slug"] for r in PLANS if r["seller_slug"] in CLINIC_PROFILES and cmp_clinic_plan(r["seller_slug"], sub)},
                         key=lambda x: cmp_slugify(cmp_clinic_name(x)))
        for i, a in enumerate(clinics):
            for b in clinics[i + 1:]:
                out.setdefault((a, b), []).append(sub)
    if len(out) > CMP_MAX:
        out = {k: v for k, v in out.items() if all((PROFILES[x].get("score") or 0) >= 2 for x in k)}
    return dict(list(out.items())[:CMP_MAX])


def cmp_path(a, b, clinic=False):
    name = (lambda x: cmp_slugify(cmp_clinic_name(x))) if clinic else (lambda x: x)
    return f"/compare/{name(a)}-vs-{name(b)}/"


def cmp_table(caption, heads, rows):
    """The /compare/ two-column table, static: the row name, then one cell per side."""
    trs = "".join(f'<tr><th scope="row">{k}</th><td>{x}</td><td>{y}</td></tr>' for k, x, y in rows)
    return (f'<table class="cmp"><caption class="vh">{escape(caption)}</caption><thead><tr><td></td>'
            f'<th scope="col">{heads[0]}</th><th scope="col">{heads[1]}</th></tr></thead><tbody>{trs}</tbody></table>')


STATUS_WORDS = {"approved": "FDA approved", "cosmetic": "sold as a cosmetic"}


def cmp_status_words(slug):
    s = pep_status(slug)
    return STATUS_WORDS.get(pep_group(s), s["label"].lower())


def cmp_sub_cell(slug, goals):
    """One substance's cells, in the row order of cmp_sub_rows."""
    s = pep_status(slug)
    host = "FDA source" if "fda.gov" in s["url"] else "Source"
    approved = pep_group(s) == "approved"
    low, n = pep_low_shop(slug), len({r["seller_slug"] for r in pep_shops(slug)})
    plan = pep_low_plan(slug) if approved else None
    opt = next((p for g in goals for p in g["peptides"] if subs_of(p) == [slug]), None) or \
        next((p for g in goals for p in g["peptides"] if slug in subs_of(p)), None)
    guides_ = [g for g in guides.GUIDES if any(w in g["title"].lower() for w in (pep_short(slug).lower(), slug.replace("-", " ")))]
    return [
        f'<span class="chip chip-{s["chip"]}">{s["label"]}</span><span class="cmp-sub">{s["sentence"]}. '
        f'<a href="{escape(s["url"])}" rel="nofollow">{host}</a>, {nice_date(s["seen"])}</span>',
        ", ".join(f'<a href="/{g["slug"]}/">{g["name"]}</a>' for g in ALL_GOALS if g.get("page") and any(slug in subs_of(p) for p in g["peptides"])),
        ("Not shown: we list clinics, not shops, for an approved medicine" if approved else
         f'<span class="num">{per_mg(low["price_per_mg"])}/mg</span><span class="cmp-sub">lowest of {plural(n, "shop")}</span>' if low else "None shown"),
        (f'<span class="num">{usd(plan["price_monthly"])}/mo</span><span class="cmp-sub">{clinic_link(plan["seller_slug"], seller_base(plan["seller_name"]), True)}, {escape(clean(plan["plan_name"]))}</span>'
         if plan else "No plan we track" if approved else "Not applicable"),
        ", ".join(pep_forms(slug)) or "Unknown",
        opt["does"] if opt else "Not on this goal page",
        ((f'<a href="/fda-warning-letters/?sub={slug}">{plural(len(LETTER_SUBS.get(slug, [])), "letter")}</a><span class="cmp-sub">name{"s" if len(LETTER_SUBS.get(slug, [])) == 1 else ""} it</span>'
          if LETTER_SUBS.get(slug) else "None we track names it") if LETTER_SUBS_ON else
         f'<a href="/fda-warning-letters/">FDA warning letters</a><span class="cmp-sub">listed by company, not by substance</span>') if LETTERS_ALL else "Not listed by substance",
        ", ".join(f'<a href="/learn/{g["slug"]}/">{g["title"]}</a>' for g in guides_) or "No guide names it",
    ]


CMP_SUB_ROWS = ["FDA status", "Goal pages", "Lowest price at shops", "Clinic plans from", "Forms sold", "What the goal page says",
                "FDA letters", "Guides"]


def cmp_sub_answer(a, b):
    """Two or three sentences from data: the statuses, then the prices that can be set side by side."""
    na, nb = pep_short(a), pep_short(b)
    wa, wb = cmp_status_words(a), cmp_status_words(b)
    out = [f"Both are {wa}." if wa == wb else f"{na} is {wa}; {nb} is {wb}."]
    la, lb = pep_low_shop(a), pep_low_shop(b)
    pa = pep_low_plan(a) if pep_group(pep_status(a)) == "approved" else None
    pb = pep_low_plan(b) if pep_group(pep_status(b)) == "approved" else None
    if la and lb:
        lo, hi = sorted(((na, la), (nb, lb)), key=lambda x: x[1]["price_per_mg"])
        out.append(f"At the shops we show, {lo[0]} is cheaper per mg: {per_mg(lo[1]['price_per_mg'])}/mg against {per_mg(hi[1]['price_per_mg'])}/mg.")
    elif pa and pb:
        lo, hi = sorted(((na, pa), (nb, pb)), key=lambda x: float(x[1]["price_monthly"]))
        out.append(f"At the online clinics we track, {lo[0]} plans start lower: {usd(lo[1]['price_monthly'])} a month against {usd(hi[1]['price_monthly'])}.")
    else:
        for n, l, p in ((na, la, pa), (nb, lb, pb)):
            if l:
                out.append(f"{n} is from {per_mg(l['price_per_mg'])}/mg at the shops we show.")
            elif p:
                out.append(f"{n} plans start at {usd(p['price_monthly'])} a month at the online clinics we track.")
    return out[:3]


def cmp_title(base, *tails):
    for t in [t for x in tails for t in (f"{base}: {x} | Peptide Chooser", f"{base}: {x}")] + [base]:
        if len(t) <= 60:
            return t
    return base


def cmp_fit(parts):
    """A description from parts, 110 to 160 characters: parts are added while they fit."""
    out = parts[0]
    for x in parts[1:]:
        if len(out) + 1 + len(x) <= 160:
            out += " " + x
    return out


def cmp_sub_page(a, b, goals):
    na, nb = pep_short(a), pep_short(b)
    checked = max(pep_checked(a), pep_checked(b))
    heads = [f'<a class="name" href="/peptides/{x}/">{escape(pep_short(x))}</a><span class="cmp-sub">{pep_status(x)["label"]}</span>' for x in (a, b)]
    ca, cb = cmp_sub_cell(a, goals), cmp_sub_cell(b, goals)
    table = cmp_table(f"{na} and {nb}", heads, list(zip(CMP_SUB_ROWS, ca, cb)))
    plans = [pep_low_plan(x) if pep_group(pep_status(x)) == "approved" else None for x in (a, b)]
    pre = f'?a=p.{plans[0]["seller_slug"]}.{plans[0]["plan_slug"]}&amp;b=p.{plans[1]["seller_slug"]}.{plans[1]["plan_slug"]}' if all(plans) else ""
    body = cmp_body(f"{na} vs {nb}", checked, cmp_sub_answer(a, b), table,
                    [(f"/peptides/{a}/", na), (f"/peptides/{b}/", nb)], pre,
                    "Statuses come from the FDA lists; prices are the lowest we show, per mg at the shops or per month at the online clinics.")
    desc = cmp_fit([f"{na} vs {nb}: {cmp_sub_answer(a, b)[0][:-1]}.", *cmp_sub_answer(a, b)[1:2],
                    f'Both on our {goals[0]["name"].lower()} page.', f"Checked {nice_date(checked)}.", "We compare and never sell."])
    return cmp_title(f"{na} vs {nb}", "FDA status and prices"), desc, body


def cmp_body(h1, checked, answer, table, links, pre, note):
    more = " and ".join(f'<a href="{u}">{escape(t)}</a>' for u, t in links)
    return f"""
<section class="section letters-hd">
  <div class="wrap">
    <h1>{escape(h1)}</h1>
    <p class="lede">{" ".join(answer)}</p>
    <p class="letters-stamp"><span class="stamp">Checked {nice_date(checked)}</span><span class="small"><a href="/about/">{AUTHOR}</a>. {note}</span></p>
  </div>
</section>
<section class="band-2" id="compare-two">
  <div class="wrap">
    {table}
    <p class="small" style="margin-top:16px">Our pages on each: {more}. We do not link to the shops or the clinics.</p>
    {f'<p class="cmp-link"><a class="btn btn-line" href="/compare/{pre}">Compare any two</a></p>' if pre else ""}
  </div>
</section>
"""


def cmp_clinic_cells(c, subs):
    p = PROFILES[c]
    plans = [cmp_clinic_plan(c, s) for s in subs]
    marks = "".join(f'<span class="chip chip-{"ok" if p.get(k) else "neutral"} mark-{"yes" if p.get(k) else "no"}">{t}'
                    f'<span class="vh">: {"yes" if p.get(k) else "no"}</span></span>' for k, t in SCORE_CHECKS)
    fee = plans[0].get("membership_fee_monthly")
    n, last = p.get("fda_letter_count") or 0, p.get("last_fda_letter_date")
    state = STATES.get(p.get("entity_state") or "", p.get("entity_state") or "")
    company = ("No registered company found" if not shown_company(p) else
               f'{escape(clean(p["entity_name"]))}{", " + state if state else ""}'
               f'<span class="cmp-sub">{"State registry" if p["entity_evidence"] == "registry" else "Named in an FDA letter"}</span>')
    return [f'<span class="num">{usd(r["price_monthly"])}/mo</span><span class="cmp-sub">{escape(clean(r["plan_name"]))}</span>' for r in plans] + [
        "Not known" if fee is None else "None, all-in" if float(fee) == 0 else f"{usd(fee)}/mo",
        f'<a class="chip chip-warn chip-link" href="{LETTERS_URL}">FDA letter {nice_date(last)}</a>' if n and last else "None",
        f'<span class="score"><span class="score-n"><span class="num">{p["score"]}</span> of {len(SCORE_CHECKS)} checks</span>'
        f'<span class="score-marks">{marks}</span></span>',
        company,
        nice_date(max(r["last_seen"] for r in plans)),
    ]


def cmp_clinic_answer(a, b, subs):
    na, nb = cmp_clinic_name(a), cmp_clinic_name(b)
    out = []
    for s in subs:
        pa, pb = cmp_clinic_plan(a, s), cmp_clinic_plan(b, s)
        if float(pa["price_monthly"]) == float(pb["price_monthly"]):
            out.append(f"For compounded {s}, both list {usd(pa['price_monthly'])} a month.")
            continue
        lo, hi = sorted(((na, pa), (nb, pb)), key=lambda x: float(x[1]["price_monthly"]))
        out.append(f"For compounded {s}, {lo[0]} is cheaper: {usd(lo[1]['price_monthly'])} a month ({care_note(lo[1])}) "
                   f"against {usd(hi[1]['price_monthly'])} ({care_note(hi[1])}).")
    la, lb = [(PROFILES[x].get("fda_letter_count") or 0, PROFILES[x].get("last_fda_letter_date")) for x in (a, b)]
    if la[0] and lb[0]:
        out.append("Both have an FDA warning letter.")
    elif la[0] or lb[0]:
        (n, (_, d)), other = ((na, la), nb) if la[0] else ((nb, lb), na)
        out.append(f"{n} has an FDA warning letter{' from ' + nice_date(d) if d else ''}; {other} has none.")
    else:
        out.append("Neither has an FDA warning letter.")
    return out[:3]


def cmp_clinic_page(a, b, subs):
    na, nb = cmp_clinic_name(a), cmp_clinic_name(b)
    plans = [cmp_clinic_plan(x, subs[0]) for x in (a, b)]
    checked = max(r["last_seen"] for x in (a, b) for r in (cmp_clinic_plan(x, s) for s in subs))
    heads = [f'<a class="name" href="/sellers/{x}/">{escape(cmp_clinic_name(x))}</a><span class="cmp-sub">Online clinic</span>' for x in (a, b)]
    rows = [f"Compounded {s}" for s in subs] + ["Care fee", "FDA letter", "Checks", "Company", "Prices checked"]
    table = cmp_table(f"{na} and {nb}", heads, list(zip(rows, cmp_clinic_cells(a, subs), cmp_clinic_cells(b, subs))))
    pre = f'?a=p.{plans[0]["seller_slug"]}.{plans[0]["plan_slug"]}&amp;b=p.{plans[1]["seller_slug"]}.{plans[1]["plan_slug"]}'
    answer = cmp_clinic_answer(a, b, subs)
    body = cmp_body(f"{na} vs {nb}", checked, answer, table, [(f"/sellers/{a}/", na), (f"/sellers/{b}/", nb)], pre,
                    "Prices are the clinics' published monthly prices. Checks are facts we hold about the clinic, not a safety or quality grade.")
    what = " and ".join(f"compounded {s}" for s in subs)
    desc = cmp_fit([f"{na} vs {nb} for {what}: monthly price, care fee, FDA warning letters and five background checks.",
                    answer[-1], f"Checked {nice_date(checked)}."])
    if len(desc) < 110:
        desc = cmp_fit([desc, "We compare and never sell."])
    return cmp_title(f"{na} vs {nb}", "prices, care fees and checks", "prices and checks"), desc, body


CMP_PAGES = []  # (path, title, kind, weight, a, b): one per pair, for the links in
HAS_COMPARE = any(p[0] == "/compare/" for p in PAGES)  # the pairs hang under /compare/ (breadcrumb, "Compare any two")
if PEPTIDE_SLUGS and HAS_COMPARE:
    for (_a, _b), _goals in cmp_sub_pairs().items():
        _t, _d, _body = cmp_sub_page(_a, _b, _goals)
        _w = sum(len({r["seller_slug"] for r in pep_shops(x)}) + len(pep_plans(x)) for x in (_a, _b))
        CMP_PAGES.append((cmp_path(_a, _b), f"{pep_short(_a)} vs {pep_short(_b)}", "sub", _w, _a, _b))
        PAGES.append((cmp_path(_a, _b), cmp_path(_a, _b).strip("/") + "/index.html", _t, _d, _body, "",
                      [("/compare/", "Compare any two"), (cmp_path(_a, _b), f"{pep_short(_a)} vs {pep_short(_b)}")]))
if CLINIC_PROFILES and HAS_COMPARE:
    for (_a, _b), _subs in cmp_clinic_pairs().items():
        _t, _d, _body = cmp_clinic_page(_a, _b, _subs)
        _w = len(clinic_plan_rows(PROFILES[_a])) + len(clinic_plan_rows(PROFILES[_b]))
        _p = cmp_path(_a, _b, clinic=True)
        CMP_PAGES.append((_p, f"{cmp_clinic_name(_a)} vs {cmp_clinic_name(_b)}", "clinic", _w, _a, _b))
        PAGES.append((_p, _p.strip("/") + "/index.html", _t, _d, _body, "",
                      [("/compare/", "Compare any two"), (_p, f"{cmp_clinic_name(_a)} vs {cmp_clinic_name(_b)}")]))


def cmp_compared_with(key):
    """"Compared with: A, B." for a /peptides/ page or a clinic page, or "" when it is in no pair."""
    links = [f'<a href="{p}">{escape(t)}</a>' for p, t, _, _, a, b in CMP_PAGES if key in (a, b)]
    return f'<p class="compared"><strong>Compared with:</strong> {", ".join(links)}</p>' if links else ""


def cmp_links_in():
    """Popular comparisons on /compare/ (the pairs with the most shops or plans) and the "Compared with" lines."""
    top = sorted(CMP_PAGES, key=lambda x: (-x[3], x[1].lower()))[:CMP_POPULAR]
    popular = (f'<section class="section" id="popular"><div class="wrap"><section class="related" aria-labelledby="popular-h">'
               f'<h2 id="popular-h" class="h-sources">Popular comparisons</h2><ul>'
               + "".join(f'<li><a href="{p}">{escape(t)}</a></li>' for p, t, *_ in top) + "</ul></section></div></section>\n") if top else ""
    for i, (path, out, title, desc, body, schema, crumb) in enumerate(PAGES):
        if path == "/compare/" and popular:
            body = body.replace(COMPARE_JS, popular + COMPARE_JS, 1)
        elif path.startswith("/peptides/") and path.count("/") == 3:
            line = cmp_compared_with(path.split("/")[2])
            body = body.replace('<section class="section pep-foot">\n  <div class="wrap">', '<section class="section pep-foot">\n  <div class="wrap">\n    ' + line, 1)
        elif path.startswith("/sellers/") and path.split("/")[2] in CLINIC_PROFILES:
            line = cmp_compared_with(path.split("/")[2])
            body += f'<section class="section"><div class="wrap">{line}</div></section>\n' if line else ""
        PAGES[i] = (path, out, title, desc, body, schema, crumb)


cmp_links_in()


# Home, footer and llms.txt catch up with the site (pages.md, Home, Every page, 404; owner task 2 Nov 2026). Built after
# every other page so they list only what this build has.
def built(path):
    return any(p[0] == path for p in PAGES)


def foot_browse():
    """The footer's Browse column: each section this build has, then Home's legal table."""
    items = [("/peptides/", "Peptides A to Z"), ("/sellers/", "Sellers"), ("/compare/", "Compare"), ("/learn/", "Guides"),
             ("/fda-warning-letters/", "FDA warning letters")]
    links = "".join(f'<li><a href="{u}">{t}</a></li>' for u, t in items if built(u))
    return (f'<nav class="foot-browse" aria-labelledby="foot-browse-h"><h2 class="foot-h" id="foot-browse-h">Browse</h2>'
            f'<ul class="foot-links">{links}<li><a href="/#legal">Legal status</a></li></ul></nav>')


HOME_PAIRS = 6


def home_compare_card():
    """Home's Compare card beside "Sellers we track": the six pairs with the most shops or plans, and "Compare any two"."""
    if not built("/compare/"):
        return ""
    top = sorted(CMP_PAGES, key=lambda x: (-x[3], x[1].lower()))[:HOME_PAIRS]
    items = "".join(f'<li><a href="{p}">{escape(t)}</a></li>' for p, t, *_ in top)
    pairs = f'<div class="related home-pairs"><ul>{items}</ul></div>' if top else ""
    return f"""
    <div class="home-card">
    <div class="sec-hd"><div><h2>Popular comparisons</h2><p>Two plans, two sellers or two substances side by side, from our data.</p></div></div>
    {pairs}
    <p class="letters-all"><a class="btn btn-line" href="/compare/">Compare any two</a></p>
    </div>"""


for _i, _pg in enumerate(PAGES):
    if _pg[0] == "/":
        PAGES[_i] = _pg[:4] + (_pg[4].replace("<!--compare-card-->", home_compare_card(), 1),) + _pg[5:]

LLMS_SECTIONS = [("/sellers/", "Sellers and online clinics"), ("/peptides/", "Peptides"), ("/compare/", "Comparisons"),
                 ("/learn/", "Guides"), ("/fda-warning-letters/", "FDA warning letters")]


def llms_sections():
    """llms.txt (pages.md, Every page): the pages by section, each heading with its page count from this build."""
    goal_paths = {goal_href(g) for g in ALL_GOALS if g.get("page")}
    groups = {"Home and goals": [], **{name: [] for _, name in LLMS_SECTIONS}, "About the site": []}
    for p, _, t, d, *_ in PAGES:
        if p in NOINDEX:
            continue
        name = ("Home and goals" if p in goal_paths or p == "/" else
                next((n for pre, n in LLMS_SECTIONS if p.startswith(pre)), "About the site"))
        groups[name].append(f"- [{t}]({SITE}{p}): {d}\n")
    return "".join(f"\n## {name} ({plural(len(rows), 'page')})\n\n" + "".join(rows) for name, rows in groups.items() if rows)


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "assets" / "og").mkdir(parents=True)
    for f in (ROOT / "assets").iterdir():
        if f.is_file():
            shutil.copy(f, DIST / "assets" / f.name)
    (DIST / "assets" / "fonts").mkdir()
    for f in (ROOT / "assets" / "fonts").iterdir():
        shutil.copy(f, DIST / "assets" / "fonts" / f.name)
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
        + llms_sections())
    # the search index (pages.md, Every page, Header, Search): one entry per page, substance and seller
    if COMPARE_DATA:
        (DIST / "compare" / "data.json").write_text(COMPARE_DATA, encoding="utf-8")
    (DIST / "search-index.json").write_text(json.dumps(search_index(), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    # lastmod: the newest data date of this build, the database pull when connected, else the hand-checked date (owner, Q1 a, 2 Nov 2026)
    lastmod = max(DATA["checked"], (DATA.get("pulled_at") or "")[:10])
    urls = "".join(f"<url><loc>{SITE}{p[0]}</loc><lastmod>{lastmod}</lastmod></url>" for p in PAGES if p[0] not in NOINDEX)
    (DIST / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    (DIST / "pages.json").write_text(json.dumps([{"path": p[0], "title": p[2]} for p in PAGES] + [{"path": "/404", "title": "Page not found | Peptide Chooser"}]))
    print("built", len(PAGES) + 1, "pages")


# The Learn section (pages.md, Learn and Guide): /learn/ and the guides, from guides.py, which reads this module's helpers.
PAGES += guides.pages(sys.modules[__name__])


if __name__ == "__main__":
    main()
