# Master 1

The design system for Peptide Chooser (peptidechooser.com), the human peptide comparison portal: online clinics, prices, legal status.

**This book is the single source for every design decision on the site.** Every page, button, colour, size and spacing comes from here. Anything not in this book does not exist yet: it is proposed and added here first, then built. The site's CSS is generated from `tokens.json` and `components/bundle.css`. Layout and margin rules are in `layout.md`; what goes on each page type, and which button where, is in `pages.md`.

## Logo

The mark is a peptide chain: three `action` green links ending in one `mark` yellow link, the one that is highlighted, on an `ink` square with 4px corners (`assets/Logos`). Next to it the name "Peptide Chooser" in Bricolage Grotesque 800, in `ink` (on paper) or `paper` (on ink). The mark is never redrawn, recoloured, rotated, shadowed or animated.

- `peptide-chooser-mark.svg`: on light backgrounds (header, favicon, social image).
- `peptide-chooser-mark-on-dark.svg`: paper square, for the ink footer and dark panels.
- Header: mark 32px tall, 10px gap to the name at 22px. Footer: mark 28px. Favicon: the mark alone. Smallest use 16px.
- Clear space around the mark and name: at least half the mark's height. Nothing else on that line except the nav.

## The job

The site compares; it never sells. Every visual choice serves one job: let a worried adult find the real price and a trustworthy clinic in under a minute, on a phone, and click Visit with confidence.

## Who it is for

US adults, mostly 30 to 55, comparing peptide and prescription treatments by goal: hair first (from October 2026), then skin, muscle, recovery, libido, energy and weight loss. They are price-anxious and legitimacy-anxious. They scan, they do not read. Most arrive from Google on a phone with one question: what does this cost, is it legal, where do I get it.

## Principles

1. **The number is the hero.** Every page has one big number (price or score) set in `number-xl` with the `mark` highlighter under it. Everything else is quieter.
2. **Borders, not shadows.** Hierarchy comes from 2px ink rules and 1px line dividers. No drop shadows, no gradients, no decorative cards. A thing has a border only when the border tells you something.
3. **Two typefaces, clear roles.** Bricolage Grotesque for everything that shouts (headings, numbers). Atkinson Hyperlegible for everything that is read, because it was designed for readers with low vision and this is a health site.
4. **Green means go, yellow means look here.** `action` green is only on links and the Visit button. `mark` yellow is only under the key number, on the compare band and the alert button. Nothing else is coloured.
5. **Honesty is visible.** "Paid link" sits under every paid button in `fine`. Sponsored rows carry a chip and never move up. A seller without a named pharmacy gets a grey chip, not a green one.
6. **Plain words.** Labels use the words people type into Google: "Where to buy", not "Providers". "Is it legal?", not "Regulatory status". No all-caps labels, no abbreviations without the plain name next to them.

## Clinical paper (the medical look, decided 30 Oct 2026)

The site is about medicine, so its paper looks like a clinic's paper, not like a software dashboard. The cues, and only these:

- **The price pad.** The hero board is drawn as a prescription pad: `paper` card with a 2px `ink` border, an ℞ mark in `display` 800 next to the title, a 2px rule under the head, ledger rows on 1px lines, a rotated "Checked <date>" stamp in `action-text` outline, a dashed tear line at the bottom. It always says "Not a prescription." in `fine`. It replaces the dark ink board everywhere (Home hero, category hero).
- **The body figure.** Our own flat silhouette in `neutral-tint` with dots, like an intake form's "where does it hurt". Never a stock photo, never an anatomical illustration with organs.
- **Chips as lab labels.** Status chips stay small, square-cornered and factual, like labels on a sample.
- **Stamps for dates.** A date the site checked something may be shown as the stamp above; everywhere else dates are plain `small` text.

Not allowed: fake documents (anything that could pass as a real prescription, lab report or letter), stock doctors, pills or syringes as decoration, caduceus or cross icons, handwriting fonts, script signatures. The two typefaces and the colour tokens do not change.

## Motion (decided 30 Oct 2026)

Motion confirms; it never entertains. Everything plays once on arrival and then the page is still. CSS only, no animation library; the page reads the same with JavaScript off.

| What | Trigger | Move | Time |
|---|---|---|---|
| Price pad | page load | ledger rows and hero number rise 8px and fade in, 60ms apart | 280ms ease-out |
| Highlighter under the hero number | page load, after the number | the `mark` bar draws from left to right | 420ms, 200ms delay |
| "Checked" stamp | page load, last | lands from 1.15 scale to its -2° resting angle | 320ms, 650ms delay |
| Active body dot | on choosing a goal | one ring pulse in `mark`, then still | 600ms, twice |
| Goal panel | on choosing a goal | cross-fade in | 160ms |
| Section headings | scrolled into view (JavaScript adds the class; without it nothing is hidden) | rise 12px and fade in | 360ms ease-out |

`prefers-reduced-motion: reduce` turns all of it off and shows the final state at once. Nothing loops, nothing moves on hover except colour, nothing delays reading by more than 0.7s.

## Page anatomy

- **Notice bar** (`paper-2`, 40px, `small`): one sentence on what we are and how we earn, with a link.
- **Header** (76px): wordmark in `display-4` weight 800, five nav items, one primary button. Nav never wraps; on phones it scrolls.
- **Hero**: H1 in `display-1`, lede, the category buttons. Landing: 7 + 5 columns with the price pad on the right. Article pages: title left, hero number right, 2px rule under both.
- **Sections** on landing pages: `space-9` apart, each opened by a section heading (H2 + one-sentence lede, 2px rule, "All X" link on the right).
- **Article pages**: 8-column body with `body` text at 64ch, H2 in `display-3` above a 2px rule, 4-column sticky sidebar with the decision card first.
- **Footer** (`ink`): wordmark and the one-line disclaimer.

## Colour usage rules

| Need | Token |
|---|---|
| Text | `ink`; secondary `ink-2`; on dark `ink-on-dark` |
| Backgrounds | `paper`; alternate bands `paper-2`; dark panels `ink` (footer only since 30 Oct 2026) |
| Approved, named, verified | `action-tint` + `action-text` |
| Waiting, sponsored, partial | `warn-tint` + `warn-text` |
| Prescription, compounding | `info-tint` + `info-text` |
| Not shown, not approved, neutral | `neutral-tint` + `ink-2` |
| The key number | `mark` behind it, `ink` text |

## Shape (decided 28 Oct 2026)

- **Near-sharp.** 4px on buttons, inputs, the price pad, the yellow compare band and the alert band; 2px on chips. No 8–16px rounding anywhere.
- Hierarchy still comes from the highlighter mark, 2px ink rules and the price pad's border, not from rounding or shadows. Master 2 goes fully square (0px) with sharp white panels, which keeps the two sites apart.

## What not to do

- No uppercase labels above headings. The heading is the label.
- No middle dots between facts. Use commas or separate lines.
- No icons in buttons. Words do the work.
- No cards inside cards. A panel contains rows, not more panels.
- No "→" at the end of links.
- No colour other than `action` for links.

## Content rules (added 28 Oct 2026)

- **No placeholders in public.** A page ships with real data or with an honest empty state ("No reader reviews yet. Used Henry Meds? Your review is published as written."). Never "[Dr. Name]" or "[N]".
- **Reviewer line.** Until a named medical reviewer exists, the standfirst says "Every claim links to its source. Prices checked <date>." Add a named reviewer only when the person and credentials are real.
- **Creators.** Only group A from the YouTube research (DeLauer, Williamson, Stillson MD). Group B needs a conflict-of-interest label; group X is never shown.
- **Sources block.** Every peptide and clinic page ends with a numbered "Sources" list: FDA label, FDA policy page, court filing or study, each with the date it was current.
- **Notice bar on phones.** Keep only the first sentence; the "How we make money" link moves to the footer trust row.

## Components

Each component below has a guideline and a live preview. The CSS in `components/bundle.css` is the single source for buttons, chips, tables and section headings: change a token or a class there and every page follows.

Built and previewed: Button, Chip, DataTable, Price, SectionHeading. Built on the site, preview owed here: PricePad (the ℞ board), BodyMap (figure, goal list, goal panel), LegalTable, CreatorList, TrustRow, CookieNotice. Defined in `pages.md` and built in phase 2 before any content page ships: Header, NoticeBar, Footer, Breadcrumbs, ShortAnswer, DecisionCard, ProductRow, SourcesList, AuthorLine, CookieNotice. Each gets its README and preview here first.

## Changes

| Date | Change | Approved |
|---|---|---|
| 28 Oct 2026 | First version: tokens, brand book, five components, cover | Karlo |
| 30 Oct 2026 | Logo added; `layout.md` (margins, no overflow) and `pages.md` (page types, which button where) added; audience widened to goal categories, hair first | ODOBRENO DIZAJN - Karlo - 30. 10. 2026. |
| 30 Oct 2026 | Home rebuilt from the 26 Oct mockup (body map, legal table, creators, trust row); nav by section | Karlo: „ajmo sve 4” |
| 30 Oct 2026 | Wide screens: two frame steps (1480px from 1600px, 1720px from 2200px) with scaled type; checks at 1920 and 2560. Clinical paper: the dark board becomes the ℞ price pad, medical cues listed, fake documents and clip art banned | waiting for Karlo |
| 30 Oct 2026 | Direction A, "Clinical paper, finished": Home hero number is the price (pages.md), pad under the H1 on phones, motion budget, tap targets 44px on phones (dots, nav, header button), shadows removed from the active dot and cookie bar, stamp in sentence case (no uppercase labels) | waiting for Karlo |
