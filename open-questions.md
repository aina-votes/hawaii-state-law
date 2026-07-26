---
type: synthesis
title: Open questions
aliases: ["gaps", "todo"]
status: derived
last_verified: 2026-07-24
tags: [meta]
---

# Open questions

Known gaps, unresolved contradictions, and sources worth going after. Ingests both answer and add
to this list. Nothing here is a claim — these are the things the wiki does **not** know.

The mechanical version of "what have we cited but not ingested" is [[citation-queue]], generated
from the graph. This page holds the questions that need judgment rather than a fetch.

---

## Resolved

**✅ Why is the general-election registration deadline Oct 26 and not Oct 24?** *(resolved
2026-07-24 by the corpus ingest)* The rollover rule is [[hrs-11-24|§11-24(a)]], not
[[hrs-11-102|§11-102]]: the register closes ten days out, "but if the day is a Saturday, Sunday, or
holiday then at 4:30 p.m. on the first working day immediately thereafter." §11-102(b)'s seven-day
address-update deadline has no such clause, which is why Sat Aug 1 stood while Sat Oct 24 rolled to
Mon Oct 26. All four published 2026 dates now reconcile. Table on [[deadlines]].

*Two earlier passes got this wrong in opposite directions: the first attributed Oct 26 to weekend
rollover without a cite, the second concluded there was no rollover rule at all. Both were looking
only at §11-102. The lesson is in [[hrs-citation-graph]]: the answer was one citation hop away.*

**✅ Is HRS §11-15.2 really the same-day registration authority?** Yes. Confirmed against the
retrieved text — "Same day in-person registration," registration at any voter service center on or
before election day. Safe to cite in voter-facing copy. See [[hrs-11-15.2]].

---

## Corrected assumptions

**⚠️ HRS §12-31 is not "the wording constraint on vote-page copy."** It was carried at the top of
the ingest queue on that description, sourced from the `moho-vote-page` skill and memory rather
than from the statute. [[hrs-12-31|§12-31]] is *Selection of party ballot; voting*: no voter may be
required to state a party preference, every voter is issued every party's ballot, and **a primary
ballot marked across more than one party is not counted at all.**

That last point is a live and more serious copy constraint than the one we thought we were
chasing. Two things still open:

1. **Where did the "wording constraint" belief come from?** If a different provision restricts how
   a voter guide may describe the ballot, it has not been found. If it came from a non-statutory
   source (a clerk's guidance, an OoE FAQ), that should be traced and recorded as secondary.
2. **Does mohoaina.com/vote correctly warn about cross-party spoilage?** The `moho-vote-page` skill
   needs checking against [[hrs-12-31]], and so do the carousel and any primary text blast.

---

## Verification debt

- **What did Act 213 (2021) §18 and Act 166 (2022) §2 change in [[hrs-11-102]]?** If the 10-day or
  7-day figures ever moved, guidance written before the 2024 primary is wrong. Need the session
  laws. Amendment histories are now recorded on all 393 pages but **no page traces what an act
  actually changed** — that is the largest single piece of unfinished verification in the vault.
- **Did Hawaiʻi actually join ERIC?** [[hrs-11-1.52|§11-1.52]] (Act 190, 2024) *requires* the
  Office of Elections to apply by June 30, 2025 and maintain membership. The statute creates the
  duty; it does not report compliance, and ERIC membership has been politically volatile in other
  states. Confirm current status with the Office of Elections before relying on it.
- **Chapter 13 (Board of Education) serves no sections.** It is listed on the Office of Elections
  election-laws page but capitol.hawaii.gov returns only a chapter stub. Consistent with full
  repeal, but the repealing act has not been traced. See [[hrs-ch13]].
- **[[county-clerks]] is still `derived`** — assembled from one statute plus the OoE site, written
  before the corpus existed. It should be rebuilt now that [[hrs-11-92.1]], [[hrs-11-91]] and the
  chapter 11 Part VII sections are all in the vault.
- **380 of 393 statute pages are `depth: harvested`** — verbatim text and citation graph, no
  operational reading. That is honest, not finished. Priority annotation queue below.

---

## What to annotate next

Thirteen pages carry `depth: annotated`. The next tranche, in rough order of how much they unblock:

1. **Election period** — the unit the [[hrs-11-357]] contribution limits are measured over. The
   limits page is annotated but explicitly cannot be used alone without this. Part XIII subpart A.
2. **[[hrs-11-358]] and subpart E generally** — prohibited contributions, contractor bans,
   aggregation rules.
3. **Subpart C, registration** ([[hrs-11-321]]–[[hrs-11-327]]) — when a committee must register,
   and [[hrs-11-326]] termination, which is what ends candidate status under [[hrs-11-302]].
4. **Subpart I, enforcement** ([[hrs-11-401]]–[[hrs-11-412]]) — how the Commission actually acts.
5. **[[hrs-11-15]]** — application to register; the most-cited section in the corpus (9 inbound).
6. **Chapter 15 absentee** and **chapter 15D UMOVA** — both expressly preserved by §11-102(b) and
   neither has been read.
7. **Chapter 12 nomination papers** ([[hrs-12-3]], [[hrs-12-6]]) — ballot access mechanics.

---

## Cross-layer questions

- **Texting.** Hawaiʻi has no distinct political-texting statute that we have verified. The
  operating assumption is that the constraint is federal (TCPA/FCC) plus carrier policy — still an
  **assumption, not verified**. What the corpus *did* establish is that
  [[hrs-11-391|§11-391]] reaches any advertisement "communicated by electronic means," so the state
  disclaimer duty applies to SMS regardless of what TCPA requires. The TCPA question itself is
  still owed.
- **Nonprofit electoral activity.** Where the federal 501(c) line and the state noncandidate-
  committee registration trigger intersect.
- **Escheat of unused campaign funds — the statutes are now located.** Carried since the founding
  note as "not yet located in Part XIII." The corpus found them:
  - [[hrs-11-364|§11-364]] **Excess contribution; return; escheat** (subpart E, Contributions)
  - [[hrs-11-384|§11-384]] **Disposition of campaign funds; termination of registration**
    (subpart G, Expenditures)
  - [[hrs-11-326|§11-326]] **Termination of a committee's registration** (subpart C), which is also
    what ends candidate status under [[hrs-11-302|§11-302]]

  All three are `depth: harvested` — text is in, nobody has read it. Next step: annotate them,
  cross-check against `projects/escheat-investigation/` (`legal-landscape-onepager.md`,
  `methodology.md`), and give escheat its own concept page. The investigation's conclusions should
  now be traceable to statute rather than asserted.

---

## Sources worth going and getting

**Read [[sources-of-law]] first.** It maps all eight layers of Hawaiʻi law, names the verified
primary source for each, and ranks them by operative value per unit of work. The short version:
HRS is one layer of eight, the citation graph cannot see the other seven, and the highest-value
next move is **not** more HRS.

Newly verified 2026-07-24, and newly missing:

- **The Hawaiʻi Constitution, Article II (suffrage and elections)** sits above every page in this
  vault and is **absent from the HRS master index** — a crawl of `hrscurrent/` looks complete while
  omitting it. Lives at `lrb.hawaii.gov/constitution/`.
- **Session laws** at `capitol.hawaii.gov/slh/`. Two distinct gaps: the codified HRS lags the
  session, and uncodified provisions (effective dates, sunsets, applicability, findings) never enter
  HRS at all. Without this layer the corpus goes stale silently rather than loudly.
- **County charters and ordinances**, four of them, none on capitol.hawaii.gov. Election
  administration is substantially county-run and the county candidates on the roster are governed
  by these directly.
- **112 case citations and an Attorney General Opinions heading are already sitting in `raw/`**,
  in the annotation zone of 58 harvested sections. Extracting a fourth citation kind gives inbound
  case law with no new crawl. Highest value per unit of work of anything on this page.
- **AG opinions index** — ~~not located~~ **LOCATED 2026-07-25**, and it is LRB-published rather
  than AG-published, which is why every `ag.hawaii.gov` path 404s:
  `lrb.hawaii.gov/wp-content/uploads/AGOpinions.pdf` (1,694,274 bytes, verified HTTP 200,
  SHA-256 `6b24e46d3dcc3044f989079b6c657b8edbde92d48dac57f72d6c023bcb799605`). Downloaded but not
  yet parsed. Same publisher pattern as the HAR crosswalk — **when a Hawaiʻi index is missing from
  the agency that owns the subject, look at the LRB.**

- **HAR title 3, chapter 160** — the Campaign Spending Commission's administrative rules, including
  in-kind valuation. Now enumerated and cross-referenced but **text not yet harvested**:
  [[har-3-160]] carries **141** `implements` edges into HRS chapter 11's campaign-finance part.
  Two direct PDFs are known: `ags.hawaii.gov/campaign/files/2016/12/HAR3-160120916.pdf` and
  `.../HAR3-161120916.pdf`. Note these are **not** linked from the Office of Elections
  election-laws page; the CSC publishes separately.
- **HAR chapters 3-170 and 3-177** — Elections Commission and Office of Elections rules, both
  linked as PDFs from the election-laws page and not yet ingested. 3-177 is heavily cross-referenced
  in the LRB table and carries footnote 2, an LRB-flagged defect in its own `Imp:` list.

### Corrected 2026-07-25: the HAR index is not what this page said

`ltgov.hawaii.gov/the-office/administrative-rules/` is **not** the authoritative HAR index. It
carries per-department links (20 of them, which is more than a previous session credited it with)
but **omits titles 1, 9, 21 and 22 entirely**, and is stale where it disagrees with the LRB. The
authoritative enumeration is [[src-2026-07-25-lrb-har-table-and-directory]] — 24 titles, 1,595
chapters. See [[har-citation-graph]].

### New, opened by the HAR ingest

- **`tools/hrs_lib.py` cannot parse colon-form HRS citations, and will silently drop them.**
  Chapters 412 (Code of Financial Institutions), 431 (Insurance Code) and 490 (UCC) number their
  sections `412:2-105`, `431:10A-301`, `490:2-201`. `_SEC` in `hrs_lib.py` is
  `\d+[A-Z]?-\d+(?:\.\d+)?`, which does not match a colon. The LRB crosswalk uses this form for 289
  keys — 93% of the keys a chapter-section pattern rejects. **Nothing is broken today** because the
  harvested corpus (chapters 10–50) does not use the form, but any HRS harvest reaching 412, 431 or
  490 loses those cross-references without erroring. Fix `_SEC` before the next chapter expansion.
- **Is HAR 19-150 (autonomous vehicle regulations) in force?** The LRB Directory lists chapter
  19-150 twice: live under "Subtitle 5 Motor Vehicle Safety Office" as "Autonomous Vehicle
  Regulations", and "Repealed" under "Subtitle 6 Statewide Transportation Planning Office". HAR
  chapter numbers are unique within a title, so the source contradicts itself. Resolvable only
  against DOT's actual rule text. **`contested` until then.**
- **Title 15 double-lists five chapters with disagreeing catchlines** (15-210, 15-211, 15-321 agree;
  **15-301 and 15-310 do not**). Recorded in `graph/har_directory_problems.json`.
- **63 LRB footnotes flag defects in what agencies asserted** — "No such HRS section", "Probably
  should be 431:12-112", "Probably should be 127-9, which has since been repealed". Each is an
  inbound lead on a rule with a broken authority chain. In `graph/har-edges.json` under `footnotes`.
  Unreviewed.
- **The `Auth:` relation does not exist in the graph at all.** The LRB table carries only `Imp:`
  (what a rule implements). Which statute *authorised* a rule can only be read off the rule text, so
  no "did the agency have power to adopt this?" question is answerable until HAR text is harvested.
- **Ten crosswalk keys are malformed in the LRB source** (`92F-__`, `189-)3.5`, `321-.15.6`,
  `431:7-`, `431:10C-B`, `157.31`, `348.3`), leaving three HAR citations unreachable. Deliberately
  not guessed at.
- **Whether Title 22 (Judiciary) rule text is published anywhere.** The LRB lists 21 live chapters
  — Judiciary personnel rules and grants/purchase-of-service rules — distinct from the Rules of
  Court that `courts.state.hi.us` does publish.
- **HRS chapter 91 (Administrative Procedure)** — 31 operative citations from inside the corpus,
  the most-cited outside body of law, and the procedural spine under CSC enforcement. Top of
  [[citation-queue]].
- **CSC advisory opinions index** — ~~not yet located~~ **LOCATED**:
  `ags.hawaii.gov/campaign/legal-resources/advisory-opinions/`, 14 PDFs, AO10-01 through AO26-02,
  direct URLs. Still the densest single source for how the Commission actually reads Part XIII, and
  still not ingested. Also at that site: `HRS-JUL2026.pdf`, the Commission's own compilation of the
  campaign-finance statutes current to this month — a free cross-check on the HRS harvest for
  anything the 2026 session moved.
  **The site moved:** `csc.hawaii.gov` is a 135-byte meta-refresh stub, which returns HTTP 200 and
  parses as an empty page rather than failing. Narrow the earlier "dead" characterisation: the
  informational apex is a stub, but `csc.hawaii.gov/CFSPublic/menu/` and `/NCFSPublic/` are live
  filing portals still linked from the new site.
- **Session laws** for the amendment questions above.
- **139 H. 386, 390 P.3d 1273 (2017)** — cited in the Case Notes to [[hrs-11-25]] and
  [[hrs-11-26]], on when a government-closure day counts as a holiday for computing deadlines under
  HRS §1-29. Now that [[hrs-11-24]] is understood this is less urgent, but it bears on how holidays
  interact with the rollover.
