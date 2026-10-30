# How we design here (the method, adapted from "You Can Now Build $10,000 Websites With Claude Code", Charlie Chang, Jul 2026)

Read this before any design task. It is the working method; `CLAUDE.md` holds the rules that never bend, `design/` holds the design book.

## 1. Set-up (done once, already in this repo)

- Three design skills are installed as project skills in `.claude/skills/`: `impeccable` (review, audit, critique, polish, typeset, animate), `ui-ux-pro-max` (searchable data: palettes, font pairings, UX guidelines, GSAP presets; with `design-system` and `ui-styling`) and `frontend-design` (account-level Anthropic plugin). Use them, do not reinvent what they already know.
- One project folder per session: this repo. Everything you make lives here.
- The video also adds two MCPs (Magic UI, React Bits) for React components. We do not use them: this site is static HTML rendered by `build.py`, no framework. If you need a component, write it into `design/bundle.css` as ours.

## 2. What separates a bad site from a premium one (the video's point, which we agree with)

Design and motion: how the page feels when the visitor lands, what moves and how, the colours, the typography. Not more features. The craft is in restraint: one accent, one hero number, generous space, type that feels like print, motion that confirms rather than entertains.

## 3. The prompt pattern (how briefs are written for you)

Every design brief we give you has the same parts, in this order:
1. **Role.** "Treat this as if you are the creative director of …": you own the result, you make decisions, you do not ask for permission for details.
2. **Who and what.** The site, the audience, what the page must do in one sentence.
3. **Feel.** Three to five adjectives plus two "not like" references (for us: clinical, calm, editorial, premium, trustworthy; not a wellness brand, not a SaaS dashboard, never AI-generated).
4. **Palette and type direction.** Named, with what carries the colour (for us: paper, ink, one accent; the number is the hero).
5. **Structure.** The sections in order. Here the order is fixed by `design/pages.md`; a brief may restyle sections, never reorder or drop them.
6. **Motion.** What moves, on what trigger, how long, and the reduced-motion fallback. GSAP from cdnjs is allowed; Three.js and WebGL are not (performance on phones and trust on a health site).
7. **Constraints.** What must not change (Tier 1 text, numbers from data, URL/title/H1, one pair of actions), the checks that must pass, the screenshots to deliver.
8. **"Use any skills you need."** You may read the three skills and their data freely.

When a brief is thin, do what the video recommends: rewrite it into this pattern yourself, show the rewritten brief in one paragraph, then build.

## 4. The build loop (what the video's agent did, which we require)

1. Read `CLAUDE.md`, `design/`, `build.py`, `data/site.json`. Build and serve locally.
2. Mine the skills first: `impeccable` for critique and direction, `ui-ux-pro-max` data for palettes, pairings, guidelines, motion presets.
3. Lock a short creative and motion spec (one paragraph each) before touching CSS.
4. Build on a branch. Tokens first (`design/tokens.json`), then components (`design/bundle.css`), then layout (`assets/site.css`), then markup in `build.py`.
5. Verify in a real browser at 390, 1440 and 2560 px: no console errors, keyboard works, contrast 4.5:1, touch targets 44 px, reduced motion respected, page works with JavaScript off.
6. Run `python3 build.py && python3 tools/check.py && node tools/check_layout.js`. Fix the page, never the check.
7. Deliver: before/after screenshots in `shots/`, a plain-words report (what changed, what you decided, what you were unsure about), and the design book updated so it describes what is built.
8. Stop. Publishing is the owner's decision (`ODOBRENO DIZAJN - Karlo - <date>`); you never push to `main`.

## 5. What "premium" means on this site, concretely

- The visitor's question is answered above the fold: which option, what it costs per month, is it legal, with the check date.
- The ℞ price pad, the body figure with goals, the legal table and the sources list are the signature parts. Make them beautiful; do not add new signature parts without the book.
- Motion budget: the figure draws itself once, the active dot pulses, panels cross-fade, sections reveal on scroll with a short stagger, the stamp lands once. Nothing moves after the page settles. LCP under 2.5 s on a phone, CLS under 0.1.
- No stock photos, no illustrations of pills or syringes, no caduceus, no gradients, no cards inside cards, no icons in buttons, no uppercase labels, no em dashes.
