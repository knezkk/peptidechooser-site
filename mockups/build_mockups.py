"""Five look options for the Home page, drawn as standalone mockups (not part of the site build).
python3 mockups/build_mockups.py  ->  mockups/option-1.html ... option-5.html and mockups/index.html
Text, numbers and statuses come from data/site.json, so every option shows the real content.
"""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "mockups"
DATA = json.loads((ROOT / "data" / "site.json").read_text())
CHECKED = (lambda d: f"{d.day} {d.strftime('%b %Y')}")(date.fromisoformat(DATA["checked"]))
H1 = "The best peptides for your goal, compared honestly."
LEDE = ("For each goal we put peptide products next to the FDA-approved alternatives and show what the evidence says, "
        "what it costs per month and how you would get it. We compare; we never sell.")

GOALS = []
for g in DATA["goals"]:
    GOALS.append({"slug": g["slug"], "label": g["label"], "intro": g["intro"], "count": len(g["peptides"]),
                  "peps": [[p["name"], p["status"], p["chip"]] for p in g["peptides"]],
                  "price": g.get("price_from_usd") if g.get("live") else None,
                  "best": g.get("best_option", ""), "checked_n": g.get("options_checked", 0), "page": bool(g.get("page"))})


# The body: front view, eight heads tall, viewBox 240 x 480. Right half is listed, mirrored and smoothed.
def body_path():
    r = [(128, 52), (130, 74), (146, 80), (164, 88), (175, 100), (178, 118), (179, 150), (181, 182), (185, 214), (188, 244),
         (192, 262), (191, 280), (185, 288), (179, 284), (176, 266), (172, 248), (167, 216), (162, 184), (158, 150), (154, 128),
         (151, 150), (146, 192), (150, 224), (155, 250), (155, 284), (150, 322), (145, 348), (147, 378), (142, 416), (138, 446),
         (146, 462), (142, 472), (126, 472), (124, 458), (125, 440), (124, 404), (126, 378), (125, 350), (126, 316), (122, 276)]
    pts = r + [(120, 270)] + [(240 - x, y) for x, y in reversed(r)]
    f = lambda v: ("%.1f" % v).rstrip("0").rstrip(".")
    d = "M%s %s" % (f(pts[0][0]), f(pts[0][1]))
    n = len(pts)
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6, p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6, *p2)
        d += " C%s %s %s %s %s %s" % tuple(map(f, c))
    return d + "Z"


BODY = body_path()
HEAD = '<ellipse cx="120" cy="34" rx="21" ry="27"/>'
# Body regions per goal (figure coordinates): shaded areas clipped to the body, and where the pin sits.
REGIONS = {
    "hair": ([(120, 14, 24, 12)], (120, 13)),
    "skin": ([(120, 40, 17, 15)], (120, 42)),
    "muscle": ([(168, 128, 13, 26), (72, 128, 13, 26)], (72, 126)),
    "longevity": ([(131, 134, 13, 12)], (131, 134)),
    "weight-loss": ([(120, 204, 28, 24)], (120, 204)),
    "libido": ([(120, 258, 22, 12)], (120, 258)),
    "recovery": ([(136, 352, 13, 14), (104, 352, 13, 14)], (136, 352)),
}
# Label side and height for the leader-line version.
LABELS = {"hair": ("l", 30), "skin": ("l", 92), "muscle": ("l", 154), "weight-loss": ("l", 226),
          "longevity": ("r", 120), "libido": ("r", 262), "recovery": ("r", 352)}


def figure(kind="outline", labels=False, numbers=False, extra=""):
    """kind: outline (medical chart) or pictogram (geometric). Labels add leader lines to named goals."""
    ox = 160 if labels else 0
    vb = "0 0 560 490" if labels else "0 0 240 480"
    if kind == "pictogram":
        shape = ('<circle cx="120" cy="34" r="25"/><rect x="82" y="70" width="76" height="168" rx="22"/>'
                 '<rect x="52" y="74" width="24" height="168" rx="12"/><rect x="164" y="74" width="24" height="168" rx="12"/>'
                 '<rect x="86" y="230" width="32" height="236" rx="16"/><rect x="122" y="230" width="32" height="236" rx="16"/>')
        clip = shape
    else:
        shape = f'<path d="{BODY}"/>{HEAD}'
        clip = shape
    # The neck's top edge sits inside the head; this mask keeps that edge from showing as a line across the chin.
    head_black = HEAD.replace("/>", ' fill="#000"/>')
    nohead = f'<mask id="nohead-{kind}"><rect x="-10" y="-10" width="260" height="500" fill="#fff"/>{head_black}</mask>'
    parts = [f'<svg class="fig fig-{kind}" viewBox="{vb}" role="group" aria-label="Choose a goal on the body">',
             f'<defs><clipPath id="clip-{kind}">{clip}</clipPath>{nohead}{extra}</defs>',
             f'<g transform="translate({ox} 0)">', f'<g class="body">{shape}</g>', f'<g clip-path="url(#clip-{kind})">']
    for g in GOALS:
        for cx, cy, rx, ry in REGIONS[g["slug"]][0]:
            parts.append(f'<ellipse class="region" data-goal="{g["slug"]}" cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}"/>')
    parts.append("</g>")
    if kind == "outline":
        parts.append(f'<g class="contour"><path d="{BODY}" mask="url(#nohead-{kind})"/>{HEAD}</g>')
    parts.append("</g>")
    for i, g in enumerate(GOALS, 1):
        px, py = REGIONS[g["slug"]][1]
        px += ox
        if labels:
            side, ly = LABELS[g["slug"]]
            lx = 150 if side == "l" else 410
            elbow = lx + (30 if side == "l" else -30)
            anchor = "end" if side == "l" else "start"
            tx = lx - 8 if side == "l" else lx + 8
            parts.append(f'<g class="lbl" data-goal="{g["slug"]}" tabindex="0" role="button" aria-label="{g["label"]}">'
                         f'<polyline class="leader" points="{tx + (8 if side == "l" else -8)},{ly} {elbow},{ly} {px},{py}"/>'
                         f'<text x="{tx}" y="{ly + 5}" text-anchor="{anchor}">{g["label"]}</text></g>')
        parts.append(f'<g class="pin" data-goal="{g["slug"]}" tabindex="0" role="button" aria-label="{g["label"]}">'
                     f'<circle class="pin-hit" cx="{px}" cy="{py}" r="16"/><circle class="pin-ring" cx="{px}" cy="{py}" r="9"/>'
                     f'<circle class="pin-dot" cx="{px}" cy="{py}" r="4.5"/>'
                     + (f'<text class="pin-n" x="{px}" y="{py + 4}" text-anchor="middle">{i}</text>' if numbers else "") + "</g>")
    parts.append("</svg>")
    return "".join(parts)


def goal_list(numbers=False):
    items = "".join(
        f'<li><button type="button" data-goal="{g["slug"]}">'
        + (f'<span class="gl-n">{i:02d}</span>' if numbers else "")
        + f'<span class="gl-name">{g["label"]}</span><span class="gl-c">{g["count"]} options</span></button></li>'
        for i, g in enumerate(GOALS, 1))
    return f'<ul class="goals">{items}</ul>'


NAV = ('<header class="top"><div class="wrap top-in"><a class="brand" href="#"><img src="../assets/mark.svg" alt="" width="30" height="30">'
       '<span>Peptide Chooser</span></a><nav class="nav"><a href="#">Peptides</a><a href="#">Safety and legal</a><a href="#">Learn</a>'
       '<a href="#">How we rate</a><a href="#">About</a></nav><a class="btn btn-ink" href="#">Compare by goal</a></div></header>')
NOTICE = '<div class="notice"><div class="wrap">We compare, we don\'t sell. <span class="nm">Some links pay us. <a href="#">How we make money</a></span></div></div>'

JS = """<script>
var G=__GOALS__,CHECKED='__CHECKED__';
function chip(c,t){return '<span class="chip chip-'+c+'">'+t+'</span>';}
function render(s){var g=G.filter(function(x){return x.slug===s;})[0],p=document.getElementById('panel');if(!p)return;
var price=g.price?'<div class="p-price"><span class="p-num">$'+g.price+'</span><span class="p-unit">/mo</span></div><p class="p-what"><b>Cheapest proven option:</b> '+g.best+'<span class="p-sub">'+g.checked_n+' options checked, '+CHECKED+'</span></p>'
:'<p class="p-none">Full comparison for this goal is not published yet. The legal status below is current as of '+CHECKED+'.</p>';
p.innerHTML='<p class="p-k">'+g.label+'</p><h3 class="p-h">Peptides for '+g.label.toLowerCase()+'</h3>'+price+'<p class="p-intro">'+g.intro+'</p><ul class="p-list">'
+g.peps.map(function(x){return '<li><span>'+x[0]+'</span>'+chip(x[2],x[1])+'</li>';}).join('')+'</ul>'
+(g.page?'<div class="p-btns"><a class="btn btn-ink" href="#">Compare '+g.label.toLowerCase()+' options</a><a class="btn btn-line" href="#">Legal status</a></div>':'');
p.classList.remove('swap');void p.offsetWidth;p.classList.add('swap');}
function pick(s){document.querySelectorAll('[data-goal]').forEach(function(e){e.classList.toggle('on',e.getAttribute('data-goal')===s);
if(e.tagName==='BUTTON')e.setAttribute('aria-pressed',e.getAttribute('data-goal')===s?'true':'false');});render(s);}
document.addEventListener('click',function(e){var t=e.target.closest('[data-goal]');if(t)pick(t.getAttribute('data-goal'));});
document.addEventListener('keydown',function(e){var t=e.target.closest&&e.target.closest('[data-goal]');if(t&&(e.key==='Enter'||e.key===' ')){e.preventDefault();pick(t.getAttribute('data-goal'));}});
document.querySelectorAll('.fig [data-goal]').forEach(function(el){el.addEventListener('mouseenter',function(){var s=el.getAttribute('data-goal');
document.querySelectorAll('.fig [data-goal]').forEach(function(x){x.classList.toggle('hov',x.getAttribute('data-goal')===s);});});
el.addEventListener('mouseleave',function(){document.querySelectorAll('.hov').forEach(function(x){x.classList.remove('hov');});});});
pick('hair');
</script>"""

BASE_CSS = """*,*::before,*::after{box-sizing:border-box}body{margin:0}img,svg{display:block;max-width:100%}
.wrap{max-width:1240px;margin:0 auto;padding:0 32px}.top-in{display:flex;align-items:center;gap:28px;min-height:72px}
.brand{display:inline-flex;align-items:center;gap:10px;text-decoration:none;white-space:nowrap}.nav{display:flex;gap:22px;margin-left:auto}
.nav a{text-decoration:none;white-space:nowrap}.btn{display:inline-flex;align-items:center;justify-content:center;min-height:46px;padding:0 20px;text-decoration:none;font-weight:700;white-space:nowrap}
.notice .wrap{min-height:36px;display:flex;align-items:center;gap:6px}
.goals{list-style:none;margin:0;padding:0}.goals button{width:100%;display:flex;align-items:center;gap:12px;border:0;background:none;cursor:pointer;text-align:left;font:inherit;color:inherit}
.gl-c{margin-left:auto;white-space:nowrap}.p-list{list-style:none;margin:0;padding:0}.p-list li{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:6px 14px}
.p-btns{display:flex;flex-wrap:wrap;gap:10px}.p-sub{display:block}.chip{display:inline-block;white-space:nowrap}
.pin,.lbl{cursor:pointer}.pin-hit{fill:transparent}.leader{fill:none}.fig .region{transition:fill-opacity .25s}
.swap{animation:sw .28s ease-out}@keyframes sw{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.mock-tag{position:fixed;left:16px;bottom:16px;z-index:50;font:600 13px/1.3 system-ui,sans-serif;background:#111;color:#fff;padding:8px 12px;border-radius:6px}
@media (max-width:900px){.nav{display:none}.top-in .btn{margin-left:auto}}
@media (max-width:640px){.wrap{padding:0 16px}.nm{display:none}.top-in{min-height:60px}.top-in .btn{min-height:44px;padding:0 14px}.mock-tag{display:none}}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}"""


def page(n, name, fonts, css, body):
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Option {n}: {name} | Peptide Chooser mockup</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?{fonts}&display=swap" rel="stylesheet">
<style>{BASE_CSS}
{css}</style></head><body>{body}<div class="mock-tag">Option {n}: {name}</div>
{JS.replace("__GOALS__", json.dumps(GOALS)).replace("__CHECKED__", CHECKED)}</body></html>"""
    (OUT / f"option-{n}.html").write_text(html, encoding="utf-8")


SUB = {"H1": H1, "LEDE": LEDE, "NAV": NAV, "NOTICE": NOTICE, "CHECKED": CHECKED}


def fill(t, **kw):
    for k, v in {**SUB, **kw}.items():
        t = t.replace("{{" + k + "}}", v)
    return t


# 1. Clinic intake: white clinical chart, the body picks the goal and the prescription pad answers.
page(1, "Clinic intake", "family=Public+Sans:wght@400;500;600;700;800",
"""body{font-family:'Public Sans',system-ui,sans-serif;color:#0f1d2b;background:#fff}
.notice{background:#f1f5f8;color:#475569;font-size:14px}.notice a{color:#0b5cad}
.top{border-bottom:1px solid #e2e8ee}.brand{font-weight:800;font-size:20px;color:#0f1d2b}.nav a{color:#0f1d2b;font-weight:600;font-size:15px}
.btn{border-radius:6px;font-size:15px}.btn-ink{background:#0f1d2b;color:#fff}.btn-line{border:1.5px solid #0f1d2b;color:#0f1d2b}
.hero{padding:40px 0 48px;background:linear-gradient(#fff,#f6f9fb)}
.intro{display:grid;grid-template-columns:1fr auto;align-items:end;gap:24px;margin-bottom:28px}
h1{font-size:44px;line-height:1.08;letter-spacing:-.02em;margin:0;font-weight:800;max-width:17ch}
.lede{font-size:17px;line-height:1.55;color:#475569;margin:0;max-width:46ch}
.chart{display:grid;grid-template-columns:240px 300px 1fr;gap:28px;background:#fff;border:1px solid #dbe3ea;border-radius:12px;padding:24px;box-shadow:0 1px 2px rgba(15,29,43,.04)}
.chart-h{grid-column:1/-1;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #e2e8ee;padding-bottom:14px;margin-bottom:4px;font-size:13px;color:#64748b}
.chart-h b{color:#0f1d2b;font-size:15px}
.fig{height:440px;width:auto;margin:0 auto}.fig .body{fill:#eef3f7}.contour{fill:none;stroke:#7b8a99;stroke-width:1.1}
.region{fill:#0b5cad;fill-opacity:0}.region.hov{fill-opacity:.18}.region.on{fill-opacity:.32}
.pin-ring{fill:#fff;stroke:#0b5cad;stroke-width:2}.pin-dot{fill:#0b5cad}.pin.on .pin-ring{fill:#0b5cad}.pin.on .pin-dot{fill:#fff}
.goals li+li{border-top:1px solid #e9eef2}.goals button{padding:12px 12px;border-radius:8px;font-weight:600;font-size:16px}
.goals button:hover{background:#f1f5f8}.goals button.on{background:#e7f0fa;color:#0b4a8b}.gl-c{font-weight:400;font-size:13px;color:#64748b}
.panel{border:1.5px solid #0f1d2b;border-radius:10px;padding:20px 22px;position:relative;background:#fff}
.panel::before{content:"\\211E";position:absolute;right:18px;top:12px;font:700 28px/1 Georgia,serif;color:#0f1d2b}
.p-k{margin:0;font-size:13px;color:#64748b}.p-h{margin:2px 0 12px;font-size:22px;letter-spacing:-.01em}
.p-price{display:flex;align-items:baseline;gap:4px;border-top:2px solid #0f1d2b;padding-top:10px}.p-num{font-size:56px;font-weight:800;letter-spacing:-.03em;line-height:1}
.p-unit{color:#64748b;font-size:18px}.p-what{margin:8px 0 10px;font-size:15px}.p-sub{color:#64748b;font-size:13px;margin-top:2px}
.p-none{border-top:2px solid #0f1d2b;padding-top:12px;font-size:15px;color:#334155}.p-intro{font-size:14px;color:#475569;line-height:1.5;margin:0 0 8px}
.p-list li{padding:8px 0;border-top:1px solid #e9eef2;font-size:14px;font-weight:600}.p-btns{margin-top:14px}
.chip{font-size:12px;font-weight:700;padding:3px 8px;border-radius:4px}.chip-ok{background:#e3f4ea;color:#11633a}.chip-info{background:#e6eefb;color:#1e4b9b}.chip-warn{background:#fdf0e1;color:#8a3e05}.chip-neutral{background:#eef1f4;color:#475569}
@media (max-width:1100px){.chart{grid-template-columns:200px 1fr}.chart .panel{grid-column:1/-1}}
@media (max-width:640px){.hero{padding:24px 0}.intro{grid-template-columns:1fr}h1{font-size:32px}.chart{grid-template-columns:110px 1fr;padding:14px;gap:14px}.fig{height:250px}.goals button{padding:9px 6px;font-size:14px}.gl-c{display:none}.p-num{font-size:48px}}""",
fill("""{{NOTICE}}{{NAV}}<main class="hero"><div class="wrap">
<div class="intro"><div><h1>{{H1}}</h1></div><p class="lede">{{LEDE}}</p></div>
<section class="chart" aria-label="Choose a goal"><div class="chart-h"><b>Where do you want to see a change?</b><span>Tap the body or a goal. Prices and status checked {{CHECKED}}.</span></div>
<div>{{FIG}}</div><div>{{LIST}}</div><div id="panel" class="panel" aria-live="polite"></div></section>
</div></main>""", FIG=figure("outline"), LIST=goal_list()))

# 2. Diagnostic: dark imaging-room hero, wireframe body on a measuring grid, mono numbers.
page(2, "Diagnostic", "family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600",
"""body{font-family:'IBM Plex Sans',system-ui,sans-serif;color:#e6edf3;background:#0a1320}
.notice{background:#07101b;color:#8fa3b8;font-size:13px;border-bottom:1px solid #1b2a3c}.notice a{color:#5eead4}
.top{border-bottom:1px solid #1b2a3c}.brand{font-weight:700;font-size:19px;color:#fff}.nav a{color:#c4d1de;font-size:15px}
.btn{border-radius:4px;font-size:15px}.btn-ink{background:#5eead4;color:#06201c}.btn-line{border:1px solid #5eead4;color:#5eead4}
.hero{padding:36px 0 40px;background:radial-gradient(900px 500px at 50% 40%,#10233a 0,#0a1320 70%)}
.grid3{display:grid;grid-template-columns:1fr 360px 1fr;gap:32px;align-items:center}
h1{font-size:40px;line-height:1.1;letter-spacing:-.015em;margin:0 0 16px;font-weight:600;color:#fff}
.lede{font-size:16px;line-height:1.6;color:#9fb1c3;margin:0 0 22px}
.k{font:500 12px 'IBM Plex Mono',monospace;color:#5eead4;letter-spacing:.04em;margin:0 0 10px}
.scan{position:relative;border:1px solid #1d3550;border-radius:6px;padding:10px;background-image:linear-gradient(#13263b 1px,transparent 1px),linear-gradient(90deg,#13263b 1px,transparent 1px);background-size:20px 20px}
.scan::after{content:"";position:absolute;left:10px;right:10px;top:10px;height:2px;background:#5eead4;opacity:.55;box-shadow:0 0 12px #5eead4;animation:scan 2.4s ease-in-out 1 forwards}
@keyframes scan{from{transform:translateY(0)}to{transform:translateY(440px);opacity:0}}
.corner{position:absolute;width:14px;height:14px;border-color:#5eead4;border-style:solid}.c1{left:-1px;top:-1px;border-width:2px 0 0 2px}.c2{right:-1px;top:-1px;border-width:2px 2px 0 0}.c3{left:-1px;bottom:-1px;border-width:0 0 2px 2px}.c4{right:-1px;bottom:-1px;border-width:0 2px 2px 0}
.fig{height:450px;margin:0 auto}.fig .body{fill:#0f2236}.contour{fill:none;stroke:#5eead4;stroke-width:1;stroke-opacity:.8}
.region{fill:#5eead4;fill-opacity:0}.region.hov{fill-opacity:.2}.region.on{fill-opacity:.38}
.pin-ring{fill:none;stroke:#5eead4;stroke-width:1.2}.pin-dot{fill:#5eead4}.pin.on .pin-ring{stroke:#fff;stroke-width:2}.pin.on .pin-dot{fill:#fff}
.goals button{padding:9px 0;border-bottom:1px solid #1b2a3c;font-size:15px;color:#c4d1de}.goals button:hover,.goals button.on{color:#fff}
.goals button.on .gl-name::before{content:"";display:inline-block;width:8px;height:8px;background:#5eead4;margin-right:10px;border-radius:50%}
.gl-c{font:400 12px 'IBM Plex Mono',monospace;color:#6f8499}
.panel{border:1px solid #1d3550;border-radius:6px;padding:20px;background:#0c1a2b}
.p-k{margin:0;font:500 12px 'IBM Plex Mono',monospace;color:#5eead4}.p-h{margin:4px 0 12px;font-size:20px;font-weight:600;color:#fff}
.p-price{display:flex;align-items:baseline;gap:6px}.p-num{font:600 58px/1 'IBM Plex Mono',monospace;color:#fff;letter-spacing:-.04em}.p-unit{color:#8fa3b8;font-family:'IBM Plex Mono',monospace}
.p-what{margin:8px 0 12px;font-size:14px;color:#c4d1de}.p-sub{font:12px 'IBM Plex Mono',monospace;color:#6f8499;margin-top:4px}
.p-none{font-size:14px;color:#c4d1de;border-left:2px solid #5eead4;padding-left:10px}.p-intro{font-size:13px;color:#8fa3b8;line-height:1.55}
.p-list li{padding:8px 0;border-top:1px solid #1b2a3c;font-size:13px;color:#e6edf3}.p-btns{margin-top:14px}.p-btns .btn{min-height:40px;font-size:14px}
.chip{font:500 11px 'IBM Plex Mono',monospace;padding:3px 7px;border-radius:3px;border:1px solid}.chip-ok{color:#5eead4;border-color:#1f6b60}.chip-info{color:#93c5fd;border-color:#2a4a78}.chip-warn{color:#fdba74;border-color:#7a4a1f}.chip-neutral{color:#94a3b8;border-color:#334155}
@media (max-width:1100px){.grid3{grid-template-columns:1fr 1fr}.grid3>.col-fig{grid-row:span 2}}
@media (max-width:640px){.grid3{grid-template-columns:1fr}.fig{height:300px}h1{font-size:30px}.p-num{font-size:48px}}""",
fill("""{{NOTICE}}{{NAV}}<main class="hero"><div class="wrap grid3">
<div><p class="k">Peptide check, by body area</p><h1>{{H1}}</h1><p class="lede">{{LEDE}}</p>{{LIST}}</div>
<div class="col-fig"><div class="scan"><span class="corner c1"></span><span class="corner c2"></span><span class="corner c3"></span><span class="corner c4"></span>{{FIG}}</div></div>
<div id="panel" class="panel" aria-live="polite"></div>
</div></main>""", FIG=figure("outline"), LIST=goal_list()))

# 3. Medical textbook: journal paper and serif, the body as a labelled plate (Fig. 1) with leader lines.
page(3, "Medical textbook", "family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&family=Atkinson+Hyperlegible:wght@400;700",
"""body{font-family:'Atkinson Hyperlegible',system-ui,sans-serif;color:#161e28;background:#f8f6f1}
.notice{background:#efece4;color:#4a5361;font-size:14px;border-bottom:1px solid #ddd8cc}.notice a{color:#0b6a45}
.top{border-bottom:2px solid #161e28}.brand{font-weight:800;font-size:20px;color:#161e28}.nav a{color:#161e28;font-weight:700;font-size:15px}
.btn{border-radius:3px;font-size:15px}.btn-ink{background:#161e28;color:#f8f6f1}.btn-line{border:2px solid #161e28;color:#161e28}
.hero{padding:36px 0 44px}.cols{display:grid;grid-template-columns:5fr 7fr;gap:48px;align-items:start}
h1{font:600 46px/1.05 Newsreader,Georgia,serif;letter-spacing:-.015em;margin:0 0 16px}
.lede{font-size:17px;line-height:1.55;color:#4a5361;margin:0 0 22px}
.plate{border-top:2px solid #161e28;border-bottom:1px solid #ddd8cc;padding:14px 0 8px}
.plate-cap{display:flex;justify-content:space-between;font-size:13px;color:#4a5361;margin-bottom:4px}.plate-cap i{font:italic 500 16px Newsreader,serif;color:#161e28}
.fig{width:100%;height:auto;max-height:470px}.fig .body{fill:url(#hatch)}.contour{fill:none;stroke:#161e28;stroke-width:1.2}
.region{fill:#f5dc5c;fill-opacity:0}.region.hov{fill-opacity:.5}.region.on{fill-opacity:.85}
.leader{stroke:#7a7466;stroke-width:.8}.lbl text{font:500 15px Newsreader,serif;fill:#161e28}.lbl.on text{font-weight:600;text-decoration:underline;text-decoration-color:#f5dc5c;text-decoration-thickness:4px}
.lbl.on .leader,.lbl.hov .leader{stroke:#161e28;stroke-width:1.4}
.pin-ring{fill:#f8f6f1;stroke:#161e28;stroke-width:1.2}.pin-dot{fill:#161e28}.pin.on .pin-ring{fill:#f5dc5c}
.panel{background:#fff;border:2px solid #161e28;border-radius:3px;padding:20px 22px}
.p-k{margin:0;font-size:13px;color:#4a5361}.p-h{margin:2px 0 10px;font:600 26px/1.1 Newsreader,serif;padding-bottom:10px;border-bottom:4px double #161e28}
.p-price{display:flex;align-items:baseline;gap:6px}.p-num{font:600 64px/1 Newsreader,serif;letter-spacing:-.02em;background:linear-gradient(transparent 82%,#f5dc5c 82%)}.p-unit{color:#4a5361;font-size:18px}
.p-what{margin:10px 0;font-size:15px}.p-sub{font-size:13px;color:#4a5361;margin-top:2px}.p-none{font-size:15px}.p-intro{font-size:14px;color:#4a5361;line-height:1.5}
.p-list li{padding:8px 0;border-top:1px solid #ddd8cc;font-size:14px;font-weight:700}.p-btns{margin-top:14px}
.chip{font-size:12px;font-weight:700;padding:3px 8px;border-radius:2px}.chip-ok{background:#e3f0e8;color:#08502f}.chip-info{background:#e5ebf3;color:#27457f}.chip-warn{background:#f9eddc;color:#7d3a06}.chip-neutral{background:#ebe8e0;color:#4a5361}
.goals{display:none}
@media (max-width:1000px){.cols{grid-template-columns:1fr}}
@media (max-width:640px){h1{font-size:32px}.p-num{font-size:52px}}""",
fill("""{{NOTICE}}{{NAV}}<main class="hero"><div class="wrap cols">
<div><h1>{{H1}}</h1><p class="lede">{{LEDE}}</p><div id="panel" class="panel" aria-live="polite"></div></div>
<figure class="plate" style="margin:0"><div class="plate-cap"><i>Fig. 1</i><span>Choose an area. Status and prices checked {{CHECKED}}.</span></div>{{FIG}}</figure>
</div></main>""", FIG=figure("outline", labels=True, extra='<pattern id="hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="5" height="5" fill="#f3f0e8"/><line x1="0" y1="0" x2="0" y2="5" stroke="#d9d3c4" stroke-width="1"/></pattern>'), LIST=""))

# 4. Calm telehealth: soft white and sage, rounded cards, goal tabs over a soft body.
page(4, "Calm telehealth", "family=Plus+Jakarta+Sans:wght@400;500;600;700;800",
"""body{font-family:'Plus Jakarta Sans',system-ui,sans-serif;color:#1c2b27;background:#fbfcfa}
.notice{background:#eef4f0;color:#4b5f58;font-size:14px}.notice a{color:#1f6f52}
.brand{font-weight:800;font-size:20px;color:#1c2b27}.nav a{color:#1c2b27;font-weight:600;font-size:15px}
.btn{border-radius:999px;font-size:15px}.btn-ink{background:#1c2b27;color:#fff}.btn-line{border:1.5px solid #1c2b27;color:#1c2b27}
.hero{padding:18px 0 40px}.head{text-align:center;max-width:820px;margin:0 auto 20px}
h1{font-size:42px;line-height:1.08;letter-spacing:-.025em;margin:0 0 12px;font-weight:800}
.lede{font-size:17px;line-height:1.55;color:#4b5f58;margin:0}
.card{background:#fff;border-radius:24px;padding:22px;box-shadow:0 1px 2px rgba(28,43,39,.05),0 12px 40px rgba(28,43,39,.06);display:grid;grid-template-columns:1fr 1.1fr;gap:24px;align-items:center}
.card>*{min-width:0}.tabs{grid-column:1/-1;min-width:0}.tabs .goals{display:flex;flex-wrap:wrap;gap:8px;justify-content:center}
.tabs .goals button{border:1.5px solid #dfe8e3;border-radius:999px;padding:9px 16px;font-weight:600;font-size:14px;background:#fff}
.tabs .goals button:hover{border-color:#9cc5b1}.tabs .goals button.on{background:#1f6f52;border-color:#1f6f52;color:#fff}.tabs .gl-c{display:none}
.figbox{background:#f1f6f3;border-radius:18px;padding:14px;display:flex;justify-content:center}
.fig{height:370px}.fig .body{fill:#dbe8e1}.contour{fill:none;stroke:#b5cbbf;stroke-width:1}
.region{fill:#1f6f52;fill-opacity:0;filter:url(#soft)}.region.hov{fill-opacity:.25}.region.on{fill-opacity:.5}
.pin-ring{fill:#fff;stroke:#1f6f52;stroke-width:2}.pin-dot{fill:#1f6f52}.pin.on .pin-ring{fill:#1f6f52;stroke:#fff}.pin.on .pin-dot{fill:#fff}
.pin.on .pin-ring{animation:pulse 1.2s ease-out 2}@keyframes pulse{0%{stroke-width:2}50%{stroke-width:9;stroke-opacity:.4}100%{stroke-width:2}}
.panel{padding:6px 8px}.p-k{display:inline-block;margin:0 0 8px;font-size:12px;font-weight:700;color:#1f6f52;background:#e3f1ea;padding:4px 10px;border-radius:999px}
.p-h{margin:0 0 8px;font-size:24px;letter-spacing:-.02em}.p-price{display:flex;align-items:baseline;gap:4px;background:#f6faf7;border-radius:14px;padding:10px 16px}
.p-num{font-size:52px;font-weight:800;letter-spacing:-.03em;line-height:1}.p-unit{color:#4b5f58}.p-what{margin:10px 0;font-size:15px}.p-sub{font-size:13px;color:#6b7f78;margin-top:2px}
.p-none{background:#f6faf7;border-radius:14px;padding:14px 16px;font-size:15px}.p-intro{font-size:14px;color:#4b5f58;line-height:1.55}
.p-list li{padding:7px 0;border-top:1px solid #edf2ef;font-size:14px;font-weight:600}.p-btns{margin-top:14px}
.chip{font-size:12px;font-weight:700;padding:4px 10px;border-radius:999px}.chip-ok{background:#e3f1ea;color:#1a5c44}.chip-info{background:#e7eefa;color:#2b4e8e}.chip-warn{background:#fcefdf;color:#8a3e05}.chip-neutral{background:#eff2f0;color:#4b5f58}
@media (max-width:900px){.card{grid-template-columns:1fr}}
@media (max-width:640px){h1{font-size:32px}.card{padding:14px;border-radius:18px}.fig{height:280px}.tabs .goals{justify-content:flex-start;flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none}.tabs .goals button{white-space:nowrap}.p-num{font-size:46px}}""",
fill("""{{NOTICE}}{{NAV}}<main class="hero"><div class="wrap">
<div class="head"><h1>{{H1}}</h1><p class="lede">{{LEDE}}</p></div>
<section class="card" aria-label="Choose a goal"><div class="tabs">{{LIST}}</div><div class="figbox">{{FIG}}</div><div id="panel" class="panel" aria-live="polite"></div></section>
</div></main>""", FIG=figure("outline", extra='<filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="5"/></filter>'), LIST=goal_list()))

# 5. Swiss pharma: strict grid, big type, numbered index, geometric pictogram, one signal colour.
page(5, "Swiss pharma", "family=Inter+Tight:wght@500;600;700;800&family=Inter:wght@400;500;600",
"""body{font-family:Inter,system-ui,sans-serif;color:#111;background:#fff}
.notice{background:#111;color:#bbb;font-size:13px}.notice a{color:#fff}
.top{border-bottom:1px solid #111}.brand{font:800 20px 'Inter Tight',sans-serif;color:#111}.nav a{color:#111;font-weight:500;font-size:15px}
.btn{border-radius:0;font-size:15px}.btn-ink{background:#e5432a;color:#fff}.btn-line{border:1.5px solid #111;color:#111}
.hero{padding:0}.sw{display:grid;grid-template-columns:5fr 3fr 4fr;border-bottom:1px solid #111}
.sw>div{padding:32px 28px 28px;border-right:1px solid #111}.sw>div:last-child{border-right:0}.sw>div:first-child{padding-left:0}
h1{font:800 52px/0.98 'Inter Tight',sans-serif;letter-spacing:-.035em;margin:0 0 18px}
.lede{font-size:16px;line-height:1.55;color:#444;margin:0 0 22px;max-width:44ch}
.goals li{border-top:1px solid #111}.goals li:last-child{border-bottom:1px solid #111}.goals button{padding:10px 0;font:600 17px 'Inter Tight',sans-serif}
.gl-n{font:500 13px Inter,sans-serif;width:28px;color:#888}.goals button.on{color:#e5432a}.goals button.on .gl-n{color:#e5432a}.goals button:hover .gl-name{text-decoration:underline}
.gl-c{font:400 13px Inter,sans-serif;color:#888}
.fig{height:470px;margin:0 auto}.fig .body{fill:#111}
.region{fill:#e5432a;fill-opacity:0}.region.hov{fill-opacity:.6}.region.on{fill-opacity:1}
.pin-ring{fill:#fff;stroke:#111;stroke-width:1.5}.pin-dot{display:none}.pin-n{font:700 10px Inter,sans-serif;fill:#111}.pin.on .pin-ring{fill:#e5432a;stroke:#fff}.pin.on .pin-n{fill:#fff}
.panel{}.p-k{margin:0 0 4px;font-size:13px;color:#888}.p-h{margin:0 0 16px;font:700 26px/1.05 'Inter Tight',sans-serif;letter-spacing:-.02em}
.p-price{display:flex;align-items:baseline;gap:4px;border-top:6px solid #111;padding-top:8px}.p-num{font:800 96px/0.9 'Inter Tight',sans-serif;letter-spacing:-.05em}.p-unit{font-size:20px;color:#888}
.p-what{margin:12px 0;font-size:15px}.p-sub{font-size:13px;color:#888;margin-top:4px}.p-none{border-top:6px solid #111;padding-top:12px;font-size:15px}.p-intro{font-size:14px;color:#444;line-height:1.5}
.p-list li{padding:8px 0;border-top:1px solid #ddd;font-size:14px;font-weight:600}.p-btns{margin-top:16px}
.chip{font-size:12px;font-weight:600;padding:2px 0;border-bottom:2px solid}.chip-ok{color:#0a7a3e}.chip-info{color:#1f4fa3}.chip-warn{color:#b4540a}.chip-neutral{color:#888}
@media (max-width:1100px){.sw{grid-template-columns:1fr 1fr}.sw>div:last-child{grid-column:1/-1;border-top:1px solid #111;padding-left:0}}
@media (max-width:640px){.sw{grid-template-columns:1fr}.sw>div{padding:20px 0;border-right:0;border-bottom:1px solid #111}h1{font-size:38px}.fig{height:300px}.p-num{font-size:72px}}""",
fill("""{{NOTICE}}{{NAV}}<main class="hero"><div class="wrap sw">
<div><h1>{{H1}}</h1><p class="lede">{{LEDE}}</p>{{LIST}}</div>
<div>{{FIG}}</div>
<div id="panel" class="panel" aria-live="polite"></div>
</div></main>""", FIG=figure("pictogram", numbers=True), LIST=goal_list(numbers=True)))

OPTIONS = [(1, "Clinic intake", "White clinical chart. The body picks the goal; the prescription pad answers."),
           (2, "Diagnostic", "Dark imaging-room hero, wireframe body on a measuring grid, mono numbers."),
           (3, "Medical textbook", "Journal paper and serif; the body as a labelled plate with leader lines."),
           (4, "Calm telehealth", "Soft white and sage, rounded cards, goal tabs over a soft body."),
           (5, "Swiss pharma", "Strict grid, big type, numbered index, geometric pictogram, one signal colour.")]
(OUT / "index.html").write_text("<!doctype html><meta charset='utf-8'><title>Home look options</title><style>body{font:16px/1.5 system-ui;margin:40px;max-width:720px}li{margin:10px 0}</style><h1>Home page: five look options</h1><ol>"
                                + "".join(f"<li><a href='option-{n}.html'>{t}</a>: {d}</li>" for n, t, d in OPTIONS) + "</ol>", encoding="utf-8")
print("wrote", len(OPTIONS), "options")
