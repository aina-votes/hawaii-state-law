"""Query the HRS citation graph.

    python tools/hrs_refs.py 11-302                 what it references (1 hop)
    python tools/hrs_refs.py 11-302 --depth 3       ...and what those reference
    python tools/hrs_refs.py 11-302 --in            what references IT
    python tools/hrs_refs.py 11-302 --both --depth 2
    python tools/hrs_refs.py 11-302 --annotations   include revisor/case-note cites
    python tools/hrs_refs.py --orphans              sections nothing points at
    python tools/hrs_refs.py --hubs                 most-referenced sections
    python tools/hrs_refs.py --queue                targets outside the corpus

By default only OPERATIVE citations are traversed: references that appear in
the statute text itself.  Case Notes and Cross References are the revisor's
apparatus, not the law's own pointers, and are included only with
--annotations.
"""
import argparse
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hrs_lib import GRAPH, sec_sort_key

DB = os.path.join(GRAPH, "hrs.db")


def con():
    if not os.path.exists(DB):
        sys.exit("graph/hrs.db missing - run: python tools/build_graph.py")
    return sqlite3.connect(DB)


def meta(c, sid):
    r = c.execute("select catchline,part,subpart,repealed,chapter_title from section "
                  "where id=?", (sid,)).fetchone()
    if not r:
        return None
    return {"catchline": r[0], "part": r[1], "subpart": r[2],
            "repealed": bool(r[3]), "chapter_title": r[4]}


def label(c, sid):
    m = meta(c, sid)
    if not m:
        return f"§{sid}  [not in corpus - not yet ingested]"
    tail = "  [REPEALED]" if m["repealed"] else ""
    return f"§{sid}  {m['catchline']}{tail}"


def pretty_target(kind, target):
    if kind == "hrs_section":
        return target
    if kind == "hrs_chapter":
        return f"HRS ch. {target.split(':')[1]}"
    if kind == "hrs_part":
        p = target.split(":")
        return f"part {p[2]} of ch. {p[1]}"
    if kind in ("usc", "cfr"):
        p = target.split(":")
        unit = "U.S.C." if kind == "usc" else "C.F.R."
        return f"{p[1]} {unit}" + (f" §{p[2]}" if len(p) > 2 and p[2] else "")
    if kind == "har":
        p = target.split(":")
        return "HAR title " + p[1] + (f", ch. {p[2]}" if len(p) > 2 else "")
    if kind == "hi_const":
        p = target.split(":")
        return f"Haw. Const. art. {p[1]}, §{p[2]}"
    if kind == "us_const":
        return "U.S. Constitution"
    return target


def walk_out(c, root, depth, zones, seen=None, level=0, lines=None, path=None):
    lines = [] if lines is None else lines
    seen = set() if seen is None else seen
    path = [] if path is None else path
    if level >= depth:
        return lines
    q = ("select distinct kind,target,raw from edge where src=? and zone in (%s) "
         "order by kind,target" % ",".join("?" * len(zones)))
    rows = c.execute(q, (root, *zones)).fetchall()
    hrs = [r for r in rows if r[0] == "hrs_section"]
    other = [r for r in rows if r[0] != "hrs_section"]
    ind = "   " * level
    for kind, target, raw in sorted(hrs, key=lambda r: sec_sort_key(r[1])) + other:
        key = (root, target)
        if key in seen:
            continue
        seen.add(key)
        if kind == "hrs_section":
            cyc = "  ↩ cycle" if target in path else ""
            lines.append(f"{ind}├─ {label(c, target)}   (as: {raw}){cyc}")
            if not cyc:
                walk_out(c, target, depth, zones, seen, level + 1, lines, path + [root])
        else:
            inside = kind == "hrs_part" or (
                kind == "hrs_chapter"
                and target.split(":")[1] in {r[0] for r in
                                             c.execute("select distinct chapter from section")})
            note = "" if inside else "   [outside the harvested corpus]"
            lines.append(f"{ind}├─ {pretty_target(kind, target)}   (as: {raw}){note}")
    return lines


def walk_in(c, root, depth, zones, seen=None, level=0, lines=None):
    lines = [] if lines is None else lines
    seen = set() if seen is None else seen
    if level >= depth:
        return lines
    q = ("select distinct src,raw from edge where target=? and kind='hrs_section' "
         "and zone in (%s)" % ",".join("?" * len(zones)))
    rows = c.execute(q, (root, *zones)).fetchall()
    ind = "   " * level
    for src, raw in sorted(rows, key=lambda r: sec_sort_key(r[0])):
        if (src, root) in seen:
            continue
        seen.add((src, root))
        lines.append(f"{ind}├─ {label(c, src)}   (as: {raw})")
        walk_in(c, src, depth, zones, seen, level + 1, lines)
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("section", nargs="?")
    ap.add_argument("--depth", type=int, default=1)
    ap.add_argument("--in", dest="inbound", action="store_true")
    ap.add_argument("--both", action="store_true")
    ap.add_argument("--annotations", action="store_true",
                    help="also traverse revisor Case Notes / Cross References")
    ap.add_argument("--orphans", action="store_true")
    ap.add_argument("--hubs", action="store_true")
    ap.add_argument("--queue", action="store_true")
    a = ap.parse_args()
    c = con()
    zones = ("operative", "annotation") if a.annotations else ("operative",)

    if a.hubs:
        print("Most-referenced sections (operative citations only)\n")
        for tgt, n in c.execute(
                "select target,count(distinct src) n from edge where kind='hrs_section' "
                "and zone='operative' group by target order by n desc limit 25"):
            print(f"  {n:3d}  {label(c, tgt)}")
        return

    if a.orphans:
        print("Sections no other section cites, and that cite nothing (operative)\n")
        rows = c.execute("""
            select id from section s where repealed=0
              and not exists(select 1 from edge where target=s.id and zone='operative')
              and not exists(select 1 from edge where src=s.id and zone='operative')
            """).fetchall()
        for (sid,) in sorted(rows, key=lambda r: sec_sort_key(r[0])):
            print(f"  {label(c, sid)}")
        print(f"\n  {len(rows)} of "
              f"{c.execute('select count(*) from section where repealed=0').fetchone()[0]} "
              f"live sections")
        return

    if a.queue:
        print("Cited but NOT in the harvested corpus - the ingest queue\n")
        rows = c.execute("""
            select kind,target,count(*) n, group_concat(distinct src)
            from edge where zone='operative' group by kind,target order by n desc""").fetchall()
        known = {r[0] for r in c.execute("select id from section")}
        chs = {r[0] for r in c.execute("select distinct chapter from section")}
        for kind, target, n, srcs in rows:
            if kind == "hrs_section" and target in known:
                continue
            if kind == "hrs_chapter" and target.split(":")[1] in chs:
                continue
            if kind == "hrs_part":
                continue
            cited = ", ".join(f"§{x}" for x in sorted(set(srcs.split(",")), key=sec_sort_key)[:6])
            print(f"  {n:3d}x  {pretty_target(kind, target):28s} cited by {cited}")
        return

    if not a.section:
        ap.error("give a section id (e.g. 11-302) or one of --orphans/--hubs/--queue")

    sid = a.section.lstrip("§").upper()
    m = meta(c, sid)
    if not m:
        sys.exit(f"§{sid} is not in the corpus. Try: python tools/hrs_refs.py --queue")

    where = " › ".join(x for x in [m["chapter_title"], m["part"], m["subpart"]] if x)
    print(f"\n§{sid}  {m['catchline']}")
    print(f"   {where}")
    print(f"   zones: {', '.join(zones)}   depth: {a.depth}\n")

    if not a.inbound or a.both:
        print(f"REFERENCES OUT (what §{sid} points at)")
        out = walk_out(c, sid, a.depth, zones)
        print("\n".join(out) if out else "   (none)")
        print()
    if a.inbound or a.both:
        print(f"REFERENCED BY (what points at §{sid})")
        inn = walk_in(c, sid, a.depth, zones)
        print("\n".join(inn) if inn else "   (none)")
        print()


if __name__ == "__main__":
    main()
