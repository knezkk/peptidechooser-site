"""Mockup for the owner (31 Oct 2026): how Home looks when one product has ten sellers, with a price comparison and a
background check per seller, opened from the option's own row in a window over the page (steps 2 and 3 are one). Built from the real
dist/index.html; only the finasteride row of the hair goal changes. Every seller, price and check here is made up and the page says so at the top.

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


rows = []
for i, s in enumerate(SELLERS):
    name, kind, usd, fee, n, letter, complaints, rating, link = s
    first = usd + fee
    open_ = " open" if i == 0 else ""
    rows.append(f"""<li class="seller">
  <div class="s-name"><span class="rank">{i + 1}</span><span><span class="name">{name}</span><span class="note">{kind}</span></span></div>
  <div class="s-price"><span class="num-m">${usd}<span class="num-unit">/mo</span></span><span class="note">{"no visit fee" if not fee else f"plus ${fee} first visit"}; first month ${first}</span></div>
  <div class="s-rate"><strong>{rating:.1f}</strong> <span class="note">of 5</span></div>
  <div class="s-act">{action(link)}</div>
  <details class="s-checks"{open_}><summary>{check_chip(n, letter)} <span class="see">See checks</span></summary>{details(s)}</details>
</li>""")

# The button sits on the option's row; the sellers open in a window over the page that closes with "Close", Esc or a
# click outside it (owner, 31 Oct 2026: not expanded inside the row).
panel = ('<button type="button" class="btn btn-line btn-sm sellers-open" '
         'onclick="document.getElementById(\'sellers-fin\').showModal()">Compare 10 sellers</button>')
dialog = f"""<dialog class="sellers-dlg" id="sellers-fin" aria-labelledby="sellers-h" onclick="if(event.target===this)this.close()">
  <div class="dlg-hd"><h2 id="sellers-h">Finasteride 1 mg: 10 sellers compared</h2>
    <form method="dialog"><button class="btn btn-line btn-sm">Close</button></form></div>
  <div class="sellers-hd"><p>Every seller is checked the same six ways. Sorted by our rating; a paid link never moves a seller up. Prices checked {CHECKED}.</p>
    <div class="sort" role="group" aria-label="Sort sellers"><span class="note">Sort by</span>
      <button type="button" class="seg" aria-pressed="true">Rating</button><button type="button" class="seg" aria-pressed="false">Price</button><button type="button" class="seg" aria-pressed="false">First month</button></div></div>
  <ol class="seller-list">{"".join(rows)}</ol>
  <p class="small">The six checks: {"; ".join(c[0] for c in CHECKS)}. Each result links to its source with the date we checked it.</p>
</dialog>"""

# The finasteride row in the hair options: its Visit gives way to the seller list, which opens inside the row.
start = html.index('<li class="opt"><div class="opt-main"><span class="name">Finasteride 1 mg')
end = html.index("</li>", start)
row = html[start:end]
if '<span class="pick-act">' in row:
    pa = row.index('<span class="pick-act">')
    row = row[:pa] + row[row.index("</span></span>", pa) + len("</span></span>"):]
html = html[:start] + row + panel + html[end:]
html = html.replace("</body>", dialog + "</body>", 1)

css = """<style>
.mock-note{background:var(--warn-tint);color:var(--warn-text);font:600 14px var(--font-text);padding:10px 16px;text-align:center}
.flow .opt .sellers-open{grid-column:1/-1;width:max-content;margin-top:4px}
.sellers-dlg{width:min(960px,calc(100% - 32px));max-height:calc(100vh - 48px);padding:0 24px 24px;border:1px solid var(--line-strong);border-radius:var(--radius-panel);background:var(--white);color:var(--ink);box-shadow:var(--shadow-card)}
.sellers-dlg::backdrop{background:color-mix(in srgb,var(--ink) 55%,transparent)}
.dlg-hd{position:sticky;top:0;z-index:1;display:flex;justify-content:space-between;align-items:center;gap:16px;padding:20px 0 12px;margin-bottom:12px;background:var(--white);border-bottom:1px solid var(--line)}
.dlg-hd h2{font-size:20px;line-height:1.3;margin:0}
.dlg-hd form{margin:0}
.sellers-hd{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:8px 16px;margin-bottom:8px}
.sellers-hd p{margin:0;font-size:var(--small-size);line-height:1.45;color:var(--ink-2);max-width:52ch}
.sort{display:flex;flex-wrap:wrap;align-items:center;gap:6px}
.seg{min-height:var(--touch);padding:0 12px;border:1px solid var(--line-strong);border-radius:var(--radius-control);background:var(--white);font:600 13px var(--font-text);color:var(--ink);cursor:pointer}
.seg[aria-pressed="true"]{background:var(--clinic-tint);border-color:var(--clinic);color:var(--clinic-text)}
.seller-list{list-style:none;margin:0;padding:0}
.seller{display:grid;grid-template-columns:minmax(0,1fr) auto;grid-template-areas:"name rate" "price price" "checks checks" "act act";gap:8px 16px;padding:12px 0;border-top:1px solid var(--line)}
.s-name{grid-area:name;display:flex;gap:10px}.s-price{grid-area:price}.s-rate{grid-area:rate;text-align:right}.s-act{grid-area:act}.s-checks{grid-area:checks}
.seller .rank{font:800 15px var(--font-display);color:var(--ink-2);min-width:20px}
.seller .name{display:block;font-weight:700}
.seller .note{display:block;font-size:var(--small-size);line-height:1.4;color:var(--ink-2)}
.s-rate .note{display:inline}
.num-m{font:800 20px/1.2 var(--font-display);color:var(--ink)}
.s-checks summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:8px}
.s-checks summary::-webkit-details-marker{display:none}
.see{font-size:var(--small-size);color:var(--clinic);text-decoration:underline}
.bg-list{list-style:none;margin:10px 0 0;padding:0;display:grid;gap:8px}
.bg-list li{display:grid;grid-template-columns:44px minmax(0,1fr);gap:8px;align-items:start;font-size:var(--small-size);line-height:1.4}
.bg-list .note{display:block;color:var(--ink-2)}
@media (max-width:640px){
 .sellers-dlg{width:100%;max-width:100%;max-height:100%;height:100%;margin:0;border-radius:0;padding:0 16px 16px}
}
@media (min-width:900px){
 .seller{grid-template-columns:minmax(0,1.3fr) minmax(0,1.1fr) 56px 118px;grid-template-areas:"name price rate act" "checks checks checks checks";align-items:start}
 .s-act{justify-self:end}.s-act .pick-act{align-items:flex-end}
}
</style>"""
html = html.replace("</head>", css + "</head>", 1)
html = html.replace("<body>", '<body><div class="mock-note">Mockup with example data: the ten sellers, their prices and their checks are made up to show the layout.</div>', 1)
assert "mock-note" in html and 'id="sellers-fin"' in html
(ROOT / "mockups" / "sellers-10.html").write_text(html, encoding="utf-8")
print("ok")
