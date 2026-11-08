"""The picture parts of the site (design/README.md, Pictures; owner package 4 Nov 2026, part C): the seller tile, the product
drawing and the goal drawing. The drawings live in one sprite, assets/art.svg. Every picture has a fixed box, so nothing shifts
as it loads, and is hidden from screen readers unless it is the only place a name appears.
"""
import json
import re
import zlib
from html import escape
from pathlib import Path

ART = "/assets/art.svg"
# The goal photos (design/pages/parts.md, Goal photos): one entry per goal, with its source and licence.
_PHOTOS = Path(__file__).parent / "data" / "goal_photos.json"
GOAL_PHOTOS = json.loads(_PHOTOS.read_text(encoding="utf-8")) if _PHOTOS.exists() else {}
# trailing words a monogram skips: Mochi Health -> "Mo", Strut Health -> "St"; Good Life Meds -> "GL"
GENERIC = {"health", "clinic", "medical", "wellness", "telehealth", "inc", "llc", "co"}
DRAWINGS = ("pill-bottle", "pen-brand", "foam-bottle", "serum-dropper", "cream-tube", "vial-compounded", "vial-research", "vial-brand")
GOALS = ("hair", "skin", "weight-loss", "muscle", "recovery", "libido", "longevity")


def monogram(name):
    """The first two letters of the short name; two words or more, their first letters."""
    words = re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])", name)
    while len(words) > 1 and words[-1].lower() in GENERIC:
        words.pop()
    if len(words) > 1:
        return (words[0][0] + words[1][0]).upper()
    return words[0][:2].capitalize() if words else "?"


def tile_colour(slug):
    """One of the ten tile tokens, fixed per seller."""
    return zlib.crc32(slug.encode()) % 10 + 1


def tile(slug, name, size, shop=False, seller=None, named=True, quiet=False):
    """The seller tile at one size. A real logo only from `logo_path` with its source and check date (a brand kit the owner
    approved) and never for a research-use shop; else the monogram: a palette colour for an online clinic, grey for a shop.
    `named` False: the tile is the only place the name appears, so it speaks. `quiet`: its parent is already hidden."""
    s = seller or {}
    speak = "" if quiet else f' role="img" aria-label="{escape(name)} logo"' if not named else ' aria-hidden="true"'
    if not shop and s.get("logo_path") and s.get("logo_source") and s.get("logo_checked_at"):
        alt = "" if named else f"{escape(name)} logo"
        hide = ' aria-hidden="true"' if named else ""
        return (f'<span class="tile tile-{size} tile-logo"{hide}><img src="{escape(s["logo_path"])}" alt="{alt}" '
                f'width="{size}" height="{size}" loading="lazy"></span>')
    tone = "tile-shop" if shop else f"tile-c{tile_colour(slug)}"
    return f'<span class="tile tile-{size} {tone}"{speak}>{escape(monogram(name))}</span>'


def thumb(key, no_form=False):
    """A product drawing on its tile. No drawing keeps the tile's space; tools/check.py fails it unless the data names no form
    at all (`no_form`)."""
    if key not in DRAWINGS:
        return f'<span class="thumb thumb-none"{" data-noform" if no_form else ""} aria-hidden="true"></span>'
    return f'<span class="thumb thumb-{key}" aria-hidden="true"><svg width="56" height="56" viewBox="0 0 56 56"><use href="{ART}#{key}"/></svg></span>'


def form_drawing(text):
    """A form word in any text -> its drawing, or ""."""
    t = (text or "").lower()
    if re.search(r"\b(pill|pills|tablet|tablets|capsule|capsules|oral|odt)\b", t):
        return "pill-bottle"
    if re.search(r"\b(pen|pens|kwikpen|autoinjector|shot|shots)\b", t):
        return "pen-brand"
    if re.search(r"\b(foam|liquid|solution|topical|spray)\b", t):
        return "foam-bottle"
    if re.search(r"\b(cream|gel|lotion)\b", t):
        return "cream-tube"
    if re.search(r"\bserum\b", t):
        return "serum-dropper"
    if re.search(r"\b(vial|injection)\b", t):
        return "vial-brand"
    return ""


def plan_drawing(r):
    """The one mapping for a clinic plan (design/README.md, Pictures): compounded first, then the plan's form from its data, then
    a form word in its name; anything else has no drawing."""
    if r.get("product_kind") == "compounded":
        return "vial-compounded"
    # Drops are a liquid (design/pages/parts.md, the one mapping); only a plan's own form says so, because "drops" in running text can mean something else.
    form = (r.get("dosage_form") or "").replace("_", " ").replace("drops", "liquid")
    return form_drawing(form) or form_drawing(r.get("plan_name"))


def plan_picture(r):
    """A plan's drawing; a plan whose data names no form at all keeps the space."""
    key = plan_drawing(r)
    return thumb(key, no_form=not key and not r.get("dosage_form"))


def goal_photo(slug, art_size, small=False):
    """A goal's photo in its panel; decorative, because the goal's name stands beside it. A goal without an entry keeps its drawing.
    Lazy, so a phone never loads the goal page's panel, which is not drawn there."""
    e = GOAL_PHOTOS.get(slug)
    if not e:
        return goal_art(slug, art_size)
    src, w, h = (e["file_small"], 450, 300) if small else (e["file"], 900, 600)
    return f'<img class="goal-photo" src="{escape(src)}" alt="" width="{w}" height="{h}" loading="lazy" decoding="async">'


def goal_art(slug, size):
    """A goal's line drawing, in the goal's own colour (goal-<slug>, on the panel around it)."""
    # A goal with no drawing of its own in the book (/menopause/) shows the existing pill bottle on the neutral panel.
    ref = f"goal-{slug}" if slug in GOALS else "pill-bottle"
    return (f'<svg class="goal-art" width="{size}" height="{size}" viewBox="0 0 56 56" aria-hidden="true">'
            f'<use href="{ART}#{ref}"/></svg>')
