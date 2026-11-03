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
  - site.letter_substances -> "letter_substances": the substances each FDA warning letter names, for /peptides/, the
    compare pairs and the letters page's substance filter
  - site.seller_profile, site.seller_substances, site.seller_letters -> "seller_profiles", "seller_substances" (top 12 per
    seller, see top_substances), "seller_letters": the seller pages /sellers/ and /sellers/<slug>/

Everything else in site.json (hand-checked prices with their sources, texts, goals) is left untouched.
Run before build.py:  SITE_DATABASE_URL=postgres://site_reader:...@host:5432/postgres python3 tools/pull_data.py
Without SITE_DATABASE_URL it exits 0 and changes nothing, so a local build never needs the database.
"""
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "site.json"
URL = os.environ.get("SITE_DATABASE_URL", "")


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


def substances(d):
    """The substances the site shows: every option's `substance` or `substances` and every legal row's `substances`."""
    out = {p["substance"] for g in d["goals"] for p in g.get("peptides", []) if p.get("substance")}
    out |= {s for g in d["goals"] for p in g.get("peptides", []) for s in p.get("substances", [])}
    return out | {s for r in d["legal"]["rows"] for s in r.get("substances", [])}


# Cosmetic product forms (products.product_form): a cosmetic option's window lists only these (build.py COSMETIC_FORMS)
COSMETIC_FORMS = {"cream", "serum", "lotion", "gel"}


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
    return out


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
        "seller_name, seller_kind, match_kind, peptide_related from site.fda_letters_all "
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
        "commitment_months, observed_at, last_seen, pricing_url, fda_letter_count, last_fda_letter_date "
        "from site.plan_prices order by seller_slug, plan_slug")
    products = rows(
        "select seller_slug, seller_name, seller_status, product_name, variant_title, product_url, substance_slug, is_blend, "
        "amount_mg, form, price_usd, price_per_mg, price_observed_at, first_seen, last_seen, has_coa, coa_count from site.products")
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
        "legal_checked_on, legal_check_outcome "
        "from site.seller_profile order by seller_slug")
    d["seller_substances"] = top_substances(rows(
        "select seller_slug, substance_slug, listing_count, price_per_mg_min, price_per_mg_max, has_coa, "
        "newest_price_observed_at from site.seller_substances"))
    d["seller_letters"] = rows(
        "select seller_slug, letter_date, letter_url, letter_subject, issuing_office, match_kind from site.seller_letters "
        "order by seller_slug, letter_date desc")
    # which substances each FDA warning letter names, with a short first-mention quote (owner task 2 Nov 2026)
    d["letter_substances"] = rows(
        "select letter_reference, letter_url, letter_date, substance_slug, substance_name, first_mention "
        "from site.letter_substances order by letter_date desc, substance_slug")
    d["pulled_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
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
    print("pull_data: cosmetic listings (cream, serum, lotion, gel): "
          + (", ".join(f"{k} {v}" for k, v in sorted(cos.items())) or "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
