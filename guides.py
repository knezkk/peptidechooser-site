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
    # guides 11 to 16: one per remaining goal and the two questions people type most (owner task 2 Nov 2026, feat/learn-3)
    {"slug": "best-peptides-for-muscle-growth", "title": "Best peptides for muscle growth: what the evidence shows",
     "h1": "Best peptides for muscle growth: what the evidence in people shows.",
     "desc": "CJC-1295, ipamorelin, sermorelin and tesamorelin: what each was tested on in people, their FDA status, what is approved and for what, and prices.",
     "line": "Growth hormone peptides: what was tested, their status and what is approved."},
    {"slug": "bpc-157-vs-tb-500", "title": "BPC-157 vs TB-500: status, evidence, prices",
     "h1": "BPC-157 vs TB-500: FDA status, evidence and prices side by side.",
     "desc": "BPC-157 and TB-500 side by side: the FDA status of each from our database, the studies in people, what shops charge per mg and the FDA letters.",
     "line": "The two recovery peptides side by side: status, studies and shop prices."},
    {"slug": "are-peptides-legal-in-the-us", "title": "Are peptides legal in the US? Status by kind in 2026",
     "h1": "Are peptides legal in the US? It depends on the kind.",
     "desc": "Approved, pharmacy-made, cosmetic and research-use peptides: what each kind means in law, the FDA's 503A lists and how to read our status chip.",
     "line": "The four kinds of peptide in law, the 503A lists and our status chip."},
    {"slug": "semaglutide-vs-tirzepatide-price", "title": "Semaglutide vs tirzepatide: price at online clinics",
     "h1": "Semaglutide vs tirzepatide: what online clinics charge for each.",
     "desc": "Every semaglutide and tirzepatide plan at the online clinics we track, brand and compounded, cheapest first, with care fees and what each is approved for.",
     "line": "Both GLP-1 medicines, brand and compounded, with the plans side by side."},
    {"slug": "peptides-for-skin-what-works", "title": "Peptides for skin: what works and what is marketing",
     "h1": "Peptides for skin: what has evidence, what is marketing.",
     "desc": "GHK-Cu, Matrixyl and Argireline: what each skin peptide was tested on, in people or in a dish, their cosmetic status and how to read an ingredient list.",
     "line": "Copper peptides, Matrixyl and Argireline, and what each was tested on."},
    {"slug": "how-we-check-sellers", "title": "How we check peptide sellers: the five checks explained",
     "h1": "How we check peptide sellers: the five checks, with examples.",
     "desc": "The five checks behind every seller score, each with a real example from our database, what the score does not tell you and how often it refreshes.",
     "line": "The five seller checks, each with a real example, and what the score is not."},
]
# Home's card shows the first six with "All guides" under them (owner task 2 Nov 2026: the first six when space is tight)
HOME_CARD = 6
# The related strip: guides on the same topic first, then the rest, at most RELATED_MAX (pages.md, Guide)
TOPIC = {"is-bpc-157-legal": "legal", "are-peptides-safe": "legal", "how-to-read-a-coa": "legal",
         "what-an-fda-warning-letter-means": "legal", "compounded-vs-brand-glp-1": "glp1",
         "compounded-semaglutide-price": "glp1", "peptides-for-hair-loss-what-works": "hair",
         "best-peptides-for-hair-growth": "hair", "ghk-cu-for-hair": "hair", "injectable-peptides-for-hair-growth": "hair",
         "best-peptides-for-muscle-growth": "body", "bpc-157-vs-tb-500": "body", "peptides-for-skin-what-works": "body",
         "are-peptides-legal-in-the-us": "legal", "how-we-check-sellers": "legal", "semaglutide-vs-tirzepatide-price": "glp1"}
RELATED_MAX = 5

LEARN_TITLE = "Peptide guides in plain words | Peptide Chooser"
LEARN_H1 = "Peptide guides in plain words"
LEARN_DESC = ("Sixteen short guides on peptides in the US: what is legal, lab reports, seller checks, GLP-1 prices, and "
              "peptides for hair, skin, muscle and recovery.")

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
    # guides 11 to 16
    "fda-503a": ("FDA, Bulk Drug Substances Used in Compounding Under Section 503A of the FD&C Act, current as of 14 May 2026",
                 "https://www.fda.gov/drugs/human-drug-compounding/bulk-drug-substances-used-compounding-under-section-503a-fdc-act"),
    "label-ozempic": ("FDA drug label for Ozempic, Indications and Usage, through openFDA, effective 30 Jan 2026",
                      "https://api.fda.gov/drug/label.json?search=openfda.brand_name:%22OZEMPIC%22"),
    "label-wegovy": ("FDA drug label for Wegovy, Indications and Usage, through openFDA, effective 23 Apr 2024",
                     "https://api.fda.gov/drug/label.json?search=openfda.brand_name:%22WEGOVY%22"),
    "label-mounjaro": ("FDA drug label for Mounjaro, Indications and Usage, through openFDA, effective 29 Jul 2026",
                       "https://api.fda.gov/drug/label.json?search=openfda.brand_name:%22MOUNJARO%22"),
    "label-zepbound": ("FDA drug label for Zepbound, Indications and Usage, through openFDA, effective 28 Aug 2026",
                       "https://api.fda.gov/drug/label.json?search=openfda.brand_name:%22ZEPBOUND%22"),
    "label-egrifta": ("FDA drug label for Egrifta SV (tesamorelin), Indications and Usage, through openFDA, effective 29 Jul 2026",
                      "https://api.fda.gov/drug/label.json?search=openfda.brand_name:%22EGRIFTA%22"),
    "label-genotropin": ("FDA drug label for Genotropin (somatropin), Indications and Usage, through openFDA, effective 4 Aug 2026",
                         "https://api.fda.gov/drug/label.json?search=openfda.brand_name:%22GENOTROPIN%22"),
    "pm-teichman": ("Teichman SL et al., Prolonged stimulation of growth hormone and IGF-I secretion by CJC-1295 in healthy adults, "
                    "J Clin Endocrinol Metab 91(3), 2006, PubMed 16352683", "https://pubmed.ncbi.nlm.nih.gov/16352683/"),
    "pm-raun": ("Raun K et al., Ipamorelin, the first selective growth hormone secretagogue, Eur J Endocrinol 139(5), 1998, PubMed 9849822",
                "https://pubmed.ncbi.nlm.nih.gov/9849822/"),
    "pm-beck": ("Beck DE et al., Randomized, controlled, proof-of-concept study of ipamorelin for postoperative ileus, "
                "Int J Colorectal Dis 29(12), 2014, PubMed 25331030", "https://pubmed.ncbi.nlm.nih.gov/25331030/"),
    "pm-poolton": ("Poolton JT et al., Human evidence for BPC-157 in orthopaedic and regenerative medicine: a systematic review, "
                   "Acta Orthop Belg 92(3), 2026, PubMed 42885452", "https://pubmed.ncbi.nlm.nih.gov/42885452/"),
    "pm-esposito": ("Esposito S et al., The N-terminal acetylated 17-23 fragment of thymosin beta 4 identified in TB-500, "
                    "Drug Test Anal 4(9), 2012, PubMed 22962027", "https://pubmed.ncbi.nlm.nih.gov/22962027/"),
    "pm-robinson": ("Robinson LR et al., Topical palmitoyl pentapeptide provides improvement in photoaged human facial skin, "
                    "Int J Cosmet Sci 27(3), 2005, PubMed 18492182", "https://pubmed.ncbi.nlm.nih.gov/18492182/"),
    "pm-blanes": ("Blanes-Mira C et al., A synthetic hexapeptide (Argireline) with antiwrinkle activity, Int J Cosmet Sci 24(5), 2002, "
                  "PubMed 18498523", "https://pubmed.ncbi.nlm.nih.gov/18498523/"),
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
        "tirz_all": [r for r in plans if r["substance_slug"] == "tirzepatide" and r.get("product_kind") in ("compounded",) + b.BRANDED],
        "sema_all": [r for r in plans if r["substance_slug"] == "semaglutide" and r.get("product_kind") in ("compounded",) + b.BRANDED],
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
    # registered whenever shop data is there, not only with the guide counts: sentences on shop prices and clinic plans cite
    # it too, and a cited source that is missing stopped the whole build (owner, 2 Nov 2026). Dated by the counts, else
    # by the data pull.
    on = f["stats_on"] or (b.DATA.get("pulled_at") or "")[:10]
    if (f["sellers"] or b.SHOPS or b.PRODUCTS) and on:
        k["db-sellers"] = (f"Peptide Chooser database: the research-use and cosmetic peptide shops we check, {nice(on)}. "
                           "Their prices and checks are in the seller windows on our goal pages", "/recovery/", "own")
    st = b.db_status("bpc-157")
    if st:
        k["db-bpc"] = (f"FDA status of BPC-157 in the Peptide Chooser database, first seen {nice(st['seen'])}", st["url"], "link")
    if f["letters"]:
        k["db-letters"] = (f"Peptide Chooser, FDA warning letters to peptide sellers, compounders and online clinics, "
                           f"checked {nice(f['letters_on'])}", b.LETTERS_URL, "own")
    for slug in sorted({r["substance_slug"] for r in b.LEGAL_DB or []} - {"bpc-157"}):
        st = b.db_status(slug)
        if st:
            k[f"db-{slug}"] = (f"FDA status of {b.substance_name(slug)} in the Peptide Chooser database, first seen {nice(st['seen'])}",
                               st["url"], "link")
    for r in f["hair_plans"] + f["sema_all"] + f["tirz_all"]:
        k[f"plan-{r['seller_slug']}-{r['plan_slug']}"] = (f"{b.seller_base(r['seller_name'])}, {r['plan_name']}, {nice(r['last_seen'])}",
                                                          r["pricing_url"], "text")
    # our own pages (the seller guide): How we rate, the sellers list and each seller's page
    k["own-how-we-rate"] = ("Peptide Chooser, How we rate peptide products and sellers", "/how-we-rate/", "own")
    if b.PROFILES:
        on = max((r.get("score_checked_on") or "" for r in b.PROFILES.values()), default="")
        k["own-sellers"] = (f"Peptide Chooser, Peptide sellers and their checks{', checked ' + nice(on) if on else ''}", "/sellers/", "own")
        for slug, r in b.PROFILES.items():
            k[f"seller-{slug}"] = (f"Peptide Chooser, {b.clean(r['seller_name'])}: our page on this seller"
                                   + (f", checked {nice(r['score_checked_on'])}" if r.get("score_checked_on") else ""), f"/sellers/{slug}/", "own")
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
<p>Because they were tested on hair in people, in large trials. In two one-year trials with 1,553 men, those who took finasteride had 107 more hairs than the placebo group after one year, and 138 more after two years. The men on placebo kept losing hair.{N('pm-kaufman')}</p>
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
        what = plan_kind_words(r) if kind == "hair" else glp1_words(b, r) if kind == "glp1" else b.care_note(r)
        ref = N(f"plan-{r['seller_slug']}-{r['plan_slug']}")
        trs.append(f'<tr><td>{b.clinic_link(r["seller_slug"], b.seller_base(r["seller_name"]))}</td><td data-l="Plan">{r["plan_name"]}</td>'
                   f'<td data-l="{"Care fee" if kind == "price" else "What it is"}">{what}</td>'
                   f'<td data-l="Per month"><span class="num">{b.usd(r["price_monthly"])}</span>{ref}'
                   + (f'<span class="sub">{b.care_note(r)}</span>' if kind == "glp1" else "") + '</td>'
                   f'<td data-l="FDA letter">{letter}</td><td data-l="Checked">{nice(r["last_seen"])}</td></tr>')
    third = "Care fee" if kind == "price" else "What it is"
    cls = "tbl tbl-cards tbl-clinics" if kind == "glp1" else "tbl tbl-cards"  # the clinic table part, care fee under the price
    return (f'<div class="tbl-wrap"><table class="{cls}"><thead><tr><th scope="col">Clinic</th><th scope="col">Plan</th>'
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


def glp1_words(b, r):
    """What a GLP-1 plan is: the brand by its name, or a pharmacy-made copy."""
    if r.get("product_kind") == "compounded":
        return "Compounded, not FDA approved"
    return f"{b.brand_base(r['plan_name'])}, FDA approved"


def and_list(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1] if xs else ""


def pep_link(b, slug, name=None):
    """A substance's name, linked to its /peptides/ page when the site has one."""
    name = name or b.substance_name(slug)
    return f'<a href="/peptides/{slug}/">{name}</a>' if any(p[0] == f"/peptides/{slug}/" for p in b.PAGES) else name


def brands(b, slug):
    """The brand names approved_db holds for a substance ("Ozempic, Rybelsus and Wegovy"), or ""."""
    names = sorted({b.brand_base(a["brand_name"]) for a in b.APPROVED_DB if a["substance_slug"] == slug and a.get("brand_name")}
                   - {slug.split("-")[0].title()})
    return and_list(names[:4])


def db_sentence(b, slug, N):
    """The database's status sentence with its source ("on the FDA list of ... compound.[n]"), or ""."""
    st = b.db_status(slug)
    if not st:
        return ""
    key = "db-bpc" if slug == "bpc-157" else f"db-{slug}"
    src = next((k for k, (_, u) in SOURCES.items() if u == st["url"]), key)
    return f"{st['sentence']}.{N(src)}"


def low_shop_words(b, slug, N):
    """"the lowest price per mg among the shops in our window is $1.14 (Chimera Peptides)" with its source, or ""."""
    r = b.pep_low_shop(slug)
    if not r:
        return ""
    name = b.seller_base(b.clean(b.SELLERS.get(r["seller_slug"], {}).get("seller_name") or r["seller_name"]))
    return (f"The lowest price per mg in our {b.substance_name(slug)} window is {b.per_mg(r['price_per_mg'])} "
            f"({b.clinic_link(r['seller_slug'], name, True)}).{N('db-sellers')}")


def g_muscle(b, f, N):
    eg, ge = brands(b, "tesamorelin"), brands(b, "somatropin")
    short = (f"No peptide is FDA approved for building muscle. Tesamorelin ({eg or 'Egrifta'}) is approved to reduce belly fat in "
             f"adults with HIV and lipodystrophy, and growth hormone itself (somatropin) mainly for growth hormone deficiency."
             f"{N('label-egrifta')}{N('label-genotropin')} CJC-1295 and ipamorelin are research-use peptides")
    ipa = db_sentence(b, "ipamorelin", N)  # after the labels, so the short answer's footnotes read in order
    short += (f", and ipamorelin is {ipa}" if ipa else ".") + " We found no trial in people that shows any of them builds muscle."
    mus = next(g for g in b.ALL_GOALS if g["slug"] == "muscle")
    opts = "".join(f"<li><strong>{p['name']}</strong>: {p['status']}. {p['does']}</li>" for p in mus["peptides"])
    counts = " ".join(x for x in (shops_line(b, f, s, N) for s in ("cjc-1295", "ipamorelin", "sermorelin")) if x)
    tes_shops = f["subs"].get("tesamorelin", {}).get("shops")
    cjc = db_sentence(b, "cjc-1295", N)
    body = f"""
<h2>Which peptides are sold for muscle?</h2>
<p>Our <a href="/muscle/">muscle page</a> lists the options people ask about:</p>
<ul>{opts}</ul>
<p>Most of them work on the same signal. They make the body release more growth hormone, which is why they are called growth hormone secretagogues. CJC-1295 is a long-acting copy of the hormone that tells the body to release growth hormone.{N('pm-teichman')} Ipamorelin acts on a different receptor with the same aim.{N('pm-raun')}</p>

<h2>What has been tested in people?</h2>
<p>Hormone levels, not muscle. In two placebo-controlled trials in healthy adults, CJC-1295 raised growth hormone and IGF-I, a hormone made in response to it, for days after each injection.{N('pm-teichman')} The trials measured those hormones and side effects; they did not measure muscle or strength.</p>
<p>Ipamorelin was developed in rats and pigs.{N('pm-raun')} Its one larger trial in people was for a different problem: 117 patients after bowel surgery, where it did no better than a placebo.{N('pm-beck')}</p>
<p>We found no trial in people that shows CJC-1295, ipamorelin or sermorelin builds muscle. A higher hormone level in a blood test is not the same as more muscle.</p>

<h2>Why are they on the FDA's risk list for compounding?</h2>
<p>The FDA keeps a list of substances that may be risky when pharmacies use them to make medicines.{N('fda-bulk-risks')} {f"Our database records that ipamorelin is {ipa}" if ipa else ""} The FDA says ipamorelin may set off an immune reaction when given some ways, and that a published study found serious side effects, including a death, when it was given into a vein for gut problems.{N('fda-bulk-risks')}</p>
<p>{f"For CJC-1295, our database records that {cjc}" if cjc else ""} The FDA lists serious side effects linked to CJC-1295, including a faster heart rate and a reaction in which blood vessels widen across the body, and says the data in people are limited.{N('fda-bulk-risks')}</p>

<h2>What is approved, and for what?</h2>
<p><strong>Tesamorelin</strong>{f" ({eg})" if eg else ""} is approved to reduce excess belly fat in adults with HIV who have lipodystrophy, a change in where the body stores fat. Its label says it is not for weight loss.{N('label-egrifta')} It is not approved for muscle.</p>
<p><strong>Somatropin</strong> is growth hormone made in a lab{f", sold as {ge}" if ge else ""}. It is approved for children who do not grow because of growth hormone deficiency or some other conditions, and for adults with growth hormone deficiency.{N('label-genotropin')} It is not approved for building muscle in healthy people.</p>
<p>A doctor decides whether you have a condition they treat.</p>

<h2>What do they cost?</h2>
<p>{counts or "We show shop prices once the shops are in our database."}{f" {tes_shops} shops also list tesamorelin as a research-use vial; that is not the approved medicine.{N('db-sellers')}" if tes_shops else ""}</p>
<p>A price per mg says nothing about what is in a vial. Our guide on <a href="/learn/how-to-read-a-coa/">how to read a COA</a> shows what a lab report can tell you, and <a href="/learn/how-we-check-sellers/">how we check sellers</a> explains the five checks next to each shop.</p>

<h2>So what are the best peptides for muscle?</h2>
<p>On the evidence in people, none. The peptides sold for muscle raise hormone levels in short trials or were tested for other problems, and the FDA lists safety concerns for two of them. The approved growth hormone medicines are for medical conditions.</p>
<p>None of this is medical advice. A doctor can tell you what fits your goal.</p>"""
    nxt = (("/muscle/", "Compare muscle options"), ("/learn/are-peptides-safe/", "Are peptides safe? guide"))
    return short, body, nxt


def g_bpc_tb(b, f, N):
    sb_, st_ = b.db_status("bpc-157"), b.db_status("tb-500")
    same = sb_ and st_ and sb_["sentence"] == st_["sentence"]
    short = (f"Neither BPC-157 nor TB-500 is FDA approved for any use.{N('drugsfda-hair')} "
             + (f"For each, {db_sentence(b, 'bpc-157', N)} " if same else ""))
    bs, ts = status_words(b, "bpc-157", N, plain=True), status_words(b, "tb-500", N, plain=True)
    short += (
             f"In July 2026 the FDA proposed not to let pharmacies use either one.{N('legal-6')} For BPC-157 we found three small "
             f"studies in people, rated very low in certainty; for TB-500 the FDA found no human data.{N('pm-poolton')}{N('fda-bulk-risks')}")
    rec = next(g for g in b.ALL_GOALS if g["slug"] == "recovery")
    uses = "".join(f"<li><strong>{p['name']}</strong>: {p['does']}</li>" for p in rec["peptides"])
    prices = "".join(f"<li>{x}</li>" for x in (shops_line(b, f, s, N) + (" " + low_shop_words(b, s, N) if low_shop_words(b, s, N) else "")
                                                for s in ("bpc-157", "tb-500")) if x.strip())
    cmp_url = ("/compare/bpc-157-vs-tb-500/" if any(p[0] == "/compare/bpc-157-vs-tb-500/" for p in b.PAGES)
               else "/compare/" if any(p[0] == "/compare/" for p in b.PAGES) else "")
    letters = (f"<p>Of the {f['letters']} FDA warning letters on our <a href=\"{b.LETTERS_URL}\">letters page</a>, {f['ruo_letters']} "
               f"went to research-use peptide shops, the kind that sell both.{N('db-letters')}</p>") if f["letters"] else ""
    body = f"""
<h2>What are BPC-157 and TB-500?</h2>
<p>{pep_link(b, "bpc-157", "BPC-157")} is a lab-made peptide of 15 amino acids, popular for recovery from muscle and tendon injuries.{N('pm-poolton')} {pep_link(b, "tb-500", "TB-500")} is a short piece of a larger body protein, thymosin beta-4: the fragment found in TB-500 products is seven amino acids long.{N('pm-esposito')}{N('fda-bulk-risks')}</p>
<p>Both are sold by research-use shops as powder in a vial, often side by side and sometimes in one blend.</p>

<h2>What is the FDA status of each?</h2>
<ul>
<li><strong>BPC-157</strong>: {bs or "not approved for any use." + N('drugsfda-hair')}</li>
<li><strong>TB-500</strong>: {ts or "not approved for any use." + N('drugsfda-hair')}</li>
</ul>
<p>On 23 and 24 July 2026 the FDA's Pharmacy Compounding Advisory Committee reviewed both, and the FDA proposed not to allow pharmacies to use them to make medicines.{N('legal-6')} The FDA says both may set off an immune reaction when given some ways.{N('fda-bulk-risks')} Our guide <a href="/learn/is-bpc-157-legal/">Is BPC-157 legal?</a> explains the review.</p>

<h2>What do the studies show?</h2>
<p>For BPC-157, most of the research is in animals. A 2026 review found three studies in people, with 30 people in all: two looked back at patients treated for knee pain or a bladder condition, and one tested its safety in two people. The reviewers rated the evidence very low in certainty.{N('pm-poolton')}</p>
<p>For TB-500, the FDA says it found no data on its use in people.{N('fda-bulk-risks')} We found no trial in people either.</p>

<h2>How do the FDA's concerns compare?</h2>
<p>The FDA lists both among the substances that may be risky when pharmacies use them to make medicines, for slightly different reasons.{N('fda-bulk-risks')}</p>
<ul>
<li><strong>BPC-157</strong>: it may set off an immune reaction when given some ways, it may be hard to make without unwanted peptide fragments, and the FDA found no, or only limited, safety information for the ways it was proposed to be used.{N('fda-bulk-risks')}</li>
<li><strong>TB-500</strong>: it may set off an immune reaction because the peptide can clump together or carry unwanted fragments, and the FDA found no data on its use in people, so it does not know whether it would cause harm.{N('fda-bulk-risks')}</li>
</ul>
<p>In both cases the FDA's point is the same: there is too little information to know what the product does to a person.</p>

<h2>What do people buy them for?</h2>
<p>Our <a href="/recovery/">recovery page</a> describes each one:</p>
<ul>{uses}</ul>
<p>Those are the claims shops make. Neither has been shown in a trial in people to speed recovery.</p>

<h2>What do they cost?</h2>
{f"<ul>{prices}</ul>" if prices else "<p>We show shop prices once the shops are in our database.</p>"}
<p>The window on our recovery page lists each shop with its five checks; we never link to the shops.{f' You can also put two shops side by side on <a href="{cmp_url}">Compare</a>.' if cmp_url else ''}</p>

<h2>What has the FDA said to the shops?</h2>
{letters}
<p>A warning letter is the FDA's formal notice, not a court ruling.{N('fda-letters')} Our guide on <a href="/learn/what-an-fda-warning-letter-means/">what an FDA warning letter means</a> explains what follows one.</p>

<h2>So which is better?</h2>
<p>Neither has the evidence in people to answer that. Both are not approved, both were reviewed by the FDA in July 2026, and both have little or no human data. A lower price per mg does not make one a better choice.</p>
<p>None of this is medical advice. A doctor or physical therapist can tell you what helps your injury.</p>"""
    nxt = (("/recovery/", "Compare recovery options"), ("/learn/is-bpc-157-legal/", "Is BPC-157 legal? guide"))
    return short, body, nxt


def g_legal(b, f, N):
    groups = {}
    for slug in sorted({r["substance_slug"] for r in b.LEGAL_DB or []}):
        st = b.db_status(slug)
        if st:
            groups.setdefault(st["label"], []).append(pep_link(b, slug, b.pep_short(slug)))
    cos = [r["peptide"] for r in b.LEGAL["rows"] if r.get("chip") == "info"][:3]
    ruo = lambda: (f'The FDA warning letters on our <a href="{b.LETTERS_URL}">letters page</a> went to companies: {f["ruo_letters"]} of the '
           f'{f["letters"]} went to research-use peptide shops.{N("db-letters")}') if f["letters"] else ""
    ex = lambda label: f" In our database: {and_list(groups[label][:3])}." if groups.get(label) else ""
    short = ("It depends on the kind. An FDA-approved peptide medicine is legal on a prescription.{0} A pharmacy may make some "
             "peptides for a patient under the FDA's compounding rules.{1} Cosmetic peptides are legal to sell without approval.{2} "
             "Research-use peptides are not approved for use in people.{3}").format(N('fda-approval'), N('fda-503a'), N('legal-5'),
                                                                                  N('drugsfda-hair'))
    short += (f" The FDA warning letters we track went to the companies selling peptides, not to people who bought them.{N('db-letters')}"
              if f["letters"] else "")
    body = f"""
<h2>What are the four kinds of peptide?</h2>
<p>The law treats a peptide by how it is made and sold, not by what it is. The same substance can be an approved medicine in one product and a research-use powder in another.</p>
<ul>
<li><strong>FDA-approved medicines.</strong> The maker sent the FDA its trial data, and the FDA found that the benefits outweigh the known risks.{N('fda-approval')}{ex("FDA approved")}</li>
<li><strong>Pharmacy-made (compounded).</strong> A pharmacy makes the medicine for one patient with a prescription. It is not FDA approved, and the FDA does not check its safety, effectiveness or quality before it is sold.{N('fda-compounding')}{ex("Pharmacy-made")}</li>
<li><strong>Cosmetics.</strong> Serums and creams with peptides. They do not need FDA approval before they are sold.{N('legal-5')}{f" On our legal table: {and_list(cos)}." if cos else ""}</li>
<li><strong>Research-use.</strong> Powders and vials sold "for research only". They are not approved for use in people.{N('drugsfda-hair')}{ex("Not approved")}</li>
</ul>

<h2>What are the 503A lists?</h2>
<p>Section 503A of the federal drug law covers ordinary pharmacies. A pharmacy may make a medicine from a raw ingredient only if that ingredient is allowed, for example because it is on the FDA's 503A bulks list.{N('fda-503a')}</p>
<p>While the FDA reviews the ingredients people have asked to add, it sorts them into three groups:{N('fda-503a')}</p>
<ul>
<li><strong>Category 1</strong>: enough information was sent to review it; the FDA does not plan to act against pharmacies that use it, under conditions.</li>
<li><strong>Category 2</strong>: the FDA found significant safety risks, so the category 1 policy does not apply.</li>
<li><strong>Category 3</strong>: too little information was sent to review it.</li>
</ul>
<p>The FDA's page on substances that may be risky to compound also names peptides whose nomination was withdrawn, such as BPC-157.{N('fda-bulk-risks')} Outsourcing facilities work under a different section, 503B, with their own list.{N('fda-glp1-supply')}</p>

<h2>What does "research use only" mean for a buyer?</h2>
<p>It is a label the seller puts on the product: it says the product is for lab research, not for people. It does not make the product approved, checked or safe to use.{N('fda-approval')} It also does not tell you what is in the vial; only a lab report from an outside lab can, and only for one batch. Our guide on <a href="/learn/how-to-read-a-coa/">how to read a COA</a> explains what to look for.</p>
<p>{ruo()} We make no claim about what the law means for a person who buys one. A lawyer can answer that for your state.</p>

<h2>How do you read our status chip?</h2>
<p>Every peptide on our pages carries one chip, taken from our database when it has a row for the substance, else from our own checked table:</p>
<ul>
<li><span class="chip chip-ok">FDA approved</span> an FDA-approved product with this substance exists. It may be approved for one use and not for another.</li>
<li><span class="chip chip-warn">Pharmacy-made</span> pharmacies may make it while the FDA reviews it; there is no approved product.</li>
<li><span class="chip chip-neutral">Not approved</span> no approved product, and the FDA has not allowed pharmacies to use it, or its nomination was withdrawn.</li>
<li><span class="chip chip-info">Cosmetic</span> sold as a cosmetic; no approval is needed.</li>
</ul>
<p>Each status on our legal table and our peptide pages comes with its source and the date we first saw it. Our <a href="/#legal">Is it legal today?</a> table and our <a href="/peptides/">peptides A to Z</a> show every one.</p>

<h2>Can a status change?</h2>
<p>Yes. The FDA can add a substance to a list, move it between categories or approve a new product. In July 2026 its compounding advisory committee reviewed BPC-157, TB-500, MOTS-c and epitalon, and the FDA proposed not to allow them.{N('legal-6')} We check the FDA's pages and change our chips when the FDA publishes a decision.</p>
<p>None of this is legal or medical advice.</p>"""
    nxt = (("/peptides/", "See every peptide's status"), ("/learn/is-bpc-157-legal/", "Is BPC-157 legal? guide"))
    return short, body, nxt


def g_sema_tirz(b, f, N):
    sa, ta = f["sema_all"], f["tirz_all"]
    ref = lambda r: N(pkey(r))
    brand = lambda rows: [r for r in rows if r.get("product_kind") in b.BRANDED]
    comp = lambda rows: [r for r in rows if r.get("product_kind") == "compounded"]
    def low(rows, name):
        return f"{name} from {b.usd(rows[0]['price_monthly'])}{ref(rows[0])}" if rows else ""
    weg = [r for r in sa if b.brand_base(r["plan_name"]) == "Wegovy"]
    zep = [r for r in ta if b.brand_base(r["plan_name"]) == "Zepbound"]
    parts = [x for x in (low(weg, "Wegovy"), low(zep, "Zepbound"), low(comp(sa), "compounded semaglutide"),
                         low(comp(ta), "compounded tirzepatide")) if x]
    short = ((f"At the online clinics we track, the monthly plans start at: {and_list(parts)}. " if parts else "")
             + f"Wegovy and Zepbound are FDA approved for weight management; Ozempic and Mounjaro are approved for type 2 diabetes."
             f"{N('label-wegovy')}{N('label-zepbound')}{N('label-ozempic')}{N('label-mounjaro')} Compounded copies are not FDA approved."
             f"{N('fda-compounding')}")
    sb, tb = brands(b, "semaglutide"), brands(b, "tirzepatide")
    newest = max((r["last_seen"] for r in sa + ta), default=None)
    def section(rows, name):
        return plan_table(b, rows, N, "glp1") if rows else f"<p>We show {name} plans once the clinic plans are in our database.</p>"
    fee = [r for r in sa + ta if r.get("membership_fee_monthly") not in (None,) and float(r["membership_fee_monthly"]) > 0]
    body = f"""
<h2>What are semaglutide and tirzepatide?</h2>
<p>Both act on the body's receptors for gut hormones. Semaglutide acts on one, the GLP-1 receptor;{N('label-ozempic')} tirzepatide acts on two, the GIP and GLP-1 receptors.{N('label-mounjaro')}</p>
{f"<p>Each is sold under more than one brand name: semaglutide as {sb}, tirzepatide as {tb}.{N('db-semaglutide')}{N('db-tirzepatide')}</p>" if sb and tb and b.db_status("semaglutide") and b.db_status("tirzepatide") else ""}

<h2>Which brands are approved for weight loss?</h2>
<ul>
<li><strong>Wegovy</strong> (semaglutide): to reduce excess body weight and keep it off in adults with obesity, or with overweight and a weight-related condition, and to lower the risk of heart attack and stroke in some adults.{N('label-wegovy')}</li>
<li><strong>Zepbound</strong> (tirzepatide): to reduce excess body weight and keep it off in the same groups, and to treat moderate to severe sleep apnea in adults with obesity.{N('label-zepbound')}</li>
<li><strong>Ozempic</strong> (semaglutide): for blood sugar in adults with type 2 diabetes, and to lower heart risk in some of them.{N('label-ozempic')}</li>
<li><strong>Mounjaro</strong> (tirzepatide): for blood sugar in adults and children aged 10 and over with type 2 diabetes.{N('label-mounjaro')}</li>
</ul>
<p>Some clinics sell Ozempic plans too, as the table below shows. The label tells you what the FDA approved each brand for.</p>

<h2>What do clinics charge for semaglutide?</h2>
<p>Every semaglutide plan at the online clinics we track, brand and compounded, cheapest first{f", checked {nice(newest)}" if newest else ""}:</p>
{section(sa, "semaglutide")}

<h2>What do clinics charge for tirzepatide?</h2>
{section(ta, "tirzepatide")}
<p>A clinic with an FDA warning letter is still listed; the chip opens our <a href="{b.LETTERS_URL}">letters page</a>. Prices are the clinics' published monthly prices; "from" prices are the lowest shown.</p>

<h2>What does the care fee add?</h2>
<p>Under each price is the clinic's care fee: "all-in" when the price includes the prescriber and check-ins, a monthly amount when it is charged on top, or "care fee not known" when the clinic's page did not say.{f" {len(fee)} of the plans above add a fee on top." if fee else ""} Add it before you compare two plans.</p>

<h2>What does the price not tell you?</h2>
<ul>
<li>Whether the price goes up as the dose goes up. Ask the clinic.</li>
<li>For a compounded plan, which pharmacy makes it. The FDA does not check a compounded medicine before it is sold.{N('fda-compounding')}</li>
<li>Whether a compounded semaglutide is a salt form, which the FDA says is a different ingredient from the one in the approved drugs.{N('fda-glp1-concerns')}</li>
</ul>
<p>Our guides on <a href="/learn/compounded-semaglutide-price/">compounded semaglutide prices</a> and <a href="/learn/compounded-vs-brand-glp-1/">compounded vs brand GLP-1</a> go further. None of this is medical advice; your prescriber can tell you which medicine fits you.</p>"""
    nxt = (("/weight-loss/", "Compare clinic prices"), ("/learn/compounded-vs-brand-glp-1/", "Compounded vs brand guide"))
    return short, body, nxt


def g_skin(b, f, N):
    skin = next(g for g in b.ALL_GOALS if g["slug"] == "skin")
    pep = [p for p in skin["peptides"] if p.get("substance")]
    short = (f"Skin peptides are sold as cosmetics: legal without FDA approval, and nobody has to show that they work.{N('legal-5')} "
             f"Matrixyl, a palmitoyl pentapeptide, has one 12-week, placebo-controlled study in 93 women that found fewer fine lines."
             f"{N('pm-robinson')} Argireline, an acetylated hexapeptide, has a study in women without a placebo group.{N('pm-blanes')} "
             f"For copper peptides (GHK-Cu), a 2026 review called the studies in people small and few.{N('pm-najafi')}")
    opts = "".join(f"<li><strong>{p['name']}</strong>: {p['status']}. {p['does']}</li>" for p in pep)
    counts = " ".join(x for x in (shops_line(b, f, p["substance"], N) for p in pep) if x)
    body = f"""
<h2>Which peptides are sold for skin?</h2>
<p>Our <a href="/skin/">skin page</a> lists the peptides you see most on labels:</p>
<ul>{opts}</ul>
<p>All three are sold in serums and creams as cosmetics. Cosmetics do not need FDA approval before they are sold, and the maker does not have to show that they work.{N('legal-5')}</p>

<h2>What does Matrixyl have behind it?</h2>
<p>The peptide in Matrixyl is a palmitoyl pentapeptide (pal-KTTKS), made in a lab and designed to help skin make collagen. In a 12-week study, 93 women aged 35 to 55 used a moisturizer with it on one side of the face and the same moisturizer without it on the other, without knowing which was which. The side with the peptide showed fewer wrinkles and fine lines in image analysis.{N('pm-robinson')}</p>
<p>That is a study in people, with a placebo, which is more than most skin peptides have. It was one study, in one group of women, in a cream at a stated strength.{N('pm-robinson')}</p>

<h2>What does Argireline have behind it?</h2>
<p>Argireline is an acetylated hexapeptide, designed to act a little like botulinum toxin by calming the nerve signal that tightens face muscles. In lab tests it blocked that signal, much more weakly than the toxin. In healthy women, a cream with 10% of it reduced wrinkle depth by up to 30% over 30 days.{N('pm-blanes')}</p>
<p>The study reports no placebo group and gives no number of women in its summary, so it is weaker evidence than the Matrixyl study.{N('pm-blanes')}</p>

<h2>What about copper peptides?</h2>
<p>GHK-Cu is a copper peptide the body makes; lab studies link it to skin repair and collagen.{N('pm-pickart')} A 2026 review of the research found four decades of lab and animal work, but called the studies in people thin: most trials were small and tested face creams.{N('pm-najafi')} Our <a href="/learn/ghk-cu-for-hair/">GHK-Cu guide</a> has more.</p>

<h2>How do you read a skin peptide claim?</h2>
<p>Ask four questions before you believe a promise on the box:</p>
<ul>
<li>Was it tested in people, or only in a dish?</li>
<li>Was there a placebo, a cream without the peptide, to compare with?</li>
<li>How many people, and for how long?</li>
<li>Was the product you are buying tested, or only the ingredient at a stated strength?</li>
</ul>
<p>The Matrixyl study answers the first three well; most skin peptide claims answer none of them.{N('pm-robinson')}</p>

<h2>How do you read the ingredient list?</h2>
<p>On a cosmetic label, the ingredients are listed from the largest amount to the smallest, and ingredients at 1% or less may follow in any order.{N('fda-cosmetic-labels')} A peptide near the end of the list may be there in a very small amount.</p>
<ul>
<li>Look for the ingredient name, not the brand name: our skin page names palmitoyl pentapeptide-4 for Matrixyl and acetyl hexapeptide-8 for Argireline, and GHK-Cu often appears as copper tripeptide-1.{N('pm-inci')}</li>
<li>The studies above used a stated amount. A product that does not say how much it contains cannot tell you whether it matches.</li>
<li>A product meant to treat a disease or change how the body works is a drug under the law, even when it is sold as a cosmetic.{N('legal-5')}</li>
</ul>

<h2>What do they cost?</h2>
<p>{counts or "We show prices once the shops are in our database."} Those are research-use powders and vials, not finished creams.</p>
<p>Our skin page lists every option with its status and its source. None of this is medical advice. A dermatologist can tell you what fits your skin.</p>"""
    nxt = (("/skin/", "Compare skin options"), ("/learn/ghk-cu-for-hair/", "GHK-Cu guide"))
    return short, body, nxt


def g_checks(b, f, N):
    shops = list(b.SHOPS.values())
    scored = [r for r in shops if r.get("score") is not None]
    order = lambda r: (-(r.get("score") or 0), -(r.get("product_count") or 0), r["seller_slug"])
    used = set()

    def example(key):
        met = sorted((r for r in scored if r.get(key)), key=lambda r: (r["seller_slug"] in used,) + order(r))
        n_met = len(met)
        if not scored:
            return ""
        out = f"Today {n_met} of the {len(scored)} shops we score meet it.{N('own-sellers')}"
        if met:
            r = met[0]
            used.add(r["seller_slug"])
            out += (f" One that does: <a href=\"/sellers/{r['seller_slug']}/\">{b.clean(r['seller_name'])}</a>."
                    f"{N('seller-' + r['seller_slug'])}")
        else:
            out += " No shop meets it yet."
        if len(scored) - n_met:
            miss = len(scored) - n_met
            out += f" {miss} {'does' if miss == 1 else 'do'} not; we do not name them here, and each one's page shows its checks."
        return out
    names = [t for _, t in b.SCORE_CHECKS]
    checked = max((r.get("score_checked_on") or "" for r in scored), default="")
    short = (f"Every shop we track gets the same five yes or no checks: {and_list(names)}.{N('own-how-we-rate')} "
             "The score is how many it meets, out of five. It is a count of facts we found, not a safety or quality grade, and "
             "a shop with five of five can still sell a product that is not approved for any use.{0}".format(N('own-how-we-rate'))
             + (f" We recompute the checks each time we pull our data; the newest check is from {nice(checked)}.{N('own-sellers')}"
                if checked else ""))
    body = f"""
<h2>Why do we check sellers at all?</h2>
<p>Research-use shops sell products that are not approved for use in people, so no regulator checks them before they are sold.{N('fda-approval')} We cannot test what is in a vial. What we can do is collect the same public facts about every shop and show them side by side, with their dates.</p>

<h2>Lab reports</h2>
<p>Met when the shop has published at least one lab report (a certificate of analysis) dated in the last 12 months, for any of its products. A miss means we found no recent report; it does not mean a product failed a test.{N('own-how-we-rate')}</p>
<p>{example("score_lab_testing")}</p>

<h2>No FDA letter</h2>
<p>Met when the FDA's list of warning letters holds no letter matched to the shop by its web address or street address. A letter that only shares a company name does not count, because names repeat.{N('own-how-we-rate')}</p>
<p>{example("score_no_fda_letter")} This is the one check where a miss means we found something against the shop: the FDA sent it a letter, and its page links the letter.</p>

<h2>Company found</h2>
<p>Met when we find the business behind the shop in a state business registry, matched with high confidence. We do not search every state yet, so a real company can still show as not found.{N('own-how-we-rate')}</p>
<p>{example("score_registered_company")}</p>

<h2>Legal pages</h2>
<p>Met when the shop's site has a terms page and a privacy or refund page, seen by our crawler in the last 30 days. Having them says nothing about what they promise.{N('own-how-we-rate')}</p>
<p>{example("score_legal_pages")}</p>

<h2>Fresh prices</h2>
<p>Met when our own price crawl saw at least one price per mg on the shop's site in the last 30 days. A miss means our prices for that shop are older, so read them with care.{N('own-how-we-rate')}</p>
<p>{example("score_fresh_prices")}</p>

<h2>What does the score not tell you?</h2>
<ul>
<li>Whether a product is safe or works. The checks are about the shop, not the vial.</li>
<li>Whether the product is approved. A shop with five of five can sell a product that is not approved for any use.{N('own-how-we-rate')}</li>
<li>That a low score means problems. A shop with zero of five is one where we found none of the five facts; only a missed "No FDA letter" means we found something against it.{N('own-how-we-rate')}</li>
</ul>
<p>Paid links do not change a check, and nobody can buy a higher score.{N('own-how-we-rate')}</p>

<h2>How often do the checks refresh?</h2>
<p>We recompute all five each time we pull our data, and each seller page shows the date of its last check.{N('own-how-we-rate')} The time windows are fixed: 12 months for lab reports, 30 days for legal pages and prices.{N('own-how-we-rate')}</p>
<p>Our <a href="/how-we-rate/">How we rate</a> page has the full rules{', and our <a href="/sellers/">sellers list</a> shows every shop with its score' if b.PROFILES else ''}. A lab report still covers only one batch; our guide on <a href="/learn/how-to-read-a-coa/">how to read a COA</a> explains why.</p>"""
    nxt = ((("/sellers/", "See all sellers") if b.PROFILES else (b.LETTERS_URL, "See FDA warning letters")), ("/how-we-rate/", "How we rate"))
    return short, body, nxt


TEXTS = {"is-bpc-157-legal": g_bpc, "are-peptides-safe": g_safe, "how-to-read-a-coa": g_coa,
         "compounded-vs-brand-glp-1": g_glp1, "what-an-fda-warning-letter-means": g_letter,
         "peptides-for-hair-loss-what-works": g_hair, "best-peptides-for-hair-growth": g_best,
         "ghk-cu-for-hair": g_ghk, "injectable-peptides-for-hair-growth": g_inject,
         "compounded-semaglutide-price": g_sema_price, "best-peptides-for-muscle-growth": g_muscle,
         "bpc-157-vs-tb-500": g_bpc_tb, "are-peptides-legal-in-the-us": g_legal, "semaglutide-vs-tirzepatide-price": g_sema_tirz,
         "peptides-for-skin-what-works": g_skin, "how-we-check-sellers": g_checks}


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
