# Master 1

The design system for Peptide Chooser (peptidechooser.com), the human peptide comparison portal: online clinics, prices, legal status.

**This book is the single source for every design decision on the site.** Every page, button, colour, size and spacing comes from here. Anything not in this book does not exist yet: it is proposed and added here first, then built. The site's CSS is generated from `tokens.json` and `components/bundle.css`. Layout and margin rules are in `layout.md`; what goes on each page type, and which button where, is in `pages.md`.

Logo, the medical cues and page anatomy are in `pages/parts.md` and `pages/every-page.md`. Every change is in `CHANGELOG.md`.

## The job

The site compares; it never sells. Every visual choice serves one job: let a worried adult find the real price and a trustworthy clinic in under a minute, on a phone, and click Visit with confidence.

## Who it is for

US adults, mostly 30 to 55, comparing peptide and prescription treatments by goal: hair first (from October 2026), then skin, muscle, recovery, libido, energy and weight loss. They are price-anxious and legitimacy-anxious. They scan, they do not read. Most arrive from Google on a phone with one question: what does this cost, is it legal, where do I get it.

## The look: clinic intake (chosen 30 Oct 2026, "Option 1")

The site looks like a good clinic's online intake: clean white, calm clinical blue, plain type, and one chart where you point at the body and get the answer. Not a wellness brand, not a SaaS dashboard, not a journal.

## Principles

1. **The answer comes first, read left to right.** Home opens on the flow (owner decision 31 Oct 2026): one white card that reads from left to right: 1 the body figure and the goal list, 2 the chosen goal's options with status, price and where to get them; the top pick's row carries the Visit button. The price is `ink` figures on its option row.
2. **White cards on a pale band.** Hierarchy comes from white cards with 1px `line` borders on `paper` or `paper-2`, one 1.5px `ink` border on the category price pad, and a 2px `ink` rule above its price. The Home first screen is `white` with no card around the flow (owner, 31 Oct 2026); its option list is one white frame with a 1px `line` border, and the grey `paper-2` band starts where the first screen ends. No shadows on Home. No gradients anywhere.
3. **One typeface.** Public Sans, the US government's open typeface: plain, clinical and very legible. Weight does the work: 800 for headings and numbers, 600 to 700 for labels, 400 for reading.
4. **Blue is ours, green is paid.** `clinic` blue marks the site's own things: links, the step numbers, the chosen goal row, the body areas and pins, focus rings. `action` green appears only on the paid Visit button (`btn-action`, with "Paid link" under it). Chips keep their status colours. No yellow on Home (owner, 31 Oct 2026). Nothing else is coloured.
5. **Honesty is visible.** "Paid link" sits under every paid button in `fine`. An FDA letter alone does not block a paid link and stays visible next to every price; a research-use shop, and a seller whose letter is about adulterated drug products with no close-out letter, get none (pages.md, the paid link rule). Sponsored rows carry a chip and never move up. A seller without a named pharmacy gets a grey chip, not a green one.
6. **Plain words.** Labels use the words people type into Google: "Where to buy", not "Providers". "Is it legal?", not "Regulatory status". No all-caps labels, no abbreviations without the plain name next to them.

## Medical cues (only these)

The cues, each with its rules, are in `pages/parts.md`, Medical cues.

Not allowed: fake documents (anything that could pass as a real prescription, lab report or letter), stock photos, except the goal photos (parts.md), stock doctors, pills or syringes as decoration, caduceus or cross icons, handwriting fonts, script signatures.

## Motion (updated 30 Oct 2026, clinic intake)

Motion confirms; it never entertains. Everything plays once and then the page is still. GSAP 3.12.5 from cdnjs (with ScrollTrigger) runs the goal change and the scroll reveals; the rail line and the stamp are CSS. Durations are the `motion-*` tokens.

| What | Trigger | Move | Time |
|---|---|---|---|
| Body figure (GSAP) | on choosing a goal, and back | the view moves to the goal's part of the body, ease out, plays once and stays still; no idle rotation | `motion-zoom` (700ms) |
| Body figure close-up and glow (CSS) | when the zoom lands | the sharp close-up and the glow fade in over the same picture; its pin fills blue | `motion-swap` |
| Checked stamp in column 2 (CSS) | page load, once | lands: fades in from 1.15 scale to 1 | `motion-base` |
| Goal row (CSS) | on choosing a goal | background cross-fades to `clinic-tint` | `motion-quick` |
| Pin (CSS) | hover on a pin or a goal row | the ring tints | `motion-quick` |
| Column 2 (GSAP) | on choosing a goal | old content fades out, new content fades in, option rows rise 4px `motion-stagger` apart | `motion-swap` |
| Category price pad (CSS) | page load | rows rise 8px and fade in, 60ms apart | `motion-base` |
| Section headings, table rows (tables of up to 25 rows; a longer data table shows at once, 2 Nov 2026), criteria, creators, trust row (GSAP) | scrolled into view, once | rise `motion-rise` (12px) and fade in, `motion-stagger` (50ms) apart | `motion-reveal` (420ms) |

Fallbacks: things are pre-hidden only while `html.motion` is set, which a small head script sets when reduced motion is off. If GSAP has not started within 3s, the class is removed and everything shows. With `prefers-reduced-motion: reduce` or JavaScript off, the page shows its final state at once. Not used on the page: Three.js, WebGL, video, parallax (the body figure's 3D runs only offline, when its images are made). With reduced motion the figure swaps straight to the close-up; with JavaScript off it stays the full figure.

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

- **Soft but firm.** 6px on buttons, inputs, nav items and goal rows; 12px on cards (option list frame, category price pad, table frames, top picks, glossary); 4px on chips and the Home price pad; step circles and pins are round.
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

**Scores** (owner decision C9, 3 Nov 2026): a shop is checked on five facts and shows "N of 5"; an online clinic publishes no lab reports, is checked on four and shows "N of 4". A score is never compared across the two kinds (pages.md, Seller). Waits for ODOBRENO PRAVILA.

## Components

Each component below has a guideline and a live preview. The CSS in `components/bundle.css` is the single source for buttons, chips, tables and section headings: change a token or a class there and every page follows.

Built and previewed: Button, Chip, DataTable, Price, SectionHeading. Built on the site, preview owed here: PricePad (the ℞ board), Flow (body chart, goal list, option list, top pick), LegalTable, CreatorList, TrustRow, CookieNotice. Defined in `pages.md` and built in phase 2 before any content page ships: Header, NoticeBar, Footer, Breadcrumbs, ShortAnswer, DecisionCard, ProductRow, SourcesList, AuthorLine, CookieNotice. Each gets its README and preview here first.

## Changes

See `CHANGELOG.md`, newest row first.
