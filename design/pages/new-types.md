# Templates for the new page types

Index: [`design/pages.md`](../pages.md). Owner queue block 6, step 3A (8 Nov 2026; ODOBRENO DIZAJN - Karlo - 8. 11. 2026 - PR #142; every title, description and H1 pattern below is a proposal that waits for ODOBRENO SEO). Page types, parents and Google rules: `docs/site-map-rules-2026-11-08.md`, section 1. Shared parts: breadcrumb, filter look, lab mark and price history in [nav-parts.md](nav-parts.md); everything else is already in this book.

Rules for all five:
- **Made only when it passes** its Google rule; a live page that later fails is noindexed, never deleted. They go to Google in steps of 20, 200, then all, each step in its own sitemap file (site map rules, section 1).
- **Title, description and H1** are set when the page first goes live and never carry a count, price or date from data (rule 5.3); later data changes go into the body only.
- **Every page** has the breadcrumb and BreadcrumbList, the author line, a "Checked <date>" stamp, What to do next, Sources, and links across to up to five indexable pages of the same type that share a goal or substance (rule 4.3).
- **Paid links** by the paid link rule (parts.md, Buttons) and site map rule 4.5: a clinic may carry one; a supplement seller only on a cosmetic product; a research-use shop never, its offer pages included; a guide never.
- **No dose, ever** (`tools/check.py`), and no link to a shop's domain.

## Brand `/peptides/<substance>/<brand>/`

One approved brand of a substance (Wegovy under semaglutide), when at least one clinic offers it and a measured search for the brand is owned by no live page. A brand of several substances gets one parent, kept in the database.

- **Proposed title:** "<Brand> (<substance>): price and where to get it | Peptide Chooser". **H1:** "<Brand> (<substance>)".
- **First screen** (the substance page's `pep-first`, 6 + 6 from 900px): H1; the author line; the status line (the brand's own Drugs@FDA approval: approved for <use>, <date>, "FDA source"); the intro: who makes it, the form (pen, tablet), and the lowest monthly plan with its clinic and check date. Right: "Where to get it" with the brand's three cheapest clinic plans, the table button per row (`btn-action` "Visit <Clinic>" with "Paid link" when the clinic has one, else `btn-wait` "See plans").
- **The full table:** the substance page's clinic table filtered to plans of this brand only (no compounded plan on a brand page; the compounded rows stay on the substance page, which the page links to: "Compounded <substance> and other forms").
- **Price history** of the cheapest plan of the brand, when the data has one.
- **The blocks** (8 + 4): left, what the label approves it for (from the goal page's own line, with its Drugs@FDA source) and the FDA warning letters that name the brand; right, the facts card (maker, approval date, form, prescription needed) and the guides on the substance.
- **Schema:** BreadcrumbList and Drug (name, activeIngredient, manufacturer, from data only; `tools/check.py` today forbids Drug on substance pages, so the check gains the brand page as the one allowed place).

## Seller offer `/sellers/<seller>/<substance>/`

One seller's offer of one substance. Made only when it shows at least one of three things the parent pages do not (own price history, own lab report, plan terms) and either a measured search for the pair or two of the three. Blends never get one; a failing pair stays a row on the seller page. The first test uses clinic pairs.

- **Proposed title:** "<Substance> at <Seller>: price, plans and checks | Peptide Chooser". **H1:** "<Substance> at <Seller>".
- **First screen** (the seller page's top block, 8 + 4 from 900px): left, H1, the author line, the seller's kind (Online clinic, Research-use shop, Supplement shop) as a `chip-neutral`, and one paragraph: what the seller offers of this substance and the lowest price with its check date. Right, the Background check card of the seller (the same card, same five marks; a clinic meets at most four).
- **The offer** (white): a clinic: its plans of this substance as the clinic table's rows (plan, form, kind chip, monthly price, care fee, the table button), then the plan terms when data has them (length, what the price covers, cancellation) as a ledger. A shop: its listings of this substance (product, size, price, price per mg, the lab mark), no button (research-use) or the cosmetic link on a cosmetic row (supplement shop).
- **Price history** of the offer, when the data has one; **Lab reports** (shops only): every report for these listings as rows with the lab mark and the test date.
- **Compared with others:** the three cheapest other sellers of the same substance and kind, as the substance page's "Where to get it" list, and "Every seller of <Substance>" to /sellers/#substance=<slug>.
- **On the seller page:** the row of this substance links to the offer page when it is indexed (rule 4.3); the substance page's seller row the same.
- **Schema:** BreadcrumbList only (no Product or Offer).

## Lab `/labs/<lab>/`

A testing lab whose reports cover at least three sellers. Needs the price-history and lab-report views (data task 1g).

- **Proposed title:** "<Lab>: lab reports for peptide sellers | Peptide Chooser". **H1:** "<Lab> lab reports".
- **Top** (white): breadcrumb; H1; the author line; one `lede` paragraph from data: where the lab is, what it tests for (identity, purity, endotoxin, as its reports state), and the number of reports and sellers we hold (in the body, never the title). A facts pad right (7 + 5): first and newest report dates, sellers covered, the "Checked <date>" stamp.
- **The reports** (`paper-2` band): one table, newest first: date, seller (link to its page), product and size, substance (link when indexed), and the report's source as text. The filter look: seller, substance, year chips.
- **What a lab report shows and does not:** a fixed short paragraph (for ODOBRENO SEO) linking the guide on reading a lab report: a report is about one batch, the lab is chosen and paid by the seller, and it says nothing about the shop's other products.
- **Never** a grade, a rank or "trusted" about a lab or a seller (`tools/check.py`, the words rule).
- **/labs/**: the list page, one table (lab, reports, sellers, newest report) with the filter look; linked from /sellers/ and every lab mark.
- **Schema:** BreadcrumbList; Organization for the lab (name, address from its reports), without url.

## Company FDA letters `/fda-warning-letters/<company>/`

The FDA letters to one company, never a person, when the company has no indexed seller page. A close-out letter shows when one exists. A live company page keeps its address if the company later gets a seller page; the two link to each other and the seller page becomes the main page for the name (rule 5.5).

- **Proposed title:** "<Company>: FDA warning letters | Peptide Chooser". **H1:** "FDA warning letters to <Company>".
- **Top** (white, the Letters page's top parts): breadcrumb Home / FDA warning letters / <Company>; H1; the two ledes of the Letters page cut to one: "A warning letter is the FDA's formal notice that a company broke the law; it is not a fine or a ban."; the author line and "Checked <date>".
- **The letters:** the Letters table filtered to the company (date, subject, the letter's first mention in quotes, "FDA letter" nofollow to fda.gov), then the close-out letter as its own row with `chip-ok` "Closed by FDA" and its date (the Letters page's Closed by FDA rule).
- **What the company sold:** the substances the letters name, as links to their substance pages when indexed.
- **No paid link, no seller button, no link to the company's site.**
- **Schema:** BreadcrumbList; Organization (name, address from the letter) without url.

## Tool `/tools/<tool>/`

A price calculator with a measured search: price per mg and price per month only, never dosing. First confirm the site's code publishes no folder at /tools/ already (the goal pages' "Tools" section is text, not a folder).

- **Proposed title:** "<Tool name> | Peptide Chooser", the tool's name as people search it ("Peptide price per mg calculator"). **H1:** the same name.
- **The tool** (white, first screen): one `panel-line` card, the inputs left and the answer right from 900px (stacked on phones): labelled inputs (price, amount in mg, vials per month), 44px tall, `radius-control`; the answer in the price pad's figure style ("$X per mg", "$Y per month") updating as you type, `aria-live="polite"`. No button: the answer follows the inputs. Without JavaScript the card shows the formula in words ("price divided by the mg in the vial") and one worked example from today's data with its check date. Nothing is sent anywhere and the inputs never go into the address.
- **Under it:** "Compare with today's prices" as the substance page's three best-checked shops or three cheapest plans, from data, with their check dates.
- **Never** an input or an answer in mg per dose, per day or per kg, and never the word "dose" (`tools/check.py`).
- **/tools/**: the list page, one line per tool (name, one sentence), linked from the goal pages' Tools section.
- **Schema:** BreadcrumbList; WebApplication (name, applicationCategory "FinanceApplication", isAccessibleForFree) only.

## Round 3 fixes (owner answer a, 8 Nov 2026, after the round 2 shots and audit; waits for ODOBRENO DIZAJN)

- **Seller offer:** its plan table drops the Clinic column (one seller) and the plan name leads the row; the band is headed "<Substance> plans" with "The plans on this clinic's price page, cheapest first."; the list of other sellers is headed "Other clinics for <substance>" (or "Other shops for <substance>"), never "Where to get it", which belongs to the substance page.
- **Brand and seller offer:** the clinic table's `paper-2` band sits straight under the first screen, with the band's own padding only (no section padding around it).
- **Tool:** the H1 is the hero H1 of the other templates (the `hero` section), not a larger display size.
