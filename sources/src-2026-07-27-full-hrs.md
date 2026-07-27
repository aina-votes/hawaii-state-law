# Source record — the full HRS (every chapter, every section)

**Date:** 2026-07-26 → 2026-07-27 (overnight harvest)
**Layer:** HRS, complete. Layer 3 goes from 421 sections (~1.8%) to the whole statute book.
**Tools:** `tools/harvest_hrs_all.py` (new) → `tools/build_graph.py` → `tools/build_definitions.py`
→ `tools/db_build.py` → `tools/snapshot.py`.

## Harvest

Work-list = `graph/hrs-universe.json` — the State's own volume/chapter listings enumerated
2026-07-24 (1,108 chapter directories, 22,973 section files). NOT a recon list; the listing is
the authority, and the harvester re-checks it live per chapter (zero drift found).

**22,972 of 22,973 sections fetched. Zero fetch failures across ~24k requests.** Sequential,
polite (~1/s), resumable via a listings cache; ~6.5h wall-clock. The gap of 1 is
`HRS_0431-0009A-0101_[OLD].htm` — a superseded duplicate the State left in the ch. 431
directory, excluded deliberately (the current §431:9A-101 is in).

Server-side filename defects found and healed (all recorded in
`raw/hrs/_harvest_problems.json`):

- `%C2%AD` — a URL-encoded **soft hyphen inside a filename** (§291-24.4). The U+00AD class
  from schema rule 0, now observed in a filename.
- `.docx.htm` double extensions (§§663E-10, 663E-11, 663E-12).
- `_[OLD]` superseded-copy suffix (the one exclusion above).

`file_to_section` sanitizes all three; colon (article) chapters parse from their three-part
filenames (`HRS_0412-0001-0100.htm` → §412:1-100).

## Parse fixes the full corpus forced

- **Colon-form citations** (§412:2-105, §431:10A-301): `_SEC` now matches them (3-digit
  chapter guard keeps clock times out). Regression on the prior corpus: +2 recovered edges,
  0 lost. Closes the open question carried since 2026-07-25.
- **Colon-form section headers** in `SEC_START_RE` + the catchline regex, and the
  **bracketed-section convention** (`[§46-55 Catchline.]` closes as `.]`): no-catchline
  problems fell 3,093 → 94 (0.4%, long-tail formatting, recorded).

## Result

- **22,972 HRS sections / 38,759 hrs_text edges** (28,224 operative / 4,375 renumbering /
  6,199 annotation-zone); 1,463 repealed/reserved; 1,110 sections accounted for by range
  repeals; 4,814 unresolved citation targets (leads, recorded).
- **Definitions: 151 → 12,146** statute-declared, scope-resolved terms — the mechanical
  concept backbone at full scale ("employer" ×35 scopes, "agency" ×33).
- DB total (with HAR 566 chapters + Constitution + CSC AOs): **34,912 sections, 138,672
  edges, 100,961 FTS zone rows, 233MB. All validation checks pass; annotations/doctrine
  preserved.**
- Snapshot: `hawaii-law/snapshots/hawaii-law-2026-07-27-740fce06.db.gz` (57.6MB, verified).

## Same-window HAR additions (see [[src-2026-07-26-har-text-at-scale]] for the base pass)

- **Gap harvest** (`har_gap_harvest.py`): 102 of 312 targets recovered (+76 chapters,
  +1,667 sections); 210 unfound recorded per-title with pages searched
  (`raw/har/_pdf/_gap_discovery.json`).
- **Title 20** recovered from the primary after the VPN came off — the `www.hawaii.edu`
  TCP resets and archive.org 429s were **VPN-exit-IP reputation blocks**, not agency
  behavior. HAR layer: 566 chapters / 11,768 sections / 56,559 rule_text edges.

## Currency

Everything fetched 2026-07-26/27 from `hrscurrent` (the 2024 replacement volumes + 2025
supplement era). Per-section `retrieved` dates in headers and DB. The session-law feed
(ingest-order: act→HRS bridge with hi-leg-db) is the staleness guard still owed.
