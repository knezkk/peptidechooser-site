# Peptide Chooser (peptidechooser.com)

Static comparison site for the US peptide market: peptides next to FDA-approved alternatives, by goal (hair first). We compare; we never sell. Owner: Karlo (writes Croatian, does not read code). Talk to him in plain words, short, with a recommendation. Code, commits and docs in English.

## How it is built

- `build.py` renders every page from `data/site.json` into `dist/`. No framework, no build step beyond Python 3.
- `design/` is the working copy of the Master 1 design book (`README.md` principles and rules, `CHANGELOG.md` every change, `tokens.json`, `bundle.css` components, `layout.md` margins and breakpoints, `pages.md` the index of `pages/<page>.md`, what goes on each page and which button where). `assets/site.css` holds layout only and uses tokens; `assets/tokens.css` is generated.
- `tools/check.py` (words, seo, schema, parts, data, book, addresses and more) and `tools/check_layout.js` (no sideways scroll at 320 to 2560 px) gate every deploy (`.github/workflows/pages.yml`). `tools/og.py` draws share images. `tools/pull_data.py` fills `site.json` from the peptide-data database when `SITE_DATABASE_URL` is set.

```bash
python3 build.py && python3 tools/check.py && node tools/check_layout.js   # before every commit
python3 tools/og.py && python3 build.py                                     # after adding a page
python3 -m http.server 8765 -d dist                                         # look at it locally (w1 8765, w2 8766, w3 8767, w4 8768)
```

## Rules that never bend (from the rulebook, "Peptide Chooser: pravila i faze", chapter 11)

1. **The design book is the only source of design.** Nothing is drawn that is not in `design/`. A new part, colour, size or page type is written into the book first (and the owner approves it), then built. Every design change lands in the book in the same commit; the owner mirrors the book (`README.md`, `CHANGELOG.md`, `layout.md`, `tokens.json`, `bundle.css`, `pages.md` and every file in `pages/`) to the live design artefact.
2. **Approval tiers.** Tier 1 (text people read, titles, H1, descriptions, URLs, anything that can move rankings): never published without the owner's exact phrase `ODOBRENO SEO - Karlo - <date>`. Design changes (look, layout, components): `ODOBRENO DIZAJN - Karlo - <date>`. Rules and phases: `ODOBRENO PRAVILA - Karlo - <date>`. Silence is not approval. The deploy stops when the words of a page's title, description or H1 differ from the live page, unless the owner's phrase covers exactly that text; only other digits, dates, prices or counts, a new seller, compare or substance page that follows its live template, and a page gone with a redirect pass and are listed in the run log (`tools/tier1_guard.py`). Commit locally, push only after the phrase (or on a side branch, never `main`).
3. **Proof by picture.** Before and after screenshots at 390, 1440 and 2560 px for any visible change, sent to the owner. A `/go` task takes the shots its size sets (`.claude/skills/go/SKILL.md`, owner decision 5 Nov 2026).
4. **Numbers from data, never typed.** Prices, counts, dates and FDA status come from `data/site.json` (and later the database) with their check date and source. No placeholders in public, no "coming soon".
5. **Words.** Vocabulary: "Paid link" (never "affiliate link"), "online clinic", "research-use peptide", "FDA approved", "Not approved". Banned: cure, guaranteed, miracle, breakthrough, #1, revolutionary, clinically proven, risk-free, unlock, delve, crucial, leverage, comprehensive, ensure, utilize, in order to, em dashes. `tools/check.py` enforces it.
6. **One pair of actions per page**: `btn-ink` for our action, `btn-action` (green) only for a paid outbound link through `/out/<name>/` with `rel="sponsored"` and "Paid link" under it. Research-use sellers get no link.
7. **Not an AI look.** No gradient washes, no left-border cards, no emoji, no stock photos except the goal photos (`design/pages/parts.md`), no icons in buttons, no rounded-everything, no uppercase labels. Borders and the yellow `mark` make hierarchy. Medical cues allowed: the ℞ price pad, the body figure, lab-label chips, the "Checked <date>" stamp. Never a fake prescription, lab report or letter.
8. **Protect pages that rank.** A page with impressions in Search Console keeps its URL, title and H1; only additions.

## Site map rules (8 Nov 2026)

Owner, ODOBRENO PRAVILA - Karlo - 8. 11. 2026. The full rules are in `docs/site-map-rules-2026-11-08.md`: the 12 page types with address, parent and Google rule (section 1), links incl. `rel="sponsored"` on every `/out/` link (4), data changes (5), the main page for each overlap (6), what the site never builds (7) and the 36-address move list (8). Every agent places and names every new page by them. `tools/check.py` (check-addresses) enforces the mechanical address rules on new addresses; live addresses that break one are listed in `data/live-addresses.txt`, and nothing new is added there.

### 2. Where a new page goes
Before question 1: does a live page already target this search? Two searches are the same when they share 3 or more of the Google top 10. If a live page owns it, add a section to that page. A page Google already shows keeps its address, title and H1.

1. Compares two things? Two named sellers, substances or brands side by side from data with no written verdict: /compare/{a}-vs-{b}/, names in alphabetical order, the reverse never made. A broad comparison (peptides vs steroids) or one with a written verdict is a guide. If a guide owns the pair, no comparison is made.
2. One seller, or one seller's offer of one substance? /sellers/{seller}/ or /sellers/{seller}/{substance}/. Blends never get an offer page.
3. One substance or one of its brands? /peptides/{substance}/ or /peptides/{substance}/{brand}/. A question about one substance with its own measured search that the substance page's format does not match (legal?, price per mg, use for one goal) is a guide with the substance name in its title; it links to the substance page and counts as one of its 6 signals. A brand with several substances gets its parent once, kept in the database: the substance whose page is indexed; if several or none, the first alphabetically that has a page.
4. One lab, or one company's FDA letters? /labs/{lab}/ or /fda-warning-letters/{company}/.
5. A goal people search for? /{goal}/; a narrower search inside a goal is /{goal}/{topic}/.
6. A group of substances by approval, route or class? /{group}/.
7. A price calculator? /tools/{tool}/, never dosing.
8. None of these? A guide at /learn/{guide}/.

### 3. Address rules (every new page)
1. Lowercase letters, numbers and hyphens, with a trailing slash.
2. Each thing has one slug from the database. Once live, a slug never changes; a new name goes into the database as an alias. Only exception: the 36 addresses in section 8, moved once before wave A.
3. A seller's slug is the brand people search for, not the legal company name.
4. No year, date or amount, no word that goes stale ("best", "cheapest", "latest"). One allowed fixed word: "new" in /weight-loss/new-drugs/.
5. No address deeper than three levels below home.
6. A goal or group never takes a list or trust page name: peptides, sellers, compare, learn, labs, tools, fda-warning-letters, search, out, about, how-we-rate, sources, contact, corrections, disclosure, privacy, or any folder name the site's code publishes.
7. Filters on list pages never create an indexable address.
8. A new page type needs a template in the design book first (ODOBRENO DIZAJN).


## Hand-off with the owner's assistant

The owner's assistant writes the next task into `.handoff/next.md`; the owner types `/go` (`.claude/skills/go/SKILL.md`) and the agent runs it and writes the full report into `.handoff/report.md` (the PR, the screenshot paths, the checks, and open questions under `## Questions`). An approval phrase counts only inside `.handoff/next.md`, on its own line in that task's block of `.handoff/queue.md`, or typed by the owner in the terminal. `.handoff/` is never committed (owner, ODOBRENO PRAVILA - Karlo - 31. 10. 2026).

Work runs in parallel worktrees named w1, w2, w3 and w4, each on its own branch with its own PR. Only w1 merges to `main` (after the owner's phrase); w2, w3 and w4 stop at a ready PR and say so in their report (owner, ODOBRENO PRAVILA - Karlo - 3. 11. 2026).

`.handoff/queue.md` holds a worktree's numbered tasks; `/go` takes them one by one. Task size, the report's shape, ports and the real-data build are in the go skill.
The watcher `tools/watch_go.sh` runs `/go` by itself: the owner starts it once per worktree in a plain terminal (`sh tools/watch_go.sh`).
Every 30 s it looks for a changed `queue.md` or `next.md` with an open task, runs `claude -p "/go"` and logs to `.handoff/watch.log`.
It uses the owner's `defaultMode` from `~/.claude/settings.json` (or `GO_PERMISSION_MODE`; if neither, `acceptEdits`) and stops with "LOGIN EXPIRED" when the login runs out.

## Who owns what

- **w1** (`peptidechooser-site`): the design book (`design/`), `assets/site.css`, `design/bundle.css`, tokens, every new part; the only agent that merges to `main`.
- **w2** (`-w2`): data on the site: `build.py` data paths, `tools/pull_data.py`, `tools/check.py`, `/out/`, `data/`.
- **w3** (`-w3`): words and pages: Tier 1 text, new goal pages, `/learn/`, SEO, schema.
- **w4** (`-w4`): larger visual pieces (the body figure, illustrations, drawings), built from parts the book already has.
- An agent that needs a new part, colour, size or layout rule writes the request into `.handoff/to-w1.md` in its own worktree and continues with existing parts; it never adds to `design/` itself. w1 adds the part in its own PR first.
- The data repo stays as it is.

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
