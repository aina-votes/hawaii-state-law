# Hawaiʻi State Law

A machine-queryable corpus of Hawaiʻi law: verbatim statute text, a citation graph
across it, and a scope-resolved definitions layer. Built and maintained by Claude
Code; curated by Sam Peck.

**This repo is the source of truth for the corpus.** It lives nested in place inside the
`Firefly's Path` workspace at `Brain/LLM Wikis/Knowledge Base/Hawaii State Law` (moved into
the OS 2026-07-25; the old `C:\Law` junction is retired), ignored by the parent repo's git.
Commits land here.

## Start here

| File | What it is |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | The schema. Read this before doing any work in the repo. |
| [`overview.md`](overview.md) | Map of the domain in prose. |
| [`INDEX.md`](INDEX.md) | Catalog of every page, with coverage and depth. |
| [`hrs-citation-graph.md`](hrs-citation-graph.md) | How to query the graph, and what it does not claim. |
| [`log.md`](log.md) | Append-only record of every ingest, query, and lint. |

## Coverage today

HRS Title 2 (Elections), chapters 10 through 19: **393 sections, 484 citation
edges, 151 defined terms.** That is roughly 1.7% of the Hawaiʻi Revised Statutes
by section count, and HRS is only one of several bodies that make up state law
(see `open-questions.md`).

## Query it

```bash
python tools/hrs_refs.py 11-302 --both --depth 2   # what cites what
python tools/hrs_define.py contribution --at 11-357 # what a term means HERE
python tools/hrs_define.py --collisions             # terms with competing definitions
```

The pipeline that produces all of it:

```bash
python tools/harvest_hrs.py     # fetch  -> raw/hrs/
python tools/build_graph.py     # parse  -> graph/
python tools/build_definitions.py
python tools/build_pages.py     # write  -> statutes/ (curated blocks preserved)
python tools/build_queue.py
```

## Two rules that matter most

- **`raw/` is immutable.** It is what the State actually served, byte for byte.
  Corrections go on the source page, never into a raw file.
- **`status` and `depth` are honesty flags, not decoration.** `depth: harvested`
  means the text is verbatim and nobody has read it operationally yet. It is not
  an answer to a legal question.

This is not legal advice and is not a substitute for the statute.
