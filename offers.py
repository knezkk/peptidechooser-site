"""Seller offer pages, test of 20 (queue block 28, task 6A; design/pages/new-types.md, Seller offer, with the round 3 fixes;
site map rules section 1; ODOBRENO PRAVILA - Karlo - 9. 11. 2026 - 6A test). One online clinic's offer of one substance at
/sellers/<seller>/<substance>/, built for the pilot of 3 (build.py, OFFER_PILOT) and, with PC_OFFERS=preview, for the
rest of the test. Every fact comes from the data; the title, description, H1 and the template sentences below are
approved (ODOBRENO SEO - Karlo - 9. 11. 2026 - PR #161).

The page, top to bottom: the first screen (H1, author line, the kind chip, one paragraph; the Background check card on the
right), the "<Substance> plans" band (the clinic table's rows without the Clinic column), the plan terms and the price
history when the data has them, "Other clinics for <substance>", then What to do next and Sources."""
from html import escape


TITLE_TAILS = (": price, plans and checks", ": plans and checks", ": plans and prices", " plans", "")


def title(b, seller, sub):
    """Proposed title (new-types.md): "<Substance> at <Seller>: price, plans and checks | Peptide Chooser", its middle words
    shortened step by step to the 60 characters tools/check.py allows, as seller_title does; the names always stay."""
    for tail in TITLE_TAILS:
        t = f"{sub_name(b, sub)} at {seller_short(b, seller)}{tail} | Peptide Chooser"
        if len(t) <= 60:
            return t
    return t


def h1(b, seller, sub):
    return f"{sub_name(b, sub)} at {seller_short(b, seller)}"


def description(b, seller, sub):
    """Proposed description: no count, price or date from data (new-types.md, rule 5.3), under 160 characters."""
    s, n = sub_name(b, sub), seller_short(b, seller)
    d = f"{s} plans at {n}, an online clinic: each plan's monthly price, care fee and terms, our background checks, and other clinics for {s}."
    return d if len(d) <= 160 else f"{s} plans at {n}, an online clinic: monthly prices, plan terms and our background checks."


def sub_name(b, sub):
    return b.re.sub(r" *\(.*\)$", "", b.sub_label(sub))


def seller_short(b, seller):
    return b.seller_base(b.seller_name(b.PROFILES[seller]))


def first_screen(b, seller, sub, plans):
    r, s, n = b.PROFILES[seller], sub_name(b, sub), seller_short(b, seller)
    low = plans[0]
    on = max(p["last_seen"] for p in plans)
    what = (f"{n} is an online clinic. Its price page shows "
            + (f"one plan of {escape(s)}, {escape(b.clean(low['plan_name']))}, at {b.usd(low['price_monthly'])} a month"
               if len(plans) == 1 else
               f"{b.plural(len(plans), 'plan')} of {escape(s)}; the lowest is {b.usd(low['price_monthly'])} a month "
               f"({escape(b.clean(low['plan_name']))})")
            + f", {b.care_words(low)}. Prices checked {b.nice_date(on)}.")
    # the left column takes no class of its own in the CSS: "seller-main" would put the card above the H1 on phones (order 2)
    return f"""
<section class="seller-top">
  <div class="wrap seller-body">
    <div class="offer-first">
      <h1>{escape(h1(b, seller, sub))}</h1>
      <p class="seller-kind"><span class="chip chip-neutral">{b.kind_words(r)[1]}</span></p>
      {b.author_line(on)}
      <p class="intro seller-answer">{what}</p>
    </div>
    <aside class="seller-side" aria-label="Background check">{b.check_card(r)}</aside>
  </div>
</section>"""


def plans_band(b, sub, plans):
    """The clinic table's rows for this one clinic (round 3: no Clinic column, the plan name leads)."""
    trs = []
    for p in plans:
        trs.append(f'<tr><td><span class="cell-pic">{b.parts.plan_picture(p)}<span class="name">{b.slash_break(b.clean(p["plan_name"]))}</span></span></td>'
                   f'<td data-l="Form">{b.plan_form_word(p)}</td>'
                   f'<td data-l="What it is">{b.plan_chip(b.plan_goal(p), p)}</td>'
                   f'<td data-l="Per month"><span class="num">{b.usd(p["price_monthly"])}</span>{b.plan_letter(p)}</td>'
                   f'<td data-l="Care fee">{b.care_words(p)}</td>'
                   f'<td class="act">{b.clinic_row_act(p, "seller page")}</td></tr>')
    return f"""
<section class="band-2" id="plans">
  <div class="wrap">
    <div class="sec-hd"><div><h2>{escape(sub_name(b, sub))} plans</h2><p>The plans on this clinic's price page, cheapest first.</p></div></div>
    <div class="tbl-wrap"><table class="tbl tbl-cards tbl-clinics">
      <thead><tr><th scope="col">Plan</th><th scope="col">Form</th><th scope="col">What it is</th><th scope="col">Per month</th><th scope="col">Care fee</th><th scope="col"><span class="vh">Action</span></th></tr></thead>
      <tbody>{"".join(trs)}</tbody>
    </table></div>
  </div>
</section>"""


def terms_section(b, plans):
    """Plan terms as a ledger per plan (the Facts card's list), and each plan's own price history when it has one."""
    blocks = []
    for p in plans:
        facts = b.plan_terms(p)
        if not facts:
            continue
        rows = "".join(f"<li><span>{k}</span><span>{v}</span></li>" for k, v in facts)
        blocks.append(f'<div class="pep-group"><h3>{escape(b.clean(p["plan_name"]))}</h3><ul class="facts-list">{rows}</ul></div>')
    hist = []
    for p in plans:
        pts = b.offer_history(p)
        if pts:
            rows = "".join(f'<tr><td>{b.nice_date(d)}</td><td class="num">{b.usd(v)}/mo</td></tr>' for d, v in pts)
            hist.append(f'<h3>Price over time: {escape(b.clean(p["plan_name"]))}</h3><div class="tbl-wrap"><table class="tbl tbl-compact">'
                        f'<thead><tr><th scope="col">Date</th><th scope="col">Per month, care fee included</th></tr></thead><tbody>{rows}</tbody></table></div>')
    if not blocks and not hist:
        return ""
    head = ('<div class="sec-hd"><div><h2>Plan terms</h2><p>What the price page says beyond the monthly price: how long you '
            'commit, what the first month costs and any consult fee.</p></div></div>') if blocks else ""
    return f'<section class="section" id="terms"><div class="wrap">{head}{"".join(blocks)}{"".join(hist)}</div></section>'


def others_section(b, seller, sub):
    """The three cheapest other clinics for the substance (one plan each), as the substance page's list, and every seller."""
    best = {}
    for p in sorted((p for p in b.PLANS if p["seller_slug"] != seller and p["substance_slug"] == sub and p.get("price_monthly") is not None
                     and not b.plan_is_blend(p) and p["seller_slug"] in b.PROFILES),
                    key=lambda p: (float(p["price_monthly"]), p["seller_name"])):
        best.setdefault(p["seller_slug"], p)
    rows = list(best.values())[:3]
    if not rows:
        return ""
    s = sub_name(b, sub)
    lines = "".join(
        f'<li><span class="where-who">{b.clinic_link(p["seller_slug"], b.seller_base(p["seller_name"]))}'
        f'<span class="sub">{escape(b.clean(p["plan_name"]))}<span class="chip chip-{b.kind_chip(p)[0]}">{b.kind_chip(p)[1]}</span></span></span>'
        f'<span class="where-price"><span class="num">{b.usd(p["price_monthly"])}/mo</span>{b.plan_letter(p)}</span>'
        f'{b.clinic_button(p["seller_slug"], "See plans", plan=p, placement="seller page")}</li>' for p in rows)
    return f"""
<section class="section" id="others">
  <div class="wrap">
    <div class="panel-line pep-where"><h2>Other clinics for {escape(s)}</h2><p class="small">The cheapest plan of {escape(s)} at each of the other online clinics we track.</p>
    <ul class="where-list">{lines}</ul>
    <p class="small"><a href="/sellers/#substance={sub}">Every seller of {escape(s)}</a></p></div>
  </div>
</section>"""


def next_and_sources(b, seller, sub, plans):
    s, n = sub_name(b, sub), seller_short(b, seller)
    links = [f'<li><a href="/sellers/{seller}/">Our review of {escape(n)}, with every plan</a></li>']
    if sub in b.PEPTIDE_SLUGS:
        links.append(f'<li><a href="/peptides/{sub}/">{escape(s)}: FDA status and every clinic</a></li>')
    # across to up to five indexable offer pages of the same substance (site map rule 4.3)
    links += [f'<li><a href="/sellers/{x}/{sub}/">{escape(sub_name(b, sub))} at {escape(seller_short(b, x))}</a></li>'
              for x, y in sorted(b.OFFER_INDEXED) if y == sub and x != seller][:5]
    srcs, seen = [], set()
    for p in plans:
        url = p.get("pricing_url")
        if url and url not in seen:
            seen.add(url)
            srcs.append(f'<li>{escape(n)}, {escape(b.clean(p["plan_name"]))}, price page, {b.nice_date(p["last_seen"])}: '
                        f'{escape(url)}</li>')  # as text: a seller page never links to a seller's site (pages/seller.md)
    src = (f'<section class="pep-sources" aria-labelledby="sources-h"><h2 id="sources-h" class="h-sources">Sources</h2>'
           f'<ol class="small sources">{"".join(srcs)}</ol></section>') if srcs else ""
    return (f'<section class="section pep-foot"><div class="wrap"><div class="goal-two"><div><h2 class="h-sources">What to do next</h2>'
            f'<ul class="next-list">{"".join(links)}</ul></div>{src}</div></div></section>')


def page(b, seller, sub):
    plans = b.offer_plans(seller, sub)
    return (first_screen(b, seller, sub, plans) + plans_band(b, sub, plans) + terms_section(b, plans)
            + others_section(b, seller, sub) + next_and_sources(b, seller, sub, plans))


def pages(b):
    """PAGES entries for the offer pages this build makes (b.OFFER_BUILT), and the paths that carry noindex."""
    out, noindex = [], set()
    for seller, sub in sorted(b.OFFER_BUILT):
        path = f"/sellers/{seller}/{sub}/"
        out.append((path, path.strip("/") + "/index.html", title(b, seller, sub), description(b, seller, sub), page(b, seller, sub), "",
                    [("/sellers/", "Sellers"), (f"/sellers/{seller}/", b.seller_name(b.PROFILES[seller])), (path, sub_name(b, sub))]))
        if (seller, sub) not in b.OFFER_INDEXED:
            noindex.add(path)
    return out, noindex
