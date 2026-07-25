"""Resolve what a term means AT A GIVEN PLACE in the statutes.

    python tools/hrs_define.py contribution --at 11-357
    python tools/hrs_define.py office              # every scope that defines it
    python tools/hrs_define.py --collisions        # terms defined in >1 scope
    python tools/hrs_define.py --in 11-302         # everything that section defines

"What does X mean" is not a search, it is a scope resolution.  The same word is
defined differently across HRS and each definition declares its own reach.  This
walks outward from the asking section - section, subpart, part, chapter, title -
and the FIRST hit controls.  Everything it shadows is printed too, because the
shadowed ones are exactly what you would have wrongly quoted.
"""
import argparse
import os
import sqlite3
import sys
import textwrap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hrs_lib import GRAPH

DB = os.path.join(GRAPH, "hrs.db")


def con():
    if not os.path.exists(DB):
        sys.exit("graph/hrs.db missing - run build_graph.py then build_definitions.py")
    c = sqlite3.connect(DB)
    if not c.execute("select name from sqlite_master where name='definition'").fetchone():
        sys.exit("no definition table - run: python tools/build_definitions.py")
    return c


def scope_chain(c, sid):
    """Narrowest to broadest scope keys that govern `sid`."""
    r = c.execute("select chapter,part,subpart,title_group from section where id=?",
                  (sid,)).fetchone()
    if not r:
        return None, []
    chap, part, sub, grp = r
    chain = [f"sec:{sid}"]
    if part and sub:
        chain.append(f"ch:{chap}:{part}:{sub}")
    if part:
        chain.append(f"ch:{chap}:{part}")
    chain.append(f"ch:{chap}")
    if grp:
        chain.append(grp)
    return (chap, part, sub), chain


def show(d, marker=""):
    head = f"  {marker}§{d['section']}  scope: {d['scope_type']}"
    if d["scope_type"] in ("part", "subpart"):
        head += f" ({d['part']}{(' > ' + d['subpart']) if d['subpart'] else ''})"
    elif d["scope_type"] == "chapter":
        head += f" (ch. {d['chapter']})"
    elif d["scope_type"] == "title":
        head += f" ({d['title_group']})"
    print(head)
    for line in textwrap.wrap(d["text"], 92):
        print("      " + line)
    if d["imports_from"]:
        print(f"      -> imports the meaning from §{d['imports_from']}")
    print()


def rowdict(c, row):
    cols = [x[1] for x in c.execute("PRAGMA table_info(definition)")]
    return dict(zip(cols, row))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("term", nargs="?")
    ap.add_argument("--at", help="section id giving the context, e.g. 11-357")
    ap.add_argument("--in", dest="insec", help="list every term a section defines")
    ap.add_argument("--collisions", action="store_true")
    a = ap.parse_args()
    c = con()

    if a.collisions:
        print("Terms defined in more than one scope. Quoting one of these without\n"
              "naming its scope is how a definition becomes wrong two chapters over.\n")
        rows = c.execute("""select term_norm, count(distinct scope_key) n
                            from definition group by term_norm having n>1 order by n desc""")
        for term, n in rows:
            print(f"  {term}  ({n} scopes)")
            for r in c.execute("select * from definition where term_norm=? order by scope_rank",
                               (term,)):
                d = rowdict(c, r)
                print(f"      §{d['section']:<10} {d['scope_type']:<8} "
                      f"{d['text'][:78]}...")
            print()
        return

    if a.insec:
        rows = list(c.execute("select * from definition where section=? order by term", (a.insec,)))
        if not rows:
            sys.exit(f"§{a.insec} defines no terms (or is not in the corpus)")
        print(f"\n§{a.insec} defines {len(rows)} term(s):\n")
        for r in rows:
            show(rowdict(c, r))
        return

    if not a.term:
        ap.error("give a term, or --collisions, or --in SECTION")

    t = a.term.lower().strip()
    rows = [rowdict(c, r) for r in
            c.execute("select * from definition where term_norm=? order by scope_rank", (t,))]
    if not rows:
        like = [r[0] for r in c.execute(
            "select distinct term from definition where term_norm like ? limit 8", (f"%{t}%",))]
        sys.exit(f'no definition of "{a.term}" in the corpus'
                 + (f"\ndid you mean: {', '.join(like)}" if like else ""))

    if not a.at:
        print(f'\n"{a.term}" is defined in {len(rows)} place(s). '
              f"No context given, so none of these is authoritative for your question:\n")
        for d in rows:
            show(d)
        print("Pass --at <section> to resolve which one actually governs.")
        return

    sid = a.at.lstrip("§").upper()
    loc, chain = scope_chain(c, sid)
    if loc is None:
        sys.exit(f"§{sid} is not in the corpus")

    controlling, shadowed = None, []
    for key in chain:
        for d in rows:
            if d["scope_key"] == key and controlling is None:
                controlling, d2 = d, None
                break
        if controlling:
            break
    shadowed = [d for d in rows if d is not controlling]

    chap, part, sub = loc
    where = " > ".join(x for x in [f"ch. {chap}", part, sub] if x)
    print(f'\n"{a.term}" as used in §{sid}')
    print(f"   context: {where}")
    print(f"   scope chain searched, narrowest first:")
    for k in chain:
        print(f"      {k}")
    print()

    if controlling:
        print("CONTROLLING")
        show(controlling, marker="")
    else:
        print("NOT DEFINED for this section.")
        print(f'   "{a.term}" is defined elsewhere in HRS, but none of those definitions\n'
              f"   reaches §{sid}. Do not borrow them. Ordinary meaning applies unless a\n"
              "   general construction provision (HRS ch. 1) supplies one.\n")

    if shadowed:
        print("SHADOWED - defined elsewhere, does NOT govern here")
        for d in shadowed:
            show(d, marker="x ")


if __name__ == "__main__":
    main()
