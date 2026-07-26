---
type: source
title: "CSC rule text — HAR chapters 3-160 and 3-161 (chapter PDFs, eff. 2016-12-09)"
aliases: ["CSC rules PDFs", "HAR 3-160 text", "HAR 3-161 text"]
status: verified
last_verified: 2026-07-25
tags: [har, csc, campaign-finance, source]
---

# CSC rule text — HAR 3-160 and 3-161

The first **rule text** in the corpus: the Campaign Spending Commission's two HAR chapters,
ingested in full. Until this ingest the HAR layer was enumeration and LRB-table edges only.

## Provenance

| | |
|---|---|
| Publisher | Campaign Spending Commission (DAGS), `ags.hawaii.gov/campaign/` |
| Source page | <https://ags.hawaii.gov/campaign/legal-resources/hawaii-administrative-rules/> |
| 3-160 PDF | <https://ags.hawaii.gov/campaign/files/2016/12/HAR3-160120916.pdf> — 40 pp, SHA-256 `b4f2431f9938fe4c020799d35c60137b7d412f065383b4defc4b2dfc3f37c92d` |
| 3-161 PDF | <https://ags.hawaii.gov/campaign/files/2016/12/HAR3-161120916.pdf> — 48 pp, SHA-256 `19cf808a8b379ef1e1feb48beec2973896a1888434b18b4ffb4cd09056c0e992` |
| Effective | December 9, 2016 (both chapters, per cover and compilation stamps) |
| Retrieved | 2026-07-25 |
| Extracted text | `raw/har/har-3-160.txt`, `raw/har/har-3-161.txt` (verbatim, one page per formfeed) |
| Pipeline | `tools/har_text.py` → `tools/har_rules.py` → `tools/har_build_pages.py` |

The same CSC page also posts **its own HRS compilation updated July 2026**
(`HRS-JUL2026.pdf`) — a candidate source for verifying post-2016 amendments to the
campaign-finance part, logged in [[open-questions]].

## What was extracted

- **121 sections** (48 in 3-160, 5 repealed; 73 in 3-161, 1 repealed), each parsed into the
  five zones of schema rule 11 and written as a wiki page under `har/`.
- **1,047 typed edges**: `authorized_by` (from `Auth:`, previously absent from the graph
  entirely), `implements` (from `Imp:`), and operative-zone `cites`.
- Chapter hubs [[har-3-160]] and [[har-3-161]] with per-subchapter section tables.

## Print quality: this PDF pair actively fights extraction

The scan carries a rubber received-stamp on nearly every page that bleeds into the text
layer. Every defect below is recorded per-instance in `graph/har_text_problems.json`
(72 entries); none was repaired without corroboration.

- **~40 of 121 source notes lose a bracket** — the closing `]` prints as `l` or vanishes.
  Parsed with logged fallbacks (`unbracketed_source_note`).
- **Section-number misprints**: `§3-160-4 0`, `§3 161-41`, `§3-161 51` (3 repaired, logged).
- **Citations inside Auth/Imp notes break**: dropped hyphens (`11 336`), an OCR'd `I` inside
  a cite (`11- I 407`), stamp digits glued onto numbers (`11-4071`, `11-1 410`). **17 cites
  healed**, each corroborated by an independent arbiter before repair: the LRB 2025 Table's
  edge set for that exact rule (Imp) or existence in our harvested HRS corpus (Auth).
  Uncorroborated residue stays flagged, never guessed (`note_leftover_digits`).
- The stamp itself OCRs a new way per page (`DEC092016`, `DEC 0 9 2016`, `DECO 9 2016`,
  `nEC 09 2016`) — normalised only in the derived `effective` field.

## Independent validation

- **TOC-vs-body assertion**: every section listed in each chapter's own table of contents
  was found in the body, and vice versa — zero mismatches after the 3 logged repairs.
- **Strict sweep**: 963 citation tokens inside Auth/Imp notes checked against emitted
  edges — zero missed.
- **Two-attestation cross-check**: our rule-text `Imp:` edges vs the LRB 2025 Table's
  independently-parsed edges — **115 of 116 rules agree exactly.**

## Findings

1. **The graph can now answer validity questions for these chapters.** `Auth:` edges exist:
   nearly every CSC rule rests on [[hrs-11-314|HRS §11-314]](8) (general rulemaking), and
   3-161's procedural rules also on §91-2. A rule challenged as exceeding authority is
   tested against these, not against `Imp:`.
2. **The sole LRB disagreement is an LRB defect**: the 2025 Table lists **3-161-84
   implementing §11-314, but §3-161-84 was repealed 2016-12-09**. A stale edge in the
   LRB compilation — same defect class as title 19's chapter 150 double listing.
   Recorded in [[open-questions]].
3. **Cross-title HAR citation found**: [[har-3-160-10|§3-160-10]] (government records)
   cites HAR §2-71-31 — the **OIP records rules, a title-2 chapter hosted under title 3**
   (`foreign_title` in the universe). The five-zone parse caught it; the HRS extractor
   would have minted a phantom HRS §2-71.
4. **The shared citation extractor had two silent-loss defects**, found via this corpus and
   fixed for both layers: a pin cite breaks a list (`11-359(b), and 11-360` dropped 11-360)
   and an Oxford comma breaks the separator (`, and`). Regenerating the HRS graph with the
   fix recovered **8 edges that were silently missing** (484 → 492).

## Pages touched

121 rule pages + 2 chapter hubs (created), [[har-citation-graph]], [[INDEX]],
[[open-questions]], `graph/har-rules.json`, `graph/har_text_problems.json`, and the HRS
graph + 393 statute pages (regenerated with the extractor fix).

## Open questions raised

- Post-2016 amendments: both chapters print eff. 2016-12-09; have any sections been amended
  since? The CSC's `HRS-JUL2026.pdf` and the LRB's next Table are the check.
- HAR §2-71-31 (OIP records rules) is now cited from the corpus but not ingested.
