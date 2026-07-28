"""Bridge the legislature's record onto the statute corpus: act -> HRS edges.

THE GAP THIS CLOSES. Until now the corpus held what the law says today and
nothing about how it got that way. `sources-of-law.md` layer 4 (Session Laws)
was mapped-not-read, and that is the layer that makes a statute corpus go
stale SILENTLY rather than loudly: the codified HRS lags the session, and
uncodified provisions -- effective dates, sunsets, applicability -- never
enter HRS at all.

The sibling database `hi-leg-db` already holds every measure since 2008.
This tool reads it (read-only, never written to) and emits the edges that
join the two.

TWO ATTESTATIONS, DELIBERATELY NOT MERGED. The same claim -- "Act 213 (2021)
touched §11-102" -- is available from two independent sources of differing
quality, and the corpus's standing rule is to record both rather than pick
a winner:

  act_text  -- parsed from the act's own operative sentence ("Section 11-102,
               Hawaii Revised Statutes, is amended by amending subsection
               (b)"). Precise, carries the operation and the subsection, and
               is backed by the change atoms in hi-leg-db's act_changes.
  bill_refs -- hi-leg-db's citation extraction over the whole bill text.
               Broader (it catches acts this pipeline has not parsed yet)
               and looser (a bill that merely mentions §91-3 produces a
               reference, not an amendment).

Edges are written src=statute, dst=act, matching the corpus grain where src
is always something the corpus holds: "which acts touched §11-102" is then
one indexed lookup. dst uses the id namespace the schema already documents
for session laws: `slh:<year>:<act>`.

Unresolved targets are recorded, never dropped: a citation that does not
join is a lead (a repealed section, pre-2010 numbering, a section the act
proposed and the revisor renumbered), and the join rate is printed so a
regression is visible.

Usage:
  python tools/act_bridge.py                     # writes graph/act-edges.json
  python tools/act_bridge.py --hileg <path>
  python tools/act_bridge.py --report            # join stats, no write
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GRAPH = os.path.join(ROOT, "graph")
DB = os.path.join(ROOT, "hawaii-law.db")
HILEG_DEFAULT = os.path.normpath(os.path.join(ROOT, "..", "hi-leg-db", "hileg.db"))

# "11-1, 11-2, and 11-3" / "412:2-105" / "11-102.5"
SEC_TOKEN = re.compile(r"\d+[A-Z]?(?::\d+[A-Z]?)?-[\w.]+")


def slh_id(year: int, act: int, special: int) -> str:
    """`slh:2021:213`, with special sessions kept distinct -- both series
    restart numbering at 1, so the year+number alone is ambiguous."""
    return f"slh:{year}:{act}" + (":ss" if special else "")


def hrs_ids(con: sqlite3.Connection) -> set[str]:
    return {r[0] for r in con.execute(
        "SELECT num FROM sections WHERE layer='hrs'")}


def build(law: sqlite3.Connection, hileg: sqlite3.Connection):
    known = hrs_ids(law)
    edges: list[dict] = []
    unresolved: dict[str, int] = {}
    stats = {"act_text": [0, 0], "bill_refs": [0, 0]}   # [joined, total]

    def emit(sec: str, year, act, special, relation, attest, raw, context):
        key = sec.strip()
        bucket = stats[attest]
        bucket[1] += 1
        if key not in known:
            unresolved[key] = unresolved.get(key, 0) + 1
            return
        bucket[0] += 1
        edges.append({
            "src": f"hrs:{key}",
            "dst": slh_id(year, act, special),
            "dst_kind": "session_law",
            "relation": relation,
            "attestation": attest,
            "raw": raw,
            "context": context,
        })

    # ---- attestation 1: the act's own operative sentences -----------------
    has_amend = hileg.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' "
        "AND name='act_amendments'").fetchone()[0]
    if has_amend:
        q = """SELECT year, act_number, special_session, bill_section,
                      operation, target_kind, target, subsection, header,
                      n_deleted, n_inserted
                 FROM act_amendments
                WHERE target_kind IN ('hrs_section','hrs_chapter')
                  AND target IS NOT NULL"""
        for (year, act, sp, bsec, op, kind, target, subsection, header,
             ndel, nins) in hileg.execute(q):
            relation = {"amend": "amended_by", "repeal": "repealed_by",
                        "add_new": "added_by"}.get(op, "affected_by")
            ctx = (f"Act {act} ({year}) §{bsec}: {op}"
                   + (f" {subsection}" if subsection else "")
                   + f" [-{ndel}/+{nins}]")
            if kind == "hrs_chapter":
                # A chapter-level target ("chapter 11 is amended by adding a
                # new section") names no section; the section it creates is
                # "appropriately designated" by the revisor and is not
                # knowable from the act. Recorded as a chapter edge only.
                edges.append({
                    "src": f"hrs:ch:{target}",
                    "dst": slh_id(year, act, sp),
                    "dst_kind": "session_law",
                    "relation": relation,
                    "attestation": "act_text",
                    "raw": target,
                    "context": ctx,
                })
                continue
            for tok in SEC_TOKEN.findall(target):
                emit(tok, year, act, sp, relation, "act_text", target, ctx)

    # ---- attestation 2: hi-leg-db's citation extraction -------------------
    q2 = """SELECT a.year, a.act_number, a.special_session,
                   r.hrs_ref, r.edge_kind, r.n_occurrences
              FROM acts a
              JOIN bill_hrs_refs r
                ON r.measure_id = a.measure_id
               AND r.draft = COALESCE(a.enacted_draft,'')
             WHERE r.ref_kind = 'section'
               AND r.edge_kind IN ('amends','repeals','adds_new')"""
    for year, act, sp, ref, kind, nocc in hileg.execute(q2):
        relation = {"amends": "amended_by", "repeals": "repealed_by",
                    "adds_new": "added_by"}[kind]
        emit(ref, year, act, sp, relation, "bill_refs", ref,
             f"Act {act} ({year}): {kind} (x{nocc})")

    # ---- cross-check the two attestations ---------------------------------
    # Same discipline as the LRB-table-vs-rule-text check in the HAR layer:
    # where both sources speak, record where they disagree instead of
    # picking a winner.
    #
    # FOUND ON THE FIRST RUN: bill_refs UNDER-REPORTS on enacted drafts.
    # Act 166 (2022) plainly amends §11-102 -- hi-leg-db itself labels the
    # introduced and HD1 drafts 'amends' -- but labels the enacted SD1 draft
    # 'references', so an operative-kinds filter drops the act entirely.
    # act_text (parsed from "Section 11-102, Hawaii Revised Statutes, is
    # amended") gets it right. Where the two differ, act_text is the better
    # witness: it reads the act's own operative sentence.
    by_act_text: dict[tuple[str, str], str] = {}
    by_bill_refs: dict[tuple[str, str], str] = {}
    for e in edges:
        key = (e["src"], e["dst"])
        (by_act_text if e["attestation"] == "act_text"
         else by_bill_refs)[key] = e["relation"]

    disagreements = {
        "act_text_only": sorted(
            f"{s} {d}" for (s, d) in by_act_text if (s, d) not in by_bill_refs),
        "bill_refs_only": sorted(
            f"{s} {d}" for (s, d) in by_bill_refs if (s, d) not in by_act_text),
        "relation_conflict": sorted(
            f"{s} {d}: act_text={by_act_text[(s, d)]} "
            f"bill_refs={by_bill_refs[(s, d)]}"
            for (s, d) in by_act_text
            if (s, d) in by_bill_refs
            and by_act_text[(s, d)] != by_bill_refs[(s, d)]),
    }
    return edges, unresolved, stats, disagreements


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hileg", default=HILEG_DEFAULT)
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.hileg):
        print(f"hi-leg-db not found at {args.hileg} -- the bridge needs the "
              f"sibling database; it is not vendored in this repo.")
        return 2

    law = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    hileg = sqlite3.connect(f"file:{args.hileg}?mode=ro", uri=True)
    edges, unresolved, stats, disagreements = build(law, hileg)

    # de-duplicate: the same (src,dst,relation,attestation) can be asserted
    # by several bill sections of one act.
    seen, deduped = set(), []
    for e in edges:
        k = (e["src"], e["dst"], e["relation"], e["attestation"])
        if k in seen:
            continue
        seen.add(k)
        deduped.append(e)

    for name, (joined, total) in stats.items():
        pct = 100 * joined / total if total else 0
        print(f"  {name:10s} {joined}/{total} section refs joined ({pct:.1f}%)")
    print(f"  edges {len(deduped)} after dedup (from {len(edges)})")
    print(f"  distinct acts: "
          f"{len({e['dst'] for e in deduped})}")
    print(f"  distinct statutes touched: "
          f"{len({e['src'] for e in deduped})}")
    top = sorted(unresolved.items(), key=lambda x: -x[1])[:12]
    print(f"  unresolved targets: {len(unresolved)} distinct; top: {top}")
    print(f"  cross-check: act_text-only {len(disagreements['act_text_only'])}, "
          f"bill_refs-only {len(disagreements['bill_refs_only'])}, "
          f"relation conflicts {len(disagreements['relation_conflict'])}")

    if args.report:
        return 0

    os.makedirs(GRAPH, exist_ok=True)
    out = os.path.join(GRAPH, "act-edges.json")
    json.dump({"built": date.today().isoformat(),
               "source": "hi-leg-db acts + act_amendments + bill_hrs_refs",
               "stats": {k: {"joined": v[0], "total": v[1]}
                         for k, v in stats.items()},
               "unresolved": unresolved,
               "disagreements": disagreements,
               "edges": deduped},
              open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
