---
type: source
title: "HRS election-law corpus — 14 chapters harvested from capitol.hawaii.gov"
aliases: ["HRS corpus", "election law corpus", "the corpus"]
status: verified
last_verified: 2026-07-24
tags: [source, hrs, citation-graph, corpus]
sources: []
---

# HRS election-law corpus

The bulk ingest that this wiki's `statutes/` folder is built from. Every HRS section page in the
vault traces here.

## Provenance

| Field | Value |
|---|---|
| Discovery page | <https://elections.hawaii.gov/resources/election-laws/> |
| Publisher | Hawaiʻi Office of Elections (discovery), Hawaiʻi State Legislature (text) |
| Text source | `https://www.capitol.hawaii.gov/hrscurrent/…` |
| Master chapter index | <https://www.capitol.hawaii.gov/docs/HRS.htm> |
| Retrieved | 2026-07-24 |
| Method | `urllib` GET, browser User-Agent, redirects followed, charset sniffed, HTML stripped |
| Raw copies | `raw/hrs/` — 407 files (393 sections + 14 chapter listings), `raw/hrs-master-chapter-index.md` |
| Tooling | `tools/harvest_hrs.py` → `tools/build_graph.py` → `tools/build_pages.py` → `tools/build_queue.py` |

## What it covers

The 14 chapters listed under **"Hawaii Revised Statutes"** on the Office of Elections election-laws
page, in the order that page lists them:

| Ch. | Title | Sections |
|---|---|---:|
| 10 | Office of Hawaiian Affairs | 49 |
| 11 | Elections, Generally | 212 |
| 12 | Primary Elections | 17 |
| 13 | Board of Education | 0 |
| 13D | Board of Trustees, Office of Hawaiian Affairs | 5 |
| 14 | Presidential Elections | 13 |
| 14D | Agreement Among the States to Elect the President by National Popular Vote | 1 |
| 15 | Absentee Voting | 17 |
| 15D | Uniform Military and Overseas Voters Act | 19 |
| 16 | Voting Systems | 21 |
| 17 | Vacancies | 7 |
| 19 | Election Offenses | 8 |
| 25 | Reapportionment | 9 |
| 50 | Charter Commissions | 15 |
| | **Total** | **393** |

**Chapter 13 (Board of Education) is listed on the State's page but serves no section files** —
only a chapter stub. That is consistent with the chapter having been repealed in full, but the
repeal has not been traced to a session law. Recorded in [[open-questions]].

## What was extracted

- **393 section pages**, each with verbatim operative text, amendment history, and Part/subpart
  placement. See [[hrs-citation-graph]] for the graph built on top.
- **484 citations**, split into three zones that are never merged:

| Zone | Count | What it is |
|---|---:|---|
| `operative` | 409 | A citation inside the statute text. The law pointing at other law. |
| `history` | 15 | Prior-numbering provenance from the source note. Not a reference. |
| `annotation` | 60 | Revisor apparatus: Case Notes, Cross References. Not statute. |

- **68 citation targets outside the corpus**, catalogued in [[citation-queue]].

## Findings worth recording

- **Chapter 11 Part XIII is the campaign finance statute**, and it is structured in ten lettered
  subparts: A General Provisions · B Campaign Spending Commission · C Registration · D Reporting
  and Filing with the Commission · E Contributions · F Loans · G Expenditures · H Advertisements
  · I Enforcement · J Partial Public Financing. §11-301 through §11-435.
- **[[hrs-11-1|§11-1]] defines terms for the whole title, not just chapter 11** — its own words are
  "Whenever used in **this title**." Chapters 11 through 19 inherit those definitions. Any reading
  of a chapter 12 or 19 term has to check §11-1 first.
- **HRS chapter 91 (Administrative Procedure) is the single most-cited outside body of law**, 31
  operative citations. It governs how agencies make rules and run contested cases, which is the
  procedural spine under Campaign Spending Commission enforcement. It is the highest-value
  chapter not yet in the corpus.
- **Chapter 50 was renumbered from former chapter 143A.** All 15 sections carry a source note
  recording the old number. Isolated to the `history` zone so it does not read as 15 phantom
  cross-references.
- **A 2017 Hawaiʻi Supreme Court case (139 H. 386, 390 P.3d 1273)** appears in the Case Notes to
  [[hrs-11-25|§11-25]] and [[hrs-11-26|§11-26]], holding that a day on which government is closed
  counts as a holiday for computing when an act is due under HRS §1-29. That is a live lead on the
  deadline-computation question in [[open-questions]].

## Retrieval gotchas

Recorded here and in `CLAUDE.md` rule 0 because each one silently corrupts a harvest:

1. `capitol.hawaii.gov` returns **HTTP 403 to WebFetch**. A browser User-Agent is required.
2. The apex host **301-redirects to `www.`**. Without redirect-following every fetch returns a
   167-byte stub that parses as an empty page rather than failing loudly.
3. `/docs/HRS.htm` is **windows-1252**, not UTF-8. Decoding it as UTF-8 mangles the ʻokina.
4. Section filenames encode decimals as underscore groups that **concatenate**:
   `HRS_0011-0001_0005_0002.htm` is **§11-1.52**, not §11-1.5.2. Verified against the retrieved
   text of §11-1.52, §11-1.55 and §10-14.55.
5. Some section numbers use **U+2011 non-breaking hyphen** (`§10‑24`, `section 11‑15`). Eleven real
   cross-references were dropped before this was caught. Normalised at parse time; `raw/` keeps
   what the State served.
6. `elections.hawaii.gov/election-information/` **404s**; the dates widget lives in the sidebar of
   ordinary pages such as `/voting/`.

## Not covered

The election-laws page lists four other source categories, none yet ingested: U.S. Constitution
excerpts, HAVA, Hawaiʻi State Constitution excerpts, and two Hawaiʻi Administrative Rules PDFs
(Elections Commission ch. 3-170, Office of Elections ch. 3-177). Campaign finance administrative
rules are **not** on that page at all. See [[citation-queue]].

## Pages touched

All 393 pages in `statutes/`, all 14 chapter hubs, [[citation-queue]], [[hrs-citation-graph]],
[[INDEX]], [[open-questions]], [[log]].
