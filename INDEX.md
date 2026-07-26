---
type: synthesis
title: Index
aliases: ["catalog", "toc", "index"]
status: derived
last_verified: 2026-07-24
tags: [meta]
---

# Index — Hawaiʻi election & campaign law

Catalog of the wiki. Read this first when answering a question, then drill in. Schema and
workflows: `CLAUDE.md`. Front door: [[overview]].

**Last ingest: 2026-07-24** — the HRS election-law corpus, 14 chapters.
**Counts:** 3 sources · 393 statute pages · 14 chapter hubs · 2 concepts · 1 agency · 484 citation
edges.

Status legend: `verified` traced to primary source · `derived` synthesized from verified pages ·
`unverified` secondary source, needs a primary check · `contested` sources disagree · `superseded`.

**Depth legend** *(added 2026-07-24)*: `harvested` = verbatim statute text plus a mechanically
extracted citation graph, **no operational reading written**. `annotated` = a hand-written reading
sits in the page's curated block. Both are `verified` as to the quoted text. **`harvested` is
honest, not finished** — it means the words are right and nobody has told you what they mean.
380 pages are `harvested`; 13 are `annotated`.

---

## The rule that makes this vault safe

*(Carried forward verbatim in substance from the vault's founding note.)*

**A statute note without a citation is worse than no note.** Law changes, and a confidently-worded
uncited paragraph is exactly the poisoning failure this whole structure exists to prevent. Every
note carries its citation and the date it was pulled. When a legal answer matters, cite the section
and say when the text was retrieved, so the reader can check it.

**Official sources only:** the Capitol site and the HRS full text, the Office of Elections, the
Campaign Spending Commission, the courts. Third-party aggregators and summaries are a provenance
step down and do not belong here without the official citation beside them.

Legal research supports the work; it is not legal advice, and anything consequential goes to a
lawyer.

---

## Start here

| Page | What it is |
|---|---|
| [[overview]] | Front door. Six territories of the domain with coverage status. |
| [[sources-of-law]] | **What this vault does not hold.** All eight layers of Hawaiʻi law, the verified primary source for each, and why the citation graph cannot see seven of them. Read before trusting any answer to be complete. |
| [[hrs-citation-graph]] | **How to ask what a statute references.** The query tool, the three citation zones, what the graph does and does not claim. |
| [[har-citation-graph]] | **How to ask which rule executes a statute.** The rule layer: 24 titles, 1,595 chapters, 42,002 cross-layer edges. Five zones, typed relations, and why `Auth:` ≠ `Imp:`. |
| [[deadlines]] | Every date-driven obligation for the 2026 cycle, reconciled against statute. `verified` |
| [[citation-queue]] | Everything the corpus cites but does not contain. Generated. |
| [[open-questions]] | Known gaps, corrected assumptions, what to annotate next. |
| [[log]] | Append-only chronological record. |

---

## Load-bearing provisions

The statutes this operation actually runs on.

| Provision | Governs | Status |
|---|---|---|
| HRS §11-102(b) | Mail-ballot registration and address-update cutoffs (10-day / 7-day) | ✅ [[hrs-11-102]] `annotated` |
| **HRS §11-24(a)** | **Closing the register, and the weekend/holiday rollover that explains the published dates** | ✅ [[hrs-11-24]] `annotated` |
| HRS §11-15.2 | Same-day in-person registration at a voter service center | ✅ [[hrs-11-15.2]] `annotated` |
| HRS §11-15.3 | Online registration, and why it does not get a ballot mailed after the cutoff | ✅ [[hrs-11-15.3]] `annotated` |
| HRS §11-92.1 | Voter service centers and places of deposit | ✅ [[hrs-11-92.1]] `annotated` |
| HRS §12-31 | Party-ballot selection. **Cross-party marks void the whole primary ballot.** | ✅ [[hrs-12-31]] `annotated` — *and it is not what the old queue said it was* |
| HRS §11-391 | Advertisement disclaimers, expressly including electronic means | ✅ [[hrs-11-391]] `annotated` |
| HRS §11-302 | Campaign finance definitions, the Part XIII vocabulary | ✅ [[hrs-11-302]] `annotated` |
| HRS §11-357 | Contribution limits | ✅ [[hrs-11-357]] `annotated` |
| HRS §11-334 | Candidate committee reporting calendar | ✅ [[hrs-11-334]] `annotated` |
| HRS §19-3 | Election frauds, bribery, intimidation | ✅ [[hrs-19-3]] `annotated` |
| HRS ch. 11 pt. XIII | Campaign finance generally, all 10 subparts | 🟡 all 86 sections `harvested`, 4 annotated |
| Escheat of unused campaign funds | What happens to leftover committee money | ⬜ not ingested — `projects/escheat-investigation/` |
| TCPA as applied in Hawaiʻi | Political texting consent | ⬜ **not yet researched, owed** |

---

## Statutes — by chapter

393 sections across 14 chapters. Each hub lists its sections with catchlines and reference counts.
Do not browse the folder; start at a hub or query the graph.

| Chapter | Title | Sections | Hub |
|---|---|---:|---|
| 10 | Office of Hawaiian Affairs | 49 | [[hrs-ch10]] |
| **11** | **Elections, Generally** | **212** | [[hrs-ch11]] |
| 12 | Primary Elections | 17 | [[hrs-ch12]] |
| 13 | Board of Education | 0 | [[hrs-ch13]] |
| 13D | Board of Trustees, OHA | 5 | [[hrs-ch13d]] |
| 14 | Presidential Elections | 13 | [[hrs-ch14]] |
| 14D | National Popular Vote compact | 1 | [[hrs-ch14d]] |
| 15 | Absentee Voting | 17 | [[hrs-ch15]] |
| 15D | Uniform Military and Overseas Voters Act | 19 | [[hrs-ch15d]] |
| 16 | Voting Systems | 21 | [[hrs-ch16]] |
| 17 | Vacancies | 7 | [[hrs-ch17]] |
| 19 | Election Offenses | 8 | [[hrs-ch19]] |
| 25 | Reapportionment | 9 | [[hrs-ch25]] |
| 50 | Charter Commissions | 15 | [[hrs-ch50]] |

**Chapter 11 Part XIII is the campaign finance statute**, §11-301 to §11-435, in ten subparts:
A General Provisions · B Campaign Spending Commission · C Registration · D Reporting and Filing ·
E Contributions · F Loans · G Expenditures · H Advertisements · I Enforcement · J Partial Public
Financing.

**[[hrs-11-1|§11-1]] defines terms for the entire title**, not just chapter 11. Chapters 12 through
19 inherit those definitions. Check it before reading a term anywhere in the corpus.

---

## Concepts

| Page | What it is | Status |
|---|---|---|
| [[mail-ballot-registration-cutoff]] | The 10-day register / 7-day address-update rule, why late online registration still gets no ballot, and the GOTV copy risk | `verified` |
| [[ballot-package]] | The four statutorily required contents, prepaid postage, envelope language requirements | `verified` |

## Agencies

| Page | What it is | Status |
|---|---|---|
| [[county-clerks]] | County Elections Divisions. Written from §11-102 alone, before the corpus existed — **due for a rebuild** | `derived` |

## Procedures

*None yet.*

## Opinions

*None yet — CSC advisory opinions, AG opinions, court decisions.*

## Questions

*None yet. Filed-back answers to Sam's queries land here.*

## Sources

| Page | Publisher | Retrieved | Tier |
|---|---|---|---|
| [[src-2026-07-24-hrs-election-law-corpus]] | capitol.hawaii.gov, discovered via elections.hawaii.gov | 2026-07-24 | Primary |
| [[src-2026-07-24-hrs-11-102]] | capitol.hawaii.gov (HRS Current) | 2026-07-24 | Primary |
| [[src-2026-07-24-oe-election-dates-2026]] | State Office of Elections | 2026-07-24 | Primary (dates) / secondary (legal description) |
| [[src-2026-07-25-lrb-har-table-and-directory]] | Legislative Reference Bureau | 2026-07-25 | Primary (the only authoritative HAR enumeration and the only published statute→rule crosswalk) |

---

## The HAR layer

Enumerated and cross-referenced 2026-07-25; **rule text not yet harvested**. Every chapter below is
`depth: harvested`-equivalent at best — the corpus knows a chapter exists, what it is called, and
which statute it claims to implement, and does not yet know what it says.

| | |
|---|---|
| Titles | **24**, numbered by department (title 3 DAGS, title 11 Health, title 19 DOT) |
| Chapters | **1,595** total, **991** live, the rest repealed or reserved |
| Cross-layer edges | **42,002** HRS→HAR `implements`, over 4,431 HRS sections and 19,633 HAR sections |
| Session-law edges | **455** |
| Text harvested | **0 bytes.** Download cost projected ~365 MB across ~20 department sites |
| Nearest to this wiki | [[har-3-160]] (CSC, 141 edges into HRS ch. 11) · [[har-3-161]] · `3-170`, `3-177` (Elections) |

**Title 2 subtitle 4 "Elections" is entirely repealed** — chs 34–38, 40, 50–54, plus 2-14.1/2-14.2.
The CSC rules that the 2001 crosswalk points at (`2-51`, `2-14.1`) are dead; they are now
[[har-3-160]] and [[har-3-161]] under DAGS. Do not cite the 2001 table.

---

## Tooling

The corpus is regenerable. Scripts in `tools/`, data in `graph/`, immutable sources in `raw/`.

```
python tools/harvest_hrs.py    # fetch from capitol.hawaii.gov  (--refresh to re-pull)
python tools/build_graph.py    # parse   -> graph/ (sections, edges, hrs.db, queue)
python tools/build_pages.py    # write   -> statutes/
python tools/build_queue.py    # write   -> citation-queue.md
python tools/annotations.py    # inject bulk-written curated blocks
python tools/hrs_refs.py 11-302 --both --depth 2      # query the statute graph

python tools/har_directory.py  # LRB PDF -> graph/har-universe.json  (24 titles, 1,595 chapters)
python tools/har_crosswalk.py  #         -> graph/har-edges.json     (42,002 cross-layer edges)
python tools/har_sources.py    #         -> graph/har-sources.json   (where each title's text lives)
```

`graph/*.db` is **not** tracked — it is derived from tracked JSON by one command, and a
page-structured binary costs its full size in every commit forever. Neither are PDFs; `raw/har/`
holds extracted text plus a SHA-256 per source PDF, which is what ties text to retrieval.

**Hand-written analysis lives between `<!-- BEGIN CURATED -->` and `<!-- END CURATED -->` and
survives regeneration.** Everything outside those markers is rebuilt from the graph. A page with no
markers is never overwritten; the generator reports it instead.

## Referenced but not yet written

`[[office-of-elections]]` · `[[campaign-spending-commission]]` · `[[election-period]]` ·
plus every out-of-corpus statute in [[citation-queue]], which Obsidian also surfaces natively in
its unresolved-links view.
