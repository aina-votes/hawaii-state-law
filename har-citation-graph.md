---
type: synthesis
title: The HAR citation graph — what it is, how to query it, what it does not claim
aliases: ["HAR graph", "har-edges", "har-universe"]
status: derived
last_verified: 2026-07-25
tags: [har, citation-graph, schema, cross-layer, methodology]
sources: ["[[src-2026-07-25-lrb-har-table-and-directory]]"]
---

Companion to [[hrs-citation-graph]]. That page covers statute citing statute. This one covers the
**rule layer** and, more importantly, the **edges between layers** — which the HRS graph
structurally cannot see.

Derived from [[src-2026-07-25-lrb-har-table-and-directory]]. Read that page for provenance and for
the caveats the LRB puts on its own data.

## What exists today

| File | What it holds |
|---|---|
| `graph/har-universe.json` | the enumeration: 24 titles, **1,595 chapters**, **991 live** |
| `graph/har-edges.json` | **42,002** HRS→HAR edges, **455** session-law→HAR edges, 63 LRB footnotes |
| `graph/har-sources.json` | where each title's rule text lives, and how big it is |

**There is no rule text yet.** The corpus is enumerated and cross-referenced, not harvested. That
distinction is the whole point of `depth` in [[CLAUDE]] §3, and it applies at corpus scale here:
knowing that HAR §11-55-34.08 exists, what it is called, and which statute it implements is not the
same as knowing what it says.

## Why HAR needed a new schema rather than HRS's

### Zones: HRS has three, HAR has five

An HRS section page has `operative` / `history` / `annotation`, and merging them manufactures
phantom edges ([[CLAUDE]] rule 10). A HAR **section** has five, because the revisor's format puts
*two structurally different* statutory citations in two different parenthetical notes:

| Zone | Where | What it is |
|---|---|---|
| `operative` | the rule's own text | rule pointing at rule, or at statute |
| `source` | bracketed note: `[Eff 7/1/81; am 3/4/94; comp 9/12/16]` | effective dates and amendment history — **not** a reference |
| `auth` | `(Auth: HRS §§11-193, 11-194)` | statutes the agency asserts **authorised** it to adopt the rule |
| `imp` | `(Imp: HRS §11-191)` | statutes the agency asserts the rule **implements** |
| `annotation` | after the notes | revisor or court apparatus |

**`auth` and `imp` are not the same relation and are never collapsed.** A rule can be authorised by
a general rulemaking grant while implementing an entirely different substantive section. A court
asking whether a rule exceeds the agency's authority looks only at `auth`. Collapsing them produces
a graph that answers "is this rule connected to that statute" and cannot answer "is this rule
*valid*", which is the question that matters.

### Relations: HRS has one untyped `cites`, HAR has five typed

Adding a second layer is the moment to type edges, because "statute delegates to rule" and "rule
implements statute" are opposite directions with different meanings, and re-deriving the whole graph
later is expensive. Defined in `tools/har_lib.py`:

| Relation | Direction | Source of truth |
|---|---|---|
| `cites` | either | generic reference in rule text |
| `authorized_by` | HAR section → HRS section | the rule's `Auth:` note |
| `implements` | HAR section → HRS section | the rule's `Imp:` note (and the LRB table) |
| `delegates_to` | HRS section → HAR chapter | statute text ("the department shall adopt rules") |
| `renumbered_from` | HAR section → HAR section | the `ren` abbreviation in a source note |

`implements` and `delegates_to` are near-inverses but **independently attested** — one from the
rule, one from the statute — so they are stored separately. Where they disagree, that is a finding,
not a bug to normalise away.

Only `implements` is populated today, from the LRB table. `authorized_by` needs the rule text.

### Identifiers

A HAR citation is `TITLE-CHAPTER-SECTION`: `HAR §3-160-20` is title 3, chapter 160, section 20.
Every part is messier than it looks, and each of these silently drops citations if the pattern is
too tight:

- chapters carry letters and decimals — `16-89C-35`, `18-237D-4`, `11-200.1-3`
- sections carry decimals, letters, and sometimes **a fourth part** — Taxation uses
  `HAR §18-231-9.9-07`, and one cite runs to five: `11-54-9.1.01`
- decimal points are kept in page names: `har-11-55-34.08.md`, linked `[[har-11-55-34.08]]`

**Cross-title chapters are real and are never renumbered.** A chapter that moved departments keeps
its original number, so the Directory lists them under the new title with the old prefix:

| Chapter | Listed under | Why |
|---|---|---|
| `2-71`, `2-73` | title 3 (DAGS) | Office of Information Practices, formerly under Lt. Governor |
| `6-60` … `6-83` | title 16 (DCCA) | Public Utilities Commission, formerly under Budget & Finance |
| `15-185`, `15-186`, `15-193` | title 17 (DHS) | Hawaii Public Housing Authority, formerly under DBEDT |
| `17-2006`, `17-2015`, `17-2017` | title 15 (DBEDT) | Barbers Point NAS Redevelopment, formerly under DHS |

Renumbering these to match their host title would invent citations the law does not use. They carry
`foreign_title: true`.

## How to query it

The graph is plain JSON; there is no `.db` (see `.gitignore` for why). Python:

```python
import json
E = json.load(open('graph/har-edges.json', encoding='utf-8'))['edges']
U = json.load(open('graph/har-universe.json', encoding='utf-8'))['titles']

# Which rules implement the campaign-finance statutes?
{e['src'] for e in E if e['dst'].startswith('11-3')}

# Which statutes does the CSC's rule chapter claim to implement?
sorted({e['dst'] for e in E if e['src'].startswith('3-160-')})

# Most-implemented HRS sections
import collections
collections.Counter(e['dst'] for e in E).most_common(10)

# Rules still pointing at a statute the LRB marks repealed
{(e['src'], e['dst']) for e in E if e['dst_repealed']}

# Every live chapter of a title, with catchline
[(c['chapter'], c['catchline']) for c in U['3']['chapters']
 if not c['repealed'] and not c['reserved']]
```

## Worked example: the Campaign Spending Commission

The one corner of HAR this wiki already needed. [[har-3-160]] has **141** `implements` edges, all
into HRS chapter 11's campaign-finance part — §§11-302, 11-311, 11-314, 11-321 through 11-326,
11-331, 11-333, 11-334 and more. That is the map from the statute Sam files under to the rule that
says how.

**HAR 2-51 has zero edges.** The 2001 crosswalk pointed HRS §11-54 at HAR 2-51-43, and the
Directory now shows title 2 subtitle 4 "Elections" entirely repealed — chapters 34–38, 40, 50–54,
plus 2-14.1 and 2-14.2. The CSC's rules moved to title 3 when the Commission was attached to DAGS.
Anyone reading the 2001 table, or an aggregator that mirrored it, gets a dead chapter.

## What this graph does not claim

1. **It is mostly not the rule text.** *(Narrowed 2026-07-25: [[har-3-160]] and [[har-3-161]]
   are now harvested in full — 121 sections with all five zones, in `graph/har-rules.json` and
   as `har/` pages; see [[src-2026-07-25-csc-har-rules]].)* For every other chapter, every claim
   here is about *structure and cross-reference*, not content.
2. **`implements` is the agency's assertion**, compiled by the LRB — not the revisor's
   determination and not a court's. See [[src-2026-07-25-lrb-har-table-and-directory]].
3. **Absence of an edge proves nothing.** Rules never converted to HAR format, and rules exempt from
   HRS chapter 91, are absent from the source entirely.
4. **`auth` is missing outside the CSC chapters.** *(Narrowed 2026-07-25.)* The authority
   relation cannot be read off the LRB table; it only exists in rule text. The 3-160/3-161
   harvest put the graph's first `authorized_by` edges in — the CSC's power to adopt each rule
   now traces (nearly all to §11-314(8); 3-161's procedure adds §91-2). For every other title
   the question stays unanswerable until its text is harvested.
5. **The enumeration is current to 2026-01-01**, the LRB's filing cutoff. Rules filed in the first
   half of 2026 are not here.
6. **The source contradicts itself in six places** and those are preserved, not resolved. Most
   consequentially, HAR 19-150 is listed both live and repealed.
7. **HRS is one layer of eight and this adds a second** — [[sources-of-law]]. County ordinances,
   case law, AG opinions, and the Constitution are still outside the graph.

## Next

In value-per-unit-work order:

1. **Harvest the rule text** for the titles that matter to this wiki — 3 (DAGS/CSC) and what
   remains of 2 (Elections) — then generalise. `graph/har-sources.json` is the target map.
2. **Extract `Auth:` and `Imp:` from the harvested text** and reconcile `imp` against the LRB's
   table. Disagreements are real findings: the table is a compilation and the rule is the source.
3. **Add the time axis** from the `Eff`/`am`/`comp`/`R` source notes, before session laws arrive as
   a third layer.
4. **Resolve HAR 19-150** and the five title-15 double-listings against the actual rule text.
