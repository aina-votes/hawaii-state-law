"""Write citation-queue.md: everything the harvested corpus cites but does not
contain.

Chapter and title names come from the State's own master index
(capitol.hawaii.gov/docs/HRS.htm), saved to raw/, never from recall.
"""
import datetime as dt
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hrs_lib import GRAPH, IN_SCOPE, RAW, VAULT, fetch, sec_sort_key, strip_html

INDEX_URL = "https://www.capitol.hawaii.gov/docs/HRS.htm"
INDEX_RAW = os.path.join(os.path.dirname(RAW), "hrs-master-chapter-index.md")


def chapter_titles():
    """{chapter: (title, hrs_title_group)} from the State's master index."""
    if os.path.exists(INDEX_RAW):
        text = open(INDEX_RAW, encoding="utf-8").read()
        text = re.sub(r"^---.*?---\n", "", text, flags=re.S)
        text = re.sub(r"^\s*<!--.*?-->\s*", "", text, flags=re.S)
    else:
        text = strip_html(fetch(INDEX_URL))
        hdr = ("---\n"
               f"retrieved: {dt.date.today().isoformat()}\n"
               f"url: {INDEX_URL}\n"
               "publisher: Hawaii State Legislature (capitol.hawaii.gov)\n"
               "kind: master chapter index\n"
               "method: urllib GET with browser User-Agent, charset sniffed, HTML stripped\n"
               "---\n\n"
               "<!-- PROVENANCE HEADER ABOVE. VERBATIM RETRIEVED TEXT BELOW. DO NOT EDIT. -->\n\n")
        os.makedirs(os.path.dirname(INDEX_RAW), exist_ok=True)
        with open(INDEX_RAW, "w", encoding="utf-8") as fh:
            fh.write(hdr + text + "\n")

    blocks = [" ".join(b.split()) for b in re.split(r"\n\s*\n", text)]
    out, group = {}, ""
    i = 0
    while i < len(blocks):
        b = blocks[i]
        tm = re.match(r"TITLE\s+(\d+[A-Z]?)\.\s*(.+)$", b)
        if tm:
            group = f"Title {tm.group(1)}. {tm.group(2).title()}"
            i += 1
            continue
        if re.fullmatch(r"\d+[A-Z]?", b) and i + 1 < len(blocks):
            nxt = blocks[i + 1]
            if nxt and not re.fullmatch(r"\d+[A-Z]?", nxt) and not nxt.startswith("TITLE"):
                out.setdefault(b, (nxt, group))
                i += 2
                continue
        i += 1
    return out


def main():
    titles = chapter_titles()
    U = json.load(open(os.path.join(GRAPH, "unresolved.json"), encoding="utf-8"))
    built = U["built"]
    rows = U["unresolved"]
    covered = json.load(open(os.path.join(GRAPH, "repealed_ranges.json"),
                             encoding="utf-8"))["covered_by_range_repeal"]

    zones = {}
    for e in json.load(open(os.path.join(GRAPH, "edges.json"), encoding="utf-8"))["edges"]:
        zones.setdefault(e["target"], set()).add(e["zone"])

    chaps = [r for r in rows if r["kind"] == "hrs_chapter"]
    secs = [r for r in rows if r["kind"] == "hrs_section"]
    fed = [r for r in rows if r["kind"] in ("usc", "cfr", "public_law")]
    other = [r for r in rows if r["kind"] in ("har", "hi_const", "us_const")]

    # Group loose sections by their parent chapter.
    by_chap = defaultdict(list)
    for r in secs:
        by_chap[r["target"].split("-")[0].upper()].append(r)

    L = ["---", "type: synthesis", 'title: "Citation queue — cited but not yet ingested"',
         'aliases: ["citation queue", "ingest queue", "unresolved citations"]',
         "status: derived", f"last_verified: {built}",
         "tags: [meta, citation-graph, queue]",
         'sources: ["[[src-2026-07-24-hrs-election-law-corpus]]"]', "---", "",
         "# Citation queue — cited but not yet ingested", "",
         "Every statute, rule, and constitutional provision that the harvested corpus points at "
         "but does **not** contain. Generated from `graph/unresolved.json`; regenerate with "
         "`python tools/build_queue.py`. Do not hand-edit above the curated block.", "",
         f"Built {built} from the 14 HRS chapters listed on the Office of Elections "
         "[election-laws page](https://elections.hawaii.gov/resources/election-laws/). "
         "See [[INDEX]] and [[hrs-citation-graph]].", "",
         "**How to read the zone column.** `statute` means the citation sits in operative "
         "statutory text — the law itself points there, so the gap is real. `notes` means it "
         "appears only in the revisor's Case Notes or Cross References, which is a weaker "
         "signal. `history` means it is prior-numbering provenance in a source note, not a "
         "reference at all.", ""]

    def zlabel(t):
        z = zones.get(t, set())
        return "/".join(x for x in ("operative", "history", "annotation") if x in z) \
            .replace("operative", "statute").replace("annotation", "notes") or "-"

    L += ["## 1. Whole HRS chapters cited from inside the corpus", "",
          "Ranked by how often the corpus reaches for them. These are the highest-value "
          "additions: each one is a body of law our statutes actively depend on.", "",
          "| Chapter | Official title | Cites | Zone | Cited by |", "|---|---|---:|---|---|"]
    for r in chaps:
        ch = r["target"].split(":")[1]
        t, grp = titles.get(ch, ("*(title not found in master index)*", ""))
        cited = ", ".join(f"[[hrs-{s.lower()}\\|§{s}]]" for s in r["cited_by"][:8])
        if len(r["cited_by"]) > 8:
            cited += f", +{len(r['cited_by'])-8} more"
        L.append(f"| **HRS ch. {ch}** | {t} | {r['count']} | {zlabel(r['target'])} | {cited} |")
    L.append("")

    L += ["## 2. Individual sections cited from outside those chapters", "",
          "Grouped by parent chapter. Ingesting the parent chapter picks these up.", ""]
    for ch in sorted(by_chap, key=lambda c: -sum(r["count"] for r in by_chap[c])):
        t, grp = titles.get(ch, ("*(title not found in master index)*", ""))
        L.append(f"### HRS ch. {ch} — {t}")
        if grp:
            L.append(f"*{grp}*")
        L.append("")
        L.append("| Section | Cites | Zone | Cited by |")
        L.append("|---|---:|---|---|")
        for r in sorted(by_chap[ch], key=lambda r: sec_sort_key(r["target"])):
            cited = ", ".join(f"[[hrs-{s.lower()}\\|§{s}]]" for s in r["cited_by"])
            L.append(f"| §{r['target']} | {r['count']} | {zlabel(r['target'])} | {cited} |")
        L.append("")

    L += ["## 3. Federal law", "",
          "A different legal layer. State pages must never let one of these silently answer "
          "a state-law question — see rule 9 in `CLAUDE.md`.", "",
          "| Citation | Cites | Zone | Cited by |", "|---|---:|---|---|"]
    for r in fed:
        p = r["target"].split(":")
        unit = {"usc": "U.S.C.", "cfr": "C.F.R.", "public_law": "Pub. L."}[r["kind"]]
        name = f"{p[1]} {unit}" + (f" §{p[2]}" if len(p) > 2 and p[2] else "")
        cited = ", ".join(f"[[hrs-{s.lower()}\\|§{s}]]" for s in r["cited_by"])
        L.append(f"| `{name}` | {r['count']} | {zlabel(r['target'])} | {cited} | ")
    L += ["", "## 4. Constitutions and administrative rules", "",
          "| Citation | Cites | Zone | Cited by |", "|---|---:|---|---|"]
    for r in other:
        p = r["target"].split(":")
        if r["kind"] == "hi_const":
            name = f"Haw. Const. art. {p[1]}, §{p[2]}"
        elif r["kind"] == "us_const":
            name = "U.S. Constitution"
        else:
            name = "HAR title " + p[1] + (f", ch. {p[2]}" if len(p) > 2 else "")
        cited = ", ".join(f"[[hrs-{s.lower()}\\|§{s}]]" for s in r["cited_by"])
        L.append(f"| {name} | {r['count']} | {zlabel(r['target'])} | {cited} |")
    L.append("")

    if covered:
        L += ["## 5. Not missing — covered by a range repeal", "",
              "These section numbers have no page of their own because a single repealing "
              "section covers the whole range. They are accounted for, not gaps.", "",
              "| Section | Repealed by |", "|---|---|"]
        for k in sorted(covered, key=sec_sort_key):
            L.append(f"| §{k} | [[hrs-{covered[k].lower()}\\|§{covered[k]}]] |")
        L.append("")

    L += ["## Also on the Office of Elections page, not yet ingested", "",
          "The election-laws page lists four source categories besides the HRS chapters. "
          "None are harvested yet:", "",
          "- U.S. Constitution excerpts",
          "- Help America Vote Act (HAVA)",
          "- Hawaiʻi State Constitution excerpts",
          "- Hawaiʻi Administrative Rules — Elections Commission (ch. 3-170) and Office of "
          "Elections (ch. 3-177), both served as PDFs", "",
          "The HAR chapters matter most: they are the operative rules under these statutes. "
          "Note that the **campaign finance** rules (HAR title 3, ch. 160) are *not* linked "
          "from this page — the Campaign Spending Commission publishes separately.", "",
          "<!-- BEGIN CURATED -->", "",
          "<!-- Priority calls, notes on why a chapter matters, and Sam's steer on ingest",
          "     order go here. This block survives regeneration. -->", "",
          "<!-- END CURATED -->", "",
          "## Provenance", "",
          f"- Generated {built} from `graph/unresolved.json` by `tools/build_queue.py`.",
          f"- Chapter titles from the State's master index: <{INDEX_URL}>, "
          f"raw copy at `raw/hrs-master-chapter-index.md`.", ""]

    path = os.path.join(VAULT, "citation-queue.md")
    # Preserve an existing curated block.
    if os.path.exists(path):
        old = open(path, encoding="utf-8").read()
        i, j = old.find("<!-- BEGIN CURATED -->"), old.find("<!-- END CURATED -->")
        if i != -1 and j > i:
            keep = old[i + len("<!-- BEGIN CURATED -->"):j].strip("\n")
            txt = "\n".join(L)
            a, b = txt.find("<!-- BEGIN CURATED -->"), txt.find("<!-- END CURATED -->")
            L = [txt[:a + len("<!-- BEGIN CURATED -->")] + "\n" + keep + "\n" + txt[b:]]

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print(f"citation-queue.md written: {len(chaps)} chapters, {len(secs)} sections, "
          f"{len(fed)} federal, {len(other)} const/HAR, {len(covered)} range-repeal-covered")
    print(f"chapter titles resolved from master index: {len(titles)}")
    missing = [r['target'].split(':')[1] for r in chaps
               if r['target'].split(':')[1] not in titles]
    if missing:
        print("  !! no title found for:", ", ".join(missing))


if __name__ == "__main__":
    main()
