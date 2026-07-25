"""Extract every defined term with the scope the statute declares for it.

The same word is defined differently all over HRS, and the statute is explicit
about reach every time: "used in this title" / "this chapter" / "this part" /
"for the purposes of this section".  That declaration is the whole ballgame -
a definition without its scope is worse than no definition, because it looks
authoritative while being wrong two chapters over.

Writes graph/definitions.json and a `definition` table in graph/hrs.db.
"""
import datetime as dt
import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hrs_lib import GRAPH, RAW, split_section
from build_graph import read_raw

# Ordered narrowest -> broadest.  Narrower always wins.
SCOPE_RANK = {"section": 0, "subpart": 1, "part": 2, "chapter": 3, "title": 4, "unstated": 5}

SCOPE_PATTERNS = [
    (r"for\s+(?:the\s+)?purposes?\s+of\s+this\s+section", "section"),
    (r"for\s+this\s+purpose", "section"),
    (r"as\s+used\s+in\s+this\s+section", "section"),
    (r"(?:when|whenever|as)?\s*used\s+in\s+this\s+subpart", "subpart"),
    (r"in\s+this\s+subpart", "subpart"),
    (r"(?:when|whenever|as)?\s*used\s+in\s+this\s+part", "part"),
    (r"for\s+(?:the\s+)?purposes?\s+of\s+this\s+part", "part"),
    (r"in\s+this\s+part\b", "part"),
    (r"(?:when|whenever|as)?\s*used\s+in\s+this\s+chapter", "chapter"),
    (r"for\s+(?:the\s+)?purposes?\s+of\s+this\s+chapter", "chapter"),
    (r"in\s+this\s+chapter\b", "chapter"),
    (r"(?:when|whenever|as)?\s*used\s+in\s+this\s+title", "title"),
    (r"for\s+(?:the\s+)?purposes?\s+of\s+this\s+title", "title"),
    (r"in\s+this\s+title\b", "title"),
]
SCOPE_RX = [(re.compile(p, re.I), k) for p, k in SCOPE_PATTERNS]

# Modern drafting: "Term" means / includes / has the same meaning as ...
DEF_RX = re.compile(
    r'"([^"\n]{2,80})"\s+(means|includes|has\s+the\s+same\s+meaning|shall\s+mean|'
    r'shall\s+have\s+the\s+same\s+meaning|denotes|refers\s+to)\b', re.I)

# Older drafting, still in force in §11-1 (the title-wide definitions section):
#   "Ballot", the paper ballot ...      "Office", an elective public office.
# There is no verb at all, just a comma.  Only trusted inside a section whose
# catchline is "Definitions", because "the word "vote", as used here" would
# otherwise read as a definition.
DEF_COMMA_RX = re.compile(r'"([^"\n]{2,80})",\s+(?=[a-z"])')

# "... as defined in section 11-1" / "has the same meaning as in section 707-700"
IMPORT_RX = re.compile(
    r'(?:as\s+)?defined\s+in\s+(?:section\s+)?([\dA-Z]+-[\d.]+)|'
    r'same\s+meaning\s+as\s+(?:that\s+)?(?:defined\s+)?in\s+(?:section\s+)?([\dA-Z]+-[\d.]+)', re.I)


def scope_declarations(text):
    """Every scope declaration in the section, with its position.

    A definitions block declares its reach ONCE in the lead-in and then lists
    terms, so a fixed look-back window only scopes the first term correctly.
    But a section can also shift scope mid-way (§19-3(b), §11-341(d) both open
    a "for the purposes of this section" block), so the declarations must be
    tracked in order and each term bound to the last one before it.
    """
    decls = []
    for rx, kind in SCOPE_RX:
        for m in rx.finditer(text):
            decls.append((m.end(), kind))
    decls.sort()
    # Collapse overlapping matches at the same spot, keeping the narrowest.
    out = []
    for pos, kind in decls:
        if out and pos - out[-1][0] < 12:
            if SCOPE_RANK[kind] < SCOPE_RANK[out[-1][1]]:
                out[-1] = (pos, kind)
            continue
        out.append((pos, kind))
    return out


def scope_for(decls, pos):
    kind = "unstated"
    for dpos, dkind in decls:
        if dpos <= pos:
            kind = dkind
        else:
            break
    return kind


def main():
    man = json.load(open(os.path.join(RAW, "_manifest.json"), encoding="utf-8"))
    S = json.load(open(os.path.join(GRAPH, "sections.json"), encoding="utf-8"))["sections"]
    try:
        from build_queue import chapter_titles
        titles = chapter_titles()
    except Exception:                                    # noqa: BLE001
        titles = {}

    rows = []
    for rec in man["sections"]:
        sid = rec["section"]
        meta = S.get(sid, {})
        _, body = read_raw(os.path.join(RAW, rec["file"]))
        p = split_section(body)
        text = " ".join(p["body_only"].split())
        if '"' not in text:
            continue

        decls = scope_declarations(text)
        is_defs = bool(re.match(r"(?i)definitions", meta.get("catchline", "")))
        hits = list(DEF_RX.finditer(text))
        if is_defs:
            # Merge in comma-form entries, then re-sort so the slicing that
            # bounds each definition still works.
            spans = {m.start() for m in hits}
            hits += [m for m in DEF_COMMA_RX.finditer(text) if m.start() not in spans]
            hits.sort(key=lambda m: m.start())
        seen_terms = set()
        for i, m in enumerate(hits):
            term = " ".join(m.group(1).split())
            # Skip quoted prose that is not a definition list entry.
            if term.lower() in ("s", "") or len(term) < 2:
                continue
            # A term quoted repeatedly in the same section is one definition,
            # not several.
            if term.lower() in seen_terms:
                continue
            seen_terms.add(term.lower())
            end = hits[i + 1].start() if i + 1 < len(hits) else min(len(text), m.end() + 700)
            dtext = text[m.start():end].strip().rstrip(";").strip()
            kind = scope_for(decls, m.start())
            if kind == "unstated":
                # A section titled "Definitions" with no declaration defaults to
                # its own chapter, which is the HRS drafting convention.
                kind = "chapter" if re.match(r"(?i)definitions", meta.get("catchline", "")) \
                    else "section"

            chap = meta.get("chapter", sid.split("-")[0])
            part = meta.get("part", "")
            sub = meta.get("subpart", "")
            grp = titles.get(chap, ("", ""))[1]
            key = {
                "section": f"sec:{sid}",
                "subpart": f"ch:{chap}:{part}:{sub}",
                "part": f"ch:{chap}:{part}",
                "chapter": f"ch:{chap}",
                "title": grp or f"ch:{chap}",
            }[kind]

            im = IMPORT_RX.search(dtext[:300])
            rows.append({
                "term": term, "term_norm": term.lower().strip(" .,"),
                "section": sid, "chapter": chap, "part": part, "subpart": sub,
                "scope_type": kind, "scope_key": key, "scope_rank": SCOPE_RANK[kind],
                "verb": (" ".join(m.group(2).split()).lower()
                         if m.re.groups > 1 else "(comma form)"),
                "text": dtext[:1200],
                "imports_from": (im.group(1) or im.group(2)) if im else None,
                "title_group": grp,
            })

    stamp = dt.date.today().isoformat()
    json.dump({"built": stamp, "definitions": rows},
              open(os.path.join(GRAPH, "definitions.json"), "w", encoding="utf-8"), indent=1)

    con = sqlite3.connect(os.path.join(GRAPH, "hrs.db"))
    con.execute("DROP TABLE IF EXISTS definition")
    con.execute("""CREATE TABLE definition(
        term TEXT, term_norm TEXT, section TEXT, chapter TEXT, part TEXT, subpart TEXT,
        scope_type TEXT, scope_key TEXT, scope_rank INT, verb TEXT, text TEXT,
        imports_from TEXT, title_group TEXT)""")
    con.execute("CREATE INDEX def_term ON definition(term_norm)")
    con.execute("CREATE INDEX def_sec ON definition(section)")
    con.executemany("INSERT INTO definition VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    [(r["term"], r["term_norm"], r["section"], r["chapter"], r["part"],
                      r["subpart"], r["scope_type"], r["scope_key"], r["scope_rank"],
                      r["verb"], r["text"], r["imports_from"], r["title_group"])
                     for r in rows])
    con.commit()

    import collections
    print(f"defined terms extracted : {len(rows)}")
    print(f"distinct terms          : {len(set(r['term_norm'] for r in rows))}")
    print(f"definition imports      : {sum(1 for r in rows if r['imports_from'])}")
    print("\nby declared scope:")
    for k, v in collections.Counter(r["scope_type"] for r in rows).most_common():
        print(f"   {v:5d}  {k}")
    dupes = collections.Counter(r["term_norm"] for r in rows)
    multi = [(t, n) for t, n in dupes.most_common() if n > 1]
    print(f"\nterms defined more than once (the collision problem): {len(multi)}")
    for t, n in multi[:12]:
        scopes = [f"{r['section']}/{r['scope_type']}" for r in rows if r["term_norm"] == t]
        print(f"   {n}x  {t:<28} {', '.join(scopes)}")
    con.close()


if __name__ == "__main__":
    main()
