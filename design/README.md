# Master 1

The design system for Peptide Chooser (peptidechooser.com), the human peptide comparison portal: online clinics, prices, legal status.

**This book is the single source for every design decision on the site.** Every page, button, colour, size and spacing comes from here. Anything not in this book does not exist yet: it is proposed and added here first, then built. The site's CSS is generated from `tokens.json` and `components/bundle.css`. Layout and margin rules are in `layout.md`; what goes on each page type, and which button where, is in `pages.md`.

## Logo

The mark is a peptide chain: three green links ending in one yellow link, on an `ink` square with 4px corners (`assets/Logos`); it keeps its own colours. Next to it the name "Peptide Chooser" in Public Sans 800 (`font-brand`), in `ink` (on white) or `white` (on the ink footer). The mark is never redrawn, recoloured, rotated, shadowed or animated.

- `peptide-chooser-mark.svg`: on light backgrounds (header, favicon, social image).
- `peptide-chooser-mark-on-dark.svg`: paper square, for the ink footer and dark panels.
- Header: mark 30px tall, 10px gap to the name at 20px. Footer: mark 28px. Favicon: the mark alone. Smallest use 16px.
- Clear space around the mark and name: at least half the mark's height. Nothing else on that line except the nav.

## The job

The site compares; it never sells. Every visual choice serves one job: let a worried adult find the real price and a trustworthy clinic in under a minute, on a phone, and click Visit with confidence.

## Who it is for

US adults, mostly 30 to 55, comparing peptide and prescription treatments by goal: hair first (from October 2026), then skin, muscle, recovery, libido, energy and weight loss. They are price-anxious and legitimacy-anxious. They scan, they do not read. Most arrive from Google on a phone with one question: what does this cost, is it legal, where do I get it.

## The look: clinic intake (chosen 30 Oct 2026, "Option 1")

The site looks like a good clinic's online intake: clean white, calm clinical blue, plain type, and one chart where you point at the body and get the answer. Not a wellness brand, not a SaaS dashboard, not a journal.

## Principles

1. **The answer comes first.** Home opens on the evidence rail (31 Oct 2026): the body figure on the left and three numbered steps on the right (choose a goal, compare the options, get it), so the goal, its options with status and price, and the top pick are all in the hero. The price sits in a yellow pad on its option row.
2. **White cards on a pale band.** Hierarchy comes from white cards with 1px `line` borders on `paper` or `paper-2`, one 1.5px `ink` border on the category price pad, and a 2px `ink` rule above its price. The Home hero is a flat `paper-2` band; its option list is one white frame. No shadows on Home, no gradients anywhere.
3. **One typeface.** Public Sans, the US government's open typeface: plain, clinical and very legible. Weight does the work: 800 for headings and numbers, 600 to 700 for labels, 400 for reading.
4. **Blue is ours, green is paid, yellow is the choice.** `clinic` blue marks the site's own things: links, the evidence rail (line and step numbers), the body areas, focus rings. `mark` yellow on Home only marks the chosen goal chip, the chosen pin and the price pad. `action` green appears only on the paid Visit button (`btn-action`, with "Paid link" under it). Chips keep their status colours. Nothing else is coloured.
5. **Honesty is visible.** "Paid link" sits under every paid button in `fine`. Sponsored rows carry a chip and never move up. A seller without a named pharmacy gets a grey chip, not a green one.
6. **Plain words.** Labels use the words people type into Google: "Where to buy", not "Providers". "Is it legal?", not "Regulatory status". No all-caps labels, no abbreviations without the plain name next to them.

## Medical cues (only these)

- **The body figure** (redrawn 31 Oct 2026, traced from the evidence rail mockup: `mockups/body-figure.svg`). Our own front view as one closed outline, head included: `white` fill, `ink` stroke 7 units wide in its 980 by 2400 box (about 1.6px on screen). Each goal has a body area that shades in `clinic` blue, clipped to the outline (light on hover, stronger when chosen), and a pin: a white circle with an `ink` outline, filled `mark` when chosen. Areas: head top for hair, face for skin, shoulders for muscle, chest for energy and aging, belly for weight loss, pelvis for sex drive, knees for healing and joints. Pins and the goal chips are one control: choosing either updates both and the steps. Like a clinic's "where does it hurt" chart. Never a stock photo, never organs. Sticky beside the rail from 900px, hidden under 640px (the chips do the job). The outline and the areas live in `build.py` (`body_path`, `REGIONS`).
- **The evidence rail** (Home hero, 31 Oct 2026). A vertical 2px `clinic` line joining three 44px `clinic` circles with white step numbers (800, 18px). Each step is an H2 in `display-3` beside its circle; the content sits under the heading, indented to the line. Three steps only, always in this order: Choose a goal, Compare the options, Get it. Not a card: the steps sit on the band.
- **Goal chips** (step 1). One button per goal, 44px tall, `white` with a 1px `line-strong` border, 6px corners, `label` in 600 15px. The chosen one is filled `mark` with an `ink` border. They wrap on wide screens and sit in two columns on phones.
- **The option list** (step 2). One white frame, 12px corners, 1px `line` border, `line` between rows. A row: the name (700) and its `does` line; the status chip with the plain status under it; the price pad (where a price source exists) and the `how` line. One line of three columns on wide screens, three short lines on phones.
- **The price pad on an option row.** `mark` background, 4px corners, "from $X/mo" in 800 15px `ink`, with the source and its check date in `fine` under it, linked to the numbered source. Only on a row whose price has a source in data/site.json.
- **The answer panel as a prescription pad.** White card, 1.5px `ink` border, 12px corners, an ℞ mark top right, the title, then a 2px `ink` rule and the price. It always says "Not a prescription." in `fine`. Category pages use the same look for their price pad.
- **Chips as lab labels.** Small, 4px corners, factual.
- **The Checked stamp.** "Checked <date>" in a small `action-text` outline next to "options checked"; everywhere else dates are plain `small` text.

Not allowed: fake documents (anything that could pass as a real prescription, lab report or letter), stock doctors, pills or syringes as decoration, caduceus or cross icons, handwriting fonts, script signatures.

## Motion (updated 30 Oct 2026, clinic intake)

Motion confirms; it never entertains. Everything plays once and then the page is still. GSAP 3.12.5 from cdnjs (with ScrollTrigger) runs the goal change and the scroll reveals; the rail line and the stamp are CSS. Durations are the `motion-*` tokens.

| What | Trigger | Move | Time |
|---|---|---|---|
| Evidence rail line (CSS) | page load, once | the line between the step circles draws downward, segment by segment | `motion-draw` (600ms) |
| Checked stamp in step 2 (CSS) | page load, once, after the line | lands: fades in from 1.15 scale to 1 | `motion-base` |
| Goal chip and pin (CSS) | on choosing a goal | fill cross-fades to `mark` | `motion-swap` (200ms) |
| Body areas (CSS) | hover on a pin or a goal chip | the area shades lightly | `motion-quick` |
| Steps 2 and 3 (GSAP) | on choosing a goal | old content fades out, new content fades in, option rows rise 4px `motion-stagger` apart | `motion-swap` |
| Category price pad (CSS) | page load | rows rise 8px and fade in, 60ms apart | `motion-base` |
| Section headings, table rows, criteria, creators, trust row (GSAP) | scrolled into view, once | rise `motion-rise` (12px) and fade in, `motion-stagger` (50ms) apart | `motion-reveal` (420ms) |

Fallbacks: things are pre-hidden only while `html.motion` is set, which a small head script sets when reduced motion is off. If GSAP has not started within 3s, the class is removed and everything shows. With `prefers-reduced-motion: reduce` or JavaScript off, the page shows its final state at once. Not used: Three.js, WebGL, video, parallax.

## Page anatomy

- **Notice bar** (`paper-2`, 36px, `small`): one sentence on what we are and how we earn, with a link.
- **Header** (72px, white, 1px `line` under it): wordmark, five nav items (44px tall), one `btn-ink`. Nav never wraps; on phones it scrolls.
- **Home hero**: H1 and lede side by side, then the evidence rail beside the body figure, then the How we rate strip and the trust links (pages.md, Home).
- **Category hero**: H1 and short answer left, price pad right (7 + 5).
- **Sections** on landing pages: 72px apart, each opened by a section heading (H2 in `display-2`, one-sentence lede, 1px `line` under it, "All X" link on the right).
- **Tables**: a white card with 12px corners and a 1px `line` frame, a `paper-2` header row in 13px `ink-2`, `line` between rows; prices in `number-l`.
- **Lists of short items** (Top picks, glossary): white cards with 1px `line` borders in a grid. **How we rate on Home** is one strip: the heading, then the five criteria in a row, divided by 1px `line` rules, no cards.
- **Article pages**: 8-column body with `body` text at 64ch, H2 in `display-3` with a 1px `line` above, 4-column sticky sidebar with the decision card first.
- **Footer** (`ink`): wordmark and the one-line disclaimer.

## Colour usage rules

| Need | Token |
|---|---|
| Text | `ink`; secondary `ink-2`; on dark `ink-on-dark` |
| Backgrounds | `paper` (white); bands and the Home hero's lower edge `paper-2`; cards `white`; the footer `ink` |
| Links, chosen goal, body areas, focus | `clinic`; hover `clinic-hover`; chosen row `clinic-tint` + `clinic-text` |
| Paid Visit button only | `action` |
| Approved, named, verified | `action-tint` + `action-text` |
| Waiting, sponsored, partial | `warn-tint` + `warn-text` |
| Prescription, cosmetic, compounding | `info-tint` + `info-text` |
| Not shown, not approved, neutral | `neutral-tint` + `ink-2` |

Every text pair is 6.4:1 or better (ink-2 on paper-2 7.2:1, clinic on paper 6.7:1).

## Shape (updated 30 Oct 2026)

- **Soft but firm.** 6px on buttons, inputs, nav items and goal chips; 12px on cards (option list frame, category price pad, table frames, top picks, glossary); 4px on chips and the Home price pad; step circles and pins are round.
- No card holds a card.

## What not to do

- No uppercase labels above headings. The heading is the label.
- No middle dots between facts. Use commas or separate lines.
- No icons in buttons. Words do the work.
- No cards inside cards.
- No "→" at the end of links.
- No green except the paid button and approved chips.

## Content rules (added 28 Oct 2026)

- **No placeholders in public.** A page ships with real data or with an honest empty state ("No reader reviews yet. Used Henry Meds? Your review is published as written."). Never "[Dr. Name]" or "[N]".
- **Reviewer line.** Until a named medical reviewer exists, the standfirst says "Every claim links to its source. Prices checked <date>." Add a named reviewer only when the person and credentials are real.
- **Creators.** Only group A from the YouTube research (DeLauer, Williamson, Stillson MD). Group B needs a conflict-of-interest label; group X is never shown.
- **Sources block.** Every peptide and clinic page ends with a numbered "Sources" list: FDA label, FDA policy page, court filing or study, each with the date it was current.
- **Notice bar on phones.** Keep only the first sentence; the "How we make money" link moves to the footer trust row.

## Components

Each component below has a guideline and a live preview. The CSS in `components/bundle.css` is the single source for buttons, chips, tables and section headings: change a token or a class there and every page follows.

Built and previewed: Button, Chip, DataTable, Price, SectionHeading. Built on the site, preview owed here: PricePad (the ℞ board), EvidenceRail (figure, goal chips, option list, top pick), LegalTable, CreatorList, TrustRow, CookieNotice. Defined in `pages.md` and built in phase 2 before any content page ships: Header, NoticeBar, Footer, Breadcrumbs, ShortAnswer, DecisionCard, ProductRow, SourcesList, AuthorLine, CookieNotice. Each gets its README and preview here first.

## Changes

| Date | Change | Approved |
|---|---|---|
| 28 Oct 2026 | First version: tokens, brand book, five components, cover | Karlo |
| 30 Oct 2026 | Logo added; `layout.md` (margins, no overflow) and `pages.md` (page types, which button where) added; audience widened to goal categories, hair first | ODOBRENO DIZAJN - Karlo - 30. 10. 2026. |
| 30 Oct 2026 | Home rebuilt from the 26 Oct mockup (body map, legal table, creators, trust row); nav by section | Karlo: „ajmo sve 4” |
| 30 Oct 2026 | Wide screens: two frame steps (1480px from 1600px, 1720px from 2200px) with scaled type; checks at 1920 and 2560. Clinical paper: the dark board becomes the ℞ price pad, medical cues listed, fake documents and clip art banned | ODOBRENO DIZAJN - Karlo - 30. 10. 2026. |
| 30 Oct 2026 | Direction A, "Clinical paper, finished": Home hero number is the price (pages.md), pad under the H1 on phones, motion budget, tap targets 44px on phones (dots, nav, header button), shadows removed from the active dot and cookie bar, stamp in sentence case (no uppercase labels) | ODOBRENO DIZAJN - Karlo - 30. 10. 2026. |
| 30 Oct 2026 | Medical journal direction: display face Newsreader (wordmark stays Bricolage), warmer palette (paper, ink, hairlines; green deepened, all text 6:1 or better), type scale and motion tokens, journal section heads and tables, notepad price pad with double rule, body figure redrawn as one outline, GSAP motion with fallbacks, in-table buttons 44px | ODOBRENO DIZAJN - Karlo - 30. 10. 2026. |
| 30 Oct 2026 | Look changed to "Clinic intake" (Option 1 of five mockups in `mockups/`, chosen by Karlo): white and clinical blue, Public Sans, the chooser (body chart, goal list, answer panel with the price) moved into the Home hero so the figure is never cut, new body chart with shaded areas and pins, cards for tables and lists, links blue, green only for the paid button | ODOBRENO DIZAJN - Karlo - 30. 10. 2026. |
| 31 Oct 2026 | Home hero becomes "the evidence rail" (owner's mockup `mockups/evidence-rail.png`): body figure redrawn from `mockups/body-figure.svg` with new areas and a yellow chosen pin, three numbered steps on a clinic-blue rail (goal chips, option list with the price pad, top pick with Visit), How we rate as one strip with the trust links in the hero band; hero gradient and chooser card removed; motion tokens `motion-draw` 600ms (rail line) and `motion-swap` 200ms | Proposed; waiting for ODOBRENO DIZAJN |
