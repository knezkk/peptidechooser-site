"""The paid link plumbing (owner task 4 Nov 2026; pages.md, Paid link redirect page): the /out/<slug>/ pages and the
/disclosure/ list of networks. Tracking addresses live only in data/paid.json (tools/pull_data.py) and in the /out/ pages,
never in site.json or another page. Until the data side has the views, the small fixture stands in for data/paid.json.
"""
import json
import os
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIVE = ROOT / "data" / "paid.json"
FIXTURE = ROOT / "tools" / "fixtures" / "paid.json"

# The address parameter that carries the click source, per network; FirstPromoter has none.
CLICK_PARAM = {"katalys": "aff_sub", "awin": "clickref", "cj": "sid"}
CLICK_SOURCE_MAX = 50  # the shortest limit we know of (Awin's clickref); a longer path is cut, never dropped

# One plain line per network on /disclosure/ (Tier 1). A network without a line here shows its name alone.
NETWORKS = {
    "katalys": ("Katalys", "Katalys: paid links through this network pass through track.revoffers.com."),
    "awin": ("Awin", "Awin: paid links through this network pass through awin1.com."),
    "cj": ("CJ", "CJ: paid links through this network pass through anrdoezrs.net."),
    "firstpromoter": ("FirstPromoter", "FirstPromoter: paid links through this service go to the brand's own site with our code in the address."),
}


def load():
    """{"redirects": [...], "copy_rules": [...], "networks": [...]}; PAID_JSON points at another file (a local test)."""
    src = Path(os.environ["PAID_JSON"]) if os.environ.get("PAID_JSON") else LIVE if LIVE.exists() else FIXTURE
    return json.loads(src.read_text(encoding="utf-8"))


def out_dir(out_path):
    """/out/shedrx/ -> out/shedrx"""
    return out_path.strip("/")


def out_page(name, tracking_url, network):
    """The redirect page: no analytics, no fonts, no styles. The script runs first and adds the click source (the path of
    the page on our site that sent the click, nothing else); the meta refresh and the link work without JavaScript."""
    url = json.dumps(tracking_url).replace("</", "<\\/")
    param = json.dumps(CLICK_PARAM.get(network.lower(), ""))
    href = escape(tracking_url, quote=True)
    label = escape(name)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Continue to {label}</title>
<meta name="robots" content="noindex,nofollow"><meta name="viewport" content="width=device-width,initial-scale=1">
<script>(function(){{var u={url},k={param},p="";try{{var r=new URL(document.referrer);if(r.host===location.host)p=r.pathname}}catch(e){{}}
if(k&&p){{var s=k+"="+encodeURIComponent(p.slice(0,{CLICK_SOURCE_MAX})),i=u.indexOf("&ued=");u=i<0?u+(u.indexOf("?")<0?"?":"&")+s:u.slice(0,i+1)+s+u.slice(i)}}
location.replace(u)}})();</script>
<meta http-equiv="refresh" content="0;url={href}"></head>
<body><p><a href="{href}" rel="sponsored nofollow">Continue to {label}</a></p></body></html>
"""


def write_out_pages(dist, names):
    """One page per redirect row. `names` maps a seller slug to the name our pages use; a row's own `name` covers a brand
    we have no profile for."""
    for r in load()["redirects"]:
        name = names.get(r["seller_slug"]) or r.get("name") or r["seller_slug"].replace("-", " ").title()
        target = dist / out_dir(r["out_path"]) / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(out_page(name, r["tracking_url"], r["network"]), encoding="utf-8")


def networks_block():
    """The /disclosure/ sentence and list: the networks we hold an approved account with, from the data."""
    d = load()
    keys = sorted({n.lower() for n in d.get("networks") or []} | {r["network"].lower() for r in d["redirects"]},
                  key=lambda k: (list(NETWORKS).index(k) if k in NETWORKS else len(NETWORKS), k))
    if not keys:
        return "<p>We may take part in affiliate programs run by individual brands and by affiliate networks. We will list the networks we work with on this page as those relationships start.</p>"
    lines = "".join(f"<li>{NETWORKS[k][1] if k in NETWORKS else escape(k)}</li>" for k in keys)
    return ("<p>We may take part in affiliate programs run by individual brands and by affiliate networks. "
            f"These are the networks where we have an approved account:</p>\n<ul>{lines}</ul>")
