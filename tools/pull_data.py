"""Pull the numbers the site shows from the peptide-data database (rulebook 11.8: numbers from data, never typed).

Reads the `site.*` views through the read-only role (peptide-data spec 0015) and updates data/site.json:
  - site.catalog_counts  -> "db": options and sellers counted, newest price date
  - site.substance_status, site.approved_drugs -> "legal_db": status per substance with its source and date
  - site.plan_prices     -> "plans": telehealth plan prices per seller, with the date the page was last seen
                            and the seller's FDA warning letters (fda_letter_count, last_fda_letter_date)
  - site.products        -> "products": research-use listings for the substances the site shows (see keep_products)
  - site.sellers         -> "sellers": the seller rows those listings point to, with their background check and their
                            five-check score (score, score_* yes/no, score_checked_on)
  - site.fda_letters    -> "letters": the newest FDA warning letters to sellers in the database (see letters_rows)
  - site.fda_letters_all -> "letters_all": every peptide-related letter or letter to a seller we know, for /fda-warning-letters/
  - site.sellers, site.seller_profile, site.products -> "guide_stats": the counts the guides in guides.py quote (shops we
                            check, those with a lab report in the last 12 months, shops that list BPC-157)
  - site.paid_links      -> `paid_url` on seller_profiles; site.paid_redirects, site.seller_copy_rules -> data/paid.json
    (pull_paid), never site.json
  - site.letter_substances -> "letter_substances": the substances each FDA warning letter names, for /peptides/, the
    compare pairs and the letters page's substance filter
  - site.seller_profile, site.seller_substances, site.seller_letters -> "seller_profiles", "seller_substances" (top 12 per
    seller, see top_substances), "seller_letters": the seller pages /sellers/ and /sellers/<slug>/

Everything else in site.json (hand-checked prices with their sources, texts, goals) is left untouched.
Run before build.py:  SITE_DATABASE_URL=postgres://site_reader:...@host:5432/postgres python3 tools/pull_data.py
Without SITE_DATABASE_URL it exits 0 and changes nothing, so a local build never needs the database.
The address comes from the environment, or else from a `.env` file in the worktree (never committed).
"""
import json
import re
import os
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "site.json"
PAID = ROOT / "data" / "paid.json"


def database_url():
    """The environment wins; else the SITE_DATABASE_URL line of .env, read by hand (no dependency)."""
    if os.environ.get("SITE_DATABASE_URL"):
        return os.environ["SITE_DATABASE_URL"]
    env = ROOT / ".env"
    for line in env.read_text(encoding="utf-8").splitlines() if env.exists() else []:
        key, _, value = line.strip().removeprefix("export ").partition("=")
        if key.strip() == "SITE_DATABASE_URL":
            return value.strip().strip("'\"")
    return ""


URL = database_url()


def fetch(sql):
    import psycopg  # installed in CI only (requirements-data.txt)

    with psycopg.connect(URL, connect_timeout=10, options="-c statement_timeout=5000") as con:
        with con.cursor() as cur:
            cur.execute(sql)
            cols = [d.name for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]


def plain(v):
    if isinstance(v, (date, datetime)):
        return v.isoformat()[:10]
    if hasattr(v, "quantize"):  # Decimal
        return float(v)
    return v


def rows(sql):
    return [{k: plain(v) for k, v in r.items()} for r in fetch(sql)]


def optional_columns(view, *cols):
    """Columns the data side is still adding (peptide-data task 12): ", a, b" for those the view has, so a pull never breaks
    while they are missing."""
    have = {r["column_name"] for r in rows(
        f"select column_name from information_schema.columns where table_schema = 'site' and table_name = '{view}'")}
    return "".join(f", {c}" for c in cols if c in have)


def has_view(view):
    """A view the data side is still adding: a pull never breaks while it is missing."""
    return bool(rows(f"select 1 from information_schema.views where table_schema = 'site' and table_name = '{view}'"))


def add_paid_links(d):
    """A seller's `paid_url` is the /out/ path from site.paid_links, which applies the paid link rule (pages.md, Buttons)
    and never gives the tracking address. A cosmetic link belongs to one product, not to the seller's buttons."""
    if not has_view("paid_links"):
        return
    paid = {r["seller_slug"]: r["out_path"] for r in rows(
        "select seller_slug, out_path from site.paid_links where allowed_on <> 'cosmetic' order by active_from")}
    for r in d["seller_profiles"]:
        if r["seller_slug"] in paid:
            r["paid_url"] = paid[r["seller_slug"]]


def add_cosmetic_links(products):
    """A supplement shop's paid link belongs to one cosmetic product (decision D6a, owner decision 0a = B, 8 Nov 2026): the
    product row with that `product_id` gets `paid_url`, the /out/ path from site.paid_links (allowed_on 'cosmetic'), one link
    per product row, for /skin/ and /topical/. keep_products always keeps such a row. The view applies the paid link rule."""
    if not has_view("paid_links") or not products or "product_id" not in products[0]:
        return
    links = {r["cosmetic_product_id"]: r["out_path"] for r in rows(
        "select cosmetic_product_id, out_path from site.paid_links where allowed_on = 'cosmetic' "
        "and cosmetic_product_id is not null order by active_from")}
    for r in products:
        if r.get("product_id") in links:
            r["paid_url"] = links[r["product_id"]]
    print(f"pull_data: {sum(1 for r in products if r.get('paid_url'))} cosmetic products with a paid link")


def move_sellers(x, redirects):
    """Task 4C (owner task 23, 8 Nov 2026): every `seller_slug` and every /sellers/<old>/ in the data takes the seller's new
    page slug, so site.json, paid.json, the build and the checks all speak of the new address (build.py does the same for
    the repo data and writes the 301s). The seller_redirects rows themselves keep both slugs."""
    moves = {r["old_slug"]: r["new_slug"] for r in redirects if r.get("old_slug") and r.get("new_slug")}
    if not moves:
        return x
    def walk(v, key=None):
        if isinstance(v, dict):
            return {k: (w if k in ("old_slug", "new_slug") else walk(w, k)) for k, w in v.items()}
        if isinstance(v, list):
            return [walk(w) for w in v]
        if isinstance(v, str) and key == "seller_slug":
            return moves.get(v, v)
        if isinstance(v, str) and "/sellers/" in v:
            return re.sub(r"/sellers/([a-z0-9-]+)/", lambda m: f"/sellers/{moves.get(m.group(1), m.group(1))}/", v)
        return v
    return walk(x)


def add_history_and_labs(d):
    """Owner task 24 (9 Nov 2026; peptide-data spec 0025): the price history of the sizes and plans the site shows, the lab
    reports of its listings and the lab list. Each view is read only once it exists; until then the keys stay empty and the
    build is unchanged. The build draws them only with PC_ARCH_DATA=1."""
    ids = lambda key: ",".join(str(int(r[key])) for r in d["products"] if r.get(key) is not None) or "0"
    d["price_history"] = (rows(
        "select seller_slug, substance_slug, product_id, variant_id, price_usd, price_per_mg, observed_on, source_id "
        f"from site.price_history where variant_id in ({ids('variant_id')}) order by variant_id, observed_on")
        if has_view("price_history") and any(r.get("variant_id") is not None for r in d["products"]) else [])
    d["plan_price_history"] = (rows(
        "select seller_slug, plan_slug, price_monthly, membership_fee_monthly, observed_on, source_id, source_url "
        "from site.plan_price_history where price_monthly is not null order by seller_slug, plan_slug, observed_on")
        if has_view("plan_price_history") else [])
    d["coa_reports"] = (rows(
        "select seller_slug, substance_slug, product_id, lab_slug, lab_name, coa_date, source_id, source_url "
        f"from site.coa_reports where product_id in ({ids('product_id')}) order by product_id, coa_date desc")
        if has_view("coa_reports") else [])
    d["labs"] = rows("select * from site.labs order by lab_slug") if has_view("labs") else []
    print(f"pull_data: {len(d['price_history'])} size and {len(d['plan_price_history'])} plan price changes, "
          f"{len(d['coa_reports'])} lab reports, {len(d['labs'])} labs")


def pull_paid():
    """site.paid_redirects and site.seller_copy_rules (peptide-data task 13) into data/paid.json, the only data file that
    holds tracking addresses (paid.py). Until both views exist the file stays as it is and the build uses the fixture.
    The approved networks: site.affiliate_networks when the view exists; else the fixture's list, plus any network in use."""
    have = {r["table_name"] for r in rows("select table_name from information_schema.tables where table_schema = 'site'")}
    if not {"paid_redirects", "seller_copy_rules"} <= have:
        print("pull_data: site.paid_redirects or site.seller_copy_rules not there yet, the build uses the paid fixture")
        return
    redirects = rows("select out_path, seller_slug, network, tracking_url from site.paid_redirects order by out_path")
    if "affiliate_networks" in have:
        networks = [r["network"] for r in rows("select network from site.affiliate_networks order by network")]
    else:
        networks = json.loads((ROOT / "tools" / "fixtures" / "paid.json").read_text(encoding="utf-8"))["networks"]
    PAID.write_text(json.dumps({
        "networks": sorted(set(networks) | {r["network"] for r in redirects}),
        "redirects": redirects,
        "copy_rules": rows("select seller_slug, phrase, replace_with, note from site.seller_copy_rules order by seller_slug, phrase"),
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"pull_data: {len(redirects)} paid redirects")


def substances(d):
    """The substances the site shows: every option's `substance` or `substances` and every legal row's `substances`."""
    out = {p["substance"] for g in d["goals"] for p in g.get("peptides", []) if p.get("substance")}
    out |= {s for g in d["goals"] for p in g.get("peptides", []) for s in p.get("substances", [])}
    return out | {s for r in d["legal"]["rows"] for s in r.get("substances", [])}


# Cosmetic product forms (products.product_form): a cosmetic option's window lists only these (build.py COSMETIC_FORMS)
# "topical" too (owner answer, 3 Nov 2026: the database holds GHK-Cu, SNAP-8 and AHK-Cu listings as topical)
COSMETIC_FORMS = ("cream", "serum", "lotion", "gel", "topical")


def cosmetic_forms_line(all_rows, subs):
    """The deploy log's cosmetic listings per form (owner answer Q2 a, 4 Nov 2026): the total per form, then each substance's
    split, for the substances the site shows."""
    rows = [r for r in all_rows if r.get("form") in COSMETIC_FORMS and r["substance_slug"] in subs]
    if not rows:
        return "pull_data: cosmetic listings per form: none"
    count = lambda items: ", ".join(f"{f} {sum(r['form'] == f for r in items)}" for f in COSMETIC_FORMS if any(r["form"] == f for r in items))
    per_sub = "; ".join(f"{x}: {count([r for r in rows if r['substance_slug'] == x])}" for x in sorted({r["substance_slug"] for r in rows}))
    return f"pull_data: cosmetic listings per form: {count(rows)} ({per_sub})"


def keep_products(all_rows, subs, n=10):
    """site.json stays small: per substance, each seller's cheapest listing, then the n cheapest of those by price per mg
    (listings with a price per mg first, then blends and listings without one, by price), so the seller window
    shows one row per seller (owner, 31 Oct 2026). Cosmetic forms and the rest are picked apart, n each, so a serum
    is never pushed out by cheaper vials (owner UX audit, 3 Nov 2026)."""
    key = lambda r: (r["price_per_mg"] is None, r["price_per_mg"] or 0, r["price_usd"] is None, r["price_usd"] or 0, r["seller_slug"])
    out = []
    for slug in sorted(subs):
        for cosmetic in (False, True):
            best = {}
            for r in sorted((r for r in all_rows if r["substance_slug"] == slug and (r.get("form") in COSMETIC_FORMS) == cosmetic), key=key):
                best.setdefault(r["seller_slug"], r)
            out += sorted(best.values(), key=key)[:n]
    # a cosmetic product with its own paid link stays, so its link reaches the page (add_cosmetic_links)
    return out + [r for r in all_rows if r.get("paid_url") and r["substance_slug"] in subs and not any(r is x for x in out)]


def letters_rows(n=8):
    """The newest FDA warning letters, at most n, one row per letter and seller: letters matched to a seller by domain or
    address (a name-only match is left out), newest first, from site.fda_letters (owner, 1 Nov 2026)."""
    return rows(
        "select distinct seller_slug, seller_name, letter_date, letter_url, letter_subject, issuing_office, letter_reference, "
        "source_id from site.fda_letters where match_kind = 'domain_or_address' "
        f"order by letter_date desc nulls last, seller_name limit {int(n)}")


def letters_all_rows():
    """Every FDA warning letter the letters page lists (owner, 1 Nov 2026): letters marked peptide_related or matched to a
    seller in the database, newest first, from site.fda_letters_all."""
    return rows(
        "select letter_date, letter_url, company_name, letter_subject, issuing_office, letter_reference, seller_slug, "
        "seller_name, seller_kind, match_kind, peptide_related"
        + optional_columns("fda_letters_all", "closed_on", "closeout_url") +
        " from site.fda_letters_all "
        "where peptide_related or seller_slug is not null order by letter_date desc nulls last, company_name")


def top_substances(all_rows, n=12):
    """site.json stays small: per seller, its n substances with the most listings (ties by slug), for the seller pages
    (owner task, phase 4d, 2 Nov 2026)."""
    out, per = [], {}
    for r in sorted(all_rows, key=lambda r: (r["seller_slug"], -(r["listing_count"] or 0), r["substance_slug"])):
        per[r["seller_slug"]] = per.get(r["seller_slug"], 0) + 1
        if per[r["seller_slug"]] <= n:
            out.append(r)
    return out


def guide_stats():
    """The counts the guides quote (guides.py; owner task 2 Nov 2026), with the day they were counted. site.json keeps only
    ten listings per substance, so these cannot be counted from its rows."""
    r = rows(
        # shops only (product_count > 0): since peptide-data decision 26 the online clinics are site.sellers rows too
        "select (select count(*) from site.sellers where product_count > 0) as sellers, "
        "(select count(*) from site.seller_profile where product_count > 0 "
        "and newest_coa_date >= current_date - interval '12 months') as sellers_coa_12m, "
        "(select count(distinct seller_slug) from site.products where substance_slug = 'bpc-157') as bpc_sellers")[0]
    # per substance the guides name (hair, muscle, recovery, skin, libido, longevity, buying): shops that list it and the middle price per mg across all of them (owner task
    # 2 Nov 2026, guides 7 to 9); site.json's ten listings per substance cannot give either
    # and, for the BPC-157 price guide (owner task 2 Nov 2026, feat/learn-5), the lowest and highest price per mg inside the
    # band /compare/ uses ($0.01 to $100 per mg), so one mislabeled listing does not set the range
    r["substances"] = {x["substance_slug"]: {"shops": x["shops"], "ppm_median": x["ppm_median"], "ppm_min": x["ppm_min"],
                                             "ppm_max": x["ppm_max"]} for x in rows(
        "select substance_slug, count(distinct seller_slug) as shops, "
        "round((percentile_cont(0.5) within group (order by price_per_mg))::numeric, 2) as ppm_median, "
        "min(price_per_mg) filter (where price_per_mg between 0.01 and 100) as ppm_min, "
        "max(price_per_mg) filter (where price_per_mg between 0.01 and 100) as ppm_max "
        "from site.products where substance_slug in ('bpc-157', 'ghk-cu', 'tb-500', 'cjc-1295', 'ipamorelin', 'sermorelin', "
        "'tesamorelin', 'palmitoyl-pentapeptide-4', 'acetyl-hexapeptide-8', 'bremelanotide', 'melanotan-2', 'epitalon', "
        "'mots-c', 'nad-plus', 'semaglutide') group by substance_slug")}
    r["checked_on"] = date.today().isoformat()
    return r


def main():
    if not URL:
        print("pull_data: SITE_DATABASE_URL not set, site.json left as it is")
        return 0
    d = json.loads(DATA.read_text(encoding="utf-8"))
    d["db"] = rows("select * from site.catalog_counts")[0]
    # fda_listing (the FDA's own wording, e.g. "GHK-Cu (except for injectable routes of administration)") is read once the
    # data side adds the column; the site shows it when present and nothing when not (owner task 2 Nov 2026)
    listing = rows("select count(*) as n from information_schema.columns where table_schema = 'site' "
                   "and table_name = 'substance_status' and column_name = 'fda_listing'")[0]["n"]
    d["legal_db"] = rows(
        "select substance_slug, canonical_name, is_peptide, regime, status_value, scope, valid_from, "
        f"first_seen_by_us, source_id, source_url{', fda_listing' if listing else ''} from site.substance_status "
        "order by substance_slug, regime")
    d["approved_db"] = rows(
        "select substance_slug, brand_name, application_no, sponsor, approval_date, route, indications "
        "from site.approved_drugs order by substance_slug, approval_date")
    d["plans"] = rows(
        "select seller_slug, seller_name, plan_slug, plan_name, product_kind, dosage_form, substance_slug, "
        "pharmacy_partner, price_monthly, price_first_month, membership_fee_monthly, consult_fee, "
        "commitment_months, observed_at, last_seen, pricing_url, fda_letter_count, last_fda_letter_date"
        # spec 0023 (task 22, 8 Nov 2026): a per-order price, read once the data side has migrated it; substance_slugs: every
        # medicine a plan covers (decision 0d, owner 8 Nov 2026)
        f"{optional_columns('plan_prices', 'price_per_order', 'order_quantity', 'order_supply_days', 'fee_per_order', 'substance_slugs')} "
        "from site.plan_prices order by seller_slug, plan_slug")
    products = rows(
        "select seller_slug, seller_name, seller_status, product_name, variant_title, product_url, substance_slug, is_blend, "
        "amount_mg, form, price_usd, price_per_mg, price_observed_at, first_seen, last_seen, has_coa, coa_count"
        f"{optional_columns('products', 'product_id', 'variant_id')} from site.products")
    add_cosmetic_links(products)
    d["products"] = keep_products(products, substances(d))
    used = {r["seller_slug"] for r in d["products"]}
    sellers = rows(
        "select seller_slug, seller_name, domain, seller_kind, legal_entity_name, registry_state, legal_entity_source_url, "
        "fda_letter_count, last_fda_letter_date, coa_count, product_count, price_updated_at, first_seen, last_seen, "
        "score, score_lab_testing, score_no_fda_letter, score_registered_company, score_legal_pages, score_fresh_prices, "
        "score_checked_on from site.sellers order by seller_slug")
    d["sellers"] = [r for r in sellers if r["seller_slug"] in used]
    d["letters"] = letters_rows()
    # the line under the letters table: how many letters, since when (domain or address matches only)
    tot = rows("select count(*) as n, min(letter_date) as oldest from site.fda_letters where match_kind = 'domain_or_address'")[0]
    d["letters_total"], d["letters_oldest"] = tot["n"], tot["oldest"]
    d["letters_all"] = letters_all_rows()
    # the count and the oldest date the letters page and Home's "See all N letters" show
    d["letters_all_total"] = len(d["letters_all"])
    d["letters_all_oldest"] = min((r["letter_date"] for r in d["letters_all"] if r["letter_date"]), default=None)
    d["guide_stats"] = guide_stats()
    # The seller pages /sellers/ and /sellers/<slug>/ (pages.md, Seller): every seller's profile with its five checks,
    # its top 12 substances by listing count and its FDA warning letters.
    d["seller_profiles"] = rows(
        "select seller_slug, seller_name, domain, seller_kind, product_count, substance_count, price_per_mg_min, "
        "price_per_mg_max, coa_count, newest_coa_date, fda_letter_count, last_fda_letter_date, entity_name, entity_state, "
        "entity_evidence, entity_source_url, registry_status, registry_checked_on, terms_seen, terms_checked_on, privacy_seen, "
        "privacy_checked_on, refund_seen, refund_checked_on, first_seen, price_updated_at, score, score_lab_testing, "
        "score_no_fda_letter, score_registered_company, score_legal_pages, score_fresh_prices, score_checked_on, "
        # the newest legal-pages crawl (peptide-data spec 0015 decision 28): found, absent, blocked, failed or null
        f"legal_checked_on, legal_check_outcome{optional_columns('seller_profile', 'sells_lab_tests')} "
        "from site.seller_profile order by seller_slug")
    add_paid_links(d)
    # task 4C prep (owner task 23, 8 Nov 2026; peptide-data spec 0024): old and new seller page slugs, empty until the
    # owner runs the 4C-day script; [] while the view is missing
    d["seller_redirects"] = (rows("select old_slug, new_slug from site.seller_redirects order by old_slug")
                             if has_view("seller_redirects") else [])
    # excluded states per clinic (pages.md, Clinic rows); while the view is missing build.py reads data/clinic_states.json
    d["seller_states"] = rows("select * from site.seller_states order by seller_slug") if has_view("seller_states") else []
    pull_paid()
    d["seller_substances"] = top_substances(rows(
        "select seller_slug, substance_slug, listing_count, price_per_mg_min, price_per_mg_max, has_coa, "
        "newest_price_observed_at from site.seller_substances"))
    d["seller_letters"] = rows(
        "select seller_slug, letter_date, letter_url, letter_subject, issuing_office, match_kind"
        + optional_columns("seller_letters", "closed_on", "closeout_url") +
        " from site.seller_letters "
        "order by seller_slug, letter_date desc")
    # which substances each FDA warning letter names, with a short first-mention quote (owner task 2 Nov 2026)
    d["letter_substances"] = rows(
        "select letter_reference, letter_url, letter_date, substance_slug, substance_name, first_mention "
        "from site.letter_substances order by letter_date desc, substance_slug")
    add_history_and_labs(d)
    d["pulled_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    d = move_sellers(d, d["seller_redirects"])
    if PAID.exists() and d["seller_redirects"]:
        PAID.write_text(json.dumps(move_sellers(json.loads(PAID.read_text(encoding="utf-8")), d["seller_redirects"]),
                                   indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DATA.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"pull_data: {len(d['legal_db'])} status rows, {len(d['approved_db'])} approvals, {len(d['plans'])} plans, "
          f"{len(d['products'])} of {len(products)} listings, {len(d['sellers'])} of {len(sellers)} sellers, "
          f"{len(d['letters'])} of {d['letters_total']} letters, {d['letters_all_total']} on the letters page, "
          f"{len(d['seller_profiles'])} seller pages")
    # cosmetic listings per substance the site shows (owner UX audit, 3 Nov 2026), for the report
    cos = {}
    for r in products:
        if r.get("form") in COSMETIC_FORMS and r["substance_slug"] in substances(d):
            cos[r["substance_slug"]] = cos.get(r["substance_slug"], 0) + 1
    print(f"pull_data: cosmetic listings ({', '.join(COSMETIC_FORMS)}): "
          + (", ".join(f"{k} {v}" for k, v in sorted(cos.items())) or "none"))
    print(cosmetic_forms_line(products, substances(d)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
