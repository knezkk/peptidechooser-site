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
5. Buttons: label at most 24 characters. Full width under 640px (except `btn-sm` in tables). A button row wraps onto a new line rather than overflow.
6. Header nav never wraps; on phones it becomes one row that scrolls inside itself. The wordmark never shrinks below the 16px mark.
7. Headings use the phone sizes from `tokens.json` under 640px (`display-1` 32px, 28px in the Home hero; `display-2` 26px; `display-3` 22px; `number-xl` 48px).
8. No element is positioned outside the container (no negative margins, no absolute elements past the edges). Sticky only for the article sidebar, from 900px up.

## Touch

Every control is at least 44px tall: nav items, the header button, in-table `btn-sm`, cookie buttons, goal rows. Body pins have a 48-unit hit circle; the goal list beside the figure is the full-size control for the same choice.

## Vertical spacing

Only spacing tokens. Between landing sections `space-9` (56px on phones). Home first screen 28px top, 32px bottom (12px and 24px on phones), 16px between the H1 and the flow (12px on phones); the grey band after it 32px top, 56px bottom (24px and 40px on phones), 48px above the How we rate strip; category hero 56px. H2 in articles: `space-8` above. Inside panels `space-5`. Nothing else.

## Checks before every release

Run headless Chrome (Playwright) at 320, 390, 768, 1024, 1440, 1920 and 2560px wide on every page type:

- `document.documentElement.scrollWidth` must equal the window width (no sideways scroll).
- No element's right edge past the container's padding, except inside `.tbl-wrap`.
- Screenshots at 390, 1440 and 2560 are looked at, and sent to Karlo with any new page or any design change.
- Lighthouse on mobile: 90+ on Performance, Accessibility, Best Practices and SEO.

A page that fails any check does not ship.
