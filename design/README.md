# Master 1

The design system for Peptide Chooser (peptidechooser.com), the human peptide comparison portal: online clinics, prices, legal status.

**This book is the single source for every design decision on the site.** Every page, button, colour, size and spacing comes from here. Anything not in this book does not exist yet: it is proposed and added here first, then built. The site's CSS is generated from `tokens.json` and `components/bundle.css`. Layout and margin rules are in `layout.md`; what goes on each page type, and which button where, is in `pages.md`.

## Logo

The mark is a peptide chain: three `action` green links ending in one `mark` yellow link, the one that is highlighted, on an `ink` square with 4px corners (`assets/Logos`). Next to it the name "Peptide Chooser" in Bricolage Grotesque 800 (`font-brand`, loaded for those letters only), in `ink` (on paper) or `paper` (on ink). The wordmark is the only Bricolage text on the site. The mark is never redrawn, recoloured, rotated, shadowed or animated.

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
2. **Borders, not shadows.** Hierarchy comes from 2px ink rules, 1px warm `line` hairlines and, on the price pad and goal panel, a 4px double rule under the title. No drop shadows, no gradients, no decorative cards. A thing has a border only when the border tells you something.
3. **Two typefaces, clear roles.** Newsreader, an editorial serif with optical sizes, for everything that shouts (headings, the price pad, numbers in lining figures), so the site reads like a medical journal, not an app. Atkinson Hyperlegible for everything that is read, because it was designed for readers with low vision and this is a health site.
4. **Green means go, yellow means look here.** `action` green is only on links and the Visit button. `mark` yellow is only under the key number, on the compare band and the alert button. Nothing else is coloured.
5. **Honesty is visible.** "Paid link" sits under every paid button in `fine`. Sponsored rows carry a chip and never move up. A seller without a named pharmacy gets a grey chip, not a green one.
6. **Plain words.** Labels use the words people type into Google: "Where to buy", not "Providers". "Is it legal?", not "Regulatory status". No all-caps labels, no abbreviations without the plain name next to them.

## Clinical paper (the medical look, decided 30 Oct 2026)

The site is about medicine, so its paper looks like a clinic's paper, not like a software dashboard. The cues, and only these:

- **The price pad.** The hero board is drawn as a clinic notepad: a `white` sheet on journal paper with a 2px `ink` border, an ℞ mark in `display` 600 next to the title, a 4px double rule under the head, the price in `number-xl` with the `mark` bar under it, ledger rows on 1px lines, a rotated "Checked <date>" stamp in `action-text` outline, a dashed tear line at the bottom. It always says "Not a prescription." in `fine`. It replaces the dark ink board everywhere (Home hero, category hero).
- **The body figure.** Our own flat silhouette, one continuous outline in `ink-2` (1.5px) over a `neutral-tint` fill, with dots: `paper` with a 2px `ink` border, the active one `mark` with a `mark` ring. Like an intake form's "where does it hurt". Never a stock photo, never an anatomical illustration with organs.
- **Chips as lab labels.** Status chips stay small, square-cornered and factual, like labels on a sample.
- **Stamps for dates.** A date the site checked something may be shown as the stamp above; everywhere else dates are plain `small` text.

Not allowed: fake documents (anything that could pass as a real prescription, lab report or letter), stock doctors, pills or syringes as decoration, caduceus or cross icons, handwriting fonts, script signatures. The two typefaces and the colour tokens change only through this book.

## Motion (decided 30 Oct 2026, medical journal direction)

Motion confirms; it never entertains. Everything plays once and then the page is still. GSAP 3.12.5 from cdnjs (with ScrollTrigger) runs the figure and the scroll reveals; the price pad plays in CSS so the price never waits for a script. Durations are the `motion-*` tokens.

| What | Trigger | Move | Time |
|---|---|---|---|
| Price pad (CSS) | page load | rows and hero number rise 8px and fade in, 60ms apart | `motion-base` (280ms) |
| Highlighter under the hero number (CSS) | page load, after the number | the `mark` bar draws from left to right | `motion-reveal`, 260ms delay |
| "Checked" stamp (CSS) | page load, last | lands from 1.15 scale to its -2° resting angle | 320ms, 650ms delay |
| Body figure (GSAP) | first time it scrolls into view (at once if already visible) | the outline draws itself, then the fill fades in under it | `motion-draw` (1.5s) |
| Active body dot (CSS) | on choosing a goal | a `mark` ring pulses outward, twice, then still | 600ms |
| Goal panel (GSAP) | on choosing a goal | old panel fades out, new one fades in | 120ms out, 200ms in |
| Section headings, table rows, criteria, creators, trust row (GSAP) | scrolled into view, once | rise `motion-rise` (12px) and fade in, `motion-stagger` (50ms) apart | `motion-reveal` (420ms) |

Fallbacks: things are pre-hidden only while `html.motion` is set, which a small head script sets when reduced motion is off. If GSAP has not started within 3s (blocked or slow), the class is removed and everything shows. With `prefers-reduced-motion: reduce` or JavaScript off, the page shows its final state at once. Nothing loops, nothing moves on hover except colour, nothing shifts layout (transforms and opacity only). Not used: Three.js, WebGL, video, parallax.

## Page anatomy

- **Notice bar** (`paper-2`, 40px, `small`): one sentence on what we are and how we earn, with a link.
- **Header** (76px, 2px `ink` rule under it): wordmark in `font-brand` 800, five nav items (44px tall), one primary button. Nav never wraps; on phones it scrolls.
- **Hero**: H1 in `display-1`, lede, the category buttons. Landing: 7 + 5 columns with the price pad on the right. Article pages: title left, hero number right, 2px rule under both.
- **Sections** on landing pages: `space-9` apart, each opened by a section heading like a journal's running head: 2px `ink` rule above, H2 in `display-2`, one-sentence lede, 1px `line` under it, "All X" link on the right.
- **Tables**: journal tables, 2px `ink` rule above the header row and under the last row, 1px `ink` under the header, `line` between rows; prices in `number-l` with even-width figures.
- **Article pages**: 8-column body with `body` text at 64ch, H2 in `display-3` above a 2px rule, 4-column sticky sidebar with the decision card first.
- **Footer** (`ink`): wordmark and the one-line disclaimer.

## Colour usage rules

| Need | Token |
|---|---|
| Text | `ink`; secondary `ink-2`; on dark `ink-on-dark` |
| Backgrounds | `paper` (warm journal paper); alternate bands `paper-2`; sheets on paper (price pad, goal panel) `white`; dark panels `ink` (footer only since 30 Oct 2026) |
| Approved, named, verified | `action-tint` + `action-text` |
| Waiting, sponsored, partial | `warn-tint` + `warn-text` |
| Prescription, compounding | `info-tint` + `info-text` |
| Not shown, not approved, neutral | `neutral-tint` + `ink-2` |
| The key number | `mark` behind it, `ink` text |

## Shape (decided 28 Oct 2026)

- **Near-sharp.** 4px on buttons, inputs, the price pad, the yellow compare band and the alert band; 2px on chips. No 8–16px rounding anywhere.
- Hierarchy still comes from the highlighter mark, 2px ink rules, double rules and the price pad's border, not from rounding or shadows. Master 2 goes fully square (0px) with sharp white panels, which keeps the two sites apart.

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
| 30 Oct 2026 | Wide screens: two frame steps (1480px from 1600px, 1720px from 2200px) with scaled type; checks at 1920 and 2560. Clinical paper: the dark board becomes the ℞ price pad, medical cues listed, fake documents and clip art banned | ODOBRENO DIZAJN - Karlo - 30. 10. 2026. |
| 30 Oct 2026 | Direction A, "Clinical paper, finished": Home hero number is the price (pages.md), pad under the H1 on phones, motion budget, tap targets 44px on phones (dots, nav, header button), shadows removed from the active dot and cookie bar, stamp in sentence case (no uppercase labels) | ODOBRENO DIZAJN - Karlo - 30. 10. 2026. |
| 30 Oct 2026 | Medical journal direction: display face Newsreader (wordmark stays Bricolage), warmer palette (paper, ink, hairlines; green deepened, all text 6:1 or better), type scale and motion tokens, journal section heads and tables, notepad price pad with double rule, body figure redrawn as one outline, GSAP motion with fallbacks, in-table buttons 44px | waiting for Karlo |
