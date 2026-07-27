# Source record — HAR text at scale (all-titles harvest)

**Date:** 2026-07-26
**Layer:** HAR (administrative rules), rule TEXT at scale — the ingest-order step after CSC
advisory opinions.
**Tools:** `tools/har_harvest.py` → `tools/har_extract_all.py` → `tools/har_parse_all.py` →
`tools/db_build.py` → `tools/snapshot.py`. Per-document provenance (URL, source page, SHA-256,
retrieval date, chapter hint) in `raw/har/_pdf/_downloads.json`; extraction manifest in
`raw/har/txt/_extract.json`; both gitignored with the cache, hashes preserved in the DB's
`sources` table (one row per chapter).

## What was fetched

Work-list of 792 documents across the 24 title sites, assembled from the 2026-07-25 recon link
lists plus live re-enumeration where recon under-recorded:

- **Title 11 (Health):** recon saved a 10-link sample; live index re-enumeration found 164 PDFs.
- **Title 12 (Labor):** six divisional find-a-law subpages recursed live.
- **Title 8 (Education):** 21 of recon's 55 URLs were 404s — stale/wrong names. Re-enumerated
  live; all 55 real PDFs fetched. **Lesson re-learned: recon agents report wrong answers with
  full confidence; a link list is a claim, not a fact.**
- **Extras outside the LRB-directory recon:** HAR 3-170 (Elections Commission) and 3-177
  (Office of Elections) from `elections.hawaii.gov/resources/election-laws/`.

**740 documents downloaded and verified `%PDF`** across 20 titles. Not fetched, with reasons:

| What | Why |
|---|---|
| Titles 1, 9, 22 | no rules published online (per LRB + recon; title 22 Judiciary rules exist on paper, no public URL found) |
| Title 20 (UH, 28 docs) | `www.hawaii.edu` resets connections to both urllib and curl — blocked at TCP/TLS level. Retry owed. |
| t16 HAR-16-16, t17 17-1709-2/3 | genuine 404s at the agency (dead links on their own index) |

Politeness: sequential, 0.7s pause, 429-aware backoff (budget.hawaii.gov throttled hard —
~20-80s waits honored), resumable by manifest.

## Extraction

pdfplumber, verbatim, one page per formfeed, parallel workers. 740 extracted. **243 documents
(~33%) have no text layer** — pure scans (chars ≈ page count): t11 Health 109 of 160, t17 DHS
37, t04 Agriculture 25, t14 HRD 17 of 19. These are the **OCR tail**: mapped, hashed, cached,
unread. Same class as the 7 CSC AO scans.

## Parse

497 text-bearing docs → **480 chapters kept / 9,953 sections / 47,258 typed edges**
(attestation `rule_text`), including **4,976 federal edges** (3,994 CFR / 948 USC / 94 P.L.)
from Auth/Imp notes — the health and human-services titles implement federal law directly.

Honesty ledger, all in `graph/har_text_problems.json` and the DB `problems` table:

- **14 chapters quarantined** (parse-integrity: TOC-unmatched >20% or majority-empty operative),
  incl. 18-235 income tax (64 TOC sections) and 17-1739. Mapped-not-read until layout work.
- **10 OCR-suspect stray chapters dropped** (out-of-universe ids minted beside a real parsed
  chapter, e.g. `11-74` from inside the 11-174 doc).
- **10 out-of-universe chapters KEPT** (substantial text the 2025 LRB Table does not list:
  23-601…604 from the DCR consolidated PDF, 17-799.1, 15-316, 13-60.41…) — the compilation
  trails the rules it compiles.
- **99 partial-vs-LRB chapters** — the posted PDF is an excerpt (e.g. 4-42: 2 sections posted,
  LRB expects 43).
- **LRB Imp crosswalk two-attestation check: 6,336 rules agree / 1,686 differ** — each
  disagreement recorded as a finding, never normalised. Includes a `231-19.5` vs `213-19.5`
  digit transposition (2-73-16).
- **207 section headers repaired via TOC corroboration** (OCR'd `§` → `5`/`S`); **222 note
  cites healed** (LRB- or corpus-attested only: `92F-ll`→`92F-11`, `92Y-ll`→`92F-11`,
  spaced-out digits); every repair logged.
- ~2,000 leftover-digit flags remain (mostly severely OCR-mangled old chapters, uncorroborable);
  768 missing-Imp / 641 missing-Auth (mostly genuinely absent in old rules or partial docs).

## Verification

CSC regression gate: re-parsing 3-160/3-161 through the generalized parser produces an edge set
**identical** to the committed baseline. `db_build.py` validation: all checks pass, hand-written
annotations/doctrine preserved. DB: 10,546 sections, 71.3MB.
Snapshot: `hawaii-law/snapshots/hawaii-law-2026-07-26-6ac8a544.db.gz` (verified private, 16.3MB).

## Currency caveat

Each section row carries `effective` from its own source note; chapter PDFs are as posted by
each agency as of 2026-07-26 — some agencies post rules current to 2025-2026, others post
compilations a decade old. Per-chapter `retrieved` dates are in `sources`; staleness is
per-agency, not uniform.
