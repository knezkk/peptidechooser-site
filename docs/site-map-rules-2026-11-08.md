# Site map rules (approved by the owner, 8 Nov 2026)

Source: "Peptidechooser site map" (8 Nov 2026) and the architecture plan "Arhitektura peptidechooser.com" (Claude Docs), section "Karta stranica: pravila za rast". Owner decisions 1-5 approved 8 Nov 2026; open decisions 0a = B (revisit in quarter 2), 0b = yes, 0c = settled, 0d = yes (8 Nov 2026).

## 1. Page types
Besides home, list pages and trust pages, every page belongs to one of 12 types. One address pattern, one parent, one Google rule each.

| Type | Address | Parent | Today | Google rule |
|---|---|---|---|---|
| Goal | /{goal}/ | home | 8 | a measured search, and at least 6 of the Google top 10 match the page's format |
| Goal subpage | /{goal}/{topic}/ | goal | 0 | a measured search sharing fewer than 3 of the top 10 with the goal's main search |
| Group page | /{group}/ | home | 0 | a measured search, at least 6 of the top 10 match the format (list or guide); the format follows that check |
| Substance | /peptides/{substance}/ | /peptides/ | 43 (17 indexed) | 3 of the 6 signals, as today; below that the page exists, noindex |
| Brand | /peptides/{substance}/{brand}/ | substance | 0 | at least one clinic offers it, and a measured search for the brand that no live page owns |
| Seller | /sellers/{seller}/ | /sellers/ | 152 | active, with a product or plan seen in the last 90 days; below that noindex. Live seller pages keep today's setting until the data agent confirms plans carry a last-seen date |
| Seller offer | /sellers/{seller}/{substance}/ | seller | 0 | shows at least 1 of 3 things the parent pages do not (own price history, own COA, plan terms) and either a measured search for the pair or 2 of the 3. Blends never. A failing pair stays a row on the seller page |
| Lab | /labs/{lab}/ | /labs/ | 0 | COAs for at least 3 sellers; needs the price-history/COA views (data task 1g) |
| Company FDA letters | /fda-warning-letters/{company}/ | /fda-warning-letters/ | 0 | a company, never a person, without an indexed seller page; a close-out letter is shown when one exists |
| Comparison | /compare/{a}-vs-{b}/ | /compare/ | 50 | a measured search for the pair, and no guide owns it |
| Guide | /learn/{guide}/ | /learn/ | 28 | a measured search no other page owns |
| Tool | /tools/{tool}/ | /tools/ | 0 | a measured search; price per mg / per month only, never dosing. First confirm the site does not publish its own folder at /tools/ |

Only substance and seller pages may exist noindexed before they pass. Any other type is made only when it passes. A live page that later fails is noindexed, never deleted.

New types (brand, seller offer, lab, company FDA letters, tool) go to Google in steps: 20 pages first, in their own sitemap file. The type passes when at least 16 of 20 are indexed, at least 5 get clicks, and the parent pages' impressions do not drop; then 200, then all, same check each step. If fewer than 70% of its pages stay indexed, the type is noindexed again and listed for the owner. The first test uses clinic offer pairs. Research-use pairs need their own test later.

## 2. Where a new page goes
Before question 1: does a live page already target this search? Two searches are the same when they share 3 or more of the Google top 10. If a live page owns it, add a section to that page. A page Google already shows keeps its address, title and H1.

1. Compares two things? Two named sellers, substances or brands side by side from data with no written verdict: /compare/{a}-vs-{b}/, names in alphabetical order, the reverse never made. A broad comparison (peptides vs steroids) or one with a written verdict is a guide. If a guide owns the pair, no comparison is made.
2. One seller, or one seller's offer of one substance? /sellers/{seller}/ or /sellers/{seller}/{substance}/. Blends never get an offer page.
3. One substance or one of its brands? /peptides/{substance}/ or /peptides/{substance}/{brand}/. A question about one substance with its own measured search that the substance page's format does not match (legal?, price per mg, use for one goal) is a guide with the substance name in its title; it links to the substance page and counts as one of its 6 signals. A brand with several substances gets its parent once, kept in the database: the substance whose page is indexed; if several or none, the first alphabetically that has a page.
4. One lab, or one company's FDA letters? /labs/{lab}/ or /fda-warning-letters/{company}/.
5. A goal people search for? /{goal}/; a narrower search inside a goal is /{goal}/{topic}/.
6. A group of substances by approval, route or class? /{group}/.
7. A price calculator? /tools/{tool}/, never dosing.
8. None of these? A guide at /learn/{guide}/.

## 3. Address rules (every new page)
1. Lowercase letters, numbers and hyphens, with a trailing slash.
2. Each thing has one slug from the database. Once live, a slug never changes; a new name goes into the database as an alias. Only exception: the 36 addresses in section 8, moved once before wave A.
3. A seller's slug is the brand people search for, not the legal company name.
4. No year, date or amount, no word that goes stale ("best", "cheapest", "latest"). One allowed fixed word: "new" in /weight-loss/new-drugs/.
5. No address deeper than three levels below home.
6. A goal or group never takes a list or trust page name: peptides, sellers, compare, learn, labs, tools, fda-warning-letters, search, out, about, how-we-rate, sources, contact, corrections, disclosure, privacy, or any folder name the site's code publishes.
7. Filters on list pages never create an indexable address.
8. A new page type needs a template in the design book first (ODOBRENO DIZAJN).

## 4. Links
1. Every page has a breadcrumb (e.g. Home > Sellers > {seller} > {substance}) and BreadcrumbList structured data.
2. List pages show every child on one page, so every page is 3 clicks or fewer from home. Home links every list page.
3. Every body page links across to up to 5 pages of the same type sharing a goal or substance. A seller's row on a substance page links to its offer page when that page is indexed. Cross-links only to indexable pages.
4. The sitemap lists only indexable pages, each with the date its visible content last changed. Later: one sitemap index pointing to one file per page type.
5. Paid links: clinics may carry one (not a clinic with an FDA letter about an adulterated drug and no close-out letter); supplement sellers only cosmetic products (decision D6a, owner decision 0a = B, 8 Nov 2026, to be revisited in quarter 2); research-use shops never, their offer pages included (rule 6); guides never.
6. Every paid link goes through /out/ and carries rel="sponsored" (owner, 8 Nov 2026). robots.txt already disallows /out/.

## 5. When data changes
1. A live page keeps its address when its data changes. A closed seller or withdrawn brand shows "no longer sold". No page is deleted.
2. When a live page fails its Google rule, the build noindexes it and lists it for the owner before the merge.
3. On new pages, title, meta description and H1 are set when the page first goes live and never contain counts, prices or dates from data. Later data changes go into the body only.
4. When two database entries are the same thing, only a page Google has never shown may redirect to the other. If both have impressions, both keep their addresses, the weaker one canonicals to the stronger, and the build lists them for the owner.
5. A live company FDA-letters page keeps its address if the company later gets a seller page; the seller page becomes the main page for the company name and they link to each other.

## 6. Main page for each overlap
In each pair both pages link to each other, and the other page links with the main page's search words.
- /weight-loss/ keeps "peptides for weight loss", next to /learn/best-peptides-for-weight-loss/.
- /weight-loss/pills/ is the main page for GLP-1 pills; "oral semaglutide" stays on /peptides/semaglutide/.
- /peptides/sermorelin/, /peptides/ipamorelin/, /peptides/tesamorelin/ stay the main pages for their substances, next to /growth-hormone/.
- /libido/ stays the main page for libido and keeps its TRT row, next to /testosterone/. If testosterone becomes a substance, /peptides/testosterone/ takes the bare substance search and /testosterone/ keeps "peptides for testosterone" and "trt online".
- /peptides/bremelanotide/ is the main page for "pt-141" (49,500/month); no /peptides/pt-141/ address. Its title should carry the name PT-141 (separate task, needs the owner's yes).
- /recovery/ is the main page for healing and joints ("peptides for healing", "joint pain", "joints", "injury recovery", "tendon repair").
- /peptides/retatrutide/ stays the main page for retatrutide, next to /weight-loss/new-drugs/.
- /peptides/epitalon/ stays the main page for epitalon, next to /bioregulators/.
- /sleep/ takes "peptides for sleep"; /peptides/dsip/ stays noindex until its guide (wave E).
- /peptides/ stays the A-Z list with its Approved filter; /fda-approved/ takes "fda approved peptides".
- /learn/what-is-a-503a-pharmacy/ stays a guide next to /prescription/.
- /learn/injectable-peptides-for-hair-growth/ covers hair only; /injections/ takes the broad search.
- /skin/ keeps "peptides skin care"; /topical/ takes "peptide serum".
- Price guides (ozempic-vs-wegovy-price, semaglutide-vs-tirzepatide-price, cheapest-bpc-157-per-mg, compounded-semaglutide-price) keep their searches; a brand page takes only the brand name.
- /learn/fda-warning-letters-peptides(-2026)/ and /learn/what-an-fda-warning-letter-means/ keep their searches; a company page takes only that company's name.
- Candidate, not approved: /energy/ (about 7,300 searches/month, no page today), pending a Google top-10 check.

## 7. What the site never builds
- Pages combining goal, route and approval automatically.
- "Near me" pages; dosing calculators.
- A tanning goal; "before and after" pages; anticancer pages.
- /research-use-only/, /prescription/bpc-157/, /learn/hhs-peptide-policy/.
- Pages for nasal sprays, patches or under-the-tongue products.
- A /for/ level in addresses; any move of a live address other than the one clean-up in section 8.
- /pills/ (dropped 8 Nov 2026: Google reads "peptide pills" as supplements). /prescription/ and /injections/ are built as group pages with a guide layout.

## 8. The one address clean-up (decision 5), before wave A
Order: hosting move (task 4A) -> owner checks Search Console impressions for these 36 -> data agent's slug change and the site redirects go live together (task 4C). Each moved page keeps its title and H1; the old address 301-redirects (server redirect on the new host); links, comparison pages (with #anchors) and the sitemap switch to the new address. Proposed new names are confirmed by the data agent against the brand name first.

| Old | New |
|---|---|
| /sellers/alloy-alloy-inc/ | /sellers/alloy/ |
| /sellers/apollo-peptide-sciences-llc/ | /sellers/apollo-peptide-sciences/ |
| /sellers/chemistry-works-llc/ | /sellers/chemistry-works/ |
| /sellers/eden-eden-health-international-inc/ | /sellers/eden/ |
| /sellers/ezpeps-ez-peps-llc/ | /sellers/ezpeps/ |
| /sellers/fridays-thrive-health-inc/ | /sellers/fridays/ |
| /sellers/genpeptide-debonaire-llc/ | /sellers/genpeptide/ |
| /sellers/good-life-meds-good-life-meds-llc/ | /sellers/good-life-meds/ |
| /sellers/legendary-peptides-llc/ | /sellers/legendary-peptides/ |
| /sellers/maximus-maximus-health-inc/ | /sellers/maximus/ |
| /sellers/measured-better-health-labs-inc/ | /sellers/measured/ |
| /sellers/midwest-peptide-midwest-bioresearch-llc/ | /sellers/midwest-peptide/ |
| /sellers/mile-high-compounds-llc/ | /sellers/mile-high-compounds/ |
| /sellers/nation-peptides-nation-labs-inc/ | /sellers/nation-peptides/ |
| /sellers/nationwide-peptides-national-science-labs-llc/ | /sellers/nationwide-peptides/ |
| /sellers/nuscience-peptides-llc/ | /sellers/nuscience-peptides/ |
| /sellers/royal-peptides-llc/ | /sellers/royal-peptides/ |
| /sellers/silverstone-labs-co/ | /sellers/silverstone-labs/ |
| /sellers/skinnyrx-lean-rx-inc/ | /sellers/skinnyrx/ |
| /sellers/strut-health-strut-health-llc/ | /sellers/strut-health/ |
| /sellers/tex-peptides-txp-innovations-llc/ | /sellers/tex-peptides/ |
| /sellers/trumprx-gov/ | /sellers/trumprx/ |
| /sellers/ventra-sciences-llc/ | /sellers/ventra-sciences/ |
| /sellers/viviomd-viviomd-group-llc/ | /sellers/viviomd/ |
| /sellers/wellmedr-wellmedr-llc/ | /sellers/wellmedr/ |
| /sellers/zappy-health-kare-solutions-llc/ | /sellers/zappy-health/ |
| /sellers/zealthy-fitrx-llc-also-dba-fitrx-and-am-rx/ | /sellers/zealthy/ |
| /sellers/american-peptides-americanpeptides-us/ | /sellers/american-peptides/ |
| /sellers/fifty-410-aspen-aesthetics/ | /sellers/fifty-410/ |
| /sellers/found-found-health/ | /sellers/found/ |
| /sellers/go-alpha-labs-alphalabs-peptides/ | /sellers/go-alpha-labs/ |
| /sellers/novocare-pharmacy-novo-nordisk/ | /sellers/novocare-pharmacy/ |
| /sellers/pure-peptides-purepeptides-bio/ | /sellers/pure-peptides/ |
| /sellers/sesame-sesame-care/ | /sellers/sesame/ |
| /sellers/swiss-chems-swisschems/ | /sellers/swiss-chems/ |
| /learn/fda-warning-letters-peptides-2026/ | /learn/fda-warning-letters-peptides/ |

Check before the move: good-life-meds vs goodlife-health, american-peptides vs american-peptide-research, ezpeps vs ez-peptides, nation-peptides vs nationwide-peptides must be different sellers (else rule 5.4 applies now).
