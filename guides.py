"""The Learn section (design/pages.md, Learn and Guide; owner task 2 Nov 2026): /learn/ and its guides in plain words
(six on 2 Nov 2026, four more on feat/learn-2).

Guide texts are Tier 1 drafts (ODOBRENO SEO before they go public). Every number in them comes from data/site.json:
the hand-checked rows, the database rows tools/pull_data.py writes (plans, letters_all, guide_stats) and the FDA and
MedlinePlus pages listed in SOURCES. A sentence whose number is missing from the data is left out, never filled in.
build.py imports this module and calls pages(build) once its own helpers exist.
"""
import json
import re
from collections import Counter
from datetime import date
from html import escape

BUILD_DATE = date.today().isoformat()

# The guides, in the order /learn/ and Home's card list them.
GUIDES = [
    {"slug": "is-bpc-157-legal", "title": "Is BPC-157 legal in the US? What the FDA decided",
     "h1": "Is BPC-157 legal? What the FDA says in 2026.",
     "desc": "BPC-157 is not FDA approved. What the July 2026 FDA review proposed, what research-use labels mean and how we check the shops that sell it.",
     "line": "Not approved, the July 2026 FDA review, and what research-use shops are doing."},
    {"slug": "are-peptides-safe", "title": "Are peptides safe? Approved, cosmetic and research-use",
     "h1": "Are peptides safe? It depends on which of the four kinds you mean.",
     "desc": "Approved, compounded, cosmetic and research-use peptides carry very different safety data. What each kind has, what a COA shows and how to read our checks.",
     "line": "The four kinds of peptide and what safety data each one has."},
    {"slug": "how-to-read-a-coa", "title": "How to read a peptide COA (certificate of analysis)",
     "h1": "How to read a peptide COA, and what it cannot tell you.",
     "desc": "What a peptide certificate of analysis tests (purity, identity, amount, endotoxin, sterility), who issues it, and why it only covers one batch.",
     "line": "Who issues a lab report, what it tests and why it covers one batch."},
    {"slug": "compounded-vs-brand-glp-1", "title": "Compounded vs brand semaglutide and tirzepatide",
     "h1": "Compounded or brand GLP-1: what you get, what it costs, what the FDA says.",
     "desc": "Compounded semaglutide and tirzepatide next to Wegovy and Zepbound: when pharmacies may copy them, what online clinics charge and the FDA letters to clinics.",
     "line": "Pharmacy-made copies next to Wegovy and Zepbound, with clinic prices."},
    {"slug": "what-an-fda-warning-letter-means", "title": "What an FDA warning letter means for a seller",
     "h1": "What an FDA warning letter means, and what it does not.",
     "desc": "An FDA warning letter is a formal notice, not a court ruling. What the letters to peptide sellers say, what happens after one and how we show them.",
     "line": "What a letter is, what happens after it and why it is not a verdict."},
    {"slug": "peptides-for-hair-loss-what-works", "title": "Peptides for hair loss: what works and what is marketing",
     "h1": "Peptides for hair loss: what has evidence, what does not.",
     "desc": "Finasteride and minoxidil are the FDA-approved hair loss options. What copper peptide serums and injectable peptides have behind them, and what clinics charge.",
     "line": "Finasteride and minoxidil next to copper peptides and injectables."},
    # guides 7 to 10 (owner task 2 Nov 2026, feat/learn-2)
    {"slug": "best-peptides-for-hair-growth", "title": "Best peptides for hair growth: what the evidence shows",
     "h1": "Best peptides for hair growth: what the evidence in people shows.",
     "desc": "GHK-Cu, PTD-DBM, biotin and injectable peptides sold for hair, next to finasteride and minoxidil: what each has been tested on, and what thicker means.",
     "line": "Copper peptides, PTD-DBM, biotin and injectables, and what each was tested on."},
    {"slug": "ghk-cu-for-hair", "title": "GHK-Cu for hair: what it is, the studies and how it is sold",
     "h1": "GHK-Cu for hair: what it is, what the studies show, how it is sold.",
     "desc": "GHK-Cu is a copper peptide sold in scalp serums and in research-use vials. Its FDA status, the hair studies, what a serum label tells you and what it costs.",
     "line": "The copper peptide in serums and vials: status, studies, labels and prices."},
    {"slug": "injectable-peptides-for-hair-growth", "title": "Injectable peptides for hair growth: legal status, evidence",
     "h1": "Injectable peptides for hair growth: legal status and evidence.",
     "desc": "BPC-157, TB-500 and GHK-Cu vials are sold for hair. Their FDA status from our database, the evidence in people, and what approved options cost.",
     "line": "The vials sold for hair, their FDA status, and what approved options cost."},
    {"slug": "compounded-semaglutide-price", "title": "Compounded semaglutide price: what clinics charge in 2026",
     "h1": "Compounded semaglutide price: what online clinics charge.",
     "desc": "Every compounded semaglutide plan at the online clinics we track, cheapest first, with its care fee and FDA letter, next to Wegovy and Ozempic plans.",
     "line": "Every compounded semaglutide plan we track, with care fees and brand prices."},
]
# Home's card shows the first six with "All guides" under them (owner task 2 Nov 2026: the first six when space is tight)
HOME_CARD = 6
# The related strip: guides on the same topic first, then the rest, at most RELATED_MAX (pages.md, Guide)
TOPIC = {"is-bpc-157-legal": "legal", "are-peptides-safe": "legal", "how-to-read-a-coa": "legal",
         "what-an-fda-warning-letter-means": "legal", "compounded-vs-brand-glp-1": "glp1",
         "compounded-semaglutide-price": "glp1", "peptides-for-hair-loss-what-works": "hair",
         "best-peptides-for-hair-growth": "hair", "ghk-cu-for-hair": "hair", "injectable-peptides-for-hair-growth": "hair"}
RELATED_MAX = 5

LEARN_TITLE = "Peptide guides in plain words | Peptide Chooser"
LEARN_H1 = "Peptide guides in plain words"
LEARN_DESC = ("Ten short guides on peptides in the US: what is legal, what is safe to know, lab reports, GLP-1 prices, "
              "FDA letters and peptides for hair.")

# Outside pages the guides cite (fda.gov and MedlinePlus only, plus the sources already on the site, which build.py
# hands over). The date is the page's own "Content current as of" where it shows one.
SOURCES = {
    "fda-approval": ("FDA, Development and Approval Process: Drugs", "https://www.fda.gov/drugs/development-approval-process-drugs"),
    "fda-compounding": ("FDA, Compounding and the FDA: Questions and Answers",
                        "https://www.fda.gov/drugs/human-drug-compounding/compounding-and-fda-questions-and-answers"),
    "fda-glp1-concerns": ("FDA, FDA's Concerns with Unapproved GLP-1 Drugs Used for Weight Loss, current as of 1 Oct 2026",
                          "https://www.fda.gov/drugs/postmarket-drug-safety-information-patients-and-providers/fdas-concerns-unapproved-glp-1-drugs-used-weight-loss"),
    "fda-glp1-supply": ("FDA, FDA clarifies policies for compounders as national GLP-1 supply begins to stabilize",
                        "https://www.fda.gov/drugs/drug-alerts-and-statements/fda-clarifies-policies-compounders-national-glp-1-supply-begins-stabilize"),
    "fda-bulk-risks": ("FDA, Certain Bulk Drug Substances for Use in Compounding that May Present Significant Safety Risks, current as of 22 Apr 2026",
                       "https://www.fda.gov/drugs/human-drug-compounding/certain-bulk-drug-substances-use-compounding-may-present-significant-safety-risks"),
    "fda-letters": ("FDA, About Warning and Close-Out Letters, current as of 20 Mar 2024",
                    "https://www.fda.gov/inspections-compliance-enforcement-and-criminal-investigations/warning-letters/about-warning-and-close-out-letters"),
    "medline-minoxidil": ("MedlinePlus, Minoxidil Topical", "https://medlineplus.gov/druginfo/meds/a689003.html"),
    # guides 7 to 10: PubMed, MedlinePlus and FDA only (owner task 2 Nov 2026)
    "medline-minoxidil-oral": ("MedlinePlus, Minoxidil (tablets)", "https://medlineplus.gov/druginfo/meds/a682608.html"),
    "medline-biotin": ("MedlinePlus Medical Encyclopedia, Pantothenic acid and biotin, reviewed 21 Jan 2025",
                       "https://medlineplus.gov/ency/article/002410.htm"),
    "fda-cosmetic-labels": ("FDA, Cosmetics Labeling Guide",
                            "https://www.fda.gov/cosmetics/cosmetics-labeling-regulations/cosmetics-labeling-guide"),
    "drugsfda-hair": ("Drugs@FDA, searched through openFDA for BPC-157, GHK-Cu (also as copper tripeptide and prezatide) and TB-500 "
                      "(also as thymosin beta-4): no approved product, 2 Nov 2026", "https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm"),
    "pm-kaufman": ("Kaufman KD et al., Finasteride in the treatment of men with androgenetic alopecia, J Am Acad Dermatol 39(4), 1998, PubMed 9777765",
                   "https://pubmed.ncbi.nlm.nih.gov/9777765/"),
    "pm-pyo": ("Pyo HK et al., The effect of tripeptide-copper complex on human hair growth in vitro, Arch Pharm Res 30(7), 2007, PubMed 17703734",
               "https://pubmed.ncbi.nlm.nih.gov/17703734/"),
    "pm-lee": ("Lee SH et al., Targeting of CXXC5 by a competing peptide stimulates hair regrowth and wound-induced hair neogenesis, "
               "J Invest Dermatol 137(11), 2017, PubMed 28595998", "https://pubmed.ncbi.nlm.nih.gov/28595998/"),
    "pm-patel": ("Patel DP et al., A review of the use of biotin for hair loss, Skin Appendage Disord 3(3), 2017, PubMed 28879195",
                 "https://pubmed.ncbi.nlm.nih.gov/28879195/"),
    "pm-pickart": ("Pickart L, Margolina A, Regenerative and protective actions of the GHK-Cu peptide in the light of the new gene data, "
                   "Int J Mol Sci 19(7), 2018, PubMed 29986520", "https://pubmed.ncbi.nlm.nih.gov/29986520/"),
    "pm-najafi": ("Najafi N et al., A systematic review of the mechanisms and therapeutic applications of GHK-Cu in topical microneedle "
                  "delivery, Arch Intern Med Res 9(3), 2026, PubMed 42787770", "https://pubmed.ncbi.nlm.nih.gov/42787770/"),
    "pm-inci": ("Skin Res Technol 32(8), 2026: a study naming the ingredient \"copper tripeptide-1 GHK-Cu\", PubMed 42573538",
                "https://pubmed.ncbi.nlm.nih.gov/42573538/"),
}


def checked(b):
    """The "Checked" date of every guide: the data pull date, as on the goal pages, else the hand-checked date."""
    return (b.DATA.get("pulled_at") or b.DATA["checked"])[:10]


def nice(iso):
    d = date.fromisoformat(iso[:10])
    return f"{d.day} {d.strftime('%b %Y')}"


def home_card():
    """Home's "Guides in plain words" card (pages.md, Home, Learn): after "What the labels mean", the first six titles as
    links and "All guides"."""
    links = "".join(f'<li><a href="/learn/{g["slug"]}/">{g["title"]}</a></li>' for g in GUIDES[:HOME_CARD])
    return (f'<section class="learn-card" aria-labelledby="learn-card-h"><h2 id="learn-card-h">Guides in plain words</h2>'
            f'<ul>{links}</ul><a href="/learn/">All guides</a></section>')


class Notes:
    """A guide's numbered sources, in the order the text first cites them. note(key) returns the footnote; the list
    renders under "Sources". Outside pages link with rel=nofollow; a clinic's plan page shows its address as text (no
    link to any clinic site, as on /weight-loss/); our own pages link without rel."""

    def __init__(self, known):
        self.known, self.order = known, []

    def __call__(self, key):
        if key not in self.order:
            self.order.append(key)
        n = self.order.index(key) + 1
        return f'<sup><a class="ref" href="#src-{n}" aria-label="Source {n}">{n}</a></sup>'

    def html(self):
        out = []
        for i, key in enumerate(self.order, 1):
            text, url, kind = self.known[key]
            if kind == "text":
                out.append(f'<li id="src-{i}">{text}: {url}</li>')
            elif kind == "own":
                out.append(f'<li id="src-{i}"><a href="{url}">{text}</a></li>')
            else:
                out.append(f'<li id="src-{i}">{text}: <a href="{url}" rel="nofollow">{url}</a></li>')
        return "".join(out)


def facts(b):
    """Every number the guides use, from data/site.json through build.py's helpers. A missing value is None."""
    d = b.DATA
    gs = d.get("guide_stats") or {}
    letters = b.LETTERS_ALL
    tele = lambda r: "(Telehealth)" in (r.get("letter_subject") or "") or r.get("seller_kind") == "S2_GLP1_TELEHEALTH"
    june = [r for r in letters if (r.get("letter_date") or "").startswith("2026-06") and tele(r)]
    june_day = Counter(r["letter_date"] for r in june).most_common(1)
    # a subject's plain form: the FDA's own subject without the bracket that names the channel ("(Telehealth)")
    subj = Counter(re.sub(r"\s*\([^)]*\)$", "", b.clean(r["letter_subject"])) for r in letters if r.get("letter_subject"))
    wl = next(g for g in b.ALL_GOALS if g["slug"] == "weight-loss")
    plans = b.clinic_plans(wl)

    def cheapest(sub, kinds):
        rows = [r for r in plans if r["substance_slug"] == sub and r.get("product_kind") in kinds and not b.other_use(wl, r)]
        return rows[0] if rows else None

    hair_plans = sorted((r for r in b.PLANS if r["substance_slug"] in ("finasteride", "minoxidil") and r.get("price_monthly") is not None),
                        key=lambda r: (float(r["price_monthly"]), r["seller_name"]))
    return {
        "sellers": gs.get("sellers"), "coa_12m": gs.get("sellers_coa_12m"), "bpc_sellers": gs.get("bpc_sellers"),
        "stats_on": gs.get("checked_on"),
        "letters": len(letters), "letters_on": (d.get("pulled_at") or "")[:10] or None,
        "letters_oldest": d.get("letters_all_oldest"),
        "ruo_letters": sum(r.get("seller_kind") == "S1_RUO" for r in letters),
        "tele_letters": sum(tele(r) for r in letters),
        "compounders": sum("Compounding Pharmacy" in (r.get("letter_subject") or "") for r in letters),
        "june": len(june), "june_day": june_day[0][0] if june_day else None,
        "june_day_n": june_day[0][1] if june_day else 0,
        "subjects": subj.most_common(4),
        "comp_sema": cheapest("semaglutide", ("compounded",)), "brand_sema": cheapest("semaglutide", b.BRANDED),
        "comp_tirz": cheapest("tirzepatide", ("compounded",)), "brand_tirz": cheapest("tirzepatide", b.BRANDED),
        "fin_plan": next((r for r in hair_plans if r["substance_slug"] == "finasteride" and r.get("product_kind") != "compounded"), None),
        "hair_comp": next((r for r in hair_plans if r.get("product_kind") == "compounded"), None),
        "bpc_window": len({r["seller_slug"] for r in b.seller_rows("bpc-157")}),
        # guides 7 to 10: shops and middle price per mg per substance, the cheapest GHK-Cu listing in its seller window,
        # the hair plans and every semaglutide plan at the clinics we track
        "subs": gs.get("substances") or {},
        "ghk_cheap": min((r for r in b.seller_rows("ghk-cu") if r.get("price_per_mg") is not None),
                         key=lambda r: r["price_per_mg"], default=None),
        "hair_plans": hair_plans,
        "sema_comp": [r for r in plans if r["substance_slug"] == "semaglutide" and r.get("product_kind") == "compounded"],
        "sema_brand": [r for r in plans if r["substance_slug"] == "semaglutide" and r.get("product_kind") in b.BRANDED],
    }


def known_sources(b, f):
    """Every source a guide may cite: SOURCES, the site's own legal and hair sources from data/site.json, our database
    pages and the clinic plans the guides name."""
    k = {key: (t, u, "link") for key, (t, u) in SOURCES.items()}
    for s in b.LEGAL["sources"]:
        k[f"legal-{s['n']}"] = (s["text"], s["url"], "link")
    hair = next(g for g in b.ALL_GOALS if g["slug"] == "hair")
    for s in hair.get("sources", []):
        k[f"hair-{s['n']}"] = (s["text"], s["url"], "link")
    if f["sellers"]:
        k["db-sellers"] = (f"Peptide Chooser database: the research-use and cosmetic peptide shops we check, {nice(f['stats_on'])}. "
                           "Their prices and checks are in the seller windows on our goal pages", "/recovery/", "own")
    st = b.db_status("bpc-157")
    if st:
        k["db-bpc"] = (f"FDA status of BPC-157 in the Peptide Chooser database, first seen {nice(st['seen'])}", st["url"], "link")
    if f["letters"]:
        k["db-letters"] = (f"Peptide Chooser, FDA warning letters to peptide sellers, compounders and online clinics, "
                           f"checked {nice(f['letters_on'])}", b.LETTERS_URL, "own")
    for slug in ("ghk-cu", "tb-500"):
        st = b.db_status(slug)
        if st:
            k[f"db-{slug}"] = (f"FDA status of {b.substance_name(slug)} in the Peptide Chooser database, first seen {nice(st['seen'])}",
                               st["url"], "link")
    for r in f["hair_plans"] + f["sema_comp"] + f["sema_brand"]:
        k[f"plan-{r['seller_slug']}-{r['plan_slug']}"] = (f"{b.seller_base(r['seller_name'])}, {r['plan_name']}, {nice(r['last_seen'])}",
                                                          r["pricing_url"], "text")
    hair = next(g for g in b.ALL_GOALS if g["slug"] == "hair")
    for s in hair.get("sources", []):
        k[f"hair-text-{s['n']}"] = (s["text"], s["url"], "text")  # a shop's page as plain text, never a link
    for key in ("comp_sema", "brand_sema", "comp_tirz", "brand_tirz", "fin_plan", "hair_comp"):
        r = f[key]
        if r:
            k[f"plan-{key}"] = (f"{b.seller_base(r['seller_name'])}, {r['plan_name']}, {nice(r['last_seen'])}", r["pricing_url"], "text")
    return k


def plan_words(b, r, n):
    """"$60/mo (Mochi Health, Compounded Semaglutide; care fee not known)" with its footnote."""
    return f"{b.usd(r['price_monthly'])}/mo ({b.seller_base(r['seller_name'])}, {r['plan_name']}; {b.care_note(r)}){n}"


# The texts. Each returns the body (H2 sections), the short answer and the two "What to do next" links. N is the
# guide's Notes; f the facts. Sentences that need a number are joined in only when the number exists.

def g_bpc(b, f, N):
    # The status sentence a reader sees on /recovery/ and in "Is it legal today?" (owner task 2 Nov 2026): the database's
    # status with its source, then the hand note on the July 2026 review; without the database, the hand row alone.
    st, hand = b.db_status("bpc-157"), next(r for r in b.LEGAL["rows"] if r.get("substances") == ["bpc-157"])
    if st:
        src = next((k for k, (_, u) in SOURCES.items() if u == st["url"]), "db-bpc")
        status = f"{st['label']}: {st['sentence']}.{N(src)}"
        status += f" {hand['note'][0].upper()}{hand['note'][1:]}.{N('legal-6')}"
    else:
        status = f"{hand['status']}: {hand['note']}.{N('legal-6')}"
    short = (f"{status} "
             + (f"The FDA's warning letters we track went to the companies selling peptides, not to people who bought them for "
                f"themselves.{N('db-letters')}" if f["letters"] else ""))
    research = (f" The FDA has sent warning letters to shops like these: {f['ruo_letters']} of the letters on our letters page went "
                f"to research-use peptide shops.{N('db-letters')}" if f["ruo_letters"] else "")
    shops = (f"<p>We track {f['bpc_sellers']} shops that list BPC-157.{N('db-sellers')} "
             + (f"Of the {f['sellers']} research-use and cosmetic peptide shops we check, {f['coa_12m']} posted a lab report "
                f"(a certificate of analysis, or COA) in the last 12 months.{N('db-sellers')}" if f["coa_12m"] is not None else "")
             + "</p>") if f["bpc_sellers"] else ""
    window = (f'the cheapest {f["bpc_window"]} of them' if f["bpc_window"] else "the shops")
    body = f"""
<h2>What is BPC-157?</h2>
<p>BPC-157 is a lab-made peptide, a short chain of amino acids. Online shops sell it as a "healing peptide", mostly as a powder in a vial that is meant to be mixed and injected. You will also see it in capsules and nasal sprays.</p>
<p>The studies behind it are in animals and in cells. We found no large trials in people, and the FDA says it found no, or only limited, information on its safety in people for the ways it was proposed to be used.{N('fda-bulk-risks')}</p>

<h2>Is BPC-157 FDA approved?</h2>
<p>No. There is no FDA-approved medicine that contains BPC-157, for any use. An approved medicine is one whose maker sent the FDA its trial data and the FDA found that the benefits outweigh the known risks for the people it is meant for.{N('fda-approval')} Nobody has done that for BPC-157.</p>
<p>The FDA's page on substances that may be risky in pharmacy-made medicines lists BPC-157 among those whose nomination for pharmacy compounding was withdrawn. It says BPC-157 made by a pharmacy may set off an immune reaction when given some ways, may be hard to make free of unwanted peptide fragments, and has little or no safety information behind it.{N('fda-bulk-risks')}</p>

<h2>What did the FDA review in July 2026?</h2>
<p>On 23 and 24 July 2026 the FDA's Pharmacy Compounding Advisory Committee, a panel of outside experts, reviewed BPC-157 together with TB-500, MOTS-c and epitalon. The question was whether pharmacies may use these substances to make medicines for patients on a prescription. The FDA proposed not to allow it.{N('legal-6')}</p>
<p>A committee advises; the FDA decides. A proposal is a step, not the last word. We keep the status on our <a href="/#legal">Is it legal today?</a> table and change this page when the FDA publishes what it decided.</p>

<h2>Is BPC-157 the same as TB-500?</h2>
<p>No. TB-500 is a lab-made copy of part of a natural repair protein, and shops often sell it next to BPC-157 or in the same blend. It went through the same July 2026 review and got the same proposal: not approved, and the FDA proposed not to let pharmacies use it.{N('legal-6')}</p>
<p>A blend of the two is not a tested product either. Nobody has studied the mix in people, and a lab report for a blend rarely says how much of each peptide is in the vial.</p>

<h2>What does "research use only" mean?</h2>
<p>"Research use only" and "not for human use" are words the shop puts on its own label. They do not mean that anyone approved the product, and they tell you nothing about what is in the vial or how clean it is.{research}</p>
<p>The label also means there is no dose on the box and no instructions from a doctor or pharmacist. We do not give doses either, and we never link to these shops.</p>

<h2>What are research-use shops doing?</h2>
<p>They keep selling it, in vials of different sizes and in blends with other peptides.</p>
{shops}
<p>A lab report is a start, not proof. It covers one batch, tested once, and it is only worth something if a lab outside the shop did the test. Our guide on <a href="/learn/how-to-read-a-coa/">how to read a peptide COA</a> shows what to look for.</p>

<h2>How do we check the shops that sell it?</h2>
<p>For every shop we hold the same five checks: Lab reports, No FDA letter, Company found, Legal pages and Fresh prices. Each one is a yes or no that we can show the source for, and we add them up to a score out of five.</p>
<p>On our <a href="/recovery/">recovery page</a>, the BPC-157 row has a "Prices at" button with the number of shops. It opens a window with {window}, each with its price per mg, its five checks and six facts: a COA for that listing, FDA warning letters, the registered company, whether the shop is active, when we first saw it and when we last checked the price.</p>
<p>These checks are facts we hold about the shop. They are not a safety or quality grade, and a shop with five of five is still selling a product that is not approved.</p>"""
    nxt = (("/recovery/", "Compare recovery options"), (b.LETTERS_URL, "See FDA warning letters"))
    return short, body, nxt


def g_safe(b, f, N):
    short = (f"It depends on the kind. Approved peptide medicines have trial data the FDA reviewed; pharmacy-made and "
             f"research-use peptides do not.{N('fda-approval')}{N('fda-compounding')} Cosmetic peptides are legal to sell "
             f"without approval and nobody has to show that they work.{N('legal-5')}")
    aes = (f"<p>For pharmacy-made semaglutide and tirzepatide, the FDA has counted 990 reports of side effects linked to "
           f"compounded semaglutide and more than 730 linked to compounded tirzepatide, as of 31 May 2026. It also says these "
           f"numbers are likely too low, because most pharmacies do not have to report them.{N('fda-glp1-concerns')}</p>")
    letters = (f" Our letters page lists {f['letters']} of them sent to peptide sellers, compounders and online clinics, "
               f"{f['ruo_letters']} of them to research-use shops.{N('db-letters')}" if f["letters"] else "")
    body = f"""
<h2>What are the four kinds of peptide?</h2>
<p>A peptide is a short chain of amino acids. The same word covers four very different things you can buy in the US:</p>
<ul>
<li><strong>Approved medicines.</strong> Semaglutide (Wegovy), tirzepatide (Zepbound) and bremelanotide (Vyleesi) are peptides the FDA approved for a stated use, on prescription.{N('legal-1')}{N('legal-2')}{N('legal-3')}</li>
<li><strong>Pharmacy-made (compounded) peptides.</strong> A pharmacy mixes them on a prescription. They are not FDA approved.{N('fda-compounding')}</li>
<li><strong>Cosmetic peptides.</strong> Creams and serums with peptides such as GHK-Cu or Matrixyl. Cosmetics are regulated, but they do not need FDA approval to be sold.{N('legal-5')}</li>
<li><strong>Research-use peptides.</strong> Vials sold online "for research" or "not for human use", such as BPC-157. No approved product exists.{N('legal-7')}</li>
</ul>

<h2>What safety data does each kind have?</h2>
<p><strong>Approved medicines</strong> have the most. Before approval the maker tests the medicine in people, usually in two well-designed trials, and the FDA reviews the data. It approves the medicine only if the benefits outweigh the known and possible risks for the people it is meant for.{N('fda-approval')} The label then lists the side effects found.</p>
<p><strong>Pharmacy-made peptides</strong> have none of their own. The FDA does not check their safety, how well they work or their quality before they are sold.{N('fda-compounding')} Large pharmacies registered as outsourcing facilities must follow federal manufacturing rules and the FDA inspects them; regular pharmacies are mainly overseen by state boards of pharmacy.{N('fda-compounding')}</p>
{aes}
<p><strong>Cosmetic peptides</strong> are judged as cosmetics: they must be safe to use on skin as labelled, but nobody has to prove that they do what the jar says.{N('legal-5')}</p>
<p><strong>Research-use peptides</strong> have the least. Most have animal or cell studies only, and nobody has checked what is in a given vial. For BPC-157, the FDA says it found little or no safety information for use in people.{N('fda-bulk-risks')}</p>

<h2>What does a lab report (COA) show?</h2>
<p>A certificate of analysis, or COA, is a lab report for one batch. It can show how pure the powder is and whether it is the peptide on the label. It cannot show that the peptide is safe or that it works in people, and it says nothing about the next batch.</p>
<p>Read more in our guide on <a href="/learn/how-to-read-a-coa/">how to read a peptide COA</a>.</p>

<h2>What is an FDA warning letter?</h2>
<p>A warning letter is the FDA's formal notice to a company that it found what it believes are serious breaks of the law, such as poor manufacturing, claims a product cannot back up, or wrong directions for use.{N('fda-letters')}{letters}</p>
<p>A letter is not a court ruling. Our guide on <a href="/learn/what-an-fda-warning-letter-means/">what an FDA warning letter means</a> explains what happens after one.</p>

<h2>How do we show safety on this site?</h2>
<p>Every option on our goal pages carries one of four labels: FDA approved, Cosmetic, Not FDA approved, pharmacy-made, or Not approved. We never call a research-use peptide safe, because nobody has the data to say so.</p>
<p>For shops we show facts, not grades: five checks (Lab reports, No FDA letter, Company found, Legal pages, Fresh prices) and the listing's own lab report. A shop that meets all five still sells a product that is not approved.</p>
<h2>What should you ask before you buy?</h2>
<ul>
<li>Which of the four kinds is it: approved, pharmacy-made, cosmetic or research-use?</li>
<li>If it is a medicine, who prescribes it, and which pharmacy makes or sells it?</li>
<li>Is there a lab report for this batch, from a lab outside the shop?</li>
<li>Has the seller had an FDA warning letter? Our letters page lists the ones we know.</li>
<li>Is there an FDA-approved option for the same goal? Our goal pages put it next to the peptides.</li>
</ul>
<p>None of this is medical advice. If you are thinking about any of these products, talk to a doctor first.</p>"""
    nxt = (("/#goals", "Compare by goal"), (b.LETTERS_URL, "See FDA warning letters"))
    return short, body, nxt


def g_coa(b, f, N):
    count = (f" Of the {f['sellers']} research-use and cosmetic peptide shops we check, {f['coa_12m']} posted a report in the last "
             f"12 months.{N('db-sellers')}" if f["coa_12m"] is not None else "")
    short = ("A COA is a lab report for one batch. It usually shows how pure the peptide is and whether it is the right one; "
             "check whether it also covers the amount, bacterial toxins and germs. It tells you about that batch only, and only if a "
             f"lab outside the shop did the test.{count}")
    often = (f"<p>Of the {f['sellers']} research-use and cosmetic peptide shops we check, {f['coa_12m']} posted at least one lab "
             f"report in the last 12 months.{N('db-sellers')} The rest posted none we could find, or only older ones. In our seller "
             "windows this is the \"Lab reports\" check, and each listing has its own chip: \"This product: COA yes\" with the "
             "number of reports, or \"This product: no COA\".</p>") if f["coa_12m"] is not None else ""
    body = f"""
<h2>What is a COA?</h2>
<p>A certificate of analysis, or COA, is a short report from a lab that tested a sample of a product. For peptides it is usually one or two pages with the product name, a batch or lot number, the date of the test, the tests that were run and the results.</p>
<p>Shops that sell research-use peptides often post COAs on their product pages. A COA is the closest thing these products have to a quality check, because no approved product exists and no regulator checked the vial.{N('legal-7')}</p>

<h2>Who issues a COA?</h2>
<p>There are two kinds. A <strong>third-party COA</strong> comes from a lab that the shop does not own. A <strong>seller COA</strong> is made by the shop or by the factory that made the powder. Only the first kind is an outside check.</p>
<p>Look for the lab's name, address and a way to check the report, such as a code or link on the lab's own site. A report with no lab name, or one that names the shop as the lab, tells you only what the shop says about itself.</p>

<h2>What does a COA test?</h2>
<p>A full report covers five things. Check which of them your report has:</p>
<ul>
<li><strong>Purity.</strong> How much of the powder is the peptide, shown as a percentage (often measured by HPLC). The rest can be leftovers from making it.</li>
<li><strong>Identity.</strong> Whether the peptide is the one on the label, usually by mass spectrometry: the weight of the molecule found should match the weight expected.</li>
<li><strong>Quantity.</strong> How many milligrams are really in the vial. A pure peptide in a half-full vial is still not what you paid for.</li>
<li><strong>Endotoxin.</strong> Toxins left behind by bacteria.</li>
<li><strong>Sterility.</strong> Whether living germs grew from the sample.</li>
</ul>
<p>Many peptide COAs show purity and identity only. A report that lists only purity tells you nothing about the amount, toxins or germs.</p>

<h2>Why does a COA cover only one batch?</h2>
<p>A COA is for the sample the lab received. It is worth something only if the batch or lot number on the report matches the number on your vial. A shop can make a new batch every few weeks; a report from last year says nothing about this month's powder.</p>
<p>Check the date too. A report much older than the product listing, or the same report on several different products, is a warning sign.</p>

<h2>What does a good COA look like?</h2>
<ul>
<li>It names an outside lab, with an address and a way to check the report on the lab's own site.</li>
<li>It has a batch or lot number that is also printed on the vial.</li>
<li>It is dated, and the date fits the product you are buying.</li>
<li>It shows how each result was measured (for example HPLC for purity, mass spectrometry for identity).</li>
<li>It covers more than purity: the amount in the vial, and for anything injected, endotoxin and sterility.</li>
</ul>

<h2>How often do shops publish them?</h2>
{often}
<p>A shop with reports is not a shop with good products. It is a shop that shows some of its work.</p>

<h2>What can a COA not tell you?</h2>
<p>It cannot tell you that a peptide is safe or that it works in people. Only trials can show that, and for research-use peptides there are none that the FDA reviewed.{N('fda-approval')} It cannot tell you a dose, and we do not either.</p>
<p>Signs that a report needs a closer look: no lab name, no batch number, the same purity to the decimal on every product, a date before the product existed, or a file that looks edited. When in doubt, the lab named on the report can usually confirm whether it issued it.</p>"""
    # owner answer Q1 a (2 Nov 2026): the outline button goes to the seller list once it is built
    nxt = (("/recovery/", "Compare recovery options"),
           ("/sellers/", "See all sellers") if b.PROFILES else (b.LETTERS_URL, "See FDA warning letters"))
    return short, body, nxt


def g_glp1(b, f, N):
    cs, bs, ct, bt = f["comp_sema"], f["brand_sema"], f["comp_tirz"], f["brand_tirz"]
    price = (f" At the online clinics we track, compounded semaglutide starts at {b.usd(cs['price_monthly'])}/mo and brand "
             f"semaglutide at {b.usd(bs['price_monthly'])}/mo.{N('plan-comp_sema')}{N('plan-brand_sema')}" if cs and bs else "")
    short = (f"Brand semaglutide (Wegovy) and tirzepatide (Zepbound) are FDA approved for weight management; compounded "
             f"copies are not, and the FDA does not check them before they are sold.{N('legal-1')}{N('legal-2')}"
             f"{N('fda-compounding')}{price}")
    rows = []
    for label, r, key in (("Compounded semaglutide", cs, "comp_sema"), ("Brand semaglutide (Wegovy)", bs, "brand_sema"),
                          ("Compounded tirzepatide", ct, "comp_tirz"), ("Brand tirzepatide (Zepbound)", bt, "brand_tirz")):
        if r:
            rows.append(f"<li><strong>{label}:</strong> from {plan_words(b, r, N('plan-' + key))}</li>")
    prices = (f"""<h2>What do they cost at online clinics?</h2>
<p>The cheapest monthly plan of each kind at the online clinics we track, with the care fee some clinics add each month:</p>
<ul>{"".join(rows)}</ul>
<p>Prices are the clinics' own published prices on the date in the source. Our <a href="/weight-loss/">weight loss page</a> lists every plan we track, cheapest first, with each clinic's FDA letters.</p>""") if rows else ""
    june = (f"""<h2>What happened in June 2026?</h2>
<p>In June 2026 the FDA sent {f['june']} warning letters to online clinics and telehealth companies on our letters page, {'all' if f['june_day_n'] == f['june'] else f['june_day_n']} of them on {nice(f['june_day'])}.{N('db-letters')} Their subject, as the FDA filed it, is "False &amp; Misleading Claims/Misbranded (Telehealth)": the FDA said the clinics' websites made claims about their products that it believes break the law.</p>
<p>Altogether, {f['tele_letters']} of the {f['letters']} letters on our letters page went to telehealth companies.{N('db-letters')} A letter is not a ban: a clinic with one can keep selling while it answers the FDA. We list the clinic and the date of its newest letter next to its prices.</p>""") if f["june"] else ""
    body = f"""
<h2>What is compounding?</h2>
<p>Compounding means a pharmacist mixes a medicine for a patient on a prescription. It is meant for people an approved medicine does not suit, for example someone allergic to a dye in the tablet, or a child who needs a liquid.{N('fda-compounding')}</p>
<p>Compounded medicines are not FDA approved. The FDA does not check their safety, how well they work or their quality before they are sold.{N('fda-compounding')} Regular pharmacies (called 503A pharmacies, after the part of the law they work under) are mainly overseen by state boards; larger outsourcing facilities (503B) follow federal manufacturing rules and the FDA inspects them.{N('fda-compounding')}</p>

<h2>When may a pharmacy copy Wegovy or Zepbound?</h2>
<p>A pharmacy may make copies of a medicine that is on the FDA's drug shortages list, if it meets the conditions in federal law.{N('fda-compounding')} That is how compounded semaglutide and tirzepatide came to be sold while both were in short supply.</p>
<p>The FDA said the tirzepatide shortage was resolved in October 2024 and the semaglutide shortage in February 2025. It gave regular pharmacies until 22 April 2025 and outsourcing facilities until 22 May 2025 to stop making copies of semaglutide, and its page says neither medicine is on the shortage list.{N('fda-glp1-supply')}</p>
<p>Online clinics still sell compounded versions; our clinic table lists them next to the brand plans. The FDA also warns that some sellers use salt forms (semaglutide sodium or acetate), which are different ingredients from the one in the approved medicine, and that it knows of no lawful basis for using them.{N('fda-glp1-concerns')}</p>
{prices}
<h2>What does the FDA say about compounded GLP-1s?</h2>
<p>The FDA has counted 990 reports of side effects linked to compounded semaglutide and more than 730 linked to compounded tirzepatide, as of 31 May 2026, and says the real numbers are likely higher because most pharmacies do not have to report them.{N('fda-glp1-concerns')} It has also had reports of people taken to hospital after dosing mistakes with compounded semaglutide, where the dose was measured or worked out wrongly.{N('fda-glp1-concerns')}</p>
<p>Compounded versions are often sent in vials that hold several doses, which you draw up yourself.{N('fda-glp1-concerns')} We do not give doses; your prescriber does.</p>
{june}
<h2>What should you ask a clinic?</h2>
<ul>
<li>Is this the brand medicine (Wegovy, Zepbound) or a pharmacy-made copy?</li>
<li>Which pharmacy makes it, and is it a 503A pharmacy or a 503B outsourcing facility?</li>
<li>Is the price all-in, or is there a monthly care fee on top?</li>
<li>Does the price change when the dose goes up?</li>
<li>Has the clinic had an FDA warning letter? Our weight loss page shows the date of each clinic's newest one.</li>
</ul>
<p>None of this is medical advice. Your prescriber can tell you which medicine fits you.</p>"""
    nxt = (("/weight-loss/", "Compare clinic prices"), (b.LETTERS_URL, "See FDA warning letters"))
    return short, body, nxt


def g_letter(b, f, N):
    top = f["subjects"]
    short = ("A warning letter is the FDA's formal notice that it found what it believes are significant violations of the law; "
             f"the company is asked to reply within 15 business days.{N('fda-letters')} It is public record, but it is not a "
             "court ruling and not a fine."
             + (f" Of the {f['letters']} letters on our letters page, the most common subject is \"{escape(top[0][0])}\" "
                f"({top[0][1]} letters).{N('db-letters')}" if top else ""))
    subjects = ("<ul>" + "".join(f"<li>{escape(s)}: {n} letters</li>" for s, n in top) + "</ul>") if top else ""
    typical = (f"""<h2>What do the letters to peptide sellers say?</h2>
<p>Our letters page lists {f['letters']} FDA warning letters sent to peptide sellers, compounders and online clinics since {nice(f['letters_oldest'])}.{N('db-letters')} Each has a subject, the FDA's short label for the problem. The most common ones:</p>
{subjects}
<p>In plain words: <strong>misbranded</strong> means the label or the website says something the FDA believes is false or not allowed, such as claims a product cannot back up; <strong>unapproved new drug</strong> means a product sold as a medicine without FDA approval; <strong>adulterated</strong> and <strong>CGMP</strong> point to how a product was made, such as poor manufacturing practice.{N('fda-letters')} Subjects marked "(Telehealth)" went to online clinics.</p>""") if top else ""
    body = f"""
<h2>What is an FDA warning letter?</h2>
<p>When the FDA finds what it believes are significant violations of federal rules, it tells the company, often in a warning letter. The letter names the problems, for example poor manufacturing practices, claims about what a product can do, or wrong directions for use.{N('fda-letters')}</p>
<p>The company is asked to reply within a set time, with its plan to fix the problems or with its reasons if it disagrees.{N('fda-letters')} The FDA publishes the letters on fda.gov, sometimes with private details removed, so anyone can read them.</p>
{typical}
<h2>Who gets warning letters?</h2>
<p>Any company the FDA oversees can get one: drug makers, pharmacies, online clinics and shops. """ + (f"Of the {f['letters']} letters on our letters page, {f['tele_letters']} went to telehealth companies and online clinics, {f['ruo_letters']} to research-use peptide shops and {f['compounders']} to compounding pharmacies.{N('db-letters')}" if f['letters'] else "") + f"""</p>
<p>Each letter is on fda.gov, where anyone can read it in full. It names the company, the products and the claims or practices the FDA objects to, and it says what the FDA expects the company to do.</p>

<h2>What happens after a letter?</h2>
<p>First the company replies. If it plans to fix the problems, the FDA checks the corrections, usually with a follow-up inspection.{N('fda-letters')}</p>
<p>When the FDA has checked that the problems were really fixed, it may send a close-out letter. A promise to fix is not enough for one, and when a problem by its nature cannot be fixed, no close-out letter comes.{N('fda-letters')}</p>
<p>If the FDA later finds the problems again, it may take further action without another warning.{N('fda-letters')}</p>

<h2>Why is a letter not a verdict?</h2>
<p>A warning letter is the FDA's view at the time it was written. The company can answer with its own reasons and evidence, and what both sides do next can change where things stand.{N('fda-letters')} No court has ruled, and no fine comes with the letter itself.</p>
<p>After a letter, a company may fix the problem, change its website or stop selling the product. The letter keeps its date, so read it as what the FDA found at that time, and check the date before you judge a seller today.</p>
<p>So a letter is a fact worth knowing, not proof that a product is dangerous. And no letter is not proof of anything either: a shop without a letter has simply not been sent one.</p>

<h2>How do we show letters?</h2>
<p>On our <a href="{b.LETTERS_URL}">letters page</a> every letter is listed newest first, with its date, the company as the FDA names it, the subject, the FDA office that sent it and a link to the letter on fda.gov. When we can match a letter to a shop or clinic in our database, its name is shown under the company.</p>
<p>In the seller windows on our goal pages each shop has a chip with its number of FDA warning letters, and the "No FDA letter" check is one of its five checks. On the <a href="/weight-loss/">weight loss page</a> each clinic shows the date of its newest letter. A shop or clinic with a letter is still listed: the letter is public record, and you can read it and decide.</p>"""
    nxt = ((b.LETTERS_URL, "See FDA warning letters"), ("/#goals", "Compare by goal"))
    return short, body, nxt


def g_hair(b, f, N):
    hair = next(g for g in b.ALL_GOALS if g["slug"] == "hair")
    serum = next((o for o in hair.get("options") or [] if o["name"].startswith("Copper")), None)
    short = (f"Finasteride and minoxidil are the FDA-approved options for hair loss, and neither is a peptide.{N('hair-1')}"
             f"{N('medline-minoxidil')} Copper peptide serums are cosmetics with lab and follicle studies behind them, not "
             f"large trials in people.{N('hair-3')}{N('legal-5')} Injectable peptides sold for hair are not approved for any "
             "use, and we found no human evidence for hair.")
    generic = (f" Generic finasteride starts at about ${hair['price_from_usd']} a month with a pharmacy coupon.{N('hair-2')}"
               if hair.get("price_from_usd") is not None else "")
    serum_p = (f" A scalp serum with copper peptides costs about {serum['price']} ({serum['price_note'].replace(serum['price'] + ' ', '', 1)}).{N('hair-text-4')}"
               if serum and serum.get("price") else "")
    fp, hc = f["fin_plan"], f["hair_comp"]
    clinics = (f"""<h2>What do online clinics charge?</h2>
<p>""" + (f"The cheapest finasteride plan at the online clinics we track is {plan_words(b, fp, N('plan-fin_plan'))}. " if fp else "")
               + (f"Pharmacy-made mixes, such as finasteride and minoxidil in one capsule or liquid, start at {plan_words(b, hc, N('plan-hair_comp'))}; "
                  "a mix like that is not itself an FDA-approved product." if hc else "")
               + """</p>
<p>A clinic plan includes the prescription; a pharmacy coupon needs a prescription from your own doctor. Our <a href="/hair/">hair page</a> shows every option with its price and source.</p>""") if fp or hc else ""
    body = f"""
<h2>Why do people look for peptides for hair?</h2>
<p>Because the approved options have limits. Finasteride is a daily pill that some people do not want to take, and minoxidil has to be used every day, for months, to keep working.{N('medline-minoxidil')} Peptide products promise an easier answer: a serum, a shampoo or an injection.</p>
<p>The question is not whether a peptide sounds promising, but what has been shown in people. That is what this guide sorts out.</p>

<h2>Which hair loss treatments are FDA approved?</h2>
<p>Two, and neither is a peptide. <strong>Finasteride 1 mg</strong> is a daily pill on prescription.{N('hair-1')} <strong>Minoxidil</strong> is a liquid or foam you put on the scalp, sold without a prescription.{N('medline-minoxidil')}</p>
<p>No peptide is FDA approved for hair loss. When a product is sold as a "hair peptide", it is either a cosmetic or a research-use product.</p>

<h2>What does finasteride do?</h2>
<p>Finasteride slows hair loss and regrows some hair in most men who take it. It is not for women who are or may become pregnant.{N('hair-1')}{generic}</p>
<p>It works while you take it. Your prescriber will go through side effects with you; MedlinePlus lists them in plain words.{N('hair-1')}</p>

<h2>What does minoxidil do?</h2>
<p>Minoxidil helps hair grow and slows balding. It works best in people under 40 whose hair loss is recent, and it does not help a receding hairline.{N('medline-minoxidil')}</p>
<p>It takes at least four months, and sometimes up to a year, before you see an effect, and most new hair is lost within a few months after you stop.{N('medline-minoxidil')}</p>

<h2>Do copper peptides (GHK-Cu) grow hair?</h2>
<p>GHK-Cu is a small copper peptide found in serums and shampoos. The evidence for hair comes from lab work: a 2007 study tested AHK-Cu, a close relative of GHK-Cu, on human hair follicles kept alive in a dish.{N('hair-3')} That is not the same as a trial in people, and we found no large trial in people.</p>
<p>Copper peptide serums are sold as cosmetics. Cosmetics do not need FDA approval, and nobody has to show that they work.{N('legal-5')}{serum_p}</p>

<h2>What about peptide shampoos and creams?</h2>
<p>Many shampoos, conditioners and scalp tonics list peptides, such as copper peptides, among their ingredients. They are cosmetics too, under the same rules as serums.{N('legal-5')} A peptide on the ingredient list tells you what is in the bottle, not what it does.</p>

<h2>What about injectable peptides sold for hair?</h2>
<p>Research-use shops sell vials of BPC-157, TB-500 and injectable GHK-Cu, and some of them market these for hair. None is approved for any use.{N('legal-7')} In July 2026 the FDA proposed not to let pharmacies use BPC-157 or TB-500 to make medicines.{N('legal-6')}</p>
<p>We found no studies in people that show these injections grow hair. We list their prices and checks on our hair page and never link to the shops.</p>
{clinics}
<h2>How do you tell evidence from marketing?</h2>
<ul>
<li>Ask which study: in people, in animals or in a dish. Only studies in people tell you about your hair.</li>
<li>"Contains peptides" on a shampoo is an ingredient list, not a result.</li>
<li>Before and after photos, a famous name and "doctor formulated" are marketing.</li>
<li>An FDA-approved product says so on its label, and its maker had to show results in people to get there.{N('fda-approval')}</li>
</ul>
<p>None of this is medical advice. A doctor or dermatologist can tell you which option fits your hair loss.</p>"""
    nxt = (("/hair/", "Compare hair options"), (b.LETTERS_URL, "See FDA warning letters"))
    return short, body, nxt


pkey = lambda r: f"plan-{r['seller_slug']}-{r['plan_slug']}"  # a clinic plan's source key (known_sources)


def shops_line(b, f, slug, N):
    """"76 shops list GHK-Cu; the middle price is $0.65 per mg" from guide_stats, or "" without the database."""
    s = f["subs"].get(slug)
    if not s:
        return ""
    mid = f"; the middle price across their listings is {b.money(s['ppm_median'])} per mg" if s.get("ppm_median") is not None else ""
    return f"{s['shops']} shops we track list {b.substance_name(slug)}{mid}.{N('db-sellers')}"


def status_words(b, slug, N, plain=False):
    """The database's status of a substance with its source ("Not approved: its nomination ... was withdrawn."), else "".
    `plain` for the middle of a sentence: "not approved: its nomination ... was withdrawn." (an approved status keeps its case)."""
    st = b.db_status(slug)
    if not st:
        return ""
    key = "db-bpc" if slug == "bpc-157" else f"db-{slug}"
    src = next((k for k, (_, u) in SOURCES.items() if u == st["url"]), key)
    label = st["label"].lower() if plain and st["label"] == "Not approved" else st["label"]
    return f"{label}: {st['sentence']}.{N(src)}"


def plan_kind_words(r):
    """What a hair or weight loss plan is, in plain words, from its product kind and substance."""
    if r.get("product_kind") == "compounded":
        return "Pharmacy-made mix, not FDA approved"
    if r["substance_slug"] == "finasteride":
        return "Finasteride, FDA approved for hair loss"
    if r["substance_slug"] == "minoxidil" and (r.get("dosage_form") == "tablet" or "oral" in r["plan_slug"]):
        return "Minoxidil tablet, a blood pressure medicine"
    return "Minoxidil"


def g_best(b, f, N):
    hair = next(g for g in b.ALL_GOALS if g["slug"] == "hair")
    inj = next((p for p in hair["peptides"] if p.get("substances")), None)
    names = [b.substance_name(s) for s in (inj["substances"] if inj else [])]
    short = (f"No peptide has been shown to grow hair in large trials in people. Finasteride and minoxidil, which are not "
             f"peptides, are the FDA-approved options.{N('hair-1')}{N('medline-minoxidil')} Copper peptides have a lab study "
             f"on hair follicles behind them, PTD-DBM has mouse and cell studies, and biotin has helped only people with a "
             f"condition behind their hair loss.{N('pm-pyo')}{N('pm-lee')}{N('pm-patel')} Injectable research-use peptides "
             "have no hair evidence in people that we could find.")
    vials = (f"Research-use shops sell vials of {', '.join(names[:-1])} and {names[-1]} that are meant to be injected. "
             if len(names) > 1 else "")
    counts = " ".join(x for x in (shops_line(b, f, s, N) for s in (inj["substances"] if inj else [])) if x)
    body = f"""
<h2>Which peptides are sold for hair?</h2>
<p>Four kinds of product come up when you search for hair peptides.</p>
<ul>
<li><strong>Copper peptides (GHK-Cu)</strong> in serums and shampoos, sold as cosmetics.{N('legal-5')}</li>
<li><strong>PTD-DBM</strong>, a lab-made peptide that some scalp serums now list.</li>
<li><strong>Biotin</strong>, often sold next to peptides. It is vitamin B7, not a peptide.{N('medline-biotin')}</li>
<li><strong>Injectable peptides.</strong> {vials}{counts}</li>
</ul>
<p>The question for each one is the same: was it tested on hair in people, and what did the test measure?</p>

<h2>What do copper peptides have behind them?</h2>
<p>The study that hair pages quote, ours included, is from 2007. Researchers kept human hair follicles alive in a dish and added a copper peptide; the follicles grew longer.{N('pm-pyo')} The peptide in that study was AHK-Cu, a close relative of GHK-Cu, not GHK-Cu itself.{N('pm-pyo')}</p>
<p>A 2026 review of the GHK-Cu research found four decades of lab and animal work, but called the studies in people thin: most trials were small and tested face creams.{N('pm-najafi')} We found no large trial of GHK-Cu for hair loss in people. Our <a href="/learn/ghk-cu-for-hair/">GHK-Cu guide</a> goes through it in more detail.</p>

<h2>What is PTD-DBM?</h2>
<p>PTD-DBM is a peptide built in a lab to block a protein called CXXC5, which slows a signal that hair follicles need to grow. In a 2017 study, mice treated with it regrew hair faster, and cells from human balding scalps showed more of the CXXC5 protein.{N('pm-lee')}</p>
<p>That is a study in mice and in cells. We found no published trial in people that shows PTD-DBM grows hair.</p>

<h2>Does biotin help hair grow?</h2>
<p>Only in people who lack it. A lack of biotin can cause hair loss, skin rashes and brittle nails.{N('medline-biotin')} A 2017 review found 18 reported cases where biotin helped hair or nails, and every one of those people had an underlying condition. The authors found no good evidence for biotin in healthy people.{N('pm-patel')}</p>

<h2>What about injectable peptides?</h2>
<p>None of the vials sold for hair is FDA approved for any use, and we found no study in people that shows any of them grows hair. Our guide on <a href="/learn/injectable-peptides-for-hair-growth/">injectable peptides for hair growth</a> has the FDA status of each one.</p>

<h2>Why do finasteride and minoxidil come first?</h2>
<p>Because they were tested on hair in people, in large trials. In two one-year trials with 1,553 men, those who took finasteride 1 mg a day had 107 more hairs than the placebo group after one year, and 138 more after two years. The men on placebo kept losing hair.{N('pm-kaufman')}</p>
<p>Minoxidil, put on the scalp, helps hair grow and slows balding, most in people under 40 whose hair loss is recent.{N('medline-minoxidil')} Both work only while you use them.{N('hair-1')}{N('medline-minoxidil')}</p>

<h2>What does "and thickness" mean in hair studies?</h2>
<p>Product pages say "thicker hair". Trials measure something you can check. The finasteride trials counted the hairs in a marked circle of scalp one inch across, compared photos judged by a panel of experts and asked the men and the doctors to rate the change.{N('pm-kaufman')}</p>
<p>So when a product promises thicker hair, ask three things:</p>
<ul>
<li>Was it tested in people, in animals or in a dish?</li>
<li>What was measured: a hair count, photos or only how people felt?</li>
<li>How many people took part, and was there a group that got a dummy product?</li>
</ul>
<p>A cosmetic does not have to answer any of these before it is sold.{N('legal-5')} None of this is medical advice. A doctor or dermatologist can tell you which option fits your hair loss.</p>"""
    nxt = (("/hair/", "Compare hair options"), ("/learn/peptides-for-hair-loss-what-works/", "Peptides for hair loss guide"))
    return short, body, nxt


def g_ghk(b, f, N):
    hair = next(g for g in b.ALL_GOALS if g["slug"] == "hair")
    serum = next((o for o in hair.get("options") or [] if o.get("substance") == "ghk-cu" and o.get("price")), None)
    serum_src = next((n for n in (serum or {}).get("sources", []) if "price" in next(
        (s["text"] for s in hair["sources"] if s["n"] == n), "")), None) if serum else None
    # the short answer's sources first, so its footnotes read 1, 2, 3, 4
    short = (f"GHK-Cu is a small copper peptide that the body makes, sold in scalp serums and in research-use vials.{N('pm-pickart')} "
             f"Serums are cosmetics: legal to sell without FDA approval, and nobody has to show that they grow hair.{N('legal-5')} "
             f"The hair evidence is one lab study on follicles, done with a close relative, AHK-Cu.{N('pm-pyo')} ")
    status = status_words(b, "ghk-cu", N, plain=True)
    short += (f"Injectable GHK-Cu is {status}" if status else f"Injectable GHK-Cu is not approved for any use.{N('drugsfda-hair')}")
    price = ""
    if serum:
        note = serum["price_note"].split(",")[0]
        price += (f"<p>A scalp serum with copper peptides costs about {serum['price']} for {serum['price_unit'].lstrip('/')} "
                  f"({note}).{N(f'hair-text-{serum_src}') if serum_src else ''}</p>")
    line = shops_line(b, f, "ghk-cu", N)
    c = f["ghk_cheap"]
    cheap = (f" The cheapest listing in our GHK-Cu window is {b.money(c['price_per_mg'])} per mg, for "
             f"{c['amount_mg']:,g} mg at {b.usd(c['price_usd'])}.{N('db-sellers')}" if c and c.get("amount_mg") else "")
    if line:
        price += (f"<p>{line}{cheap} Those are research-use vials and powders, not serums. Our <a href=\"/hair/\">hair page</a> "
                  "lists them with each shop's five checks; we never link to the shops.</p>")
    body = f"""
<h2>What is GHK-Cu?</h2>
<p>GHK is a peptide of three amino acids (glycine, histidine and lysine). GHK-Cu is the same peptide carrying copper. The body makes it, and lab studies link it to skin repair and collagen.{N('pm-pickart')}</p>
<p>Most of that work is in cells and animals. A 2026 review of the GHK-Cu research called the studies in people thin: most trials were small and tested face creams.{N('pm-najafi')}</p>

<h2>Is GHK-Cu FDA approved?</h2>
<p>No product with GHK-Cu is FDA approved for hair loss, or for anything else.{N('drugsfda-hair')} How it may be sold depends on what it is sold as.</p>
<p>As a serum or shampoo, it is a cosmetic. Cosmetics do not need FDA approval before they are sold, and the maker does not have to show that they work.{N('legal-5')}</p>
<p>As a powder or vial, it is sold by research-use shops.{' Our database records it as ' + status if status else ''} A research-use label means the product is not meant for people.</p>

<h2>What do the studies show for hair?</h2>
<p>The study that hair pages quote, ours included, is from 2007. Researchers kept human hair follicles alive in a dish and added a copper peptide; the follicles grew longer and the cells at their base grew more.{N('pm-pyo')}</p>
<p>Two things to know about it. The peptide was AHK-Cu, a close relative of GHK-Cu, not GHK-Cu itself.{N('pm-pyo')} And a follicle in a dish is not a person: it tells you a peptide does something to cells, not that a serum on your scalp grows hair. We found no large trial of GHK-Cu for hair loss in people.</p>

<h2>Serum or injection: what is the difference?</h2>
<p>A serum goes on the scalp. It is a cosmetic, so its maker may sell it without proving any effect.{N('legal-5')}</p>
<p>An injection is a vial of powder from a research-use shop, meant to be mixed and injected. It is not a medicine: no maker has sent the FDA the trial data that approval needs.{N('fda-approval')} We found no study in people that shows injected GHK-Cu grows hair. Our guide on <a href="/learn/injectable-peptides-for-hair-growth/">injectable peptides for hair growth</a> has more.</p>

<h2>What should you look for on a serum label?</h2>
<p>On a cosmetic label, the ingredients are listed from the largest amount to the smallest. Ingredients at 1% or less may follow in any order.{N('fda-cosmetic-labels')} So a copper peptide near the end of the list tells you little about how much is in the bottle.</p>
<ul>
<li>Look for the name: GHK-Cu often appears as copper tripeptide-1.{N('pm-inci')}</li>
<li>If the label or the maker states the amount, note it, so you can compare two serums.</li>
<li>A product meant to treat a disease or change how the body works is a drug under the law, even when it is sold as a cosmetic.{N('legal-5')} So a serum that promises to treat hair loss is making a drug claim.</li>
<li>Before and after photos and "clinically tested" are marketing until you see the study.</li>
</ul>

<h2>What does GHK-Cu cost?</h2>
{price or "<p>We show GHK-Cu prices on our hair page once the shops' prices are in our database.</p>"}
<p>A low price per mg is not a sign of quality. Our guide on <a href="/learn/how-to-read-a-coa/">how to read a COA</a> shows what a lab report can and cannot tell you.</p>
<p>None of this is medical advice. A doctor or dermatologist can tell you which option fits your hair loss.</p>"""
    nxt = (("/hair/", "Compare hair options"), ("/learn/peptides-for-hair-loss-what-works/", "Peptides for hair loss guide"))
    return short, body, nxt


def plan_table(b, rows, N, kind):
    """A table of clinic plans (the site's tbl part): clinic as text or our page, plan, what it is or the care fee, per
    month, the FDA letter chip to our letters page and the day the price was checked. No link to any clinic site."""
    trs = []
    for r in rows:
        n = r.get("fda_letter_count") or 0
        letter = (f'<a class="chip chip-warn chip-link" href="{b.LETTERS_URL}">FDA letter {nice(r["last_fda_letter_date"])}</a>'
                  if n and r.get("last_fda_letter_date") else '<span class="no-letter">none</span>')
        what = plan_kind_words(r) if kind == "hair" else b.care_note(r)
        ref = N(f"plan-{r['seller_slug']}-{r['plan_slug']}")
        trs.append(f'<tr><td>{b.clinic_link(r["seller_slug"], b.seller_base(r["seller_name"]))}</td><td data-l="Plan">{r["plan_name"]}</td>'
                   f'<td data-l="{"What it is" if kind == "hair" else "Care fee"}">{what}</td>'
                   f'<td data-l="Per month"><span class="num">{b.usd(r["price_monthly"])}</span>{ref}</td>'
                   f'<td data-l="FDA letter">{letter}</td><td data-l="Checked">{nice(r["last_seen"])}</td></tr>')
    third = "What it is" if kind == "hair" else "Care fee"
    return (f'<div class="tbl-wrap"><table class="tbl tbl-cards"><thead><tr><th scope="col">Clinic</th><th scope="col">Plan</th>'
            f'<th scope="col">{third}</th><th scope="col">Per month</th><th scope="col">FDA letter</th><th scope="col">Checked</th>'
            f'</tr></thead><tbody>{"".join(trs)}</tbody></table></div>')


def g_inject(b, f, N):
    hair = next(g for g in b.ALL_GOALS if g["slug"] == "hair")
    inj = next((p for p in hair["peptides"] if p.get("substances")), None)
    subs = inj["substances"] if inj else []
    names = [b.substance_name(s) for s in subs]
    listed = f"{', '.join(names[:-1])} and {names[-1]}" if len(names) > 1 else "".join(names)
    plans = [r for r in f["hair_plans"] if r.get("product_kind") != "compounded"]
    cheapest = plans[0] if plans else None
    short = (f"Research-use shops sell {listed} in vials for hair. None is FDA approved for any use, and we found no trial in "
             f"people that shows any of them grows hair.{N('drugsfda-hair')} "
             + (f"The approved option finasteride starts at {b.usd(cheapest['price_monthly'])} a month at the online clinics we track "
                f"({b.seller_base(cheapest['seller_name'])}).{N(pkey(cheapest))}"
                if cheapest and cheapest["substance_slug"] == "finasteride" else ""))
    rows = []
    for s, name in zip(subs, names):
        st = status_words(b, s, N)
        line = shops_line(b, f, s, N)
        rows.append(f"<li><strong>{name}</strong>: {st or 'Not approved for any use.' + N('drugsfda-hair')}"
                    + (f" {line[0].upper()}{line[1:]}" if line else "") + "</li>")
    review = next((r["note"] for r in b.LEGAL["rows"] if r.get("substances") == ["bpc-157"]), "")
    letters = (f"<p>Of the {f['letters']} FDA warning letters on our <a href=\"{b.LETTERS_URL}\">letters page</a>, "
               f"{f['ruo_letters']} went to research-use peptide shops.{N('db-letters')} Each letter names the products and the "
               "claims the FDA objects to; you can read it in full on fda.gov.</p>") if f["letters"] else ""
    table = plan_table(b, f["hair_plans"], N, "hair") if f["hair_plans"] else ""
    july = (f"<p>In July 2026 the FDA's advisory committee on pharmacy compounding reviewed BPC-157 and TB-500: {review}.{N('legal-6')} "
            'Our guide <a href="/learn/is-bpc-157-legal/">Is BPC-157 legal?</a> explains what that review means.</p>') if review else ""
    body = f"""
<h2>Which injectable peptides are sold for hair?</h2>
<p>The hair vials we see at research-use shops are {listed}. They come as a powder in a vial, meant to be mixed with water and injected. The label says they are for research, not for people.</p>
<p>They are not approved medicines. A medicine needs FDA approval first: its maker sends trial data, and the FDA checks that the benefits outweigh the risks.{N('fda-approval')} Nobody has done that for these peptides.</p>

<h2>What is their FDA status?</h2>
<p>From our database, with the FDA page behind each one:</p>
<ul>{"".join(rows)}</ul>
<p>The FDA lists BPC-157 among the substances that may be risky in pharmacy-made medicines: it may set off an immune reaction when given some ways, and there is little or no safety information on it in people.{N('fda-bulk-risks')}</p>
{july}

<h2>Is there any evidence they grow hair?</h2>
<p>Not in people, as far as we could find. The hair study quoted for copper peptides was done on follicles in a dish, with AHK-Cu, a close relative of GHK-Cu.{N('pm-pyo')} The studies on BPC-157 are in animals and cells.{N('fda-bulk-risks')}</p>
<p>A study in a dish or in mice tells you what a substance does to cells. It does not tell you what an injection does to your hair, or what it does to the rest of you.</p>
<p>A price per mg does not tell you either. It says nothing about what is in the vial: a lab report covers one batch, tested once, and only if a lab outside the shop did the test. Our guide on <a href="/learn/how-to-read-a-coa/">how to read a COA</a> shows what to look for. Our <a href="/learn/best-peptides-for-hair-growth/">best peptides for hair growth</a> guide puts these vials next to serums, biotin and the approved options.</p>

<h2>What has the FDA said to the shops?</h2>
{letters}
<p>A warning letter is the FDA's formal notice, not a court ruling.{N('fda-letters')} Our guide on <a href="/learn/what-an-fda-warning-letter-means/">what an FDA warning letter means</a> explains what follows one.</p>

<h2>What do the approved options cost at online clinics?</h2>
<p>Finasteride 1 mg is FDA approved for hair loss in men.{N('hair-1')} Minoxidil on the scalp is approved too, and sold without a prescription.{N('medline-minoxidil')} Minoxidil tablets are a blood pressure medicine; for hair, a prescriber decides whether they fit you.{N('medline-minoxidil-oral')}</p>
{table}
<p>Pharmacy-made mixes, such as finasteride and minoxidil in one capsule, are not themselves FDA-approved products.{N('fda-compounding')} A clinic with an FDA letter is still listed: the letter is public record.</p>
<p>None of this is medical advice. A doctor or dermatologist can tell you which option fits your hair loss.</p>"""
    nxt = (("/hair/", "Compare hair options"), ("/learn/is-bpc-157-legal/", "Is BPC-157 legal? guide"))
    return short, body, nxt


def g_sema_price(b, f, N):
    comp, brand = f["sema_comp"], f["sema_brand"]
    wl = next(g for g in b.ALL_GOALS if g["slug"] == "weight-loss")
    ref = lambda r: N(f"plan-{r['seller_slug']}-{r['plan_slug']}")
    rng = lambda rows: (f"{b.usd(rows[0]['price_monthly'])}" if len(rows) == 1 else
                        f"{b.usd(rows[0]['price_monthly'])} to {b.usd(rows[-1]['price_monthly'])}")
    wegovy = [r for r in brand if b.brand_base(r["plan_name"]) == "Wegovy"]
    frm = "from " if len(comp) > 1 else ""
    ozempic = [r for r in brand if b.other_use(wl, r)]
    short = ((f"At the online clinics we track, compounded semaglutide costs {frm}{rng(comp)} a month ({len(comp)} plans){ref(comp[0])}"
              + (f", against {rng(wegovy)} for Wegovy{ref(wegovy[0])}" if wegovy else "") + ". ") if comp else "") \
        + (f"Compounded semaglutide is a pharmacy-made copy, not FDA approved, and the FDA does not check its safety, "
           f"effectiveness or quality before it is sold.{N('fda-compounding')} The FDA has warned about dosing errors and "
           f"about versions made from salt forms of semaglutide.{N('fda-glp1-concerns')}")
    fees = [r for r in comp if r.get("membership_fee_monthly") not in (None, 0, 0.0) and float(r["membership_fee_monthly"]) > 0]
    fee_ex = max(fees, key=lambda r: float(r["membership_fee_monthly"]), default=None)
    unknown = sum(r.get("membership_fee_monthly") is None for r in comp)
    allin = sum(r.get("membership_fee_monthly") is not None and float(r["membership_fee_monthly"]) == 0 for r in comp)
    fee_p = ("<p>" + (f"Of the {len(comp)} plans, {allin} say{'s' if allin == 1 else ''} the price is all-in and {len(fees)} add{'s' if len(fees) == 1 else ''} a monthly fee. " if comp else "")
             + (f"At {b.seller_base(fee_ex['seller_name'])}, {b.usd(fee_ex['price_monthly'])} for the medicine plus "
                f"{b.usd(fee_ex['membership_fee_monthly'])} for care makes "
                f"{b.usd(float(fee_ex['price_monthly']) + float(fee_ex['membership_fee_monthly']))} a month.{ref(fee_ex)} " if fee_ex else "")
             + (f"For {unknown} plan{'s' if unknown != 1 else ''} the clinic's page did not show whether a fee is added, so ask before you sign up." if unknown else "")
             + "</p>")
    newest = max((r["last_seen"] for r in comp + brand), default=None)
    brand_li = "".join(
        f"<li>{b.seller_base(r['seller_name'])}, {r['plan_name']}: {b.usd(r['price_monthly'])}/mo, {b.care_note(r)}{ref(r)}"
        + (f" (Ozempic is approved for {b.other_use(wl, r)}, not for weight loss)" if b.other_use(wl, r) else "") + "</li>" for r in brand)
    body = f"""
<h2>What is compounded semaglutide?</h2>
<p>Semaglutide is the medicine in Wegovy.{N('legal-1')} Compounded semaglutide is a copy made by a pharmacy for a patient with a prescription. It is not FDA approved: the FDA does not check a compounded medicine's safety, effectiveness or quality before it is sold.{N('fda-compounding')}</p>
<p>While semaglutide was in short supply, pharmacies could make copies of it. Semaglutide is no longer on the FDA's drug shortage list, and for state-licensed pharmacies the time the FDA allowed for copies ended on 22 April 2025.{N('fda-glp1-supply')} Online clinics still sell compounded plans. Our guide on <a href="/learn/compounded-vs-brand-glp-1/">compounded vs brand GLP-1</a> explains the rules.</p>

<h2>What do online clinics charge for it?</h2>
<p>Every compounded semaglutide plan at the online clinics we track, cheapest first. Prices are the clinics' published monthly prices{f", checked {nice(newest)}" if newest else ""}.</p>
{plan_table(b, comp, N, "price") if comp else "<p>We show these prices once the clinic plans are in our database.</p>"}
<p>A clinic with an FDA warning letter is still listed. The letter is public record, and the chip opens our <a href="{b.LETTERS_URL}">letters page</a>.</p>

<h2>What is the care fee?</h2>
<p>Many clinics charge for the medicine and for the care around it: the prescriber, the check-ins and messages. Some fold it into one price, some add it as a monthly membership.</p>
{fee_p}

<h2>What do Wegovy and Ozempic plans cost?</h2>
<p>For contrast, the brand semaglutide plans at the same clinics:</p>
<ul>{brand_li}</ul>
<p>Wegovy is FDA approved for weight management.{N('legal-1')} A brand plan gets you that approved product.</p>

<h2>What does a lower price not tell you?</h2>
<ul>
<li>The dose. Ask whether the price goes up when the dose goes up.</li>
<li>The care fee, if it is charged on top.</li>
<li>Which pharmacy makes it, and whether the clinic tells you.</li>
<li>Whether it is semaglutide or a salt form. The FDA says salt forms such as semaglutide sodium and semaglutide acetate are different ingredients from the one in the approved drugs.{N('fda-glp1-concerns')}</li>
<li>Whether the clinic has had an FDA warning letter. The table shows the newest one.</li>
</ul>

<h2>What has the FDA warned about?</h2>
<p>The FDA has had reports of side effects, some needing a hospital stay, that may be linked to dosing errors with compounded semaglutide injections: patients measuring the wrong amount, and sometimes prescribers working out the dose wrong.{N('fda-glp1-concerns')}</p>
<p>It has also had reports from people given compounded semaglutide in doses beyond the approved label. Most pharmacies do not have to report side effects to the FDA, so the FDA says these are likely under-reported.{N('fda-glp1-concerns')}</p>
<p>None of this is medical advice. Your prescriber can tell you which medicine and which dose fit you.</p>"""
    nxt = (("/weight-loss/", "Compare clinic prices"), ("/learn/compounded-vs-brand-glp-1/", "Compounded vs brand guide"))
    return short, body, nxt


TEXTS = {"is-bpc-157-legal": g_bpc, "are-peptides-safe": g_safe, "how-to-read-a-coa": g_coa,
         "compounded-vs-brand-glp-1": g_glp1, "what-an-fda-warning-letter-means": g_letter,
         "peptides-for-hair-loss-what-works": g_hair, "best-peptides-for-hair-growth": g_best,
         "ghk-cu-for-hair": g_ghk, "injectable-peptides-for-hair-growth": g_inject,
         "compounded-semaglutide-price": g_sema_price}


def article_schema(b, g):
    url = f"{b.SITE}/learn/{g['slug']}/"
    org = {"@type": "Organization", "name": "Peptide Chooser", "url": b.SITE + "/"}
    return ('<script type="application/ld+json">' + json.dumps({
        "@context": "https://schema.org", "@type": "Article", "headline": g["title"], "description": g["desc"],
        "datePublished": BUILD_DATE, "dateModified": BUILD_DATE, "author": org,
        "publisher": dict(org, logo={"@type": "ImageObject", "url": f"{b.SITE}/assets/icon-512.png"}),
        "mainEntityOfPage": url, "image": f"{b.SITE}/assets/og/learn-{g['slug']}.png"}) + "</script>")


def related(slug):
    """The related guides strip (pages.md, Guide): up to five other guides as text links, those on the same topic first."""
    others = sorted((g for g in GUIDES if g["slug"] != slug), key=lambda g: TOPIC[g["slug"]] != TOPIC[slug])
    items = "".join(f'<li><a href="/learn/{g["slug"]}/">{g["title"]}</a></li>' for g in others[:RELATED_MAX])
    return (f'<section class="related" aria-labelledby="related-h"><h2 id="related-h" class="h-sources">Related guides</h2>'
            f'<ul>{items}</ul></section>')


def guide_body(b, g):
    f = facts(b)
    N = Notes(known_sources(b, f))
    short, body, (ink, line) = TEXTS[g["slug"]](b, f, N)
    return f"""
<article class="page guide"><div class="wrap prose">
<h1>{g["h1"]}</h1>
<p class="small meta"><a href="/about/">{b.AUTHOR}</a>. Checked {nice(checked(b))}.</p>
<section class="short-answer" aria-labelledby="short-h"><h2 id="short-h">Short answer</h2><p>{short}</p></section>
{body}
<h2>What to do next</h2>
<div class="btn-row"><a class="btn btn-ink" href="{ink[0]}">{ink[1]}</a><a class="btn btn-line" href="{line[0]}">{line[1]}</a></div>
{related(g["slug"])}
<section class="guide-sources" aria-labelledby="sources-h"><h2 id="sources-h" class="h-sources">Sources</h2>
<ol class="small sources">{N.html()}</ol></section>
</div></article>
"""


def learn_body(b):
    items = "".join(f'<li><h2><a href="/learn/{g["slug"]}/">{g["title"]}</a></h2><p>{g["line"]}</p>'
                    f'<p class="small">Checked {nice(checked(b))}</p></li>' for g in GUIDES)
    return f"""
<section class="page learn"><div class="wrap prose">
<h1>{LEARN_H1}</h1>
<p class="lede">Short answers to the questions people ask about peptides in the US, each with its sources. No doses, no sales.</p>
<p class="small meta"><a href="/about/">Peptide Chooser editorial team</a>. Every claim links to its source.</p>
<ul class="guide-list">{items}</ul>
</div></section>
"""


def pages(b):
    """/learn/ and the guides as build.py PAGES rows: (path, file, title, description, body, schema, crumb)."""
    out = [("/learn/", "learn/index.html", LEARN_TITLE, LEARN_DESC, learn_body(b), "", [("/learn/", "Learn")])]
    for g in GUIDES:
        path = f"/learn/{g['slug']}/"
        out.append((path, f"learn/{g['slug']}/index.html", g["title"], g["desc"], guide_body(b, g), article_schema(b, g),
                    [("/learn/", "Learn"), (path, g["title"])]))
    return out
