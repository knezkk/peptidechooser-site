# Search

Index: [`design/pages.md`](../pages.md).

## Search `/search/` (owner task 2 Nov 2026; ODOBRENO DIZAJN and ODOBRENO SEO - Karlo - 2. 11. 2026)

Result types (owner UX audit, 3 Nov 2026): Goal, Peptide, Seller, Clinic, Comparison (`/compare/<a>-vs-<b>/`), Guide (`/learn/<x>/`), Page, in that order when matches tie; a comparison's and a guide's line start with "Comparison:" and "Guide:", so two results with one name never look alike.

The results of the header search on their own page. `noindex`, not in the sitemap or llms.txt.

- **Title:** "Search | Peptide Chooser". **H1:** "Search". **Description:** "Search Peptide Chooser for a peptide, a goal or a seller: FDA status, background checks and prices from our data, each with a link to its page."
- **Top** (white): H1; the form: label "Search a peptide, a goal or a seller", the input and `btn-ink` "Search" on one row (wrapping under 640px); with JavaScript the list for `q` from `/search-index.json` (the header's result rows, at most 50, in one white frame with hairlines between them) after one `aria-live` line: "N results for "q".", "Nothing found for "q". Browse by goal instead." or, with no q, "Type a peptide, a goal or a seller.". With JavaScript off: "Search needs JavaScript; browse by goal instead."
- Then the goals strip, headed "Browse by goal".
- **The index** (`/search-index.json`, written by build.py, under 150 KB, `tools/check.py`): one entry `{type, name, aliases, url, line}` per page (Home, goal pages as Goal, letters, sellers, compare, trust pages; not /search/ or the seller pages), per substance with a database status (Peptide: the database name with its brands, aliases from the legal rows and option names that carry it, the first goal page that carries it or `/#legal`, the status label and sentence) and per seller page (Seller: its name, its domain as an alias, never a link). Ranking: a name that starts with the words typed, then a later word, then anywhere; aliases one step lower; then Goal, Peptide, Seller, Page; then the shorter name.
- **No jump when results arrive** (Lighthouse, owner task 4 Nov 2026): with a query in the address the form holds one screen's height from before the first paint, so "Browse by goal" starts below it and does not move (CLS 0.388 to 0).
