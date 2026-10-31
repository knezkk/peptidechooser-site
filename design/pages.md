# Pages and buttons

What goes on each page type, top to bottom, and which button sits where. A page is built only from the parts listed for its type. A new part is added to this book first.

## Buttons: one rule each

| Button | Only for | Label pattern | Max per |
|---|---|---|---|
| `btn-action` (green) | A paid outbound link to a partner, through `/out/<name>/` with `rel="sponsored"` | "Visit Hims", "See Keeps prices" | one per table row or decision card; always with "Paid link" under it. Before the goal has an affiliate url in data/site.json it is disabled: `<span class="btn btn-action" role="button" aria-disabled="true">Visit</span>` in `ink-muted`, never an `<a>`, no `/out/` link, no `rel`, with "No paid link yet" under it |
| `btn-ink` | The site's own main action | "Compare hair options", "Search" | one per section; one in the header |
| `btn-line` | A second choice next to an ink or action button, or a quiet action alone | "Read our Hims review", "How we rate" | one per group |
| `btn-sm` | Any of the above inside a table row | as above | one action + one line per row |
| `btn-mark` | The email alert band (not built yet) | "Get price alerts" | one per page |

**One pair of actions per page.** The site's own action is `btn-ink`; the paid click is `btn-action` with "Paid link" under it. A text link never repeats the button above it. No link to a partner anywhere except through a `btn-action`.

Everything else is a text link in `action` green. A partner without an affiliate program gets `btn-line` "Read review", never green. A "research use only" seller gets no button at all: one row with a `chip-neutral` "Not approved", no price, no link.

## Every page

1. **Notice bar** (`paper-2`, `small`): "We compare, we don't sell. Some links pay us." + link to /disclosure/. On phones the first sentence only.
2. **Header**: logo (links home), nav, one `btn-ink`. Nav is by section of the site, not by category: Peptides (the goals section on Home), Where to buy, Compare prices, Safety and legal (the legal table on Home), Learn, How we rate, About. An item appears only when its section exists; never more than 7 items; on phones the nav scrolls inside itself (layout.md). The header button is "Compare by goal" → the goals section on Home (becomes "Find my option" when the questionnaire exists).
3. **Breadcrumbs** (`small`) on every page except Home.
4. Page content (below, by type).
5. **Footer** (`ink`): logo on dark, links (About, How we rate, Contact, Affiliate and medical disclosure, Privacy), one-line disclaimer "Not medical advice. Talk to a doctor before starting any treatment.", "How we make money" link.
6. **Cookie notice** (Google Analytics): bottom bar, "Accept" `btn-ink` and "Reject" `btn-line`, equal size.

## Home `/`

Home is the hub for every goal, built from the 26 Oct 2026 mockup ("Peptidi Master 1 i 2", landing) with the parts that need data we do not have yet left out until the data exists. Its title, H1, description and layout are set once and never change when a category is added; a new category only adds rows and a panel.

- **Title:** "Best peptides by goal, compared | Peptide Chooser". **H1:** "The best peptides for your goal, compared honestly." Home never targets one category's main search term.
- **Hero** (the evidence rail, owner decision 31 Oct 2026, mockup `mockups/evidence-rail.png`): a flat `paper-2` band. H1 `display-1` and the lede side by side on wide screens, "What is a peptide?" under the lede. Then the body figure on the left (sticky from 900px, hidden under 640px) and the rail on the right (`id="goals"`): a 2px `clinic` line joining three 44px `clinic` circles numbered 1 to 3 (design book, Medical cues). Below the rail, in the same band: How we rate as one strip (heading, its one sentence and "Read the full method", then the five criteria in a row) and the trust links (How we make money, Who checks our facts, Mistakes we fixed, Sources); then "What the labels mean" (one white card per `glossary` entry). On phones (under 640px) the order is H1, the rail, the lede with "What is a peptide?", How we rate, the labels; steps stacked, chips in two columns, option rows as three short lines. No search box until there is a database to search.
- **The three steps** (inside the hero; every goal is on the figure and in the chips from day one, a goal is never "coming soon"; with JavaScript off the first goal is shown):
  1. **Choose a goal**: one chip per goal (all seven, `label`), the chosen one filled `mark`; the pins on the figure are the same control. Click, Enter or Space choose; arrow keys move to the next or previous chip and choose it.
  2. **Compare the options**: at the right of the step heading, "Is it legal today?" with "Checked <date>" under it (the legal table's checked date), linking to `#legal`. Then the chosen goal's `for` sentence, then the option list: one row per option in the goal's `peptides`: the name and its `does` line (footnotes for any number); the status chip (database status when there is one, else the hand-written one) with `status_plain` under it; the price pad "from $X/mo" with its source and check date, only where the option's price has a source in data/site.json (the goal's `price_source` for the option marked `price`, or the option's own `price_source` with `price_from_usd`); then the `how` line. Under the rows "<N> options checked" (`options_checked`, else the number of rows) with the Checked stamp. Then `btn-ink` "Compare <goal> options" for a goal with a page; for an unpublished goal the existing sentence "Full comparison for this goal is not published yet. The legal status above is current as of <date>."
  3. **Get it**: the goal's top pick (the rule of "Top pick per goal" below): name and status chip, one sentence on how people get it (the option's `how_plain`, else its `how`), and `btn-action` "Visit" with "Paid link" under it, or the disabled span with "No paid link yet" until the goal has an affiliate url. A goal with no FDA-approved option shows "No FDA-approved option", its research-use peptide with its chip and "Sold by research-use shops; we do not link to them.", and no button.
- **One pair of actions in the hero**: `btn-ink` only in step 2, `btn-action` only in step 3.
- **Lay-reader copy** (docs/copy-home-2026-10-30.md, approved 30 Oct 2026): the chips show `label`; step 2 shows the `for` sentence and, per option, `does`, the chip with `status_plain`, and `how` (one line on wide screens, three short lines on phones). A price in `status_plain` shows only when its source is on the page, and is left out of a row whose price pad already shows it. The goal's `intro` and `panel_title` are not on Home since the evidence rail (31 Oct 2026); /hair/ keeps its own copy. /hair/'s options table shows the same three parts under the name and the chip.
- **Compare by goal** (`id="compare"`, SectionHeading): DataTable, one row per published goal: goal, best proven option, price from, FDA chip, `btn-sm` ink "Compare", and a Visit column: `btn-sm btn-action` "Visit" (disabled until the goal has an affiliate url, see the button table).
- **Is it legal today?** (`id="legal"`, `paper-2` band): DataTable of the peptides people ask about most: peptide, status chip (`chip-ok` approved, `chip-info` cosmetic, `chip-warn` compounded or not a peptide, `chip-neutral` not approved), what that means, a superscript link to the source. Checked date in the heading. When data/site.json has `legal_db` from the database, a row whose substances all have a status there renders one row per substance from it: `DB_STATUS` in build.py maps each (regime, status_value) to the chip, its label and the plain sentence, the row links its `source_url` with the date we first saw it, and the heading's checked date is the newest of those dates. Brand names after an approved substance are the distinct base names from `approved_db` (first word, no bracket, title case, at most four). A hand row marked `note_with_db` (the July 2026 PCAC proposal for BPC-157, TB-500, MOTS-c and epitalon) keeps its note and source as a second sentence after the database one. Status sentences approved: ODOBRENO SEO - Karlo - 31. 10. 2026. Without `legal_db`, or for a row the database does not fully cover, the hand-written `legal` row is shown, and option chips likewise use the database status for their `substance` when there is one, else the hand-written status.
- **How we rate**: the five criteria, as the strip in the hero band.
- **Learn** (`id="learn"`): the six newest guides when guides exist, and "Who to follow": up to six creators from the creator review, each with one line on why, `rel="nofollow"`, a note that nobody on the list pays us.
- **Trust links**: in the hero band under How we rate: How we make money, Who checks our facts, Mistakes we fixed (/corrections/), Sources (`#sources`).
- **Sources**: numbered, legal sources first (they are the ones referenced), then price sources.

**Top pick per goal** (`id="top-picks"`, after "Is it legal today?", owner decision 31 Oct 2026): one white card per goal, all seven goals: the goal's `label`, the top pick's name and status chip, and `btn-action` "Visit". The top pick is the first option in the goal's `options` (or, for a goal without a comparison page, its chooser options) whose status is FDA approved and that is not marked `top_pick: false` (an option approved for another use, like tesamorelin for muscle); if none, the option marked `best`; if neither, the card says "No FDA-approved option" and has no button; under it the goal's most asked-about peptide: the first option with a not-approved status (database chip when there is one, else the hand-written one) that research-use shops sell, as name and status chip, then "Sold by research-use shops; we do not link to them." (ODOBRENO SEO - Karlo - 31. 10. 2026.), no button, no price. Every approved chip on Home reads "FDA approved"; prescription is stated in the option's "how" line. No price is typed. The button is disabled with "No paid link yet" under it until the goal has `affiliate` (`name`, `url`) in data/site.json; then it is `<a class="btn btn-action" href="/out/<name>/" rel="sponsored">` with "Paid link" under it. **Compare any two**, **FDA warning letters** and the **email alert band** are added when the compare pages, the letters feed and the email service exist, never drawn empty.

**The goal list** (one list for the figure, the nav and the folders): Hair /hair/, Skin /skin/, Weight loss /weight-loss/, Muscle and hormones /muscle/, Recovery and joints /recovery/, Sexual health /libido/, Longevity and energy /longevity/. The body areas and pins live in `build.py` (`REGIONS`); the old `map` positions in data/site.json are no longer used.

## Category `/hair/`

H1, ShortAnswer (`intro`), hero number (cheapest proven option per month, `num-xl` + `mark`), DataTable of every option (Rx, serums, research-use rows at the bottom), guides list, sources.

## Guide `/hair/<topic>/`

Article 8 + sidebar 4. Main: H1, AuthorLine + "Last updated", ShortAnswer, body (`body`, 64ch), H2s as `.art-h2`, product rows where options are named, SourcesList. Sidebar (sticky from 900px): DecisionCard (best pick, its price, `btn-action` + "Paid link", `btn-line` for the runner-up).

## Peptide `/peptides/<name>/`

H1, ShortAnswer, facts ledger (FDA status chip, forms, prescription needed chip), evidence by goal (table: goal, evidence chip, source), where to get it (DataTable), SourcesList. No doses, ever.

## Vendor `/vendors/<name>/`

H1 + hero number (price per month), DecisionCard in the sidebar, rating by our five criteria in words (no numeric score yet), what's good / not so good, prices ledger with dates, SourcesList.

## Compare `/compare/<a>-vs-<b>/`

H1, ShortAnswer ("Pick A if …, pick B if …"), two-column comparison table (stacks under 640px), a `btn-action` per side, SourcesList.

## Trust pages (About, How we rate, Disclosure, Privacy, Contact, Corrections)

Prose only: H1, lede, body. Contact has one `btn-ink` "Email hello@peptidechooser.com". No tables, no buttons to partners.

## Rules that apply to every page

- **Author line** (`small`): on every guide, peptide and vendor page, under the H1: author name linked to /about/, "Last updated 9 Sep 2026", and the standing line "Every claim links to its source. Prices checked 9 Sep 2026." until a named medical reviewer exists.
- **No placeholders in public.** Nothing in square brackets ships. A fact that cannot be checked is left out or reads "To confirm".
- **Share image.** Every page gets an og:image drawn at build time from its title: mark, title in `display-2`, "Peptide Chooser" in `small`, on `paper`. 1200 by 630. Never hand-made.
- **Numbers from data, never typed.** Prices, counts and FDA status come from the site's data file; the page only renders them, with their check date.

## 404

H1 "This page doesn't exist", one sentence, `btn-ink` "Go to the home page" and links to the categories.
