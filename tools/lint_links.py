"""Wikilink lint.

Resolved links are navigation.  Unresolved links that point at an HRS section are
deliberate - they are the ingest queue, and Obsidian's unresolved-links view is
the live version of citation-queue.md.  Anything else unresolved is a typo or a
page somebody meant to write.
"""
import collections
import glob
import os
import re
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# [[page]], [[page|alias]], and the table-escaped [[page\|alias]]
RX = re.compile(r"\[\[\s*([^\]|#]+?)\s*(?:\\?\|[^\]]*)?\]\]")


def main():
    os.chdir(VAULT)
    pages = {os.path.splitext(os.path.basename(f))[0]
             for f in glob.glob("**/*.md", recursive=True)}
    links = collections.Counter()
    where = {}
    for f in glob.glob("**/*.md", recursive=True):
        if f.replace(os.sep, "/").startswith("raw/"):
            continue
        for m in RX.finditer(open(f, encoding="utf-8").read()):
            t = m.group(1).strip().rstrip("\\").strip()
            links[t] += 1
            where.setdefault(t, set()).add(f)

    un = {k: v for k, v in links.items() if k not in pages}
    hrs = {k: v for k, v in un.items() if k.startswith("hrs-")}
    oth = {k: v for k, v in un.items() if not k.startswith("hrs-")}

    print(f"distinct wikilink targets {len(links)}   resolved {len(links)-len(un)}   "
          f"unresolved {len(un)}")
    print(f"  unresolved HRS  (deliberate: the ingest queue)  {len(hrs)}")
    print(f"  unresolved other (typo or page to write)        {len(oth)}")
    if hrs:
        print("\n  HRS targets awaiting ingest:")
        for k, v in sorted(hrs.items(), key=lambda x: -x[1]):
            print(f"     {k:24s} x{v}")
    if oth:
        print("\n  non-HRS unresolved:")
        for k, v in sorted(oth.items(), key=lambda x: -x[1]):
            print(f"     {k:34s} x{v}   e.g. {sorted(where[k])[0]}")

    orphan = sorted(p for p in pages
                    if p not in links and p not in ("INDEX", "CLAUDE", "log"))
    print(f"\npages with no inbound wikilink: {len(orphan)}")
    for p in orphan[:15]:
        print("   ", p)
    if len(orphan) > 15:
        print(f"    ... and {len(orphan)-15} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
