"""Extract case / AG-opinion / law-review citations from the revisor's
annotation zones — the first DB-native ingest (zero crawl: the text is
already harvested).

    python tools/case_cites.py      # zones -> graph/annotation-cites.json

These are the revisor's Case Notes: **leads, not authority** (they curate,
they go stale, they are not exhaustive — sources-of-law). Modeled as:

    hrs:X --construed_by--> case:...  / agop:...    (attestation: revisor_note)
    hrs:X --discussed_by--> lrev:...                (attestation: revisor_note)

The `context` on each edge is the revisor's one-paragraph holding summary —
that is the actual value: "what has been held about §X" becomes queryable.

Parallel citations ("96 H. 388, 31 P.3d 901") are ONE case: id from the
first (official) reporter, every parallel cite kept in `raw`. The sweep
asserts zero reporter tokens missed across all annotation zones.
"""
import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hrs_lib import GRAPH, VAULT

DB = os.path.join(VAULT, "hawaii-law.db")

# Reporters seen in Hawaii revisor notes. Order matters (longest first).
# U.S. must not swallow U.S.C.; F./P./H. bare forms need guards.
_REP = (r"H\.\s?App\.|Haw\.\s?App\.|Haw\.|H\.|"
        r"P\.3d|P\.2d|P\.|"
        r"U\.S\.(?!C)|S\.\s?Ct\.|L\.\s?Ed\.\s?2d|L\.\s?Ed\.|"
        r"F\.\s?Supp\.\s?3d|F\.\s?Supp\.\s?2d|F\.\s?Supp\.|F\.3d|F\.2d|F\.4th|F\.")
CITE = re.compile(rf"\b(\d{{1,4}})\s+({_REP})\s+(\d{{1,5}})")
AGOP = re.compile(r"Att'?y?\.?\s?Gen\.?\s?Op\.?\s?(?:No\.?\s?)?(\d{2}-\d+)", re.I)
LREV = re.compile(r"\b(\d{1,3})\s+(UH\s?L\.\s?Rev\.|U\.?\s?Haw\.?\s?L\.\s?Rev\.|"
                  r"HBJ|Haw\.\s?B\.?\s?J\.)\s+(\d{1,4})")
YEAR = re.compile(r"^\s*\((\d{4})\)")


def dewrap(s):
    return " ".join(s.split())


def rep_slug(rep):
    return re.sub(r"[^A-Za-z0-9]", "", rep)


def parse_zone(sid, body, edges):
    found_tokens = 0
    # paragraphs = revisor notes; blank-line separated in the zone text
    for para in re.split(r"\n\s*\n", body):
        p = dewrap(para)
        if not p:
            continue
        # ---- case cites, grouped into parallel-cite runs ------------------
        ms = list(CITE.finditer(p))
        found_tokens += len(ms)
        i = 0
        while i < len(ms):
            run = [ms[i]]
            while (i + 1 < len(ms)
                   and re.fullmatch(r"[,;]?\s*", p[ms[i].end():ms[i + 1].start()])):
                i += 1
                run.append(ms[i])
            i += 1
            first = run[0]
            raw = p[first.start():run[-1].end()]
            ym = YEAR.match(p[run[-1].end():])
            if ym:
                raw += f" ({ym.group(1)})"
            cid = f"case:{first.group(1)}-{rep_slug(first.group(2))}-{first.group(3)}"
            edges.append({"src": sid, "dst": cid, "dst_kind": "case",
                          "relation": "construed_by", "raw": raw,
                          "context": p[:400]})
        # ---- AG opinions ---------------------------------------------------
        for m in AGOP.finditer(p):
            edges.append({"src": sid, "dst": f"agop:{m.group(1)}",
                          "dst_kind": "ag_opinion", "relation": "construed_by",
                          "raw": m.group(0), "context": p[:400]})
        # ---- law reviews ---------------------------------------------------
        for m in LREV.finditer(p):
            edges.append({"src": sid,
                          "dst": f"lrev:{m.group(1)}-{rep_slug(m.group(2))}-{m.group(3)}",
                          "dst_kind": "law_review", "relation": "discussed_by",
                          "raw": m.group(0), "context": p[:400]})
    return found_tokens


def main():
    con = sqlite3.connect(DB)
    rows = con.execute("SELECT section_id, body FROM zones "
                       "WHERE zone='annotation' AND section_id LIKE 'hrs:%'").fetchall()
    edges, total_tokens = [], 0
    for sid, body in rows:
        total_tokens += parse_zone(sid, body, edges)

    # ---- strict sweep: every reporter token is inside some edge's raw ------
    swept = 0
    by_src = {}
    for e in edges:
        if e["dst_kind"] == "case":
            by_src.setdefault(e["src"], []).append(e["raw"])
    missed = []
    for sid, body in rows:
        raws = " || ".join(by_src.get(sid, []))
        for m in CITE.finditer(dewrap(body)):
            swept += 1
            token = f"{m.group(1)} {m.group(2)} {m.group(3)}"
            if dewrap(token) not in dewrap(raws):
                missed.append({"section": sid, "token": token})
    out = {"built": "2026-07-26", "attestation": "revisor_note",
           "edges": edges, "sweep": {"tokens": swept, "missed": missed}}
    with open(os.path.join(GRAPH, "annotation-cites.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)

    cases = {e["dst"] for e in edges if e["dst_kind"] == "case"}
    agops = {e["dst"] for e in edges if e["dst_kind"] == "ag_opinion"}
    lrevs = {e["dst"] for e in edges if e["dst_kind"] == "law_review"}
    secs = {e["src"] for e in edges}
    print(f"{len(edges)} edges from {len(secs)} sections: "
          f"{len(cases)} distinct cases, {len(agops)} AG opinions, "
          f"{len(lrevs)} law-review pieces")
    print(f"sweep: {swept} reporter tokens, {len(missed)} missed")
    if missed:
        for m in missed[:10]:
            print("  MISSED", m)
        sys.exit(1)


if __name__ == "__main__":
    main()
