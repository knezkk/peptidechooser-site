"""The "Legit?" rating (owner decisions 21 Nov 2026, queue block 59, wave 1): one rating per seller, from the checks the
site already holds. The only place the site may call a seller "Legit"; build.py draws it and tools/check.py recomputes it.

- A research-use shop is always "Lab-use only", also with every check met; never "Legit" and never "Caution".
- Clinics, supplement and cosmetic shops share one scale: every check met is "Legit"; one gap (one missing check, or an
  FDA warning letter the FDA has closed out) is "Legit, with gaps"; an FDA warning letter without a close-out letter, or
  two gaps or more, is "Caution".
- The state registry never lowers the rating: a seller not found in one is rated on its other checks and gets the note
  "Not found in a state business registry yet".
- Fresh prices is never counted (owner, 22 Nov 2026, block 59 fix): it is our data's freshness, not the seller's; the check
  stays on the page's check list.
No imports from build.py, so the check can use the same function."""

REGISTRY = "score_registered_company"
LETTER = "score_no_fda_letter"
FRESH = "score_fresh_prices"
REGISTRY_NOTE = "Not found in a state business registry yet"

# label, chip class (existing book chips until w1 draws the rating part), the slug check.py and the page use
LEGIT = ("Legit", "chip-ok", "legit")
GAPS = ("Legit, with gaps", "chip-info", "gaps")
CAUTION = ("Caution", "chip-warn", "caution")
LAB = ("Lab-use only", "chip-neutral", "lab")
LABELS = {x[2]: x[0] for x in (LEGIT, GAPS, CAUTION, LAB)}


def seller_rating(r, letters, checks, research_use, date=lambda d: d):
    """A seller's rating: dict(key, label, chip, reason, notes). `r` the seller profile (its score_* booleans), `letters`
    the seller's FDA warning letters (letter_date, closed_on), `checks` the (key, short name) pairs it is scored on,
    `research_use` true for a research-use shop, `date` the page's date format."""
    if research_use:
        return {"key": LAB[2], "label": LAB[0], "chip": LAB[1],
                "reason": "Sold for research use only, not for use in people.", "notes": []}
    notes = [REGISTRY_NOTE] if any(k == REGISTRY for k, _ in checks) and not r.get(REGISTRY) else []
    missing = [name for k, name in checks if k not in (REGISTRY, LETTER, FRESH) and not r.get(k)]
    letter, open_letter = "", False
    if any(k == LETTER for k, _ in checks) and not r.get(LETTER):
        newest = max(letters, key=lambda x: x.get("letter_date") or "", default=None)
        on = (newest or {}).get("letter_date") or r.get("last_fda_letter_date") or ""
        closed = bool(letters) and all(x.get("closed_on") for x in letters)
        if closed:
            shut = max(x["closed_on"] for x in letters)
            letter = f"FDA letter {date(on[:10])}, closed out {date(shut[:10])}" if on else f"FDA letter closed out {date(shut[:10])}"
        else:
            open_letter = True
            letter = f"FDA letter {date(on[:10])}, not closed out" if on else "FDA letter, not closed out"
    gaps = len(missing) + (1 if letter and not open_letter else 0)
    parts = ([letter] if letter else []) + ([f'Missing: {", ".join(missing)}'] if missing else [])
    if open_letter or gaps >= 2:
        kind = CAUTION
    elif gaps == 1:
        kind = GAPS
    else:
        kind = LEGIT
    reason = "; ".join(parts) + "." if parts else "Every check we rate on is met."
    return {"key": kind[2], "label": kind[0], "chip": kind[1], "reason": reason, "notes": notes}
