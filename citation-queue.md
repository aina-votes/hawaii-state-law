---
type: synthesis
title: "Citation queue — cited but not yet ingested"
aliases: ["citation queue", "ingest queue", "unresolved citations"]
status: derived
last_verified: 2026-07-25
tags: [meta, citation-graph, queue]
sources: ["[[src-2026-07-24-hrs-election-law-corpus]]"]
---

# Citation queue — cited but not yet ingested

Every statute, rule, and constitutional provision that the harvested corpus points at but does **not** contain. Generated from `graph/unresolved.json`; regenerate with `python tools/build_queue.py`. Do not hand-edit above the curated block.

Built 2026-07-25 from the 14 HRS chapters listed on the Office of Elections [election-laws page](https://elections.hawaii.gov/resources/election-laws/). See [[INDEX]] and [[hrs-citation-graph]].

**How to read the zone column.** `statute` means the citation sits in operative statutory text — the law itself points there, so the gap is real. `notes` means it appears only in the revisor's Case Notes or Cross References, which is a weaker signal. `history` means it is prior-numbering provenance in a source note, not a reference at all.

## 1. Whole HRS chapters cited from inside the corpus

Ranked by how often the corpus reaches for them. These are the highest-value additions: each one is a body of law our statutes actively depend on.

| Chapter | Official title | Cites | Zone | Cited by |
|---|---|---:|---|---|
| **HRS ch. 91** | Administrative Procedure | 31 | statute | [[hrs-10-18\|§10-18]], [[hrs-10-21\|§10-21]], [[hrs-11-2\|§11-2]], [[hrs-11-4\|§11-4]], [[hrs-11-7.5\|§11-7.5]], [[hrs-11-8.5\|§11-8.5]], [[hrs-11-25\|§11-25]], [[hrs-11-42\|§11-42]], +21 more |
| **HRS ch. 76** | Civil Service Law | 10 | statute | [[hrs-10-10\|§10-10]], [[hrs-10-12\|§10-12]], [[hrs-10-27\|§10-27]], [[hrs-11-1.6\|§11-1.6]], [[hrs-11-5\|§11-5]], [[hrs-11-7.5\|§11-7.5]], [[hrs-11-314\|§11-314]], [[hrs-25-5\|§25-5]], +1 more |
| **HRS ch. 92F** | Uniform Information Practices Act (Modified) | 4 | statute/notes | [[hrs-11-14\|§11-14]], [[hrs-11-97\|§11-97]], [[hrs-11-122\|§11-122]], [[hrs-15d-14\|§15D-14]] |
| **HRS ch. 89** | Collective Bargaining in Public Employment | 3 | statute | [[hrs-11-5\|§11-5]], [[hrs-11-314\|§11-314]] |
| **HRS ch. 103D** | Hawaii Public Procurement Code | 2 | statute | [[hrs-10-17\|§10-17]], [[hrs-11-5\|§11-5]] |
| **HRS ch. 92** | Public Agency Meetings and Records | 2 | statute | [[hrs-11-403\|§11-403]], [[hrs-11-410\|§11-410]] |
| **HRS ch. 37** | Budget | 1 | statute | [[hrs-10-14.5\|§10-14.5]] |
| **HRS ch. 662** | State Tort Liability Act | 1 | statute | [[hrs-10-16\|§10-16]] |
| **HRS ch. 103F** | Purchases of Health and Human Services | 1 | statute | [[hrs-10-17\|§10-17]] |
| **HRS ch. 103** | Expenditure of Public Money and Public Contracts | 1 | statute | [[hrs-11-5\|§11-5]] |
| **HRS ch. 560** | Uniform Probate Code | 1 | statute | [[hrs-11-23\|§11-23]] |
| **HRS ch. 602** | Courts of Appeal | 1 | statute | [[hrs-11-51\|§11-51]] |
| **HRS ch. 831** | Uniform Act on Status of Convicted Persons | 1 | notes | [[hrs-11-117\|§11-117]] |
| **HRS ch. 78** | Public Service | 1 | statute | [[hrs-11-314\|§11-314]] |
| **HRS ch. 84** | Standards of Conduct | 1 | statute | [[hrs-11-316\|§11-316]] |
| **HRS ch. 853** | Criminal Procedure: Deferred Acceptance of Guilty Plea, Nolo Contendere Plea | 1 | statute | [[hrs-11-412\|§11-412]] |
| **HRS ch. 329** | Uniform Controlled Substances Act | 1 | notes | [[hrs-50-15\|§50-15]] |

## 2. Individual sections cited from outside those chapters

Grouped by parent chapter. Ingesting the parent chapter picks these up.

### HRS ch. 143A — *(title not found in master index)*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §143A-1 | 1 | history | [[hrs-50-1\|§50-1]] |
| §143A-2 | 1 | history | [[hrs-50-2\|§50-2]] |
| §143A-3 | 1 | history | [[hrs-50-3\|§50-3]] |
| §143A-4 | 1 | history | [[hrs-50-4\|§50-4]] |
| §143A-5 | 1 | history | [[hrs-50-5\|§50-5]] |
| §143A-6 | 1 | history | [[hrs-50-6\|§50-6]] |
| §143A-7 | 1 | history | [[hrs-50-7\|§50-7]] |
| §143A-8 | 1 | history | [[hrs-50-8\|§50-8]] |
| §143A-9 | 1 | history | [[hrs-50-9\|§50-9]] |
| §143A-10 | 1 | history | [[hrs-50-10\|§50-10]] |
| §143A-12 | 1 | history | [[hrs-50-11\|§50-11]] |
| §143A-13 | 1 | history | [[hrs-50-12\|§50-12]] |
| §143A-14 | 1 | history | [[hrs-50-13\|§50-13]] |
| §143A-15 | 1 | history | [[hrs-50-14\|§50-14]] |
| §143A-16 | 1 | history | [[hrs-50-15\|§50-15]] |

### HRS ch. 286 — Highway Safety
*Title 17. Motor And Other Vehicles*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §286-111 | 2 | statute | [[hrs-11-15.7\|§11-15.7]] |
| §286-111.5 | 1 | notes | [[hrs-11-15.7\|§11-15.7]] |
| §286-303 | 2 | statute | [[hrs-11-15.7\|§11-15.7]] |
| §286-303.5 | 1 | notes | [[hrs-11-15.7\|§11-15.7]] |

### HRS ch. 26 — Executive and Administrative Departments
*Title 4. State Organization And Administration, Generally*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §26-34 | 3 | statute | [[hrs-11-7\|§11-7]], [[hrs-11-311\|§11-311]] |
| §26-35 | 1 | statute | [[hrs-11-317\|§11-317]] |

### HRS ch. 1 — Common Law; Construction of Laws
*Title 1. General Provisions*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §1-28.5 | 2 | statute | [[hrs-25-2\|§25-2]] |
| §1-29 | 2 | notes | [[hrs-11-25\|§11-25]], [[hrs-11-26\|§11-26]] |

### HRS ch. 831 — Uniform Act on Status of Convicted Persons
*Title 38. Procedural And Supplementary Provisions*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §831-2 | 3 | statute | [[hrs-11-23\|§11-23]], [[hrs-12-3\|§12-3]] |

### HRS ch. 673 — Native Hawaiian Trusts Judicial Relief Act
*Title 36. Civil Remedies And Defenses And Special Proceedings*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §673-2 | 1 | statute | [[hrs-10-9.5\|§10-9.5]] |
| §673-10 | 1 | notes | [[hrs-10-16\|§10-16]] |

### HRS ch. 78 — Public Service
*Title 7. Public Officers And Employees*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §78-4 | 1 | notes | [[hrs-50-4\|§50-4]] |
| §78-5 | 1 | notes | [[hrs-50-10\|§50-10]] |

### HRS ch. 40 — Audit and Accounting
*Title 5. State Financial Administration*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §40-81 | 1 | statute | [[hrs-10-13\|§10-13]] |

### HRS ch. 201H — Hawaii Housing Finance and Development Corporation
*Title 13. Planning And Economic Development*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §201H-1 | 1 | statute | [[hrs-10-13.6\|§10-13.6]] |

### HRS ch. 657 — Limitation of Actions
*Title 36. Civil Remedies And Defenses And Special Proceedings*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §657-1.5 | 1 | notes | [[hrs-10-16\|§10-16]] |

### HRS ch. 321 — Department of Health
*Title 19. Health*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §321-4.7 | 1 | notes | [[hrs-10-20\|§10-20]] |

### HRS ch. 39 — State Bonds
*Title 5. State Financial Administration*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §39-55 | 1 | statute | [[hrs-10-25\|§10-25]] |

### HRS ch. 28 — Attorney General
*Title 4. State Organization And Administration, Generally*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §28-8.3 | 1 | statute | [[hrs-11-5\|§11-5]] |

### HRS ch. 621 — Evidence and Witnesses, Generally
*Title 33. Evidence*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §621-7 | 1 | statute | [[hrs-11-43\|§11-43]] |

### HRS ch. 572C — Reciprocal Beneficiaries
*Title 31. Family*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §572C-3 | 1 | statute | [[hrs-11-302\|§11-302]] |

### HRS ch. 8 — Holidays and Periods of Recognition and Observance
*Title 1. General Provisions*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §8-1 | 1 | statute | [[hrs-11-343\|§11-343]] |

### HRS ch. 127A — Emergency Management
*Title 10. Public Safety And Internal Security*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §127A-2 | 1 | statute | [[hrs-11-366\|§11-366]] |

### HRS ch. 235 — Income Tax Law
*Title 14. Taxation*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §235-102.5 | 1 | statute | [[hrs-11-421\|§11-421]] |

### HRS ch. 23G — Office of the Legislative Reference Bureau
*Title 3. Legislature*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §23G-15 | 1 | notes | [[hrs-12-6\|§12-6]] |

### HRS ch. 91 — Administrative Procedure
*Title 8. Public Proceedings And Records*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §91-1 | 1 | statute | [[hrs-12-8\|§12-8]] |

### HRS ch. 302A — Education
*Title 18. Education*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §302A-121 | 1 | notes | [[hrs-17-6\|§17-6]] |

### HRS ch. 707 — Offenses Against the Person
*Title 37. Hawaii Penal Code*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §707-700 | 1 | statute | [[hrs-19-3\|§19-3]] |

### HRS ch. 701 — Preliminary Provisions
*Title 37. Hawaii Penal Code*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §701-107 | 1 | notes | [[hrs-19-4\|§19-4]] |

### HRS ch. 706 — Disposition of Convicted Defendants
*Title 37. Hawaii Penal Code*

| Section | Cites | Zone | Cited by |
|---|---:|---|---|
| §706-610 | 1 | notes | [[hrs-19-4\|§19-4]] |

## 3. Federal law

A different legal layer. State pages must never let one of these silently answer a state-law question — see rule 9 in `CLAUDE.md`.

| Citation | Cites | Zone | Cited by |
|---|---:|---|---|
| `42 U.S.C. §1983` | 2 | notes | [[hrs-10-3\|§10-3]], [[hrs-10-12\|§10-12]] | 
| `15 U.S.C. §7001` | 2 | statute | [[hrs-15d-18\|§15D-18]] | 
| `29 U.S.C. §794d` | 1 | statute | [[hrs-11-122\|§11-122]] | 
| `15 U.S.C. §7003` | 1 | statute | [[hrs-15d-18\|§15D-18]] | 

## 4. Constitutions and administrative rules

| Citation | Cites | Zone | Cited by |
|---|---:|---|---|
| U.S. Constitution | 5 | statute/notes | [[hrs-11-113\|§11-113]], [[hrs-13d-1\|§13D-1]], [[hrs-13d-3\|§13D-3]], [[hrs-17-2\|§17-2]], [[hrs-25-2\|§25-2]] |
| Haw. Const. art. II, §7 | 1 | statute | [[hrs-13d-2\|§13D-2]] |

## 5. Not missing — covered by a range repeal

These section numbers have no page of their own because a single repealing section covers the whole range. They are accounted for, not gaps.

| Section | Repealed by |
|---|---|
| §11-2.7 | [[hrs-11-2.5\|§11-2.5]] |
| §11-72 | [[hrs-11-71\|§11-71]] |
| §11-73 | [[hrs-11-71\|§11-71]] |
| §11-74 | [[hrs-11-71\|§11-71]] |
| §11-75 | [[hrs-11-71\|§11-71]] |
| §11-94 | [[hrs-11-93\|§11-93]] |
| §11-95 | [[hrs-11-93\|§11-93]] |
| §11-134 | [[hrs-11-133\|§11-133]] |
| §11-135 | [[hrs-11-133\|§11-133]] |
| §11-136 | [[hrs-11-133\|§11-133]] |
| §11-228 | [[hrs-11-227\|§11-227]] |
| §11-229 | [[hrs-11-227\|§11-227]] |
| §14-2 | [[hrs-14-1\|§14-1]] |
| §14-3 | [[hrs-14-1\|§14-1]] |
| §14-4 | [[hrs-14-1\|§14-1]] |
| §14-5 | [[hrs-14-1\|§14-1]] |
| §14-6 | [[hrs-14-1\|§14-1]] |
| §14-7 | [[hrs-14-1\|§14-1]] |
| §14-8 | [[hrs-14-1\|§14-1]] |
| §14-9 | [[hrs-14-1\|§14-1]] |
| §14-10 | [[hrs-14-1\|§14-1]] |
| §15-8 | [[hrs-15-7\|§15-7]] |
| §19-8 | [[hrs-19-7\|§19-7]] |
| §19-9 | [[hrs-19-7\|§19-7]] |

## Also on the Office of Elections page, not yet ingested

The election-laws page lists four source categories besides the HRS chapters. None are harvested yet:

- U.S. Constitution excerpts
- Help America Vote Act (HAVA)
- Hawaiʻi State Constitution excerpts
- Hawaiʻi Administrative Rules — Elections Commission (ch. 3-170) and Office of Elections (ch. 3-177), both served as PDFs

The HAR chapters matter most: they are the operative rules under these statutes. Note that the **campaign finance** rules (HAR title 3, ch. 160) are *not* linked from this page — the Campaign Spending Commission publishes separately.

<!-- BEGIN CURATED -->
<!-- Priority calls, notes on why a chapter matters, and Sam's steer on ingest
     order go here. This block survives regeneration. -->
<!-- END CURATED -->

## Provenance

- Generated 2026-07-25 from `graph/unresolved.json` by `tools/build_queue.py`.
- Chapter titles from the State's master index: <https://www.capitol.hawaii.gov/docs/HRS.htm>, raw copy at `raw/hrs-master-chapter-index.md`.
