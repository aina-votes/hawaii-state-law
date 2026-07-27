---
type: synthesis
title: What actually comprises Hawaiʻi state law
aliases: ["sources of law", "layers of law", "what are we missing"]
status: derived
last_verified: 2026-07-26
tags: [meta, roadmap, sources, coverage]
sources: ["[[src-2026-07-24-hrs-election-law-corpus]]"]
---

# What actually comprises Hawaiʻi state law

This page names every layer of Hawaiʻi law, says where its primary source lives, and states
plainly what this wiki does and does not hold of it. **As of 2026-07-26 this is the coverage
ledger for the whole ambition** — Sam set the scope to *all* of Hawaiʻi law, every surface,
as a graph-mapped database; the election/campaign slice is the sequencing beachhead, not the
boundary. Two verbs matter and are tracked separately below: **mapped** (the layer's objects
and edges are enumerated in `graph/`) and **read** (the actual text is in the corpus).

**Why this page exists:** a citation graph over HRS alone will answer confidently and
be wrong, because the answer to a real question often lives in a rule, an advisory
opinion, or a county charter that the statute never cites. HRS points *down* to rules
only rarely and never points at cases at all. Absence from the graph is not absence
from the law.

Status is `derived`: the layer structure is general legal architecture, and the URLs
below were probed on 2026-07-24 and returned what is noted. Nothing here is a claim
about the *content* of any layer.

---

## The layers, in order of authority

| # | Layer | Binds | Primary source | Mapped | Read |
|---|---|---|---|---|---|
| 1 | **U.S. Constitution + federal law** | everything | uscode.house.gov, federalregister.gov | no | no |
| 2 | **Hawaiʻi Constitution** | all state and county law | `lrb.hawaii.gov/constitution/` (200, 236KB) | no | **no** |
| 3 | **HRS** (codified statutes) | statewide | `capitol.hawaii.gov/hrscurrent/` | **yes** — all 1,108 chapter dirs enumerated (`enumerate_hrs.py`) | **COMPLETE: 22,972 of 22,973 sections (2026-07-27, [[src-2026-07-27-full-hrs]])** — the whole statute book; the 1 exclusion is a superseded `[OLD]` duplicate. 12,146 scoped definitions; 38,759 typed edges. |
| 4 | **Session Laws of Hawaiʻi** (SLH) | statewide, incl. uncodified text | `capitol.hawaii.gov/slh/` (200) | partial — 455 SLH→HAR edges from the LRB Table; sibling `hi-leg-db` holds 116k measures | **no** |
| 5 | **HAR** (administrative rules) | within the agency's grant | LRB 2025 Table & Directory (authoritative); ltgov index omits 4 titles | **yes, completely** — 24 titles / 1,595 chapters / 42,002 typed HRS→HAR edges + per-title source URLs and size estimates (2026-07-25) | **566 chapters / 11,768 sections (2026-07-27, after the gap pass + title 20; [[src-2026-07-26-har-text-at-scale]] + [[src-2026-07-27-full-hrs]] §HAR).** Remaining unread-live: **210 gap-targets unfound on walked agency pages** (per-title detail in `_gap_discovery.json`; worst DLNR/DAGS-boards/DHRD — needs deeper per-board seeds), ~139 scans (OCR tail, worst in Health), 21 not published (title 22), plus quarantined layouts and excerpt-only postings (problems table). Title 20 recovered from primary 2026-07-27 — the "fetch-blocked" was a VPN-exit-IP block, not the agency. A first record claimed "everything posted online" — corrected 2026-07-26, same day: it was everything the recon-walked pages linked. |
| 6 | **Case law** | interprets 2-5, binding | `courts.state.hi.us/opinions_and_orders/opinions` (200) | no — but 112+ case cites sit unextracted in the harvested annotation zones | no |
| 7 | **Agency opinions and guidance** | persuasive to binding-in-practice | CSC AOs: `ags.hawaii.gov/campaign/legal-resources/advisory-opinions/` (14 PDFs, AO10-01–AO26-02). AG opinions: `lrb.hawaii.gov/wp-content/uploads/AGOpinions.pdf` — **LRB-published, which is why every ag.hawaii.gov path 404s** | indexes located 2026-07-25 | no |
| 8 | **County charters and ordinances** | one county each | four separate county sites | no | **no** |

---

## Layer by layer, and why each one bites

### 2. The Hawaiʻi Constitution

Article II is the suffrage and elections article and it sits **above** everything in
the harvested corpus. A statute that contradicts it loses. It also holds provisions
HRS never restates: voter qualifications, the residency and age floor, and the
initiative and amendment machinery.

It is **not in the HRS master index** on capitol.hawaii.gov, which is the trap: a
crawl of `hrscurrent/` looks complete and silently omits the supreme state authority.
The Legislative Reference Bureau publishes it separately.

### 4. Session Laws — the currency problem

This is the layer most likely to make the wiki quietly wrong, and it has two edges:

- **The codified HRS lags.** An act passed and effective this session may not be
  reflected in `hrscurrent/` yet. Reading only HRS means reading superseded law
  without any signal that you are.
- **Uncodified provisions never appear in HRS at all.** Effective dates, sunset and
  repeal clauses, severability, appropriations, applicability and transition
  provisions, and legislative findings live in the act and stay there. A rule can be
  fully in force and completely invisible to a search of HRS.

`projects/hi-leg-db/` already holds 116k measures from the Capitol, so the raw
material for tracking this is partly in hand.

### 5. HAR — where the operative detail actually lives

Statutes authorize; rules specify. The rules carry the forms, the thresholds, the
filing mechanics, the deadlines-within-deadlines. For Sam's actual filing work the
CSC's rules are closer to the day-to-day operative law than the statute is.

Three structural facts:

- **HAR is organized by department title, not by subject.** The Lt. Governor's index
  lists Title 2 = Lt. Governor, Title 3 = DAGS, Title 4 = Agriculture, and so on. So
  you must know which department houses an agency before you can find its rules.
- **The Campaign Spending Commission sits under DAGS**, which is why CSC rules are
  cited as HAR Title 3. See the CSC redirect finding below.
- **The citation graph cannot see rules.** Statutes almost never cite HAR by rule
  number; they delegate ("shall adopt rules in accordance with chapter 91"). The
  useful edges run the other way: rules cite their enabling statute. So HAR must be
  found deliberately, per agency, and it will never surface from HRS traversal.

### 6. Case law — and the seed already in the corpus

Yes, it belongs here, and it has the same one-way problem as HAR: statutes never cite
cases, cases cite statutes. So case law joins the graph as **inbound edges**, which is
the direction you actually want. "What has been held about §11-391?" is a better
question than anything the current graph answers.

**The corpus already contains the seed.** The revisor's annotation zone carries Case
Notes, and a sweep of the 393 harvested sections finds **112 case citations across 58
sections**, plus Attorney General Opinions and Law Journals and Reviews headings, all
sitting in text already on disk. Extracting a fourth citation kind (`case`) over the
annotation zone is a small job against text that has already been fetched.

Two cautions, both already demonstrated:

- **Annotation-zone citations are leads, not authority.** §11-111's Cross References
  points at §11-134, which is repealed and 404s. The revisor's notes go stale.
- **They are not exhaustive.** The revisor curates. Anything recent, unpublished, or
  federal will be missing. Hawaiʻi also issues non-precedential memorandum and summary
  dispositions, which are not citable as authority.

Federal courts matter too: D. Haw., the Ninth Circuit, and the Supreme Court set
constitutional limits on state election law, and none of them appear in an HRS crawl.

### 7. Agency opinions — binding in practice

CSC advisory opinions are the operative interpretive gloss on campaign finance. The
Commission enforces on them, so for practical purposes they bind, whatever their
formal weight. AG opinions are formally advisory and persuasive.

**Finding, 2026-07-24:** `csc.hawaii.gov` is no longer the site. It serves a
135-byte page whose entire content is `<META HTTP-EQUIV="Refresh" ... URL=http://ags.hawaii.gov/campaign/">`.
The real site is **`ags.hawaii.gov/campaign/`**. This matters twice over:

1. Both `CLAUDE.md` files still name `csc.hawaii.gov` as a primary source.
2. **A meta-refresh is not an HTTP redirect.** `curl -L` does not follow it. Any
   fetcher pointed at the old host gets HTTP 200 and 135 bytes of nothing, which
   parses as an empty page rather than failing. Same silent-corruption class as the
   403 and the apex-redirect stub already recorded in the schema.

### 8. County charters and ordinances

**Election administration in Hawaiʻi is substantially county-run.** The clerks
maintain the rolls and run the places of deposit. County charters set council
districts, term limits, and the nonpartisan structure of county races, and Honolulu
carries its own campaign-adjacent provisions.

Four separate corpora on four separate sites, none of them on capitol.hawaii.gov,
none reachable from the HRS citation graph, and directly load-bearing for the Moho
ʻĀina candidates running county races.

---

## What else could be missing

Beyond the eight layers, these are the blind spots that do not announce themselves:

- **Court rules.** Election contests go to the Supreme Court under HRS §11-172; the
  procedure is in the rules of court, not the statute.
- **Executive proclamations.** The Governor's emergency powers can move election
  administration. Exercised in Hawaiʻi within living memory.
- **Legislative history.** Hawaiʻi courts lean heavily on standing and conference
  committee reports for statutory interpretation. Available at the Capitol.
- **Repealed-but-relevant sections.** 34 of the 393 harvested sections are repealed.
  Conduct is judged under the law in force at the time.
- **Forms, instructions, and portal behavior.** What the CSC's filing system will and
  will not accept is operative in practice and written down nowhere in law.
- **Attorney General opinions index.** ~~Not located~~ **Located 2026-07-25**:
  `lrb.hawaii.gov/wp-content/uploads/AGOpinions.pdf` — LRB-published, not AG-published,
  which is why every `ag.hawaii.gov` path 404s. General pattern: when a Hawaiʻi index is
  missing from the agency that owns the subject, look at the LRB.
- **Federal overlay by name:** NVRA, HAVA, UOCAVA, the Voting Rights Act, TCPA and the
  FCC's rules on texting, FEC rules where a federal candidate is involved, and IRS
  treatment of 527 and 501(c) organizations. Schema rule 9 governs: never let a
  federal rule silently answer a state question.

---

## What this means for sequencing

Ranked by operative value per unit of work, not by authority:

| Priority | Layer | Why |
|---|---|---|
| 1 | **Case + AG citations from the annotation zone** | already fetched, 112 waiting, no new crawl |
| 2 | **HAR for CSC and Elections** | closest to Sam's actual filing work; small, targeted |
| 3 | **Hawaiʻi Constitution, Article II** | one document, sits above everything already harvested |
| 4 | **Session laws, current session forward** | the staleness guard; without it the corpus rots silently |
| 5 | **County charters, four of them** | directly binds the county candidates on the roster |
| 6 | **The other 22,580 HRS sections** | largest volume, lowest marginal value per section |

The last row is the point worth arguing with. Finishing HRS is the biggest single
crawl available and it is **not** the highest-value next move. Election law's real
unanswered questions currently sit in layers 5 through 8, not in HRS chapters 431 or
490.

*(Re-read 2026-07-26 under the all-of-law scope: the ranking above is about SEQUENCE, and it
still holds — but every row is now a destination, not an option. Full HRS, full HAR text, the
session-law feed, the case-law corpus, and the four counties are all owed; the election slice
just gets read first because it serves live filings. Watch corpus size as text layers land:
the extracted-text-plus-hashes policy is what keeps an all-of-law repo viable.)*

---

## Related

[[INDEX]] · [[overview]] · [[hrs-citation-graph]] · [[citation-queue]] ·
[[open-questions]] · [[campaign-spending-commission]] · [[deadlines]]
