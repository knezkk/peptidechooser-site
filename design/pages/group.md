# Group pages and goal subpages

Index: [`design/pages.md`](../pages.md). Owner queue block 6, step 3a (8 Nov 2026; ODOBRENO DIZAJN - Karlo - 8. 11. 2026 - PR #142; every visible word, title and H1 waits for ODOBRENO SEO). Page types and Google rules: `docs/site-map-rules-2026-11-08.md`, section 1. Breadcrumb and filter look: [nav-parts.md](nav-parts.md).

## Group page `/<group>/`

Substances grouped by approval, route or class. A group page is made only when it passes its Google rule (a measured search, at least 6 of the top 10 match the format); the format, list or guide, follows that check. No goal colour, no goal drawing, no body figure: a group is not a goal.

**Which layout** (owner, 8 Nov 2026): guide layout for /fda-approved/, /prescription/ and /injections/; list layout for /supplements/, /topical/ and /bioregulators/. A later group takes the layout its Google check shows.

### List layout (/supplements/, /topical/, /bioregulators/)
- **Top** (white): breadcrumb Home / <Group>; H1; the author line; the short answer as the `lede` (two sentences: what the group is, and what is and is not approved in it); a facts pad right from 900px (7 + 5), the price pad's frame (`white`, 1.5px `ink` border, `radius-panel`): the number of substances in the group, how many are FDA approved, and the "Checked <date>" stamp. Counts come from data; the H1 and title never carry them (site map rules 5.3).
- **The substances** (`paper-2` band): the /peptides/ A to Z table filtered to the group (Substance, Status chip, What it means, Lowest price), with the filter look (name, status chips, sort). Each name links to its substance page; a thin (noindex) substance shows as plain text (cross-links only to indexable pages, rule 4.3).
- **Where to buy, by kind** (white, only for a group with sellers): the Sellers list's two tables cut to the group's substances, the tab control on top (Online clinics, Research-use shops, and Supplements once /sellers/ has that group, sellers-list.md). Buttons by the paid link rule: a clinic's paid `btn-action` "Visit <Name>" or `btn-wait` "See plans"; a supplement shop's link only on a cosmetic product row; a research-use shop never.
- **Guides** (white): up to five guides on the group's substances, as text links between hairlines (the Related guides part).
- **What to do next** and **Sources** as on the goal pages.
- **Schema:** ItemList of the substances (as /peptides/) and BreadcrumbList.

### Guide layout (/fda-approved/, /prescription/, /injections/)
- The Guide template (learn.md, Guide) with its short answer card, prose H2s phrased as the questions people type and the optional Questions part, at the Guide's 64ch body.
- After the short answer: **the substances in this group** as the A to Z table above (no filter row when it has 12 rows or fewer).
- Breadcrumb Home / <Group> (not under Learn: the group is its own type). Schema: Article and BreadcrumbList (plus FAQPage with Questions).
- No paid link anywhere on a guide-layout page (guides never carry one, rule 4.5).

### Checks (to add with the first group page)
- The slug is not a list or trust page name (`tools/check.py` check-addresses, already live).
- Every substance in the table has the group in its data; the counts in the pad equal the table's rows.

## Goal subpage `/<goal>/<topic>/`

A narrower search inside a goal that shares fewer than 3 of the Google top 10 with the goal's main search. The first planned one is /weight-loss/new-drugs/.

- **Built from the goal page** (goal.md, Category), cut to the topic: breadcrumb Home / <Goal> / <Topic>; H1; the short answer; the goal's colour panel with the goal's drawing or photo (the goal's own tokens, no new colour).
- **The options:** the goal's option rows filtered to the topic's options (for new-drugs: the experimental and newest approved shots), same buttons, same clinic window.
- **The clinic table:** the goal's table filtered to the topic's medicines, when any plan carries them; else left out.
- **Is it legal today?:** the goal's accordion cut to the topic's substances.
- **What to do next:** first "Every <goal> option" to the goal page, then up to five pages of the same goal (rule 4.3).
- **On the goal page:** a "Narrower questions" line under the options: the goal's indexable subpages as text links between hairlines (the What to do next part), only when one exists.
- **Not on Home, not in the By goal menu:** a subpage is reached from its goal page, search and the sitemap; the goal stays the one entry.
- **Schema:** BreadcrumbList; FAQPage only with the Questions part.

## Round 3 fixes (owner answer a, 8 Nov 2026; ODOBRENO DIZAJN - Karlo - 9. 11. 2026 - PR #143)

- **Not a peptide:** in a group's substance table (and on /fda-approved/ first), a substance that is not a peptide (today finasteride, minoxidil and orforglipron, from a peptide flag in the data, w2) stays in the table with a `chip-neutral` "Not a peptide" right after its name, so the page never calls it a peptide (the architecture plan).
- **Goal subpage:** the first screen's right column is the goal's own panel (`goal-panel goal-c-<goal>` with the goal's photo, or its drawing until a photo is chosen), never an empty tint.
