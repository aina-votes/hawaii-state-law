---
type: source
title: LRB — Hawaiʻi Administrative Rules 2025 Table of Statutory Sections Implemented and Directory
aliases: ["LRB HAR Directory", "Table of Statutory Sections Implemented", "2025AdminRules_Supplement.pdf"]
status: verified
last_verified: 2026-07-25
tags: [har, administrative-rules, citation-graph, enumeration, lrb, cross-layer]
sources: ["[[src-2026-07-25-lrb-har-table-and-directory]]"]
---

The single most valuable document for the HAR layer. It is simultaneously the **only
authoritative enumeration of HAR that exists** and the **only published crosswalk between
statute and rule**. Everything in `graph/har-universe.json` and `graph/har-edges.json` comes
from this one PDF.

## Provenance

| | |
|---|---|
| Publisher | Hawaiʻi Legislative Reference Bureau |
| Title | *Hawaii Administrative Rules 2025 Table of Statutory Sections Implemented, and Directory* |
| Compiled by | Melissa Lee (Researcher), Wayne Scott (Research Attorney); supervised by John Morsey, Assistant Director for Revision of Statutes |
| Published | July 2026 |
| Coverage | rules filed with the Office of the Lieutenant Governor **before 2026-01-01** |
| URL | `https://lrb.hawaii.gov/wp-content/uploads/2025AdminRules_Supplement.pdf` |
| Retrieved | 2026-07-25 |
| SHA-256 | `6d25bfff915ce0aeaeced1de58678c13b97d1c69b86b601135b00fe0efba1d1a` |
| Size | 3,102,685 bytes, 163 pages |
| Landing page | `https://lrb.hawaii.gov/admin-rules-directory/` |

The PDF itself is **not tracked in git** (see `.gitignore`); the SHA-256 above is what ties the
extracted data to this exact retrieval. `tools/har_directory.py --fetch` re-downloads it.

**The filename is misleading.** `2025AdminRules_Supplement.pdf` is not a supplement. Its own
foreword says it "replaces all of the Tables of Statutory Sections Implemented that have been
published before this date." The 2001 edition
(`2001_HIAdminRules_TableofStatutorySectionsImplemented.pdf`) is therefore **superseded** and must
not be used to build edges — see [[#The 2001 edition is superseded]].

## What it contains

Four distinct assets in one file:

1. **Title list** (p. 1) — the 24 HAR titles and the department each belongs to.
2. **Table of the HRS Sections Implemented or Interpreted by Administrative Rules** (pp. 3–118,
   PDF pages 16–123) — HRS section → the HAR sections that implement it.
3. **Table of Hawaiʻi Session Laws Implemented by Administrative Rules** (p. 119) — session law →
   HAR sections. A third layer of cross-reference this wiki did not previously have at all.
4. **HAR Directory** (pp. 121–157) — every chapter of every title, with catchline, subtitle/part
   placement, repealed/reserved status, and **the department's canonical rules URL**.

## Extracted claims

### Structure of HAR

> The Hawaii Administrative Rules format prescribed by the Revisor of Statutes is substantially
> similar to the format used in the Hawaii Revised Statutes. […] The agency rule numbering system
> consists of a series of titles, with each title divided into chapters, and each chapter divided
> into sections. A title includes all of the rules of a particular department and all other
> agencies attached to that department for administrative purposes. The first number is the title
> number, which indicates the state department that adopted the rule section.

— 2025 ed. p. 1

**24 titles**, numbered by department, not by subject. This corrects two earlier guesses: LexisNexis
sells the print set as 21 volumes, and the 2001 edition listed 23 titles. Titles 23 and 24 are
**Corrections and Rehabilitation** and **Law Enforcement**, reflecting the split of the former
Department of Public Safety. Title 4 is now **Agriculture and Biosecurity**.

### The three informational notes — this is the schema finding

> A person viewing a copy of the actual rules will find three informational notes listed at the
> end of each section. The **source note** (material in brackets) gives historical information
> concerning that particular section. Abbreviations include "Eff" (date section originally became
> effective), "am" (date section was amended), "ren" (renumbered), "comp" (compiled--merging in
> amendments and other changes to notes without modifying text of section), and "R" (repealed).
> Citations of **authority** (material in parentheses beginning with "Auth:") indicate the state
> statutes, federal statutes, or federal rules that the adopting agency asserts authorized the
> adoption of that particular section. The list of **sections implemented** (material in
> parentheses beginning with "Imp:") indicate the state statutes, federal statutes, federal rules,
> or other laws that the adopting agency asserts the particular section is implementing.

— 2025 ed. p. 1 (emphasis added)

**Our reading.** `Auth:` and `Imp:` are two *different relations* to statute and must never be
collapsed into one edge type. A rule can be authorised by a general rulemaking grant while
implementing an entirely different substantive section; a court asking whether a rule exceeds the
agency's authority looks only at `Auth:`. This is why `tools/har_lib.py` defines five zones
(`operative`, `source`, `auth`, `imp`, `annotation`) rather than reusing HRS's three, and five typed
relations rather than HRS's single untyped `cites`. See [[hrs-citation-graph]] and
[[har-citation-graph]].

The `Eff`/`am`/`ren`/`comp`/`R` vocabulary in the source note is also the raw material for the
time axis (effective-from / effective-to per node) that HRS does not yet have.

### The two caveats that bound every edge

> (1) Rule listings are only to rules that have been converted to the Hawaii Administrative Rules
> format. This does not preclude the existence of other rules implementing the same section that
> have not been converted.
>
> (2) Whether or not a particular rule section is said to implement a particular statutory section
> is a determination made solely by the administrative agency that adopted the rule.

— 2025 ed. p. 1

> Caveat: This table contains no references to rules that have not been converted to the Hawaii
> Administrative Rules format or that are exempt from the Hawaii Administrative Procedure Act
> [HRS chapter 91].

— 2025 ed., Foreword

**Our reading.** Two things follow, and both are recorded in `graph/har-edges.json` under
`relation_semantics` so they travel with the data:

- **Absence of an edge is not evidence that no rule implements a section.** Unconverted and
  HAPA-exempt rules are invisible here.
- **These are the agency's assertions**, compiled by the LRB. Not the revisor's, not a court's. An
  `implements` edge is a claim about what an agency said, and it is useful precisely because it is
  the agency's own characterisation — but it is not an adjudicated fact.

### The LRB flags 63 defects in what the agencies asserted

The table carries 63 numbered footnotes, captured in `graph/har-edges.json` under `footnotes`.
They are the revisor's staff catching agencies citing statutes that do not exist or have moved:

> 1. No such HRS section.
> 3. Probably should be 431:12-112.
> 5. Probably should be 127-9, which has since been repealed.
> 2. In the list of sections implemented for 3-177-150, "11-4" was listed twice. The second "11-4"
>    probably should be […]

Each is an inbound lead on a rule whose authority chain is broken. Kept rather than discarded.

## What was built from it

| Artifact | Contents |
|---|---|
| `graph/har-universe.json` | 24 titles, **1,595 chapters**, **991 live**, with catchline, subtitle, part, repealed/reserved, canonical URL |
| `graph/har-edges.json` | **42,002** HRS→HAR `implements` edges over **4,431** distinct HRS targets and **19,633** distinct HAR sections; **455** session-law edges; 63 footnotes |
| `graph/har-sources.json` | per-title publication shape, document counts, byte sizes, corpus size estimate |
| `graph/har_directory_problems.json` | 6 entries, all defects in the source — see below |
| `graph/har_crosswalk_problems.json` | 14 entries, all source typos — see below |

## Defects in the source, recorded not repaired

Under schema rule "if a raw source is wrong, that fact gets recorded on its source page, never by
editing the raw file."

**The Directory lists six chapters twice.** Title 15 lists chapters 210, 211, 301, 310 and 321
under two different subtitles each, and for **15-301** and **15-310 the two listings give different
catchlines**:

| Chapter | First listing | Second listing |
|---|---|---|
| 15-301 | "Kikala-Keokea Revolving Loan Program" (Subtitle 5, HHFDC) | "Kikala-Keokea Housing Revolving Fund Program" (Subtitle 14, HHFDC) |
| 15-310 | "Pineapple Workers and Retirees Housing Assistance **Fund** Program" (Subtitle 5) | "Pineapple Workers and Retirees Housing Assistance Program" (Subtitle 14) |
| 19-150 | "Autonomous Vehicle Regulations" (Subtitle 5, Motor Vehicle Safety Office) — **live** | "Repealed" (Subtitle 6, Statewide Transportation Planning Office) |

HAR chapter numbers are unique within a title, so these are contradictions in the compilation. Both
listings are kept and flagged `duplicate_listing`; deduping would pick a winner arbitrarily and hide
the conflict. **19-150 is the one that matters operationally** — whether Hawaiʻi's autonomous-vehicle
rules are in force cannot be answered from this document.

**Ten keys in the crosswalk are malformed in the source**: `92F-__` (a literal blank), `189-)3.5`,
`321-.15.6`, `431:7-`, `431:10C-B`, `157.31`, `348.3`. Three HAR citations are consequently
unreachable (`4-60-13`, `16-19-1`, and one under `157.31`). Not guessed at — a fabricated pin cite is
worse than a recorded gap.

**One chapter has no catchline**: HAR 23-700, carrying footnote 64, "Title probably should be
'Hawaii Paroling Authority'."

## The 2001 edition is superseded

`2001_HIAdminRules_TableofStatutorySectionsImplemented.pdf` (638,824 bytes, SHA-256
`257bf67b0adf3bdc4a6d0fa439aa8e245f7e8a31aa482d6bceae6c3c39f14d5c`, retrieved 2026-07-25) was
fetched and read before the 2025 edition was understood. It is expressly superseded and **was not
used to build any edge**. It retains one narrow use: diffing it against the 2025 edition would show
which rules moved or died over 24 years.

It is also actively misleading if used directly. It maps HRS §11-54 → HAR 2-51-43 and HRS §11-103 →
HAR 2-14.1-11 — the Campaign Spending Commission's old election rules under the Lieutenant
Governor's title. **Those chapters are now repealed** and the CSC's rules live at
[[har-3-160]]/[[har-3-161]] under DAGS. See [[campaign-spending-commission]].

## Pages touched

- [[har-citation-graph]] — created; how to query these edges and what they do not claim
- [[sources-of-law]] — the HAR row moves from "not held" to enumerated
- [[hrs-citation-graph]] — the `Auth:`/`Imp:` distinction, and the colon-form gap below
- [[INDEX]], [[log]], [[open-questions]]

## Open questions raised

1. **`tools/hrs_lib.py` cannot parse colon-form HRS citations.** Chapters 412 (Code of Financial
   Institutions), 431 (Insurance Code) and 490 (UCC) number sections `412:2-105`, `431:10A-301`.
   The crosswalk uses that form for 289 keys; `_SEC` in `hrs_lib.py` is
   `\d+[A-Z]?-\d+(?:\.\d+)?`, which does not match it. The current HRS corpus (chapters 10–50) does
   not use the form, so nothing is broken **yet** — but any HRS harvest reaching chapter 412 or 431
   will silently drop these cross-references. Filed in [[open-questions]].
2. Is HAR 19-150 (autonomous vehicles) in force? The Directory contradicts itself.
3. Are the 63 footnoted defects still uncorrected in the current rule text?
4. Title 22 (Judiciary) and Title 21 (State Ethics Commission) have LRB-listed live chapters;
   whether the text is published online is unresolved.
