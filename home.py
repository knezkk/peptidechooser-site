"""Home's sections under the hero (design/pages.md, Home; the "Home v2" sketch approved by the owner on 3 Nov 2026):
Where to get it, Compare by goal, Guides and How we rate, Is it legal today?, Latest FDA warning letters, Who explains
this well. Every number comes from data/site.json through build.py's helpers; a section whose data is missing is left
out (never drawn empty). build.py calls finish(build, page) once all of its helpers exist.
"""
import json
import re
from html import escape

import guides
import parts

WHERE_FIRST = 8          # rows the seller table shows before any filter (sketch: 8)
WHERE_JSON = "sellers/home.json"
LETTERS_SHOWN = 3
CREATORS_SHOWN = 4
WORDS = "zero one two three four five six seven eight nine ten eleven twelve".split()


def num_word(n):
    return WORDS[n].capitalize() if n < len(WORDS) else str(n)


def subs_short(b, slugs, n=2):
    """"semaglutide, tirzepatide": the first n substance names in lower case, as in a sentence (BPC-157 keeps its case)."""
    names = []
    for s in slugs[:n]:
        name = re.sub(r" *\(.*\)$", "", b.sub_label(s))
        names.append(name if any(c.isdigit() for c in name) or name.isupper() else name.lower())
    return ", ".join(names)


# ---------------------------------------------------------------- Where to get it

def seller_kind(b, r):
    return "clinic" if r["seller_slug"] in b.CLINIC_PROFILES else "shop"


def where_order(b, r):
    """Online clinics first, then shops (owner answer Q1 a, 3 Nov 2026); in each group most checks first, then most plans or
    products, then name."""
    clinic = seller_kind(b, r) == "clinic"
    size = len(b.clinic_plan_rows(r)) if clinic else (r.get("product_count") or 0)
    return (0 if clinic else 1, -(r.get("score") if r.get("score") is not None else -1), -size, b.seller_name(r).lower())


def where_line(b, r):
    """The small line under the name: a shop's company and state (only a company we show) and its product count; a
    clinic's goal and the medicines its plans carry."""
    if seller_kind(b, r) == "clinic":
        subs = b.clinic_subs(r)
        goal = next((b.SUB_GOAL[s]["label"] for s in subs if s in b.SUB_GOAL), "")
        return " · ".join(x for x in (goal, subs_short(b, subs)) if x)
    parts = []
    if b.shown_company(r):
        parts.append(b.clean(r["entity_name"]))
        if b.STATES.get(r.get("entity_state") or ""):
            parts.append(b.STATES[r["entity_state"]])
    parts.append(b.plural(r.get("product_count") or 0, "product"))
    return " · ".join(parts)


def where_from(b, r):
    """From: a clinic's cheapest monthly plan (with its care fee when it has one), a shop's lowest price per mg."""
    if seller_kind(b, r) == "clinic":
        plans = b.clinic_plan_rows(r)
        if not plans:
            return "unknown"
        p, fee = plans[0], plans[0].get("membership_fee_monthly")
        return f'{b.usd(p["price_monthly"])}/mo' + (f' + {b.usd(fee)} care' if fee and float(fee) > 0 else "")
    lo = b.compare_ppm(r)[0]
    return f"{b.per_mg(lo)}/mg" if lo is not None else "unknown"


def where_letters(b, r):
    n = r.get("fda_letter_count")
    if n is None:
        return "unknown"
    if n == 0:
        return "None"
    newest = b.newest_letter(r)
    return f'<span class="chip chip-warn">{b.plural(n, "letter")}{", " + b.nice_date(newest) if newest else ""}</span>'


def where_action(b, r):
    """The row's one action (pages.md, Home, Where to get it): a clinic with a paid link (`paid_url`; build.clinic_button,
    none yet) gets btn-action "Visit <Name>" through /out/; a clinic without, btn-wait "See plans" to our clinic page;
    a shop, btn-line "Our review" to our page on it. Never a link to a seller's own site."""
    if seller_kind(b, r) == "clinic":
        return b.clinic_button(r["seller_slug"], "See plans", in_table=True)
    return (f'<span class="pick-act"><a class="btn btn-line btn-sm" href="/sellers/{r["seller_slug"]}/">Our review</a></span>')


def where_row(b, r):
    kind = seller_kind(b, r)
    chip = ('<span class="chip chip-info">Online clinic</span>' if kind == "clinic" else
            f'<span class="chip chip-neutral">{b.kind_words(r)[1]}</span>')
    return ('<tr>'
            f'<td><span class="cell-pic">{parts.tile(r["seller_slug"], b.seller_base(b.seller_name(r)), 40, shop=kind == "shop", seller=r)}<span><a class="name" href="/sellers/{r["seller_slug"]}/">{b.seller_name(r)}</a><span class="sub">{escape(where_line(b, r))}</span></span></span></td>'
            f'<td data-l="Type">{chip}</td>'
            f'<td class="num" data-l="Checks">{b.score_of(r) or 0} of {b.out_of(r)}</td>'
            f'<td class="num" data-l="From">{where_from(b, r)}</td>'
            f'<td data-l="FDA letters">{where_letters(b, r)}</td>'
            f'<td class="act">{where_action(b, r)}</td></tr>')


def where_section(b):
    rows = sorted(list(b.SHOPS.values()) + list(b.CLINIC_PROFILES.values()), key=lambda r: where_order(b, r))
    rows = [r for r in rows if r.get("score") is not None]
    if not rows:
        return "", ""
    n = len(rows)
    shops = [r for r in rows if seller_kind(b, r) == "shop"]
    clinics = [r for r in rows if seller_kind(b, r) == "clinic"]
    # the substance select: the /sellers/ page's own list (same values, so its hash reads the same)
    opts = re.search(r'<select class="input" id="sellers-sub"[^>]*>(.*?)</select>', b.sellers_filter(shops, clinics), re.S).group(1)
    mins = "".join(f'<option value="{i}">{"Any" if i == 0 else f"{i} of {len(b.SCORE_CHECKS)}" if i == len(b.SCORE_CHECKS) else f"{i} or more"}</option>'
                   for i in range(len(b.SCORE_CHECKS) + 1))
    seg = "".join(f'<button type="button" class="seg-b" data-type="{k}" data-filter="type" data-value="{k or "all"}" aria-pressed="{"true" if not k else "false"}">{t}</button>'
                  for k, t in (("", "All"), ("clinic", "Online clinics"), ("shop", "Research-use shops")))
    data = [{"t": seller_kind(b, r), "s": r.get("score") or 0, "u": (b.clinic_subs(r) if seller_kind(b, r) == "clinic" else b.shop_subs(r)),
             "n": b.seller_name(r).lower(), "h": where_row(b, r)} for r in rows]
    body = "".join(where_row(b, r) for r in rows[:WHERE_FIRST])
    html = f"""
<section class="section home-sec" id="where">
  <div class="wrap">
    <div class="sec-hd"><div><h2>Where to get it: {n} sellers, each with background checks</h2><p>Online clinics prescribe and ship medicines; research-use shops sell vials labeled for lab use. Every name opens our page on that seller.</p></div></div>
    <form class="where-filter" hidden onsubmit="return false">
      <div class="where-f"><label for="where-sub">Substance</label><select class="input" id="where-sub" data-filter="substance"><option value="">Any</option>{opts}</select></div>
      <div class="seg" role="group" aria-label="Type">{seg}</div>
      <div class="where-f"><label for="where-min">Checks</label><select class="input" id="where-min" data-filter="min_checks">{mins}</select></div>
      <div class="where-f where-q"><label for="where-q">Seller name</label><input class="input" id="where-q" type="text" autocomplete="off" data-filter="name" data-value="text"></div>
    </form>
    <p class="small where-n" id="where-n" aria-live="polite">Showing {min(WHERE_FIRST, n)} of {n} · online clinics first, then by checks</p>
    <div class="tbl-wrap"><table class="tbl tbl-cards tbl-where" id="where-table"><caption class="vh">Sellers, online clinics first, then by checks</caption>
      <thead><tr><th scope="col">Seller</th><th scope="col">Type</th><th scope="col">Checks</th><th scope="col">From</th><th scope="col">FDA letters</th><th scope="col"><span class="vh">Action</span></th></tr></thead>
      <tbody>{body}</tbody>
    </table></div>
    <p class="small where-note">Clinics are checked on four facts (FDA letters, registered company, legal pages, fresh prices), shops on those and lab reports, five. Facts we hold, not a safety grade. <a href="/how-we-rate/">How we rate</a></p>
    <p class="sec-act"><a class="btn btn-ink" id="where-all" href="/sellers/">See all {n} sellers</a></p>
  </div>
</section>
{WHERE_JS.replace("FIRST_N", str(WHERE_FIRST))}"""
    return html, json.dumps(data, separators=(",", ":"))


# With JavaScript the filter shows; the first change loads every seller row (sellers/home.json) and the table shows the
# first 8 that match. The filter writes the hash /sellers/ reads (substance, min, type, q) onto "See all", so the link
# carries it. Without JavaScript the 8 rows show and the filter stays hidden.
WHERE_JS = """<script>
(function(){var f=document.querySelector('.where-filter'),tb=document.getElementById('where-table');if(!f||!tb||!window.fetch)return;
var sb=document.getElementById('where-sub'),mn=document.getElementById('where-min'),q=document.getElementById('where-q'),n=document.getElementById('where-n'),
all=document.getElementById('where-all'),segs=[].slice.call(f.querySelectorAll('.seg-b')),rows=null,FIRST=FIRST_N;
function type(){var on=segs.filter(function(x){return x.getAttribute('aria-pressed')==='true';})[0];return on?on.getAttribute('data-type'):'';}
function draw(){var s=q.value.trim().toLowerCase(),u=sb.value,k=parseInt(mn.value,10),t=type(),hit=rows.filter(function(r){
return(!s||r.n.indexOf(s)>=0)&&(!u||r.u.indexOf(u)>=0)&&r.s>=k&&(!t||r.t===t);});
tb.tBodies[0].innerHTML=hit.slice(0,FIRST).map(function(r){return r.h;}).join('');
[].forEach.call(tb.tBodies[0].rows,function(r){r.style.opacity=1;});
n.textContent=hit.length?'Showing '+Math.min(FIRST,hit.length)+' of '+hit.length+' that match · online clinics first, then by checks':'No seller matches. Try fewer filters.';
var h=[];if(u)h.push('substance='+u);if(k)h.push('min='+k);if(t)h.push('type='+t);if(s)h.push('q='+encodeURIComponent(s));
all.href='/sellers/'+(h.length?'#'+h.join('&'):'');}
function ch(){if(rows)return draw();fetch('/sellers/home.json').then(function(r){return r.json();}).then(function(d){rows=d;draw();});}
f.hidden=false;[sb,mn].forEach(function(x){x.addEventListener('change',ch);});q.addEventListener('input',ch);
segs.forEach(function(x){x.addEventListener('click',function(){segs.forEach(function(y){y.setAttribute('aria-pressed',y===x?'true':'false');});ch();});});})();
</script>"""


# ---------------------------------------------------------------- Compare by goal

def goal_price(b, g):
    """A goal card's price and its one-word source: the cheapest clinic plan for the goal (any plan on a goal with its
    own clinic plans, else the goal's cheapest plan that is not compounded, else a compounded one), else the lowest
    price per mg at research-use shops for the goal's research-use options. (price, source) or ("", "")."""
    plans = b.clinic_plans(g) if g.get("clinic_plans") else []
    if not plans:
        subs = {p["substance"] for p in g["peptides"] if p.get("substance")}
        found = [r for r in b.PLANS if r["substance_slug"] in subs and r.get("price_monthly") is not None]
        plans = sorted(found, key=lambda r: (r.get("product_kind") == "compounded", float(r["price_monthly"]), r["seller_name"]))
    if plans:
        p = min(plans, key=lambda r: (float(r["price_monthly"]), r["seller_name"])) if g.get("clinic_plans") else plans[0]
        sub = subs_short(b, [p["substance_slug"]], 1) if p.get("substance_slug") else ""
        return f'from {b.usd(p["price_monthly"])}/mo', (f"compounded {sub}" if p.get("product_kind") == "compounded" else f"{sub}, clinic").strip(", ")
    subs = {s for p in g["peptides"] if not b.approved_row(p) and p.get("chip") != "info" for s in b.subs_of(p)}
    subs -= {s for s in subs if b.pep_status(s) and b.pep_group(b.pep_status(s)) == "approved"}  # never an approved medicine
    # the lowest price per mg any shop lists for those substances (seller_substances), inside the /compare/ band
    vals = [x["price_per_mg_min"] for slug, rows in b.SELLER_SUBS.items() if slug in b.SHOPS for x in rows
            if x.get("substance_slug") in subs and x.get("price_per_mg_min") is not None
            and b.PPM_LOW <= x["price_per_mg_min"] <= b.PPM_HIGH]
    return (f"from {b.per_mg(min(vals))}/mg", "research-use only") if vals else ("", "")


def goals_section(b):
    cards = []
    for g in b.CHOOSER_GOALS:
        plans = b.clinic_plans(g)
        count = b.plural(len(plans), "clinic plan") if plans else b.plural(len(g["peptides"]), "option")
        price, src = goal_price(b, g)
        inner = (f'<span class="goal-pic goal-c-{g["slug"]}">{parts.goal_photo(g["slug"], 48, small=True)}</span><span class="goal-name">{g["label"]}</span><span class="small">{count}</span>'
                 + (f'<span class="goal-price">{price}</span><span class="small">{src}</span>' if price else ""))
        cards.append(f'<li><a class="goal-card" href="/{g["slug"]}/">{inner}</a></li>' if g.get("page")
                     else f'<li><span class="goal-card">{inner}</span></li>')
    return f"""
<section class="section home-sec" id="compare">
  <div class="wrap">
    <div class="sec-hd"><div><h2>Compare by goal</h2><p>{num_word(len(b.CHOOSER_GOALS))} goals, the same rule on each: the FDA-approved option first, then what people buy instead, with its real status.</p></div></div>
    <ul class="goal-cards">{"".join(cards)}</ul>
  </div>
</section>"""


# ---------------------------------------------------------------- Guides and How we rate

RATE = [("Lab reports", "A lab report dated in the last 12 months."),
        ("No FDA letter", "No FDA warning letter matched to its web or street address."),
        ("Company found", "The business behind the shop found in a state registry."),
        ("Legal pages", "A terms page and a privacy or refund page, seen in the last 30 days."),
        ("Fresh prices", "A price per milligram seen in the last 30 days.")]


def learn_rate_section(b):
    links = "".join(f'<li><a href="/learn/{g["slug"]}/">{g["title"]}</a></li>' for g in guides.GUIDES[:guides.HOME_CARD])
    rate = "".join(f'<li><strong>{t}</strong> {p}</li>' for t, p in RATE)
    return f"""
<section class="section home-sec" id="learn">
  <div class="wrap home-two">
    <div class="learn-card" aria-labelledby="learn-card-h"><h2 id="learn-card-h">Guides in plain words</h2>
      <ul>{links}</ul>
      <p class="sec-act"><a class="btn btn-line" href="/learn/">All {len(guides.GUIDES)} guides</a></p>
    </div>
    <div class="rate-card" aria-labelledby="rate-h"><h2 id="rate-h">How we rate</h2>
      <p>Every shop gets these five checks, in this order; an online clinic gets the last four, because clinics publish no lab reports. They are facts we hold about the seller, not a safety grade.</p>
      <ol class="rate-list">{rate}</ol>
      <a class="more-link" href="/how-we-rate/">Read the full method →</a>
    </div>
  </div>
</section>"""


# ---------------------------------------------------------------- Is it legal today?

def legal_chips(b, slug):
    """A substance's chips as the legal tables give them. A substance sold both as a cosmetic (its hand row is a
    cosmetic) and with a drug status from the database shows both: "Cosmetic", then the drug status, which reads
    "Injection withdrawn" when the database's status is a withdrawn compounding nomination (GHK-Cu)."""
    s = b.pep_status(slug)
    if not s:
        return ""
    hand = b.hand_legal(slug)
    if hand and hand.get("chip") == "info" and not s.get("hand"):
        withdrawn = any(r["substance_slug"] == slug and r["regime"] == "fda_nomination_withdrawn" for r in b.LEGAL_DB or [])
        return ('<span class="chip chip-info">Cosmetic</span>'
                + (f'<span class="chip chip-neutral">Injection withdrawn</span>' if withdrawn else f'<span class="chip chip-{s["chip"]}">As a drug: {s["label"]}</span>'))
    return f'<span class="chip chip-{s["chip"]}">{s["label"]}</span>'


def legal_section(b):
    slugs = [s for s in (b.DATA.get("home_checked") or {}).get("slugs", []) if s in b.PEPTIDE_SLUGS]
    cards = "".join(f'<li><a class="legal-card" href="/peptides/{s}/"><span class="name">{b.pep_short(s)}</span>'
                    f'<span class="chips">{legal_chips(b, s)}</span></a></li>' for s in slugs)
    right = (f'<div class="legal-most"><h3>Most checked this month</h3><ul class="legal-cards">{cards}</ul>'
             f'<a class="more-link" href="/peptides/">All {len(b.PEPTIDE_SLUGS)} substances, A to Z →</a></div>') if cards else ""
    return f"""
<section class="band-2 home-sec" id="legal">
  <div class="wrap home-two">
    <div>
      <h2>Is it legal today?</h2>
      <p class="lede">Type a peptide. You get its FDA status with the source and date, where it is sold, and what a warning letter says about it.</p>
      <form class="legal-check" action="/peptides/" method="get" role="search" data-ev="legal_check">
        <label for="legal-q">Check a peptide, for example BPC-157</label>
        <div class="legal-row"><input class="input" id="legal-q" name="q" type="text" autocomplete="off" required><button class="btn btn-ink" type="submit">Check</button></div>
        <p class="small" id="legal-msg" aria-live="polite"></p>
      </form>
    </div>
    {right}
  </div>
</section>
{LEGAL_CHECK_JS}""" if b.PEPTIDE_SLUGS else ""


# "Check" (pages.md, Home, Is it legal today?): the search index's first Peptide result opens its page; nothing found
# opens /peptides/. Without JavaScript the form opens /peptides/.
LEGAL_CHECK_JS = """<script>
(function(){var f=document.querySelector('.legal-check');if(!f)return;
f.addEventListener('submit',function(e){var S=window.pcSearch;if(!S)return;e.preventDefault();var v=document.getElementById('legal-q').value.trim();
S.load(function(d){var r=S.find(d,v,20).filter(function(x){return x.type==='Peptide';});if(window.pcEv)pcEv(f.getAttribute('data-ev'),{substance:r.length?r[0].url.split('/')[2]:'none'});location.href=r.length?r[0].url:'/peptides/';});});})();
</script>"""


# ---------------------------------------------------------------- Latest FDA warning letters

def letter_kind(r):
    """The kind of company, short: our match first, else the FDA's bracket in the subject; "" when neither says."""
    k = r.get("seller_kind") or ""
    if k == "S1_RUO":
        return "Research-use shop"
    if "TELEHEALTH" in k or "CLINIC" in k:
        return "Online clinic"
    m = re.search(r"\(([^()]+)\)\s*$", r.get("letter_subject") or "")
    word = (m.group(1) if m else "").lower()
    return {"telehealth": "Online clinic", "internet pharmacy": "Internet pharmacy",
            "compounding pharmacy": "Compounding pharmacy", "compounding": "Compounding pharmacy"}.get(word, "")


def letters_section(b):
    rows = [r for r in b.LETTERS_ALL if r.get("peptide_related")][:LETTERS_SHOWN]
    if not rows:
        return ""
    cards = []
    for r in rows:
        company = re.split(r"/(?:www\.|https?:)", b.clean(r["company_name"]))[0].strip()
        subj = re.sub(r"\s*\([^()]+\)\s*$", "", b.clean(r["letter_subject"]))
        kind = letter_kind(r)
        cards.append(f'<li class="letter-card"><span class="small">{b.nice_date(r["letter_date"])}{" · " + kind if kind else ""}</span>'
                     f'<span class="name">{escape(company)}</span><span class="small">{escape(subj)}</span>'
                     f'<a href="{escape(r["letter_url"])}" rel="nofollow">FDA letter</a></li>')
    sub = (f'<a class="btn btn-ink" href="/fda-warning-letters/#sub-h">Get new letters by email</a>' if b.BUTTONDOWN else "")
    return f"""
<section class="section home-sec" id="letters">
  <div class="wrap">
    <div class="sec-hd"><div><h2>Latest FDA warning letters</h2><p>{b.N_LETTERS} letters to peptide sellers, compounders and online clinics, read for you. The three newest:</p></div></div>
    <ul class="letter-cards">{"".join(cards)}</ul>
    <p class="sec-act"><a class="btn btn-line" href="/fda-warning-letters/">All {b.N_LETTERS} letters</a>{sub}</p>
  </div>
</section>"""


# ---------------------------------------------------------------- Who explains this well

def subs_count(n):
    """4,470,000 -> "4.5M", 755,000 -> "755K"."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
    return f"{round(n / 1000):,}K" if n >= 1000 else str(n)


def creators_section(b):
    c = b.CREATORS
    cards = sorted((x for x in c.get("cards", []) if x.get("group") == "A" and x.get("subscribers")),
                   key=lambda x: -x["subscribers"])[:CREATORS_SHOWN]
    if not cards:
        return ""
    lis = "".join(f'<li><a class="name" href="{escape(x["url"])}" rel="nofollow noopener">{x["name"]}</a>'
                  f'<span class="small">{subs_count(x["subscribers"])}, {x["platform"]}</span><p>{x["stance"]}</p></li>' for x in cards)
    return f"""
<section class="section home-sec" id="creators">
  <div class="wrap">
    <div class="sec-hd"><div><h2>Who explains this well</h2><p>{num_word(len(cards))} creators we read before we write. Numbers from their channels; we take no money from them and they take none from us.</p></div></div>
    <ul class="creator-strip">{lis}</ul>
    <p class="small" style="margin-top:16px">Subscribers as of {b.nice_date(c["cards_checked"])} ({c["cards_source"]}).</p>
  </div>
</section>"""


# ---------------------------------------------------------------- the page

SECTIONS = [("where", None), ("compare", goals_section), ("learn", learn_rate_section), ("legal", legal_section),
            ("letters", letters_section), ("creators", creators_section)]


JS = ""  # Home's scripts; build.py's main() writes them to /assets/home.js
ROWS = ""  # every seller row for the Where filter; build.py's main() writes it to WHERE_JSON


def finish(b, page):
    """Home's PAGES entry with every <!--home:name--> marker replaced by its section."""
    global ROWS
    path, out, title, desc, body, *rest = page
    where, ROWS = where_section(b)
    for key, fn in SECTIONS:
        body = body.replace(f"<!--home:{key}-->", where if key == "where" else fn(b))
    # Home's own scripts (goal switch, price windows, seller filter, legal check) go to one cached file, so the page stays
    # under 60 KB with the shared header (pages.md, Home); deferred, they run once the page is parsed, as they did inline.
    global JS
    JS = "\n".join(m.strip()[len("<script>"):-len("</script>")] for m in re.findall(r"<script>.*?</script>", body, re.S))
    body = re.sub(r"<script>.*?</script>\s*", "", body, flags=re.S) + '<script src="/assets/home.js" defer></script>\n'
    return (path, out, title, desc, body, *rest)
