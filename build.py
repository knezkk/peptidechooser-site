"""Builds the static Peptide Chooser site into ./dist. Run: python3 build.py

Design source: design/tokens.json and design/bundle.css (copies of the Master 1 design book).
Numbers source: data/site.json. Nothing numeric is typed into a template.
"""
from pathlib import Path
import json
import os
import sys
import re
from html import escape, unescape
from urllib.parse import urlparse
import shutil
import subprocess
from datetime import date

import guides
import parts
import home
import paid

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
SITE = "https://peptidechooser.com"
EMAIL = "hello@peptidechooser.com"
AUTHOR = "Peptide Chooser editorial team"

# SITE_JSON points at another data file (a local preview with database rows); the deploy always reads data/site.json.
DATA = json.loads(Path(os.environ.get("SITE_JSON") or ROOT / "data" / "site.json").read_text(encoding="utf-8"))
# The HHS compounding policy of 30 Oct 2026 is worded once, in legal.hhs_policy (owner queue block 4, 7 Nov 2026): every
# {hhs_<key>} in the data is that entry's text, so no page types its own version.
HHS = DATA["legal"].get("hhs_policy") or {}
if HHS:
    _raw = json.dumps(DATA, ensure_ascii=False)
    for _k, _v in HHS.items():
        if isinstance(_v, str):
            _raw = _raw.replace("{hhs_" + _k + "}", json.dumps(_v, ensure_ascii=False)[1:-1])
    DATA = json.loads(_raw)
    HHS = DATA["legal"]["hhs_policy"]


def hhs_sentence(what):
    """The policy in one sentence for the peptides named in `what` ("BPC-157 and TB-500"), from legal.hhs_policy."""
    return HHS["sentence"].replace("{what}", what) if HHS else ""
TOKENS = json.loads((ROOT / "design" / "tokens.json").read_text(encoding="utf-8"))
LIVE_GOALS = [g for g in DATA["goals"] if g.get("live")]
# the newest data date of this build: the database pull when connected, else the hand-checked date (owner, Q1 a, 2 Nov 2026)
DATA_CHECKED = max(DATA["checked"], (DATA.get("pulled_at") or "")[:10])
COLOR = {t["name"]: t["value"] for t in TOKENS["color"]["tokens"]}


def nice_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%b %Y')}"


CHECKED = nice_date(DATA["checked"])


def text_changed(*ranges):
    """The date of the last commit that changed these lines (owner answer Q2 b, 4 Nov 2026): "Last updated" on /privacy/ and
    /disclosure/, never typed. Each range is (first line regex, last line regex, file). A shallow clone would give the wrong
    date, so the build stops; lines with no commit yet take the newest commit's date, never the build clock."""
    def git(*args):
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if git("rev-parse", "--is-shallow-repository").stdout.strip() == "true":
        sys.exit("build.py: a shallow clone has no text dates; check out with fetch-depth 0")
    dates = [git("log", "-1", "-s", "--format=%cs", "-L", f"/{a}/,/{b}/:{f}").stdout.strip()[:10] for a, b, f in ranges]
    newest = git("log", "-1", "--format=%cs").stdout.strip()
    return nice_date(max(d or newest for d in dates))


GA4_ID = DATA.get("ga4_id", "")

# Google Analytics 4 with Consent Mode v2. Everything starts denied; the cookie notice (design book,
# Pages and buttons, item 6) flips analytics_storage to granted only after "Accept". The choice is kept
# in localStorage under "pc-consent" so the bar is shown once.
# Google's script loads only after "Accept" (now or on an earlier visit), so nothing reaches Google before consent, as the
# privacy policy says; consent mode alone still sent cookieless pings (design/site-polish, 2 Nov 2026).
# The search words (?q=) never reach Google: the address and the referrer are sent without them (pages/every-page.md, Measurement).
ANALYTICS = f"""<script>
window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}
gtag('consent','default',{{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',analytics_storage:'denied'}});
window.pcLoadGA=function(){{if(window.pcGA)return;window.pcGA=1;gtag('consent','update',{{analytics_storage:'granted'}});
function noq(u){{try{{var x=new URL(u);x.searchParams.delete('q');return x.href;}}catch(e){{return '';}}}}
gtag('set',{{page_location:noq(location.href),page_referrer:noq(document.referrer)}});
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


def ev(name, **params):
    """The data attributes the events script reads (pages/every-page.md, Measurement): slugs and numbers only."""
    return f' data-ev="{name}"' + "".join(f' data-ev-{k}="{escape(str(v))}"' for k, v in params.items() if v not in (None, ""))


def page_type(path):
    """`page_type` of every event, on <body data-pt> (pages/every-page.md, Measurement)."""
    bits = path.strip("/").split("/")
    if path == "/":
        return "home"
    if len(bits) == 1 and bits[0] in {g["slug"] for g in ALL_GOALS}:
        return "goal"
    if bits[0] == "compare":
        return "compare"
    if bits[0] == "fda-warning-letters":
        return "letters"
    if bits[0] == "search":
        return "search"
    if bits[0] == "sellers":
        return "seller" if len(bits) > 1 else "sellers"
    if bits[0] == "peptides" and len(bits) > 1:
        return "peptide"
    if bits[0] == "learn" and len(bits) > 1:
        return "guide"
    return "other"


def author_line(iso):
    """The one author line of every inner page (goal, seller, peptide, compare, guide, letters; pages.md, Rules that apply
    to every page): the team linked to /about/ and the newest data date the page shows."""
    return f'<p class="small meta"><a href="/about/">{AUTHOR}</a>. Checked {nice_date(iso)}.</p>'


# its own line under the author line on the goal and peptide pages (owner answer Q2 b, 3 Nov 2026)
SOURCE_LINE = '\n        <p class="small meta">Every claim links to its source.</p>'

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
NAV_SCRIPT = """// Header categories (pages.md, Every page, Header; owner task 3 Nov 2026): one open at a time. From 1180px a mouse opens
// a category on hover and closes it 250ms after leaving; a click, Enter or Space opens it too (a mouse click never closes
// one the hover opened). Arrow keys: left and right between the categories, down into the panel, up and down inside it.
// Escape, a click outside or focus leaving closes it. Under 1180px the same buttons open the accordion inside the Menu.
(function(){var cats=[].slice.call(document.querySelectorAll('.nav-cat'));if(!cats.length)return;
var btns=cats.map(function(c){return c.querySelector('.nav-cat-btn');}),wide=matchMedia('(min-width: 1180px)'),t=null,ptr='';
function cur(){for(var j=0;j<cats.length;j++)if(cats[j].classList.contains('open'))return j;return -1;}
function set(i){clearTimeout(t);cats.forEach(function(c,j){c.classList.toggle('open',j===i);btns[j].setAttribute('aria-expanded',j===i?'true':'false');});if(i>=0)place(i);}
// the card under its item (owner task 3 Nov 2026): left edge on the item's, moved left so it ends 24px inside the container
function place(i){var pn=cats[i].querySelector('.nav-panel'),h=document.querySelector('.site-head'),w=h&&h.querySelector('.wrap');if(!w)return;
if(!wide.matches){pn.style.left='';return;}var r=w.getBoundingClientRect(),cs=getComputedStyle(w),L=r.left+parseFloat(cs.paddingLeft),R=r.right-parseFloat(cs.paddingRight);
var x=Math.max(L,Math.min(btns[i].getBoundingClientRect().left,R-24-pn.offsetWidth));pn.style.left=Math.round(x-h.getBoundingClientRect().left)+'px';}
window.addEventListener('resize',function(){var i=cur();if(i>=0)place(i);});
function links(i){return [].slice.call(cats[i].querySelectorAll('.nav-panel a'));}
cats.forEach(function(c,i){var b=btns[i];
b.addEventListener('pointerdown',function(e){ptr=e.pointerType;});
b.addEventListener('click',function(){var m=ptr==='mouse'&&wide.matches;ptr='';set(m||cur()!==i?i:-1);});
c.addEventListener('pointerenter',function(e){if(e.pointerType==='mouse'&&wide.matches)set(i);});
c.addEventListener('pointerleave',function(e){if(e.pointerType==='mouse'&&wide.matches&&cur()===i){clearTimeout(t);t=setTimeout(function(){set(-1);},250);}});
b.addEventListener('keydown',function(e){var k=e.key,n=btns.length;
if(wide.matches&&(k==='ArrowRight'||k==='ArrowLeft')){e.preventDefault();var j=(i+(k==='ArrowRight'?1:n-1))%n;btns[j].focus();if(cur()>=0)set(j);}
else if(k==='ArrowDown'){e.preventDefault();set(i);var l=links(i);if(l[0])l[0].focus();}});
c.querySelector('.nav-panel').addEventListener('keydown',function(e){var l=links(i),p=l.indexOf(document.activeElement);if(p<0)return;
if(e.key==='ArrowDown'){e.preventDefault();l[(p+1)%l.length].focus();}
else if(e.key==='ArrowUp'){e.preventDefault();if(p===0)b.focus();else l[p-1].focus();}});});
document.addEventListener('click',function(e){if(cur()>=0&&!e.target.closest('.nav-cat,.nav-toggle'))set(-1);});
document.addEventListener('focusin',function(e){if(wide.matches&&cur()>=0&&!e.target.closest('.nav-cat'))set(-1);});
// registered before the Menu's own Escape, so the first Escape closes only the open category
document.addEventListener('keydown',function(e){var i=cur();if(e.key==='Escape'&&i>=0&&wide.matches){e.stopImmediatePropagation();set(-1);btns[i].focus();}});
wide.addEventListener('change',function(){set(-1);});
var tg=document.querySelector('.nav-toggle');if(tg)tg.addEventListener('click',function(){if(tg.getAttribute('aria-expanded')!=='true'&&cur()<0)set(0);});})();
(function(){var b=document.querySelector('.nav-toggle'),n=document.getElementById('site-nav');if(!b||!n)return;
function set(o){n.classList.toggle('open',o);b.setAttribute('aria-expanded',o?'true':'false');}
// opening the menu moves focus to its first visible link: the links come before the button in the page, so Tab alone
// would skip them (design/site-polish, 2 Nov 2026)
b.addEventListener('click',function(){var o=!n.classList.contains('open');set(o);if(o){var f=[].filter.call(n.querySelectorAll('a,button,input'),function(x){return x.offsetParent;})[0];if(f)f.focus();}});
n.addEventListener('click',function(e){if(e.target.closest('a'))set(false);});
// phones (owner task 3 Nov 2026, the 390px walkthrough): "Search" beside "Menu" opens the menu with the search field
// focused, and a tap anywhere outside the open menu closes it
var st=document.querySelector('.search-toggle'),q=document.getElementById('hs-q');
if(st&&q)st.addEventListener('click',function(){if(!n.classList.contains('open'))b.click();q.focus();});
document.addEventListener('click',function(e){if(n.classList.contains('open')&&!e.target.closest('#site-nav,.nav-toggle,.search-toggle,.head-search,.head-cta'))set(false);});
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&n.classList.contains('open')){set(false);b.focus();}});})();
"""
# Measurement (pages/every-page.md, Measurement; owner decision 5 Nov 2026): what visitors click, in the cached nav.js. One gate,
# the page view's (window.pcGA, set only after "Accept"): without consent an event is dropped, never queued. One listener per
# kind on `document`, so windows loaded on demand are covered; capture, so it runs before a click moves or removes anything.
# Parameters come from data-ev-* attributes the build writes (slugs and numbers), never from what a visitor typed.
# The state filter (pages/windows.md, State filter; owner task 5 Nov 2026): the choice stays in this browser, never in the URL.
STATE_SCRIPT = r"""(function(){var K='pc_state',S={AL:'Alabama',AK:'Alaska',AZ:'Arizona',AR:'Arkansas',CA:'California',CO:'Colorado',CT:'Connecticut',DE:'Delaware',DC:'District of Columbia',FL:'Florida',GA:'Georgia',HI:'Hawaii',ID:'Idaho',IL:'Illinois',IN:'Indiana',IA:'Iowa',KS:'Kansas',KY:'Kentucky',LA:'Louisiana',ME:'Maine',MD:'Maryland',MA:'Massachusetts',MI:'Michigan',MN:'Minnesota',MS:'Mississippi',MO:'Missouri',MT:'Montana',NE:'Nebraska',NV:'Nevada',NH:'New Hampshire',NJ:'New Jersey',NM:'New Mexico',NY:'New York',NC:'North Carolina',ND:'North Dakota',OH:'Ohio',OK:'Oklahoma',OR:'Oregon',PA:'Pennsylvania',RI:'Rhode Island',SC:'South Carolina',SD:'South Dakota',TN:'Tennessee',TX:'Texas',UT:'Utah',VT:'Vermont',VA:'Virginia',WA:'Washington',WV:'West Virginia',WI:'Wisconsin',WY:'Wyoming'},cur='';
try{cur=localStorage.getItem(K)||'';}catch(x){}if(!S[cur])cur='';
function one(s){if(s.options.length<2)Object.keys(S).sort(function(a,b){return S[a].localeCompare(S[b]);}).forEach(function(k){var o=document.createElement('option');o.value=k;o.textContent=k+' '+S[k];s.appendChild(o);});
s.value=cur||'all';s.closest('.state-filter').hidden=false;var id=s.getAttribute('data-state-for'),r=id?document.getElementById(id):s.closest('[data-state-root]');if(!r)return;
var all={},ok={};[].forEach.call(r.querySelectorAll('tr[data-clinic]'),function(t){var c=t.getAttribute('data-clinic'),out=cur&&(' '+(t.getAttribute('data-no')||'')+' ').indexOf(' '+cur+' ')>=0;
all[c]=1;if(out)t.setAttribute('data-state-out','');else{t.removeAttribute('data-state-out');ok[c]=1;}});
var n=r.querySelector('.state-n');if(n){var w=s.getAttribute('data-noun'),m=Object.keys(all).length,x=m-Object.keys(ok).length;n.hidden=!cur;
n.textContent=!cur?'':x?x+' of '+m+' '+w+' '+(x===1?'does':'do')+' not ship to '+S[cur]:'No '+w.slice(0,-1)+' here is known to skip '+S[cur];}}
function paint(){[].forEach.call(document.querySelectorAll('select[data-state]'),one);}
window.pcState=paint;
document.addEventListener('change',function(e){var s=e.target;if(!s.matches||!s.matches('select[data-state]'))return;cur=s.value==='all'?'':s.value;try{if(cur)localStorage.setItem(K,cur);else localStorage.removeItem(K);}catch(x){}paint();document.dispatchEvent(new Event('pc-state'));});
paint();if(cur)document.dispatchEvent(new Event('pc-state'));})();
"""
EVENTS_SCRIPT = r"""
(function(){var path=location.pathname,pt=document.body&&document.body.getAttribute('data-pt')||'other',bits=path.split('/'),base={page_type:pt,page_path:path};
if(pt==='seller')base.seller=bits[2];if(pt==='peptide')base.substance=bits[2];if(pt==='goal')base.goal=bits[1];
function send(n,o){try{if(!window.pcGA)return;var p={},k;for(k in base)p[k]=base[k];for(k in o)if(o[k]||o[k]===0)p[k]=o[k];gtag('event',n,p);}catch(x){}}
window.pcEv=send;
function own(el){var o={},g=el.closest('[data-goal]');[].forEach.call(el.attributes,function(a){if(a.name.indexOf('data-ev-')===0)o[a.name.slice(8)]=/^\d+(\.\d+)?$/.test(a.value)?Number(a.value):a.value;});
if(g&&!o.goal)o.goal=g.getAttribute('data-goal');return o;}
function typed(s){var i=document.querySelector(s);return i?i.value.trim().length:0;}
function letter(a){var m=/\/warning-letters\/([^\/]+)/.exec(a.pathname);return m&&m[1].indexOf('about-')!==0?m[1].slice(0,100):'none';}
document.addEventListener('click',function(e){try{var t=e.target;if(!t||!t.closest)return;
var a=t.closest('a[href]'),el=t.closest('[data-ev]'),c=t.closest('[data-card]'),f=t.closest('button[data-filter]'),r=t.closest('#hs-list a,#sp-results a');
if(a&&/(^|\.)fda\.gov$/.test(a.hostname))send('outbound_fda',{letter:letter(a)});
if(c&&t.closest('a,button')&&!t.closest('.ref'))send('decision_card_click',{card:c.getAttribute('data-card')});
if(r){var k=r.querySelector('.chip');send('search',{query_length:typed(r.closest('#hs-list')?'#hs-q':'#sp-q'),result_type:k?k.textContent.toLowerCase():'other'});}
if(f&&!(f.classList.contains('seg-b')&&f.getAttribute('aria-pressed')==='true'))send('filter_change',{filter:f.getAttribute('data-filter'),value:f.getAttribute('data-value')});
if(el&&el.tagName!=='FORM'&&el.getAttribute('aria-pressed')!=='true')send(el.getAttribute('data-ev'),own(el));
}catch(x){}},true);
document.addEventListener('change',function(e){try{var i=e.target;if(i&&i.getAttribute&&i.getAttribute('data-filter')&&i.tagName!=='BUTTON')send('filter_change',{filter:i.getAttribute('data-filter'),value:i.getAttribute('data-value')||i.value});}catch(x){}},true);
document.addEventListener('submit',function(e){try{var f=e.target;if(f.matches('.head-search,#sp-form')){var n=f.querySelector('input').value.trim().length;if(n)send('search',{query_length:n,result_type:'page'});}
else if(f.getAttribute('data-ev')==='newsletter_submit')send('newsletter_submit',{});}catch(x){}},true);})();
"""
# one cached file for every page instead of 4 KB inline on each (Home stays under its 60 KB check with the card menu)
NAV_JS = '<script src="/assets/nav.js" defer></script>'
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
(function(){var idx=null,wait=[],ORDER={Goal:0,Peptide:1,Seller:2,Clinic:3,Comparison:4,Guide:5,Page:6};
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
else if(e.key==='Enter'&&!list.hidden&&act>=0&&res[act]){e.preventDefault();if(window.pcEv)pcEv('search',{query_length:inp.value.trim().length,result_type:String(res[act].type).toLowerCase()});location.href=res[act].url;}
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
// a jump to an anchor (/weight-loss/#clinics) never lands on a hidden heading (owner UX audit B24, 3 Nov 2026): with a
// hash, or on a hash change, everything shows at once; otherwise what is already in or above the window shows on load
var show=function(els){{gsap.set(els,{{opacity:1,y:0}});}};
if(location.hash){{show(sel);return;}}
window.addEventListener('hashchange',function(){{ScrollTrigger.getAll().forEach(function(t){{t.kill();}});show(sel);}});
show([].filter.call(document.querySelectorAll(sel),function(el){{return el.getBoundingClientRect().top<innerHeight;}}));
ScrollTrigger.batch(sel,{{start:'top 92%',once:true,
onEnter:function(els){{els=els.filter(function(el){{return getComputedStyle(el).opacity!=='1';}});if(els.length)gsap.fromTo(els,{{opacity:0,y:rise}},{{opacity:1,y:0,duration:ms('reveal'),ease:'power2.out',stagger:ms('stagger'),overwrite:true}});}}}});
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
        if t.get("tint"):
            out.append(f"  --{t['name']}-tint: {t['tint']};")
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
                    for g in CHOOSER_GOALS if g.get("page") and g["slug"] != skip)
    return f"""
<section class="section goals-strip" id="other-goals">
  <div class="wrap">
    <h2 class="h-sources">{heading}</h2>
    <div class="btn-row">{links}</div>
  </div>
</section>""" if links else ""


# Header categories (pages.md, Every page, Header; owner task 3 Nov 2026, the "Home v2" sketch): five buttons, each opening
# a panel of links to pages (never a section of Home). A link shows only when its page is in this build, a category only
# when it has a link. By goal groups the goal pages as below, each with its option count and the cheapest price the data has.
NAV_GOAL_GROUPS = [("Hair and skin", ("hair", "skin")), ("Weight", ("weight-loss",)), ("Body", ("muscle", "recovery")),
                   ("Drive and aging", ("libido", "longevity"))]
# "Body" added (owner answer 2 a to w2, 3 Nov 2026): /learn/ has a sixth topic for the muscle, skin, recovery, libido and aging guides
LEARN_TOPICS = [("hair", "Hair"), ("glp1", "GLP-1"), ("legal", "Legal"), ("buying", "Buying"), ("data", "Data"), ("body", "Body")]


def goal_from(g):
    """"from $10/mo" for the goal's cheapest price: its checked price (the Home price source), else its cheapest
    FDA-approved clinic plan; None when the data has neither."""
    if g["slug"] in PRICE_REF:
        return f'${g["price_from_usd"]}/mo'
    plan = cheapest_plan(g)
    return f'{usd(plan["price_monthly"])}/mo' if plan else None


def nav_link(path, href, label, sub="", attrs=""):
    cur = ' aria-current="page"' if href == path else ""
    sub = f'<span class="nav-sub">{sub}</span>' if sub else ""
    return f'<li><a href="{href}"{cur}{attrs}><span class="nav-l">{label}</span>{sub}</a></li>'


def nav_counts():
    """The count sentence under "Start here" (pages.md, Every page, Header; owner task 3 Nov 2026), from this build."""
    parts = [plural(len(PROFILES), "seller") if PROFILES else "", plural(len(PEPTIDE_SLUGS), "substance") if PEPTIDE_SLUGS else "",
             plural(len(LETTERS_ALL), "FDA letter") if LETTERS_ALL else ""]
    parts = [x for x in parts if x]
    return (", ".join(parts) + ". " if parts else "") + f"Checked {nice_date(DATA_CHECKED)}."


def top_substances(n=2):
    """The substances the most sellers list (shops' substances and clinics' plan medicines), with a page in this build."""
    count = {}
    for r in PROFILES.values():
        for x in (clinic_subs(r) if r["seller_slug"] in CLINIC_PROFILES else shop_subs(r)):
            count[x] = count.get(x, 0) + 1
    return [x for x in sorted(count, key=lambda x: (-count[x], x)) if x in PEPTIDE_SLUGS][:n]


def nav_cats(path):
    goals = {g["slug"]: g for g in ALL_GOALS if g.get("page") and built(f'/{g["slug"]}/')}

    def goal_link(sl):
        g = goals[sl]
        return nav_link(path, f"/{sl}/", g["label"], plural(len(g["peptides"]), "option") + (f", from {goal_from(g)}" if goal_from(g) else ""), ev("goal_pick", goal=sl))

    def col(groups):
        out = "".join(f'<p class="nav-h">{head}</p><ul>{"".join(goal_link(x) for x in slugs if x in goals)}</ul>'
                      for head, slugs in groups if any(x in goals for x in slugs))
        return f'<div class="nav-col">{out}</div>' if out else ""

    # By goal in two columns, as in the sketch: Hair and skin with Weight, then Body with Drive and aging
    goal_cols = [col(NAV_GOAL_GROUPS[:2]), col(NAV_GOAL_GROUPS[2:])]
    letters_on = max((r["letter_date"] for r in LETTERS_ALL if r.get("letter_date")), default="")
    plans, sellers = compare_items() if (PLANS or PROFILES) else ([], [])
    legal = next((g["line"] for g in guides.GUIDES if g["slug"] == "are-peptides-legal-in-the-us"), "")
    topics = {t: sum(1 for g in guides.GUIDES if guides.TOPIC.get(g["slug"]) == t) for t, _ in LEARN_TOPICS}
    flat = {
        "sellers": ("Sellers", [("/sellers/#clinics", "Online clinics", plural(len(CLINIC_PROFILES), "clinic") if CLINIC_PROFILES else ""),
                                ("/sellers/", "Research-use shops", plural(len(SHOPS), "shop") if SHOPS else ""),
                                ("/compare/", "Compare any two", " and ".join(x for x in (plural(len(plans), "plan") if plans else "",
                                                                                          plural(len(sellers), "seller") if sellers else "") if x))]),
        "peptides": ("Peptides", [("/peptides/", "A to Z", plural(len(PEPTIDE_SLUGS), "substance") if PEPTIDE_SLUGS else ""),
                                  ("/learn/are-peptides-legal-in-the-us/", "Legal status", legal),
                                  ("/fda-warning-letters/", "FDA warning letters",
                                   f'{plural(len(LETTERS_ALL), "letter")}, the newest {nice_date(letters_on)}' if letters_on else "")]),
        "learn": ("Learn", [(f"/learn/#{t}", label, plural(topics[t], "guide")) for t, label in LEARN_TOPICS if topics[t]]
                  + [("/learn/", "All guides", plural(len(guides.GUIDES), "guide"))]),
        "about": ("About", [("/how-we-rate/", "How we rate", ""), ("/about/", "About", ""), ("/contact/", "Contact", ""),
                            ("/disclosure/", "How we make money", "")]),
    }
    # "Start here", the card's right column: three links per category to pages in this build
    start = {
        "goal": [("/", "Cheapest approved option per goal"), ("/learn/are-peptides-legal-in-the-us/", "Is it legal today?"),
                 ("/how-we-rate/", "How we rate sellers")],
        "sellers": [("/sellers/#clinics", "Online clinics first"), ("/compare/", "Compare any two"), ("/how-we-rate/", "How we rate")],
        "peptides": [(f"/peptides/{x}/", re.sub(r" *\(.*\)$", "", sub_label(x))) for x in top_substances()]
                    + [("/fda-warning-letters/", "FDA warning letters")],
        "learn": [(f'/learn/{g["slug"]}/', g["title"]) for g in guides.GUIDES[-3:]],  # the guides added last
        "about": [("/disclosure/", "How we make money"), ("/contact/", "Contact"), ("/corrections/", "Corrections")],
    }
    panels = [("goal", "By goal", "".join(goal_cols))]
    for key, (label, items) in flat.items():
        links = "".join(nav_link(path, h, t, sub) for h, t, sub in items if built(h.split("#")[0])
                        and (t != "Online clinics" or CLINIC_PROFILES) and (t != "Research-use shops" or SHOPS))
        if links:
            panels.append((key, label, f'<div class="nav-col"><ul>{links}</ul></div>'))

    def side(key):
        links = "".join(f'<li><a href="{h}">{escape(t)}</a></li>' for h, t in start[key] if built(h.split("#")[0]))
        return (f'<div class="nav-side"><p class="nav-h">Start here</p><ul>{links}</ul><p class="nav-count">{nav_counts()}</p></div>'
                if links else "")
    return '<ul class="nav-cats">' + "".join(
        f'<li class="nav-cat"><button type="button" class="nav-cat-btn" aria-expanded="false" aria-controls="nav-p-{key}">{label}</button>'
        f'<div class="nav-panel nav-card" id="nav-p-{key}"><div class="nav-panel-in">{inner}{side(key)}</div></div></li>'
        for key, label, inner in panels if inner) + "</ul>"


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


# One page per search (data/canonicals.json, queue block 8): a listed page points its canonical at the page that keeps the
# search, leaves the sitemap and llms.txt, and links to it from other pages go to that page.
CANON = json.loads((ROOT / "data" / "canonicals.json").read_text(encoding="utf-8"))["pages"] if (ROOT / "data" / "canonicals.json").exists() else {}


def page(path, title, description, body, schema="", crumb=None):
    canonical = SITE + CANON.get(path, path)
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
<body data-pt="{page_type(path)}">
<a class="skip" href="#main">Skip to content</a>
<div class="notice"><div class="wrap"><p>Independent. Every price checked and dated. Some links pay us. <a href="/disclosure/">How we make money</a></p></div></div>
<header class="site-head">
  <div class="wrap">
    <a class="brand" href="/"><img src="/assets/logo.svg" alt="" width="50" height="20">Peptide Chooser</a>
    <nav class="nav" id="site-nav" aria-label="Main">{nav_cats(path)}</nav>
    {SEARCH_FORM}
    {head_cta()}
    <button type="button" class="btn btn-line btn-sm search-toggle" aria-controls="site-nav">Search</button>
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
        <p>An independent comparison site for the United States that sells nothing and is not medical advice: talk to a doctor before starting any treatment.</p>
      </div>
      {foot_cols()}
    </div>
    <p class="trust">&copy; 2026 Peptide Chooser · {EMAIL} · Data checked {nice_date(DATA_CHECKED)}</p>
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


ALL_GOALS = DATA["goals"]
# The hair goal's cosmetic option is a scalp product (data agent's task 33): its window takes only listings named for hair or scalp.
SCALP_OPTIONS = {id(p) for g in ALL_GOALS if g["slug"] == "hair" for p in g.get("peptides") or [] if p["status"].startswith("Cosmetic")}
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
# A plan's monthly figure includes its monthly membership or care fee when the data has one (data agent's task 33, owner
# 7 Nov 2026: Ivim stores the medication, $65, and the membership, $74.99, apart; the reader pays $139.99). The medicine's
# own price stays in price_medicine; the care fee is shown as included, never added twice.
for _p in PLANS:
    _p["price_medicine"] = _p.get("price_monthly")
    _fee = _p.get("membership_fee_monthly")
    if _p.get("price_monthly") is not None and _fee is not None and float(_fee) > 0:
        _p["price_monthly"] = round(float(_p["price_monthly"]) + float(_fee), 2)


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


# The price per mg band (owner, 2 Nov 2026): a value outside $0.01 to $100/mg is a misread unit until the database fixes it.
PPM_LOW, PPM_HIGH = 0.01, 100


def per_mg(v):
    """A price per mg as people read it: cents from $0.10 up, else two significant figures ($0.019)."""
    return f"${v:,.2f}" if v >= 0.1 else f"${v:.2g}"


def plural(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"


# A goal's clinic plans (pages.md, Category, weight loss; owner task 2 Nov 2026): the rows of site.plan_prices whose
# substance is one of the goal's `clinic_plans.substances`. A plan with no substance, or another one, shows only on the seller's
# own page, never on a goal page or in a clinic window, until the data carries a goal tag (owner answer to #104 Q2 A, 5 Nov 2026).
BRANDED = ("branded", "oral_branded")


def clinic_plans(g):
    cp = g.get("clinic_plans")
    if not cp:
        return []
    rows = [r for r in PLANS if r.get("price_monthly") is not None
            and r["substance_slug"] in cp["substances"]]
    return sorted(rows, key=lambda r: (float(r["price_monthly"]), r["seller_name"], r["plan_name"]))


def goal_plans(g):
    """Every clinic plan for a goal, cheapest first: its `clinic_plans` rows, else the plans of its options' substances
    (any kind; the goal page's Cheapest card, owner task 3 Nov 2026)."""
    if g.get("clinic_plans"):
        return clinic_plans(g)
    subs = {s for p in g["peptides"] for s in ([p["substance"]] if p.get("substance") else [])}
    return sorted((r for r in PLANS if r["substance_slug"] in subs and r.get("price_monthly") is not None),
                  key=lambda r: (float(r["price_monthly"]), r["seller_name"], r["plan_name"]))


def other_use(g, r):
    """A brand plan whose brand is approved for another use (`clinic_plans.other_use`, e.g. Ozempic: diabetes), or ""."""
    return next((use for brand, use in (g.get("clinic_plans") or {}).get("other_use", {}).items()
                 if r.get("product_kind") in BRANDED and r["plan_name"].split()[0] == brand), "")


def needs_rx(p):
    """True when the option's "how" line says it takes a prescription, False when it says none is needed (over the
    counter, or "no prescription"), None when it says neither (owner UX audit, 3 Nov 2026)."""
    how = p.get("how", "").lower()
    if "no prescription" in how or "over the counter" in how:
        return False
    return True if how.startswith("prescription") else None


def plan_fits(p, r):
    """A plan fits a medicine sold without a prescription only when it is one too: never a compounded plan or a pill (owner
    answer Q5 a, 4 Nov 2026: Keeps' Oral Minoxidil stood on the Minoxidil row, "a liquid or foam, no prescription")."""
    if needs_rx(p) is not False:
        return True
    return (r.get("product_kind") != "compounded" and (r.get("dosage_form") or "") not in ("tablet", "capsule")
            and not re.search(r"\boral\b", r.get("plan_name") or "", re.I))


def row_fits(p, r):
    """A plan stands on an FDA-approved row when its substance is the row's `substance` or one of its `plan_substances` (the
    data's own slug: Winona's "estrogen" on the Estradiol row), and its name matches the row's `plan_name_match` when the row
    has one (only the forms the approval covers: tablets and patches, never a body cream; owner task 7 Nov 2026)."""
    if r["substance_slug"] != p["substance"] and r["substance_slug"] not in (p.get("plan_substances") or []):
        return False
    return not p.get("plan_name_match") or bool(re.search(p["plan_name_match"], r.get("plan_name") or "", re.I))


def form_fits(p, r, strict=True):
    """An option that names its form (`plan_form`, "shot" or "pill") takes only plans of that form: a card's price and window are
    the same medicine in the same form (owner's audit, 7 Nov 2026: the Wegovy shot card showed the Wegovy Pill's price). Its window
    (strict=False) leaves out only plans of another stated form, so a plan that states none still shows, as "Form not stated"."""
    if not p.get("plan_form"):
        return True
    f = (r.get("dosage_form") or "").lower()  # plan_form's words, read here because module-level tables call this first
    form = "pill" if f in ("tablet", "capsule", "oral", "odt") else "shot" if f in ("injection_vial", "pen", "injection") else ""
    return form == p["plan_form"] or (not strict and not f)


def compounded_subs(g, p):
    """The substances of a compounded row: its own `plan_substances` (the hair goal's minoxidil spray), else the goal's approved ones."""
    return set(p.get("plan_substances") or []) or {x["substance"] for x in g["peptides"] if x.get("substance") and x["status"].startswith("FDA approved")}


def row_plan(g, p):
    """The plan behind an option row's "Online clinics from" line on a goal with clinic plans: an FDA-approved row, the
    cheapest brand plan (branded or oral_branded) of its substance; the compounded row (`plan_kind`), the cheapest
    compounded plan of the goal's approved substances. On a goal without clinic plans, an FDA-approved row with a
    substance gets its substance's cheapest plan that is not compounded (Home v2, 3 Nov 2026: minoxidil at Keeps).
    None for other rows."""
    if p.get("plan_kind") == "compounded" and not g.get("clinic_plans"):
        found = [r for r in PLANS if r["substance_slug"] in compounded_subs(g, p) and r.get("price_monthly") is not None
                 and r.get("product_kind") == "compounded"]
        return min(found, key=lambda r: (float(r["price_monthly"]), r["seller_name"])) if found else None
    if not g.get("clinic_plans"):
        if not (p.get("substance") and p["status"].startswith("FDA approved")):
            return None
        found = [r for r in PLANS if row_fits(p, r) and r.get("price_monthly") is not None
                 and r.get("product_kind") != "compounded" and plan_fits(p, r) and form_fits(p, r)]
        best = min(found, key=lambda r: (float(r["price_monthly"]), r["seller_name"])) if found else None
        plan = GOAL_PLANS.get(g["slug"])
        return plan if best and plan and best["seller_slug"] == plan["seller_slug"] and best["plan_slug"] == plan["plan_slug"] else best
    rows = clinic_plans(g)
    if p.get("plan_kind") == "compounded":
        subs = compounded_subs(g, p)
        found = [r for r in rows if r.get("product_kind") == "compounded" and r["substance_slug"] in subs]
    elif p.get("substance") and p["status"].startswith("FDA approved"):
        found = [r for r in rows if row_fits(p, r) and r.get("product_kind") in BRANDED
                 and not other_use(g, r) and form_fits(p, r)]
    else:
        return None
    return found[0] if found else None


# Plans shown on a row or a price pad that are not a goal's GOAL_PLANS plan get their own source after the plan sources.
plan_key = lambda r: f'{r["seller_slug"]}-{r["plan_slug"]}'
EXTRA_PLANS = {}
for _g in ALL_GOALS:
    _rows = goal_plans(_g)
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


def letter_href(slug):
    """Where a letter chip in a table goes (owner UX audit A17, 3 Nov 2026): the seller's own letters section,
    /sellers/<slug>/#fda-letters (the id the seller page template gives it), else the letters page."""
    return f"/sellers/{slug}/#fda-letters" if slug in PROFILES else LETTERS_URL


# "Closed by FDA <date>" (pages.md, Letters; a chip state, owner task 4 Nov 2026): only when the data has `closed_on` and
# the close-out letter on fda.gov (peptide-data task 12; both optional, nothing is drawn while they are missing).
LETTER_ROWS = (DATA.get("seller_letters") or []) + (DATA.get("letters_all") or [])
CLOSED = {r["letter_url"]: r for r in LETTER_ROWS if r.get("closed_on") and (r.get("closeout_url") or "").startswith("https://www.fda.gov/")}


def closed_chip(letter_url):
    r = CLOSED.get(letter_url)
    return (f' <a class="chip chip-ok chip-link" href="{escape(r["closeout_url"])}" rel="nofollow">Closed by FDA {nice_date(r["closed_on"][:10])}</a>'
            if r else "")


def seller_closed_chip(slug):
    """The seller window's chip: the newest letter's close-out, only when every letter the seller has is closed."""
    rows = sorted((r for r in DATA.get("seller_letters") or [] if r["seller_slug"] == slug), key=lambda r: r["letter_date"])
    return closed_chip(rows[-1]["letter_url"]) if rows and all(r["letter_url"] in CLOSED for r in rows) else ""


def paid_href(seller_slug, paid):
    """`paid_url` holds the /out/ path from site.paid_links; never a seller's own address."""
    return paid if paid.startswith("/out/") else f"/out/{seller_slug}/"


def paid_ev(seller_slug, paid):
    return ev("paid_link_click", seller=seller_slug, out_path=paid_href(seller_slug, paid))


def plans_ev(seller_slug, plan=None):
    """"See plans": the plan the row shows, else the clinic's cheapest (the price its row shows)."""
    r = PROFILES.get(seller_slug)
    rows = [x for x in (clinic_plan_rows(r) if r else []) if x.get("price_monthly") is not None]
    shown = plan or (min(rows, key=lambda x: float(x["price_monthly"])) if rows else None)
    return ev("see_plans_click", seller=seller_slug, price_month=shown and shown.get("price_monthly"),
              kind=shown and plan_kind(shown), substance=plan and plan.get("substance_slug"))


def plan_letter(r):
    """The clinic's FDA letter chip beside a clinic price (owner decision 2 Nov 2026, enforced after the owner UX audit,
    3 Nov 2026: Strut Health's $25/mo showed no letter): every place a plan price appears, or "" without a letter."""
    if (r.get("fda_letter_count") or 0) and r.get("last_fda_letter_date"):
        return f' <a class="chip chip-warn chip-link" href="{letter_href(r["seller_slug"])}">FDA letter {nice_date(r["last_fda_letter_date"])}</a>'
    return ""


def plan_line(g, cls, r=None):
    """"Online clinics from $25/mo (Strut Health)" with its footnote: the goal's plan, or the plan row given; "" when
    there is none."""
    r = r or GOAL_PLANS.get(g["slug"])
    if not r:
        return ""
    sid, n = plan_ref(g, r)
    return (f'<span class="{cls}">Online clinics from {usd(r["price_monthly"])}/mo ({clinic_link(r["seller_slug"], seller_base(r["seller_name"]), True)})'
            f'<sup><a class="ref" href="#{sid}" aria-label="Source {n}">{n}</a></sup>{plan_letter(r)}</span>')

# Numbers from the database (tools/pull_data.py writes these keys when SITE_DATABASE_URL is set). Without them the
# page renders the hand-written statuses and dates above, unchanged.
DB = DATA.get("db")
LEGAL_DB = DATA.get("legal_db")
# Until the database carries the HHS policy (regime hhs_503a_interim, status listed), its rows come from legal.hhs_policy,
# one per listed substance the database already names, so a database build shows the same status as the repo build.
if LEGAL_DB is not None and HHS and not any(r["regime"] == "hhs_503a_interim" for r in LEGAL_DB):
    _names = {r["substance_slug"]: r["canonical_name"] for r in LEGAL_DB}
    LEGAL_DB = LEGAL_DB + [{"substance_slug": x, "canonical_name": _names[x], "regime": "hhs_503a_interim", "status_value": "listed",
                            "source_url": HHS["url"], "source_id": "hand_hhs_policy", "first_seen_by_us": HHS["seen"], "valid_from": HHS["date"], "fda_listing": None}
                           for x in HHS["substances"] if x in _names]
APPROVED_DB = DATA.get("approved_db") or []
_plan_seen = max((r["last_seen"] for r in GOAL_PLANS.values()), default="")
_prices_on = DB.get("prices_checked_on", "") if DB else ""
STAMP_CHECKED = nice_date(max(_prices_on, _plan_seen)) if (_prices_on or _plan_seen) else CHECKED
GOAL_CHECKED = max(DATA["checked"], _prices_on, _plan_seen)  # the goal pages' data date: hand check, prices, plans
# The one lookup from a database status to what the page shows: (regime, status_value) -> (rank, chip, label, sentence).
# Lower rank wins when a substance has several open statuses. Statuses not listed here (shortage, not_listed) are
# not legal statuses and are skipped.
DB_STATUS = {
    ("fda_approval", "approved"): (0, "ok", "FDA approved", "an FDA-approved product exists"),
    # the HHS policy of 30 Oct 2026 is newer than the FDA's lists for the six peptides it names, so it wins over them
    ("hhs_503a_interim", "listed"): (0.5, "neutral", "Not approved", HHS.get("note", "")),
    # the database carries the policy as "enforcement_discretion" (7 Nov 2026); the same fact, so the same words (owner: the HHS text stays)
    ("hhs_503a_interim", "enforcement_discretion"): (0.5, "neutral", "Not approved", HHS.get("note", "")),
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
    # a status split by route (GHK-Cu: category 1 "except for injectable routes", a withdrawn nomination "for injectable
    # routes"; data agent's task 33): both rows are shown, each with its own words, listing and source, the same everywhere
    inj = [x for x in rows if re.search(r"\(for injectable routes", x[1].get("fda_listing") or "")]
    other = [x for x in rows if re.search(r"\(except for injectable routes", x[1].get("fda_listing") or "")]
    routes = [(by, x[0][3], x[1]) for by, x in (("by injection", min(inj, key=lambda x: x[0][0]) if inj else None),
                                                 ("by other routes", min(other, key=lambda x: x[0][0]) if other else None)) if x]
    if len(routes) == 2:
        sentence = "; ".join(f"{by}, {said}" for by, said, _ in routes)
    # generic products carry the substance's own name as their brand; those are not brands (Finasteride -> Propecia, Proscar)
    generic = row["canonical_name"].split()[0].title()
    brands = sorted({brand_base(a["brand_name"]) for a in APPROVED_DB if a["substance_slug"] == slug and a.get("brand_name")} - {generic})[:4]
    name = row["canonical_name"] + (f' ({", ".join(brands)})' if brands and chip == "ok" else "")
    # the FDA's own wording, from the same row as the status shown (fda_listing; shown in small, never required). GHK-Cu has
    # two rows with two wordings ("except for injectable" on category 1, "for injectable" on the withdrawn nomination);
    # another row's wording under this status would pair the wrong facts.
    listing = row.get("fda_listing") or ""
    split = [{"listing": r.get("fda_listing") or "", "url": r["source_url"]} for _, _, r in routes] if len(routes) == 2 else []
    return {"chip": chip, "label": label, "sentence": sentence, "name": name, "url": row["source_url"],
            "seen": min(r["first_seen_by_us"] for _, _, r in routes) if split else row["first_seen_by_us"],
            "listing": "; ".join(f'"{x["listing"]}"' for x in split)[1:-1] if split else listing, "routes": split,
            # the short form for a meta description (160 characters)
            "meta": "by injection, its compounding nomination was withdrawn; by other routes, pharmacies may compound it" if split else ""}


def source_word(url):
    """The link word for a status source: "FDA source" for fda.gov, else "Source" (the HHS policy)."""
    return "FDA source" if "fda.gov" in url else "Source"


def listing_html(s):
    """The FDA's own wording for a substance in small under its status, when the database has it (fda_listing). A status
    split by route shows both listings, each linked to its own FDA source."""
    if s and s.get("routes"):
        return ('<span class="listing">FDA listings: ' + "; ".join(
            f'<a href="{escape(x["url"])}" rel="nofollow">"{escape(x["listing"])}"</a>' for x in s["routes"]) + "</span>")
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

# The body figure (design book, The body figure): our own offline render of the CC0 MakeHuman model, made by
# tools/render_body/. Only the images and manifest.json ship; assets/body/ holds one folder per look. Pins sit where the
# render's own camera puts them; a goal's view (zoom z, centre v) comes from the manifest too.
BODY = json.loads((ROOT / "assets" / "body" / "manifest.json").read_text(encoding="utf-8"))
# Home's chooser, its goal cards and the 404 list hold the goals with a pin on the figure (every chooser goal is on the
# figure, pages.md, Home). A goal page without a pin (/menopause/) is built but stays off them until the figure has its pin.
CHOOSER_GOALS = [g for g in ALL_GOALS if all(g["slug"] in v["pins"] for v in BODY["variants"].values())]
BODY_DEFAULT = "neutral-clay"


def figure_3d(variant=BODY_DEFAULT):
    base = f"/assets/body/{variant}/"
    pins = BODY["variants"][variant]["pins"]
    btns = []
    for i, g in enumerate(CHOOSER_GOALS):
        u, v = pins[g["slug"]]
        on = i == 0
        btns.append(f'<span class="pin{" on" if on else ""}" aria-hidden="true" data-goal="{g["slug"]}" aria-pressed="{"true" if on else "false"}" '
                    f'aria-label="{g["label"]}" style="left:{u * 100:.2f}%;top:{v * 100:.2f}%"><span class="pin-ring"><span class="pin-dot"></span></span></span>')
    views = json.dumps({k: {"z": x["z"], "v": x["v"]} for k, x in BODY["views"].items()}, separators=(",", ":"))
    return (f"<div class=\"fig fig3d\" role=\"group\" aria-label=\"Choose a goal on the body\" data-base=\"{base}\" data-views='{views}'>"
            f'<div class="fig3d-view"><div class="fig3d-stage"><img class="fig3d-full" src="{base}full-744.webp" '
            f'srcset="{base}full-380.webp 190w, {base}full-744.webp 372w, {base}full-1080.webp 540w" '
            f'sizes="(max-width: 899px) 95px, (min-width: 2200px) 270px, (min-width: 1600px) 240px, 186px" '
            f'width="540" height="1080" alt="">{"".join(btns)}</div></div>'
            f'<span class="fig3d-label" hidden></span>'
            f'<button type="button" class="btn btn-line btn-sm fig3d-back" aria-label="Back to full body" hidden>Full body</button></div>')


# Research-use sellers per substance (site.products and site.sellers, tools/pull_data.py keeps each seller's cheapest
# listing, ten per substance). The seller window (pages.md, Home) shows them with their background check; seller names
# are plain text and nothing in the window links to a seller (owner, 31 Oct 2026; tools/check.py enforces it).
PRODUCTS = DATA.get("products") or []
SELLERS = {r["seller_slug"]: r for r in DATA.get("sellers") or []}
# Seller pages (pages.md, Seller): one per seller in site.seller_profile, through tools/pull_data.py
PROFILES = {r["seller_slug"]: r for r in DATA.get("seller_profiles") or []}
# A tool (pages.md, Category, Tools) does not prescribe: no seller page, not counted as a clinic. A shop stays a shop. An entry
# with `clinic` prescribes too (Vitals Vault, owner answer to #104 Q1 A): it keeps its seller page and counts as a clinic.
TOOL_PROFILES = {t["seller_slug"]: PROFILES.pop(t["seller_slug"]) for g in DATA.get("goals") or [] for t in g.get("tools") or []
                 if not t.get("clinic") and not (PROFILES.get(t["seller_slug"]) or {"product_count": 1}).get("product_count")}
# Shops and clinics (peptide-data decision 26; pages.md, Rules that apply to every page): a shop lists products
# (product_count > 0), a clinic only plans (product_count 0). Every list of shops takes SHOPS; a clinic is never in one.
SHOPS = {k: r for k, r in PROFILES.items() if (r.get("product_count") or 0) > 0}
CLINIC_PROFILES = {k: r for k, r in PROFILES.items() if k not in SHOPS}
# A real logo (pages.md, Seller tile): the entry in data/seller_logos.json and the brand's file in assets/logos/, both, never a shop.
# A tool has no seller page: its logo is used only in the Tools block. An entry with neither a page nor a tool waits for its seller.
TOOL_LOGOS = {}
for _slug, _logo in json.loads((ROOT / "data" / "seller_logos.json").read_text(encoding="utf-8")).items():
    _file = next((f for f in (ROOT / "assets" / "logos" / f"{_slug}.{e}" for e in ("svg", "png")) if f.exists()), None)
    if _file and _slug in CLINIC_PROFILES:
        CLINIC_PROFILES[_slug].update(_logo, logo_path=f"/assets/logos/{_file.name}")
    elif _file and _slug in {t["seller_slug"] for g in DATA.get("goals") or [] for t in g.get("tools") or []} and _slug not in SHOPS:
        TOOL_LOGOS[_slug] = {**_logo, "logo_path": f"/assets/logos/{_file.name}"}


# States a clinic does not serve (pages.md, Category and Seller; owner task 4 Nov 2026): data/clinic_states.json, keyed by
# seller slug, until the database has a column. Never typed into a page.
# site.seller_states (a row per seller, or per seller and state) replaces the file once the database has it.
def clinic_states():
    view = {}
    for r in DATA.get("seller_states") or []:
        raw = r.get("excluded_states") or r.get("not_in") or r.get("state_code") or r.get("state") or []
        view.setdefault(r["seller_slug"], {"not_in": []})["not_in"] += re.findall(r"[A-Z]{2}", raw) if isinstance(raw, str) else list(raw)
    return view or {k: v for k, v in json.loads((ROOT / "data" / "clinic_states.json").read_text(encoding="utf-8")).items() if not k.startswith("_")}


CLINIC_STATES = clinic_states()


def strip_tags(t):
    return re.sub(r"<[^>]+>", "", t or "")


def state_attrs(slug):
    """A clinic's row for the state filter (pages/windows.md, State filter): its slug and the states it does not serve. No
    exclusion data means it serves every state."""
    states = (CLINIC_STATES.get(slug) or {}).get("not_in") or []
    return f' data-clinic="{slug}"' + (f' data-no="{" ".join(states)}"' if states else "")


def state_filter(noun="clinics", target=""):
    """"Your state": one control in a filter row. nav.js fills the select, keeps the choice in this browser and hides the rows of
    clinics that do not serve it. Hidden without JavaScript, where every row shows."""
    to = f' data-state-for="{target}"' if target else ""
    return (f'<label class="state-filter" hidden><span>Your state</span><select class="input" data-state data-noun="{noun}"{to} data-filter="state">'
            '<option value="all">All states</option></select></label>')


STATE_N = '<p class="small state-n" aria-live="polite" hidden></p>'


def not_in_line(slug, tag="span"):
    """"Not available in: AL, AK, ..." as one small line, or "" for a clinic that serves every state."""
    states = (CLINIC_STATES.get(slug) or {}).get("not_in")
    return f'<{tag} class="not-in">Not available in: {", ".join(states)}</{tag}>' if states else ""


def clinic_button(seller_slug, label, small="Our clinic page", plan=None, paid_ok=True, in_table=False):
    """A clinic's one action (Home v2, 3 Nov 2026), on clinic_row_act's rule (owner answer Q1 a and decision C8, 3 Nov
    2026): btn-action "Visit <Name> ..." through /out/<seller>/ with "Paid link" under it only when the data carries the
    clinic's paid link (`paid_url` on the plan row, else on its profile; none yet; site.paid_links applies the paid link
    rule, pages.md, Buttons, and an FDA letter alone does not block it, owner decision 4 Nov 2026); else
    btn-wait `label` to our page on the clinic with `small` under it; "" when we have no page on the clinic."""
    r = PROFILES.get(seller_slug)
    if not r:
        return ""
    paid = (plan or {}).get("paid_url") or r.get("paid_url")
    if paid_ok and paid:
        tail = label.split(" · ", 1)[1] if " · " in label else ""
        return (f'<span class="pick-act"><a class="btn btn-action btn-sm" href="{paid_href(seller_slug, paid)}"{paid_ev(seller_slug, paid)} rel="sponsored">'
                f'Visit {seller_base(r["seller_name"])}{" · " + tail if tail else ""}'
                + ('<span class="paid">Paid link</span></a></span>' if in_table else '</a><span class="paid">Paid link</span></span>'))
    return (f'<span class="pick-act"><a class="btn btn-wait btn-sm" href="/sellers/{seller_slug}/"{plans_ev(seller_slug, plan)}>{label}</a>'
            f'{"" if in_table else f"""<span class="paid">{small}</span>"""}</span>')


def clinic_link(seller_slug, name, inline=False):
    """A clinic's name as a link to its page on our site when it has one, else plain text; never the clinic's own site.
    `inline` for a name inside a line of text (no name style)."""
    if seller_slug in PROFILES:
        return f'<a href="/sellers/{seller_slug}/">{name}</a>' if inline else f'<a class="name" href="/sellers/{seller_slug}/">{name}</a>'
    return name if inline else f'<span class="name">{name}</span>'



def clean(t):
    """Sellers' product names as text the site may show: no em or en dashes, single spaces."""
    return " ".join(str(t).replace("\u2014", "-").replace("\u2013", "-").split())


def seller_name(r):
    return seller_base(clean(r["seller_name"]))  # never a legal name in brackets, whatever the data holds


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


# Cosmetic product forms (peptide-data products.product_form): a cosmetic option's window lists only these, a research-use
# option's window never does (owner UX audit, 3 Nov 2026: the GHK-Cu serum row opened injectable vials). "topical" counts
# too (owner answer, 3 Nov 2026); tools/pull_data.py keeps the same list.
COSMETIC_FORMS = ("cream", "serum", "lotion", "gel", "topical")
is_cosmetic = lambda p: p["status"].startswith("Cosmetic")


COSMETIC_KINDS = ("cosmetic", "scalp")
SCALP_WORDS = re.compile(r"\b(?:hair|scalp)\b", re.I)


def form_ok(r, kind):
    """kind None: every listing; "cosmetic": cosmetic forms only; "scalp": cosmetic forms whose name says hair or scalp (data
    agent's task 33: a body lotion or a skin cream is not a scalp serum); "research": every listing not of a cosmetic form."""
    if kind is None:
        return True
    if kind == "scalp":
        return r.get("form") in COSMETIC_FORMS and bool(SCALP_WORDS.search(r.get("product_name") or ""))
    return (r.get("form") in COSMETIC_FORMS) == (kind in COSMETIC_KINDS)


def vial_ppm(rows):
    """The prices per mg a research-use "from $X/mg" may use: vials only (site.products.form = 'vial'), inside the /compare/
    band; powders and listings with no form do not count (data agent's task 33, 7 Nov 2026)."""
    return [r["price_per_mg"] for r in rows if r.get("form") == "vial" and r.get("price_per_mg") is not None
            and PPM_LOW <= r["price_per_mg"] <= PPM_HIGH]


def seller_rows(slug, kind=None):
    """The listings for one substance, one per seller (its cheapest by price per mg, blends and unknown amounts last),
    of one kind (form_ok). The rows are sorted by the seller's score, high first, then by how many products it lists,
    more first, then by name (owner, 2 Nov 2026); a seller without a score goes last."""
    key = lambda r: (r.get("price_per_mg") is None, r.get("price_per_mg") or 0, r.get("price_usd") or 0, r["seller_slug"])
    best = {}
    for r in sorted((r for r in PRODUCTS if r["substance_slug"] == slug and r["seller_slug"] not in CLINIC_PROFILES
                     and form_ok(r, kind)), key=key):
        best.setdefault(r["seller_slug"], r)
    def order(r):
        s = SELLERS.get(r["seller_slug"], {})
        return (-(s.get("score") if s.get("score") is not None else -1), -(s.get("product_count") or 0),
                clean(s.get("seller_name") or r["seller_name"]).lower())
    return sorted(best.values(), key=order)


# The seller score (pages.md, Seller window, owner 2 Nov 2026): five yes/no checks from site.sellers, in this order, with
# the short name each mark carries. Facts we hold about the seller, never a safety or quality grade.
SCORE_CHECKS = [("score_lab_testing", "Lab reports"), ("score_no_fda_letter", "No FDA letter"),
                ("score_registered_company", "Found in a state registry"), ("score_legal_pages", "Legal pages"),
                ("score_fresh_prices", "Fresh prices")]
# Online clinics are scored out of 4 (owner decision C9, 3 Nov 2026; pages.md, Seller): they publish no lab reports, so
# the lab check is never counted for a clinic. A score is never compared across the two kinds.
CLINIC_RULE = ("Online clinics prescribe and ship medicines; they publish no lab reports, so a clinic is checked on four facts, "
               "not five: no FDA warning letter, registered company, legal pages, fresh prices. A shop is checked on five. "
               "A score is never compared across the two kinds.")


def seller_checks(r):
    """The checks this seller is scored on: a clinic's four, a shop's five."""
    return SCORE_CHECKS[1:] if r["seller_slug"] in CLINIC_PROFILES else SCORE_CHECKS


def score_of(r):
    """A clinic's score: the count of its four met checks, from the booleans (the lab check never counts). A shop's: `score`."""
    return sum(bool(r.get(k)) for k, _ in seller_checks(r)) if r["seller_slug"] in CLINIC_PROFILES else r.get("score")


def out_of(r):
    return len(seller_checks(r))


def score_line(r):
    """"N of 5 checks" with the five checks as small marks in one line: met chip-ok, not met chip-neutral with a dashed
    ink-muted border, so the state never rests on colour alone (owner answer Q1 a, 2 Nov 2026; it is also spoken).
    Nothing when the seller has no score yet."""
    s = SELLERS.get(r["seller_slug"], {})
    if s.get("score") is None:
        return ""
    marks = "".join(f'<span class="chip chip-{"ok" if s.get(k) else "neutral"} mark-{"yes" if s.get(k) else "no"}">'
                    f'<span class="vh">{t}: {"yes" if s.get(k) else "no"}</span><span aria-hidden="true">{t}</span></span>' for k, t in SCORE_CHECKS)
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


def seller_table(slug, kind=None):
    """One substance's sellers as a table, its source lines and its newest last_seen. No link to a seller."""
    rows = seller_rows(slug, kind)
    newest = max((r["last_seen"] for r in rows if r.get("last_seen")), default="")
    scored = max((SELLERS.get(r["seller_slug"], {}).get("score_checked_on") or "" for r in rows), default="")
    trs, src = [], []
    for r in rows:
        name = clean(r["product_name"])
        variant = clean(r["variant_title"]) if r.get("variant_title") and r["variant_title"] != "Default Title" else ""
        if variant and variant.lower() not in name.lower():
            name += f", {variant}"
        size = f'{r["amount_mg"]:g} mg' if r.get("amount_mg") else "size unknown"
        if kind in COSMETIC_KINDS and r.get("form"):  # the form word per row in a cosmetic window ("Serum", "Cream", "Topical")
            size = f'{r["form"].capitalize()} · {size}'
        price = money(r["price_usd"]) if r.get("price_usd") is not None else "unknown"
        ppm = (f'{per_mg(r["price_per_mg"])}/mg' if r.get("price_per_mg") is not None else "blend" if r.get("is_blend") else "unknown")
        seller = seller_base(clean(SELLERS.get(r["seller_slug"], {}).get("seller_name") or r["seller_name"]))
        # the name opens our page on the seller when it has one (owner task 2 Nov 2026); never the seller's own site
        name_html = (f'<a class="name" href="/sellers/{r["seller_slug"]}/">{seller}</a>' if r["seller_slug"] in PROFILES
                     else f'<span class="name">{seller}</span>')
        trs.append(f'<tr data-seller="{r["seller_slug"]}" data-form="{escape(r.get("form") or "")}"><td>{name_html}</td><td data-l="Product">{name}<span class="sub">{size}</span></td>'
                   f'<td data-l="Price"><span class="num">{price}</span></td>'
                   + ("" if kind in COSMETIC_KINDS else f'<td data-l="Per mg"><span class="num">{ppm}</span></td>') +
                   f'<td class="checks">{score_line(r)}{check_chips(r)}{seller_closed_chip(r["seller_slug"])}</td></tr>')
        seen = r.get("price_observed_at") or r.get("last_seen")
        src.append(f'<li>{seller}, {name}{", " + nice_date(seen) if seen else ""}: {r["product_url"]}</li>')
    per_mg_th = "" if kind in COSMETIC_KINDS else '<th scope="col">Per mg</th>'  # a cream has no price per mg
    table = (f'<div class="tbl-wrap"><table class="tbl"><thead><tr><th scope="col">Seller</th><th scope="col">Product</th>'
             f'<th scope="col">Price</th>{per_mg_th}<th scope="col">Background check</th></tr></thead>'
             f'<tbody>{"".join(trs)}</tbody></table></div>')
    return table, src, newest, scored


def subs_of(p):
    """An option's substances for the seller window: its `substance`, or its `substances` list (a row that stands for
    several research-use peptides, e.g. "Injectable peptides sold for hair"; owner, 1 Nov 2026)."""
    return [p["substance"]] if p.get("substance") else list(p.get("substances") or [])


def window_kind(p):
    """"scalp" for a cosmetic option on the hair goal (its window lists scalp products only), "cosmetic" for another
    cosmetic option, else "research"."""
    return ("scalp" if id(p) in SCALP_OPTIONS else "cosmetic") if is_cosmetic(p) else "research"


def window_key(p):
    kind = window_kind(p)
    return {"scalp": "scalp-", "cosmetic": "cosmetics-"}.get(kind, "sellers-") + "-".join(s for s in subs_of(p) if seller_rows(s, kind))


def window_who(p):
    """Who sells in a window, from its listings' sellers (owner UX audit A18, 3 Nov 2026: NAD+ listings come from clinics, so
    the window may not say "Research-use sellers"): cosmetic listings "Cosmetic shops"; all research-use shops "Research-use
    sellers"; all clinics or pharmacies "Clinics and pharmacies"; a mix "Sellers"."""
    kind = window_kind(p)
    if kind in COSMETIC_KINDS:
        return "Cosmetic shops"
    kinds = {(SELLERS.get(r["seller_slug"]) or PROFILES.get(r["seller_slug"]) or {}).get("seller_kind") or ""
             for s in subs_of(p) for r in seller_rows(s, kind)}
    if kinds and all(k == "S1_RUO" for k in kinds):
        return "Research-use sellers"
    if kinds and all(any(w in k for w in ("CLINIC", "TELEHEALTH", "PHARMACY")) for k in kinds):
        return "Clinics and pharmacies"
    return "Sellers" if kinds - {""} else "Research-use sellers"


def seller_window(p):
    """One seller window for an option row (a dialog; a plain section with JavaScript off). One substance: its table
    under the substance name. Several: the option's name as the heading and one table per substance under the
    substance name as a sub-heading. No Visit, no link to a seller."""
    kind = window_kind(p)
    subs = [s for s in subs_of(p) if seller_rows(s, kind)]
    key = window_key(p)
    parts, src, newest, scored = [], [], "", ""
    for s in subs:
        table, lines, seen, sc = seller_table(s, kind)
        parts.append((f'<h3 class="dlg-sub">{substance_name(s)}</h3>' if len(subs) > 1 else "") + table)
        src += lines
        newest, scored = max(newest, seen), max(scored, sc)
    title = substance_name(subs[0]) if p.get("substance") else p["name"]
    checked = f" Prices checked {nice_date(newest)}." if newest else ""
    return f"""<dialog class="sellers-dlg" id="{key}" aria-labelledby="{key}-h"><div class="dlg-in">
  <div class="dlg-hd"><h2 id="{key}-h">{title}</h2><form method="dialog"><button class="btn btn-line btn-sm" type="submit">Close</button></form></div>
  <p class="dlg-lede">{window_who(p)}, with our checks.{checked}</p>
  {"".join(parts)}
  {"" if kind in COSMETIC_KINDS else '<p class="dlg-foot">Price per mg is price divided by the stated amount; blends have no per-mg price.</p>'}
  {f'<p class="dlg-foot dlg-score">Checks are facts we hold about the seller, not a safety or quality grade. Checked {nice_date(scored)}.</p>' if scored else ""}
  <ol class="dlg-src">{"".join(src)}</ol>
</div></dialog>"""


def approved_row(p):
    """An FDA-approved option (hand status or database status). Its row gets no seller window: we do not send people
    from an approved medicine to research-use sellers (owner, 31 Oct 2026)."""
    s = db_status(p["substance"]) if p.get("substance") else None
    return p["status"].startswith("FDA approved") or bool(s and s["label"] == "FDA approved")


def has_window(p):
    return not approved_row(p) and any(seller_rows(s, window_kind(p)) for s in subs_of(p))


def how_line(p):
    """The option's "how you get it" line, true to its window: a research-use row whose window lists shops but whose
    line names none (sermorelin: "Prescription through clinics.") says where the window's listings come from, and
    whether any clinic plan in our data carries the substance (owner UX audit, 3 Nov 2026)."""
    if has_window(p) and window_kind(p) == "research" and not re.search(r"shop|do not link", p["how"], re.I):
        clinics = any(r["substance_slug"] in subs_of(p) for r in PLANS)
        return "Research-use shops, with our checks." + (" Online clinics also prescribe it." if clinics else "")
    return p["how"]


# A row whose data has no listing says so where the button would be, by its kind (owner, 4 Nov 2026), never an empty space.
NO_LISTING_TEXTS = {"otc": "Any pharmacy, no prescription", "rx": "On prescription; no clinic prices yet",
                    "cosmetic": "Sold in creams and serums; no prices checked", "research": "No listings yet"}


def no_listing_text(p):
    if is_cosmetic(p):
        return NO_LISTING_TEXTS["cosmetic"]
    if needs_rx(p) is False:
        return NO_LISTING_TEXTS["otc"]
    return NO_LISTING_TEXTS["rx"] if approved_row(p) or p.get("plan_kind") == "compounded" else NO_LISTING_TEXTS["research"]


# The substance page's line for a cosmetic with no listing (unchanged by the option rows' rule).
COSMETIC_LATER = "Sold as a cosmetic; no prices checked."


# One window per distinct set of substances (two rows for the same substance share it).
# Home loads them on demand from /windows/<key>.json (sellers_button, lazy); goal pages keep their own inline.
SELLER_WINDOWS = {window_key(p): seller_window(p) for g in ALL_GOALS for p in g["peptides"] if has_window(p)}


def option_plans(g, p):
    """The rows of an option's clinic window (pages.md, Clinic window; owner decision 4 Nov 2026): every priced plan of the
    option's substance at any clinic, brand and compounded, leaving out a brand approved for another use on this goal
    (Ozempic on weight loss); the compounded row, the compounded plans of the goal's approved substances. A research-use or
    cosmetic row has none: its window lists shops, and a window never mixes the two."""
    priced = [r for r in PLANS if r.get("price_monthly") is not None]
    if p.get("plan_kind") == "compounded":
        subs = compounded_subs(g, p)
        return [r for r in priced if r["substance_slug"] in subs and r.get("product_kind") == "compounded"]
    if not (p.get("substance") and approved_row(p)):
        return []
    return [r for r in priced if row_fits(p, r) and not other_use(g, r) and plan_fits(p, r) and form_fits(p, r, strict=False)]


def clinic_key(g, p):
    return f'clinics-{g["slug"]}-{"compounded" if p.get("plan_kind") == "compounded" else p["substance"]}'


def clinic_open(g, p, rp=None, low=None):
    """The option's button (pages.md, Clinic window): "Buy from $X/mo · N clinics", opening the window from /windows/<key>.json,
    N the clinics in the window, $X the row's own plan (a row's price is its brand plan; a compounded plan's price never stands
    on an FDA-approved row), `low` for a card that names another plan. Without JavaScript it opens the goal page's clinic table,
    or the plan's clinic page on a goal without one. "" for an option with no clinic plan."""
    rows = option_plans(g, p)
    if not rows:
        return ""
    plan = low or rp or min(rows, key=lambda r: (float(r["price_monthly"]), r["seller_name"]))
    otc = needs_rx(p) is False
    noun = "seller" if otc else "clinic"
    n = len({r["seller_slug"] for r in rows})
    key = clinic_key(g, p)
    href = f'/{g["slug"]}/#clinics' if (g.get("clinic_plans") or g.get("clinic_table")) and g.get("page") else f'/sellers/{plan["seller_slug"]}/'
    small = '<span class="paid">Pharmacy, no prescription</span>' if otc else ""
    return (f'<span class="pick-act"><a class="btn btn-wait btn-sm btn-cta sellers-open" href="{href}" data-dlg="{key}" data-src="/windows/{key}.json"{ev("prices_window_open", substance="compounded" if p.get("plan_kind") == "compounded" else p.get("substance"), window_kind="clinic", rows=len(rows))}>'
            f'Buy from {usd(plan["price_monthly"])}/mo · {plural(n, noun)}</a>{small}</span>')


def clinic_window(g, p):
    """One option's clinic window (pages.md, Clinic window): the shop window's part with every clinic that has a plan for the
    option, brand plans first, then compounded, each cheapest first. The clinic's name opens our page on it; its one action is
    btn-wait "See plans" until the data carries its paid link (clinic_row_act), and only then btn-action "Visit <Name>"."""
    # what is not compounded first (brand, generic and other), so the first row is the button's price; each cheapest first
    rows = sorted(option_plans(g, p), key=lambda r: (r.get("product_kind") == "compounded", clinic_order(r)))
    key, named, trs = clinic_key(g, p), set(), []
    otc = needs_rx(p) is False
    for r in rows:
        fee = r.get("membership_fee_monthly")
        prof = PROFILES.get(r["seller_slug"], {})
        base = seller_base(r["seller_name"])
        checks = f'{score_of(prof) or 0} of {out_of(prof)}' if prof else "not checked"
        trs.append(f'<tr{state_attrs(r["seller_slug"])}><td><span class="cell-pic">{parts.tile(r["seller_slug"], base, 28, seller=prof)}{clinic_link(r["seller_slug"], base)}</span>{not_in_line(r["seller_slug"])}</td>'
                   f'<td data-l="Plan"><span class="cell-pic">{parts.plan_picture(r)}<span>{explain_brand(r["plan_name"], named)}</span></span></td>'
                   f'<td data-l="What it is">{plan_chip(g, r)}</td>'
                   f'<td data-l="Form">{plan_form_word(r)}</td>'
                   f'<td data-l="Per month"><span class="num">{usd(r["price_monthly"])}</span>{plan_letter(r)}{seller_closed_chip(r["seller_slug"])}</td>'
                   f'<td data-l="Care fee">{"not known" if fee is None else "none" if float(fee) == 0 else usd(fee) + "/mo, included"}</td>'
                   f'<td data-l="Checks">{checks}</td>'
                   f'<td class="act">{clinic_row_act(r)}</td></tr>')
    newest = max(r["last_seen"] for r in rows)
    who = "Sellers" if otc else "Clinics"
    return f"""<dialog class="sellers-dlg clinic-dlg" id="{key}" aria-labelledby="{key}-h"><div class="dlg-in" data-state-root>
  <div class="dlg-hd"><h2 id="{key}-h">{p["name"]}</h2><form method="dialog"><button class="btn btn-line btn-sm" type="submit">Close</button></form></div>
  <p class="dlg-lede">{who} with plans, prices checked {nice_date(newest)}.</p>
  {state_filter(who.lower())}{STATE_N}
  <div class="tbl-wrap"><table class="tbl tbl-cards tbl-compact tbl-window"><thead><tr><th scope="col">{who[:-1]}</th><th scope="col">Plan</th><th scope="col">What it is</th><th scope="col">Form</th><th scope="col">Per month</th><th scope="col">Care fee</th><th scope="col">Checks</th><th scope="col"><span class="vh">Our page</span></th></tr></thead><tbody>{"".join(trs)}</tbody></table></div>
  <p class="dlg-foot">Prices are the clinics' published monthly prices on {nice_date(newest)}. A clinic with an FDA warning letter is still listed; the letter is public record.</p>
</div></dialog>"""


def option_picture(p, rp):
    """A row's drawing (pages.md, Pictures and the clinic window): the compounded row, a cosmetic and a research-use row their
    own; an approved option, the form its own lines name (a row says what it is), else the form of the row's plan."""
    if p.get("plan_kind") == "compounded":
        return parts.thumb("vial-compounded")
    if is_cosmetic(p):
        return parts.thumb("serum-dropper")
    if not approved_row(p):
        return parts.thumb("vial-research")
    if p.get("drawing"):  # the form its own lines do not name (data/site.json, with its source)
        return parts.thumb(p["drawing"])
    key = parts.form_drawing(" ".join((p["name"], p.get("plain", ""), p.get("how", ""))))
    return parts.thumb(key) if key else parts.plan_picture(rp) if rp else parts.thumb("")


def sellers_button(p, lazy=False, label=None, kind="btn-line"):
    """"Prices at N shops" on a research-use option row with listings, N the distinct sellers across its substances;
    a link to the window without JS. FDA-approved rows never get it. lazy (Home): the window is not in the page; the
    script loads it from /windows/<key>.json on the first click, and without JS the button opens the substance page's
    shop table (owner UX audit, 3 Nov 2026: every window inline made Home about 148 KB)."""
    if not has_window(p):
        return ""
    n = len({r["seller_slug"] for s in subs_of(p) for r in seller_rows(s, window_kind(p))})
    key = window_key(p)
    kind_w = window_kind(p)
    subs = [s for s in subs_of(p) if seller_rows(s, kind_w)]
    opens = ev("prices_window_open", substance=subs[0], window_kind=kind_w, rows=sum(len(seller_rows(s, kind_w)) for s in subs))
    label = label or f'Prices at {n} shop{"s" if n != 1 else ""}'
    if lazy:
        first = next(s for s in subs_of(p) if seller_rows(s, window_kind(p)))
        href = f"/peptides/{first}/#sold" if first in PEPTIDE_SLUGS else "/sellers/"
        return f'<a class="btn {kind} btn-sm btn-cta sellers-open" href="{href}" data-dlg="{key}" data-src="/windows/{key}.json"{opens}>{label}</a>'
    return f'<a class="btn {kind} btn-sm btn-cta sellers-open" href="#{key}" data-dlg="{key}"{opens}>{label}</a>'


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


RX_LINE = {True: " Needs a prescription.", False: " No prescription needed.", None: ""}


def cosmetic_word(p):
    """"serum" when every listing in a cosmetic window is a serum, else "product" (owner task 3 Nov 2026, the 390px walkthrough:
    "Compare 8 serums" opened creams and lotions)."""
    rows = [r for s in subs_of(p) for r in seller_rows(s, window_kind(p))]
    return "serum" if rows and all("serum" in clean(r.get("product_name") or "").lower() for r in rows) else "product"


def window_low(p):
    """(lowest price, shops) in an option's window: the lowest price per mg inside the /compare/ band for research-use
    listings, the lowest price for cosmetic ones; (None, n) without a price."""
    kind = window_kind(p)
    rows = [r for s in subs_of(p) for r in seller_rows(s, kind)]
    n = len({r["seller_slug"] for r in rows})
    if kind in COSMETIC_KINDS:
        vals = [r["price_usd"] for r in rows if r.get("price_usd") is not None]
    else:
        vals = vial_ppm(r for s in subs_of(p) for r in PRODUCTS if r["substance_slug"] == s and r["seller_slug"] not in CLINIC_PROFILES)
    return (min(vals) if vals else None), n


def plan_clinics(g, p, rp):
    """How many clinics have a plan like the row's: the same substances, compounded or not as the row's plan."""
    comp = rp.get("product_kind") == "compounded"
    subs = compounded_subs(g, p) if p.get("plan_kind") == "compounded" else {rp["substance_slug"]}
    return len({r["seller_slug"] for r in PLANS if r["substance_slug"] in subs and r.get("price_monthly") is not None
                and (r.get("product_kind") == "compounded") == comp})


def opt_line(g, p, rp, tag="p"):
    """The opened row's first line: the option's `plain` sentence, with the footnote of the row's plan. It never repeats the price:
    the button carries it (opt_action), and a row with no button has it in its CTA text."""
    sup = ""
    if rp:
        sid, n = plan_ref(g, rp)
        sup = f'<sup><a class="ref" href="#{sid}" aria-label="Source {n}">{n}</a></sup>'
    text = p.get("plain", "")
    return f'<{tag} class="opt-plain">{text}{sup}</{tag}>' if text else ""


def no_listing_cta(p, pad):
    """A row with no button: its text, with the row's price and footnote when it has one, so no row loses it (option rows v4)."""
    text = no_listing_text(p)
    if not pad:
        return text
    price = re.search(r"from (\$[\d.,]+/mo)", pad).group(1)
    sup = re.search(r"<sup>.*</sup>", pad).group(0)
    return f"From {price} at any pharmacy, no prescription{sup}" if needs_rx(p) is False else f"From {price}. {text}{sup}"


def opt_action(g, p, rp, lazy, pad=""):
    """The row's one button, one width on every row (pages.md, Home, Option rows): a row with clinic plans, "Buy from $X/mo · N
    clinics", opening the clinic window (clinic_open); a research-use row, "Prices at N shops" ("Our checks, no shop links"); a
    cosmetic row, "Compare N products" (its window); a row with no listing, its text by kind (no_listing_text)."""
    btn = clinic_open(g, p, rp)
    if btn:
        return btn
    if has_window(p) and window_kind(p) in COSMETIC_KINDS:
        low, n = window_low(p)
        label = f"From {money(low)} · {plural(n, cosmetic_word(p))}" if low is not None else f"Compare {plural(n, cosmetic_word(p))}"
        return f'<span class="pick-act">{sellers_button(p, lazy, label, "btn-wait")}</span>'
    if has_window(p):
        low, n = window_low(p)
        label = f'From {per_mg(low)}/mg · {plural(n, "shop")}' if low is not None else None
        return f'<span class="pick-act">{sellers_button(p, lazy, label, "btn-wait")}<span class="paid">Our checks, no shop links</span></span>'
    return f'<span class="pick-act"><span class="paid no-link">{no_listing_cta(p, pad)}</span></span>'


# "We do not link to them" and its variants (pages.md, Home): said once on Home, in the label legend.
NO_LINK_SAID = re.compile(r"\s*[Ww]e (?:do not|don't|never) link(?: to (?:them|shops|these shops|it))?\.?")


def unsaid(t):
    """A line with its "we do not link" sentence taken out ("Research-use shops; we do not link to them." ->
    "Research-use shops."); a line that said nothing else reads "Research-use shops."."""
    out = NO_LINK_SAID.sub("", t).strip().rstrip(";,") 
    return (out + ("" if out.endswith(".") else ".")) if out else "Research-use shops."


def opt_facts(g, p):
    """The facts the goal page's old "Every option, side by side" table showed that the row does not (owner task 3 Nov
    2026): from the goal's hand-checked `options` entry for this row, its evidence chip, and whether it needs a prescription."""
    first = p["name"].split()[0].lower()
    o = next((o for o in g.get("options") or [] if first in o["name"].lower()), None)
    if not o:
        return ""
    rx = {True: "Needs a prescription", False: "No prescription needed", None: ""}[needs_rx(p)]
    return (f'<p class="opt-facts">Evidence in people: <span class="chip chip-{o["evidence_chip"]}">{o["evidence"]}</span>'
            f'{" · " + rx if rx else ""}</p>')


def opt_head(p):
    """The collapsed row (pages/parts.md, Option rows): "<name> · <what it does>", then the status chip with the prescription fact."""
    return (f'<span class="opt-one"><span class="name">{p["name"]}</span> · {p["line_one"]}</span>'
            f'<span class="opt-two">{status_chip(p)}<span class="opt-rx">{p["rx_word"]}</span></span>')


def option_rows(g, lazy=False):
    """One goal's step 2 option rows (pages.md, Home, Option rows; also the goal pages): collapsed, the name and chips,
    the `plain` sentence and the price in bold, and one button (opt_action); opened, the does, status and how lines with
    their footnotes. lazy (Home): the windows load on demand, and the rows say "we do not link" nowhere (the label legend
    says it once)."""
    slug = g["slug"]
    rows = []
    for p in g["peptides"]:
        pad = opt_price(p, slug)
        rp = row_plan(g, p)
        cost = price_sentence(p, pad) + (" " + plan_line(g, "plan-in", rp).replace(")<sup>", ").<sup>", 1) if rp else "")
        how, status = how_line(p), plain_status(p, drop_price=bool(pad))
        if lazy:
            how, status = unsaid(how), (unsaid(status) if NO_LINK_SAID.search(status) else status)
        # one status chip next to the name; no seller fact on the row (pages/parts.md, Option rows, 5 Nov 2026)
        rows.append(f'<li class="opt"><details class="opt-more"><summary class="opt-sum">{option_picture(p, rp)}<span class="opt-m" aria-hidden="true"></span>{opt_head(p)}</summary>'
                    f'<div class="opt-body">{opt_line(g, p, rp, "p")}<p class="opt-does">{p["does"]}{refs(p, slug, price=not pad)}</p>'
                    f'<p class="opt-status">{status}</p><p class="opt-how">{how}{cost}</p>{"" if lazy else opt_facts(g, p)}</div></details>{opt_action(g, p, rp, lazy, pad)}</li>')
    return rows


def approved_instead(g):
    """Under a goal's options when none of them has a clinic or a cosmetic button (pages.md, Home, Option rows): one line
    to the goal's guide (`approved_instead_guide`), never an invented clinic row."""
    gd = next((x for x in guides.GUIDES if x["slug"] == g.get("approved_instead_guide")), None)
    linkable = any(row_plan(g, p) and p.get("substance") or (has_window(p) and window_kind(p) in COSMETIC_KINDS) for p in g["peptides"])
    return f'<p class="opt-instead">What is approved instead: <a href="/learn/{gd["slug"]}/">{gd["title"]}</a></p>' if gd and not linkable else ""


GOAL_PANELS = {}  # goal slug -> its step 2 panel, for /windows/goal-<slug>.json


def rail():
    """The flow (design book, pages.md, Home): the goal rows, then per goal the option list, where the top pick's row
    carries the Visit button. Every goal's options are in the page; only the first goal's show until another is chosen."""
    chips, compare = [], []
    for i, g in enumerate(CHOOSER_GOALS):
        slug, hide = g["slug"], "" if i == 0 else " hidden"
        chips.append(f'<button type="button" class="goal-item" data-goal="{slug}"{ev("goal_pick", goal=slug)} aria-pressed="{"true" if i == 0 else "false"}" '
                     f'aria-controls="opts-{slug}"><span>{g["label"]}</span><span class="small">{len(g["peptides"])} options</span></button>')
        rows = option_rows(g, lazy=True)
        link = (f'<a class="btn btn-ink" href="/{slug}/">Compare {g["short"].lower()} options</a>' if g.get("page") else
                '<p class="small">Full comparison for this goal is not published yet. The legal status above is current as of ' + CHECKED + '.</p>')
        inner = (f'<p class="goal-for">{g["for"]}</p><p class="goal-intro">{g["intro"]}</p>'
                 f'<ul class="opts">{"".join(rows)}</ul>{approved_instead(g)}{link}')
        # Home lists no sources: a footnote opens its line on /sources/, which carries the same ids (owner answer Q3 a, 3 Nov 2026)
        inner = inner.replace('href="#src-', 'href="/sources/#src-')
        # Only the first goal's options are in the page; the others load from /windows/goal-<slug>.json when chosen
        # (Home under 60 KB, Home v2, 3 Nov 2026). Without JavaScript only the first goal shows, as before.
        if i:
            GOAL_PANELS[slug] = inner
        src = f' data-src="/windows/goal-{slug}.json"' if i else ""
        compare.append(f'<div class="step-panel" id="opts-{slug}" data-goal="{slug}" data-title="{g["panel_title"]}"'
                       f'{src}{hide}>{"" if i else inner}</div>')
    # The chosen goal's panel title follows the step name in the step 2 heading (ODOBRENO SEO 30 Oct 2026, copy doc
    # section 2); the page carries the first goal's, the goal switch puts in the next one.
    return "".join(chips), "".join(compare), f'<span class="goal-t">: {ALL_GOALS[0]["panel_title"]}</span>'


def renumber_sources():
    """The price, option and plan sources numbered in the order the option rows link them, goal by goal (on /hair/:
    finasteride's price 8 and clinic plan 9, then minoxidil's own source 10; owner UX audit, 3 Nov 2026), so footnotes
    count up down the page. A source no row links keeps its place after them."""
    global SOURCES_HOME
    lis = {m.group(2): m.group(1) for m in re.finditer(r'(<li id="(src-(?:price|opt|plan)-[^"]+)">.*?</li>)', SOURCES_HOME)}
    seen = list(dict.fromkeys(s for g in ALL_GOALS for s in re.findall(r'href="#(src-(?:price|opt|plan)-[^"]+)"', "".join(option_rows(g)))))
    order = [s for s in seen if s in lis] + [s for s in lis if s not in seen]
    num = {s: len(LEGAL["sources"]) + i + 1 for i, s in enumerate(order)}
    PRICE_REF.update({k: num[f"src-price-{k}"] for k in PRICE_REF})
    OPT_REF.update({k: (num[f"src-{a}"], a) for k, (_, a) in OPT_REF.items()})
    PLAN_REF.update({k: num[f"src-plan-{k}"] for k in PLAN_REF})
    EXTRA_REF.update({k: num[f"src-plan-{k}"] for k in EXTRA_REF})
    SOURCES_HOME = SOURCES_HOME.split('<li id="src-price-', 1)[0] + "".join(lis[s] for s in order)



# Peptide pages (pages.md, Peptide; owner task 2 Nov 2026): one page per substance with a status, from the database or
# from its own hand-written "Is it legal today?" row; `no_page` for a medicine that is not a peptide (sildenafil). Defined here because the legal tables link each name to its page.
def hand_legal(slug):
    """The hand-written legal row that carries the substance and a status (not a db_only row), or None."""
    return next((r for r in LEGAL["rows"] if slug in (r.get("substances") or []) and r.get("status") and not r.get("db_only")), None)


PEPTIDE_SLUGS = sorted({r["substance_slug"] for r in LEGAL_DB or [] if db_status(r["substance_slug"])}
                       | {s for r in LEGAL["rows"] for s in r.get("substances") or [] if not db_status(s) and hand_legal(s) and not r.get("no_page")})


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
    # A substance that is both a drug row and a cosmetic row says which is which (owner UX audit, 3 Nov 2026: two rows
    # both named "GHK-Cu"): the drug row takes its route from the FDA listing ("injection"), the cosmetic row on a page
    # that shows one of its substances names that one "(cream or serum)".
    cosmetic = {x for r in LEGAL["rows"] if r.get("status") == "Cosmetic" and keep(r.get("substances", []))
                for x in r.get("substances", [])}
    route = lambda slug, s: (f' ({"injection" if "inject" in (s.get("listing") or "").lower() else "as a drug"})'
                             if slug in cosmetic else "")

    def hand_name(r):
        mine = [x for x in r.get("substances") or [] if only is not None and x in only]
        if r.get("status") == "Cosmetic" and len(mine) == 1 and len(r["substances"]) > 1:
            return f"{substance_name(mine[0])} (cream or serum)"
        return r["peptide"]
    hand = lambda r: (f'<tr><td>{legal_name(r.get("substances") or [], hand_name(r))}</td><td><span class="chip chip-{r["chip"]}">{r["status"]}</span></td>'
                      f'<td>{r["note"]} <a class="ref" href="#src-{r["src"]}" aria-label="Source {r["src"]}"><sup>{r["src"]}</sup></a></td></tr>')
    out, seen = [], []
    for r in LEGAL["rows"]:
        if not keep(r.get("substances", [])) or (only is None and r.get("goal_only")):
            continue  # a goal_only row and its source live on that goal's page, not in Home's table
        if only is not None and r.get("checked"):
            seen.append(r["checked"])
        found = [db_status(slug) for slug in r.get("substances", [])] if LEGAL_DB else []
        if not found or not all(found):
            if not r.get("db_only"):  # a db_only row (finasteride, minoxidil) is shown only from the database
                out.append(hand(r))  # a row switches to the database only when every substance in it has a status there
                if r.get("checked"):  # a hand row checked later than the table (the HHS rows, 7 Nov 2026) dates the stamp
                    seen.append(r["checked"])
            continue
        for slug, s in zip(r["substances"], found):
            if not keep([slug]):
                continue
            seen.append(s["seen"])
            # A row marked note_with_db keeps its hand-written note (e.g. the July 2026 PCAC proposal) as a second sentence.
            n = r.get("note_each", r.get("note", ""))  # the note for one substance when a grouped row splits ("them" -> "it")
            note = (f'. {n[0].upper() + n[1:]}. <a class="ref" href="#src-{r["src"]}" aria-label="Source {r["src"]}">'
                    f'<sup>{r["src"]}</sup></a>') if r.get("note_with_db") else ""
            out.append(f'<tr><td>{legal_name([slug], s["name"] + route(slug, s))}</td><td><span class="chip chip-{s["chip"]}">{s["label"]}</span></td>'
                       f'<td>{s["sentence"]}{" " + r["use"] if r.get("use") else ""} <a class="ref" href="{s["url"]}" rel="nofollow">{source_word(s["url"])}</a>, {nice_date(s["seen"])}{note}{listing_html(s)}</td></tr>')
    # Every other substance with a database status gets its own row (owner, 1 Nov 2026: the table lists every substance
    # the database has a status for, plus the hand rows it lacks), then all rows are sorted by name.
    shown = {slug for r in LEGAL["rows"] for slug in r.get("substances", [])
             if all(db_status(x) for x in r.get("substances", [])) and LEGAL_DB}
    for slug in sorted({r["substance_slug"] for r in LEGAL_DB or []} - shown):
        s = db_status(slug)
        if not s or not keep([slug]):
            continue
        seen.append(s["seen"])
        out.append(f'<tr><td>{legal_name([slug], s["name"] + route(slug, s))}</td><td><span class="chip chip-{s["chip"]}">{s["label"]}</span></td>'
                   f'<td>{s["sentence"]} <a class="ref" href="{s["url"]}" rel="nofollow">{source_word(s["url"])}</a>, {nice_date(s["seen"])}{listing_html(s)}</td></tr>')
    out.sort(key=lambda row: re.sub(r"<[^>]+>", "", row.split("</td>")[0]).strip().lower())
    checked = nice_date(max(seen)) if seen else nice_date(LEGAL["checked"])
    return out, checked


LEGAL_NOTE = ("Approved means the FDA approved a product containing it for a stated use. Not approved means no approved product "
              "exists; buying it for yourself is not a crime in the US, but nobody has checked what is in the vial.")

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
renumber_sources()  # after LETTERS_URL: the option rows' plan lines carry the letter chip

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


# "Maker of an approved drug" (owner UX audit B21, 3 Nov 2026): a letter's company that is the applicant (sponsor) of an
# approved drug in our data, matched on the name's words without "Inc", "LLC", "and Company" and the like.
CO_STOP = {"inc", "llc", "co", "company", "and", "corp", "corporation", "ltd", "limited", "plc", "the", "usa", "us", "a", "s", "as"}
co_words = lambda n: tuple(w for w in re.findall(r"[a-z0-9]+", (n or "").lower()) if w not in CO_STOP)
MAKERS = {co_words(a["sponsor"]) for a in APPROVED_DB if a.get("sponsor")} - {()}
is_maker = lambda company: any(co_words(company)[:len(m)] == m for m in MAKERS)
MAKER_CHIP = ' <span class="chip chip-neutral">Maker of an approved drug</span>'


def letters_all_rows():
    out, more = [], ' class="more"'
    for i, r in enumerate(LETTERS_ALL):
        seller = f'<span class="co-seller">In our database: {escape(seller_name(r))}</span>' if r.get("seller_slug") and r.get("seller_name") else ""
        subj = escape(clean(r["letter_subject"]))
        out.append(
            f'<tr{more if i >= LETTERS_FIRST else ""}{" data-closed" if r["letter_url"] in CLOSED else ""} data-year="{r["letter_date"][:4]}" data-subs="{" ".join(SUBS_OF_LETTER.get(r["letter_url"], []))}"><td class="num">{nice_date(r["letter_date"])}</td>'
            # the subject once, in its own column (owner UX audit A27, 3 Nov 2026: it was repeated in the company cell for
            # phones, and the Office column, always CDER, went); phones stack the row as a card
            f'<td data-l="Company"><span class="name">{escape(clean(r["company_name"]))}</span>{MAKER_CHIP if is_maker(r["company_name"]) else ""}{seller}</td>'
            f'<td class="subj" data-l="Subject">{subj.replace("/", "/<wbr>")}</td>'
            f'<td><a href="{escape(r["letter_url"])}" rel="nofollow">FDA letter</a>{closed_chip(r["letter_url"])}</td></tr>')
    return "".join(out)


LETTERS_YEARS = sorted({r["letter_date"][:4] for r in LETTERS_ALL}, reverse=True)
# The substance filter (pages.md, Letters; owner task 2 Nov 2026): every substance a letter names, most letters first
SUB_NAME = {r["substance_slug"]: clean(r["substance_name"] or r["substance_slug"]) for r in DATA.get("letter_substances") or []}
SUB_COUNTS = sorted(((slug, len(v)) for slug, v in LETTER_SUBS.items()), key=lambda x: (-x[1], SUB_NAME[x[0]].lower()))
SUB_SELECT = ('<div class="legal-filter sub-filter"><label for="letters-sub">Substance</label><select class="input" id="letters-sub" data-filter="substance">'
              '<option value="">Any substance</option>'
              + "".join(f'<option value="{slug}">{escape(SUB_NAME[slug])} ({n})</option>' for slug, n in SUB_COUNTS)
              + "</select></div>") if SUB_COUNTS else ""
YEAR_CHIPS = "".join(
    f'<button type="button" class="year-chip" data-year="{y}" data-filter="year" data-value="{y}" aria-pressed="false">{y} <span>{sum(r["letter_date"][:4] == y for r in LETTERS_ALL)}<span class="vh"> letters</span></span></button>'
    for y in LETTERS_YEARS)
# The "Closed" chip (pages.md, Letters): only when at least one letter on the page has its close-out letter.
N_CLOSED = sum(r["letter_url"] in CLOSED for r in LETTERS_ALL)
CLOSED_CHIP = (f'<div class="year-chips" role="group" aria-labelledby="letters-status"><span id="letters-status">Status</span><button type="button" class="year-chip" id="letters-closed" data-filter="status" data-value="closed" aria-pressed="false">Closed <span>{N_CLOSED}<span class="vh"> letters</span></span></button></div>'
               if N_CLOSED else "")
LETTERS_PAGE_JS = """<script>
(function(){var tb=document.getElementById('letters-table');if(!tb)return;var f=document.querySelector('.letters-filter'),q=document.getElementById('letters-q'),
c=document.getElementById('letters-clear'),m=document.querySelector('.letters-more'),all=document.getElementById('letters-all'),n=document.getElementById('letters-n'),
chips=[].slice.call(document.querySelectorAll('.year-chip[data-year]')),cl=document.getElementById('letters-closed'),rows=[].slice.call(tb.tBodies[0].rows),lim=25,sb=document.getElementById('letters-sub');
var P=new URLSearchParams(location.search);if(sb&&P.get('sub')&&sb.querySelector('option[value="'+P.get('sub')+'"]'))sb.value=P.get('sub');if(P.get('q'))q.value=P.get('q');
function draw(){var s=q.value.trim().toLowerCase(),u=sb?sb.value:'',ys=chips.filter(function(x){return x.getAttribute('aria-pressed')==='true';}).map(function(x){return x.getAttribute('data-year');}),z=!!cl&&cl.getAttribute('aria-pressed')==='true',k=0;
rows.forEach(function(r,i){var hit=(!s||r.cells[1].textContent.toLowerCase().indexOf(s)>=0)&&(!ys.length||ys.indexOf(r.getAttribute('data-year'))>=0)
&&(!u||(' '+r.getAttribute('data-subs')+' ').indexOf(' '+u+' ')>=0)&&(!z||r.hasAttribute('data-closed'));
r.hidden=!hit||(!s&&!u&&!z&&!ys.length&&i>=lim);if(hit)k++;});
if(m)m.hidden=lim>=rows.length||!!s||!!u||z||ys.length>0;n.textContent=(s||u||z||ys.length)?k+' of '+rows.length+' letters match.':'';}
f.hidden=false;if(m)m.hidden=false;q.addEventListener('input',draw);if(sb)sb.addEventListener('change',draw);
(cl?chips.concat(cl):chips).forEach(function(x){x.addEventListener('click',function(){x.setAttribute('aria-pressed',x.getAttribute('aria-pressed')==='true'?'false':'true');draw();});});
c.addEventListener('click',function(){q.value='';if(sb)sb.value='';(cl?chips.concat(cl):chips).forEach(function(x){x.setAttribute('aria-pressed','false');});draw();q.focus();});
if(all)all.addEventListener('click',function(){lim+=25;draw();});draw();})();
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
      <form class="sub-form" action="https://buttondown.com/api/emails/embed-subscribe/{escape(BUTTONDOWN)}" method="post" target="_blank" data-ev="newsletter_submit">
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
            desc += f" In our database: {seller_name(r)}."
        items.append(f"<item><title>{escape(company)}: {escape(subj)}</title><link>{escape(r['letter_url'])}</link>"
                     f"<guid isPermaLink=\"true\">{escape(r['letter_url'])}</guid><pubDate>{rss_date(r['letter_date'])}</pubDate>"
                     f"<description>{escape(desc)}</description></item>")
    built = rss_date(DATA["pulled_at"][:10]) if DATA.get("pulled_at") else rss_date(LETTERS_ALL[0]["letter_date"])
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>'
            f'<title>FDA warning letters to peptide sellers (Peptide Chooser)</title><link>{SITE}/fda-warning-letters/</link>'
            f'<atom:link href="{SITE}{FEED_PATH}" rel="self" type="application/rss+xml"/>'
            '<description>New FDA warning letters to peptide sellers, compounders and online clinics, with a link to each letter on fda.gov.</description>'
            f'<language>en-us</language><lastBuildDate>{built}</lastBuildDate>{"".join(items)}</channel></rss>\n')


def jump_row(links):
    """"Jump to" on a long page (pages.md, Every page, Jump row; owner task 3 Nov 2026, the 390px walkthrough): a row of
    links to the page's own sections, under the H1, on phones only (from 641px it is not drawn)."""
    if not links:
        return ""
    return ('<nav class="jump" aria-label="On this page"><span>Jump to</span>'
            + "".join(f'<a href="{h}">{escape(t)}</a>' for h, t in links) + "</nav>")


LETTERS_PAGE = f"""
<section class="section letters-hd">
  <div class="wrap">
    <h1>FDA warning letters to peptide sellers and online clinics</h1>
    <p class="letters-what">A warning letter is about how a company sold or advertised a product. It does not withdraw any approval and is not a safety finding about an approved medicine. When the FDA verifies the corrections it publishes a close-out letter; we show it next to the letter when one exists.</p>
    {jump_row([("#letters-list", "The letters"), ("#sub-h", "Get new letters by email")] if BUTTONDOWN else [("#letters-list", "The letters")])}
    {author_line(DATA["pulled_at"][:10]) if DATA.get("pulled_at") else ""}
    <p class="letters-stamp"><span class="small">{len(LETTERS_ALL)} letters since {nice_date(DATA["letters_all_oldest"]) if DATA.get("letters_all_oldest") else ""}, newest first. Each links to the letter on fda.gov.</span></p>
    {SUBSCRIBE_BOX}
  </div>
</section>
<section class="band-2" id="letters-list">
  <div class="wrap">
    <div class="letters-filter" hidden>
      <div class="legal-filter"><label for="letters-q">Filter by company</label><input class="input" id="letters-q" type="text" autocomplete="off" data-filter="company" data-value="text"><button type="button" class="btn btn-line btn-sm" id="letters-clear">Clear</button></div>
      {SUB_SELECT}
      <div class="year-chips" role="group" aria-labelledby="letters-years"><span id="letters-years">Year</span>{YEAR_CHIPS}</div>
      {CLOSED_CHIP}
      <p class="small" id="letters-n" aria-live="polite"></p>
    </div>
    <div class="tbl-wrap"><table class="tbl tbl-letters tbl-letters-all tbl-cards" id="letters-table"><caption class="vh">FDA warning letters, newest first</caption>
      <thead><tr><th scope="col">Date</th><th scope="col">Company</th><th scope="col" class="subj">Subject</th><th scope="col">Source</th></tr></thead>
      <tbody>{letters_all_rows()}</tbody>
    </table></div>
    {f'<p class="letters-more" hidden><button type="button" class="btn btn-line" id="letters-all">Show 25 more</button></p>' if len(LETTERS_ALL) > LETTERS_FIRST else ""}
    <p class="small" style="margin-top:16px">Company names are as the FDA lists them. "In our database" names the seller we matched the letter to.</p>
    <p class="letters-formal">A warning letter is the FDA's formal notice that it found what it believes are significant violations of the law; the company is asked to reply within 15 business days. It is public record. <a href="{FDA_ABOUT_LETTERS}" rel="nofollow">What the FDA says about warning letters</a></p>
  </div>
</section>{goals_strip("Compare peptides by goal")}
{LETTERS_PAGE_JS}
""" if LETTERS_ALL else ""
FIGURE = figure_3d()
GOAL_CHIPS, STEP_COMPARE, GOAL_TITLES = rail()
def chip_title(t):
    return f'<span class="chip chip-{t["chip"]}">{t["term"]}</span>' if t.get("chip") else t["term"]


# Each label's title carries the chip the option rows use for that status (`chip` in data/site.json); "Is it safe?" has none.
GLOSSARY = "".join(
    f'<div><dt>{chip_title(t)}</dt><dd>{t["text"]}</dd></div>' for t in DATA["glossary"])

# The seller window (pages.md, Home): with JavaScript the windows hide until "Compare N sellers" opens one as a modal
# dialog (Esc and "Close" are the dialog's own; a click on the dimmed area outside closes it; focus returns to the button).
SELLERS_JS = """<script>
(function(){if(!window.HTMLDialogElement)return;document.documentElement.classList.add('sellers-js');
document.addEventListener('click',function(e){var b=e.target.closest('.sellers-open');if(b){var d=document.getElementById(b.getAttribute('data-dlg'));
if(d){e.preventDefault();d.showModal();return;}var src=b.getAttribute('data-src');if(!src)return;e.preventDefault();
fetch(src).then(function(r){return r.json();}).then(function(j){document.querySelector('.sellers-all').insertAdjacentHTML('beforeend',j.html);
var n=document.getElementById(b.getAttribute('data-dlg'));n.querySelectorAll('tbody > tr').forEach(function(t){t.style.opacity='1';});
if(window.pcState)pcState();n.showModal();}).catch(function(){location.href=b.href;});return;}
var d=e.target.closest('.sellers-dlg');if(d&&e.target===d)d.close();});})();
</script>"""

# The goal switch (design book, pages.md, Home, the three steps): chips and pins are one control. Steps 2 and 3
# cross-fade (GSAP, motion-swap) only while motion is on; otherwise they swap at once. The stamp lands once.
# The figure's zoom (design book, Motion): GSAP moves the whole stage, the sharp close-up and the highlight fade in when it
# lands. They are the same camera, so nothing shifts. Close-ups load on first hover, focus or click. No GSAP or reduced
# motion: it swaps straight to the close-up. No JavaScript: the full figure and the goal list.
FIG_JS = """<script>
window.pcFig=function(box,choose){
var stage=box.querySelector('.fig3d-stage'),label=box.querySelector('.fig3d-label'),back=box.querySelector('.fig3d-back');
var base=box.getAttribute('data-base'),views=JSON.parse(box.getAttribute('data-views')),pins=[].slice.call(box.querySelectorAll('.pin'));
var view=box.querySelector('.fig3d-view'),cur=null,layers={},tween=null,token=0;
var zoomS=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--motion-zoom'))/1000||0.7;
// From 900px a pin is a control of its own. Below that seven do not fit: they are markers, and the whole figure and the goal rows are the targets.
var wide=window.matchMedia('(min-width: 900px)');
function roles(){pins.forEach(function(p){if(wide.matches){p.setAttribute('role','button');p.tabIndex=0;p.removeAttribute('aria-hidden');}else{p.removeAttribute('role');p.removeAttribute('tabindex');p.setAttribute('aria-hidden','true');}});}
roles();if(wide.addEventListener)wide.addEventListener('change',roles);
function rect(k){var z=views[k].z,h=1/z;return {z:z,x:(1-h)/2,y:Math.min(1-h,Math.max(0,views[k].v-h/2))};}
function ensure(k){if(layers[k])return layers[k];var r=rect(k),out=[];
function add(name){var i=new Image();i.alt='';i.className='fig3d-layer';i.style.left=r.x*100+'%';i.style.top=r.y*100+'%';i.style.width=100/r.z+'%';i.style.height=100/r.z+'%';i.src=base+name;stage.insertBefore(i,pins[0]);out.push(i);}
if(r.z>1)add(k+'.webp');add(k+'-glow.webp');layers[k]=out;return out;}
function ready(l){return Promise.all(l.map(function(i){return i.decode?i.decode().catch(function(){}):0;}));}
function move(r,animate,done){if(tween){tween.kill();tween=null;}
var to={xPercent:-r.x*r.z*100,yPercent:-r.y*r.z*100,scale:r.z};
if(animate){to.duration=zoomS;to.ease='power2.out';to.onUpdate=function(){stage.style.setProperty('--s',gsap.getProperty(stage,'scaleX'));};
to.onComplete=function(){stage.style.setProperty('--s',r.z);done();};tween=gsap.to(stage,to);return;}
if(window.gsap)gsap.set(stage,to);else stage.style.transform='translate('+to.xPercent+'%,'+to.yPercent+'%) scale('+r.z+')';
stage.style.setProperty('--s',r.z);done();}
function clear(){Object.keys(layers).forEach(function(k){layers[k].forEach(function(i){i.classList.remove('in');});});label.hidden=true;}
function place(k){var p=box.querySelector('.pin[data-goal="'+k+'"]');label.textContent=p.getAttribute('aria-label');label.hidden=false;label.style.left='0';label.style.top='0';
var b=box.getBoundingClientRect(),q=p.getBoundingClientRect(),x=q.left+q.width/2-b.left,y=q.top+q.height/2-b.top,w=label.offsetWidth,h=label.offsetHeight,g=14,lx,ly=y-h/2;
if(x+g+w<=b.width-4)lx=x+g;else if(x-g-w>=4)lx=x-g-w;else{lx=Math.max(4,Math.min(b.width-w-4,x-w/2));ly=y+g;if(ly+h>back.offsetTop-4)ly=y-g-h;}
label.style.left=lx+'px';label.style.top=Math.max(4,Math.min(b.height-h-4,ly))+'px';}
function go(k){if(cur===k)return;var t=++token,list=ensure(k),anim=!!window.pcMotion;cur=k;clear();box.classList.add('zoomed');view.classList.toggle('near',rect(k).z>1);back.hidden=false;
pins.forEach(function(p){var on=p.getAttribute('data-goal')===k;p.classList.toggle('on',on);p.setAttribute('aria-pressed',on?'true':'false');});
var land=function(){ready(list).then(function(){if(t!==token)return;list.forEach(function(i){i.classList.add('in');});place(k);});};
if(anim)move(rect(k),true,land);else ready(list).then(function(){if(t===token)move(rect(k),false,land);});}
function out(refocus){if(!cur)return;var k=cur;token++;cur=null;clear();box.classList.remove('zoomed');view.classList.remove('near');back.hidden=true;
move({z:1,x:0,y:0},!!window.pcMotion,function(){});
if(refocus){var p=box.querySelector('.pin[data-goal="'+k+'"]');if(p)p.focus();}}
box.addEventListener('click',function(e){
if(e.target.closest('.fig3d-back')){out(true);return;}
var p=e.target.closest('.pin');
if(cur){if(!p)out(false);return;}
var best=null,d=Infinity;pins.forEach(function(x){var q=x.getBoundingClientRect(),n=Math.hypot(e.clientX-q.left-q.width/2,e.clientY-q.top-q.height/2);if(n<d){d=n;best=x;}});
if(best&&d<=Math.max(44,box.offsetHeight*0.2))pinPick(best.getAttribute('data-goal'));});
function pinPick(k){if(window.pcEv)pcEv('goal_pick',{goal:k});choose(k);}
function pre(e){var p=e.target.closest&&e.target.closest('.pin');if(p)ensure(p.getAttribute('data-goal'));}
box.addEventListener('mouseover',pre);box.addEventListener('focusin',pre);
box.addEventListener('keydown',function(e){if((e.key==='Enter'||e.key===' ')&&e.target.classList.contains('pin')){e.preventDefault();pinPick(e.target.getAttribute('data-goal'));}});
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&cur)out(box.contains(document.activeElement));});
return {go:go,out:out,preload:ensure};};
</script>"""


MAP_JS = """<script>
(function(){var root=document.getElementById('goals');if(!root)return;
var chips=[].slice.call(root.querySelectorAll('.goal-item')),cur=chips[0].getAttribute('data-goal');
var figBox=root.querySelector('.fig3d'),fig=figBox&&window.pcFig?pcFig(figBox,act):null;
function act(k){pick(k);if(fig)fig.go(k);}
var swapS=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--motion-swap'))/1000||0.2;
root.addEventListener('animationend',function(e){if(e.target.classList.contains('stamp'))root.classList.add('landed');});
function show(k){var p=root.querySelector('.step-panel[data-goal="'+k+'"][data-src]');
if(p){var src=p.getAttribute('data-src');p.removeAttribute('data-src');fetch(src).then(function(r){return r.json();}).then(function(j){p.innerHTML=j.html;if(cur===k)show(k);})
.catch(function(){location.href='/'+k+'/';});return;}
root.querySelectorAll('.step-panel').forEach(function(x){x.hidden=x.getAttribute('data-goal')!==k;if(!x.hidden)root.querySelector('.goal-t').textContent=': '+x.getAttribute('data-title');});
if(!window.pcMotion)return;var on=root.querySelectorAll('.step-panel[data-goal="'+k+'"]');
gsap.fromTo(on,{opacity:0},{opacity:1,duration:swapS,ease:'power1.out'});
gsap.fromTo(root.querySelectorAll('.step-panel[data-goal="'+k+'"] .opt'),{opacity:0,y:4},{opacity:1,y:0,duration:swapS,ease:'power1.out',stagger:0.04});}
function pick(k){if(k===cur)return;cur=k;
root.querySelectorAll('.goal-item,.pin').forEach(function(x){var on=x.getAttribute('data-goal')===k;
if(x.hasAttribute('aria-pressed'))x.setAttribute('aria-pressed',on?'true':'false');x.classList.toggle('on',on);});
var old=root.querySelectorAll('.step-panel:not([hidden])');
if(window.pcMotion&&old.length){gsap.killTweensOf(old);gsap.to(old,{opacity:0,duration:swapS/2,ease:'power1.in',onComplete:function(){gsap.set(old,{opacity:1});if(cur===k)show(k);}});}else{show(k);}}
function hover(k){root.querySelectorAll('.pin').forEach(function(x){x.classList.toggle('hov',x.getAttribute('data-goal')===k);});if(k&&fig)fig.preload(k);}
root.addEventListener('click',function(e){var b=e.target.closest('.goal-item');if(b)act(b.getAttribute('data-goal'));});
root.addEventListener('mouseover',function(e){var b=e.target.closest('.goal-item,.pin');hover(b?b.getAttribute('data-goal'):null);});
root.addEventListener('mouseleave',function(){hover(null);});
root.addEventListener('keydown',function(e){var t=e.target;
// Arrow keys move to the next or previous chip and choose it (Tab, Enter and Space work as on any button).
var i=chips.indexOf(t);if(i<0)return;var d={ArrowRight:1,ArrowDown:1,ArrowLeft:-1,ArrowUp:-1}[e.key];if(!d)return;
e.preventDefault();var n=chips[(i+d+chips.length)%chips.length];n.focus();if(window.pcEv)pcEv('goal_pick',{goal:n.getAttribute('data-goal')});act(n.getAttribute('data-goal'));});
// /#goals-<slug> (the header's goal menu) chooses that goal on load and when the hash changes.
function fromHash(){var m=location.hash.match(/^#goals-([a-z0-9-]+)$/);
if(m&&root.querySelector('.goal-item[data-goal="'+m[1]+'"]')){act(m[1]);root.scrollIntoView();}}
fromHash();window.addEventListener('hashchange',fromHash);})();
</script>"""

# What we track (owner task 2 Nov 2026): the counts the trust pages and Home's sellers card show, all from site.json;
# each line is drawn only when its data is there (never a placeholder).
N_SELLERS = len(SHOPS)
N_CLINIC_PAGES = len(CLINIC_PROFILES)
# One number on Home and /about/ (owner task, 5 Nov 2026): the clinics on /sellers/, that is the clinic pages. A seller with a plan and no
# page (a tool, pages.md, Category) is not counted. Plan sellers only when the data has no seller pages at all.
N_CLINICS = N_CLINIC_PAGES or len({r["seller_slug"] for r in PLANS})
N_LETTERS = DATA.get("letters_all_total") or len(LETTERS_ALL)
N_STATUS = len({r["substance_slug"] for r in LEGAL_DB or []})
PULLED = nice_date(DATA["pulled_at"][:10]) if DATA.get("pulled_at") else ""
# Home's hero counts (pages.md, Home; owner task 2 Nov 2026): one sentence, only when every count and the pull date are there.
# owner answer Q1 c (2 Nov 2026): shops and online clinics counted apart, as on /sellers/
_ns, _nc = len(SHOPS), len(CLINIC_PROFILES)
HERO_COUNTS = (f" {_ns} shop{'' if _ns == 1 else 's'}, {f'{_nc} online clinic' + ('' if _nc == 1 else 's') + ', ' if _nc else ''}"
               f"{len(PEPTIDE_SLUGS)} substances and {N_LETTERS} FDA warning letters, checked {PULLED}."
               if SHOPS and PEPTIDE_SLUGS and N_LETTERS and PULLED else "")


# Home (pages.md, Home; the "Home v2" sketch, 3 Nov 2026): the hero with the chooser and the label legend, then the
# sections home.py fills in at the markers once every helper exists.
HOME_LEDE = ((HERO_COUNTS.strip() + " ") if HERO_COUNTS else "") + \
    "FDA-approved options first, research-use peptides with their real status, every price dated."
HOME_DESC = ("Find the right option for your goal and where to get it at the best price. FDA-approved options first, "
             "research-use peptides with their real status.")
HOME = f"""
<section class="hero hero-clinic">
  <div class="wrap">
    <h1 class="hero-h1">Find the right option for your goal, and where to get it at the best price.</h1>
    <p class="hero-lede">{HOME_LEDE}</p>
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
    <p class="what-is"><strong>What is a peptide?</strong> A short chain of amino acids. Some are approved medicines (semaglutide, bremelanotide), some are cosmetics in creams, and many are sold online with no approval and no testing. This site tells you which is which, what it costs, and what the proven alternative is.</p>
    <section class="glossary" aria-labelledby="glossary-h">
      <h2 id="glossary-h">What the labels mean</h2>
      <dl class="glossary-list">{GLOSSARY}</dl>
    </section>
  </div>
</section>
<!--home:where-->
<!--home:compare-->
<!--home:learn-->
<!--home:legal-->
<!--home:letters-->
<!--home:creators-->

<div class="wrap sellers-all"></div>
{FIG_JS}
{MAP_JS}
{SELLERS_JS}
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
          (f'<li><a href="/sellers/#clinics">{N_CLINICS} online clinics</a> with plan prices, each with its four checks.</li>' if N_CLINIC_PAGES
           else f"<li>{N_CLINICS} online clinics with plan prices.</li>") if N_CLINICS else "",
          (f'<li><a href="/fda-warning-letters/">{N_LETTERS} FDA warning letters</a> to peptide sellers, compounders and online clinics.</li>'
           if LETTERS_ALL else f"<li>{N_LETTERS} FDA warning letters to peptide sellers, compounders and online clinics.</li>") if N_LETTERS else "",
          # the same count as Home's hero, every substance with a page (owner UX audit A25, 3 Nov 2026: About said 38, Home 41)
          f'<li><a href="/peptides/">{len(PEPTIDE_SLUGS)} substances</a> with an FDA status, each with its source.</li>' if PEPTIDE_SLUGS else ""]
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
<p class="lede">We judge every shop by five checks and every online clinic by four, and build every goal page by the same rule. The checks are facts we hold about a seller, not a safety grade.</p>
<p class="small meta">{AUTHOR}. Last updated {STAMP_CHECKED}. Every claim links to its source. Prices checked {STAMP_CHECKED}.</p>
<h2>The seller checks</h2>
<p>{CLINIC_RULE}</p>
<p>{f'We track <a href="/sellers/">{N_SELLERS} shops{f" and {N_CLINIC_PAGES} online clinics" if N_CLINIC_PAGES else ""}</a>. ' if N_SELLERS else ""}Every shop page and every price window shows a line such as "3 of 5 checks", every clinic page "3 of 4 checks". These are the five, in the order the seller page shows them; a clinic has all but the first. We recompute them each time we pull our data, and the seller page shows the date as "Checked" and a date{f"; the last pull was on {PULLED}" if PULLED else ""}.</p>
<h3>Lab reports</h3>
<p>Met when the seller has published at least one lab report (a certificate of analysis) dated in the last 12 months, for any of its products. We read the reports on the seller's own pages. A miss means we found no report from the last 12 months; it does not mean a product failed a test. A lab report shows what one batch contained on the day it was tested, not that a product is safe or that it works.</p>
<h3>No FDA letter</h3>
<p>Met when the FDA's public list of warning letters holds no letter matched to the seller by its web address or street address. A letter that only shares a company name is not counted, because names repeat. A miss means the FDA sent the seller at least one warning letter; the seller page links each one.{f' We keep every letter to peptide sellers, compounders and online clinics, {N_LETTERS} so far, on our <a href="/fda-warning-letters/">FDA warning letters</a> page.' if LETTERS_ALL and N_LETTERS else ""}</p>
<p>A warning letter is the FDA's notice of violations it believes it found. The company responds, and when the FDA has verified the corrections a close-out letter follows. A letter does not withdraw any approval. We show a seller's letter next to its price and every letter on its page, and a letter alone does not stop a paid link. We still refuse a paid link in two cases: a research-use shop, always, and a seller whose letter is about adulterated drug products while the FDA has published no close-out letter. <a href="{FDA_ABOUT_LETTERS}" rel="nofollow">What the FDA says about warning letters</a></p>
<h3>Found in a state registry</h3>
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
<li>Online clinics get a white "See plans" button to our own page on the clinic until we have a paid link with that clinic. A paid link is a green button with "Paid link" under it.</li>
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

DISCLOSURE_UPDATED = text_changed(("^DISCLOSURE = f", '^"""$', "build.py"), ("^NETWORKS = ", "^}", "paid.py"))
PRIVACY_UPDATED = text_changed(("^PRIVACY_NEWSLETTER = ", '^"""$', "build.py"))
DISCLOSURE = f"""
<section class="page"><div class="wrap prose">
<h1>Affiliate and medical disclosure</h1>
<p class="small meta">Last updated {DISCLOSURE_UPDATED}</p>
<h2>Paid links</h2>
<p>Peptide Chooser is supported by affiliate commissions. Some links on this site go to sellers or services that pay us a commission if you make a purchase or sign up. This costs you nothing extra.</p>
<p>Paid links are labeled where they appear. Commissions do not affect our ratings, rankings or which products we include. Sellers without an affiliate program are rated and listed on the same terms.</p>
<p>A paid link may lead to a seller that has an FDA warning letter; the letter is shown next to the price and on the seller's page.</p>
{paid.networks_block()}
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
<p class="small meta">Last updated {PRIVACY_UPDATED}</p>
<p>This policy explains what information Peptide Chooser ("we") collects when you visit peptidechooser.com and how we use it.</p>
<h2>Information we collect</h2>
<ul>
<li><strong>Email you send us.</strong> If you contact us, we receive your email address and whatever you include in your message. We use it only to reply.</li>
<li><strong>Server logs.</strong> Our hosting provider (GitHub Pages) may record technical data such as IP address, browser type and the pages requested, for security and to operate the service. We do not use this data to identify you.</li>
<li><strong>Analytics, only if you accept.</strong> We use Google Analytics 4 to count visits and see which pages people find useful. It also counts which buttons people click, including clicks on our paid links, and never which words you type in our search. It runs only after you press "Accept" on the cookie notice. If you press "Reject", no analytics cookie is set and nothing is sent to Google. Google Analytics keeps this data for 14 months, then deletes it. Google processes this data under its own <a href="https://policies.google.com/privacy" rel="nofollow noopener">privacy policy</a>. We do not use advertising trackers, and we do not sell or share visitor data.</li>
{PRIVACY_NEWSLETTER}</ul>
<h2>Cookies</h2>
<p>The site sets one small value in your browser to remember your cookie choice. Google Analytics sets its own cookies (named _ga and similar) only after you accept. You can change your mind by clearing the site's data in your browser; the notice will then appear again.</p>
<h2>Paid links</h2>
<p>When you click a paid link, you leave our site. The seller or affiliate network may set cookies to record that you came from us. Their own privacy policies apply to that data. The address of a paid link also carries the path of our page you clicked from, never anything about you.</p>
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
    clash = {i for i, _ in used} & own & set(re.findall(r'<li id="(src-[^"]+)">', SOURCES_HOME))
    assert not clash, f"option rows link sources that this page numbers differently: {clash}"
    out = []
    for sid, n in sorted(used, key=lambda x: int(x[1])):
        m = re.search(rf'<li id="{sid}">(.*?)</li>', SOURCES_HOME)
        if m:
            out.append(f'<li value="{n}" id="{sid}">{m.group(1)}</li>')
    return "".join(out)


def page_footnotes(body):
    """A goal page's footnotes numbered 1 to N in the order the page cites them, and its Sources list made of exactly those
    entries in that order (owner UX audit A13, 3 Nov 2026: weight loss cited 1, 7, 11, 12 and 13 from Home's list while
    its own list had five entries). Each entry keeps its id, the one /sources/ links to."""
    head, sep, tail = body.partition('<section class="section" id="sources">')
    order = list(dict.fromkeys(re.findall(r'<a\b[^>]*href="#(src-[^"]+)"[^>]*>(?:<sup>)?\d+(?:</sup>)?</a>', head)))
    num = {sid: i + 1 for i, sid in enumerate(order)}

    def link(m):
        if m.group(2) not in num:
            return m.group(0)
        n = num[m.group(2)]
        a = re.sub(r'aria-label="Source \d+"', 'aria-label="Source %d"' % n, m.group(1))
        return f'{a}{m.group(3) or ""}{n}{m.group(4) or ""}</a>'
    head = re.sub(r'(<a\b[^>]*href="#(src-[^"]+)"[^>]*>)(<sup>)?\d+(</sup>)?</a>', link, head)
    if not sep:
        return head
    ol = re.search(r'(<ol class="small sources"[^>]*>)(.*?)(</ol>)', tail, re.S)
    items = {m.group(1): m.group(2) for m in re.finditer(r'<li(?: value="\d+")? id="(src-[^"]+)">(.*?)</li>', ol.group(2), re.S)}
    lis = "".join(f'<li value="{num[sid]}" id="{sid}">{items[sid]}</li>' for sid in order if sid in items)
    return head + sep + tail[:ol.start()] + ol.group(1) + lis + ol.group(3) + tail[ol.end():]


def category_page(g):
    return page_footnotes(category_body(g))


# Questions on a goal page (SEO round c, group 2, queue block 9): the searches "peptides for skin", "best peptides for
# muscle growth" and the like, answered from the goal's approved texts and its option rows; no new claim.
GOAL_FAQ = {"skin", "muscle", "weight-loss", "hair"}


def goal_price_word(g, p):
    """The row's own price words in plain text: its cost line ("From $10/mo (generic, pharmacy coupon). Online clinics from
    $50/mo (Winona)."), else its button ("From $0.10/mg · 16 shops" -> "from $0.10/mg at 16 shops"), or ""."""
    plain = lambda t: " ".join(unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<sup>.*?</sup>", "", t, flags=re.S))).split())
    pad, rp = opt_price(p, g["slug"]), row_plan(g, p)
    cost = plain(price_sentence(p, pad) + (" " + plan_line(g, "plan-in", rp) if rp else ""))
    cost = re.sub(r"\s+([).,])", r"\1", re.sub(r"\(\s+", "(", cost)).strip()
    cost = re.sub(r"\) FDA letter (\d{1,2} \w{3} \d{4})", r", FDA warning letter \1)", cost)
    if re.search(r"\$\d", cost):
        return cost.rstrip(".")
    t = re.sub(r'<span class="paid[^"]*">.*?</span>', "", opt_action(g, p, rp, False, pad), flags=re.S)
    t = plain(t).replace("Buy from", "from").replace(" · ", " at ").replace("From", "from").rstrip(".")
    t = re.sub(r" at (\d+ (?:products|creams|serums))", r" across \1", t)
    return t if re.search(r"\$\d", t) else ""


def goal_faq_pairs(g):
    if g["slug"] not in GOAL_FAQ or not g.get("main_query"):
        return []
    mq, opts = g["main_query"], g["peptides"]
    first = re.split(r"(?<=\.)\s", g["short_answer"], 1)[0]
    pairs = [(f"What are the best {mq}?",
              f"{first} The options on this page: " + "; ".join(f'{p["name"]}, {p["line_one"]}' for p in opts) + ".")]
    groups = {}
    for p in opts:
        groups.setdefault(p["status"], []).append(p["name"])
    pairs.append((f"Are {mq} FDA approved?",
                  " ".join(f"{st}: {and_list(ns)}." for st, ns in groups.items())
                  + (' Each status has its source under "Is it legal today?".' if g.get("legal_section") else "")))
    prices = [(p["name"], goal_price_word(g, p)) for p in opts]
    prices = [(n, w) for n, w in prices if re.search(r"\$\d", w)]
    if prices:
        pairs.append((f"How much do {mq} cost?",
                      " ".join(f"{n}: {w[0].lower() + w[1:]}." for n, w in prices) + f" Prices checked {nice_date(GOAL_CHECKED)}."))
    rx = {}
    for p in opts:
        rx.setdefault(p["rx_word"], []).append(p["name"])
    pairs.append((f"Do I need a prescription for {mq}?",
                  " ".join(f"{w[0].upper() + w[1:]}: {and_list(ns)}." for w, ns in rx.items())))
    return pairs


def goal_faq(g):
    pairs = goal_faq_pairs(g)
    return f'<section class="section goal-sec" id="faq"><div class="wrap">{faq_block(mq_cap(g), pairs, "faq-h")}</div></section>' if pairs else ""


def mq_cap(g):
    return g["main_query"]


# Like with like (owner UX audit A26, 3 Nov 2026: a pair compared a pill with an injection): a plan's form from its
# dosage_form, and per clinic the cheapest compounded plan of each form.
PLAN_FORM_WORD = {"injection_vial": "Injection", "pen": "Pen", "tablet": "Pill", "capsule": "Pill", "topical": "Topical",
                  "solution": "Topical", "bundle": "Bundle", "drops": "Drops", "troche": "Troche", "odt": "Dissolving tablet"}
FORM_NOT_STATED = "Form not stated"
# its own name (owner, 3 Nov 2026): plan_form is the goal page filter's "pill"/"shot"; the same name made the later
# definition replace the earlier one
def plan_form_word(r):
    """The form the data names. The data has no membership field: a plan with no form counts as one only when its own name
    says so (Ivim's "Membership and Medication"; owner decision 4 Nov 2026, answer 3 A)."""
    word = PLAN_FORM_WORD.get(r.get("dosage_form") or "")
    return word or ("Membership" if "membership" in (r.get("plan_name") or "").lower() else FORM_NOT_STATED)


KIND_CHIP = {"brand": ("ok", "Brand"), "compounded": ("warn", "Compounded"), "program": ("neutral", "Program"),
             # owner task 2 Nov 2026: "other" is never called compounded, and its label is the plan's form (kind_chip);
             # "generic" (an approved medicine under its own name) renders once the data side sends it
             "generic": ("ok", "Generic")}


def kind_chip(r):
    """(chip class, label) of a plan's kind. Owner decision 4 Nov 2026 (answer 3 A): an "other" plan says only what the
    data names, its form or "Form not stated"."""
    k = plan_kind(r)
    return ("neutral", plan_form_word(r)) if k == "other" else KIND_CHIP[k]


def plan_chip(g, r):
    """What a plan is, as a chip: "Brand, diabetes" (chip-info) for a brand approved for another use (owner answer Q1 a,
    2 Nov 2026: Ozempic is approved for diabetes, not weight loss), else the KIND_CHIP of its kind."""
    use = other_use(g, r)
    chip, label = ("info", f"Brand, {use}") if use else kind_chip(r)
    return f'<span class="chip chip-{chip}">{label}</span>'


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
    """"incl. $99/mo care" when the price holds a monthly membership (task 33), "all-in" when it adds none, "care fee not known" when the
    data has no fee (owner answer Q3 b, 2 Nov 2026)."""
    fee = r.get("membership_fee_monthly")
    return "care fee not known" if fee is None else "all-in" if float(fee) == 0 else f"incl. {usd(fee)}/mo care"


CLINICS_FIRST = 10
# "Compare any two" (btn-line) under the clinic table and under the sellers table; /compare/ is built when plans or sellers exist
COMPARE_LINK = ('<p class="cmp-link"><a class="btn btn-line" href="/compare/">Compare any two</a></p>'
                if DATA.get("plans") or DATA.get("seller_profiles") else "")
# With JavaScript the clinic table is clipped on phones (CSS hides tr.more under .clip) and "Show all N" opens it; without
# JavaScript every row shows and the button stays hidden.
CLINICS_JS = """<script>(function(){var s=document.getElementById('clinics')||document.querySelector('.pep-sold'),m=s&&s.querySelector('.clinics-more');if(!m)return;
s.classList.add('clip');m.hidden=false;document.getElementById('clinics-all').addEventListener('click',function(){s.classList.remove('clip');m.hidden=true;});})();</script>"""


# Brand names explained once (owner UX audit B23, 3 Nov 2026): a brand our data maps to a substance (approved_drugs:
# brand and substance) gets the substance in brackets at its first mention in a plan table, "Foundayo (orforglipron)".
BRAND_SUB = {}
for _a in APPROVED_DB:
    if _a.get("brand_name") and _a["substance_slug"]:
        BRAND_SUB.setdefault(brand_base(_a["brand_name"]).lower(), _a["substance_slug"])


def explain_brand(plan_name, seen):
    """The plan name with "(substance)" after its brand the first time the brand appears (seen: brands already named)."""
    first = plan_name.split()[0] if plan_name else ""
    slug = BRAND_SUB.get(first.lower())
    if not slug or first.lower() in seen or slug.replace("-", " ") in plan_name.lower():
        return plan_name
    seen.add(first.lower())
    name = next((r["canonical_name"] for r in LEGAL_DB or [] if r["substance_slug"] == slug and r.get("canonical_name")), slug.replace("-", " "))
    name = escape(re.sub(r"\s*\(.*\)", "", name).lower())
    return f"{first} ({name}){plan_name[len(first):]}"


def clinic_row_act(r):
    """A clinic plan's button, every kind (owner answer Q1 a, 3 Nov 2026; for compounded plans owner decision C8, 3 Nov 2026, labelled compounded): btn-action "Visit <Name>" with "Paid link"
    only when the data carries the clinic's paid link, on the plan row or its profile (the paid link rule, pages.md, Buttons;
    owner decision 4 Nov 2026); otherwise btn-wait "See plans" to our clinic page."""
    name, paid = seller_base(r["seller_name"]), r.get("paid_url") or PROFILES.get(r["seller_slug"], {}).get("paid_url")
    if paid:
        return (f'<span class="pick-act"><a class="btn btn-action btn-sm" href="{paid_href(r["seller_slug"], paid)}"{paid_ev(r["seller_slug"], paid)} rel="sponsored">Visit {name}'
                '<span class="paid">Paid link</span></a></span>')
    if r["seller_slug"] not in PROFILES:
        return ""
    return (f'<span class="pick-act"><a class="btn btn-wait btn-sm" href="/sellers/{r["seller_slug"]}/"{plans_ev(r["seller_slug"], r)}>See plans</a></span>')


def clinic_section(g, rows):
    """"Online clinic prices" (pages.md, Category, weight loss; owner task 2 Nov 2026): one row per plan, cheapest first;
    the clinic in plain text (no link to any clinic site), its FDA letter chip beside the price, and btn-wait "See plans"
    to our clinic page until a paid link exists per seller (clinic_row_act). Stacked cards on phones (bundle.css, Clinic table)."""
    if not rows:
        return ""
    newest = max(r["last_seen"] for r in rows)
    trs, named = [], set()
    for i, r in enumerate(rows):
        care = care_note(r)
        # on phones the first CLINICS_FIRST rows show until "Show all N" (owner answer Q2 a, 2 Nov 2026; bundle.css, Clinic table)
        more = ' class="more"' if i >= CLINICS_FIRST else ""
        plan = explain_brand(r["plan_name"], named)
        trs.append(f'<tr{more} data-s="{r["substance_slug"]}"{state_attrs(r["seller_slug"])}><td>{clinic_link(r["seller_slug"], seller_base(r["seller_name"]))}</td><td data-l="Plan"><span class="plan-cut" title="{escape(strip_tags(plan))}">{plan}</span></td>'
                   f'<td>{plan_chip(g, r)}</td>'
                   f'<td data-l="Per month"><span class="num">{usd(r["price_monthly"])}</span>{plan_letter(r)}{f"<span class=sub>{care}</span>" if care else ""}</td>'
                   # every row: the letter chip by the price, no FDA letter column, "See plans" to our clinic page (owner answers
                   # Q1 a and Q2 b, 3 Nov 2026)
                   f'<td class="act">{clinic_row_act(r)}</td></tr>')
    return f"""
<section class="band-2" id="clinics" data-state-root>
  <div class="wrap">
    <div class="sec-hd"><div><h2>Online clinic prices</h2><p>{len(rows)} plans at the online clinics we track, cheapest first.</p></div></div>
    <div class="clinic-filter">{state_filter()}</div>{STATE_N}
    <div class="tbl-wrap"><table class="tbl tbl-cards tbl-clinics">
      <thead><tr><th scope="col">Clinic</th><th scope="col">Plan</th><th scope="col">What it is</th><th scope="col">Per month</th><th scope="col"><span class="vh">Action</span></th></tr></thead>
      <tbody>{"".join(trs)}</tbody>
    </table></div>
    {f'<p class="clinics-more" hidden><button type="button" class="btn btn-line" id="clinics-all">Show all {len(rows)}</button></p>{CLINICS_JS}' if len(rows) > CLINICS_FIRST else ""}
    <p class="small" style="margin-top:16px">Prices are the clinics' published monthly prices on {nice_date(newest)}; "from" prices are the lowest shown. A clinic with an FDA warning letter is still listed; the letter is public record.</p>
    {COMPARE_LINK}
  </div>
</section>"""


def table_plans(g):
    """The plans a goal's clinic table lists: its `clinic_plans`, else the plans of its `clinic_table` substances (hair,
    libido, longevity, muscle; owner task 4 Nov 2026: a clinic shows on the goal its plans belong to, from data, no brand named)."""
    subs = (g.get("clinic_table") or {}).get("substances") or []
    return clinic_plans(g) or sorted((r for r in PLANS if r["substance_slug"] in subs and r.get("price_monthly") is not None),
                                     key=lambda r: (float(r["price_monthly"]), r["seller_name"], r["plan_name"]))


def tools_block(g, first_n):
    """The goal's "Tools" block (pages.md, Category; owner answer Q4 a, 4 Nov 2026): what helps but does not prescribe. Name and one
    sentence. A tool has no seller page, so no green button, whatever the data carries (owner task, 5 Nov 2026: a green button only
    where the seller page exists); an entry with `clinic` has that page, so it keeps the button; a row with `needs` shows nothing until the seller's data sets that flag, and a research-use
    shop never shows. Returns the block and its source entries, numbered from first_n."""
    # Drawn only with at least two priced tools in the data for this goal (owner, 5 Nov 2026); otherwise no block and no heading.
    if sum(any(r["seller_slug"] == t["seller_slug"] and r.get("price_monthly") is not None for r in PLANS)
           for t in g.get("tools") or []) < 2:
        return "", ""
    items, srcs = [], []
    for t in g.get("tools") or []:
        slug, prof = t["seller_slug"], TOOL_PROFILES.get(t["seller_slug"]) or {}
        if slug in SHOPS or (t.get("needs") and prof.get(t["needs"]) is not True):
            continue
        line, source, act = t["line"], t["source"], ""
        if t.get("clinic"):  # also a clinic: its cheapest plan comes from the data, and the row keeps the clinic's one button
            plan = min((r for r in PLANS if r["seller_slug"] == slug and r.get("price_monthly")), key=lambda r: r["price_monthly"], default=None)
            if not plan or slug not in PROFILES:
                continue
            line = line.format(plan=f'{plan["plan_name"]} at {usd(plan["price_monthly"])} a month')
            source = source.format(checked=nice_date(plan["observed_at"]))
            act = clinic_button(slug, "See plans", plan=plan)
        n = first_n + len(srcs)
        url = t.get("url")
        where = f': <a href="{url}" rel="nofollow">{url}</a>' if url and "fda.gov" in url else f": {url}" if url else ""
        srcs.append(f'<li value="{n}" id="src-tool-{slug}">{source}{where}</li>')
        name = f'{parts.tile(slug, t["name"], 28, seller=TOOL_LOGOS[slug]) if slug in TOOL_LOGOS else ""}<strong>{t["name"]}</strong>'
        items.append(f'<li class="tool-row"><p>{name}: {line} <a class="ref" href="#src-tool-{slug}" aria-label="Source {n}"><sup>{n}</sup></a></p>{act}</li>')
    if not items:
        return "", ""
    return (f'''<section class="section goal-sec" id="tools">
  <div class="wrap">
    <h2>Tools</h2>
    <ul class="tool-list">{"".join(items)}</ul>
  </div>
</section>''', "".join(srcs))


def plan_form(r):
    """"pill" or "shot" from the plan's dosage form; "" when the data names none or another form (it counts under All only)."""
    f = (r.get("dosage_form") or "").lower()
    return "pill" if f in ("tablet", "capsule", "oral", "odt") else "shot" if f in ("injection_vial", "pen", "injection") else ""


def clinic_order(r):
    """Brand plans first, then compounded, then the rest, each by price (owner task 3 Nov 2026)."""
    k = plan_kind(r)
    return (0 if k in ("brand", "generic") else 1 if k == "compounded" else 2, float(r["price_monthly"]), r["seller_name"], r["plan_name"])


# The clinic filter (pages.md, Category, Clinic prices; the Letters filter parts): kind, form and "No FDA letter" hide rows by
# their data- attributes; the count line says how many show. Without JavaScript the filter stays hidden and every row shows.
CLINIC_FILTER_JS = """<script>
(function(){var s=document.getElementById('clinics'),f=s&&s.querySelector('.clinic-filter');if(!f)return;var tb=s.querySelector('tbody'),
rows=[].slice.call(tb.rows),n=document.getElementById('clinic-n'),no=f.querySelector('.year-chip');
function val(g){var on=f.querySelector('[data-g="'+g+'"][aria-pressed="true"]');return on?on.getAttribute('data-v'):'';}
function draw(){var k=val('kind'),fm=val('form'),nl=no.getAttribute('aria-pressed')==='true',i=0;s.classList.remove('clip');
rows.forEach(function(r){var ok=(!k||r.getAttribute('data-k')===k)&&(!fm||r.getAttribute('data-f')===fm)&&(!nl||r.getAttribute('data-l')==='0')&&!r.hasAttribute('data-state-out');
r.hidden=!ok;r.style.opacity=1;if(ok)i++;});n.textContent=i+' of '+rows.length+' plans';var m=s.querySelector('.clinics-more');if(m)m.hidden=true;}
f.hidden=false;f.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;
if(b.classList.contains('year-chip')){b.setAttribute('aria-pressed',b.getAttribute('aria-pressed')==='true'?'false':'true');}
else{f.querySelectorAll('[data-g="'+b.getAttribute('data-g')+'"]').forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false');});}draw();});
document.addEventListener('pc-state',draw);})();
</script>"""


def goal_clinic_section(g, rows):
    """"Online clinic prices" on a goal page (pages.md, Category, Clinic prices; owner task 3 Nov 2026): brand plans first, then compounded,
    each by price; compact rows: the plan (a brand's substance in brackets at its first mention), its kind chip, the price
    per month with the clinic's FDA letter chip beside it and the care fee, the clinic (our page), and btn-wait "See plans"
    (clinic_row_act). Above it the clinic filter. Stacked cards on phones (bundle.css, Clinic table)."""
    if not rows:
        return ""
    rows = sorted(rows, key=clinic_order)
    newest = max(r["last_seen"] for r in rows)
    trs, named = [], set()
    for i, r in enumerate(rows):
        care = care_note(r)
        k = plan_kind(r)
        kind = "brand" if k in ("brand", "generic") else "compounded" if k == "compounded" else "other"
        more = ' class="more"' if i >= CLINICS_FIRST else ""
        plan = explain_brand(r["plan_name"], named)
        trs.append(f'<tr{more} data-s="{r["substance_slug"]}"{state_attrs(r["seller_slug"])} data-k="{kind}" data-f="{plan_form(r)}" data-l="{1 if (r.get("fda_letter_count") or 0) else 0}">'
                   f'<td><span class="cell-pic">{parts.plan_picture(r)}<span class="name plan-cut" title="{escape(strip_tags(plan))}">{plan}</span></span></td>'
                   f'<td data-l="What it is">{plan_chip(g, r)}</td>'
                   f'<td data-l="Per month"><span class="num">{usd(r["price_monthly"])}</span>{plan_letter(r)}{f"<span class=sub>{care}</span>" if care else ""}</td>'
                   f'<td data-l="Clinic"><span class="cell-pic">{parts.tile(r["seller_slug"], seller_base(r["seller_name"]), 28, seller=PROFILES.get(r["seller_slug"]))}{clinic_link(r["seller_slug"], seller_base(r["seller_name"]), True)}</span></td>'
                   f'<td class="act">{clinic_row_act(r)}</td></tr>')
    seg = lambda grp, opts: (f'<div class="seg" role="group" aria-label="{grp[1]}">'
                             + "".join(f'<button type="button" class="seg-b" data-g="{grp[0]}" data-v="{v}" data-filter="{grp[0]}" data-value="{v or "all"}" aria-pressed="{"true" if not v else "false"}">{t}</button>'
                                       for v, t in opts) + "</div>")
    filt = (f'<div class="clinic-filter" hidden>{seg(("kind", "Kind of plan"), (("brand", "Brand"), ("compounded", "Compounded"), ("", "All")))}'
            f'{seg(("form", "Form"), (("pill", "Pill"), ("shot", "Shot"), ("", "All")))}'
            '<button type="button" class="year-chip" data-filter="fda_letter" data-value="none" aria-pressed="false">No FDA letter</button>'
            f'{state_filter()}</div>')
    return f"""
<section class="band-2 goal-sec" id="clinics" data-state-root>
  <div class="wrap">
    <h2 class="goal-h2">Online clinic prices</h2>
    {filt}
    {STATE_N}<p class="small clinic-n" id="clinic-n" aria-live="polite">{len(rows)} of {len(rows)} plans</p>
    <div class="tbl-wrap"><table class="tbl tbl-compact tbl-cards tbl-clinics">
      <thead><tr><th scope="col">Plan</th><th scope="col">What it is</th><th scope="col">Per month</th><th scope="col">Clinic</th><th scope="col"><span class="vh">Action</span></th></tr></thead>
      <tbody>{"".join(trs)}</tbody>
    </table></div>
    {f'<p class="clinics-more" hidden><button type="button" class="btn btn-line" id="clinics-all">Show all {len(rows)}</button></p>{CLINICS_JS}' if len(rows) > CLINICS_FIRST else ""}
    <p class="small" style="margin-top:12px">Brand plans first, then compounded, each cheapest first. Prices are the clinics' published monthly prices on {nice_date(newest)}. A clinic with an FDA warning letter is still listed; the letter is public record.</p>
    {COMPARE_LINK}
  </div>
</section>{CLINIC_FILTER_JS}"""


def plan_src(g, r):
    """A plan's footnote on the goal page, when the plan has a numbered source; else ""."""
    try:
        sid, n = plan_ref(g, r)
    except KeyError:
        return ""
    return f'<sup><a class="ref" href="#{sid}" aria-label="Source {n}">{n}</a></sup>'


def card_slug(key):
    return key.lower().replace(" ", "-")


def decide_card(key, name, chips, price, act, pic=""):
    return (f'<li class="panel-line decide-card" data-card="{card_slug(key)}">{pic}<p class="decide-k">{key}</p><h2>{name}</h2>'
            f'{f"<span class=chips>{chips}</span>" if chips else ""}<p class="decide-price">{price}</p>{act}</li>')


def decide_cards(g):
    """The goal page's decision cards (pages.md, Category; owner task 3 Nov 2026), in place of the price pad: Best approved,
    Cheapest, No prescription. Every number from data; a card whose data is missing is left out."""
    cards = []
    # Best approved: the FDA-approved option with the most clinics, its cheapest plan that is not compounded
    best = None
    for p in g["peptides"]:
        if not (approved_row(p) and p.get("top_pick", True) and needs_rx(p) is not False):
            continue
        rp = row_plan(g, p)
        if not rp or rp.get("product_kind") == "compounded":
            continue
        n = plan_clinics(g, p, rp)
        if not best or (n, -float(rp["price_monthly"])) > (best[2], -float(best[1]["price_monthly"])):
            best = (p, rp, n)
    if best:
        p, rp, n = best
        name = seller_base(rp["seller_name"])
        cards.append(decide_card("Best approved", p["name"], status_chip(p),
                                 f'At online clinics{plan_src(g, rp)}',
                                 clinic_open(g, p, rp), option_picture(p, rp)))
    # Cheapest: the lowest monthly price among the goal's plans, labelled with its kind
    plans = goal_plans(g)
    if plans and not (best and plans[0] is best[1]):
        c, name = plans[0], seller_base(plans[0]["seller_name"])
        k = plan_kind(c)
        chip = ('<span class="chip chip-warn">Compounded, not FDA approved</span>' if k == "compounded" else
                '<span class="chip chip-ok">Brand</span>' if k in ("brand", "generic") else plan_chip(g, c))
        opens = next((b for b in (clinic_open(g, x, None, c) for x in sorted(g["peptides"], key=lambda x: x.get("plan_kind") != "compounded") if any(r is c for r in option_plans(g, x))) if b), "")
        if opens:  # a plan no option row opens (compounded sermorelin on /muscle/) stays in the clinic table, without a card
            cards.append(decide_card("Cheapest", clean(c["plan_name"]), chip,
                                     f'At {name}{plan_src(g, c)}{plan_letter(c)}',
                                     opens, parts.plan_picture(c)))
    # No prescription: the over-the-counter or cosmetic option; a goal without one, its research-use option
    otc = next((p for p in g["peptides"] if approved_row(p) and needs_rx(p) is False), None)
    cos = next((p for p in g["peptides"] if is_cosmetic(p)), None)
    if otc:
        rp = row_plan(g, otc)
        if rp:
            name = seller_base(rp["seller_name"])
            cards.append(decide_card("No prescription", otc["name"], status_chip(otc),
                                     f'Sold without a prescription{plan_src(g, rp)}{plan_letter(rp)}',
                                     clinic_open(g, otc, rp), option_picture(otc, rp)))
        else:
            # no plan that fits a medicine sold without a prescription: its checked price and the row's own text, never a clinic's plan
            pad = opt_price(otc, g["slug"])
            if pad:
                on_page = otc.get("substance") in PEPTIDE_SLUGS
                page = f'/peptides/{otc["substance"]}/' if on_page else "/learn/"
                label = "FDA status and sources" if on_page else "Read the guides"
                price = re.search(r"from (\$[\d.,]+/mo)", pad).group(1)
                cards.append(decide_card("No prescription", otc["name"], status_chip(otc),
                                         f'<strong>From {price}</strong>{re.search(r"<sup>.*</sup>", pad).group(0)}',
                                         # the card's one button (tools/check.py) goes to our own page on the medicine, or the goal's guide
                                         f'<span class="pick-act"><a class="btn btn-wait btn-sm" href="{page}" data-card="{card_slug("No prescription")}">{label}</a>'
                                         f'<span class="paid">{no_listing_text(otc)}</span></span>',
                                         option_picture(otc, None)))
    elif cos:
        if has_window(cos) and window_kind(cos) in COSMETIC_KINDS:
            low, n = window_low(cos)
            what = cosmetic_word(cos)
            if low is not None:
                cards.append(decide_card("No prescription", cos["name"], status_chip(cos),
                                         f'<strong>From {money(low)} a {"bottle" if what == "serum" else "product"}</strong>, {plural(n, "shop")}',
                                         f'<span class="pick-act">{sellers_button(cos, False, f"Compare {plural(n, what)}", "btn-wait")}</span>', parts.thumb("serum-dropper")))
    else:
        ru = next((p for p in g["peptides"] if has_window(p) and window_kind(p) == "research"), None)
        if ru:
            low, n = window_low(ru)
            if low is not None:
                cards.append(decide_card("No prescription", ru["name"], status_chip(ru),
                                         f'Research-use only, not approved. <strong>From {per_mg(low)}/mg at {plural(n, "shop")}</strong>',
                                         f'<span class="pick-act">{sellers_button(ru, False, kind="btn-wait")}<span class="paid">Our checks, no shop links</span></span>', parts.thumb("vial-research")))
    return f'<ul class="decide">{"".join(cards)}</ul>' if cards else ""


def intro_split(text):
    """The intro's first two sentences for the first screen, the rest for "Is it legal today?" (owner task 3 Nov 2026:
    nothing deleted, only moved)."""
    parts = re.split(r"(?<=\.)\s+(?=[A-Z])", text.strip())
    return " ".join(parts[:2]), " ".join(parts[2:])


# The legal accordion opens on a #legal link (the Compare heading's "Is it legal today?") and for print.
LEGAL_ACC_JS = """<script>
(function(){var d=document.getElementById('legal-acc');if(!d)return;function o(){if(location.hash==='#legal')d.open=true;}
o();window.addEventListener('hashchange',o);window.addEventListener('beforeprint',function(){d.open=true;});})();
</script>"""


def category_body(g):
    """The goal page (pages.md, Category; owner task 3 Nov 2026, UX audit 11.2 and 12): the first screen decides (H1, the
    intro's first two sentences, three decision cards), the option rows follow, then the clinic prices, then the reference
    material: "Is it legal today?" as an accordion, the goals strip, "What to do next" and the sources. The old "Every option,
    side by side" table is gone; its facts the rows did not show are in the opened rows (opt_facts)."""
    srcs = "".join(f'<li id="src-{s["n"]}">{s["text"]}: <a href="{s["url"]}" rel="nofollow">{s["url"]}</a></li>' for s in g.get("sources", []))
    opt_html = "".join(option_rows(g))
    instead = approved_instead(g)
    lead, moved = intro_split(g["short_answer"])
    subs = {x for p in g["peptides"] for x in subs_of(p)}
    legal, legal_checked = legal_rows(subs) if g.get("legal_section") else ([], "")
    legal_html = f"""
<section class="section goal-sec" id="legal">
  <div class="wrap">
    <details class="legal-acc" id="legal-acc"><summary><h2>Is it legal today?</h2><span class="stamp">FDA status checked {legal_checked}</span></summary>
    <div class="legal-acc-in">
      {f"<p>{moved}</p>" if moved else ""}
      <p class="small">FDA status of the {g.get("legal_noun", "peptide")}s on this page, each with its source.</p>
      <div class="tbl-wrap"><table class="tbl tbl-legal">
        <thead><tr><th scope="col">{g.get("legal_noun", "peptide").capitalize()}</th><th scope="col">Status</th><th scope="col">What that means</th></tr></thead>
        <tbody>{"".join(legal)}</tbody>
      </table></div>
      <p class="small" style="margin-top:12px">{g.get("legal_note", LEGAL_NOTE)} {ALL_SUBSTANCES}</p>
    </div></details>
  </div>
</section>{LEGAL_ACC_JS}""" if legal else (f'<section class="section goal-sec"><div class="wrap"><p>{moved}</p></div></section>' if moved else "")
    plans = table_plans(g)
    cards = decide_cards(g)
    own = {f'src-{s["n"]}' for s in g.get("sources", [])}
    srcs += page_sources(opt_html + legal_html + cards, own)
    if plans or goal_plans(g):
        # no link to any clinic site on a page with clinic plans: the plan sources show their address as plain text
        srcs = re.sub(r'(<li value="\d+" id="src-plan-[^"]+">.*?)<a href="([^"]+)" rel="nofollow">\2</a>', r"\1\2", srcs)
    tools_html, tool_srcs = tools_block(g, max([int(x) for x in re.findall(r'<li value="(\d+)"', srcs)] + [len(re.findall(r"<li", srcs))]) + 1)
    srcs += tool_srcs
    sources_html = f"""<section class="section" id="sources">
  <div class="wrap">
    <h2 class="h-sources">Sources</h2>
    <ol class="small sources" style="padding-left:1.2em">{srcs}</ol>
  </div>
</section>""" if srcs else ""
    windows = "".join({window_key(p): seller_window(p) for p in g["peptides"] if has_window(p)}.values())
    return f"""
<section class="hero hero-goal goal-first">
  <div class="wrap">
    <div class="goal-top"><div>
    <h1>{g["h1"]}</h1>
    {author_line(GOAL_CHECKED)}{SOURCE_LINE}
    <p class="intro">{lead}</p>
    </div><div class="goal-panel goal-c-{g["slug"]}">{parts.goal_photo(g["slug"], 120)}</div></div>
    {cards}
  </div>
</section>
<section class="goal-sec goal-opts">
  <div class="wrap">
    <div class="chooser flow flow-solo">
      <div class="flow-hd fh-compare"><h2>Compare the options</h2><a class="step-legal" href="{"#legal" if legal else "/#legal"}"><strong>Is it legal today?</strong></a></div>
      <div class="flow-compare"><div class="step-panel"><p class="goal-for">{g["for"]}</p><ul class="opts">{opt_html}</ul>{instead}</div></div>
    </div>
  </div>
</section>{goal_clinic_section(g, plans)}{tools_html}{legal_html}{goal_faq(g)}
<!--next:{g["slug"]}-->
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


def per_mg_range(lo, hi):
    if lo is None:
        return "unknown"
    return per_mg(lo) if hi is None or per_mg(lo) == per_mg(hi) else f"{per_mg(lo)} to {per_mg(hi)}"


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


# Rule 8 (CLAUDE.md): pages with Search Console impressions keep their live title and H1 (data/rule8.json, owner task 7 Nov 2026).
RULE8 = json.loads((Path(__file__).parent / "data" / "rule8.json").read_text(encoding="utf-8"))["pages"] if (Path(__file__).parent / "data" / "rule8.json").exists() else {}


def seller_title(r):
    """Title (Tier 1): the full pattern, shortened step by step to the 60 characters tools/check.py allows, always ending in
    "| Peptide Chooser" (owner queue block 5, round a, 7 Nov 2026): the middle words shorten, the brand stays."""
    kept = RULE8.get(f'/sellers/{r["seller_slug"]}/')
    if kept:
        return kept["title"]
    name, end = seller_name(r), " | Peptide Chooser"
    if r["seller_slug"] in CLINIC_PROFILES:
        base = re.sub(r"\s*\(.*\)", "", name).strip()
        tries = [f"{n} review{w}{end}" for n in dict.fromkeys((name, base))
                 for w in (": plans, prices and checks", ": plans, prices, checks", ": plans and prices", "")]
        last = f"{base} review"
    else:
        tries = [f"{name} review{w}{end}" for w in (": prices, lab reports, FDA letters", ": prices, lab reports", ": lab reports", "")]
        last = f"{name} review"
    return next((t for t in tries if len(t) <= 60), last)


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
    care = "care fee not known" if fee is None else "no care fee" if float(fee) == 0 else f"{usd(fee)}/mo care included"
    price = f"{plural(len(plans), 'plan')} from {usd(plans[0]['price_monthly'])}/mo, {care}." if plans else ""
    on = nice_date(r["score_checked_on"]) if r.get("score_checked_on") else ""
    score = f"{score_of(r)} of {out_of(r)} checks met on {on}." if on else ""
    checked = f"{score_of(r)} of {out_of(r)} checks met." if on else ""
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


def legal_state(r):
    """The Legal pages check in one of five states (owner task 3 Nov 2026; pages.md, Seller), from the newest legal-pages
    crawl (site.seller_profile legal_check_outcome and legal_checked_on): (state, sentence). A blocked or failed attempt
    is not met; the score does not change. Data from before the two columns falls back to the seen pages alone."""
    pages = (("terms", "Terms"), ("privacy", "Privacy"), ("refund", "Refund"))
    seen = [r.get(f"{k}_seen") for k, _ in pages]
    out, on = r.get("legal_check_outcome"), r.get("legal_checked_on")
    date = f" ({nice_date(on)})" if on else ""
    if r.get("score_legal_pages"):
        return "Met", "Terms, privacy and refund pages found."
    if out == "blocked":
        return "Could not check", f"the site blocks our crawler{date}."
    if out == "failed":
        return "Could not check", f"the site did not answer{date}."
    if out is None and all(x is None for x in seen):
        return "Not checked yet", "Terms, privacy and refund pages."
    return "Not met", "Missing: " + ", ".join(t.lower() for (k, t), x in zip(pages, seen) if not x) + " page."


LEGAL_STATES = ("Met", "Not met", "Could not check", "Not checked yet")


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
    state, said = legal_state(r)
    legal = ({"Not checked yet": "Terms, privacy and refund pages: not checked yet.",
              "Could not check": f"Could not check: {said}"}.get(state, said))
    seen_on = prices_checked(r)  # the same date as "Prices checked" above the table: one price date per page (audit, 7 Nov 2026)
    # the check is the data's (site.sellers.score_fresh_prices: a price per mg in the last 30 days); the date never decides it
    fresh = (f"Prices checked {nice_date(seen_on)}." if r.get("score_fresh_prices") and seen_on else
             f"No price per mg seen in the last 30 days; the newest price we hold is from {nice_date(seen_on)}." if seen_on else "No price seen.")
    return dict(zip([k for k, _ in SCORE_CHECKS], (lab, letter, company, legal, fresh)))


CLINIC_LAB_LINE = '<p class="check-nolab">Online clinics prescribe and publish no lab reports, so a clinic is checked on four facts, not five.</p>'


def card_chip(k, t, r):
    """One check's chip in the Background check card and the "Is <Name> legit?" list: its name, with the state spoken.
    The letter check says what it found instead of "No FDA letter: no" (owner UX audit, 3 Nov 2026): "FDA letter: none"
    when met, "FDA letter: yes (N)" when not ("FDA warning letter: ..." does not fit the card's 124px chip column on
    phones; the line beside the chip says "FDA warning letter")."""
    on = bool(r.get(k))
    if k == "score_no_fda_letter":
        t, state = ("FDA letter: none" if on else f'FDA letter: yes ({r.get("fda_letter_count") or 1})'), ""
    else:
        # the spoken state goes first, with the name, so a long name never pushes it past the edge (320px, task 33)
        state = f'<span class="vh">{t}: {"yes" if on else "no"}</span>'
    shown = f'<span aria-hidden="true">{t}</span>' if state else t
    return f'<span class="chip chip-{"ok" if on else "neutral"} mark-{"yes" if on else "no"}">{state}{shown}</span>'


def check_card(r):
    """Background check card (pages.md, Seller; owner task 3 Nov 2026): a summary in the right column, sticky from 900px.
    The seller's checks as one chip each (a shop's five, a clinic's four), the name only: their facts and dates live in the
    legit section, once."""
    rows = "".join(f"<li>{card_chip(k, t, r)}</li>" for k, t in seller_checks(r))
    return f"""
      <div class="board check-card" aria-labelledby="check-h">
        <div class="check-head"><h2 id="check-h">Background check</h2><p class="check-n"><span class="num-xl">{score_of(r)}</span> <span class="num-unit">of {out_of(r)} checks</span></p></div>
        <ul class="check-chips">{rows}</ul>{CLINIC_LAB_LINE if r["seller_slug"] in CLINIC_PROFILES else ""}
        <div class="rx-foot"><span class="stamp">Checked {nice_date(r["score_checked_on"])}</span><span class="fine">Checks are facts we hold about the seller, not a safety or quality grade.</span></div>
        <p class="check-how"><a href="/how-we-rate/">How we rate</a></p>
      </div>"""


def prices_checked(r):
    """The newest price date the seller's table shows: plans' last_seen for a clinic, the substances' newest price for a shop."""
    if r["seller_slug"] in CLINIC_PROFILES:
        days = [p.get("last_seen") or "" for p in clinic_plan_rows(r)]
    else:
        days = [(x.get("newest_price_observed_at") or "")[:10] for x in SELLER_SUBS.get(r["seller_slug"], [])]
    days = [d for d in days + [(r.get("price_updated_at") or "")[:10]] if d]
    return max(days) if days else ""


def seller_subs_section(r):
    rows = SELLER_SUBS.get(r["seller_slug"], [])
    if not rows:
        return ""
    trs = []
    for s in rows:
        label = escape(sub_label(s["substance_slug"]))
        page = f'/peptides/{s["substance_slug"]}/'  # the substance's own page (audit A24: not the first goal page)
        name = f'<a class="name" href="{page}">{label}</a>' if s["substance_slug"] in PEPTIDE_SLUGS else f'<span class="name">{label}</span>'
        coa = '<span class="chip chip-ok">Yes</span>' if s.get("has_coa") else '<span class="chip chip-neutral">No</span>'
        trs.append(f'<tr><td>{name}</td><td class="num" data-l="Listings">{s["listing_count"]}</td>'
                   f'<td class="num" data-l="Per mg">{per_mg_range(s.get("price_per_mg_min"), s.get("price_per_mg_max"))}</td>'
                   f'<td data-l="Lab report">{coa}</td></tr>')
    total = r.get("substance_count") or len(rows)
    on = prices_checked(r)
    more = f'<p class="small seller-more">{plural(total, "substance")} in all.</p>' if total > len(rows) else ""
    return f"""
<section class="seller-sec" id="sells" aria-labelledby="sells-h">
  <h2 id="sells-h">What it sells</h2>
  {f'<p class="small seller-lede">Prices checked {nice_date(on)}.</p>' if on else ""}
  <div class="tbl-wrap"><table class="tbl tbl-cards tbl-compact tbl-sells">
    <thead><tr><th scope="col">Substance</th><th scope="col">Listings</th><th scope="col">Per mg</th><th scope="col">Lab report</th></tr></thead>
    <tbody>{"".join(trs)}</tbody>
  </table></div>
  {more}<p class="small seller-note">Per mg is the price divided by the stated amount; blends and listings without an amount have none. A substance name opens our page on that substance.</p>
</section>"""


def seller_letters_section(r):
    rows = SELLER_LETTERS.get(r["seller_slug"], [])
    if not rows:
        return ""
    trs = "".join(f'<tr><td class="num">{nice_date(x["letter_date"])}</td><td>{escape(clean(x["letter_subject"]))}</td>'
                  f'<td><a href="{escape(x["letter_url"])}" rel="nofollow">FDA letter</a>{closed_chip(x["letter_url"])}</td></tr>' for x in rows)
    more = '<p class="small seller-note"><a href="/fda-warning-letters/">Every FDA warning letter to peptide sellers</a></p>' if LETTERS_ALL else ""
    # id="fda-letters": the letter chips in the tables link here (owner task 3 Nov 2026)
    return f"""
<section class="seller-sec" id="fda-letters" aria-labelledby="fda-letters-h">
  <h2 id="fda-letters-h">FDA warning letters</h2>
  <p class="small seller-lede">Matched by the seller's web address or street address.</p>
  <div class="tbl-wrap"><table class="tbl tbl-compact tbl-letters">
    <thead><tr><th scope="col">Date</th><th scope="col">Subject</th><th scope="col">Source</th></tr></thead>
    <tbody>{trs}</tbody>
  </table></div>
  {more}
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


def company_ledger(r):
    """The company as a 3-row ledger under the "Found in a state registry" check (owner task 3 Nov 2026): Name, State, Found in with
    its source; only with a company from a state registry or an FDA letter (owner answer Q4 a)."""
    if not shown_company(r):
        return ""
    rows = [("Name", escape(clean(r["entity_name"])))]
    if r.get("entity_state"):
        rows.append(("State", STATES.get(r["entity_state"], r["entity_state"])))
    found = EVIDENCE_WORDS.get(r.get("entity_evidence"), "")
    found = found[:1].upper() + found[1:]
    if r.get("registry_status"):
        found += f', {r["registry_status"]}' + (f' on {nice_date(r["registry_checked_on"])}' if r.get("registry_checked_on") else "")
    src = company_source(r)
    if found or src:
        rows.append(("Found in", found + (": " + src if found and src else src)))
    return '<div class="company-ledger">' + "".join(f'<div class="ledger"><span>{k}</span><span>{v}</span></div>' for k, v in rows) + "</div>"


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
    """"Similar sellers" under the card (owner task 3 Nov 2026): the three sellers similar_sellers picks, as small links."""
    items = "".join(f'<li>{parts.tile(x["seller_slug"], seller_base(seller_name(x)), 28, shop=x["seller_slug"] in SHOPS, seller=x)}<span><a href="/sellers/{x["seller_slug"]}/">{seller_name(x)}</a> · {score_of(x)} of {out_of(x)} checks</span></li>'
                    for x in similar_sellers(r))
    return f"""
      <nav class="seller-similar" aria-labelledby="similar-h">
        <h2 id="similar-h" class="h-sources">Similar sellers</h2>
        <ul class="small">{items}</ul>
        <p class="small"><a href="/sellers/">All sellers we track</a></p>
      </nav>""" if items else ""


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
    return "care fee not known" if fee is None else "no separate care fee" if float(fee) == 0 else f"{usd(fee)} a month for care included"


def plan_cost(x):
    """What a month of the plan costs the reader, for comparing two plans: the monthly figure (care fee included) plus a
    consult fee when the data has one (data agent's task 33, 7 Nov 2026)."""
    return float(x["price_monthly"]) + float(x.get("consult_fee") or 0)


def cheapest_elsewhere(p):
    """The lowest-cost plan at another clinic with the same medication, kind and stated dosage form, or None. A plan with no
    stated form gets no pair: a pill is never set against a shot (data agent's task 33, 7 Nov 2026)."""
    if not p["substance_slug"] or not p.get("dosage_form"):
        return None
    rows = [x for x in PLANS if x["seller_slug"] != p["seller_slug"] and x["substance_slug"] == p["substance_slug"]
            and x.get("dosage_form") == p["dosage_form"] and plan_kind(x) == plan_kind(p) and x.get("price_monthly") is not None]
    return min(rows, key=lambda x: (plan_cost(x), x["seller_name"]), default=None)


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
        elsewhere = (f'<span class="cell-pic">{parts.tile(other["seller_slug"], seller_base(other["seller_name"]), 24, seller=PROFILES.get(other["seller_slug"]))}<span><span class="num">{usd(plan_cost(other))}</span><span class="sub">{clinic_link(other["seller_slug"], seller_base(other["seller_name"]))}</span></span></span>'
                     if other else '<span class="sub">no medication named</span>' if not p["substance_slug"]
                     else '<span class="sub">form not stated</span>' if not p.get("dosage_form") else '<span class="sub">no other clinic</span>')
        fee = p.get("membership_fee_monthly")
        trs.append(f'<tr><td><span class="cell-pic">{parts.plan_picture(p)}<span class="name">{clean(p["plan_name"])}</span></span></td><td data-l="What it is">{plan_chip(plan_goal(p), p)}</td>'
                   f'<td class="num" data-l="Per month">{usd(p["price_monthly"])}</td>'
                   f'<td data-l="Care fee">{"not known" if fee is None else "none" if float(fee) == 0 else usd(fee) + "/mo, included"}</td>'
                   f'<td data-l="Cheapest elsewhere">{elsewhere}</td></tr>')
    on = prices_checked(r)
    return f"""
<section class="seller-sec" id="plans" aria-labelledby="plans-h">
  <h2 id="plans-h">Plans and prices</h2>
  {f'<p class="small seller-lede">Prices checked {nice_date(on)}.</p>' if on else ""}
  <div class="tbl-wrap"><table class="tbl tbl-cards tbl-clinics tbl-compact tbl-plans">
    <thead><tr><th scope="col">Plan</th><th scope="col">What it is</th><th scope="col">Per month</th><th scope="col">Care fee</th><th scope="col">Cheapest elsewhere</th></tr></thead>
    <tbody>{"".join(trs)}</tbody>
  </table></div>
  <p class="small seller-note">Per month is the clinic's published monthly price for the plan, with its monthly membership or care fee included when it shows one. Cheapest elsewhere is the lowest monthly cost, care and consult fees included, for the same medication, kind and form at another clinic we track; a plan whose form is not stated gets none.</p>
</section>"""


LEGIT_CLOSE = "These are the facts we hold; we do not call any seller legit or safe, and we never link to the shop."
# a clinic is not a research-use shop: no link until a paid one exists, and then it is marked (owner UX audit, 3 Nov 2026)
LEGIT_CLOSE_CLINIC = ("These are the facts we hold; we do not call any seller legit or safe. We do not link to the clinic "
                      "until it has a paid link, and we say so when it does.")
# a clinic with a paid link: the no-link sentence goes and nothing replaces it; "Paid link" under its button says it (owner, 5 Nov 2026)
LEGIT_CLOSE_PAID = "These are the facts we hold; we do not call any seller legit or safe."


def legit_heading(r):
    """The one place the site may write "legit" (owner decision 2 Nov 2026; pages.md, Rules that apply to every page):
    this question, as the H2 of a seller page. tools/check.py allows the word nowhere else."""
    return f"Is {seller_base(seller_name(r))} legit? What we can check"


LEGIT_TAIL = " Is it legit? See the five checks."
LEGIT_TAIL_CLINIC = " Is it legit? See the four checks."


def legit_description(d, r):
    """A seller page's description under 150 characters gets LEGIT_TAIL (owner task 2 Nov 2026), when it still fits
    in the 160 characters tools/check.py allows."""
    tail = LEGIT_TAIL_CLINIC if r["seller_slug"] in CLINIC_PROFILES else LEGIT_TAIL
    return d + tail if len(d) < 150 and len(d) + len(tail) <= 160 else d


def and_list(xs):
    xs = list(xs)
    return "" if not xs else xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def legit_more(r):
    """The "Is <Name> legit?" section's longer text (owner queue block 7, round a2, 7 Nov 2026: about 400 words, from data,
    additions only). One paragraph per field group; a missing field drops its sentence, and nothing here is a verdict."""
    name, clinic = seller_base(seller_name(r)), is_clinic(r)
    kind = kind_words(r)[0]
    out = []
    first, on = r.get("first_seen"), r.get("score_checked_on")
    who = [f"{name} is {'an' if kind[0] in 'aeiou' else 'a'} {kind}."]
    if first and on:
        who.append(f"We have tracked it since {nice_date(first[:10])} and last checked it on {nice_date(on[:10])}.")
    out.append(" ".join(who))
    if clinic:
        plans = clinic_plan_rows(r)
        if plans:
            lo, hi = plans[0]["price_monthly"], max(p["price_monthly"] for p in plans)
            comp = sum(1 for p in plans if plan_kind(p) == "compounded")
            brand = sum(1 for p in plans if plan_kind(p) == "brand")
            t = [f"Its price page shows {plural(len(plans), 'plan')}" + (f", from {usd(lo)} to {usd(hi)} a month." if hi != lo else f" at {usd(lo)} a month.")]
            if comp:
                lead = ("The plan is" if len(plans) == 1 else f"All {len(plans)} are") if comp == len(plans) else f"{plural(comp, 'plan')} {'are' if comp > 1 else 'is'}"
                t.append(f"{lead} compounded: made by a pharmacy and not FDA approved, even when an approved medicine has the same ingredient.")
            if brand:
                t.append(f"{plural(brand, 'plan')} {'are brand-name medicines' if brand > 1 else 'is a brand-name medicine'}.")
            fees = {care_words(p) for p in plans}
            t.append("The care fee is not shown on its price page." if fees == {"care fee not known"} else f"Care fees, where shown: {and_list(sorted(fees - {'care fee not known'}))}.")
            out.append(" ".join(t))
        states = (CLINIC_STATES.get(r["seller_slug"]) or {}).get("not_in") or []
        out.append(f"It does not take patients in {and_list([STATES.get(x, x) for x in states])}." if states
                   else "We have no state limits on file for it.")
        out.append("An online clinic publishes no lab reports: a pharmacy fills each prescription, so we check the clinic on four facts, not five.")
    else:
        subs = sorted(SELLER_SUBS.get(r["seller_slug"], []), key=lambda s: (-(s.get("listing_count") or 0), s["substance_slug"]))
        t = []
        if r.get("product_count") is not None and r.get("substance_count") is not None:
            t.append(f"It lists {plural(r['product_count'], 'product')} across {plural(r['substance_count'], 'substance')}.")
        if subs:
            top = [f"{sub_label(s['substance_slug'])} ({plural(s['listing_count'], 'listing')})" for s in subs[:3] if s.get("listing_count")]
            if top:
                t.append(f"The most listed: {and_list(top)}.")
        lo, hi = r.get("price_per_mg_min"), r.get("price_per_mg_max")
        if lo is not None and lo >= 0.01 and hi is not None:
            t.append(f"Price per mg: {per_mg_range(lo, hi)}.")
        if r.get("seller_kind") == "S1_RUO":
            t.append("These are research-use peptides: vials labelled for lab use, not approved for use in people.")
            ok = [sub_label(s["substance_slug"]) for s in subs if (db_status(s["substance_slug"]) or {}).get("chip") == "ok"]
            if ok:
                t.append(f"{and_list(ok[:3])} {'is' if len(ok[:3]) == 1 else 'are'} in FDA-approved medicines, but a research-use vial is not that medicine.")
        elif r.get("seller_kind") == "S4_SUPPLEMENT_COSMETIC":
            t.append("Supplements and cosmetics do not need FDA approval before they are sold.")
        if t:
            out.append(" ".join(t))
        if subs:
            withc = [sub_label(s["substance_slug"]) for s in subs if s.get("has_coa")]
            lab = (f"We found a lab report for {len(withc)} of the {plural(len(subs), 'substance')} in the table above" + (f": {and_list(withc[:4])}." if len(withc) <= 4 else ".")
                   if withc else f"We found no lab report for any of the {plural(len(subs), 'substance')} in the table above.")
            if r.get("newest_coa_date"):
                lab += f" The newest is dated {nice_date(r['newest_coa_date'])}."
            out.append(lab + " A lab report tests one batch; it says nothing about a vial from another batch, and we do not test products ourselves.")
    letters = sorted(SELLER_LETTERS.get(r["seller_slug"], []), key=lambda x: x["letter_date"], reverse=True)
    if letters:
        t = [f"The FDA sent {name} {plural(len(letters), 'warning letter')}."]
        for x in letters[:3]:
            t.append(f"On {nice_date(x['letter_date'])}: {clean(x['letter_subject'])}" + (f", closed on {nice_date(x['closed_on'])}." if x.get("closed_on") else "."))
        out.append(" ".join(t))
    elif r.get("score_no_fda_letter"):
        out.append(f"We found no FDA warning letter to {name} in the letters the FDA publishes" + (f", as of {nice_date(on[:10])}." if on else "."))
    if shown_company(r) and r.get("entity_evidence") == "registry":
        st = STATES.get(r.get("entity_state") or "", r.get("entity_state") or "")
        out.append(f"The company behind it is {clean(r['entity_name']).rstrip('.')}" + (f", {r['registry_status']} in the {st} business registry" if r.get("registry_status") and st else "")
                   + (f" on {nice_date(r['registry_checked_on'])}." if r.get("registry_checked_on") else "."))
    elif shown_company(r):
        out.append(f"The FDA's letter names the company: {clean(r['entity_name']).rstrip('.')}. We did not find it in a state business registry.")
    else:
        out.append(f"We could not match {name} to a company in a state business registry. We show a company only from a registry or an FDA letter, never from the seller's own pages.")
    state, _ = legal_state(r)
    legal_on = r.get("legal_checked_on") or r.get("terms_checked_on")
    when = f" on {nice_date(legal_on[:10])}" if legal_on else ""
    if state == "Met":
        out.append(f"Its terms, privacy and refund pages were all there when we looked{when}.")
    elif state == "Not met":
        miss = [w for k, w in (("terms", "terms"), ("privacy", "privacy"), ("refund", "refund")) if not r.get(f"{k}_seen")]
        out.append(f"When we looked{when}, we could not find its {and_list(miss)} {'page' if len(miss) == 1 else 'pages'}.")
    elif state == "Could not check":
        out.append(f"Its site did not let us read its terms, privacy and refund pages{when}.")
    else:
        out.append("We have not yet checked its terms, privacy and refund pages.")
    return "".join(f"\n  <p>{escape(p, quote=False)}</p>" for p in out)


def seller_org_schema(r):
    """The seller as an Organization (owner queue block 7, round a2, 7 Nov 2026): its name, and the company and state only
    when the page shows them (a state registry or an FDA letter). No url or sameAs: we never link to a seller's site."""
    org = {"@context": "https://schema.org", "@type": "Organization", "@id": f"{SITE}/sellers/{r['seller_slug']}/#seller",
           "name": seller_base(seller_name(r))}
    if shown_company(r):
        org["legalName"] = clean(r["entity_name"]).rstrip(".")
        if r.get("entity_state") in STATES:
            org["address"] = {"@type": "PostalAddress", "addressRegion": r["entity_state"], "addressCountry": "US"}
    return '<script type="application/ld+json">' + json.dumps(org, ensure_ascii=False) + "</script>"


def legit_section(r):
    """"Is <Name> legit? What we can check" (pages.md, Seller; owner tasks 2 and 3 Nov 2026): the seller's checks by name (a shop's five, a clinic's four), each
    "Met:" or "Not met:" with its fact and date (the only place they appear; the marks are in the card), the company
    ledger under "Found in a state registry", then the closing sentence."""
    lines = check_lines(r)
    legal = legal_state(r)
    line = lambda k: f"{legal[0]}: {legal[1]}" if k == "score_legal_pages" else f'{"Met" if r.get(k) else "Not met"}: {lines[k]}'
    items = "".join(
        f'<li><span class="check-key">{t}</span><span class="check-line">{line(k)}'
        f'{company_ledger(r) if k == "score_registered_company" else ""}</span></li>'
        for k, t in seller_checks(r))
    return f"""
<section class="seller-sec legit" id="legit" aria-labelledby="legit-h">
  <h2 id="legit-h">{legit_heading(r)}</h2>
  <ul class="check-list legit-list">{items}</ul>{legit_more(r)}
  <p class="small legit-close">{(LEGIT_CLOSE_PAID if r.get("paid_url") else LEGIT_CLOSE_CLINIC) if is_clinic(r) else LEGIT_CLOSE}</p>
</section>"""


# The FAQ part (pages/parts.md, FAQ; owner's assistant task, 7 Nov 2026): first on one seller page as the book's example, then
# on every seller page with its FAQPage schema (owner queue block 5, round a, 7 Nov 2026). Every answer is a sentence the page
# already holds from data, never a new claim.


def faq_schema(pairs):
    """FAQPage JSON-LD with the same questions and answers the page shows, tags stripped."""
    plain = lambda x: re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", x))).strip()
    els = [{"@type": "Question", "name": plain(q), "acceptedAnswer": {"@type": "Answer", "text": plain(a)}} for q, a in pairs if q and a]
    if not els:
        return ""
    return ('<script type="application/ld+json">'
            + json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": els}, ensure_ascii=False) + "</script>")


def faq_block(name, pairs, heading_id, cls="seller-sec faq"):
    """Questions as h3 with their answers, between hairlines; no accordion, no icon. A guide passes cls="faq", so its h2
    is the guide's own prose h2 (pages/learn.md, Guide)."""
    if not pairs:
        return ""
    items = "".join(f'<div class="faq-item"><h3>{q}</h3><p>{a}</p></div>' for q, a in pairs if a)
    return (f'\n<section class="{cls}" aria-labelledby="{heading_id}">\n  <h2 id="{heading_id}">Questions about {name}</h2>\n'
            f'  <div class="faq-list">{items}</div>\n</section>')


def seller_faq_pairs(r):
    """A seller's questions, answered from its data."""
    name, lines, clinic = seller_base(seller_name(r)), check_lines(r), is_clinic(r)
    states = (CLINIC_STATES.get(r["seller_slug"]) or {}).get("not_in") or []
    ans = clinic_answer(r) if clinic else short_answer(r)
    checks = [t for _, t in seller_checks(r)]
    pairs = [
        (f"What does {name} {'prescribe' if clinic else 'sell'}?", ans[0]),
        (f"How much does {name} cost?", ans[1] if clinic and len(ans) > 1 else ""),
        (f"Has the FDA sent {name} a warning letter?", lines["score_no_fda_letter"]),
        (f"Does {name} ship to every state?", f"Not to {', '.join(STATES.get(x, x) for x in states)}." if states else f"We have no state limits on file for {name}.") if clinic else ("", ""),
        (f"How do we check {name}?", f"On {home.num_word(len(checks)).lower()} facts: {', '.join(checks[:-1])} and {checks[-1]}. Each is a yes or no with its date, in the list above."),
    ]
    return name, [(q, a) for q, a in pairs if q and a]


def seller_faq(r):
    name, pairs = seller_faq_pairs(r)
    return faq_block(name, pairs, "faq-h")


def seller_action(r):
    """The page's one action on the H1's row (owner task 3 Nov 2026): a clinic compares with another clinic, a shop with
    another shop, on /compare/ (built whenever seller pages are). A clinic with a paid link in the data also gets "Visit <Name>"
    with "Paid link" under it, the same size beside it: the one pair of actions (pages.md, Seller, Top block; owner answer
    Q1 b, 4 Nov 2026)."""
    if r["seller_slug"] in CLINIC_PROFILES:
        plans = clinic_plan_rows(r)
        compare = (f'<a class="btn btn-ink" href="/compare/?a=p.{r["seller_slug"]}.{plans[0]["plan_slug"]}"{ev("compare_pick", kind="plan")}>Compare with another clinic</a>'
                   if plans else "")
        if not r.get("paid_url"):
            return compare
        return (f'<div class="seller-pair">{compare}<span class="pick-act"><a class="btn btn-action" href="{paid_href(r["seller_slug"], r["paid_url"])}"{paid_ev(r["seller_slug"], r["paid_url"])} rel="sponsored">'
                f'Visit {seller_base(seller_name(r))}</a><span class="paid">Paid link</span></span></div>')
    return f'<a class="btn btn-ink" href="/compare/?a=s.{r["seller_slug"]}"{ev("compare_pick", kind="seller")}>Compare with another shop</a>'


def seller_page(r):
    clinic = r["seller_slug"] in CLINIC_PROFILES
    answer = " ".join(clinic_answer(r) if clinic else short_answer(r))
    checked = max((r.get("price_updated_at") or "")[:10], (r.get("score_checked_on") or "")[:10], (r.get("first_seen") or "")[:10])
    on = prices_checked(r)
    meta = " · ".join(x for x in ("Prices, checks and what we found",
                                  f'Tracked since {nice_date(r["first_seen"][:10])}' if r.get("first_seen") else "",
                                  f"Prices checked {nice_date(on)}" if on else "") if x)
    return f"""
<section class="seller-top">
  <div class="wrap">
    <div class="seller-head">
      <div class="seller-id">
        {f'<img class="h1-logo" src="{r.get("wordmark_path") or r["logo_path"]}" alt="" height="28">' if clinic and r.get("logo_path") else parts.tile(r["seller_slug"], seller_base(seller_name(r)), 72, shop=not clinic, seller=r)}
        <div class="seller-id-text">
        <h1>{seller_base(seller_name(r))} review</h1>
        <p class="seller-kind"><span class="chip chip-neutral">{kind_words(r)[1]}</span></p>
        {author_line(checked) if checked else ""}
        <p class="small seller-meta">{meta}</p>{not_in_line(r["seller_slug"], "p")}
        </div>
      </div>
      <div class="seller-score"><p class="check-n"><span class="num-xl">{score_of(r)}</span> <span class="num-unit">of {out_of(r)} checks</span></p>{seller_action(r)}</div>
    </div>
    <p class="intro seller-answer">{answer}</p>
  </div>
</section>
<div class="wrap seller-body">
  <div class="seller-main">{clinic_plans_section(r) if clinic else seller_subs_section(r)}{legit_section(r)}{seller_letters_section(r)}{seller_faq(r)}</div>
  <aside class="seller-side" aria-label="Background check">{check_card(r)}{similar_section(r)}</aside>
</div>
"""



def compare_ppm(r):
    """The seller's price per mg range from listings between $0.01 and $100/mg: its own lowest and highest, and those of
    its top substances; a value outside the band is a misread unit until the database fixes it (owner, 2 Nov 2026, the
    seller pages' Q6 a rule widened to the top). (None, None) when nothing is left."""
    vals = [r.get("price_per_mg_min"), r.get("price_per_mg_max")]
    vals += [x.get(k) for x in SELLER_SUBS.get(r["seller_slug"], []) for k in ("price_per_mg_min", "price_per_mg_max")]
    vals = [v for v in vals if v is not None and PPM_LOW <= v <= PPM_HIGH]
    return (min(vals), max(vals)) if vals else (None, None)


def sellers_order(x):
    return (-(x.get("score") if x.get("score") is not None else -1), -(x.get("product_count") or 0), seller_name(x).lower())


# Filters and sort on /sellers/ (pages.md, Sellers; owner task 2 Nov 2026): with JavaScript, one filter block above the
# shops (name, substance, minimum checks, sort, the five checks as chips) that also filters the clinics where a filter
# applies (a clinic has no lab-report check); the clinics keep their own sort. The state lives in the URL hash
# (#substance=bpc-157&min=3), so a link carries a filter; the page stays one URL. The script reads only the rows' data-
# attributes, so it names no seller. Without JavaScript the controls stay hidden and every shop and clinic shows.
# chip labels in plain words (owner task w2, UX audit B7, 3 Nov 2026)
SELLER_CHECKS = [("lab", "score_lab_testing", "Lab report this year"), ("letter", "score_no_fda_letter", "No FDA letter"),
                 ("company", "score_registered_company", "Found in a state registry"), ("legal", "score_legal_pages", "Legal pages found"),
                 ("fresh", "score_fresh_prices", "Prices this month")]
SELLER_SORTS = [("checks", "Most checks"), ("products", "Most products"), ("price", "Lowest price per mg"), ("name", "Name"),
                ("since", "Tracked since, oldest first")]


def met_checks(r):
    return " ".join(k for k, f, _ in SELLER_CHECKS if r.get(f))


def clinic_subs(r):
    return sorted({p["substance_slug"] for p in clinic_plan_rows(r) if p.get("substance_slug")})


def shop_subs(r):
    return sorted({s["substance_slug"] for s in SELLER_SUBS.get(r["seller_slug"], []) if s.get("substance_slug")})


def sellers_filter(shops, clinics):
    """The filter block above the shops: substances the shops list (from seller_substances) and the clinics' plans
    carry, most shops first."""
    n_shop, n_clinic = {}, {}
    for r in shops:
        for s in shop_subs(r):
            n_shop[s] = n_shop.get(s, 0) + 1
    for r in clinics:
        for s in clinic_subs(r):
            n_clinic[s] = n_clinic.get(s, 0) + 1
    subs = sorted(set(n_shop) | set(n_clinic), key=lambda s: (-n_shop.get(s, 0), -n_clinic.get(s, 0), sub_label(s).lower()))
    def count(s):
        parts = [plural(n_shop[s], "shop")] if n_shop.get(s) else []
        return ", ".join(parts + ([plural(n_clinic[s], "clinic")] if n_clinic.get(s) else []))
    def short(s):  # the name without its bracket, as in the peptide page titles (owner answer Q3 a, 3 Nov 2026)
        return re.sub(r" *\(.*\)$", "", sub_label(s))
    opts = "".join(f'<option value="{s}">{escape(short(s))} ({count(s)})</option>' for s in subs)
    mins = "".join(f'<option value="{i}">{"Any" if i == 0 else f"{i} of {len(SCORE_CHECKS)}" if i == len(SCORE_CHECKS) else f"{i} or more"}</option>'
                   for i in range(len(SCORE_CHECKS) + 1))
    sorts = "".join(f'<option value="{k}">{t}</option>' for k, t in SELLER_SORTS)
    # each chip carries its count of clinics and of shops; the script shows the open tab's (owner task w2, 3 Nov 2026)
    chips = "".join(
        f'<button type="button" class="year-chip" data-check="{k}" data-filter="check" data-value="{k}" data-nc="{sum(bool(r.get(f)) for r in clinics)}" data-ns="{sum(bool(r.get(f)) for r in shops)}" aria-pressed="false">'
        f'{t} <span class="chip-n">{sum(bool(r.get(f)) for r in shops)}</span></button>'
        for k, f, t in SELLER_CHECKS)
    # phones (owner task 3 Nov 2026, the 390px walkthrough): the filters fold behind one "Filter" button, the count beside it
    return f"""<div class="letters-filter sellers-filter" hidden>
      <div class="filter-bar"><button type="button" class="btn btn-line btn-sm filter-toggle" aria-expanded="false" aria-controls="sellers-fbody">Filter</button></div>
      <div class="filter-body" id="sellers-fbody">
      <div class="sf-field sf-name"><label for="sellers-q">Filter by name</label><span class="sf-q"><input class="input" id="sellers-q" type="text" autocomplete="off" data-filter="name" data-value="text"><button type="button" class="sf-clear" id="sellers-clear">Clear</button></span></div>
      <div class="sf-field"><label for="sellers-sub">Substance</label><select class="input" id="sellers-sub" data-filter="substance"><option value="">Any substance</option>{opts}</select></div>
      <div class="sf-field"><label for="sellers-min">Minimum checks</label><select class="input" id="sellers-min" data-filter="min_checks">{mins}</select></div>
      <div class="sf-field sort-shops"><label for="sellers-sort">Sort</label><select class="input" id="sellers-sort" data-filter="sort">{sorts}</select></div>
      <span class="sf-field sort-clinics">{state_filter("clinics", "clinics")}</span>
      <div class="sf-field sort-clinics"><label for="clinics-sort">Sort</label><select class="input" id="clinics-sort" data-filter="sort"><option value="checks">Most checks</option><option value="low">Lowest monthly price</option></select></div>
      <span class="sf-break" aria-hidden="true"></span>
      <div class="year-chips" role="group" aria-labelledby="sellers-checks"><span id="sellers-checks">Checks met</span>{chips}</div>
      </div>
      <p class="small" id="sellers-n" aria-live="polite"></p>
    </div>"""


FILTER_FOLD_JS = """<script>
(function(){document.querySelectorAll('.filter-toggle').forEach(function(b){var p=document.getElementById(b.getAttribute('aria-controls'));if(!p)return;
b.addEventListener('click',function(){var o=b.getAttribute('aria-expanded')!=='true';b.setAttribute('aria-expanded',o?'true':'false');p.classList.toggle('open',o);});});})();
</script>"""
SELLERS_INDEX_JS = """<script>
// The sellers index (pages.md, Sellers; owner task w2, 3 Nov 2026): two tabs, clinics first, one filter block for both; the
// state in the hash (type, q, substance, min, check, sort, csort). Reads only the rows' data- attributes.
(function(){var tb=document.getElementById('sellers-table'),ct=document.getElementById('clinics-table'),f=document.querySelector('.sellers-filter');if(!f||(!tb&&!ct))return;
var tabs=document.querySelector('.sellers-tabs'),segs=tabs?[].slice.call(tabs.querySelectorAll('.seg-b')):[],
q=document.getElementById('sellers-q'),c=document.getElementById('sellers-clear'),m=document.querySelector('.sellers-more'),all=document.getElementById('sellers-all'),
n=document.getElementById('sellers-n'),sb=document.getElementById('sellers-sub'),mn=document.getElementById('sellers-min'),so=document.getElementById('sellers-sort'),
cs=document.getElementById('clinics-sort'),chips=[].slice.call(f.querySelectorAll('.year-chip')),
rows=tb?[].slice.call(tb.tBodies[0].rows):[],crows=ct?[].slice.call(ct.tBodies[0].rows):[],secS=document.getElementById('shops'),secC=document.getElementById('clinics'),
open=false,FIRST=FIRST_N,type=ct?'clinics':'shops';
rows.concat(crows).forEach(function(r,i){r._i=i;});
function num(r,k){var v=r.getAttribute('data-'+k);return v===''||v===null?null:parseFloat(v);}
function has(r,k,v){return(' '+r.getAttribute('data-'+k)+' ').indexOf(' '+v+' ')>=0;}
var SORT={checks:function(a,b){return a._i-b._i;},products:function(a,b){return num(b,'p')-num(a,'p')||a._i-b._i;},
price:function(a,b){var x=num(a,'m'),y=num(b,'m');return x===null?(y===null?a._i-b._i:1):y===null?-1:x-y||a._i-b._i;},
name:function(a,b){return a.getAttribute('data-n').localeCompare(b.getAttribute('data-n'));},
since:function(a,b){return a.getAttribute('data-t').localeCompare(b.getAttribute('data-t'))||a._i-b._i;},
low:function(a,b){var x=num(a,'low'),y=num(b,'low');return x===null?(y===null?a._i-b._i:1):y===null?-1:x-y||a._i-b._i;}};
function opt(el,v){return!!el&&!!el.querySelector('option[value="'+v+'"]');}
function on(){return chips.filter(function(x){return x.getAttribute('aria-pressed')==='true'&&!x.hidden;}).map(function(x){return x.getAttribute('data-check');});}
function hit(r,s,u,k,cks){return!r.hasAttribute('data-state-out')&&(!s||r.cells[0].textContent.toLowerCase().indexOf(s)>=0)&&(!u||has(r,'subs',u))&&num(r,'s')>=k
&&cks.every(function(x){return has(r,'c',x);});}
function save(){var h=[],cks=on();if(type==='shops'&&ct)h.push('type=shops');if(q.value.trim())h.push('q='+encodeURIComponent(q.value.trim()));if(sb.value)h.push('substance='+sb.value);
if(mn.value!=='0')h.push('min='+mn.value);if(cks.length)h.push('check='+cks.join(','));if(so&&so.value!=='checks')h.push('sort='+so.value);
if(cs&&cs.value!=='checks')h.push('csort='+cs.value);var u=location.pathname+location.search+(h.length?'#'+h.join('&'):'');
if(u!==location.pathname+location.search+location.hash)history.replaceState(null,'',u);}
function load(){var hs=location.hash.slice(1);
if(hs.indexOf('=')<0){if(hs==='shops'&&tb)type='shops';else if(hs==='clinics'&&ct)type='clinics';return;}
var P=new URLSearchParams(hs),cks=(P.get('check')||'').split(','),t=P.get('type');
q.value=P.get('q')||'';sb.value=opt(sb,P.get('substance'))?P.get('substance'):'';mn.value=opt(mn,P.get('min'))?P.get('min'):'0';
if(so)so.value=opt(so,P.get('sort'))?P.get('sort'):'checks';if(cs)cs.value=opt(cs,P.get('csort'))?P.get('csort'):'checks';
chips.forEach(function(x){x.setAttribute('aria-pressed',cks.indexOf(x.getAttribute('data-check'))>=0?'true':'false');});
// Home's "See all" sends type=clinic or type=shop; a substance link without a type opens the tab that carries it
type=(t==='shops'||t==='shop')&&tb?'shops':(t==='clinics'||t==='clinic')&&ct?'clinics':ct?'clinics':'shops';
if(!t&&sb.value&&ct&&tb&&!crows.some(function(r){return has(r,'subs',sb.value);}))type='shops';}
function mins(){var c=type==='clinics';[].forEach.call(mn.options,function(o){if(o.value==='5'){o.hidden=c;o.disabled=c;}if(o.value==='4')o.textContent=c?'4 of 4':'4 or more';});if(c&&mn.value==='5')mn.value='4';}
function draw(){mins();var s=q.value.trim().toLowerCase(),u=sb.value,k=parseInt(mn.value,10),cl=type==='clinics',
any=false,j=0,R=cl?crows:rows,T=cl?ct:tb;
segs.forEach(function(b){b.setAttribute('aria-pressed',b.getAttribute('data-type')===type?'true':'false');});
if(secC)secC.hidden=!cl;if(secS)secS.hidden=cl;
[].forEach.call(f.querySelectorAll('.sort-shops'),function(x){x.hidden=cl;});[].forEach.call(f.querySelectorAll('.sort-clinics'),function(x){x.hidden=!cl;});
chips.forEach(function(x){x.hidden=cl&&x.getAttribute('data-check')==='lab';x.querySelector('.chip-n').textContent=x.getAttribute(cl?'data-nc':'data-ns');});
var cks=on();any=!!(s||u||k||cks.length);
R.sort(SORT[cl?cs.value:so.value]).forEach(function(r){T.tBodies[0].appendChild(r);var ok=hit(r,s,u,k,cks);
r.hidden=!ok||(!cl&&!open&&!any&&j>=FIRST);if(ok)j++;r.style.opacity=1;});
if(m)m.hidden=cl||open||any||rows.length<=FIRST;n.textContent=any?j+' of '+R.length+(cl?' clinics':' shops')+' match.':'';}
function ch(){draw();save();}
f.hidden=false;if(tabs)tabs.hidden=false;load();
q.addEventListener('input',ch);[sb,mn,so,cs].forEach(function(x){if(x)x.addEventListener('change',ch);});
chips.forEach(function(x){x.addEventListener('click',function(){x.setAttribute('aria-pressed',x.getAttribute('aria-pressed')==='true'?'false':'true');ch();});});
segs.forEach(function(b){b.addEventListener('click',function(){type=b.getAttribute('data-type');ch();});});
c.addEventListener('click',function(){q.value='';sb.value='';mn.value='0';chips.forEach(function(x){x.setAttribute('aria-pressed','false');});ch();q.focus();});
window.addEventListener('hashchange',function(){load();draw();});
document.addEventListener('pc-state',draw);
if(all)all.addEventListener('click',function(){open=true;draw();});draw();})();
</script>""".replace("FIRST_N", str(SELLERS_FIRST))


def subs_words(names, total=None, n=3):
    """"BPC-157, TB-500, GHK-Cu and 35 more": the first names, then how many more of `total` (default: the names)."""
    short = [re.sub(r" *\(.*\)$", "", sub_label(x)) for x in names]
    rest = max(total or 0, len(short)) - min(n, len(short))
    return ", ".join(short[:n]) + (f" and {rest} more" if rest > 0 else "") if short else "Not named"


def check_bar(r):
    """"4 of 5" (a clinic: "3 of 4") and the seller's checks as a bar of miniature marks (the Background check card's chips at 10px; pages.md,
    Sellers), each spoken."""
    marks = "".join(f'<span class="chip chip-{"ok" if r.get(k) else "neutral"} mark-{"yes" if r.get(k) else "no"}">'
                    f'<span class="vh">{t}: {"yes" if r.get(k) else "no"}</span></span>' for k, t in seller_checks(r))
    return f'<span class="num">{score_of(r)} of {out_of(r)}</span><span class="check-bar">{marks}</span>'


ACT_TH = '<th scope="col"><span class="vh">Our page</span></th>'


def sellers_index():
    """/sellers/ (pages.md, Sellers; owner task w2, 3 Nov 2026): two tabs, the online clinics first, then the shops."""
    shops = sorted(SHOPS.values(), key=sellers_order)
    clinics = sorted(CLINIC_PROFILES.values(), key=lambda r: (-(r.get("score") or 0), seller_name(r).lower()))
    me = sys.modules[__name__]
    more_cls = ' class="more"'
    strs = "".join(
        f'<tr{more_cls if i >= SELLERS_FIRST else ""} data-c="{met_checks(r)}" data-s="{r["score"]}" data-subs="{" ".join(shop_subs(r))}"'
        f' data-p="{r.get("product_count") or 0}" data-m="{compare_ppm(r)[0] if compare_ppm(r)[0] is not None else ""}"'
        f' data-n="{escape(seller_name(r).lower())}" data-t="{r.get("first_seen") or ""}">'
        f'<td><span class="cell-pic">{parts.tile(r["seller_slug"], seller_base(seller_name(r)), 40, shop=True)}<a class="name" href="/sellers/{r["seller_slug"]}/">{seller_name(r)}</a></span></td>'
        f'<td data-l="Sells">{escape(subs_words([x["substance_slug"] for x in SELLER_SUBS.get(r["seller_slug"], [])], r.get("substance_count")))}</td>'
        f'<td class="num" data-l="From">{per_mg(compare_ppm(r)[0]) + "/mg" if compare_ppm(r)[0] is not None else "unknown"}</td>'
        f'<td data-l="Checks">{check_bar(r)}</td><td data-l="FDA letters">{home.where_letters(me, r)}</td>'
        f'<td class="act"><a class="btn btn-line btn-sm" href="/sellers/{r["seller_slug"]}/">Our review</a></td></tr>'
        for i, r in enumerate(shops))
    checked = max((r["score_checked_on"] for r in PROFILES.values() if r.get("score_checked_on")), default="")
    more = (f'<p class="legal-more sellers-more" hidden><button type="button" class="btn btn-line" id="sellers-all">Show all {len(shops)}</button></p>'
            if len(shops) > SELLERS_FIRST else "")
    lede = (f"{plural(len(clinics), 'online clinic')} that prescribe and ship, then {plural(len(shops), 'research-use shop')}." if clinics else
            f"{plural(len(shops), 'research-use shop')}.")
    tabs = ("<div class=\"seg sellers-tabs\" role=\"group\" aria-label=\"Show\" hidden>"
            f'<button type="button" class="seg-b" data-type="clinics"{ev("tab_change", tab="clinics")} aria-pressed="true">Online clinics ({len(clinics)})</button>'
            f'<button type="button" class="seg-b" data-type="shops"{ev("tab_change", tab="shops")} aria-pressed="false">Research-use shops ({len(shops)})</button></div>') if clinics and shops else ""
    shops_sec = f"""
    <section class="sellers-sec" id="shops" aria-labelledby="shops-h">
      <h2 id="shops-h" class="h-sources">Research-use shops</h2>
      <div class="tbl-wrap"><table class="tbl tbl-cards tbl-sellers tbl-where" id="sellers-table"><caption class="vh">Research-use shops, most checks first</caption>
        <thead><tr><th scope="col">Shop</th><th scope="col">Sells</th><th scope="col">From</th><th scope="col">Checks</th><th scope="col">FDA letters</th>{ACT_TH}</tr></thead>
        <tbody>{strs}</tbody>
      </table></div>
      {more}
    </section>""" if shops else ""
    return f"""
<section class="section letters-hd">
  <div class="wrap">
    <h1>Peptide sellers we track</h1>
    <p class="lede">{lede}</p>
    <p class="letters-stamp">{f'<span class="stamp">Checked {nice_date(checked)}</span>' if checked else ""}</p>
  </div>
</section>
<section class="band-2" id="sellers-list">
  <div class="wrap">
    <div class="sellers-top">{tabs}
    {sellers_filter(shops, clinics)}</div>
    {clinics_directory(clinics)}{shops_sec}
    {COMPARE_LINK}
    <p class="small" style="margin-top:16px">Checks are facts we hold about the seller, not a safety or quality grade. <a href="/how-we-rate/">How we rate</a></p>
  </div>
</section>
{SELLERS_INDEX_JS}
{FILTER_FOLD_JS}
"""


def clinics_directory(clinics):
    """The online clinics table on /sellers/ (pages.md, Sellers): the first tab, first in the HTML."""
    if not clinics:
        return ""
    me = sys.modules[__name__]
    trs = []
    for r in clinics:
        plans = clinic_plan_rows(r)
        low = min((float(p["price_monthly"]) for p in plans), default=None)
        trs.append(f'<tr{state_attrs(r["seller_slug"])} data-c="{met_checks(r)}" data-s="{r["score"]}" data-subs="{" ".join(clinic_subs(r))}" data-low="{low if low is not None else ""}">'
                   f'<td><span class="cell-pic">{parts.tile(r["seller_slug"], seller_base(seller_name(r)), 40, seller=r)}<a class="name" href="/sellers/{r["seller_slug"]}/">{seller_name(r)}</a></span></td>'
                   f'<td data-l="What it prescribes">{escape(subs_words(sorted(clinic_subs(r), key=lambda x: sub_label(x).lower())))}</td>'
                   f'<td class="num" data-l="From">{usd(low) + "/mo" if low is not None else "unknown"}</td>'
                   f'<td data-l="Checks">{check_bar(r)}</td><td data-l="FDA letters">{home.where_letters(me, r)}</td>'
                   f'<td class="act">{clinic_button(r["seller_slug"], "See plans", in_table=True)}</td></tr>')
    return f"""
    <section class="sellers-sec" id="clinics" aria-labelledby="clinics-h">
      <h2 id="clinics-h" class="h-sources">Online clinics</h2>{STATE_N}
      <div class="tbl-wrap"><table class="tbl tbl-cards tbl-sellers tbl-where" id="clinics-table"><caption class="vh">Online clinics, most checks first</caption>
        <thead><tr><th scope="col">Clinic</th><th scope="col">What it prescribes</th><th scope="col">From</th><th scope="col">Checks</th><th scope="col">FDA letters</th>{ACT_TH}</tr></thead>
        <tbody>{"".join(trs)}</tbody>
      </table></div>
      <p class="small sellers-note">Online clinics publish no lab reports, so a clinic is checked on four facts, a shop on five. A score is never compared across the two kinds.</p>
    </section>"""


# 404 (pages.md, 404; owner task 2 Nov 2026): the goal pages, then the sections that exist, and the search line.
_NF_MORE = [("/sellers/", "Sellers we track", PROFILES), ("/peptides/", "Peptides A to Z", PEPTIDE_SLUGS), ("/learn/", "Guides", True)]
NOT_FOUND = f"""
<section class="page"><div class="wrap prose">
<h1>This page doesn't exist</h1>
<p class="lede">The link may be old or mistyped. Try the search above.</p>
<div class="btn-row"><a class="btn btn-ink" href="/">Go to the home page</a></div>
<ul class="nf-links">{"".join(f'<li><a href="{goal_href(g)}">{g["label"]}</a></li>' for g in CHOOSER_GOALS)}</ul>
<ul class="nf-links">{"".join(f'<li><a href="{u}">{t}</a></li>' for u, t, ok in _NF_MORE if ok)}</ul>
</div></section>
"""

PAGES = [
    ("/", "index.html", "Best peptides by goal, compared | Peptide Chooser",
     HOME_DESC, HOME, ORG_SCHEMA, None),
    ("/about/", "about/index.html", "About Peptide Chooser",
     "Peptide Chooser is an independent site that compares peptide products and sellers for people in the United States.", ABOUT, "", [("/about/", "About")]),
    ("/how-we-rate/", "how-we-rate/index.html", "How we rate peptide products and sellers | Peptide Chooser",
     "The checks Peptide Chooser runs on every peptide seller (lab reports for shops, FDA letters, company, legal pages, fresh prices) and how goal pages are built.", HOW, "", [("/how-we-rate/", "How we rate")]),
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
                      category_page(_g), faq_schema(goal_faq_pairs(_g)), [(f"/{_g['slug']}/", _g["name"])]))

if PROFILES:
    PAGES.append(("/sellers/", "sellers/index.html", "Peptide sellers and their checks | Peptide Chooser",
                  (f"The {len(SHOPS)} peptide shops and {len(CLINIC_PROFILES)} online clinics in our database, each on its own page "
                   "with background checks, products or plans and FDA warning letters.") if CLINIC_PROFILES else
                  (f"Every peptide seller in our database, {len(PROFILES)} in all, each on its own page with five background checks, "
                   "product and substance counts and FDA warning letters."),
                  sellers_index(),
                  # ItemList (owner task 2 Nov 2026): one item per seller page on our site, never the seller's own domain
                  item_list_schema("Peptide sellers and their checks",
                                   [(seller_name(r), f"{SITE}/sellers/{r['seller_slug']}/") for r in sorted(PROFILES.values(), key=lambda x: x["seller_slug"])]),
                  [("/sellers/", "Sellers")]))
    for _r in sorted(PROFILES.values(), key=lambda x: x["seller_slug"]):
        PAGES.append((f"/sellers/{_r['seller_slug']}/", f"sellers/{_r['seller_slug']}/index.html", seller_title(_r),
                      legit_description(clinic_description(_r) if _r["seller_slug"] in CLINIC_PROFILES else seller_description(_r), _r), seller_page(_r),
                      seller_org_schema(_r) + faq_schema(seller_faq_pairs(_r)[1]),
                      [("/sellers/", "Sellers"), (f"/sellers/{_r['seller_slug']}/", seller_name(_r))]))


# Site search and "Compare any two" (pages.md, Every page, Header, Search; Search; Compare; owner task 2 Nov 2026).
# /search-index.json holds one entry per page, substance with a database status and seller; the header field and /search/
# filter it in the page. /compare/ puts two clinic plans or two sellers side by side from data embedded in the page.
NOINDEX = {"/search/"}
# a comparison before a guide of the same name (owner UX audit, 3 Nov 2026: "BPC-157 vs TB-500" listed twice alike)
TYPE_ORDER = {"Goal": 0, "Peptide": 1, "Seller": 2, "Clinic": 3, "Comparison": 4, "Guide": 5, "Page": 6}


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
            kind = ("Comparison" if re.match(r"/compare/[^/]+-vs-[^/]+/$", path) else
                    "Guide" if path.startswith("/learn/") and path != "/learn/" else "Page")
            line = desc.split(". ")[0].rstrip(".") + "."
            out.append({"type": kind, "name": "Home" if path == "/" else title.replace(" | Peptide Chooser", ""), "aliases": [],
                        "url": path, "line": f"{kind}: {line}" if kind != "Page" else line})
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
                    "url": f"/sellers/{r['seller_slug']}/", "line": f"Online clinic, {card_count(r)}, {score_of(r)} of {out_of(r)} checks"})
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
    # with a query the results take the first screen: its height is reserved before the first paint, so the goals strip
    # under the form does not jump when they arrive (Lighthouse, CLS 0.388, 4 Nov 2026; pages.md, Search)
    return f"""
<script>if(/[?&]q=./.test(location.search))document.documentElement.classList.add('has-q');</script>
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
    chip, label = ("info", f"Brand, {use}") if use else kind_chip(r)
    n = r.get("fda_letter_count") or 0
    letter = (f'<a class="chip chip-warn chip-link" href="{letter_href(r["seller_slug"])}">FDA letter {nice_date(r["last_fda_letter_date"])}</a>'
              if n and r.get("last_fda_letter_date") else "None")
    fee = r.get("membership_fee_monthly")
    care = "Not known" if fee is None else "None, all-in" if float(fee) == 0 else f"{usd(fee)}/mo, included"
    return {"k": "plan", "h": f'{parts.tile(r["seller_slug"], seller_base(r["seller_name"]), 40, seller=PROFILES.get(r["seller_slug"]))}{who}<span class="cmp-sub">{escape(r["plan_name"])}</span>', "c": [
        ("Per month", f'<span class="num">{usd(r["price_monthly"])}/mo</span>'),
        ("Care fee", care),
        ("What it is", f'<span class="chip chip-{chip}">{label}</span>'),
        ("Substance", escape(sub_label(r["substance_slug"])) if r.get("substance_slug") else "Names no medication"),
        ("FDA letter", letter),
        ("Prices checked", nice_date(r["last_seen"]))]}


def compare_seller(r):
    """One seller's column: the head (a link to its page) and the seven rows (pages.md, Compare)."""
    marks = "".join(f'<span class="chip chip-{"ok" if r.get(k) else "neutral"} mark-{"yes" if r.get(k) else "no"}">'
                    f'<span class="vh">{t}: {"yes" if r.get(k) else "no"}</span><span aria-hidden="true">{t}</span></span>' for k, t in SCORE_CHECKS)
    ppm = per_mg_range(*compare_ppm(r))
    ppm = ppm[:1].upper() + ppm[1:]
    n = r.get("fda_letter_count")
    letters = ("None" if n == 0 else "Unknown" if n is None else
               f"{n}, the newest on {nice_date(newest_letter(r))}" if newest_letter(r) else str(n))
    state = STATES.get(r.get("entity_state") or "", r.get("entity_state") or "")
    company = ("No registered company found" if not shown_company(r) else
               f'{escape(clean(r["entity_name"]))}{", " + state if state else ""}'
               f'<span class="cmp-sub">{"State registry" if r["entity_evidence"] == "registry" else "Named in an FDA letter"}</span>')
    return {"k": "seller", "h": f'{parts.tile(r["seller_slug"], seller_base(seller_name(r)), 40, shop=True)}<a class="name" href="/sellers/{r["seller_slug"]}/">{escape(seller_name(r))}</a><span class="cmp-sub">{kind_words(r)[1]}</span>', "c": [
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
// Compare any two (pages.md, Compare any two; owner task w2, 3 Nov 2026): each select becomes a text field with a
// grouped list under it (the header search's list part; arrows, Enter, Escape); two substances with a pair page open
// that page; otherwise the two columns are drawn from /compare/data.json. Without JavaScript the selects submit.
(function(){var D={},f=document.getElementById('cmp-form'),a=f.elements.a,b=f.elements.b,
out=document.getElementById('cmp-out'),p=new URLSearchParams(location.search);
function label(s){return s.selectedIndex>0?s.options[s.selectedIndex].text:'';}
function pick(sel){var w=sel.parentNode,inp=document.createElement('input'),ul=document.createElement('ul'),act=-1,res=[],id=sel.id+'-list';
inp.className='input';inp.type='text';inp.id=sel.id+'-q';inp.autocomplete='off';inp.placeholder='Type a plan, shop or substance';
inp.setAttribute('role','combobox');inp.setAttribute('aria-expanded','false');inp.setAttribute('aria-controls',id);inp.setAttribute('aria-autocomplete','list');
ul.className='search-list cmp-list';ul.id=id;ul.setAttribute('role','listbox');ul.hidden=true;
w.querySelector('label').setAttribute('for',inp.id);sel.hidden=true;sel.tabIndex=-1;w.appendChild(inp);w.appendChild(ul);
var items=[].slice.call(sel.querySelectorAll('option')).filter(function(o){return o.value;}).map(function(o){return{v:o.value,t:o.text,g:o.parentNode.label||''};});
function close(){ul.hidden=true;inp.setAttribute('aria-expanded','false');inp.removeAttribute('aria-activedescendant');act=-1;}
function choose(x){sel.value=x.v;inp.value=x.t;close();if(window.pcEv)pcEv('compare_pick',{kind:(D[x.v]||{}).k});}
// names that start with what was typed come first, then the others, each in group order
function draw(){var q=inp.value.trim().toLowerCase(),st=function(x){return q&&x.t.toLowerCase().indexOf(q)===0?0:1;};
res=items.filter(function(x){return!q||x.t.toLowerCase().indexOf(q)>=0;}).map(function(x,i){return[st(x),i,x];})
.sort(function(m,n){return m[0]-n[0]||m[1]-n[1];}).map(function(m){return m[2];}).slice(0,60);
ul.textContent='';act=-1;var g=null;res.forEach(function(x,i){if(x.g!==g){g=x.g;var h=document.createElement('li');h.className='cmp-group';h.setAttribute('role','presentation');h.textContent=g;ul.appendChild(h);}
var li=document.createElement('li');li.id=id+'-'+i;li.setAttribute('role','option');li.setAttribute('aria-selected','false');li.textContent=x.t;
li.addEventListener('mousedown',function(e){e.preventDefault();choose(x);});ul.appendChild(li);});
if(!res.length){var n=document.createElement('li');n.className='search-none';n.textContent='No match.';ul.appendChild(n);}
ul.hidden=false;inp.setAttribute('aria-expanded','true');}
function mark(i){var o=ul.querySelectorAll('[role=option]');if(!o.length)return;act=(i+o.length)%o.length;
for(var j=0;j<o.length;j++)o[j].setAttribute('aria-selected',j===act?'true':'false');inp.setAttribute('aria-activedescendant',o[act].id);o[act].scrollIntoView({block:'nearest'});}
inp.addEventListener('input',function(){sel.value='';draw();});inp.addEventListener('focus',draw);
inp.addEventListener('keydown',function(e){if(e.key==='ArrowDown'){e.preventDefault();if(ul.hidden)draw();else mark(act+1);}
else if(e.key==='ArrowUp'){e.preventDefault();mark(act-1);}
else if(e.key==='Enter'&&!ul.hidden&&act>=0){e.preventDefault();choose(res[act]);}
else if(e.key==='Escape'&&!ul.hidden){e.preventDefault();close();}});
inp.addEventListener('blur',function(){setTimeout(close,100);});
return function(){inp.value=label(sel);};}
var sa=pick(a),sb=pick(b);
function pair(){var P=D._pairs||{};return P[a.value+'|'+b.value]||P[b.value+'|'+a.value];}
function show(){var x=D[a.value],y=D[b.value];if(!x||!y){out.innerHTML='<p class="cmp-note">Choose two to see them side by side.</p>';return;}
if(x.k!==y.k){out.innerHTML='<p class="cmp-note">Choose two of the same kind: two clinic plans, two shops or two substances.</p>';return;}
var h='<table class="cmp"><caption class="vh">'+label(a)+' and '+label(b)+'</caption><thead><tr><td></td><th scope="col">'+x.h+'</th><th scope="col">'+y.h+'</th></tr></thead><tbody>';
x.c.forEach(function(c,i){h+='<tr><th scope="row">'+c[0]+'</th><td>'+c[1]+'</td><td>'+y.c[i][1]+'</td></tr>';});
out.innerHTML=h+'</tbody></table>';}
f.addEventListener('submit',function(e){e.preventDefault();var to=pair();if(to){location.href=to;return;}
history.replaceState(null,'','/compare/?a='+encodeURIComponent(a.value)+'&b='+encodeURIComponent(b.value));show();});
out.hidden=false;out.innerHTML='<p class="cmp-note">Loading the plans, shops and substances.</p>';
// the facts load once, after the page (/compare/data.json), so the page itself stays small (design/site-polish)
fetch('/compare/data.json').then(function(r){return r.json();}).then(function(d){D=d;
if(D[p.get('a')])a.value=p.get('a');if(D[p.get('b')])b.value=p.get('b');sa();sb();show();})
.catch(function(){out.innerHTML='<p class="cmp-note">The comparison could not load. Open each seller from <a href="/sellers/">the sellers we track</a>.</p>';});})();
</script>"""


COMPARE_DATA = ""


def compare_page():
    plans, sellers = compare_items()
    data = {k: v for k, _, v in plans + sellers}
    opts = lambda items: "".join(f'<option value="{k}">{escape(label)}</option>' for k, label, _ in items)
    # three groups (owner task w2, 3 Nov 2026): the substances join after the pair pages are built (cmp_links_in)
    groups = ((f'<optgroup label="Online clinic plans">{opts(plans)}</optgroup>' if plans else "")
              + (f'<optgroup label="Research-use shops">{opts(sellers)}</optgroup>' if sellers else "") + "<!--cmp-subs-->")
    select = lambda name, label: (f'<div class="cmp-field"><label for="cmp-{name}">{label}</label><select class="input" id="cmp-{name}" name="{name}">'
                                  f'<option value="">Choose a plan, shop or substance</option>{groups}</select></div>')
    checked = max([r["last_seen"] for r in PLANS if r.get("last_seen")] + [r["score_checked_on"] for r in PROFILES.values() if r.get("score_checked_on")], default="")
    global COMPARE_DATA
    COMPARE_DATA = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"""
<section class="section letters-hd">
  <div class="wrap">
    <h1>Compare any two plans or sellers</h1>
    <p class="lede">Pick two online clinic plans, two peptide shops or two substances and see them side by side: price and care fee for a plan; the five checks, products, price per mg and FDA letters for a shop; FDA status, prices and letters for a substance. Seller names open our page on the seller.</p>
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
                "fda_nomination_withdrawn": "503A nomination", "fda_shortage": "Shortage list",
                "hhs_503a_interim": "HHS compounding policy"}
VALUE_WORDS = {"approved": "approved", "category_1": "category 1", "category_2": "category 2", "category_3": "category 3",
               "withdrawn": "withdrawn", "listed": "listed", "enforcement_discretion": "listed", "in_shortage": "in shortage", "to_be_discontinued": "to be discontinued"}
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
            "seen": r.get("checked") or LEGAL["checked"], "hand": True}


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
    return [] if pep_group(s) == "approved" else seller_rows(slug, "research")  # the research-use window's rows


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


def pep_answer(slug, first=None):
    """The short answer, one sentence per fact, each with its link; a missing fact drops its sentence. The price sentence
    names the seller shown first in "Where to get it" (`first`; owner task 3 Nov 2026), else the cheapest."""
    s = pep_status(slug)
    host = source_word(s["url"])
    links = (" and ".join(f'<a href="{escape(x["url"])}" rel="nofollow">{source_word(x["url"])}</a>' for x in s["routes"])
             if s.get("routes") else f'<a href="{escape(s["url"])}" rel="nofollow">{host}</a>')
    out = [f'{s["label"]}: {s["sentence"]}. {links}, {nice_date(s["seen"])}.']
    n = len(pep_status_rows(slug))
    if n > 1:  # several current rows, each a line in the facts card (owner task 2 Nov 2026)
        who = "The FDA lists it" if not any(r["regime"] == "hhs_503a_interim" for r in pep_status_rows(slug)) else "The FDA and HHS list it"
        out.append(f'{who} in {n} places; <a href="#facts-h">see the facts</a>.')
    goals = list(dict.fromkeys(g["slug"] for g, _ in pep_goals(slug)))
    if goals:
        gs = [next(g for g in ALL_GOALS if g["slug"] == x) for x in goals]
        links = [f'<a href="/{g["slug"]}/">{g["name"].lower()}</a>' for g in gs]
        joined = links[0] if len(links) == 1 else ", ".join(links[:-1]) + " and " + links[-1]
        out.append(f'Our {joined} page{"s list" if len(links) > 1 else " lists"} it.')
    low = first if first is not None and pep_group(s) != "approved" and first.get("price_per_mg") is not None else (pep_low_shop(slug) if first is None else None)
    if low:
        n = len({r["seller_slug"] for r in pep_shops(slug)})
        seen = low.get("price_observed_at") or low.get("last_seen")
        sc = SELLERS.get(low["seller_slug"], {}).get("score")
        out.append(f'The best-checked of the {plural(n, "shop")} shown below{f" ({sc} of {len(SCORE_CHECKS)} checks)" if sc is not None else ""} lists it at {per_mg(low["price_per_mg"])}/mg '
                   f'({clinic_link(low["seller_slug"], seller_base(clean(SELLERS.get(low["seller_slug"], {}).get("seller_name") or low["seller_name"])), True)})'
                   f'{", checked " + nice_date(seen) if seen else ""}.')
    n = len(LETTER_SUBS.get(slug, [])) if pep_group(s) != "approved" else 0
    # an approved medicine's letters are about sellers, not its approval: the count stays in the letters section (owner
    # UX audit B15, 3 Nov 2026)
    if n:  # the count of letters that name it (owner task 2 Nov 2026), linking the section below
        out.append(f'<a href="#letters">{plural(n, "FDA warning letter")}</a> name{"s" if n == 1 else ""} it.')
    p = (first or pep_low_plan(slug)) if pep_group(s) == "approved" else None
    if p:
        out.append(f'The first plan below, the lowest {"compounded plan" if p.get("product_kind") == "compounded" else "monthly plan that is not compounded"} at the online clinics we track, is {usd(p["price_monthly"])} '
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
    # the HHS policy's long note does not fit a description; its short form does (legal.hhs_policy.meta)
    parts = [f'{n}{f" ({NAMES[slug][0]})" if NAMES.get(slug) else ""}: {s["label"]}, {HHS["meta"] if HHS and s["sentence"] in (HHS["note"], HHS["note_many"]) else s.get("meta") or s["sentence"]}.']
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
        # the date is measured at its widest ("30 Sep 2026"), so a short date never adds the sentence
        # and a long one never drops it: the words of the description stay the same from day to day
        fit = len("Checked 30 Sep 2026.") if x.startswith("Checked ") else len(x)
        if len(out) + 1 + fit <= 160:
            out += " " + x
    return out


def pep_chips(slug, s):
    rx = pep_rx(slug, s)[1]
    rx = f'<span class="chip chip-neutral">{rx}</span>' if rx else ""
    return (f'<p class="pep-chips"><span class="chip chip-{s["chip"]}">{s["label"]}</span>{rx}'
            f'<span class="stamp">Checked {nice_date(pep_checked(slug))}</span></p>')


def pep_status_rows(slug):
    """The substance's current status rows (a status the legal tables know), newest first."""
    rows = [r for r in pep_db_rows(slug) if (r["regime"], r["status_value"]) in DB_STATUS]
    return sorted(rows, key=lambda r: (r.get("valid_from") or r.get("first_seen_by_us") or "", r["regime"]), reverse=True)


# Each list entry in plain words (owner UX audit A22 and A23, 3 Nov 2026: "503A nomination: Not approved withdrawn (503A)"
# and "FDA approved approved"): (row name, sentence). The date is the list's own date, else the day we first saw it.
PLAIN_STATUS = {
    ("fda_approval", "approved"): ("FDA approval", "An approved product is listed in Drugs@FDA"),
    ("fda_nomination_withdrawn", "withdrawn"): ("Pharmacy compounding", "Not on the list of substances pharmacies may compound; its nomination was withdrawn"),
    ("hhs_503a_interim", "listed"): ("HHS compounding policy", HHS.get("note", "")[:1].upper() + HHS.get("note", "")[1:]),
    ("hhs_503a_interim", "enforcement_discretion"): ("HHS compounding policy", HHS.get("note", "")[:1].upper() + HHS.get("note", "")[1:]),
    ("fda_503a_category", "category_1"): ("Pharmacy compounding", "On the list of substances pharmacies may compound while the FDA reviews it"),
    ("fda_503a_category", "category_2"): ("Pharmacy compounding", "On the FDA list of substances with safety concerns; pharmacies may not compound it"),
    ("fda_503a_category", "category_3"): ("Pharmacy compounding", "Nominated without enough data; pharmacies may not compound it"),
    ("fda_cat2_safety", "category_2"): ("Outsourcing facilities", "On the FDA list of substances with safety concerns; outsourcing facilities (503B) may not compound it"),
    ("fda_shortage", "in_shortage"): ("Shortage list", "On the FDA shortage list"),
    ("fda_shortage", "to_be_discontinued"): ("Shortage list", "On the FDA shortage list as to be discontinued"),
}


def list_words(r):
    """(row name, sentence) for one database list entry, from PLAIN_STATUS, the form it applies to and its date."""
    name, said = PLAIN_STATUS.get((r["regime"], r["status_value"]), (REGIME_WORDS.get(r["regime"], "FDA list"), fact_words(r)))
    if r["regime"] == "fda_cat2_safety" and r.get("scope") == "503A":
        name, said = "Pharmacy compounding", "On the FDA list of substances with safety concerns; pharmacies may not compound it"
    form = f' for the {r["scope"]}' if r["regime"] == "fda_shortage" and r.get("scope") else ""
    day = r.get("valid_from") or r.get("first_seen_by_us")
    return name, f"{said}{form}{f' ({nice_date(day)})' if day else ''}."


def fact_words(r):
    """A list entry in the database's words: "category 1 (scope), since 1 Jan 2024"."""
    v = VALUE_WORDS.get(r["status_value"], r["status_value"].replace("_", " "))
    scope = f' ({r["scope"]})' if r.get("scope") and r["regime"] != "fda_approval" else ""
    since = f', since {nice_date(r["valid_from"])}' if r.get("valid_from") else ""
    return f"{v}{scope}{since}"


def pep_brands(slug):
    return sorted({brand_base(a["brand_name"]) for a in APPROVED_DB if a["substance_slug"] == slug and a.get("brand_name")}
                  - {pep_short(slug).split()[0].title()})


def pep_facts(slug, s):
    """The facts ledger in the Background check card's frame: FDA status and every open list entry in the database's
    words, the approved brands, forms, prescription needed, first seen by us."""
    rows = [("FDA status", f'<span class="chip chip-{s["chip"]}">{s["label"]}</span>')]
    # every current status row on its own line, newest first: its chip, the FDA's wording and its source (owner task
    # 2 Nov 2026; GHK-Cu is on the 503A list and has a withdrawn nomination, each with its own wording)
    for r in pep_status_rows(slug):
        chip, label = DB_STATUS[(r["regime"], r["status_value"])][1:3]
        listing = f'<span class="listing">FDA listing: "{escape(r["fda_listing"])}"</span>' if r.get("fda_listing") else ""
        host = source_word(r["source_url"])
        name, said = list_words(r)
        rows.append((name, f'<span class="chip chip-{chip}">{label}</span> {said}{listing}'
                     f' <a href="{escape(r["source_url"])}" rel="nofollow">{host}</a>'))
    for r in sorted(pep_db_rows(slug), key=lambda r: r["regime"]):
        if r["regime"] not in REGIME_WORDS or (r["regime"], r["status_value"]) in DB_STATUS:
            continue
        rows.append(list_words(r))
    brands = pep_brands(slug)
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


# Above an approved medicine's letters (owner UX audit B15, 3 Nov 2026)
APPROVED_LETTERS_LINE = "<p>These letters are about sellers and advertising, not about the medicine's approval.</p>"


def approved_evidence(slug, p):
    """An approved medicine's evidence cell instead of "Not rated" (owner UX audit B15): "FDA approved for <use>
    (Drugs@FDA, <date>)", the use from the goal page's own checked line, the date the first approval in Drugs@FDA, else
    the day the status was seen. None when the goal's line names no use."""
    use = re.search(r"FDA approved for ([^.;]+)", p.get("status_plain", ""))
    if not use or pep_group(pep_status(slug)) != "approved":
        return None
    # the date only of the brand the option names ("Semaglutide (Wegovy)": Wegovy's approval, not Ozempic's 2017 one for
    # diabetes); an option that names no brand in Drugs@FDA shows no date
    named = {w.lower() for w in re.findall(r"[A-Za-z]+", p.get("name", ""))}
    day = min((a["approval_date"] for a in APPROVED_DB if a["substance_slug"] == slug and a.get("approval_date")
               and a.get("brand_name") and brand_base(a["brand_name"]).lower() in named), default=None)
    return f'<span class="chip chip-ok">FDA approved</span> <span class="small">for {use.group(1)} (Drugs@FDA{", " + nice_date(str(day)[:10]) if day else ""})</span>'


def pep_evidence(slug, src):
    """One row per goal page option that carries the substance: the goal, the option, its evidence chip (from the goal's
    checked options table when it has one) and the line that page shows for it, with that page's sources."""
    trs = []
    for g, p in pep_goals(slug):
        o = next((o for o in g.get("options") or [] if o["name"] == p["name"] or o.get("substance") == slug and subs_of(p) == [slug]
                  or subs_of(p) == [slug] and sub_label(slug).lower().split()[0] in o["name"].lower()), None)
        chip = (f'<span class="chip chip-{o["evidence_chip"]}">{o["evidence"]}</span>' if o else
                approved_evidence(slug, p) or '<span class="small">Not rated</span>')
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


def shop_checks(r):
    """"N of 5 checks" in one line for a compact table (the five marks are on the seller's page), or "not checked yet"."""
    sc = SELLERS.get(r["seller_slug"], {}).get("score")
    return f'<span class="num">{sc}</span> of {len(SCORE_CHECKS)} checks' if sc is not None else "not checked yet"


def pep_shops_section(slug):
    rows = sorted(pep_shops(slug), key=shop_rank)  # the same order as "Where to get it": best-checked first
    if not rows:
        return ""
    trs, newest = [], ""
    for r in rows:
        seller = seller_base(clean(SELLERS.get(r["seller_slug"], {}).get("seller_name") or r["seller_name"]))
        name = clinic_link(r["seller_slug"], seller)
        size = f'{r["amount_mg"]:g} mg' if r.get("amount_mg") else "unknown"
        price = money(r["price_usd"]) if r.get("price_usd") is not None else "unknown"
        ppm = (f'{per_mg(r["price_per_mg"])}/mg' if r.get("price_per_mg") is not None else "blend" if r.get("is_blend") else "unknown")
        seen = r.get("price_observed_at") or r.get("last_seen") or ""
        newest = max(newest, seen)
        trs.append(f'<tr><td>{name}</td><td class="num" data-l="Size">{size}</td><td class="num" data-l="Price">{price}</td>'
                   f'<td class="num" data-l="Per mg">{ppm}</td><td data-l="Checks">{shop_checks(r)}</td></tr>')
    return f"""
<section class="section" id="sold">
  <div class="wrap">
    <div class="sec-hd"><div><h2>Where it is sold</h2><p>The {plural(len(rows), "shop")} in the price window on our goal pages, each with its cheapest listing by price per mg, most checks first. Research-use sellers, with our checks.{" Prices checked " + nice_date(newest) + "." if newest else ""}</p></div></div>
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


PEP_LETTERS_SHOWN = 5  # the five newest on the substance page; the letters page has them all (owner task 3 Nov 2026)


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
    <div class="sec-hd"><div><h2>FDA warning letters</h2>{APPROVED_LETTERS_LINE if pep_group(pep_status(slug)) == "approved" else ""}<p>{plural(len(rows), "FDA warning letter")} name{"s" if len(rows) == 1 else ""} {escape(name)}.{shown} Each quote is where the letter first names it.</p></div></div>
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


def unwrap(section):
    """(id, inner html) of a "<section ... id=..."><div class="wrap">...</div></section>" block, for a page that places it
    in its own grid; ("", "") for an empty block."""
    m = re.match(r'\s*<section[^>]*?(?:id="([^"]*)")?[^>]*>\s*<div class="wrap">(.*)</div>\s*</section>\s*$', section, re.S)
    return (m.group(1) or "", m.group(2)) if m else ("", section)


def shop_rank(r):
    """Best-checked first (owner task 3 Nov 2026, audit 11.3: BPC-157 led with a 2-of-5 shop): most checks, then the lowest
    price per mg, then the name."""
    sc = SELLERS.get(r["seller_slug"], {}).get("score")
    return (-(sc if sc is not None else -1), r.get("price_per_mg") is None, r.get("price_per_mg") or 0, r["seller_slug"])


def pep_where(slug):
    """"Where to get it", the substance page's first block (pages.md, Peptide; owner task 3 Nov 2026): an approved medicine's
    three cheapest clinic plans (brand first, then compounded), each with btn-wait "See plans", and the compare pair with the
    most plans; a research-use peptide's three best-checked shops with btn-line "Our review"; a cosmetic's serums and creams;
    a cosmetic with none says "Sold as a cosmetic; no prices checked." Returns (html, the seller shown first or None)."""
    s = pep_status(slug)
    grp = pep_group(s)
    lines, first, foot = [], None, ""
    if grp == "approved":
        plans = [r for r in pep_plans(slug) if r["seller_slug"] in PROFILES]
        plans = sorted(plans, key=lambda r: (r.get("product_kind") == "compounded", float(r["price_monthly"]), r["seller_name"]))[:3]
        named = set()
        for r in plans:
            kind = '<span class="chip chip-warn">Compounded</span>' if r.get("product_kind") == "compounded" else ""
            lines.append(f'<li><span class="where-who">{clinic_link(r["seller_slug"], seller_base(r["seller_name"]))}'
                         f'<span class="sub">{explain_brand(r["plan_name"], named)}{kind}</span></span>'
                         f'<span class="where-price"><span class="num">{usd(r["price_monthly"])}/mo</span>{plan_letter(r)}</span>'
                         f'{clinic_button(r["seller_slug"], "See plans", plan=r)}</li>')
        first = plans[0] if plans else None
        # the pair pages are built after the substance pages: cmp_links_in fills the marker (or drops it)
        foot = f"<!--pair-foot:{slug}-->"
    else:
        kind = "cosmetic" if grp == "cosmetic" else "research"
        rows = sorted(seller_rows(slug, kind), key=shop_rank)[:3]
        for r in rows:
            sc = SELLERS.get(r["seller_slug"], {}).get("score")
            ppm = f'{per_mg(r["price_per_mg"])}/mg' if r.get("price_per_mg") is not None else money(r["price_usd"]) if r.get("price_usd") is not None else "price unknown"
            what = clean(r["product_name"]) if kind == "cosmetic" else f'{sc} of {len(SCORE_CHECKS)} checks' if sc is not None else "not checked yet"
            review = (f'<a class="btn btn-line btn-sm" href="/sellers/{r["seller_slug"]}/">Our review</a>' if r["seller_slug"] in PROFILES else "")
            lines.append(f'<li><span class="where-who"><span class="name">{escape(seller_base(clean(SELLERS.get(r["seller_slug"], {}).get("seller_name") or r["seller_name"])))}</span>'
                         f'<span class="sub">{escape(what)}</span></span><span class="where-price"><span class="num">{ppm}</span></span>{review}</li>')
        first = rows[0] if rows else None
        if not rows and grp == "cosmetic":
            return f'<div class="panel-line pep-where"><h2>Where to get it</h2><p class="small">{COSMETIC_LATER}</p></div>', None
    if not lines:
        # nothing to list: the block still says so, from data (owner task 3 Nov 2026: every substance page has it)
        none = ("No clinic plan we track carries it yet." if grp == "approved" else "No shop we track lists it yet.")
        return f'<div class="panel-line pep-where" id="where"><h2>Where to get it</h2><p class="small">{none}</p></div>', None
    lede = ("The cheapest plans at the online clinics we track, brand first." if grp == "approved" else
            "Serums and creams from the shops we track." if grp == "cosmetic" else
            "The best-checked shops first. Research-use shops; every name opens our review.")
    return (f'<div class="panel-line pep-where" id="where"><h2>Where to get it</h2><p class="small">{lede}</p>'
            f'<ul class="where-list">{"".join(lines)}</ul>{foot}</div>'), first


def pep_next(slug):
    """"What to do next" before the sources (pages.md, Peptide; as on the goal page): the goal page, the compare pair with
    the most plans and shops, and /sellers/ filtered to the substance; each left out when its target is missing."""
    links = []
    goals = list(dict.fromkeys(g["slug"] for g, _ in pep_goals(slug)))
    if goals:
        g = next(x for x in ALL_GOALS if x["slug"] == goals[0])
        links.append(f'<li><a href="/{g["slug"]}/">Compare every option for {g["name"].lower()}</a></li>')
    links.append(f"<!--pair-li:{slug}-->")  # every pair with the substance, filled by cmp_links_in once the pair pages exist
    # /sellers/ is built whenever the data has seller pages (it is added after the substance pages)
    if PROFILES and (any(slug in shop_subs(r) for r in SHOPS.values()) or any(slug in clinic_subs(r) for r in CLINIC_PROFILES.values())):
        links.append(f'<li><a href="/sellers/#substance={slug}">Every seller of {escape(pep_short(slug))}, with its checks</a></li>')
    return f'<div><h2 class="h-sources">What to do next</h2><ul class="next-list">{"".join(links)}</ul></div>' if links else ""


# Other names (data/names.json; SEO round c, queue block 9): a substance sold or searched under another name ("PT-141")
# gets a section and questions on its page, from data; its title and H1 stay (rule 8).
NAMES = json.loads((ROOT / "data" / "names.json").read_text(encoding="utf-8"))["names"] if (ROOT / "data" / "names.json").exists() else {}


def pep_shop_row(slug):
    """The goal page's research-use row for an approved substance ("PT-141 from online shops"), or None."""
    return next((p for _, p in pep_goals(slug) if subs_of(p) == [slug] and p.get("rx_word") == "research use only"), None)


def pep_alias_facts(slug):
    """(alias, letters that quote it, letters that name the substance, clinic plans that carry it) or None."""
    if not NAMES.get(slug):
        return None
    alias = NAMES[slug][0]
    rows = LETTER_SUBS.get(slug, []) if LETTER_SUBS_ON else []
    quoted = [r for r in rows if alias.lower() in (r.get("first_mention") or "").lower()]
    plans = [r for r in pep_plans(slug) if alias.lower() in r["plan_name"].lower()]
    return alias, quoted, rows, plans


def pep_alias_section(slug):
    f = pep_alias_facts(slug)
    if not f:
        return ""
    alias, quoted, rows, plans = f
    name, brands, shop = pep_short(slug), pep_brands(slug), pep_shop_row(slug)
    out = [f"{alias} is another name for {name}."]
    if brands and pep_group(pep_status(slug)) == "approved":
        out.append(f'The FDA-approved product is {and_list(brands)}, on prescription.')
    if shop:
        g = next(g for g, p in pep_goals(slug) if p is shop)
        out.append(f'<a href="/{g["slug"]}/">{escape(shop["name"])}</a>: {escape(shop["plain"])}')
    if quoted:
        out.append(f'{"All " + str(len(rows)) if len(quoted) == len(rows) else f"{len(quoted)} of the {len(rows)}"} FDA warning letter{"s" if len(rows) != 1 else ""} that name {name} call it {alias}.')
    if plans:
        out.append(f'{plural(len(plans), "online clinic plan")} we track {"carries" if len(plans) == 1 else "carry"} {alias} in {"its" if len(plans) == 1 else "their"} name.')
    return f"""
<section class="section" id="names">
  <div class="wrap">
    <div class="sec-hd"><div><h2>{escape(alias)} and {escape(name)}</h2><p>{" ".join(out)}</p></div></div>
  </div>
</section>"""


def pep_faq_pairs(slug):
    """The questions on a substance page with another name, answered from its data."""
    f = pep_alias_facts(slug)
    if not f:
        return []
    alias, quoted, rows, plans = f
    s, name, brands, shop = pep_status(slug), pep_short(slug), pep_brands(slug), pep_shop_row(slug)
    approved = pep_group(s) == "approved"
    pairs = [(f"Is {alias} the same as {name}?",
              f"Yes. {alias} is another name for {name}"
              + (f", the molecule in {and_list(brands)}" if brands and approved else "") + "."
              + (f' {"All " + str(len(rows)) if len(quoted) == len(rows) else f"{len(quoted)} of the {len(rows)}"} FDA warning letter{"s" if len(rows) != 1 else ""} that name it call it {alias}.' if quoted else ""))]
    status = f'{name} is {s["label"]}' + (f" as {and_list(brands)}" if brands and approved else "") + f': {pep_means(slug)[0].lower()}{pep_means(slug)[1:]}'
    pairs.append((f"Is {alias} FDA approved?",
                  status + (f' {escape(shop["name"])}: {escape(shop["plain"])}' if shop else "")))
    p = pep_plans(slug)
    if p:
        r = p[0]
        what = ("compounded, made by a pharmacy and not FDA approved, even when an approved medicine has the same ingredient"
                if r.get("product_kind") == "compounded" else "not compounded")
        pairs.append((f"How much does {alias} cost?",
                      f'The lowest plan at the online clinics we track is {usd(r["price_monthly"])} a month '
                      f'({clinic_link(r["seller_slug"], seller_base(r["seller_name"]), True)}, {escape(clean(r["plan_name"]))}), {what}. '
                      f'Checked {nice_date(r["last_seen"])}.'))
    rx = pep_rx(slug, s)[0]
    if approved:
        pairs.append((f"Do I need a prescription for {alias}?",
                      f"{rx}: {name} is an FDA-approved medicine." + (" Research-use shops sell it without one; that is not an approved product." if shop else "")))
    if rows:
        pairs.append((f"Has the FDA warned sellers of {alias}?",
                      f'{plural(len(rows), "FDA warning letter")} we track {"names" if len(rows) == 1 else "name"} {name}, the latest on '
                      f'{nice_date(max(r["letter_date"] for r in rows))}. '
                      + ("These letters are about sellers and advertising, not about the medicine's approval." if approved else "")))
    return pairs


def pep_page(slug):
    """The substance page in one screen (pages.md, Peptide; owner task 3 Nov 2026, audit 11.3, B14, B15): H1, the author
    line, the status line in plain words, "Where to get it"; then the full table (tbl-compact); then Evidence and Facts
    side by side (8 + 4) and the FDA letters; then "What to do next", the guides and the sources."""
    s = pep_status(slug)
    src = PepSources()
    src.n(f'{"FDA" if "fda.gov" in s["url"] else "Source"}, status of {pep_short(slug)}, {nice_date(s["seen"])}', s["url"])
    host = source_word(s["url"])
    status_src = (" and ".join(f'<a href="{escape(x["url"])}" rel="nofollow">{source_word(x["url"])}</a>' for x in s["routes"])
                  if s.get("routes") else f'<a href="{escape(s["url"])}" rel="nofollow">{host}</a>')
    status = (f'<p class="pep-status"><span class="chip chip-{s["chip"]}">{s["label"]}</span> {pep_means(slug)} {status_src}</p>')
    where, first = pep_where(slug)
    ev_id, evidence = unwrap(pep_evidence(slug, src))
    lt_id, letters = unwrap(pep_letters_section(slug))
    sold_id, sold = unwrap(pep_plans_section(slug) if pep_group(s) == "approved" else pep_shops_section(slug))
    sold = sold.replace('class="tbl tbl-cards', 'class="tbl tbl-compact tbl-cards', 1)
    left = ((f'<div class="panel-line pep-block" id="evidence">{evidence}</div>' if evidence else "")
            + (f'<div class="panel-line pep-block" id="letters">{letters}</div>' if letters else ""))
    blocks = f'<div class="pep-body"><div class="pep-left">{left}</div><div class="pep-right">{pep_facts(slug, s)}{pep_guides(slug)}</div></div>'
    nxt = pep_next(slug)
    faq = (f'\n<section class="section"><div class="wrap">{faq_block(pep_name(slug) + (f" ({NAMES[slug][0]})" if NAMES.get(slug) else ""), pep_faq_pairs(slug), "faq-h")}</div></section>'
           if pep_faq_pairs(slug) else "")
    return f"""
<section class="hero hero-goal seller-pg pep-pg">
  <div class="wrap">
    <div class="pep-first">
      <div>
        <h1>{escape(pep_name(slug))}</h1>
        {author_line(pep_checked(slug))}
        {status}
        <p class="intro">{" ".join(pep_answer(slug, first)[1:])}</p>
      </div>
      {where}
    </div>
  </div>
</section>
{f'<section class="section pep-sold" id="{sold_id or "sold"}"><div class="wrap">{sold}</div></section>' if sold else ""}
<section class="section pep-blocks"><div class="wrap">{blocks}</div></section>{pep_alias_section(slug)}{faq}
<section class="section pep-foot">
  <div class="wrap">
    <div class="goal-two">{nxt}
    <section class="pep-sources" aria-labelledby="sources-h"><h2 id="sources-h" class="h-sources">Sources</h2>
    <ol class="small sources">{src.html()}</ol></section></div>
  </div>
</section>
"""


PEP_GROUPS = [("approved", "FDA approved", "Approved medicines: an FDA-approved product exists for a stated use."),
              ("not", "Not approved", "No approved product; research-use shops sell most of them, and some may be made by pharmacies."),
              ("cosmetic", "Cosmetic", "Sold in creams and serums; cosmetics do not need FDA approval.")]


def pep_checked_price(slug):
    """A goal page's hand-checked price for the substance (the option row's price with its source), as (dollars, word):
    the word is the last item of the price's bracket in the option's copy ("generic, pharmacy coupon" -> "pharmacy
    coupon"), else the source's name ("Keeps"). None without one."""
    for g in ALL_GOALS:
        for p in g["peptides"]:
            if subs_of(p) != [slug]:
                continue
            if p.get("price") in PRICE_REF:
                g2 = next(x for x in LIVE_GOALS if x["slug"] == p["price"])
                dollars, name = g2["price_from_usd"], g2["price_source_name"]
            elif p.get("price_source") and p.get("price_from_usd") is not None:
                dollars, name = p["price_from_usd"], p["price_source"]["name"]
            else:
                continue
            said = re.search(r"\$[\d.,]+/mo \(([^)]*)\)", p.get("status_plain", ""))
            return dollars, said.group(1).split(",")[-1].strip() if said else name.split(",")[0].strip()
    return None


def pep_low(slug):
    """One rule for a substance's lowest price (owner UX audit A20, 3 Nov 2026: /peptides/ showed minoxidil at $30/mo from
    a clinic plan, /hair/ at $10/mo checked): the goal page's checked price with its source word, else the lowest clinic
    plan that is not compounded for an approved medicine, else the lowest price per mg at the shops shown."""
    checked = pep_checked_price(slug)
    if checked:
        return f"${checked[0]}/mo, {checked[1]}"
    plan = pep_low_plan(slug) if pep_group(pep_status(slug)) == "approved" else None
    if plan:
        return f'{usd(plan["price_monthly"])}/mo, clinic'
    low = pep_low_shop(slug)
    return f'{per_mg(low["price_per_mg"])}/mg, shop' if low else "none shown"


# A substance that is a drug in one form and a cosmetic in another (GHK-Cu) gets a row in each group, named apart as on
# the goal pages' legal tables (owner UX audit A21, 3 Nov 2026): "GHK-Cu (injection)" under Not approved, "GHK-Cu (cream
# or serum)" under Cosmetic, from the hand-written cosmetic row and the FDA listing.
PEP_COSMETIC_TOO = {x: r for r in LEGAL["rows"] if r.get("status") == "Cosmetic" for x in r.get("substances") or []
                    if x in PEPTIDE_SLUGS and pep_group(pep_status(x)) != "cosmetic"}
PEP_ROUTE = {x: f' ({"injection" if "inject" in (pep_status(x).get("listing") or "").lower() else "as a drug"})' for x in PEP_COSMETIC_TOO}


def pep_means(slug):
    """"What it means" in plain words (owner UX audit B16): the sentence of the status row the legal tables show (the
    lowest rank, as db_status picks it), from list_words; a hand-written status keeps its own sentence."""
    rows = sorted(pep_status_rows(slug), key=lambda r: DB_STATUS[(r["regime"], r["status_value"])][0])
    st = db_status(slug)
    if st and st.get("routes"):  # a status split by route: both rows, each with its route (task 33)
        by = {x["listing"]: ("By injection" if "(for injectable" in x["listing"] else "By other routes") for x in st["routes"]}
        return " ".join(f'{by[r["fda_listing"]]}: {list_words(r)[1][0].lower()}{list_words(r)[1][1:]}'
                        for r in sorted(rows, key=lambda r: by.get(r.get("fda_listing"), "")) if r.get("fda_listing") in by)
    if rows:
        return list_words(rows[0])[1]
    t = pep_status(slug)["sentence"]
    return t[0].upper() + t[1:] + ("" if t.endswith(".") else ".")


PEP_FILTERS = [("approved", "Approved"), ("cosmetic", "Cosmetic"), ("not", "Not approved")]
PEPTIDES_JS = """<script>
(function(){var t=document.getElementById('pep-table'),f=document.querySelector('.pep-filter');if(!t||!f)return;f.hidden=false;
var n=document.getElementById('pep-n'),rows=[].slice.call(t.querySelectorAll('tbody tr'));
function draw(){var on={},c=0;f.querySelectorAll('.year-chip').forEach(function(b){on[b.getAttribute('data-group')]=b.getAttribute('aria-pressed')==='true';});
rows.forEach(function(r){var s=on[r.getAttribute('data-group')];r.hidden=!s;if(s)c++;});n.textContent=c+' of '+rows.length+' shown.';}
f.addEventListener('click',function(e){var b=e.target.closest('.year-chip');if(!b)return;b.setAttribute('aria-pressed',b.getAttribute('aria-pressed')==='true'?'false':'true');draw();});
draw();})();
</script>"""


def peptides_index():
    """/peptides/ (owner UX audit B16, 3 Nov 2026): one table in A to Z order with a Status column, a row of letters to jump
    to, and the three statuses as filter chips (all on; shown with JavaScript only). Title and H1 unchanged (rule 8)."""
    rows = [(pep_name(x) + PEP_ROUTE.get(x, ""), x, pep_group(pep_status(x)), pep_status(x)["chip"], pep_status(x)["label"],
             pep_means(x), pep_low(x)) for x in PEPTIDE_SLUGS]
    rows += [(f"{pep_name(x)} (cream or serum)", x, "cosmetic", r["chip"], r["status"], r["note"][0].upper() + r["note"][1:] + ".",
              "none shown") for x, r in PEP_COSMETIC_TOO.items()]
    rows.sort(key=lambda t: t[0].lower())
    letter = lambda name: name[0].upper() if name[0].isalpha() else "#"
    firsts = {}
    for t in rows:
        firsts.setdefault(letter(t[0]), t)
    anchor = lambda t: f' id="az-{letter(t[0]).lower()}"' if firsts[letter(t[0])] is t else ""
    trs = "".join(
        f'<tr data-group="{grp}"{anchor(t)}>'
        f'<td><a class="name" href="/peptides/{x}/">{escape(name)}</a></td>'
        f'<td data-l="Status"><span class="chip chip-{chip}">{label}</span></td>'
        f'<td data-l="What it means">{sentence}</td><td class="num" data-l="Lowest price">{low}</td></tr>'
        for t in rows for name, x, grp, chip, label, sentence, low in [t])
    jump = "".join(f'<a class="year-chip" href="#az-{k.lower()}">{k}</a>' for k in firsts)
    counts = {k: sum(t[2] == k for t in rows) for k, _ in PEP_FILTERS}
    chips = "".join(f'<button type="button" class="year-chip" data-group="{k}" data-filter="group" data-value="{k}" aria-pressed="true">{w} <span>{counts[k]}</span></button>'
                    for k, w in PEP_FILTERS if counts[k])
    checked = max(pep_checked(x) for x in PEPTIDE_SLUGS)
    return f"""
<section class="section letters-hd">
  <div class="wrap">
    <h1>Peptides and their FDA status</h1>
    <p class="lede">Every peptide and approved alternative we track, {len(PEPTIDE_SLUGS)} in all, with its FDA status, its source and the lowest price we show. Each name opens its page.</p>
    <p class="letters-stamp"><span class="stamp">Checked {nice_date(checked)}</span><span class="small">Lowest price: the price a goal page checked by hand, else per month at the online clinics for an approved medicine, else per mg at the shops we show.</span></p>
  </div>
</section>
<section class="band-2" id="peptides-list">
  <div class="wrap">
    <nav class="year-chips az-jump" aria-label="Jump to a letter">{jump}</nav>
    <div class="year-chips pep-filter" role="group" aria-labelledby="pep-show" hidden><span id="pep-show">Show</span>{chips}<p class="small" id="pep-n" aria-live="polite"></p></div>
    <div class="tbl-wrap"><table class="tbl tbl-cards tbl-peptides" id="pep-table"><caption class="vh">Peptides A to Z with their FDA status</caption>
      <thead><tr><th scope="col">Substance</th><th scope="col">Status</th><th scope="col">What it means</th><th scope="col">Lowest price</th></tr></thead>
      <tbody>{trs}</tbody>
    </table></div>
  </div>
</section>
{PEPTIDES_JS}
"""


def pep_signals(slug):
    """What a peptide page carries beyond its status, each as the page shows it (pages.md, Peptide, Thin pages)."""
    s = pep_status(slug)
    approved = pep_group(s) == "approved"
    return {"goal page": bool(pep_goals(slug)), "shop table": bool(pep_shops(slug)),
            "clinic plan": approved and bool(pep_plans(slug)), "FDA letter": bool(LETTER_SUBS_ON and LETTER_SUBS.get(slug)),
            "guide": bool(pep_guides(slug)), "approved brand": approved and bool(pep_brands(slug))}


# Thin pages (pages.md, Peptide; owner task 2 Nov 2026): a page with fewer than three of the six is still built and
# linked, but carries noindex and leaves the sitemap and llms.txt, as /search/ does.
PEP_MIN_SIGNALS = 3
PEP_THIN = [x for x in PEPTIDE_SLUGS if sum(pep_signals(x).values()) < PEP_MIN_SIGNALS]

if PEPTIDE_SLUGS:
    PAGES.append(("/peptides/", "peptides/index.html", "Peptides A to Z: FDA status and prices | Peptide Chooser",
                  (f"Every peptide and approved alternative we track, {len(PEPTIDE_SLUGS)} in all, grouped FDA approved, not "
                   "approved and cosmetic, with its source and the lowest price we show."),
                  peptides_index(), item_list_schema("Peptides and their FDA status",
                                                     [(pep_name(x), f"{SITE}/peptides/{x}/") for x in PEPTIDE_SLUGS]),
                  [("/peptides/", "Peptides")]))
    for _x in PEP_THIN:
        NOINDEX.add(f"/peptides/{_x}/")
    for _x in PEPTIDE_SLUGS:
        PAGES.append((f"/peptides/{_x}/", f"peptides/{_x}/index.html", pep_title(_x), pep_description(_x), pep_page(_x), faq_schema(pep_faq_pairs(_x)),
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


def live_paths():
    """The paths already published: the live sitemap the deploy fetches into LIVE_SITEMAP, else the last build's
    dist/sitemap.xml (read before dist is cleared), else none."""
    for f in (os.environ.get("LIVE_SITEMAP"), DIST / "sitemap.xml"):
        if f and Path(f).is_file():
            return set(re.findall(re.escape(SITE) + r"(/[^<]*)</loc>", Path(f).read_text(encoding="utf-8")))
    return set()


LIVE_PATHS = live_paths()


def cmp_clinic_pairs():
    """{(a, b): [substances]} for every two clinic pages that both have a compounded plan of a substance in
    CMP_CLINIC_SUBS, keyed by the clinics' URL names in alphabetical order. Over CMP_MAX pairs, a pair already live
    always stays (owner answer Q2 a, 3 Nov 2026; rule 8); the others fill up to CMP_MAX, only those where both clinics
    meet 2 or more of the 5 checks (owner task 2 Nov 2026), in order."""
    out = {}
    for sub in CMP_CLINIC_SUBS:
        clinics = sorted({r["seller_slug"] for r in PLANS if r["seller_slug"] in CLINIC_PROFILES and cmp_clinic_plan(r["seller_slug"], sub)},
                         key=lambda x: cmp_slugify(cmp_clinic_name(x)))
        for i, a in enumerate(clinics):
            for b in clinics[i + 1:]:
                out.setdefault((a, b), []).append(sub)
    if len(out) <= CMP_MAX:
        return out
    live = {k: v for k, v in out.items() if cmp_path(*k, clinic=True) in LIVE_PATHS}
    rest = [(k, v) for k, v in out.items() if k not in live and all((PROFILES[x].get("score") or 0) >= 2 for x in k)]
    keep = set(live) | {k for k, _ in rest[:max(CMP_MAX - len(live), 0)]}
    return {k: v for k, v in out.items() if k in keep}


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
    host = source_word(s["url"])
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
        # like with like (owner task w2, 3 Nov 2026): the brand plans of a form both sell, never a pill against a pen
        fa, fb = sub_form_lows(a), sub_form_lows(b)
        common = sorted((k for k in fa if k in fb and k[0] == "brand"), key=lambda k: float(fa[k]["price_monthly"]) + float(fb[k]["price_monthly"]))
        if common:
            k = common[0]
            lo, hi = sorted(((na, fa[k]), (nb, fb[k])), key=lambda x: float(x[1]["price_monthly"]))
            if float(lo[1]["price_monthly"]) != float(hi[1]["price_monthly"]):
                out.append(f"At the online clinics we track, brand {FORM_PLURAL[k[1]]} of {lo[0]} start lower: "
                           f"{usd(lo[1]['price_monthly'])} a month against {usd(hi[1]['price_monthly'])}.")
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


# Verdict on the pair pages (pages.md, Compare pairs; owner task w2, UX audit 7.4, B17, B18, 3 Nov 2026): from data only,
# each fact favours one side: the cheaper plan of a form and kind both sell (pen with pen, the #65 rule), the lower
# price per mg at the shops, more clinics or shops selling it, fewer FDA letters naming a research-use substance, a
# different FDA status. "Pick A if ... Pick B if ..." when each side has a fact; one side with two facts names both;
# one fact alone reads "Same FDA status; the difference is ..."; no fact, no block. No effect or side-effect claim.
FORM_PLURAL = {"Pen": "pens", "Pill": "pills", "Injection": "injections", "Topical": "topicals"}


def sub_form_lows(slug):
    """{(kind, form): the substance's cheapest plan of that kind (brand or compounded) and form}."""
    out = {}
    for r in pep_plans(slug):
        kind = "compounded" if plan_kind(r) == "compounded" else "brand" if plan_kind(r) in ("brand", "generic") else None
        if kind and plan_form_word(r) in FORM_PLURAL:
            out.setdefault((kind, plan_form_word(r)), r)
    return out


def cmp_sub_facts(a, b):
    """([(pick, diff)] for a, [(pick, diff)] for b): the facts that favour each side, strongest first."""
    na, nb = pep_short(a), pep_short(b)
    fa, fb = [], []
    side = lambda first: fa if first else fb
    ga, gb = pep_group(pep_status(a)), pep_group(pep_status(b))
    if ga != gb and "approved" in (ga, gb):
        w, o = (a, b) if ga == "approved" else (b, a)
        side(w == a).append(("you want an FDA-approved medicine", f"{pep_short(w)} is FDA approved and {pep_short(o)} is {cmp_status_words(o)}"))
    approved = ga == gb == "approved"
    if approved:
        la, lb = sub_form_lows(a), sub_form_lows(b)
        common = sorted((k for k in la if k in lb), key=lambda k: float(la[k]["price_monthly"]) + float(lb[k]["price_monthly"]))
        if common:
            k = common[0]
            x, y = float(la[k]["price_monthly"]), float(lb[k]["price_monthly"])
            if x != y:
                what = f"{k[0]} {FORM_PLURAL[k[1]]}"
                lo = (na, x, y) if x < y else (nb, y, x)
                side(x < y).append((f"price matters most: {what} from {usd(lo[1])}/mo against {usd(lo[2])}",
                                    f"price: {what} of {lo[0]} start at {usd(lo[1])} a month, against {usd(lo[2])}"))
        ca, cb = (len({r["seller_slug"] for r in pep_plans(x)}) for x in (a, b))
        where = "clinic"
    else:
        sa, sb = pep_low_shop(a), pep_low_shop(b)
        if sa and sb and sa["price_per_mg"] != sb["price_per_mg"]:
            x, y = sa["price_per_mg"], sb["price_per_mg"]
            lo = (na, x, y) if x < y else (nb, y, x)
            side(x < y).append((f"price per mg matters most: from {per_mg(lo[1])}/mg against {per_mg(lo[2])}/mg",
                                f"price: {lo[0]} starts at {per_mg(lo[1])}/mg at the shops we show, against {per_mg(lo[2])}/mg"))
        ca, cb = (len({r["seller_slug"] for r in pep_shops(x)}) for x in (a, b))
        where = "shop"
    if ca != cb and min(ca, cb) > 0:
        more = ca > cb
        side(more).append((f"you want more {where}s to choose from: {max(ca, cb)} against {min(ca, cb)}",
                           f"{plural(max(ca, cb), where)} sell {na if more else nb}, against {min(ca, cb)} for {nb if more else na}"))
    if not approved and LETTER_SUBS_ON:
        la_, lb_ = len(LETTER_SUBS.get(a, [])), len(LETTER_SUBS.get(b, []))
        if la_ != lb_:
            side(la_ < lb_).append((f"you want fewer FDA letters naming it: {min(la_, lb_)} against {max(la_, lb_)}",
                                    f"FDA letters: {plural(min(la_, lb_), 'letter')} {'names' if min(la_, lb_) == 1 else 'name'} {na if la_ < lb_ else nb}, against {max(la_, lb_)}"))
    return fa, fb


def cmp_verdict(na, nb, fa, fb, same="Same FDA status; the difference is"):
    """The verdict block and how many facts it states (2, or 0 when it is left out; never 1). `same` opens the one-fact
    sentence: the substances share their FDA status (pairs are built only from the same kind of status)."""
    if fa and fb:
        text, n = f"Pick {na} if {fa[0][0]}. Pick {nb} if {fb[0][0]}.", 2
    elif len(fa) >= 2 or len(fb) >= 2:
        name, f = (na, fa) if len(fa) >= 2 else (nb, fb)
        text, n = f"Pick {name} if {f[0][0]}, or if {f[1][0]}.", 2
    elif fa or fb:
        f = fa or fb
        text, n = f"{same} {f[0][1]}.", 2
    else:
        return "", 0
    return (f'<section class="cmp-verdict" aria-labelledby="verdict-h" data-facts="{n}"><h2 id="verdict-h" class="h-sources">Which to pick</h2>'
            f"<p>{text}</p></section>"), n


def cmp_next(links):
    """"What to do next" on a pair page: the pages the pair has in this build, as a plain link list."""
    items = "".join(f'<li><a href="{h}">{escape(t)}</a></li>' for h, t in links)
    return (f'<section class="cmp-next" aria-labelledby="next-h"><h2 id="next-h" class="h-sources">What to do next</h2>'
            f'<ul class="next-links">{items}</ul></section>') if items else ""


def cmp_brand_table(a, b):
    """Two FDA-approved substances that both have clinic plans (SEO round c, queue block 9): the approved brands, then the
    cheapest brand or generic plan and the cheapest compounded plan per form, and how many clinics sell each, from data."""
    if not (pep_group(pep_status(a)) == pep_group(pep_status(b)) == "approved" and pep_plans(a) and pep_plans(b)):
        return ""
    def forms(x, kind):
        lows = sub_form_lows(x)
        cell = "".join(f'<span class="cmp-form">{f} from <span class="num">{usd(r["price_monthly"])}/mo</span></span>'
                       for (k, f), r in sorted(lows.items(), key=lambda i: float(i[1]["price_monthly"])) if k == kind)
        return cell or "No plan we track"
    def clinics(x, kind):
        n = len({r["seller_slug"] for r in pep_plans(x) if ("compounded" if plan_kind(r) == "compounded" else
                 "brand" if plan_kind(r) in ("brand", "generic") else None) == kind})
        return f'<span class="num">{n}</span>'
    na, nb = pep_short(a), pep_short(b)
    rows = [("Approved brands", *(and_list(pep_brands(x)) or "None listed" for x in (a, b))),
            ("Brand or generic plans", *(forms(x, "brand") for x in (a, b))),
            ("Clinics with a brand or generic plan", *(clinics(x, "brand") for x in (a, b))),
            ("Compounded plans", *(forms(x, "compounded") for x in (a, b))),
            ("Clinics with a compounded plan", *(clinics(x, "compounded") for x in (a, b)))]
    heads = [f'<span class="name">{escape(pep_short(x))}</span>' for x in (a, b)]  # the first table links the sides (check-parts)
    return (f'<section class="cmp-brand" aria-labelledby="brand-h"><h2 id="brand-h">Brand and compounded {escape(na)} and {escape(nb)}</h2>'
            "<p>A brand or generic plan is an FDA-approved product. A compounded plan is made by a pharmacy and not FDA approved, "
            "even when an approved medicine has the same ingredient. Prices are the lowest monthly price per form at the online "
            f"clinics we track, checked {nice_date(max(pep_checked(a), pep_checked(b)))}.</p>"
            + cmp_table(f"Brand and compounded {na} and {nb}", heads, rows) + "</section>")


def cmp_sub_faq_pairs(a, b):
    """The questions on a substance pair page, answered from its data (SEO round c, queue block 9)."""
    na, nb = pep_short(a), pep_short(b)
    ans = cmp_sub_answer(a, b)
    sa, sb = pep_status(a), pep_status(b)
    approved = {x: pep_group(pep_status(x)) == "approved" for x in (a, b)}
    if not any(approved.values()) and sa["sentence"] == sb["sentence"]:
        st = ans[0] + f' For both, {sa["sentence"]}.'
    else:
        st = ans[0] + "".join(f' {pep_short(x)}: {pep_status(x)["sentence"]}.' for x in (a, b) if not approved[x])
    br = [f"{pep_short(x)}: {and_list(pep_brands(x))}" for x in (a, b) if approved[x] and pep_brands(x)]
    if br:
        st += f' Approved brands: {"; ".join(br)}.'
    st += f" Checked against the FDA lists on {nice_date(max(sa['seen'], sb['seen']))}."
    pairs = [(f"Is {na} or {nb} FDA approved?", st)]
    price = [x for x in ans[1:]]
    # the cheapest compounded plan of a form the table shows, so the answer and the table agree
    comp = [(pep_short(x), min((r for (k, _), r in sub_form_lows(x).items() if k == "compounded"),
                               key=lambda r: float(r["price_monthly"]), default=None)) for x in (a, b) if approved[x]]
    comp = [(n, r) for n, r in comp if r]
    if len(comp) == 2:
        price.append(f"Compounded plans, made by a pharmacy and not FDA approved, start at {usd(comp[0][1]['price_monthly'])} a month for "
                     f"{comp[0][0]} and {usd(comp[1][1]['price_monthly'])} for {comp[1][0]}.")
    if price:
        pairs.append((f"Which is cheaper, {na} or {nb}?", " ".join(price)))
    cnt = {x: len({r["seller_slug"] for r in (pep_plans(x) if approved[x] else pep_shops(x))}) for x in (a, b)}
    say = lambda x: (f'{plural(cnt[x], "online clinic")} we track {"has" if cnt[x] == 1 else "have"} a plan for {pep_short(x)}' if approved[x] else
                     f'{plural(cnt[x], "research-use shop" if pep_group(pep_status(x)) == "not" else "shop")} we show {"lists" if cnt[x] == 1 else "list"} {pep_short(x)}')
    if cnt[a] and cnt[b] and approved[a] == approved[b]:
        where = f"{say(a)}, and {cnt[b]} {'for' if approved[b] else 'list'} {nb}"
    else:
        where = "; ".join(say(x) for x in (a, b) if cnt[x])
    if where:
        pairs.append((f"Where can I get {na} or {nb}?", where + ". Each seller's page shows its checks."))
    if LETTERS_ALL and LETTER_SUBS_ON:
        la, lb = len(LETTER_SUBS.get(a, [])), len(LETTER_SUBS.get(b, []))
        pairs.append((f"Do FDA warning letters name {na} or {nb}?",
                      (f'{plural(la, "FDA warning letter")} we track {"names" if la == 1 else "name"} {na}' if la else f"No FDA warning letter we track names {na}")
                      + (f', and {lb} {"names" if lb == 1 else "name"} {nb}.' if lb else f", and none names {nb}.")
                      + (" These letters are about sellers and advertising, not about the medicine's approval." if all(approved.values()) else "")))
    return pairs


def cmp_sub_page(a, b, goals):
    na, nb = pep_short(a), pep_short(b)
    checked = max(pep_checked(a), pep_checked(b))
    heads = [f'<a class="name" href="/peptides/{x}/">{escape(pep_short(x))}</a><span class="cmp-sub">{pep_status(x)["label"]}</span>' for x in (a, b)]
    ca, cb = cmp_sub_cell(a, goals), cmp_sub_cell(b, goals)
    both_ok = pep_group(pep_status(a)) == pep_group(pep_status(b)) == "approved"
    # an approved medicine has no shop price row; the letters are one line under the table (owner task w2, 3 Nov 2026)
    rows = [r for r in zip(CMP_SUB_ROWS, ca, cb) if r[0] != "FDA letters" and not (both_ok and r[0] == "Lowest price at shops")]
    table = cmp_table(f"{na} and {nb}", heads, rows)
    if LETTERS_ALL and LETTER_SUBS_ON:
        cnt = lambda x: (f'<a href="/fda-warning-letters/?sub={x}">{plural(len(LETTER_SUBS.get(x, [])), "letter")}</a> '
                         f'{"names" if len(LETTER_SUBS.get(x, [])) == 1 else "name"} {escape(pep_short(x))}')
        table += (f'<p class="small cmp-letters">FDA warning letters we track: {cnt(a)}, {cnt(b)}. '
                  "These letters are about sellers and advertising, not about the medicine's approval.</p>")
    verdict, _ = cmp_verdict(na, nb, *cmp_sub_facts(a, b))
    sold = {x for r in PROFILES.values() for x in (clinic_subs(r) if r["seller_slug"] in CLINIC_PROFILES else shop_subs(r))}
    nxt = cmp_next([(f"/peptides/{x}/", f"{pep_short(x)}: FDA status and prices") for x in (a, b)]
                   + [(f'/{g["slug"]}/', f'{g["label"]}: every option compared') for g in goals[:1]]
                   + ([(f"/sellers/#substance={a}", f"Sellers of {na} we track")] if a in sold and PROFILES else []))
    plans = [pep_low_plan(x) if pep_group(pep_status(x)) == "approved" else None for x in (a, b)]
    pre = f'?a=p.{plans[0]["seller_slug"]}.{plans[0]["plan_slug"]}&amp;b=p.{plans[1]["seller_slug"]}.{plans[1]["plan_slug"]}' if all(plans) else ""
    more = cmp_brand_table(a, b) + faq_block(f"{na} and {nb}", cmp_sub_faq_pairs(a, b), "faq-h")
    body = cmp_body(f"{na} vs {nb}", checked, cmp_sub_answer(a, b), table,
                    [(f"/peptides/{a}/", na), (f"/peptides/{b}/", nb)], pre,
                    "Statuses come from the FDA lists; prices are the lowest we show, per mg at the shops or per month at the online clinics.",
                    verdict, "")
    # the brand table and the questions in their own section, then "What to do next" (SEO round c, queue block 9)
    body += (f'<section class="section" id="more"><div class="wrap">{more}</div></section>\n' if more else "") \
        + (f'<section class="section"><div class="wrap">{nxt}</div></section>\n' if nxt else "")
    desc = cmp_fit([f"{na} vs {nb}: {cmp_sub_answer(a, b)[0][:-1]}.", *cmp_sub_answer(a, b)[1:2],
                    f'Both on our {goals[0]["name"].lower()} page.', f"Checked {nice_date(checked)}.", "We compare and never sell."])
    return cmp_title(f"{na} vs {nb}", "FDA status and prices"), desc, body


def cmp_body(h1, checked, answer, table, links, pre, note, verdict="", nxt=""):
    more = " and ".join(f'<a href="{u}">{escape(t)}</a>' for u, t in links)
    return f"""
<section class="section letters-hd">
  <div class="wrap">
    <h1>{escape(h1)}</h1>
    <p class="lede">{" ".join(answer)}</p>
    {author_line(checked)}
    {verdict}
    <p class="small">{note}</p>
  </div>
</section>
<section class="band-2" id="compare-two">
  <div class="wrap">
    {table}
    <p class="small" style="margin-top:16px">Our pages on each: {more}.</p>
    {f'<p class="cmp-link"><a class="btn btn-line" href="/compare/{pre}">Compare any two</a></p>' if pre else ""}
    {nxt}
  </div>
</section>
"""


def clinic_forms(c, sub):
    """{form: the clinic's cheapest compounded plan of the substance in that form}, cheapest form first."""
    out = {}
    for r in sorted((r for r in PLANS if r["seller_slug"] == c and r["substance_slug"] == sub and r.get("product_kind") == "compounded"
                     and r.get("price_monthly") is not None), key=lambda r: (float(r["price_monthly"]), r["plan_name"])):
        out.setdefault(plan_form_word(r), r)
    return out


def cmp_form_cell(c, other, sub):
    """One side's price cell: the plan and its form when both clinics sell the substance in the same single form, else one
    line per form ("Pen from $299/mo")."""
    mine, theirs = clinic_forms(c, sub), clinic_forms(other, sub)
    if len(mine) == 1 and list(mine) == list(theirs):
        (form, r), = mine.items()
        return f'<span class="num">{usd(r["price_monthly"])}/mo</span><span class="cmp-sub">{escape(clean(r["plan_name"]))} · {form}</span>'
    return "".join(f'<span class="cmp-form">{form} from <span class="num">{usd(r["price_monthly"])}/mo</span></span>' for form, r in mine.items())


def cmp_clinic_cells(c, subs, other=None):
    p = PROFILES[c]
    plans = [cmp_clinic_plan(c, s) for s in subs]
    marks = "".join(f'<span class="chip chip-{"ok" if p.get(k) else "neutral"} mark-{"yes" if p.get(k) else "no"}">'
                    f'<span class="vh">{t}: {"yes" if p.get(k) else "no"}</span><span aria-hidden="true">{t}</span></span>' for k, t in seller_checks(p))
    fee = plans[0].get("membership_fee_monthly")
    n, last = p.get("fda_letter_count") or 0, p.get("last_fda_letter_date")
    state = STATES.get(p.get("entity_state") or "", p.get("entity_state") or "")
    company = ("No registered company found" if not shown_company(p) else
               f'{escape(clean(p["entity_name"]))}{", " + state if state else ""}'
               f'<span class="cmp-sub">{"State registry" if p["entity_evidence"] == "registry" else "Named in an FDA letter"}</span>')
    return [cmp_form_cell(c, other, s) for s in subs] + [
        "Not known" if fee is None else "None, all-in" if float(fee) == 0 else f"{usd(fee)}/mo, included",
        f'<a class="chip chip-warn chip-link" href="{letter_href(p["seller_slug"])}">FDA letter {nice_date(last)}</a>' if n and last else "None",
        f'<span class="score"><span class="score-n"><span class="num">{score_of(p)}</span> of {out_of(p)} checks</span>'
        f'<span class="score-marks">{marks}</span></span>',
        company,
        nice_date(max(r["last_seen"] for r in plans)),
    ]


def first_month(r):
    """What a plan costs in its first month with the care or membership fee (owner's audit, 7 Nov 2026: a "cheaper" verdict
    compares this total, not the price alone). A fee the data does not know counts as none and is said so."""
    return float(r.get("price_first_month") or r["price_medicine"]) + float(r.get("membership_fee_monthly") or 0)


def first_month_note(r):
    """"$286 with care ($151 a month + $135/mo care)", "$159 all-in" or "$129 (care fee not known)"."""
    fee, base = r.get("membership_fee_monthly"), float(r.get("price_first_month") or r["price_medicine"])
    month = "first month" if r.get("price_first_month") else "a month"
    if fee is None:
        return f"{usd(base)} (care fee not known)"
    if float(fee) == 0:
        return f"{usd(base)} all-in"
    return f"{usd(first_month(r))} with care ({usd(base)} {month} + {usd(fee)}/mo care)"


def cmp_clinic_answer(a, b, subs):
    na, nb = cmp_clinic_name(a), cmp_clinic_name(b)
    out = []
    for s in subs:
        fa, fb = clinic_forms(a, s), clinic_forms(b, s)
        # the verdict compares one form both sell (the cheapest such form), and names it
        common = sorted((f for f in fa if f in fb and f != FORM_NOT_STATED), key=lambda f: first_month(fa[f]) + first_month(fb[f]))
        if list(fa) == list(fb) == [FORM_NOT_STATED]:
            common = [FORM_NOT_STATED]
        if not common:
            # no form both state: no "cheaper", each side's lowest price with its form, or that it states none
            side = lambda n, fs: "; ".join(f"{n} {usd(r['price_monthly'])} a month" + ("" if f == FORM_NOT_STATED else f" ({f.lower()})")
                                           for f, r in list(fs.items())[:1]) + (", form not stated" if list(fs)[0] == FORM_NOT_STATED else "")
            out.append(f"For compounded {s}, the two do not list the same form, so neither is called cheaper: "
                       f"{side(na, fa)}; {side(nb, fb)}.")
            continue
        form = common[0]
        pa, pb = fa[form], fb[form]
        what = (f"compounded {s} (neither plan states the form)" if form == FORM_NOT_STATED else
                f"compounded {s} as {'' if form == 'Drops' else 'an ' if form[0] in 'AEIOU' else 'a '}{form.lower()}")
        if first_month(pa) == first_month(pb):
            out.append(f"For {what}, both come to {usd(first_month(pa))} in the first month, care included.")
            continue
        lo, hi = sorted(((na, pa), (nb, pb)), key=lambda x: first_month(x[1]))
        out.append(f"For {what}, {lo[0]} is cheaper in the first month: {first_month_note(lo[1])} against {first_month_note(hi[1])}.")
    la, lb = [(PROFILES[x].get("fda_letter_count") or 0, PROFILES[x].get("last_fda_letter_date")) for x in (a, b)]
    if la[0] and lb[0]:
        out.append("Both have an FDA warning letter.")
    elif la[0] or lb[0]:
        (n, (_, d)), other = ((na, la), nb) if la[0] else ((nb, lb), na)
        out.append(f"{n} has an FDA warning letter{' from ' + nice_date(d) if d else ''}; {other} has none.")
    else:
        out.append("Neither has an FDA warning letter.")
    return out[:3]


def cmp_clinic_facts(a, b, subs):
    """The clinic pair's facts (as cmp_sub_facts): the cheaper plan of a form both sell, no FDA letter, more checks met."""
    na, nb = cmp_clinic_name(a), cmp_clinic_name(b)
    fa, fb = [], []
    side = lambda first: fa if first else fb
    for sub in subs[:1]:
        xa, xb = clinic_forms(a, sub), clinic_forms(b, sub)
        common = sorted((f for f in xa if f in xb and f in FORM_PLURAL), key=lambda f: first_month(xa[f]) + first_month(xb[f]))
        if common:
            f = common[0]
            x, y = first_month(xa[f]), first_month(xb[f])
            if x != y:
                lo, hi = (na, xa[f], xb[f]) if x < y else (nb, xb[f], xa[f]), (xb[f] if x < y else xa[f])
                what = f"compounded {sub} {FORM_PLURAL[f]}"
                side(x < y).append((f"price matters most: in the first month, {what} cost {first_month_note(lo[1])} against {first_month_note(hi)}",
                                    f"price: in the first month, {what} at {lo[0]} cost {first_month_note(lo[1])} against {first_month_note(hi)}"))
    la, lb = (PROFILES[x].get("fda_letter_count") or 0 for x in (a, b))
    if bool(la) != bool(lb):
        side(not la).append(("you want a clinic with no FDA warning letter",
                             f"{nb if lb else na} has an FDA warning letter and {na if lb else nb} has none"))
    sa, sb = (score_of(PROFILES[x]) or 0 for x in (a, b))
    if sa != sb:
        side(sa > sb).append((f"you want more of our four checks met: {max(sa, sb)} against {min(sa, sb)}",
                              f"{na if sa > sb else nb} meets {max(sa, sb)} of our four checks, against {min(sa, sb)}"))
    return fa, fb


def cmp_clinic_page(a, b, subs):
    na, nb = cmp_clinic_name(a), cmp_clinic_name(b)
    plans = [cmp_clinic_plan(x, subs[0]) for x in (a, b)]
    checked = max(r["last_seen"] for x in (a, b) for r in (cmp_clinic_plan(x, s) for s in subs))
    heads = [f'{parts.tile(x, cmp_clinic_name(x), 40, seller=PROFILES.get(x))}<a class="name" href="/sellers/{x}/">{escape(cmp_clinic_name(x))}</a><span class="cmp-sub">Online clinic</span>' for x in (a, b)]
    rows = [f"Compounded {s}" for s in subs] + ["Care fee", "FDA letter", "Checks", "Company", "Prices checked"]
    table = cmp_table(f"{na} and {nb}", heads, list(zip(rows, cmp_clinic_cells(a, subs, b), cmp_clinic_cells(b, subs, a))))
    pre = f'?a=p.{plans[0]["seller_slug"]}.{plans[0]["plan_slug"]}&amp;b=p.{plans[1]["seller_slug"]}.{plans[1]["plan_slug"]}'
    answer = cmp_clinic_answer(a, b, subs)
    verdict, _ = cmp_verdict(na, nb, *cmp_clinic_facts(a, b, subs), same="The one difference we hold is")
    nxt = cmp_next([(f"/sellers/{x}/", f"{cmp_clinic_name(x)}: plans, prices and checks") for x in (a, b)]
                   + [(f"/peptides/{x}/", f"{pep_short(x)}: FDA status and prices") for x in subs if x in PEPTIDE_SLUGS]
                   + ([("/weight-loss/", "Weight loss: every option compared")] if any(p[0] == "/weight-loss/" for p in PAGES) else []))
    body = cmp_body(f"{na} vs {nb}", checked, answer, table, [(f"/sellers/{a}/", na), (f"/sellers/{b}/", nb)], pre,
                    "Prices are the clinics' published monthly prices. Checks are facts we hold about the clinic, not a safety or quality grade.",
                    verdict, nxt)
    what = " and ".join(f"compounded {s}" for s in subs)
    desc = cmp_fit([f"{na} vs {nb} for {what}: monthly price, care fee, FDA warning letters and four background checks.",
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
        PAGES.append((cmp_path(_a, _b), cmp_path(_a, _b).strip("/") + "/index.html", _t, _d, _body, faq_schema(cmp_sub_faq_pairs(_a, _b)),
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


def compare_sub(slug):
    """One substance's column in the tool (owner task w2, 3 Nov 2026): status, clinic price per form, lowest per mg, letters,
    goal pages."""
    s = pep_status(slug)
    forms = {}
    for r in pep_plans(slug):
        forms.setdefault(plan_form_word(r), r)
    low, n = pep_low_shop(slug), len({r["seller_slug"] for r in pep_shops(slug)})
    nl = len(LETTER_SUBS.get(slug, []))
    return {"k": "sub", "h": f'<a class="name" href="/peptides/{slug}/">{escape(pep_short(slug))}</a><span class="cmp-sub">{s["label"]}</span>', "c": [
        ("FDA status", f'<span class="chip chip-{s["chip"]}">{s["label"]}</span><span class="cmp-sub">{s["sentence"]}.</span>'),
        ("Clinic plans from", "".join(f'<span class="cmp-form">{f} from <span class="num">{usd(r["price_monthly"])}/mo</span></span>'
                                      for f, r in forms.items()) or "No plan we track"),
        ("Lowest per mg", f'<span class="num">{per_mg(low["price_per_mg"])}/mg</span><span class="cmp-sub">lowest of {plural(n, "shop")}</span>' if low else "None shown"),
        ("FDA letters", (f'{plural(nl, "letter")} {"names" if nl == 1 else "name"} it' if nl else "None we track names it") if LETTER_SUBS_ON else "Not listed by substance"),
        ("Goal pages", ", ".join(f'<a href="/{g["slug"]}/">{g["name"]}</a>' for g in ALL_GOALS if g.get("page") and any(slug in subs_of(p) for p in g["peptides"])) or "None")]}


def cmp_tool_subs():
    """Adds the substances to /compare/: their options (the third group) and data, with the pair pages the tool opens."""
    global COMPARE_DATA
    if not COMPARE_DATA:
        return ""
    data = json.loads(COMPARE_DATA)
    subs = sorted(PEPTIDE_SLUGS, key=lambda x: pep_short(x).lower())
    data.update({f"u.{x}": compare_sub(x) for x in subs})
    data["_pairs"] = {f"u.{a}|u.{b}": p for p, _, kind, _, a, b in CMP_PAGES if kind == "sub"}
    COMPARE_DATA = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return ('<optgroup label="Substances">' + "".join(f'<option value="u.{x}">{escape(pep_short(x))}</option>' for x in subs) + "</optgroup>") if subs else ""


def cmp_links_in():
    """Popular comparisons on /compare/ (the substance pairs the tool can make, the most shops or plans first), the
    substances in the tool and the "Compared with" lines."""
    sub_opts = cmp_tool_subs()
    top = sorted((x for x in CMP_PAGES if x[2] == "sub"), key=lambda x: (-x[3], x[1].lower()))[:CMP_POPULAR]
    popular = (f'<section class="section" id="popular"><div class="wrap"><section class="related" aria-labelledby="popular-h">'
               f'<h2 id="popular-h" class="h-sources">Popular comparisons</h2><ul>'
               + "".join(f'<li><a href="{p}">{escape(t)}</a></li>' for p, t, *_ in top) + "</ul></section></div></section>\n") if top else ""
    for i, (path, out, title, desc, body, schema, crumb) in enumerate(PAGES):
        if path == "/compare/":
            body = body.replace("<!--cmp-subs-->", sub_opts)
            if popular:
                body = body.replace(COMPARE_JS, popular + COMPARE_JS, 1)
        elif path.startswith("/peptides/") and path.count("/") == 3:
            slug = path.split("/")[2]
            pairs = [c for c in CMP_PAGES if slug in (c[4], c[5])]
            c = max(pairs, key=lambda c: (c[3], c[1])) if pairs else None
            body = body.replace(f"<!--pair-foot:{slug}-->", f'<p class="small where-foot"><a href="{c[0]}">Compare side by side: {escape(c[1])}</a></p>' if c else "")
            body = body.replace(f"<!--pair-li:{slug}-->", "".join(f'<li><a href="{x[0]}">Compare side by side: {escape(x[1])}</a></li>'
                                                                 for x in sorted(pairs, key=lambda x: (-x[3], x[1]))))
            line = ""  # the pair is in "What to do next" now (owner task 3 Nov 2026)
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


def head_cta():
    """The header's one btn-ink, "Find a seller" (owner task 3 Nov 2026); under 1180px the last row of the open Menu."""
    return '<div class="head-cta"><a class="btn btn-ink" href="/sellers/">Find a seller</a></div>' if built("/sellers/") else ""


# Footer (pages.md, Every page; owner task 3 Nov 2026, the "Home v2" sketch): the logo column, then Browse, Trust and Data,
# each link only when its page is in this build.
FOOT_COLS = [("Browse", [("/", "Peptides by goal"), ("/sellers/", "Sellers"), ("/peptides/", "Peptides A to Z"), ("/compare/", "Compare"),
                         ("/learn/", "Guides")]),
             ("Trust", [("/how-we-rate/", "How we rate"), ("/disclosure/", "How we make money"), ("/corrections/", "Corrections"),
                        ("/privacy/", "Privacy")]),
             ("Data", [("/sources/", "Sources"), ("/fda-warning-letters/feed.xml", "FDA warning letters feed"), ("/about/", "About and contact")])]


def foot_cols():
    out = []
    for head, items in FOOT_COLS:
        links = "".join(f'<li><a href="{u}">{t}</a></li>' for u, t in items
                        if built(u) or u.endswith("feed.xml") and LETTERS_ALL)
        if links:
            hid = f"foot-{head.lower()}-h"
            out.append(f'<nav class="foot-col" aria-labelledby="{hid}"><h2 class="foot-h" id="{hid}">{head}</h2><ul class="foot-links">{links}</ul></nav>')
    return "".join(out)


LLMS_SECTIONS = [("/sellers/", "Sellers and online clinics"), ("/peptides/", "Peptides"), ("/compare/", "Comparisons"),
                 ("/learn/", "Guides"), ("/fda-warning-letters/", "FDA warning letters")]


def llms_sections():
    """llms.txt (pages.md, Every page): the pages by section, each heading with its page count from this build."""
    goal_paths = {goal_href(g) for g in ALL_GOALS if g.get("page")}
    groups = {"Home and goals": [], **{name: [] for _, name in LLMS_SECTIONS}, "About the site": []}
    for p, _, t, d, *_ in PAGES:
        if p in NOINDEX or p in CANON:
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
    if (ROOT / "assets" / "photos").exists():
        shutil.copytree(ROOT / "assets" / "photos", DIST / "assets" / "photos")
    if (ROOT / "assets" / "logos").exists():
        shutil.copytree(ROOT / "assets" / "logos", DIST / "assets" / "logos")
    for f in (ROOT / "assets" / "og").glob("*.png"):
        shutil.copy(f, DIST / "assets" / "og" / f.name)
    shutil.copytree(ROOT / "assets" / "body", DIST / "assets" / "body")
    (DIST / "assets" / "tokens.css").write_text(tokens_css(), encoding="utf-8")
    shutil.copy(ROOT / "design" / "bundle.css", DIST / "assets" / "bundle.css")
    for path, out, title, desc, body, schema, crumb in PAGES:
        if crumb:
            schema = schema + breadcrumb_schema(crumb)
        for c, t in CANON.items():
            if path not in (c, t):
                body = body.replace(f'href="{c}"', f'href="{t}"')
        target = DIST / out
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page(path, title, desc, body, schema, crumb), encoding="utf-8")
    (DIST / "404.html").write_text(page("/404", "Page not found | Peptide Chooser",
                                        "This page does not exist on Peptide Chooser. Go to the home page or compare peptide options by goal; the link may be old or mistyped.", NOT_FOUND), encoding="utf-8")
    # Redirects (owner task w2, 3 Nov 2026; empty until the owner approves a URL change, rule 8): data/redirects.json maps
    # an old path to its new one; GitHub Pages has no server redirects, so each old path gets a page with a meta refresh,
    # the canonical of the new page and noindex. Never a path the build already has. A redirect to a page this data does
    # not build (/sellers/ in the repo data, which holds no sellers) is left out, never pointed at a missing page.
    for old_path, new_path in REDIRECTS.items():
        assert not built(old_path), f"redirect from {old_path}, which is still a page"
        if not built(new_path) and not (DIST / new_path.strip("/") / "index.html").exists():
            print(f"redirect {old_path} left out: {new_path} is not built with this data")
            continue
        target = DIST / old_path.strip("/") / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Moved</title>'
                          f'<meta name="robots" content="noindex"><link rel="canonical" href="{SITE}{new_path}">'
                          f'<meta http-equiv="refresh" content="0; url={new_path}"></head>'
                          f'<body><p>This page moved: <a href="{new_path}">{SITE}{new_path}</a></p></body></html>\n', encoding="utf-8")
    if LETTERS_ALL:
        (DIST / "fda-warning-letters" / "feed.xml").write_text(letters_feed(), encoding="utf-8")
    # Web app manifest (design book, README, Logo): the name and the icons drawn from the mark by tools/og.py.
    (DIST / "site.webmanifest").write_text(json.dumps({
        "name": "Peptide Chooser", "short_name": "Peptide Chooser", "start_url": "/", "display": "browser",
        "background_color": COLOR["white"], "theme_color": COLOR["white"],
        "icons": [{"src": "/assets/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"},
                  {"src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png"}]}, indent=2) + "\n")
    paid.write_out_pages(DIST, {slug: seller_base(r["seller_name"]) for slug, r in PROFILES.items()})
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
    (DIST / "windows").mkdir(exist_ok=True)
    for k, html in GOAL_PANELS.items():
        (DIST / "windows" / f"goal-{k}.json").write_text(json.dumps({"html": html}), encoding="utf-8")
    (DIST / "assets" / "nav.js").write_text(NAV_SCRIPT + STATE_SCRIPT + EVENTS_SCRIPT, encoding="utf-8")
    if home.JS:
        (DIST / "assets" / "home.js").write_text(home.JS, encoding="utf-8")
    if home.ROWS:
        (DIST / home.WHERE_JSON).write_text(home.ROWS, encoding="utf-8")
    (DIST / "windows").mkdir(exist_ok=True)
    for key, html in SELLER_WINDOWS.items():
        (DIST / "windows" / f"{key}.json").write_text(json.dumps({"html": html}), encoding="utf-8")
    for g in ALL_GOALS:
        for p in g["peptides"]:
            if option_plans(g, p):
                (DIST / "windows" / f"{clinic_key(g, p)}.json").write_text(json.dumps({"html": clinic_window(g, p)}), encoding="utf-8")
    (DIST / "search-index.json").write_text(json.dumps(search_index(), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    lastmod = DATA_CHECKED  # sitemap lastmod and the footer's "Data checked"
    urls = "".join(f"<url><loc>{SITE}{p[0]}</loc><lastmod>{lastmod}</lastmod></url>" for p in PAGES if p[0] not in NOINDEX and p[0] not in CANON)
    (DIST / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    (DIST / "pages.json").write_text(json.dumps([{"path": p[0], "title": p[2]} for p in PAGES] + [{"path": "/404", "title": "Page not found | Peptide Chooser"}]))
    print("built", len(PAGES) + 1, "pages")
    if PEPTIDE_SLUGS:
        print(f"peptide pages: {len(PEPTIDE_SLUGS) - len(PEP_THIN)} indexed, {len(PEP_THIN)} noindex (fewer than {PEP_MIN_SIGNALS} of the six)")
        for x in PEP_THIN:
            print(f"  noindex /peptides/{x}/: has {', '.join(k for k, v in pep_signals(x).items() if v) or 'only its status'}")
    if PROFILES:  # the Legal pages check per state on the seller pages (owner task 3 Nov 2026), for the report
        n = {k: 0 for k in LEGAL_STATES}
        for r in PROFILES.values():
            n[legal_state(r)[0]] += 1
        out = [r.get("legal_check_outcome") for r in PROFILES.values() if legal_state(r)[0] == "Could not check"]
        print("legal pages: " + ", ".join(f"{k} {v}" for k, v in n.items())
              + (f" (blocked {out.count('blocked')}, failed {out.count('failed')})" if out else ""))


# The Learn section (pages.md, Learn and Guide): /learn/ and the guides, from guides.py, which reads this module's helpers.
# A guide whose path is in data/redirects.json is not built; its path becomes a redirect page in main() (owner answers
# 1 a and 5 a, ODOBRENO PRAVILA - Karlo - 3. 11. 2026)
REDIRECTS = json.loads((ROOT / "data" / "redirects.json").read_text()) if (ROOT / "data" / "redirects.json").exists() else {}
guides.GUIDES[:] = [g for g in guides.GUIDES if f"/learn/{g['slug']}/" not in REDIRECTS]
PAGES += guides.pages(sys.modules[__name__])
# Home's sections under the hero (pages.md, Home), from home.py, once every helper above exists.
PAGES = [home.finish(sys.modules[__name__], p) if p[0] == "/" else p for p in PAGES]


def what_next(g):
    """"What to do next" on a goal page (pages.md, Category; owner UX audit B12, 3 Nov 2026), before the sources: three
    links from data, each left out when its target is missing: the goal's guide (`guide`), the compare pair with the most
    plans and shops among the goal's substances, and /sellers/ filtered to the goal's substance with the most sellers."""
    subs = {x for p in g["peptides"] for x in subs_of(p)}
    links = []
    gd = next((x for x in guides.GUIDES if x["slug"] == g.get("guide")), None)
    if gd:
        links.append(f'<li><a href="/learn/{gd["slug"]}/">Read the guide: {gd["title"]}</a></li>')
    pairs = [c for c in CMP_PAGES if c[2] == "sub" and (c[4] in subs or c[5] in subs) and built(c[0])]
    if pairs:
        c = max(pairs, key=lambda c: (c[3], c[1]))
        links.append(f'<li><a href="{c[0]}">Compare side by side: {escape(c[1])}</a></li>')
    if built("/sellers/"):
        count = {s: sum(s in shop_subs(r) for r in SHOPS.values()) + sum(s in clinic_subs(r) for r in CLINIC_PROFILES.values()) for s in subs}
        best = max((s for s in count if count[s]), key=lambda s: (count[s], s), default=None)
        if best:
            name = escape(re.sub(r" *\(.*\)$", "", sub_label(best)))
            links.append(f'<li><a href="/sellers/#substance={best}">Every seller of {name}, with its checks</a></li>')
    # beside it from 900px, the goals strip (pages.md, Category): one section, two columns, so the page stays short
    strip = re.search(r'<div class="wrap">(.*?)</div>\s*</section>', goals_strip("Compare other goals", g["slug"]), re.S)
    nxt = f'<div><h2 class="h-sources">What to do next</h2><ul class="next-list">{"".join(links)}</ul></div>' if links else ""
    other = f'<div id="other-goals">{strip.group(1)}</div>' if strip else ""
    return f'<section class="section goal-sec goal-next" id="next"><div class="wrap goal-two">{nxt}{other}</div></section>' if nxt or other else ""


_GOALS_BY_SLUG = {g["slug"]: g for g in ALL_GOALS}
PAGES = [p[:4] + (re.sub(r"<!--next:([a-z0-9-]+)-->", lambda m: what_next(_GOALS_BY_SLUG[m.group(1)]), p[4]),) + p[5:]
         if "<!--next:" in p[4] else p for p in PAGES]


# /sources/ (pages.md, Sources; owner task 3 Nov 2026): every source the site cites, read from the numbered source lists of
# the pages this build has, plus the database's own sources (FDA status rows, warning letters, state registries, the pages
# the crawler reads). Nothing is typed: a name, link and date come from the list item or the data, and a group with no
# entries is left out.
def cited_sources():
    """{url: [text, has_link, [(path, title), ...]]} from every page's source lists, in first-cited order."""
    out = {}
    for path, _, title, _, body, *_ in PAGES:
        for ol in re.findall(r'<ol class="[^"]*\bsources\b[^"]*"[^>]*>(.*?)</ol>', body, re.S):
            for li in re.findall(r"<li[^>]*>(.*?)</li>", ol, re.S):
                m = re.match(r'(.*?):\s*(?:<a href="(https?://[^"]+)"[^>]*>[^<]*</a>|(https?://\S+))\s*$', li.strip(), re.S)
                if not m:
                    continue
                url = unescape(m.group(2) or m.group(3))
                e = out.setdefault(url, [m.group(1).strip(), bool(m.group(2)), []])
                # a list the database reads for many substances is cited on each peptide page as "FDA, status of X";
                # the page's own title, where another page cites one, names it better
                if e[0].startswith("FDA, status of ") and not m.group(1).startswith("FDA, status of "):
                    e[0] = m.group(1).strip()
                name = "Home" if path == "/" else title.replace(" | Peptide Chooser", "")
                if (path, name) not in e[2]:
                    e[2].append((path, name))
    return out


def host(url):
    return re.sub(r"^www\.", "", urlparse(url).netloc)


def used_on(pages, most=3):
    links = ", ".join(f'<a href="{p}">{escape(t)}</a>' for p, t in pages[:most])
    return f"Cited on {links}" + (f" and {plural(len(pages) - most, 'more page')}" if len(pages) > most else "") + "."


def src_li(name, url, link, take, checked="", ids=()):
    """One /sources/ entry. `ids`: the ids Home's footnotes link (src-1, src-price-hair, src-plan-...), so a footnote on Home
    lands on its line here (owner answer Q3 a, 3 Nov 2026); the first is the item's id, the rest empty anchors in it."""
    head = (f'<a href="{url}" rel="nofollow">{name}</a>' if link and url.startswith("http") else
            f'<a href="{url}">{name}</a>' if link else f"{name}: {url}" if url else name)
    when = f'<span class="src-date">Checked {nice_date(checked)}</span>' if checked else ""
    ids = list(dict.fromkeys(ids))
    anchors = "".join(f'<span id="{i}"></span>' for i in ids[1:])
    id_attr = f' id="{ids[0]}"' if ids else ""
    return f'<li{id_attr}>{anchors}<span class="src-name">{head}</span><span class="src-take">{take}</span>{when}</li>'


def sources_body():
    cited = cited_sources()
    # Home's source ids by url (SOURCES_HOME: the numbered list Home's option rows link), placed on the entry for that url
    home_ids = {}
    for sid, url in re.findall(r'<li id="(src-[^"]+)">.*?<a href="([^"]+)"', SOURCES_HOME):
        home_ids.setdefault(unescape(url), []).append(sid)
    plan_ids = [sid for sid in re.findall(r'<li id="(src-plan-[^"]+)">', SOURCES_HOME)]
    seller_hosts = {host("https://" + r["domain"]) for r in PROFILES.values() if r.get("domain")}
    seller_hosts |= {host(r["pricing_url"]) for r in PLANS if r.get("pricing_url")}
    db_urls = {r["source_url"] for r in LEGAL_DB or [] if r.get("source_id") != "hand_hhs_policy"}
    fda, medline, pubmed, prices = [], [], {}, []
    for url, (text, link, pages) in cited.items():
        h = host(url)
        if url in db_urls:
            continue  # listed once below, with every substance the database reads from it
        if h.endswith("fda.gov") or h in ("dailymed.nlm.nih.gov", "www.hhs.gov", "www.federalregister.gov"):
            fda.append(src_li(text, url, link, used_on(pages), ids=home_ids.get(url, ())))
        elif h == "medlineplus.gov":
            medline.append(src_li(text, url, link, used_on(pages), ids=home_ids.get(url, ())))
        elif h == "pubmed.ncbi.nlm.nih.gov":
            for p in [p for p in pages if p[0].startswith("/learn/")] or pages:  # by guide; a study no guide cites, by its page
                pubmed.setdefault(p, []).append(src_li(text, url, link, ""))
        elif h not in seller_hosts:
            prices.append(src_li(text, url, link, used_on(pages), ids=home_ids.get(url, ())))
    # the database's FDA sources: one entry per source list (the status rows link one page, or one openFDA query per substance)
    by_src = {}
    for r in LEGAL_DB or []:
        if r.get("source_id") == "hand_hhs_policy":  # the HHS rows come from legal.hhs_policy, whose sources are listed above
            continue
        by_src.setdefault(r["source_id"], []).append(r)
    for rows in by_src.values():
        urls = sorted({r["source_url"] for r in rows})
        url = urls[0] if len(urls) == 1 else urls[0].split("?")[0]
        name = cited[url][0] if url in cited and not cited[url][0].startswith("FDA, status of ") else host(url) + urlparse(url).path
        subs = sorted({r["canonical_name"] for r in rows})
        pages = [pg for u in urls if u in cited for pg in cited[u][2]]
        fda.append(src_li(name, url, True, ids=[i for u in urls for i in home_ids.get(u, ())], take=f"FDA status of {plural(len(subs), 'substance')} in our database: {', '.join(subs[:6])}"
                          + (f" and {len(subs) - 6} more" if len(subs) > 6 else "") + f", first seen {nice_date(min(r['first_seen_by_us'] for r in rows))}."
                          + (" " + used_on(list(dict.fromkeys(pages))) if pages else "")))
    if LETTERS_ALL:
        urls = [r["letter_url"] for r in LETTERS_ALL if r.get("letter_url")]
        index = os.path.commonprefix(urls).rsplit("/", 1)[0] + "/" if len(urls) > 1 else ""
        dates = sorted(r["letter_date"] for r in LETTERS_ALL if r.get("letter_date"))
        if index.count("/") > 3 and dates:
            fda.append(src_li("FDA warning letters", index, True,
                              f'{plural(len(LETTERS_ALL), "letter")} to peptide sellers, compounders and online clinics, '
                              f'{nice_date(dates[0])} to {nice_date(dates[-1])}, each read and listed on '
                              f'<a href="/fda-warning-letters/">our letters page</a>.'))
    # state registries: the seller checks that found the company in a state's own file
    regs = {}
    for r in PROFILES.values():
        if r.get("entity_evidence") == "registry" and r.get("entity_source_url"):
            regs.setdefault((r.get("entity_state") or "", r["entity_source_url"]), []).append(r)
    registries = [src_li(f"{st} state company registry" if st else "State company registry", url, url.startswith("http"),
                         f'Found in a state registry for {plural(len(rows), "seller")}: '
                         + ", ".join(f'<a href="/sellers/{r["seller_slug"]}/">{escape(seller_name(r))}</a>' for r in rows) + ".",
                         max((r.get("registry_checked_on") or "" for r in rows), default=""))
                  for (st, url), rows in sorted(regs.items())]
    # our own database: what the crawler reads, with the newest date each part was seen
    own = []
    if PRODUCTS:
        shops = {r["seller_slug"] for r in PRODUCTS}
        own.append(src_li("Shop product pages", "/sellers/", True, f"Price, amount and lab report of {plural(len(PRODUCTS), 'product')} "
                          f"at {plural(len(shops), 'shop')}.", max((r.get("last_seen") or "" for r in PRODUCTS), default="")))
    if PLANS:
        clinics = {r["seller_slug"] for r in PLANS}
        own.append(src_li("Online clinic plan pages", "/sellers/#clinics" if built("/sellers/") else "", built("/sellers/"),
                          f"Monthly price and fees of {plural(len(PLANS), 'plan')} at {plural(len(clinics), 'clinic')}.",
                          max((r.get("last_seen") or "" for r in PLANS), default=""),
                          ids=plan_ids + [i for u, ids in home_ids.items() if host(u) in seller_hosts for i in ids]))
    if PROFILES:
        own.append(src_li("Seller checks", "/how-we-rate/", True, f"The checks on {plural(len(PROFILES), 'seller')}.",
                          max((r.get("score_checked_on") or "" for r in PROFILES.values()), default="")))
    if DATA.get("pulled_at") and own:
        own.append(src_li("Peptide Chooser database", "", False, "The copy this build of the site was made from.", DATA["pulled_at"][:10]))
    groups = [("src-fda", "FDA and HHS" if HHS else "FDA", fda), ("src-medlineplus", "MedlinePlus", medline)]
    sec = []
    for gid, head, items in groups + [("src-prices", "Price pages", prices), ("src-registries", "State registries", registries),
                                      ("src-database", "Our own database", own)]:
        if gid == "src-prices" and pubmed:
            sec.append('<section class="src-group" id="src-pubmed" aria-labelledby="src-pubmed-h"><h2 id="src-pubmed-h">PubMed studies</h2>'
                       + "".join(f'<h3><a href="{p}">{escape(t)}</a></h3><ul class="src-list">{"".join(items)}</ul>' for (p, t), items in pubmed.items())
                       + "</section>")
        if items:
            sec.append(f'<section class="src-group" id="{gid}" aria-labelledby="{gid}-h"><h2 id="{gid}-h">{head}</h2>'
                       f'<ul class="src-list">{"".join(items)}</ul></section>')
    jumps = [(f"#{m.group(1)}", m.group(2)) for m in re.finditer(r'<section class="src-group" id="([^"]+)"[^>]*><h2 id="[^"]+">([^<]+)</h2>', "".join(sec))]
    return f"""
<section class="page sources-page"><div class="wrap prose">
<h1>Sources</h1>
<p class="lede">Where every number on this site comes from: each source, what we take from it and when we last checked it.</p>
{jump_row(jumps)}
{"".join(sec)}
</div></section>
"""


PAGES.append(("/sources/", "sources/index.html", "Sources: where every number comes from | Peptide Chooser",
              "Every source behind the numbers on Peptide Chooser: FDA pages and openFDA, MedlinePlus, PubMed studies, state registries and our own database.",
              sources_body(), "", [("/sources/", "Sources")]))


if __name__ == "__main__":
    main()
