"""Measure the cost of ingesting the citation frontier.

Answers: how many sections would each cited-but-unharvested chapter add, and is
the citation a whole-chapter dependency or a single-definition pinpoint?
Read-only; writes nothing to the vault.
"""
import json
import os
import re
import sqlite3
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hrs_lib import BASE, GRAPH, fetch

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".chapmap.json")


def chapter_volume_map():
    if os.path.exists(CACHE):
        return json.load(open(CACHE, encoding="utf-8"))
    vols = re.findall(r'href="/hrscurrent/(Vol[^/"]+)/"', fetch(BASE + "/"), re.I)
    m = {}
    for v in sorted(set(vols)):
        for d in re.findall(r'href="/hrscurrent/%s/(HRS\d+[A-Z]?)/"' % re.escape(v),
                            fetch(f"{BASE}/{v}/"), re.I):
            ch = d[3:].lstrip("0") or "0"
            m.setdefault(ch, v)
    json.dump(m, open(CACHE, "w", encoding="utf-8"))
    return m


def main():
    U = json.load(open(os.path.join(GRAPH, "unresolved.json"), encoding="utf-8"))["unresolved"]
    con = sqlite3.connect(os.path.join(GRAPH, "hrs.db"))

    whole = {r["target"].split(":")[1]: r for r in U if r["kind"] == "hrs_chapter"}
    pin = defaultdict(list)
    for r in U:
        if r["kind"] == "hrs_section":
            pin[r["target"].split("-")[0]].append(r)

    cmap = chapter_volume_map()
    rows = []
    for ch in sorted(set(whole) | set(pin), key=lambda c: (int(re.match(r"\d+", c).group()), c)):
        vol = cmap.get(ch)
        n = "?"
        if vol:
            try:
                html = fetch(f"{BASE}/{vol}/HRS{('000'+ch)[-4:] if not ch[-1].isalpha() else ('000'+ch)[-5:]}/")
                n = len(set(re.findall(r'href="[^"]+/(HRS_[^"/]+\.htm)"', html, re.I))) - 1
            except Exception:
                n = "?"
        wr = whole.get(ch)
        pins = pin.get(ch, [])
        rows.append({
            "ch": ch, "sections": n,
            "whole_cites": wr["count"] if wr else 0,
            "pin_cites": sum(p["count"] for p in pins),
            "pin_targets": sorted({p["target"] for p in pins}),
        })

    tot = sum(r["sections"] for r in rows if isinstance(r["sections"], int))
    print(f"{'ch':>6} {'secs':>5} {'chap-cites':>10} {'pin-cites':>9}  pinpoint sections")
    for r in rows:
        pt = ", ".join(r["pin_targets"][:5]) + ("…" if len(r["pin_targets"]) > 5 else "")
        print(f"{r['ch']:>6} {str(r['sections']):>5} {r['whole_cites']:>10} {r['pin_cites']:>9}  {pt}")
    print(f"\n{len(rows)} chapters, ~{tot} sections would be added "
          f"(current corpus: 393). That is round 1 only.")

    # How much of the frontier is pinpoint-only?
    ponly = [r for r in rows if r["whole_cites"] == 0]
    psec = sum(r["sections"] for r in ponly if isinstance(r["sections"], int))
    print(f"\n{len(ponly)} of {len(rows)} chapters are cited ONLY for specific sections, "
          f"never as a whole chapter.")
    print(f"Those alone are ~{psec} sections to obtain "
          f"{sum(len(r['pin_targets']) for r in ponly)} actually-cited sections.")


if __name__ == "__main__":
    main()
