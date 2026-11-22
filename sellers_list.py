"""/sellers/, Sellers v2 (design/pages/sellers-list.md, Sellers v2; nav-parts.md, Filter column and Bottom sheet; owner
prototype design-2026-11-18, queue block 11). The page's words, counts and order are those of the live page; only the
look and the filter controls change. `b` is the build module."""
import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# A seller matches a goal when it sells one of the substances of that goal's Home option rows (data, not code).
GOAL_SUBS = (json.loads((ROOT / "data" / "goal-substances.json").read_text(encoding="utf-8")).get("goals") or {})
PRICE_BANDS = [("u100", "Under $100"), ("u200", "$100 to $200"), ("o200", "Over $200")]
FIRST = 25


def goals_of(subs):
    s = set(subs)
    return [g for g, xs in GOAL_SUBS.items() if s & set(xs)]


def letter_chip(b, r):
    """The FDA letter chip under the name, only when the seller has letters (the old FDA letters column)."""
    return b.home.where_letters(b, r) if (r.get("fda_letter_count") or 0) > 0 else ""


def not_in(b, slug):
    states = (b.CLINIC_STATES.get(slug) or {}).get("not_in") or []
    return f'<span class="sl-notin">Not in {", ".join(states)}</span>' if states else ""


def act(b, r, clinic):
    slug = r["seller_slug"]
    if clinic and b.has_paid(slug):
        return b.clinic_button(slug, "See plans", placement="clinic table")
    return f'<span class="pick-act"><a class="btn btn-line btn-sm" href="/sellers/{slug}/">Our review</a></span>'


def row(b, r, clinic, i):
    slug = r["seller_slug"]
    subs = b.clinic_subs(r) if clinic else b.shop_subs(r)
    toks = " ".join([b.met_checks(r)] + b.filter_tokens("sellers", slug)).strip()
    if clinic:
        plans = b.clinic_plan_rows(r)
        low = min((float(p["price_monthly"]) for p in plans), default=None)
        what = b.subs_words(sorted(subs, key=lambda x: b.sub_label(x).lower()))
        price = b.usd(low) + "/mo" if low is not None else "unknown"
        extra = f' data-low="{low if low is not None else ""}"{b.state_attrs(slug)}'
        tile = b.parts.tile(slug, b.seller_base(b.seller_name(r)), 40, seller=r)
    else:
        lo = b.compare_ppm(r)[0]
        what = b.subs_words([x["substance_slug"] for x in b.SELLER_SUBS.get(slug, [])], r.get("substance_count"))
        price = b.per_mg(lo) + "/mg" if lo is not None else "unknown"
        extra = (f' data-p="{r.get("product_count") or 0}" data-m="{lo if lo is not None else ""}"'
                 f' data-t="{r.get("first_seen") or ""}"')
        tile = b.parts.tile(slug, b.seller_base(b.seller_name(r)), 40, shop=True)
    more = ' class="more"' if i >= FIRST else ""
    under = letter_chip(b, r) + (not_in(b, slug) if clinic else "")
    return (f'<tr{more} data-c="{toks}" data-s="{r["score"]}" data-subs="{" ".join(subs)}" data-goals="{" ".join(goals_of(subs))}"'
            f' data-n="{escape(b.seller_name(r).lower())}" data-paid="{1 if b.has_paid(slug) else 0}"{extra}>'
            f'<td><span class="cell-pic">{tile}<a class="name" href="/sellers/{slug}/">{b.seller_name(r)}</a></span>'
            + (f'<span class="sl-under">{under}</span>' if under else "") + '</td>'
            f'<td class="sl-what" data-l="{"What it prescribes" if clinic else "Sells"}">{escape(what)}</td>'
            f'<td class="num sl-from" data-l="From">{price}</td>'
            f'<td class="sl-checks" data-l="Checks">{b.check_bar(r)}</td>'
            f'<td class="act">{act(b, r, clinic)}</td></tr>')


def table(b, rows, clinic):
    tid, sid = ("clinics-table", "clinics") if clinic else ("sellers-table", "shops")
    noun, what = ("Clinic", "What it prescribes") if clinic else ("Shop", "Sells")
    h2 = "Online clinics" if clinic else "Research-use shops"
    note = ('\n      <p class="small sellers-note">Online clinics publish no lab reports, so a clinic is checked on four facts, a shop on five. '
            'A score is never compared across the two kinds.</p>') if clinic else ""
    return f"""
    <section class="sellers-sec" id="{sid}" aria-labelledby="{sid}-h">
      <h2 id="{sid}-h" class="h-sources">{h2}</h2>{b.STATE_N if clinic else ""}
      <div class="tbl-wrap"><table class="tbl tbl-cards tbl-sellers tbl-where tbl-sl" id="{tid}"><caption class="vh">{h2}, most checks first</caption>
        <thead><tr><th scope="col">{noun}</th><th scope="col">{what}</th><th scope="col" class="num">From</th><th scope="col">Checks</th><th scope="col" class="sl-link-h">Link</th></tr></thead>
        <tbody>{"".join(row(b, r, clinic, i) for i, r in enumerate(rows))}</tbody>
      </table></div>{note}
    </section>"""


def opt(group, value, label, kind="checkbox", tab=""):
    t = f' data-tab="{tab}"' if tab else ""
    return (f'<label class="sl-o"{t}><input type="{kind}" name="sl-{group}" value="{value}" data-k="{group}" data-filter="{group}" data-value="{value}">'
            f'<span class="sl-l">{label}</span><span class="sl-n"></span></label>')


def group(gid, label, body, new=False, tab="", summary="Any", open_=True):
    t = f' data-tab="{tab}"' if tab else ""
    tag = ' <span class="sl-new">new</span>' if new else ""
    return (f'<details class="sl-g" data-g="{gid}"{t}{" open" if open_ else ""}><summary><span class="sl-gl">{label}{tag}</span>'
            f'<span class="sl-sum" data-any="{summary}">{summary}</span></summary><div class="sl-opts">{body}</div></details>')


def side(b, shops, clinics):
    """The Filter column (desktop) and Bottom sheet (phones): every group of the prototype; JavaScript fills the counts."""
    n = {}
    for r in clinics:
        for s in b.clinic_subs(r):
            n[s] = n.get(s, 0) + 1
    for r in shops:
        for s in b.shop_subs(r):
            n[s] = n.get(s, 0) + 1
    subs = sorted(n, key=lambda s: (-n[s], b.sub_label(s).lower()))
    short = lambda s: re.sub(r" *\(.*\)$", "", b.sub_label(s))
    goals = [g for g in b.CHOOSER_GOALS if g["slug"] in GOAL_SUBS]
    k = len(b.SCORE_CHECKS)
    mins = "".join(opt("min", i, "Any" if i == 0 else f"{i} of {k}" if i == k else f"{i} or more", "radio") for i in range(k + 1))
    checks = "".join(opt("check", key, t) for key, _, t in b.SELLER_CHECKS)
    filt = ""
    for g, pre, label, words in b.FILTER_GROUPS:
        vals = b.filter_values(g)
        if vals:
            filt += group(pre, label, "".join(opt(pre, v, words[v]) for v in vals), summary="", open_=False)
    codes = "".join(f'<button type="button" class="sl-st" data-st="{c}" aria-pressed="false" title="{escape(name)}">{c}</button>'
                    for c, name in sorted(b.STATES.items()))
    state = (f'<div class="sl-states"><button type="button" class="sl-st" data-st="all" aria-pressed="true">All</button>{codes}</div>'
             f'<div class="vh">{b.state_filter("clinics", "clinics")}</div><p class="small sl-stnote">Pick your state to hide clinics that do not ship there.</p>')
    link = group("link", "Link", opt("link", "paid", "Only clinics we can link to"), new=True, tab="clinics", summary="", open_=False) \
        if any(b.has_paid(r["seller_slug"]) for r in clinics) else ""
    body = (group("goal", "Goal", "".join(opt("goal", g["slug"], g["label"]) for g in goals), new=True)
            + group("substance", "Substance", "".join(opt("substance", s, escape(short(s))) for s in subs)
                    + '<button type="button" class="sl-more" hidden></button>')
            + (group("state", "Your state", state, tab="clinics", summary="All states", open_=False) if clinics else "")
            + group("min", "Minimum checks", mins)
            + group("check", "Checks met", checks, summary="", open_=False)
            + filt
            + (group("price", "Price per month", "".join(opt("price", v, t) for v, t in PRICE_BANDS), new=True, tab="clinics", summary="", open_=False) if clinics else "")
            + link)
    return f"""<aside class="sl-side" id="sellers-fbody" aria-label="Filters" hidden>
      <div class="sl-sheet-hd"><span class="sl-handle" aria-hidden="true"></span><h2 class="sl-h">Filters</h2><button type="button" class="sl-clear">Clear all</button><button type="button" class="sl-x" aria-label="Close filters">×</button></div>
      <div class="sl-sortg" hidden></div>
      {body}
      <div class="sl-foot"><button type="button" class="sl-clear sl-clear-f">Clear all</button><button type="button" class="btn btn-ink sl-show">Show</button></div>
    </aside>"""


def page(b):
    shops = sorted(b.SHOPS.values(), key=b.sellers_order)
    clinics = sorted(b.CLINIC_PROFILES.values(), key=lambda r: (*b.paid_rank(r["seller_slug"]), b.seller_name(r).lower()))
    checked = max((r["score_checked_on"] for r in b.PROFILES.values() if r.get("score_checked_on")), default="")
    lede = (f"{b.plural(b.site_count('clinics'), 'online clinic')} that prescribe and ship, then {b.plural(b.site_count('shops'), 'research-use shop')}." if clinics else
            f"{b.plural(b.site_count('shops'), 'research-use shop')}.")
    # queue block 39 (out-02, Fix 2): the first screen answers "where to buy peptides"; counts from data
    intro = ("For use in people, buy peptides with a prescription from an online clinic. Research-use peptide shops sell vials "
             "that are not approved for use in people, so we rate every one of them Lab-use only. "
             f"Below are the {b.plural(b.site_count('clinics'), 'online clinic')} and {b.plural(b.site_count('shops'), 'shop')} we track, "
             'each with its checks and the date we ran them. <a href="/sellers/#clinics">See the online clinics first</a>.')
    tabs = ("<div class=\"seg sellers-tabs\" role=\"group\" aria-label=\"Show\" hidden>"
            f'<button type="button" class="seg-b" data-type="clinics"{b.ev("tab_change", tab="clinics")} aria-pressed="true">Online clinics ({b.site_count("clinics")})</button>'
            f'<button type="button" class="seg-b" data-type="shops"{b.ev("tab_change", tab="shops")} aria-pressed="false">Research-use shops ({b.site_count("shops")})</button></div>') if clinics and shops else ""
    sorts = "".join(f'<option value="{k}">{t}</option>' for k, t in b.SELLER_SORTS)
    bar = f"""<div class="letters-filter sellers-filter sl-bar" hidden>
      {tabs}
      <div class="sf-field sf-name"><label class="vh" for="sellers-q">Filter by name</label><span class="sf-q"><input class="input" id="sellers-q" type="text" autocomplete="off" placeholder="Filter by name" data-filter="name" data-value="text"><button type="button" class="sf-clear" id="sellers-clear">Clear</button></span></div>
      <div class="sf-field sf-sort sort-shops"><label for="sellers-sort">Sort</label><select class="input" id="sellers-sort" data-filter="sort">{sorts}</select></div>
      <div class="sf-field sf-sort sort-clinics"><label for="clinics-sort">Sort</label><select class="input" id="clinics-sort" data-filter="sort"><option value="checks">Most checks</option><option value="low">Lowest monthly price</option></select></div>
      <div class="sl-quick"><button type="button" class="sl-q sl-fbtn" aria-controls="sellers-fbody" aria-expanded="false">Filters <span class="cf-count"></span></button><button type="button" class="sl-q" data-open="goal">Goal</button><button type="button" class="sl-q" data-open="substance">Substance</button><button type="button" class="sl-q" data-open="state" data-tab="clinics">Your state</button><button type="button" class="sl-q" data-open="min">Minimum checks</button></div>
    </div>"""
    return f"""
<section class="section letters-hd">
  <div class="wrap">
    <h1>Where to buy peptides</h1>
    <p class="lede">{intro}</p>
    <p class="lede">{lede}</p>
    <p class="letters-stamp">{f'<span class="stamp">Checked {b.nice_date(checked)}</span>' if checked else ""}</p>
  </div>
</section>
<section class="band-2 sl2" id="sellers-list" data-state-root>
  <div class="wrap">
    <div class="sellers-top">{bar}</div>
    <div class="sl-grid">
      {side(b, shops, clinics)}
      <div class="sl-scrim" hidden></div>
      <div class="sl-main">
        <div class="sl-head" hidden><p class="sl-count" id="sellers-n" aria-live="polite"></p><div class="cf-pills" aria-label="Active filters" role="group"></div></div>
        {table(b, clinics, True) if clinics else ""}{table(b, shops, False) if shops else ""}
        <p class="legal-more sellers-more" hidden><button type="button" class="btn btn-line" id="sellers-all">Show all</button></p>
        {b.COMPARE_LINK}
        <p class="small" style="margin-top:16px">Checks are facts we hold about the seller, not a safety or quality grade. <a href="/how-we-rate/">How we rate</a></p>
      </div>
    </div>
  </div>
</section>
{JS.replace("FIRST_N", str(FIRST))}
"""


JS = r"""<script>
// Sellers v2 (sellers-list.md; nav-parts.md, Filter column and Bottom sheet): the tabs, the name, the sort and the filter
// groups. Inside a group the options add up; groups narrow each other; "Checks met" needs every chosen check. Each option
// shows how many rows of the open tab it gives; an option giving 0 hides unless chosen. State in the hash; "Your state"
// in this browser (nav.js). Reads only the rows' data- attributes.
(function(){var root=document.getElementById('sellers-list');if(!root)return;
var bar=root.querySelector('.sl-bar'),side=root.querySelector('.sl-side'),scrim=root.querySelector('.sl-scrim'),head=root.querySelector('.sl-head'),
tb=document.getElementById('sellers-table'),ct=document.getElementById('clinics-table'),
segs=[].slice.call(root.querySelectorAll('.sellers-tabs .seg-b')),tabs=root.querySelector('.sellers-tabs'),
q=document.getElementById('sellers-q'),clr=document.getElementById('sellers-clear'),so=document.getElementById('sellers-sort'),cs=document.getElementById('clinics-sort'),
n=document.getElementById('sellers-n'),pills=root.querySelector('.cf-pills'),more=root.querySelector('.sellers-more'),all=document.getElementById('sellers-all'),
fbtn=root.querySelector('.sl-fbtn'),show=root.querySelector('.sl-show'),stSel=root.querySelector('select[data-state]'),
ins=[].slice.call(side.querySelectorAll('input[data-k]')),groups=[].slice.call(side.querySelectorAll('.sl-g')),
rows=tb?[].slice.call(tb.tBodies[0].rows):[],crows=ct?[].slice.call(ct.tBodies[0].rows):[],secS=document.getElementById('shops'),secC=document.getElementById('clinics'),
type=ct?'clinics':'shops',open=false,subsAll=false,FIRST=FIRST_N,wide=window.matchMedia('(min-width: 900px)');
rows.concat(crows).forEach(function(r,i){r._i=i;});
function num(r,k){var v=r.getAttribute('data-'+k);return v===''||v===null?null:parseFloat(v);}
function has(r,k,v){return(' '+(r.getAttribute('data-'+k)||'')+' ').indexOf(' '+v+' ')>=0;}
var BAND={u100:function(p){return p!==null&&p<100;},u200:function(p){return p!==null&&p>=100&&p<=200;},o200:function(p){return p!==null&&p>200;}};
var SORT={checks:function(a,b){return a._i-b._i;},products:function(a,b){return num(b,'p')-num(a,'p')||a._i-b._i;},
price:function(a,b){var x=num(a,'m'),y=num(b,'m');return x===null?(y===null?a._i-b._i:1):y===null?-1:x-y||a._i-b._i;},
name:function(a,b){return a.getAttribute('data-n').localeCompare(b.getAttribute('data-n'));},
since:function(a,b){return(a.getAttribute('data-t')||'').localeCompare(b.getAttribute('data-t')||'')||a._i-b._i;},
low:function(a,b){var x=num(a,'low'),y=num(b,'low');return x===null?(y===null?a._i-b._i:1):y===null?-1:x-y||a._i-b._i;}};
function inTab(x){var t=x.getAttribute('data-tab');return!t||t===type;}
function sel(){var s={goal:[],substance:[],min:0,check:[],sold:[],form:[],price:[],link:[]};
ins.forEach(function(i){if(!i.checked||!inTab(i.closest('[data-tab]')||i))return;var k=i.getAttribute('data-k');if(k==='min')s.min=parseInt(i.value,10);else s[k].push(i.value);});return s;}
function pass(r,s,skip){var t=q.value.trim().toLowerCase();if(t&&(r.getAttribute('data-n')||'').indexOf(t)<0)return false;
if(type==='clinics'&&r.hasAttribute('data-state-out'))return false;
if(skip!=='goal'&&s.goal.length&&!s.goal.some(function(v){return has(r,'goals',v);}))return false;
if(skip!=='substance'&&s.substance.length&&!s.substance.some(function(v){return has(r,'subs',v);}))return false;
if(skip!=='min'&&num(r,'s')<s.min)return false;
if(skip!=='check'&&!s.check.every(function(v){return has(r,'c',v);}))return false;
if(skip!=='sold'&&s.sold.length&&!s.sold.some(function(v){return has(r,'c','sold-'+v);}))return false;
if(skip!=='form'&&s.form.length&&!s.form.some(function(v){return has(r,'c','form-'+v);}))return false;
if(type==='clinics'&&skip!=='price'&&s.price.length&&!s.price.some(function(v){return BAND[v](num(r,'low'));}))return false;
if(type==='clinics'&&skip!=='link'&&s.link.length&&r.getAttribute('data-paid')!=='1')return false;return true;}
function R(){return type==='clinics'?crows:rows;}
function count(s,k,v){var t={};for(var x in s)t[x]=s[x];if(k==='min')t.min=parseInt(v,10);else if(t[k].indexOf(v)<0)t[k]=t[k].concat([v]);
return R().filter(function(r){return pass(r,t,'');}).length;}
function label(i){return i.parentNode.querySelector('.sl-l').textContent;}
function stName(){return stSel&&stSel.value!=='all'?stSel.value:'';}
function draw(){var cl=type==='clinics',s=sel(),list=R().slice().sort(SORT[cl?cs.value:so.value]),T=cl?ct:tb,j=0,
ofN=cl?4:5,any=!!(q.value.trim()||s.goal.length||s.substance.length||s.min||s.check.length||s.sold.length||s.form.length||(cl&&(s.price.length||s.link.length||stName())));
segs.forEach(function(x){x.setAttribute('aria-pressed',x.getAttribute('data-type')===type?'true':'false');});
if(secC)secC.hidden=!cl;if(secS)secS.hidden=cl;
[].forEach.call(root.querySelectorAll('.sort-shops'),function(x){x.hidden=cl;});[].forEach.call(root.querySelectorAll('.sort-clinics'),function(x){x.hidden=!cl;});
[].forEach.call(root.querySelectorAll('[data-tab]'),function(x){if(!x.matches('input'))x.hidden=!inTab(x);});
// counts on every option; an option giving 0 hides unless chosen
ins.forEach(function(i){var k=i.getAttribute('data-k'),w=i.closest('.sl-o');if(!inTab(w)){w.hidden=true;return;}
if(k==='min'){var v=parseInt(i.value,10);w.hidden=v>ofN||(v===5&&cl);w.querySelector('.sl-l').textContent=v===0?'Any':v===ofN?ofN+' of '+ofN:v+' or more';}
if(k==='check'&&i.value==='lab'&&cl){w.hidden=true;return;}
var c=count(s,k,i.value);w.querySelector('.sl-n').textContent=c;if(k!=='min')w.hidden=c===0&&!i.checked;else if(!w.hidden)w.hidden=c===0&&!i.checked;});
// the substance group: the 8 most sold that give rows, then "Show all N"
var sbx=side.querySelector('.sl-g[data-g="substance"] .sl-opts'),mb=side.querySelector('.sl-more');
ins.filter(function(i){return i.getAttribute('data-k')==='substance';}).sort(function(a,b){return(+b.parentNode.querySelector('.sl-n').textContent)-(+a.parentNode.querySelector('.sl-n').textContent)||a.value.localeCompare(b.value);}).forEach(function(i){sbx.insertBefore(i.closest('.sl-o'),mb);});
var so8=ins.filter(function(i){return i.getAttribute('data-k')==='substance'&&!i.closest('.sl-o').hidden;}).sort(function(a,b){return(+b.parentNode.querySelector('.sl-n').textContent)-(+a.parentNode.querySelector('.sl-n').textContent)||a.value.localeCompare(b.value);});
so8.forEach(function(i,x){if(x>=8&&!subsAll&&!i.checked)i.closest('.sl-o').hidden=true;});
if(mb){mb.hidden=so8.length<=8;mb.textContent=subsAll?'Show fewer':'Show all '+so8.length;}
// group summaries
groups.forEach(function(g){var k=g.getAttribute('data-g'),e=g.querySelector('.sl-sum'),a=e.getAttribute('data-any');
if(k==='state'){e.textContent=stName()||'All states';return;}if(k==='min'){e.textContent=s.min?(s.min===ofN?ofN+' of '+ofN:s.min+' or more'):'Any';return;}
var m=(s[k]||[]).length;e.textContent=m?String(m):a;});
// rows: matches in the chosen order, the first 25 until "Show all"
list.forEach(function(r){T.tBodies[0].appendChild(r);var ok=pass(r,s,'');r.hidden=!ok||(!open&&j>=FIRST);if(ok)j++;});
more.hidden=open||j<=FIRST;all.textContent='Show all '+j;
var w=j+' '+(cl?(j===1?'clinic':'clinics'):(j===1?'shop':'shops'));n.textContent=w;show.textContent='Show '+w;
// pills
pills.innerHTML='';var act=[];
ins.forEach(function(i){if(i.checked&&inTab(i.closest('[data-tab]')||i)&&!(i.getAttribute('data-k')==='min'&&i.value==='0'))act.push({t:i.getAttribute('data-k')==='link'?'Linked clinics':i.getAttribute('data-k')==='min'?'Minimum checks: '+label(i):label(i),c:function(){i.checked=false;if(i.getAttribute('data-k')==='min')side.querySelector('input[data-k="min"][value="0"]').checked=true;ch();}});});
if(cl&&stName())act.push({t:'Your state: '+stName(),c:function(){setState('all');}});
act.forEach(function(o){var e=document.createElement('button');e.type='button';e.className='cf-pill';e.textContent=o.t+' ';var x=document.createElement('span');x.className='rm';x.setAttribute('aria-hidden','true');x.textContent='×';e.appendChild(x);
var v=document.createElement('span');v.className='vh';v.textContent='remove';e.appendChild(v);e.addEventListener('click',o.c);pills.appendChild(e);});
if(act.length){var c=document.createElement('button');c.type='button';c.className='cf-clear';c.textContent='Clear all';c.addEventListener('click',clearAll);pills.appendChild(c);}
var cc=fbtn.querySelector('.cf-count');cc.textContent=act.length?'('+act.length+')':'';fbtn.classList.toggle('on',!!act.length);
[].forEach.call(bar.querySelectorAll('.sl-q[data-open]'),function(b){var g=side.querySelector('.sl-g[data-g="'+b.getAttribute('data-open')+'"]'),sm=g&&g.querySelector('.sl-sum').textContent,
on=sm&&sm!=='Any'&&sm!=='All states';b.textContent=b.getAttribute('data-l')+(on?': '+sm:'');b.classList.toggle('on',!!on);});
[].forEach.call(side.querySelectorAll('.sl-st'),function(b){b.setAttribute('aria-pressed',(b.getAttribute('data-st')===(stName()||'all'))?'true':'false');});}
function save(){var s=sel(),h=[];if(type==='shops'&&ct)h.push('type=shops');if(q.value.trim())h.push('q='+encodeURIComponent(q.value.trim()));
['goal','substance','check','sold','form','price','link'].forEach(function(k){if(s[k].length)h.push(k+'='+s[k].join(','));});if(s.min)h.push('min='+s.min);
if(so&&so.value!=='checks')h.push('sort='+so.value);if(cs&&cs.value!=='checks')h.push('csort='+cs.value);
var u=location.pathname+location.search+(h.length?'#'+h.join('&'):'');if(u!==location.pathname+location.search+location.hash)history.replaceState(null,'',u);}
function load(){var hs=location.hash.slice(1);if(hs.indexOf('=')<0){if(hs==='shops'&&tb)type='shops';else if(hs==='clinics'&&ct)type='clinics';return;}
var P=new URLSearchParams(hs),t=P.get('type');q.value=P.get('q')||'';
ins.forEach(function(i){var k=i.getAttribute('data-k'),v=(P.get(k)||'').split(',');i.checked=k==='min'?i.value===(P.get('min')||'0'):v.indexOf(i.value)>=0;});
function opt(el,v){return!!el&&!!el.querySelector('option[value="'+v+'"]');}
if(so)so.value=opt(so,P.get('sort'))?P.get('sort'):'checks';if(cs)cs.value=opt(cs,P.get('csort'))?P.get('csort'):'checks';
type=(t==='shops'||t==='shop')&&tb?'shops':(t==='clinics'||t==='clinic')&&ct?'clinics':ct?'clinics':'shops';
var sb=(P.get('substance')||'').split(',')[0];if(!t&&sb&&ct&&tb&&!crows.some(function(r){return has(r,'subs',sb);}))type='shops';}
function ch(){open=false;draw();save();}
function clearAll(){q.value='';ins.forEach(function(i){i.checked=i.getAttribute('data-k')==='min'&&i.value==='0';});if(stName())setState('all');ch();}
function setState(v){if(!stSel)return;stSel.value=v;stSel.dispatchEvent(new Event('change',{bubbles:true}));}
// the Bottom sheet (phones): opens on "Filters" or a quick pill with that group open; Escape, the scrim, × or "Show N" close it
var last=null;function sheet(o,g){if(wide.matches)return;side.classList.toggle('sheet-on',o);scrim.hidden=!o;fbtn.setAttribute('aria-expanded',o?'true':'false');document.documentElement.classList.toggle('sl-lock',o);
if(o){last=document.activeElement;if(g){var d=side.querySelector('.sl-g[data-g="'+g+'"]');if(d){d.open=true;setTimeout(function(){d.scrollIntoView({block:'start'});});}}side.querySelector('.sl-x').focus();}else if(last)last.focus();}
[].forEach.call(bar.querySelectorAll('.sl-q[data-open]'),function(b){b.setAttribute('data-l',b.textContent);b.addEventListener('click',function(){sheet(true,b.getAttribute('data-open'));});});
fbtn.addEventListener('click',function(){sheet(true);});scrim.addEventListener('click',function(){sheet(false);});
side.querySelector('.sl-x').addEventListener('click',function(){sheet(false);});show.addEventListener('click',function(){sheet(false);});
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&side.classList.contains('sheet-on'))sheet(false);});
// phones: Sort lives in the sheet, first; from 900px it goes back into the bar (owner, 18 Nov 2026)
var sortBox=side.querySelector('.sl-sortg'),sorts=[].slice.call(bar.querySelectorAll('.sf-sort')),qk=bar.querySelector('.sl-quick');
function mode(){side.hidden=false;root.classList.add('sl-js');sortBox.hidden=wide.matches;sorts.forEach(function(x){if(wide.matches)bar.insertBefore(x,qk);else sortBox.appendChild(x);});if(wide.matches){side.classList.remove('sheet-on');scrim.hidden=true;document.documentElement.classList.remove('sl-lock');}}
if(wide.addEventListener)wide.addEventListener('change',mode);
bar.hidden=false;head.hidden=false;if(tabs)tabs.hidden=false;mode();load();
side.addEventListener('change',function(e){if(e.target.matches('input[data-k]'))ch();});
side.addEventListener('click',function(e){var st=e.target.closest('.sl-st');if(st){setState(st.getAttribute('data-st'));return;}
if(e.target.closest('.sl-more')){subsAll=!subsAll;draw();return;}if(e.target.closest('.sl-clear'))clearAll();});
q.addEventListener('input',ch);[so,cs].forEach(function(x){if(x)x.addEventListener('change',ch);});
clr.addEventListener('click',function(){q.value='';ch();q.focus();});
segs.forEach(function(x){x.addEventListener('click',function(){type=x.getAttribute('data-type');ch();});});
all.addEventListener('click',function(){open=true;draw();});
window.addEventListener('hashchange',function(){load();draw();});document.addEventListener('pc-state',draw);draw();})();
</script>"""
