"""Enumerate the whole HRS: every volume, chapter, and section count.

Fetches only directory listings (one request per chapter), never section text.
Produces graph/hrs-universe.json, the planning artifact for deciding whether and
how to harvest all of state law.

    python tools/enumerate_hrs.py
"""
import datetime as dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hrs_lib import BASE, GRAPH, fetch

OUT = os.path.join(GRAPH, "hrs-universe.json")


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from build_queue import chapter_titles
    titles = chapter_titles()

    vols = sorted(set(re.findall(r'href="/hrscurrent/(Vol[^/"]+)/"', fetch(BASE + "/"), re.I)))
    print(f"{len(vols)} volumes")

    chapters = []
    for vi, v in enumerate(vols, 1):
        dirs = sorted(set(re.findall(
            r'href="/hrscurrent/%s/(HRS\d+[A-Z]?)/"' % re.escape(v),
            fetch(f"{BASE}/{v}/"), re.I)))
        print(f"  [{vi}/{len(vols)}] {v:24s} {len(dirs):4d} chapters", flush=True)
        for d in dirs:
            ch = d[3:].lstrip("0") or "0"
            try:
                html = fetch(f"{BASE}/{v}/{d}/", pause=0.12)
                files = set(re.findall(r'href="[^"]+/(HRS_[^"/]+\.htm)"', html, re.I))
                n = max(0, len(files) - 1)          # minus the chapter TOC page
            except Exception as e:                   # noqa: BLE001
                n = -1
                print(f"      !! {ch}: {e}")
            t, grp = titles.get(ch, ("", ""))
            chapters.append({"chapter": ch, "volume": v, "dir": d,
                             "sections": n, "title": t, "hrs_title_group": grp})

    ok = [c for c in chapters if c["sections"] >= 0]
    tot = sum(c["sections"] for c in ok)
    empty = [c for c in ok if c["sections"] == 0]
    json.dump({"built": dt.date.today().isoformat(),
               "volumes": len(vols), "chapters": len(chapters),
               "total_sections": tot, "detail": chapters},
              open(OUT, "w", encoding="utf-8"), indent=1)

    print(f"\nvolumes           {len(vols)}")
    print(f"chapters          {len(chapters)}")
    print(f"  empty/repealed  {len(empty)}")
    print(f"TOTAL SECTIONS    {tot}")
    print(f"\nlargest chapters:")
    for c in sorted(ok, key=lambda c: -c["sections"])[:12]:
        print(f"   ch {c['chapter']:>6}  {c['sections']:5d}  {c['title'][:58]}")
    buckets = [(0, 0), (1, 10), (11, 25), (26, 50), (51, 100), (101, 250), (251, 10000)]
    print("\nsize distribution:")
    for lo, hi in buckets:
        n = [c for c in ok if lo <= c["sections"] <= hi]
        print(f"   {lo:>4}-{hi:<5} {len(n):5d} chapters  {sum(x['sections'] for x in n):6d} sections")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
