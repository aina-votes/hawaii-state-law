"""Parse raw/hrs/ into a citation graph.

Reads only files under raw/hrs/ (never edits them) and writes graph/:
    sections.json   one record per section: catchline, part, history, sizes
    edges.json      every citation, tagged operative vs annotation
    hrs.db          the same, queryable with SQL
    unresolved.json citations pointing outside the harvested corpus

A citation found in the statute text is the law pointing at law.  A citation
found after the source note is the revisor or a court pointing at it.  The two
are never merged.
"""
import datetime as dt
import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hrs_lib import (CHAPTER_TITLE, GRAPH, IN_SCOPE, RAW, extract_citations,
                     sec_sort_key, split_section)


def read_raw(path):
    txt = open(path, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n", txt, re.S)
    meta = {}
    if m:
        for line in m.group(1).split("\n"):
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip().strip('"')
        txt = txt[m.end():]
    txt = re.sub(r"^\s*<!--.*?-->\s*", "", txt, flags=re.S)
    return meta, txt.strip()


def main():
    os.makedirs(GRAPH, exist_ok=True)
    manifest = json.load(open(os.path.join(RAW, "_manifest.json"), encoding="utf-8"))
    sections, edges, problems = {}, [], []
    # HRS title grouping (e.g. "Title 2. Elections") from the State's master
    # index.  Needed because definitions scoped to "this title" reach every
    # chapter in that title - 11-1 governs chapters 11 through 19.
    try:
        from build_queue import chapter_titles
        _titles = chapter_titles()
    except Exception:                                    # noqa: BLE001
        _titles = {}

    for rec in manifest["sections"]:
        path = os.path.join(RAW, rec["file"])
        meta, body = read_raw(path)
        sid, chap = rec["section"], rec["chapter"]
        parts = split_section(body)

        # Includes range repeals: "§§11-71 to 11-75 REPEALED. L 2019, c 136".
        repealed = bool(re.match(r"(?i)^\s*(repealed|reserved)\b", parts["catchline"] or "")) \
            or bool(re.search(r"(?i)\bREPEALED\b", parts["operative"][:180]))
        if repealed:
            # "§§19-7 to 9 REPEALED" must not read as catchline "to 9 REPEALED".
            rng = re.match(r"\s*§{1,2}\s*([\dA-Z.\-]+)\s+to\s+([\dA-Z.\-]+)\s+REPEALED",
                           parts["operative"], re.I)
            if rng:
                hi = rng.group(2)
                if "-" not in hi:
                    hi = f"{chap}-{hi}"
                parts["catchline"] = f"REPEALED (§§{rng.group(1)} to {hi})"
            elif not parts["catchline"]:
                parts["catchline"] = "REPEALED"

        sections[sid] = {
            "id": sid,
            "chapter": chap,
            "chapter_title": CHAPTER_TITLE.get(chap, ""),
            "title_group": _titles.get(chap, ("", ""))[1],
            "catchline": parts["catchline"],
            "part_heading": parts["part_heading"],
            "subpart_heading": parts["subpart_heading"],
            "history": parts["history"],
            "repealed": repealed,
            "operative_chars": len(parts["operative"]),
            "annotation_chars": len(parts["annotations"]),
            "url": rec["url"],
            "raw_file": rec["file"],
            "retrieved": meta.get("retrieved", ""),
        }
        if not parts["catchline"] and not repealed:
            problems.append({"section": sid, "issue": "no catchline parsed",
                             "head": parts["operative"][:120]})

        for zone, text in (("operative", parts["body_only"]),
                           ("history", parts["history"]),
                           ("annotation", parts["annotations"])):
            for c in extract_citations(text, this_chapter=chap):
                if c["kind"] == "hrs_section" and c["target"] == sid:
                    continue                      # self-reference
                if c["kind"] == "hrs_chapter" and c["target"] == "ch:" + chap:
                    continue                      # "this chapter"
                edges.append({"src": sid, "src_chapter": chap, "zone": zone,
                              "kind": c["kind"], "target": c["target"],
                              "raw": c["raw"], "context": c["context"]})

    # Forward-fill Part membership within each chapter.
    by_chap = {}
    for sid, s in sections.items():
        by_chap.setdefault(s["chapter"], []).append(sid)
    for chap, sids in by_chap.items():
        cur, cursub = "", ""
        for sid in sorted(sids, key=sec_sort_key):
            if sections[sid]["part_heading"]:
                cur = sections[sid]["part_heading"]
                cursub = ""
            if sections[sid]["subpart_heading"]:
                cursub = sections[sid]["subpart_heading"]
            sections[sid]["part"] = cur
            sections[sid]["subpart"] = cursub

    # A range repeal ("§§15-7, 15-8 REPEALED") covers sections that have no file
    # of their own.  They are accounted for, not missing, and must not surface in
    # the ingest queue.
    covered = {}
    for sid, s in sections.items():
        if not s["repealed"]:
            continue
        m = re.match(r"REPEALED \(§§([\dA-Z.\-]+) to ([\dA-Z.\-]+)\)", s["catchline"] or "")
        span = []
        if m:
            a, b = m.group(1), m.group(2)
            ca, na = a.split("-", 1)
            try:
                span = [f"{ca}-{n}" for n in range(int(na), int(b.split('-')[-1]) + 1)]
            except ValueError:
                span = [a, b]
        else:
            lm = re.match(r"\s*§{1,2}\s*([\dA-Z.\-]+(?:\s*,\s*[\dA-Z.\-]+)+)\s+REPEALED",
                          split_section(read_raw(os.path.join(RAW, s["raw_file"]))[1])["operative"],
                          re.I)
            if lm:
                span = [x.strip() for x in lm.group(1).split(",")]
        for x in span:
            if x not in sections:
                covered[x] = sid

    # Which citation targets fall outside the harvested corpus?
    unresolved = {}
    for e in edges:
        t, k = e["target"], e["kind"]
        known = (k == "hrs_section" and (t in sections or t in covered)) or \
                (k == "hrs_chapter" and t.split(":")[1] in IN_SCOPE) or \
                (k == "hrs_part")
        if known:
            continue
        u = unresolved.setdefault(t, {"target": t, "kind": k, "count": 0,
                                      "cited_by": [], "example": e["raw"]})
        u["count"] += 1
        if e["src"] not in u["cited_by"]:
            u["cited_by"].append(e["src"])

    for u in unresolved.values():
        u["cited_by"].sort(key=lambda s: sec_sort_key(s))

    stamp = dt.date.today().isoformat()
    ordered = {k: sections[k] for k in sorted(sections, key=sec_sort_key)}
    json.dump({"built": stamp, "sections": ordered},
              open(os.path.join(GRAPH, "sections.json"), "w", encoding="utf-8"), indent=1)
    json.dump({"built": stamp, "edges": edges},
              open(os.path.join(GRAPH, "edges.json"), "w", encoding="utf-8"), indent=1)
    json.dump({"built": stamp,
               "unresolved": sorted(unresolved.values(), key=lambda u: -u["count"])},
              open(os.path.join(GRAPH, "unresolved.json"), "w", encoding="utf-8"), indent=1)
    json.dump({"built": stamp, "covered_by_range_repeal": covered},
              open(os.path.join(GRAPH, "repealed_ranges.json"), "w", encoding="utf-8"), indent=1)
    json.dump({"built": stamp, "problems": problems},
              open(os.path.join(GRAPH, "parse_problems.json"), "w", encoding="utf-8"), indent=1)

    db = os.path.join(GRAPH, "hrs.db")
    if os.path.exists(db):
        os.remove(db)
    con = sqlite3.connect(db)
    con.executescript("""
    CREATE TABLE section(id TEXT PRIMARY KEY, chapter TEXT, chapter_title TEXT,
        catchline TEXT, part TEXT, subpart TEXT, title_group TEXT, history TEXT,
        repealed INT, operative_chars INT, annotation_chars INT, url TEXT, retrieved TEXT);
    CREATE TABLE edge(src TEXT, src_chapter TEXT, zone TEXT, kind TEXT,
        target TEXT, raw TEXT, context TEXT);
    CREATE INDEX edge_src ON edge(src);
    CREATE INDEX edge_tgt ON edge(target);
    CREATE INDEX edge_zone ON edge(zone);
    """)
    con.executemany("INSERT INTO section VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    [(s["id"], s["chapter"], s["chapter_title"], s["catchline"],
                      s.get("part", ""), s.get("subpart", ""), s.get("title_group", ""),
                      s["history"], int(s["repealed"]),
                      s["operative_chars"], s["annotation_chars"], s["url"],
                      s["retrieved"]) for s in ordered.values()])
    con.executemany("INSERT INTO edge VALUES (?,?,?,?,?,?,?)",
                    [(e["src"], e["src_chapter"], e["zone"], e["kind"],
                      e["target"], e["raw"], e["context"]) for e in edges])
    con.commit()

    op = [e for e in edges if e["zone"] == "operative"]
    hz = [e for e in edges if e["zone"] == "history"]
    print(f"sections            {len(sections)}")
    print(f"  repealed/reserved {sum(1 for s in sections.values() if s['repealed'])}")
    print(f"  no catchline      {len(problems)}")
    print(f"edges total         {len(edges)}")
    print(f"  operative         {len(op)}")
    print(f"  history/renumber  {len(hz)}")
    print(f"  annotation        {len(edges)-len(op)-len(hz)}")
    print(f"range-repeal covered {len(covered)}")
    print(f"unresolved targets  {len(unresolved)}")
    con.close()


if __name__ == "__main__":
    main()
