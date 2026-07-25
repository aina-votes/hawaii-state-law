---
type: synthesis
title: "The HRS citation graph — how to ask what a statute references"
aliases: ["citation graph", "reference graph", "hrs graph"]
status: derived
last_verified: 2026-07-24
tags: [meta, citation-graph, tooling]
sources: ["[[src-2026-07-24-hrs-election-law-corpus]]"]
---

# The HRS citation graph

Every cross-reference in the harvested corpus, extracted and made queryable. This page explains
what the graph does and does not claim. Provenance: [[src-2026-07-24-hrs-election-law-corpus]].

## The one distinction that matters

An HRS section page from capitol.hawaii.gov contains three different kinds of text, and only the
first is law:

| Zone | Where it sits | What a citation there means | Count |
|---|---|---|---:|
| `operative` | the statute text, before the bracketed source note | **The law points at other law.** This is the real citation graph. | 409 |
| `history` | inside the source note, e.g. `[… Supp, §143A-1; HRS §50-1]` | Prior numbering. The section *used to be* that. **Not a reference.** | 15 |
| `annotation` | after the source note — Case Notes, Cross References | A court or the revisor pointing at the section. Useful, not statutory. | 60 |

Collapsing these produces confident nonsense. Chapter 50 alone would show 15 phantom
cross-references to a chapter that no longer exists, because every one of its sections records
being renumbered from chapter 143A.

**Queries traverse `operative` only unless you pass `--annotations`.**

**The revisor's notes can also be stale.** [[hrs-11-111|§11-111]] carries a Cross References note
reading "Ballot boxes, see §11-134." §11-134 has been repealed, is covered by the range repeal at
[[hrs-11-133|§11-133]], and returns HTTP 404 from capitol.hawaii.gov. The note was never updated.
An annotation-zone citation is a lead, not an authority, and this is why.

## Asking the graph a question

```
python tools/hrs_refs.py 11-302                  what §11-302 references
python tools/hrs_refs.py 11-302 --depth 3        ...and what those reference, 3 hops
python tools/hrs_refs.py 11-302 --in             what references §11-302
python tools/hrs_refs.py 11-302 --both --depth 2 both directions
python tools/hrs_refs.py 11-25  --annotations    include Case Notes citations
python tools/hrs_refs.py --hubs                  most-referenced sections
python tools/hrs_refs.py --orphans               sections nothing points at
python tools/hrs_refs.py --queue                 targets outside the corpus
```

Cycles are detected and marked `↩ cycle` rather than followed.

For anything the CLI does not cover, `graph/hrs.db` is plain SQLite:

```sql
-- every section that cites the campaign finance definitions
SELECT src, raw FROM edge
WHERE target='11-302' AND zone='operative';

-- the campaign finance subparts, by size
SELECT subpart, COUNT(*) FROM section
WHERE part LIKE 'PART XIII%' GROUP BY subpart;
```

## In Obsidian

Every in-corpus citation is a real wikilink, so the backlinks pane and graph view work natively.
Out-of-corpus HRS sections are linked **deliberately as unresolved links** — Obsidian's unresolved
links view is therefore a live view of the ingest queue, and [[citation-queue]] is the written-out
version of the same thing.

## What the numbers are, and are not

- **393 sections, 484 citations.** Validated: a strict regex sweep over both zones of all 393
  sections found **zero** citations the parser missed.
- Extraction is mechanical. Every edge carries the citation exactly `as written`, so any edge can
  be checked against the quoted text on the page in one step.
- **The graph knows that §A cites §B. It does not know why, or whether the reference is
  load-bearing.** "§11-102 references §11-92.1" is a fact. What that dependency *means* is
  interpretation, and lives in the curated block of a page with `depth: annotated`.
- Subsection precision is not modelled. A citation to `§11-334(a)` is an edge to `§11-334`; the
  full string is preserved in the `raw` column.
- Ranges are stored as their endpoints. `sections 11-62 to 11-64` yields edges to §11-62 and
  §11-64, not §11-63.

## Shape of the corpus

- **117 of 359 live sections are isolated** — nothing cites them and they cite nothing. Roughly a
  third. Election statutes are largely self-contained procedural instructions, not a dense web.
- The most-cited section is [[hrs-11-15|§11-15]] (Application to register), 9 inbound operative
  citations.
- **[[hrs-11-1|§11-1]] defines terms for the entire title**, so in a real sense every chapter from
  11 to 19 depends on it whether or not it says so.

## Rebuilding

```
python tools/harvest_hrs.py     # fetch  (--refresh to re-pull after a session)
python tools/build_graph.py     # parse  -> graph/
python tools/build_pages.py     # write  -> statutes/
python tools/build_queue.py     # write  -> citation-queue.md
```

Safe to re-run. Everything between `<!-- BEGIN CURATED -->` and `<!-- END CURATED -->` on any page
survives regeneration; everything outside is rebuilt from the graph. A hand-written page that has
no markers is never overwritten — the generator reports it instead.
