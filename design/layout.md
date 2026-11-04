# Layout and margins

Nothing on any page may leave its margins or push the page sideways, at any screen width from 320px to 2560px (a 32-inch monitor). These rules make that true by construction; the checks at the end prove it before every release.

## The frame

- **Container:** max width `container` (1180px), centred. Side padding 24px; 16px under 640px. All content sits inside the container.
- **Wide screens grow in two steps, then stop (30 Oct 2026).** From 1600px the frame is `container-wide` (1480px, 32px padding) and type scales up (H1 50px, section H2 36px, body 17px, `number-xl` 64px, body figure 480px tall); from 2200px it is `container-max` (1720px, 40px padding) and type scales up again (H1 56px, section H2 40px, body 18px, `number-xl` 70px, body figure 540px tall). Grids keep their proportions. The Home body figure is 190px tall under 900px and 372px from 900px. Nothing grows past 1720px: a 4K screen shows the same frame as a 32-inch one, centred. A page is never a 1180px island on a wide screen.
- **Full-bleed is background only.** Bands (`paper-2`), the ink footer and the notice bar may run edge to edge, but their content sits in a container inside them.
- **Grid:** `columns` (12). Gap `space-6` (32px) on desktop, `space-4` (16px) under 640px. Article pages 8 + 4; landing hero 7 + 5. Under 900px the sidebar drops below the article; under 640px everything is one column.
- **Breakpoints, only these:** 480px (small phone), 640px (phone: the Home figure is 230px tall beside the goal list, goal counts hide), 760px (two-column lists), 900px (sidebar and two-column layouts start; the Home flow puts the figure, the list and the options side by side), 1100px (Home option rows go to one line of three parts; the How we rate strip goes to one row), 1180px (container reaches full width), 1600px (wide), 2200px (max). No others.

## Nothing overflows

1. Every grid or flex child has `min-width: 0`, so long content shrinks instead of pushing.
2. Text breaks: `overflow-wrap: anywhere` on headings, table cells and chips, so long words, URLs and product names wrap.
3. Images, SVG and video: `max-width: 100%`, `height: auto`. No fixed pixel widths on content blocks; only the container has a max width.
4. Tables never shrink below readable: the ranking table lives inside `.tbl-wrap`, which scrolls sideways inside itself. The page never scrolls sideways.
5. Buttons: label at most 24 characters (the option row's "Buy from $X/mo · N clinics" is the one exception; it fits `cta-width`). Full width under 640px (except `btn-sm` in tables). A button row wraps onto a new line rather than overflow.
6. Header nav never scrolls sideways (owner task 3 Nov 2026): from 1180px it is one row, logo, the five categories, the search field and "Find a seller", and the header row is 68px tall; an open category is a floating card under its item (positioned, so nothing moves; at least 24px inside the container's right edge, never past its left edge; the same pixel width at 1440, 1920 and 2560px, never wider than the container; owner task 3 Nov 2026); under 1180px the categories sit behind the "Menu" button as an accordion (the search field stays on the first row from 760px, inside the Menu below) and, with JavaScript off, show open under the logo (pages.md, Every page, Header). No breakpoint beyond the list above: the header uses 1180px and 760px. The wordmark never shrinks below the 16px mark.
7. Headings use the phone sizes from `tokens.json` under 640px (`display-1` 32px, 28px in the Home hero; `display-2` 26px; `display-3` 22px; `number-xl` 48px).
8. No element is positioned outside the container (no negative margins, no absolute elements past the edges). Sticky only for the article sidebar and the seller page's right column (the Background check card and Similar sellers; owner task 3 Nov 2026), from 900px up.

## Touch

Every control is at least 44px tall: nav items, the header button, in-table `btn-sm`, cookie buttons, goal rows. Body pins have a 48-unit hit circle; the goal list beside the figure is the full-size control for the same choice. **Exceptions** (owner task w2, 3 Nov 2026, phone finding 9): a footnote number (`sup a`) is at least 24px tall, the WCAG 2.5.8 minimum (it sits inside a line of text and a 44px target would push the lines apart); a link inside running text follows the text's line; a Chip is at least 24px tall (README, Chips). `tools/check_layout.js` checks the 44px rule at 390px on every page with these exceptions (w3's phone check, on by default since #75; the earlier `TAP=1` switch is gone).

## Text

Body text runs at most 80 characters a line (owner task w2, 3 Nov 2026): `max-width: 58ch` on prose paragraphs and list items (guides, trust pages), the goal page intro, the seller page's short answer and notes, the legit closing line and the /sources/ entries; Public Sans sets about 1.37 characters per `ch`, so 58ch measures 73 to 77 characters at 1440px (72ch would measure about 98). Not tables, cards or the header. Headings, ledes, paragraphs, list items and table cells wrap with `text-wrap: pretty` where the browser has it, so a last line is never one word; no script.

**Phones (owner task 3 Nov 2026, the 390px walkthrough; waits for ODOBRENO DIZAJN):**
- At 390 by 844, every control is at least 44px tall: the header logo, "Search" and "Menu", the breadcrumbs, the footer links, a section heading's link, "Read the full method →" style links, the letter cards' "FDA letter", the names heading a comparison table, the "Jump to" links.
- Three things may be smaller:
  - a link inside a line of text;
  - a footnote number (24 by 24px, WCAG 2.5.8; its tap areas may touch the next number's);
  - an FDA letter chip link in a line of text (at least 24px).
- No text under 13px on a phone: chips, the seller score marks and the Checked stamp are 13px under 640px. Footnote numbers and visually hidden text are the exceptions, and so is a seller tile's monogram, which is a picture hidden from screen readers (owner package 4 Nov 2026).
- No two controls overlap.
- `tools/check_layout.js` checks all of it on every page at 390px, as a returning visitor (the cookie bar answered).
- The header on phones holds the logo, "Search" and "Menu" in one row from 375px. Under 375px "Search" is not drawn; the field stays in the menu.

## Vertical spacing

**Home, landing v3 (owner package 4 Nov 2026; ODOBRENO DIZAJN - Karlo - 4. 11. 2026):** between Home's sections `space-7` (48px) at every width from 641px, `space-6` (32px) on phones; no footer margin after the last section. This replaces the larger values below for those sections. Section intros run at the 80-character measure in `ui-size`. The seller table (`tbl-where`) has rows of 68px from 641px (the table button, pages.md, Buttons; owner task 4 Nov 2026, waits for ODOBRENO DIZAJN). The body figure draws one path three times with `<use>`, so Home stays under its limit. On phones the first screen no longer holds every option: each option now has a full-width button (owner package, A2).

Only spacing tokens. Between landing sections `space-9` (56px on phones). Home first screen 28px top, 32px bottom (12px and 24px on phones), 16px between the H1 and the flow (12px on phones); the grey band after it 32px top, 56px bottom (24px and 40px on phones), 48px above the How we rate strip; category hero 56px. Goal page (owner task 3 Nov 2026, UX audit 11.2 and 12): the first screen 24px top and `space-7` (48px) bottom, the decision cards `space-5` (24px) under the intro and `space-4` (16px) apart; every section after it `space-7` (48px) top and bottom, the grey bands the same; the H2 + lede + divider pattern only where the lede says something (else the H2 alone, 16px above its content); `tbl-compact` rows 40px. Targets at 1440 by 900: /weight-loss/ under 5 screens with the clinic table starting within the second, /hair/ under 3. Seller page (owner task 3 Nov 2026): top block 24px top and 32px bottom, sections `space-7` (48px) apart with a hairline between (owner answer 3 Nov 2026: 48px, no 40px token), the two columns `space-6` apart. H2 in articles: `space-8` above. Inside panels `space-5`. Nothing else.

## Checks before every release

Run headless Chrome (Playwright) at 320, 390, 768, 1024, 1440, 1920 and 2560px wide on every page type:

- `document.documentElement.scrollWidth` must equal the window width (no sideways scroll).
- No element's right edge past the container's padding, except inside `.tbl-wrap`.
- Screenshots at 390, 1440 and 2560 are looked at, and sent to Karlo with any new page or any design change.
- Lighthouse on mobile: 90+ on Performance, Accessibility, Best Practices and SEO. `tools/check_lighthouse.js` runs it in the deploy on Home, /weight-loss/ and one seller page (one run per page; a page under 90 gets two more and the median counts); a page under 90 fails the deploy. /search/ is `noindex` on purpose, so its SEO score stays at 69: the known exception (owner task 4 Nov 2026).

A page that fails any check does not ship.
