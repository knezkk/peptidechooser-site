"""Pull the numbers the site shows from the peptide-data database (rulebook 11.8: numbers from data, never typed).

Reads the `site.*` views through the read-only role (peptide-data spec 0015) and updates data/site.json:
  - site.catalog_counts  -> "db": options and sellers counted, newest price date
  - site.substance_status, site.approved_drugs -> "legal_db": status per substance with its source and date
  - site.plan_prices     -> "plans": telehealth plan prices per seller, with the date the page was last seen

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
    d["pulled_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    DATA.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"pull_data: {len(d['legal_db'])} status rows, {len(d['approved_db'])} approvals, {len(d['plans'])} plans")
    return 0


if __name__ == "__main__":
    sys.exit(main())
