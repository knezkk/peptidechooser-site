"""The paid link plumbing (owner task 4 Nov 2026; pages.md, Paid link redirect page): the /out/<slug>/ pages and the
/disclosure/ list of networks. Tracking addresses live only in data/paid.json (tools/pull_data.py) and in the /out/ pages,
never in site.json or another page. Until the data side has the views, the small fixture stands in for data/paid.json.
"""
import json
import os
import re
import time
import urllib.error
import urllib.request
from html import escape
from pathlib import Path
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

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
    # a brand's own program, no network (queue block 55, point 10g: /disclosure/ printed the raw "in_house")
    "in_house": ("In-house", "In-house: paid links through a brand's own program go straight to the brand's site."),
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


# Plan deep links (owner, queue block 44, 18 Nov 2026): a Visit button on a plan row lands on the plan's own page (its
# pricing_url, the page we read the price from), through the network, by that network's own deep link way only:
#  - Awin: &ued=<encoded target> on the tracking address;
#  - FirstPromoter: the fpr code on the target page itself;
#  - Katalys (RevOffers, HasOffers): &url=<encoded target>, only for an offer listed here after its offer page was seen to
#    allow deep links (offer id -> the day it was checked). Empty: no offer is confirmed yet, so they keep the home page;
#  - CJ and any other network: no deep link yet, the home page.
KATALYS_DEEP = {}
DEEP_SLUG_MAX = 60


def bare_host(url):
    """getcurex.com for https://www.getcurex.com/cl/glp; "" for no host."""
    h = (urlsplit(url).hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


def deep_target_ok(target, domain):
    """Rule 3 of block 44: https, on the seller's own domain (the host of its record, www. aside), and not its home page."""
    if not target or not domain:
        return False
    s = urlsplit(target)
    own = bare_host(domain if "//" in domain else f"https://{domain}")
    return s.scheme == "https" and bool(own) and bare_host(target) == own and (s.path.strip("/") != "" or bool(s.query))


def deep_url(redirect, target):
    """The tracking address that lands on `target`, by the redirect's network's own deep link way, or None."""
    net, url = redirect["network"].lower(), redirect["tracking_url"]
    query = dict(parse_qsl(urlsplit(url).query))
    if net == "awin":
        return None if "ued=" in url else f"{url}&ued={quote(target, safe='')}"
    if net == "firstpromoter":
        if not query.get("fpr"):
            return None
        s = urlsplit(target)
        q = [(k, v) for k, v in parse_qsl(s.query) if k != "fpr"] + [("fpr", query["fpr"])]
        return urlunsplit((s.scheme, s.netloc, s.path, urlencode(q), ""))
    if net == "katalys":
        return f"{url}&url={quote(target, safe='')}" if query.get("offer_id") in KATALYS_DEEP else None
    return None


def deep_slug(target):
    """The /out/<seller>/<slug>/ name of a target: its path, lowercase, words joined by hyphens."""
    s = re.sub(r"[^a-z0-9]+", "-", urlsplit(target).path.lower()).strip("-")
    return s[:DEEP_SLUG_MAX].strip("-") or "page"


def deep_links(plans, profiles, redirects=None):
    """{(seller_slug, plan_slug): {"out_path", "target", "url", "network"}} for every plan row whose clinic has a paid link
    and whose pricing_url passes deep_target_ok and the network's deep link way. One /out/ page per seller and target:
    plans that share a target share its page. A seller without a paid link, or a plan that fails a rule, is left out, so
    its button keeps /out/<seller>/."""
    by_out = {r["out_path"]: r for r in (load()["redirects"] if redirects is None else redirects)}
    pages, links = {}, {}
    for p in plans:
        prof = profiles.get(p.get("seller_slug")) or {}
        red = by_out.get(prof.get("paid_url") or "")
        target = p.get("pricing_url")
        if not red or not p.get("plan_slug") or not deep_target_ok(target, prof.get("domain")):
            continue
        url = deep_url(red, target)
        if not url:
            continue
        seller = out_dir(red["out_path"])
        used = {v["target"]: k for k, v in pages.items() if k.startswith(f"/{seller}/")}
        out = used.get(target)
        if not out:
            base, n = f"/{seller}/{deep_slug(target)}", 1
            out = f"{base}/"
            while out in pages:
                n += 1
                out = f"{base}-{n}/"
            pages[out] = {"out_path": out, "target": target, "url": url, "network": red["network"], "seller_slug": red["seller_slug"]}
        links[(p["seller_slug"], p["plan_slug"])] = pages[out]
    return links


def target_problem(target, opener=None):
    """Rule 4 of block 44: one polite request (our deploy user agent, no login, no cookies); None when the page answers on
    its own host, else why not ("404", "redirects to other.com", "timeout")."""
    req = urllib.request.Request(target, headers={"User-Agent": "peptidechooser-deploy"})
    try:
        with (opener or urllib.request.urlopen)(req, timeout=20) as r:
            final = r.geturl()
        return None if bare_host(final) == bare_host(target) else f"redirects to {bare_host(final) or final}"
    except urllib.error.HTTPError as e:
        return str(e.code)
    except Exception as e:  # a timeout, a refused connection, a bad certificate: the home page is the safe place
        return type(e).__name__


def checked_deep_links(links, problem=target_problem, pause=1.0):
    """The links whose target answers; each target is asked once. Returns (kept links, [(out_path, target, why)])."""
    seen, dropped = {}, []
    for v in {v["out_path"]: v for v in links.values()}.values():
        if seen:
            time.sleep(pause)
        seen[v["target"]] = problem(v["target"])
        if seen[v["target"]]:
            dropped.append((v["out_path"], v["target"], seen[v["target"]]))
    return {k: v for k, v in links.items() if not seen.get(v["target"])}, dropped


def write_out_pages(dist, names, deep=None):
    """One page per redirect row, and one per plan deep link (`deep`, from deep_links). `names` maps a seller slug to the
    name our pages use; a row's own `name` covers a brand we have no profile for."""
    for r in load()["redirects"]:
        # the /out/ path is the short name; the seller slug can carry a legal name (eden-eden-health-international-inc)
        name = names.get(r["seller_slug"]) or r.get("name") or out_dir(r["out_path"]).split("/")[-1].replace("-", " ").title()
        target = dist / out_dir(r["out_path"]) / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(out_page(name, r["tracking_url"], r["network"]), encoding="utf-8")
    for v in {v["out_path"]: v for v in (deep or {}).values()}.values():
        name = names.get(v["seller_slug"]) or out_dir(v["out_path"]).split("/")[1].replace("-", " ").title()
        target = dist / out_dir(v["out_path"]) / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(out_page(name, v["url"], v["network"]), encoding="utf-8")


def networks_block():
    """The /disclosure/ sentence and list: the networks we hold an approved account with, from the data."""
    d = load()
    keys = sorted({n.lower() for n in d.get("networks") or []} | {r["network"].lower() for r in d["redirects"]},
                  key=lambda k: (list(NETWORKS).index(k) if k in NETWORKS else len(NETWORKS), k))
    if not keys:
        return "<p>We may take part in affiliate programs run by individual brands and by affiliate networks. We will list the networks we work with on this page as those relationships start.</p>"
    lines = "".join(f"<li>{NETWORKS[k][1] if k in NETWORKS else escape(k.replace('_', ' ').capitalize())}</li>" for k in keys)
    return ("<p>We may take part in affiliate programs run by individual brands and by affiliate networks. "
            f"These are the networks where we have an approved account:</p>\n<ul>{lines}</ul>")
