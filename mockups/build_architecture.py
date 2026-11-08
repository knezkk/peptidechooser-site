"""Round 2 of owner queue block 6 (ODOBRENO DIZAJN - Karlo - 8. 11. 2026 - PR #142): the new page types from
design/pages/group.md, new-types.md and nav-parts.md, drawn locally with real data. Not part of the site build;
nothing here goes live. Titles, H1s and prose are samples until ODOBRENO SEO per page type.

    python3 tools/pull_data.py && python3 build.py          # real data, the site in dist/
    python3 mockups/build_architecture.py <out-root>         # copies dist/ to <out-root> and adds /_mock/<type>/

Lab and price history are left out: their data views (data task 1g) do not exist yet.
"""
import collections
import shutil
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.argv = sys.argv[:1] + sys.argv[1:]
import build as b  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "mockups" / "architecture"
MOCK = "/_mock"
BANNER = ('<div class="wrap"><p class="small" style="margin:8px 0 0">Local template, round 2 of the design book (PR #142). '
          'Real data; title, H1 and prose are samples for ODOBRENO SEO.</p></div>')


NOT_A_PEPTIDE = {"finasteride", "minoxidil", "orforglipron"}  # sample until the data carries a peptide flag (w2)


def az_rows(slugs):
    out = []
    for x in sorted(slugs, key=lambda s: b.pep_name(s).lower()):
        s = b.pep_status(x)
        name = escape(b.pep_name(x))
        cell = f'<a class="name" href="/peptides/{x}/">{name}</a>' if f"/peptides/{x}/" not in b.NOINDEX else f'<span class="name">{name}</span>'
        if x in NOT_A_PEPTIDE:
            cell += ' <span class="chip chip-neutral">Not a peptide</span>'
        out.append(f'<tr><td>{cell}</td><td data-l="Status"><span class="chip chip-{s["chip"]}">{s["label"]}</span></td>'
                   f'<td data-l="What it means">{b.pep_means(x)}</td><td class="num" data-l="Lowest price">{b.pep_low(x)}</td></tr>')
    return "".join(out)


def az_table(slugs, caption):
    return (f'<div class="tbl-wrap"><table class="tbl tbl-cards tbl-peptides"><caption class="vh">{caption}</caption>'
            '<thead><tr><th scope="col">Substance</th><th scope="col">Status</th><th scope="col">What it means</th><th scope="col">Lowest price</th></tr></thead>'
            f'<tbody>{az_rows(slugs)}</tbody></table></div>')


def facts_pad(items, checked):
    rows = "".join(f'<div class="ledger"><span>{k}</span><span class="num">{v}</span></div>' for k, v in items)
    return (f'<aside class="board check-card"><h2>In this group</h2><div class="company-ledger">{rows}</div>'
            f'<p><span class="stamp">Checked {b.nice_date(checked)}</span></p></aside>')


def one_seller(html):
    """An offer page shows one seller: its clinic table drops the Clinic column and the plan name leads the row."""
    import re
    html = html.replace('<th scope="col">Clinic</th>', "", 1)
    html = re.sub(r'<td><a class="name" href="/sellers/[^"]+/">[^<]*</a></td>', "", html)
    html = re.sub(r"<h2>Online clinic prices</h2><p>[^<]*</p>", "<h2>Semaglutide plans</h2><p>The plans on this clinic's price page, cheapest first.</p>", html, count=1)
    return html.replace('class="tbl tbl-cards', 'class="tbl tbl-compact tbl-cards', 1)


def where_list(rows, lede, head="Where to get it"):
    lines, named = [], set()
    for r in rows:
        kind = '<span class="chip chip-warn">Compounded</span>' if r.get("product_kind") == "compounded" else ""
        lines.append(f'<li><span class="where-who">{b.clinic_link(r["seller_slug"], b.seller_base(r["seller_name"]))}'
                     f'<span class="sub">{b.explain_brand(r["plan_name"], named)}{kind}</span></span>'
                     f'<span class="where-price"><span class="num">{b.usd(r["price_monthly"])}/mo</span>{b.plan_letter(r)}</span>'
                     f'{b.clinic_button(r["seller_slug"], "See plans", plan=r)}</li>')
    return (f'<div class="panel-line pep-where" id="where"><h2>{head}</h2><p class="small">{lede}</p>'
            f'<ul class="where-list">{"".join(lines)}</ul></div>')


def next_list(links):
    return f'<div><h2 class="h-sources">What to do next</h2><ul class="next-list">{"".join(f"<li>{x}</li>" for x in links)}</ul></div>'


def foot(links, sources):
    src = "".join(f'<li>{s}</li>' for s in sources)
    return (f'<section class="section pep-foot"><div class="wrap"><div class="goal-two">{next_list(links)}'
            f'<section class="pep-sources"><h2 class="h-sources">Sources</h2><ol class="small sources">{src}</ol></section></div></div></section>')


def group_list():
    slugs = [x for x in b.PEPTIDE_SLUGS if b.pep_group(b.pep_status(x)) == "cosmetic"] + list(b.PEP_COSMETIC_TOO)
    slugs = list(dict.fromkeys(slugs))
    checked = max(b.pep_checked(x) for x in slugs)
    approved = sum(b.pep_group(b.pep_status(x)) == "approved" for x in slugs)
    body = f"""
{BANNER}
<section class="hero hero-goal"><div class="wrap"><div class="pep-first">
  <div><h1>Topical peptides</h1>{b.author_line(checked)}
  <p class="intro">Peptides sold in creams, serums and lotions you put on the skin or scalp. Cosmetics need no FDA approval, so none of these is approved as a medicine; the table says what each one is.</p></div>
  {facts_pad([("Substances in this group", len(slugs)), ("FDA approved", approved)], checked)}
</div></div></section>
<section class="band-2"><div class="wrap">
  <h2>The substances</h2>
  <div class="year-chips" role="group" aria-label="Show"><span>Show</span><button type="button" class="year-chip" aria-pressed="true">Cosmetic <span>{len(slugs)}</span></button><p class="small" aria-live="polite">{len(slugs)} of {len(slugs)} shown.</p></div>
  {az_table(slugs, "Topical peptides with their FDA status")}
</div></section>
{foot(['<a href="/skin/">Compare every option for skin</a>', '<a href="/peptides/">All substances A to Z</a>'], ["Statuses: the substance pages' FDA sources, each with its date."])}"""
    return "topical", "Topical peptides", body, [("/peptides/", "Peptides"), ("", "Topical peptides")]


def group_guide():
    slugs = [x for x in b.PEPTIDE_SLUGS if b.pep_group(b.pep_status(x)) == "approved"]
    checked = max(b.pep_checked(x) for x in slugs)
    body = f"""
{BANNER}
<article class="page guide"><div class="wrap prose">
<h1>FDA-approved peptides</h1>
{b.author_line(checked)}
<section class="short-answer"><h2>Short answer</h2><p>{len(slugs)} substances we track have an FDA-approved product for a stated use. Each needs a prescription except minoxidil; the table lists them with their status and lowest price.</p></section>
<h2>Which peptides are FDA approved?</h2>
</div><div class="wrap">{az_table(slugs, "FDA-approved substances")}</div><div class="wrap prose">
<h2>What does FDA approved mean here?</h2>
<p>An approved product exists for the use on its label. A pharmacy-made copy of the same substance is not approved, even when it has the same name.</p>
<h2>What to do next</h2>
<div class="btn-row"><a class="btn btn-ink" href="/peptides/">All substances A to Z</a><a class="btn btn-line" href="/learn/">Guides</a></div>
<section class="guide-sources"><h2 class="h-sources">Sources</h2><ol class="small sources"><li>Drugs@FDA, each substance page's source with its date.</li></ol></section>
</div></article>"""
    return "fda-approved", "FDA-approved peptides", body, [("", "FDA-approved peptides")]


def subpage():
    g = next(x for x in b.ALL_GOALS if x["slug"] == "weight-loss")
    rows = sorted(b.pep_plans("tirzepatide"), key=lambda r: float(r["price_monthly"]))
    table = b.clinic_section(g, rows)
    slugs = ["tirzepatide", "retatrutide", "orforglipron"]
    checked = max(b.pep_checked(x) for x in slugs if x in b.PEPTIDE_SLUGS)
    body = f"""
{BANNER}
<section class="hero hero-goal"><div class="wrap"><div class="pep-first">
  <div><h1>New weight loss drugs</h1>{b.author_line(checked)}
  <p class="intro">The newest weight loss medicines: tirzepatide is approved, orforglipron and retatrutide are the next ones. Here is what each is, its FDA status, and what the approved one costs at online clinics.</p></div>
  <div class="goal-panel goal-c-weight-loss">{b.parts.goal_photo("weight-loss", 120)}</div>
</div></div></section>
<section class="section"><div class="wrap"><h2>Is it legal today?</h2>{az_table([s for s in slugs if s in b.PEPTIDE_SLUGS], "New weight loss drugs and their FDA status")}</div></section>
<section class="band-2"><div class="wrap">{table}</div></section>
{foot(['<a href="/weight-loss/">Every weight loss option</a>', '<a href="/peptides/tirzepatide/">Tirzepatide</a>', '<a href="/peptides/retatrutide/">Retatrutide</a>'], ["The goal page's sources."])}"""
    return "weight-loss/new-drugs", "New weight loss drugs", body, [("/weight-loss/", "Weight loss"), ("", "New weight loss drugs")]


def brand():
    rows = sorted([r for r in b.pep_plans("semaglutide") if "wegovy" in r["plan_name"].lower() and r["seller_slug"] in b.PROFILES],
                  key=lambda r: float(r["price_monthly"]))
    g = next(x for x in b.ALL_GOALS if x["slug"] == "weight-loss")
    s = b.pep_status("semaglutide")
    low = rows[0]
    body = f"""
{BANNER}
<section class="hero hero-goal seller-pg pep-pg"><div class="wrap"><div class="pep-first">
  <div><h1>Wegovy (semaglutide)</h1>{b.author_line(max(r["last_seen"] for r in rows)[:10])}
  <p class="pep-status"><span class="chip chip-{s["chip"]}">{s["label"]}</span> {b.pep_means("semaglutide")} <a href="{escape(s["url"])}" rel="nofollow">{b.source_word(s["url"])}</a></p>
  <p class="intro">Wegovy is Novo Nordisk's semaglutide for weight loss, as a weekly pen or a daily pill. The lowest plan we track is {b.usd(low["price_monthly"])}/mo at {escape(b.seller_base(low["seller_name"]))}, checked {b.nice_date(low["last_seen"][:10])}.</p></div>
  {where_list(rows[:3], "The cheapest Wegovy plans at the online clinics we track.")}
</div></div></section>
{b.clinic_section(g, rows).replace('class="tbl tbl-cards', 'class="tbl tbl-compact tbl-cards', 1).replace('</table></div>', '</table></div><p class="small"><a href="/peptides/semaglutide/">Compounded semaglutide and other forms</a></p>', 1)}
{foot(['<a href="/weight-loss/">Compare every option for weight loss</a>', '<a href="/peptides/semaglutide/">Semaglutide</a>'], [f'Drugs@FDA, semaglutide, {b.nice_date(s["seen"])}', "Clinic price pages, each with its check date."])}"""
    return "peptides/semaglutide/wegovy", "Wegovy (semaglutide)", body, [("/peptides/", "Peptides"), ("/peptides/semaglutide/", "Semaglutide"), ("", "Wegovy")]


def offer():
    sub = "semaglutide"
    by = collections.Counter(r["seller_slug"] for r in b.pep_plans(sub) if r["seller_slug"] in b.PROFILES)
    slug = by.most_common(1)[0][0]
    r = b.PROFILES[slug]
    name = b.seller_base(b.seller_name(r))
    rows = sorted([x for x in b.pep_plans(sub) if x["seller_slug"] == slug], key=lambda x: float(x["price_monthly"]))
    g = next(x for x in b.ALL_GOALS if x["slug"] == "weight-loss")
    others = sorted([x for x in b.pep_plans(sub) if x["seller_slug"] != slug and x["seller_slug"] in b.PROFILES],
                    key=lambda x: float(x["price_monthly"]))
    seen, three = set(), []
    for x in others:
        if x["seller_slug"] not in seen:
            seen.add(x["seller_slug"]); three.append(x)
        if len(three) == 3:
            break
    body = f"""
{BANNER}
<section class="seller-top"><div class="wrap"><div class="seller-head"><div class="seller-id"><div class="seller-id-text">
  <h1>Semaglutide at {escape(name)}</h1>
  <p class="seller-kind"><span class="chip chip-neutral">{b.kind_words(r)[1]}</span></p>
  {b.author_line(max(x["last_seen"] for x in rows)[:10])}
</div></div></div>
<p class="intro seller-answer">{escape(name)} lists {len(rows)} semaglutide plans on its price page; the lowest is {b.usd(rows[0]["price_monthly"])}/mo ({escape(rows[0]["plan_name"])}), checked {b.nice_date(rows[0]["last_seen"][:10])}.</p>
</div></section>
{one_seller(b.clinic_section(g, rows))}
<div class="wrap seller-body">
  <div class="seller-main"><section class="seller-sec">{where_list(three, "The three cheapest other clinics for semaglutide.", "Other clinics for semaglutide")}</section></div>
  <aside class="seller-side" aria-label="Background check">{b.check_card(r)}</aside>
</div>
{foot([f'<a href="/sellers/{slug}/">{escape(name)} review</a>', '<a href="/peptides/semaglutide/">Semaglutide</a>', '<a href="/sellers/#substance=semaglutide">Every seller of semaglutide</a>'], [f"{escape(name)} price page, checked {b.nice_date(rows[0]['last_seen'][:10])}."])}"""
    return f"sellers/{slug}/semaglutide", f"Semaglutide at {name}", body, [("/sellers/", "Sellers"), (f"/sellers/{slug}/", name), ("", "Semaglutide")]


def company():
    co = "Harbin Jixianglong Biotech Co., Ltd."
    rows = [x for x in b.LETTERS_ALL if x["company_name"] == co]
    trs = "".join(f'<tr><td class="num" data-l="Date">{b.nice_date(x["letter_date"])}</td><td data-l="Subject">{escape(b.clean(x["letter_subject"]))}</td>'
                  f'<td><a href="{escape(x["letter_url"])}" rel="nofollow">FDA letter</a>{b.closed_chip(x["letter_url"])}</td></tr>' for x in rows)
    subs = sorted({s for x in rows for s in b.SUBS_OF_LETTER.get(x["letter_url"], [])})
    sub_links = ", ".join(f'<a href="/peptides/{s}/">{escape(b.pep_name(s))}</a>' if s in b.PEPTIDE_SLUGS else escape(s) for s in subs) or "No substance named in our data."
    body = f"""
{BANNER}
<section class="section letters-hd"><div class="wrap">
  <h1>FDA warning letters to Harbin Jixianglong Biotech</h1>
  <p class="lede">A warning letter is the FDA's formal notice that a company broke the law; it is not a fine or a ban.</p>
  {b.author_line(max(x["letter_date"] for x in rows))}
</div></section>
<section class="band-2"><div class="wrap">
  <div class="tbl-wrap"><table class="tbl tbl-cards"><caption class="vh">FDA warning letters to the company</caption>
  <thead><tr><th scope="col">Date</th><th scope="col">Subject</th><th scope="col">Letter</th></tr></thead><tbody>{trs}</tbody></table></div>
  <p class="small">Substances the letters name: {sub_links}</p>
</div></section>
{foot(['<a href="/fda-warning-letters/">Every FDA warning letter to peptide sellers</a>'], [f"FDA, warning letter, {b.nice_date(rows[0]['letter_date'])}"])}"""
    return "fda-warning-letters/harbin-jixianglong-biotech", "Harbin Jixianglong Biotech", body, [("/fda-warning-letters/", "FDA warning letters"), ("", "Harbin Jixianglong Biotech")]


def tool():
    shops = sorted([r for r in b.seller_rows("bpc-157", "research") if r.get("price_per_mg")], key=b.shop_rank)[:3]
    ex = shops[0] if shops else None
    example = (f'Example from today\'s data: {b.money(ex["price_usd"])} for a vial of {ex.get("amount_mg") or "?"} mg is {b.per_mg(ex["price_per_mg"])}/mg (checked {b.nice_date(str(ex.get("last_seen", ""))[:10])}).'
               if ex else "")
    body = f"""
{BANNER}
<section class="hero hero-goal"><div class="wrap">
  <h1>Peptide price per mg calculator</h1>
  {b.author_line(b.DATA_CHECKED)}
  <div class="panel-line" style="display:grid;gap:24px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))">
    <form onsubmit="return false" style="display:grid;gap:12px">
      <label class="small" for="t-price">Price of one vial ($)</label><input class="input" id="t-price" inputmode="decimal" value="{float(ex['price_usd']) if ex else 50}">
      <label class="small" for="t-mg">Amount in the vial (mg)</label><input class="input" id="t-mg" inputmode="decimal" value="{ex.get('amount_mg') or 5 if ex else 5}">
      <label class="small" for="t-n">Vials a month</label><input class="input" id="t-n" inputmode="decimal" value="1">
    </form>
    <div aria-live="polite"><p class="small">Price per mg</p><p class="num-xl" id="t-ppm">-</p><p class="small">Price per month</p><p class="num-xl" id="t-pm">-</p>
    <noscript><p class="small">Price per mg is the price divided by the mg in the vial. {example}</p></noscript></div>
  </div>
  <p class="small">{example}</p>
</div></section>
<section class="section"><div class="wrap"><h2>Compare with today's prices</h2><p class="small">BPC-157 at the best-checked research-use shops; we do not link to them.</p>
<ul class="where-list">{"".join(f'<li><span class="where-who"><span class="name">{escape(b.seller_base(b.clean(x["seller_name"])))}</span><span class="sub">{escape(b.clean(x["product_name"]))}</span></span><span class="where-price"><span class="num">{b.per_mg(x["price_per_mg"])}/mg</span></span></li>' for x in shops)}</ul></div></section>
<script>(function(){{var p=document.getElementById('t-price'),m=document.getElementById('t-mg'),n=document.getElementById('t-n');
function f(){{var a=parseFloat(p.value),b=parseFloat(m.value),c=parseFloat(n.value);document.getElementById('t-ppm').textContent=a>0&&b>0?'$'+(a/b).toFixed(2)+' per mg':'-';
document.getElementById('t-pm').textContent=a>0&&c>0?'$'+(a*c).toFixed(0)+' per month':'-';}}[p,m,n].forEach(function(x){{x.addEventListener('input',f);}});f();}})();</script>
{foot(['<a href="/peptides/bpc-157/">BPC-157</a>', '<a href="/learn/">Guides</a>'], ["Shop prices from the shops' product pages, each with its check date."])}"""
    return "tools/price-per-mg", "Peptide price per mg calculator", body, [("", "Tools"), ("", "Peptide price per mg calculator")]


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(b.DIST, OUT)
    index = []
    for fn in (group_list, group_guide, subpage, brand, offer, company, tool):
        path, title, body, crumb = fn()
        crumb = [(MOCK + "/" if h == "" and i < len(crumb) - 1 else h, t) for i, (h, t) in enumerate(crumb)]
        html = b.page(f"/{path}/", f"{title} | Peptide Chooser", "Local template", body, crumb=crumb)
        html = html.replace("<head>", '<head>\n<meta name="robots" content="noindex">', 1)
        f = OUT / MOCK.strip("/") / path / "index.html"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(html, encoding="utf-8")
        index.append(f'<li><a href="{MOCK}/{path}/">{escape(title)}</a> <span class="small">/{path}/</span></li>')
    (OUT / MOCK.strip("/") / "index.html").write_text(
        b.page("/_mock/", "Templates, round 2 | Peptide Chooser", "Local templates",
               f'<section class="section"><div class="wrap"><h1>Templates, round 2</h1><ul>{"".join(index)}</ul></div></section>'),
        encoding="utf-8")
    for line in index:
        path = line.split('href="')[1].split('"')[0]
        w = OUT / "_w390" / path.strip("/").replace("/", "-")
        w.mkdir(parents=True, exist_ok=True)
        (w / "index.html").write_text(f'<!doctype html><body style="margin:0"><iframe src="{path}" width="390" height="4000" style="border:0"></iframe>', encoding="utf-8")
    print("\n".join(index))


main()
