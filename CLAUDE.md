# Peptide Chooser (peptidechooser.com)

Static comparison site for the US peptide market: peptides next to FDA-approved alternatives, by goal (hair first). We compare; we never sell. Owner: Karlo (writes Croatian, does not read code). Talk to him in plain words, short, with a recommendation. Code, commits and docs in English.

## How it is built

- `build.py` renders every page from `data/site.json` into `dist/`. No framework, no build step beyond Python 3.
- `design/` is the working copy of the Master 1 design book (`README.md` principles, `tokens.json`, `bundle.css` components, `layout.md` margins and breakpoints, `pages.md` what goes on each page and which button where). `assets/site.css` holds layout only and uses tokens; `assets/tokens.css` is generated.
- `tools/check.py` (words, seo, schema, parts) and `tools/check_layout.js` (no sideways scroll at 320 to 2560 px) gate every deploy (`.github/workflows/pages.yml`). `tools/og.py` draws share images. `tools/pull_data.py` fills `site.json` from the peptide-data database when `SITE_DATABASE_URL` is set.

```bash
python3 build.py && python3 tools/check.py && node tools/check_layout.js   # before every commit
python3 tools/og.py && python3 build.py                                     # after adding a page
python3 -m http.server 8765 -d dist                                         # look at it locally
```

## Rules that never bend (from the rulebook, "Peptide Chooser: pravila i faze", chapter 11)

1. **The design book is the only source of design.** Nothing is drawn that is not in `design/`. A new part, colour, size or page type is written into the book first (and the owner approves it), then built. Every design change lands in the book in the same commit; the owner mirrors the book to the live design artefact.
2. **Approval tiers.** Tier 1 (text people read, titles, H1, descriptions, URLs, anything that can move rankings): never published without the owner's exact phrase `ODOBRENO SEO - Karlo - <date>`. Design changes (look, layout, components): `ODOBRENO DIZAJN - Karlo - <date>`. Rules and phases: `ODOBRENO PRAVILA - Karlo - <date>`. Silence is not approval. Commit locally, push only after the phrase (or on a side branch, never `main`).
3. **Proof by picture.** Before and after screenshots at 390, 1440 and 2560 px for any visible change, sent to the owner.
4. **Numbers from data, never typed.** Prices, counts, dates and FDA status come from `data/site.json` (and later the database) with their check date and source. No placeholders in public, no "coming soon".
5. **Words.** Vocabulary: "Paid link" (never "affiliate link"), "online clinic", "research-use peptide", "FDA approved", "Not approved". Banned: cure, guaranteed, miracle, breakthrough, #1, revolutionary, clinically proven, risk-free, unlock, delve, crucial, leverage, comprehensive, ensure, utilize, in order to, em dashes. `tools/check.py` enforces it.
6. **One pair of actions per page**: `btn-ink` for our action, `btn-action` (green) only for a paid outbound link through `/out/<name>/` with `rel="sponsored"` and "Paid link" under it. Research-use sellers get no link.
7. **Not an AI look.** No gradient washes, no left-border cards, no emoji, no stock photos, no icons in buttons, no rounded-everything, no uppercase labels. Borders and the yellow `mark` make hierarchy. Medical cues allowed: the ℞ price pad, the body figure, lab-label chips, the "Checked <date>" stamp. Never a fake prescription, lab report or letter.
8. **Protect pages that rank.** A page with impressions in Search Console keeps its URL, title and H1; only additions.

## Design skills

Three skills are installed for design work; use them, and write what they decide into `design/`:
- `impeccable` (`/impeccable critique|audit|polish|typeset|…`): reviews and steering of the UI; run `/impeccable audit` on a page before asking for approval.
- `ui-ux-pro-max` (with `design-system`, `ui-styling`): palettes, font pairings, UX guidelines, motion presets; search its data instead of guessing.
- `frontend-design` (Anthropic plugin, account level): distinctive, intentional visual direction.
Skills advise; the book decides. A skill's suggestion that contradicts `design/README.md` is proposed to the owner, not applied.

## Things not to do

- Do not add a framework, a bundler or a CSS library. Do not add dependencies without asking.
- Do not change `data/site.json` facts without a source URL and a date next to them.
- Do not lower a check to make it pass; fix the page.
- Do not touch `/privacy/`, `/disclosure/` or any Tier 1 text without the SEO phrase.
- Do not push to `main` without the owner's phrase; use `design/<topic>` or `feat/<topic>` branches.
