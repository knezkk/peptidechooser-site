"""The picture parts of the site (design/README.md, Pictures; owner package 4 Nov 2026, part C): the seller tile, the product
drawing and the goal drawing. The drawings live in one sprite, assets/art.svg. Every picture has a fixed box, so nothing shifts
as it loads, and is hidden from screen readers unless it is the only place a name appears.
"""
import re
import zlib
from html import escape

ART = "/assets/art.svg"
# trailing words a monogram skips: Mochi Health -> "Mo", Strut Health -> "St"; Good Life Meds -> "GL"
GENERIC = {"health", "clinic", "medical", "wellness", "telehealth", "inc", "llc", "co"}
DRAWINGS = {"pill-bottle": (40, 46), "pen-brand": (46, 46), "foam-bottle": (30, 42), "serum-dropper": (34, 48),
            "vial-compounded": (24, 40), "vial-research": (24, 40)}
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


def thumb(key):
    """A product drawing on its tile; "" keeps an empty tile's space, so rows line up."""
    if key not in DRAWINGS:
        return '<span class="thumb thumb-none" aria-hidden="true"></span>'
    w, h = DRAWINGS[key]
    return (f'<span class="thumb thumb-{key}" aria-hidden="true"><svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<use href="{ART}#{key}"/></svg></span>')


def form_drawing(text):
    """A form word in any text -> its drawing, or ""."""
    t = (text or "").lower()
    if re.search(r"\b(pill|pills|tablet|tablets|capsule|capsules|oral)\b", t):
        return "pill-bottle"
    if re.search(r"\b(pen|pens|kwikpen|autoinjector)\b", t):
        return "pen-brand"
    if re.search(r"\b(foam|liquid|solution|topical)\b", t):
        return "foam-bottle"
    return ""


def plan_drawing(r):
    """The one mapping for a clinic plan (design/README.md, Pictures): compounded first, then the plan's form from its data, then
    a form word in its name; anything else has no drawing."""
    if r.get("product_kind") == "compounded":
        return "vial-compounded"
    return form_drawing((r.get("dosage_form") or "").replace("_", " ")) or form_drawing(r.get("plan_name"))


def goal_art(slug, size, small=False):
    """A goal's line drawing in clinic blue: the short form under 48px (fewer strokes, heavier line)."""
    if slug not in GOALS:
        return ""
    sym = f"goal-{slug}{'-s' if small else ''}"
    return (f'<svg class="goal-art{" goal-art-s" if small else ""}" width="{size}" height="{size}" viewBox="0 0 56 56" aria-hidden="true">'
            f'<use href="{ART}#{sym}"/></svg>')
