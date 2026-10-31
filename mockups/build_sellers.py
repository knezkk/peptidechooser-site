"""Mockup for the owner (31 Oct 2026): how Home looks when one product has ten sellers, with a price comparison and a
background check per seller. Built from the real dist/index.html; only the hair goal's "Get it" panel and a new
sellers section are added. Every seller, price and check here is made up and the page says so at the top.

    python3 build.py && python3 mockups/build_sellers.py   # writes mockups/sellers-10.html (serve the repo root)
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
html = (ROOT / "dist" / "index.html").read_text(encoding="utf-8").replace('href="/assets/', 'href="/dist/assets/')

# name, kind, $/mo, visit fee, checks passed (of 6), warning letter, complaints, rating, link: paid | none | no
SELLERS = [
    ("Example Clinic A", "Online clinic", 12, 0, 6, False, "3 in 3 years, all answered", 4.7, "paid"),
    ("Example Pharmacy B", "Online pharmacy", 9, 15, 6, False, "1 in 3 years, answered", 4.6, "none"),
    ("Example Health C", "Online clinic", 16, 0, 6, False, "8 in 3 years, all answered", 4.4, "paid"),
    ("Example Rx D", "Mail-order pharmacy", 8, 25, 5, False, "None found", 4.2, "none"),
    ("Example Men's Care E", "Online clinic", 22, 0, 5, False, "21 in 3 years, 4 unanswered", 3.9, "paid"),
    ("Example Direct F", "Online clinic", 14, 30, 5, False, "5 in 3 years, all answered", 3.8, "none"),
    ("Example Hair Co G", "Subscription brand", 25, 0, 4, False, "37 in 3 years, 12 unanswered", 3.2, "none"),
    ("Example Telehealth H", "Online clinic", 11, 49, 4, False, "None found", 3.1, "none"),
    ("Example Meds I", "Online pharmacy", 6, 0, 2, True, "Not checked: no US address", 1.4, "no"),
    ("Example Global J", "Overseas website", 5, 0, 1, True, "Not checked: no US address", 0.8, "no"),
]
CHECKS = [
    ("Pharmacy named and US-licensed", "State board of pharmacy record"),
    ("LegitScript certified", "LegitScript directory"),
    ("A licensed US prescriber sees you", "Seller's terms and the prescriber's state license"),
    ("No FDA warning letters", "FDA warning letters database"),
    ("Who owns it is public", "Company registry and the seller's site"),
    ("Complaints answered", "Better Business Bureau file"),
]
CHECKED = "30 Oct 2026"


def check_chip(n, letter):
    if letter:
        return '<span class="chip chip-neutral">FDA warning letter</span>'
    return f'<span class="chip chip-{"ok" if n == 6 else "warn" if n >= 4 else "neutral"}">{n} of 6 checks</span>'


def action(link):
    if link == "paid":
        return '<span class="pick-act"><a class="btn btn-action btn-sm" href="#" rel="sponsored">Visit</a><span class="paid">Paid link</span></span>'
    if link == "none":
        return '<span class="pick-act"><span class="btn btn-action btn-sm" role="button" aria-disabled="true">Visit</span><span class="paid">No paid link yet</span></span>'
    return '<span class="note">We do not link to it</span>'


def details(s):
    _, _, _, _, n, letter, complaints, _, _ = s
    # the first n checks pass, the rest fail (made-up data, enough to show the layout)
    rows = []
    for i, (name, src) in enumerate(CHECKS):
        ok = i < n and not (letter and i == 3)
        res = complaints if i == 5 else ("Yes" if ok else "No")
        chip = "ok" if ok else "neutral"
        rows.append(f'<li><span class="chip chip-{chip}">{"Pass" if ok else "Fail"}</span><span><strong>{name}</strong>: {res}'
                    f'<span class="note">{src}, checked {CHECKED}</span></span></li>')
    return f'<ul class="bg-list">{"".join(rows)}</ul>'


rows, cards = [], []
for i, s in enumerate(SELLERS):
    name, kind, usd, fee, n, letter, complaints, rating, link = s
    first = usd + fee
    open_ = " open" if i == 0 else ""
    rows.append(f"""<tr>
  <td class="rank">{i + 1}</td>
  <td><span class="name">{name}</span><span class="note">{kind}</span></td>
  <td><span class="num-l">${usd}<span class="num-unit">/mo</span></span><span class="note">{"no visit fee" if not fee else f"plus ${fee} first visit"}</span></td>
  <td><span class="name">${first}</span></td>
  <td><details{open_}><summary>{check_chip(n, letter)} <span class="see">See checks</span></summary>{details(s)}</details></td>
  <td><span class="name">{rating:.1f}</span><span class="note">of 5</span></td>
  <td class="act">{action(link)}</td>
</tr>""")
    cards.append(f"""<li class="seller-card">
  <div class="sc-hd"><span class="rank">{i + 1}</span><span><span class="name">{name}</span><span class="note">{kind}</span></span><span class="sc-rate"><strong>{rating:.1f}</strong> of 5</span></div>
  <div class="sc-price"><span class="num-l">${usd}<span class="num-unit">/mo</span></span><span class="note">{"no visit fee" if not fee else f"plus ${fee} first visit"}; first month ${first}</span></div>
  <details{open_}><summary>{check_chip(n, letter)} <span class="see">See checks</span></summary>{details(s)}</details>
  <div class="sc-act">{action(link)}</div>
</li>""")

section = f"""<section class="sellers" id="sellers" aria-labelledby="sellers-h">
  <div class="sellers-hd">
    <div><h2 id="sellers-h">Finasteride 1 mg: 10 sellers compared</h2>
    <p>Every seller is checked the same six ways. Sorted by our rating; a paid link never moves a seller up. Prices checked {CHECKED}.</p></div>
    <div class="sort" role="group" aria-label="Sort sellers"><span class="note">Sort by</span>
      <button type="button" class="seg" aria-pressed="true">Our rating</button><button type="button" class="seg" aria-pressed="false">Price per month</button><button type="button" class="seg" aria-pressed="false">First month</button></div>
  </div>
  <div class="tbl-wrap sellers-tbl"><table class="tbl">
    <thead><tr><th scope="col"></th><th scope="col">Seller</th><th scope="col">Price</th><th scope="col">First month</th><th scope="col">Background check</th><th scope="col">Our rating</th><th scope="col"></th></tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table></div>
  <ul class="seller-cards">{"".join(cards)}</ul>
  <p class="small">The six checks: {"; ".join(c[0] for c in CHECKS)}. Each result links to its source with the date we checked it.</p>
</section>
"""

get_old = html[html.index('id="get-hair"'):]
get_old = get_old[:get_old.index('<div class="step-panel"')]
get_new = ('id="get-hair" data-goal="hair"><p class="get-pick"><span class="name">Finasteride 1 mg</span><span class="chip chip-ok">FDA approved</span></p>'
           '<p class="get-how">Best rated of 10 sellers: <strong>Example Clinic A</strong>, $12/mo, no visit fee, passes all 6 checks.</p>'
           '<span class="pick-act"><a class="btn btn-action" href="#" rel="sponsored">Visit</a><span class="paid">Paid link</span></span>'
           '<p class="get-more"><a href="#sellers">Compare all 10 sellers</a></p></div>')
html = html.replace(get_old, get_new)
html = html.replace('<section class="rate-strip"', section + '    <section class="rate-strip"', 1)

css = """<style>
.mock-note{background:var(--warn-tint);color:var(--warn-text);font:600 14px var(--font-text);padding:10px 16px;text-align:center}
.get-more{margin:14px 0 0;font-weight:600}
.sellers{margin-top:32px;background:var(--white);border:1px solid var(--line-strong);border-radius:var(--radius-panel);padding:24px}
.sellers-hd{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;gap:12px 24px;margin-bottom:16px}
.sellers-hd h2{font-size:22px;line-height:1.3;margin:0 0 4px}
.sellers-hd p{margin:0;color:var(--ink-2);max-width:70ch}
.sort{display:flex;align-items:center;gap:6px}
.seg{min-height:var(--touch);padding:0 14px;border:1px solid var(--line-strong);border-radius:var(--radius-control);background:var(--white);font:600 14px var(--font-text);color:var(--ink);cursor:pointer}
.seg[aria-pressed="true"]{background:var(--clinic-tint);border-color:var(--clinic);color:var(--clinic-text)}
.sellers .tbl td{vertical-align:top}
.sellers .rank{font:800 15px var(--font-display);color:var(--ink-2)}
.sellers details summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:8px}
.sellers details summary::-webkit-details-marker{display:none}
.sellers .see{font-size:var(--small-size);color:var(--clinic);text-decoration:underline}
.bg-list{list-style:none;margin:10px 0 0;padding:0;display:grid;gap:8px;min-width:300px}
.bg-list li{display:grid;grid-template-columns:44px minmax(0,1fr);gap:8px;align-items:start;font-size:var(--small-size);line-height:1.4}
.bg-list .note{display:block;color:var(--ink-2)}
.seller-cards{display:none;list-style:none;margin:0;padding:0}
@media (max-width:760px){
 .sellers{padding:16px}
 .sellers-tbl{display:none}
 .seller-cards{display:grid;gap:10px;margin-bottom:12px}
 .seller-card{border:1px solid var(--line);border-radius:var(--radius-panel);padding:14px;display:grid;gap:10px}
 .sc-hd{display:grid;grid-template-columns:24px minmax(0,1fr) auto;gap:8px;align-items:start}
 .sc-hd .name{display:block;font-weight:700}.sc-hd .note{display:block;font-size:var(--small-size);color:var(--ink-2)}
 .sc-price .note{display:block;font-size:var(--small-size);color:var(--ink-2)}
 .sort{flex-wrap:wrap}
}
</style>"""
html = html.replace("</head>", css + "</head>", 1)
html = html.replace("<body>", '<body><div class="mock-note">Mockup with example data: the ten sellers, their prices and their checks are made up to show the layout.</div>', 1)
assert "mock-note" in html and 'id="sellers"' in html
(ROOT / "mockups" / "sellers-10.html").write_text(html, encoding="utf-8")
print("ok")
