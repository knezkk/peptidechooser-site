"""Pull the numbers the site shows from the peptide-data database (rulebook 11.8: numbers from data, never typed).

Reads the `site.*` views through the read-only role (peptide-data spec 0015) and updates data/site.json:
  - site.catalog_counts  -> "db": options and sellers counted, newest price date
  - site.substance_status, site.approved_drugs -> "legal_db": status per substance with its source and date
  - site.plan_prices     -> "plans": telehealth plan prices per seller, with the date the page was last seen
  - site.products        -> "products": research-use listings for the substances the site shows (see keep_products)
  - site.sellers         -> "sellers": the seller rows those listings point to, with their background check
  - site.fda_letters    -> "letters": the newest FDA warning letters to sellers in the database (see letters_rows)

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


def keep_products(all_rows, subs, n=10):
    """site.json stays small: per substance, each seller's cheapest listing, then the n cheapest of those by price per mg
    (listings with a price per mg first, then blends and listings without one, by price), so the seller window
    shows one row per seller (owner, 31 Oct 2026)."""
    key = lambda r: (r["price_per_mg"] is None, r["price_per_mg"] or 0, r["price_usd"] is None, r["price_usd"] or 0, r["seller_slug"])
    out = []
    for slug in sorted(subs):
        best = {}
        for r in sorted((r for r in all_rows if r["substance_slug"] == slug), key=key):
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


def main():
    if not URL:
        print("pull_data: SITE_DATABASE_URL not set, site.json left as it is")
        return 0
    d = json.loads(DATA.read_text(encoding="utf-8"))
    d["db"] = rows("select * from site.catalog_counts")[0]
    d["legal_db"] = rows(
        "select substance_slug, canonical_name, is_peptide, regime, status_value, scope, valid_from, "
        "first_seen_by_us, source_id, source_url from site.substance_status order by substance_slug, regime")
    d["approved_db"] = rows(
        "select substance_slug, brand_name, application_no, sponsor, approval_date, route, indications "
        "from site.approved_drugs order by substance_slug, approval_date")
    d["plans"] = rows(
        "select seller_slug, seller_name, plan_slug, plan_name, product_kind, dosage_form, substance_slug, "
        "pharmacy_partner, price_monthly, price_first_month, membership_fee_monthly, consult_fee, "
        "commitment_months, observed_at, last_seen, pricing_url from site.plan_prices order by seller_slug, plan_slug")
    products = rows(
        "select seller_slug, seller_name, seller_status, product_name, variant_title, product_url, substance_slug, is_blend, "
        "amount_mg, form, price_usd, price_per_mg, price_observed_at, first_seen, last_seen, has_coa, coa_count from site.products")
    d["products"] = keep_products(products, substances(d))
    used = {r["seller_slug"] for r in d["products"]}
    sellers = rows(
        "select seller_slug, seller_name, domain, seller_kind, legal_entity_name, registry_state, legal_entity_source_url, "
        "fda_letter_count, last_fda_letter_date, coa_count, product_count, price_updated_at, first_seen, last_seen "
        "from site.sellers order by seller_slug")
    d["sellers"] = [r for r in sellers if r["seller_slug"] in used]
    d["letters"] = letters_rows()
    d["pulled_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    DATA.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"pull_data: {len(d['legal_db'])} status rows, {len(d['approved_db'])} approvals, {len(d['plans'])} plans, "
          f"{len(d['products'])} of {len(products)} listings, {len(d['sellers'])} of {len(sellers)} sellers, "
          f"{len(d['letters'])} letters")
    return 0


if __name__ == "__main__":
    sys.exit(main())
