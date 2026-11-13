# Navigation and data parts for the new page types

Index: [`design/pages.md`](../pages.md). Owner queue block 6, steps 3 and 3A (8 Nov 2026; ODOBRENO DIZAJN - Karlo - 8. 11. 2026 - PR #142). Every page type in `docs/site-map-rules-2026-11-08.md` is built from these parts and the parts already in this book; nothing here adds a colour, a font or a radius.

## Breadcrumb (every page except Home; site map rules 4.1)

The look the site already draws (`.crumbs` in `assets/site.css`), written down as one part:
- **Where:** the first line inside the page frame, above the H1, 16px from the header; the side padding is the frame's, so the trail lines up with the page text.
- **Look:** `small` (14px) in `ink-2`; links in `ink-2` with the site's underline on hover and focus; a "/" between items with 6px each side, `aria-hidden`. The last item is the page itself, plain text, `aria-current="page"`. No icon, no chevron, no home glyph.
- **Trail:** the parent chain of the page's type in the site map (section 1), never a shortcut: Home / Sellers / <Seller> / <Substance>; Home / Peptides / <Substance> / <Brand>; Home / <Goal> / <Topic>; Home / <Group>; Home / Labs / <Lab>; Home / FDA warning letters / <Company>; Home / Tools / <Tool>. Names are the display names the page's H1 uses, without brackets.
- **Phones (under 640px):** one line. When the trail does not fit, the items between Home and the parent fold into "…" (a link to the parent's parent), and a long last item ends in an ellipsis; nothing wraps, nothing scrolls sideways (`tools/check_layout.js`).
- **Markup:** `<nav class="crumbs" aria-label="Breadcrumb">` with an `<ol>`; BreadcrumbList JSON-LD with the same items in the same order, the last one with its own URL.
- **Checks** (to add when the first new type is built): every page but Home has the trail; the visible items and BreadcrumbList match; every link in the trail returns 200 in the build.

## Filter look (every list page; site map rules 3.7)

One look for every list that can be narrowed (/sellers/, /peptides/, /fda-warning-letters/, a group page, /labs/, /tools/), built from the Letters filter and Filter toolbar parts in `bundle.css`:
- **Row:** labelled controls on one row from 900px, `space-3` apart: "Filter by name" (input with `btn-line btn-sm` "Clear" inside it), then at most three labelled selects (label above in `small` 600 `ink`, control 44px, `radius-control`, `line-strong` border), then one segmented control when the list has two kinds (`seg`, `seg-b`, `aria-pressed`).
- **Chips:** toggles in the year-chip part, each with its count in tabular figures ("No FDA letter 41"); a chip with count 0 stays, disabled, so the row never jumps. **Disabled look:** no fill (the band shows through), a 1.5px `line` border in place of `line-strong`, name and count in `ink-muted`, no hover, default cursor; it carries the `disabled` attribute, so it is skipped by Tab and announced as unavailable.
- **Count line:** "N of M shown." in `small` `ink-2` right under the row, `aria-live="polite"`; "Clear filters" as a text link beside it once anything differs from the default.
- **Empty result:** the table area says "Nothing matches these filters." and the "Clear filters" link; never an empty table frame.
- **State:** only in the URL hash, only values that differ from the default, written with `replaceState`. A filter never makes a new path or query string, the canonical never changes, and no filtered state is in the sitemap (rule 3.7).
- **Without JavaScript:** the controls are hidden and every row shows.
- **Phones and wide screens on /sellers/ and /peptides/:** the Filter toolbar below (it replaces the Filter fold, 13 Nov 2026).

## Filter toolbar, layout A (/sellers/, /peptides/; owner pick 13 Nov 2026, w4 mock-up; waits for ODOBRENO DIZAJN)

- **One row** (`cf-bar`, `space-3` apart): the tabs or the "Show" chips, "Filter by name" (label for screen readers only, placeholder "Filter by name", "Clear" inside the field), "Sort" with its label inline, and a `btn-line` "Filters" with the number of filters on in an ink badge (22px, `radius` 11px, 13px 700 white); the count line right-aligned. While open the button shows `aria-expanded="true"` and turns `clinic-tint`, `clinic` border, `clinic-text`.
- **Panel** (`cf-panel`, opens under the row): `paper-2`, 1px `line` border, `radius-panel`, 16px padding; the selects (Substance, Your state, Minimum checks) in three columns from 641px, one below; each chip group on its own line.
- **Filters that are on** (`cf-pills`, under the row): one pill each, `clinic-tint`, 1.5px `clinic` border, `radius-chip`, 44px high (layout.md, Touch), 14px 700 `clinic-text`: a select as "<its label>: <value>", a chip by its name, then the word "remove" (400, underlined; no x icon). From two pills, "Clear all" as a text button. Removing moves focus to the next pill, else to "Filters".
- **Phones (640px and under):** tabs full width; the search full width with "Clear" beside it (44px); Sort and "Filters" side by side; the count line under them; the panel opens in place, one column.
- **/peptides/:** no name search; the "Show" chips stay in the row, "Sold as" and "Form" go in the panel.
- **Without JavaScript:** the row's controls and the panel are hidden and every row shows, as before.

## Select (every select on the site)

`appearance: none`; the option rows' chevron (2.5px `ink` stroke) drawn 16px, 12px from the right edge; 40px right padding; 44px minimum height.

## Lab mark (substance, seller, seller offer and lab pages)

A lab-label chip for a lab report (COA) we hold, in the chip family (4px corners, at least 24px tall, 12px 700):
- **Look:** `white` fill, 1px `ink` border, `ink` text: "Lab report · <Lab> · <Mon YYYY>" (the newest report's lab and test date). No tick, no percentage, no "pure", "tested" or "verified": the chip states that a report exists, never what it proves.
- **Link:** to /labs/<lab>/ when that page is indexed, else to the report's own source as text with its date (no link to a shop's domain, the existing rule).
- **Where:** a shop row's Checks cell on the substance page and the seller page, the offer page's first screen, and every row of a lab page. A listing without a report shows nothing (the seller's "Lab reports" mark already says so).
- **Never** on a clinic row: clinics publish no lab reports (sellers-list.md).
- **Classes** (`bundle.css`, Lab mark; w2 task 24, PR #151): `.chip-lab`.

## Price history (substance and seller offer pages; data task 1g)

One small chart of a price over time, from the price-history view only:
- **Shown only when** the series has at least 3 checks over at least 60 days; otherwise the block is left out (no "coming soon").
- **Look:** an inline SVG, the content width, 160px tall (120px under 640px): a step line, 1.5px `clinic`, on `white`; three `line` hairlines (low, middle, high) with their prices in `small` `ink-2` at the left; months along the bottom in `small`; the newest point a 6px `clinic` dot labelled "$X/mg, <date>" (or "$X/mo"). No area fill, no gradient, no animation, no tooltip needed to read it.
- **Heading:** h3 at display-4, "Price over time", with one `small` line under it: what the price is (lowest per mg at <Shop>, or <Clinic>'s <Plan> per month) and "Checked <dates>".
- **Table twin:** under the chart a `details` "Prices as a table" with the same points (date, price, source), so the numbers never rest on the drawing alone; the SVG has `role="img"` and an `aria-label` that says the first and last price and the dates.
- **Classes** (`bundle.css`, Price history; w2 task 24, PR #151): `.price-hist` (the SVG), `.ph-hair` (hairlines), `.ph-step` (the line), `.ph-dot` (the newest point), `.ph-label` (prices and months), `.ph-now` (the newest label). The build writes classes only, never inline style (check-parts).
- **Numbers from data, never typed:** every point comes from the view with its check date; a gap stays a gap.
