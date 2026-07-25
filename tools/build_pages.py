"""Generate one wiki page per HRS section from graph/ + raw/.

Idempotent and safe to re-run.  Everything outside the CURATED markers is
regenerated from the graph; everything inside is hand-written and preserved
verbatim.  A pre-existing page with no markers is never overwritten - it is
reported so it can be merged by hand.

    python tools/build_pages.py            # write pages
    python tools/build_pages.py --dry-run
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hrs_lib import (CHAPTERS, CHAPTER_TITLE, GRAPH, RAW, STATUTES, VAULT,
                     sec_sort_key, slug, split_section)
from build_graph import read_raw

BEGIN, END = "<!-- BEGIN CURATED -->", "<!-- END CURATED -->"
CORPUS_SRC = "src-2026-07-24-hrs-election-law-corpus"

KIND_LABEL = {
    "hrs_section": "HRS section", "hrs_chapter": "HRS chapter",
    "hrs_part": "part (same chapter)", "usc": "U.S. Code", "cfr": "C.F.R.",
    "public_law": "Public Law", "har": "Hawaii Administrative Rules",
    "hi_const": "Hawaii Constitution", "us_const": "U.S. Constitution",
}


def curated_of(path):
    """Return (curated_body, had_markers, exists)."""
    if not os.path.exists(path):
        return "", False, False
    txt = open(path, encoding="utf-8").read()
    i, j = txt.find(BEGIN), txt.find(END)
    if i == -1 or j == -1 or j < i:
        return "", False, True
    return txt[i + len(BEGIN):j].strip("\n"), True, True


def target_link(kind, target, sections):
    """Wikilink for anything that is or could become an HRS page; plain text
    otherwise.  Out-of-scope HRS sections are deliberately linked so Obsidian's
    unresolved-links view doubles as the ingest queue."""
    if kind == "hrs_section":
        mark = "" if target in sections else "  *(not yet ingested)*"
        return f"[[{slug(target)}|§{target}]]{mark}"
    if kind == "hrs_chapter":
        ch = target.split(":", 1)[1]
        mark = "" if ch in CHAPTER_TITLE else "  *(chapter not in corpus)*"
        return f"[[hrs-ch{ch.lower()}|HRS ch. {ch}]]{mark}"
    if kind == "hrs_part":
        _, ch, roman = target.split(":")
        return f"part {roman} of ch. {ch}"
    if kind == "usc":
        p = target.split(":")
        return f"`{p[1]} U.S.C. §{p[2]}`" if len(p) > 2 and p[2] else f"`title {p[1]} U.S.C.`"
    if kind == "cfr":
        p = target.split(":")
        return f"`{p[1]} C.F.R. §{p[2]}`" if len(p) > 2 and p[2] else f"`title {p[1]} C.F.R.`"
    if kind == "public_law":
        return f"`Public Law {target.split(':')[1]}`"
    if kind == "har":
        p = target.split(":")
        return f"`HAR title {p[1]}" + (f", ch. {p[2]}`" if len(p) > 2 else "`")
    if kind == "hi_const":
        p = target.split(":")
        return f"Haw. Const. art. {p[1]}, §{p[2]}"
    if kind == "us_const":
        return "U.S. Constitution"
    return f"`{target}`"


def tags_for(s):
    t = ["hrs", f"ch-{s['chapter'].lower()}"]
    part = (s.get("part") or "").lower()
    if "campaign finance" in part:
        t.append("campaign-finance")
    if "registration" in part:
        t.append("voter-registration")
    if "conduct of elections" in part or "voting procedures" in part:
        t.append("election-administration")
    if "ballots" in part:
        t.append("ballots")
    if "contest" in part:
        t.append("election-contests")
    if s["chapter"] == "19":
        t.append("election-offenses")
    if s["repealed"]:
        t.append("repealed")
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    G = json.load(open(os.path.join(GRAPH, "sections.json"), encoding="utf-8"))
    sections, built = G["sections"], G["built"]
    edges = json.load(open(os.path.join(GRAPH, "edges.json"), encoding="utf-8"))["edges"]

    out_by = defaultdict(list)
    in_by = defaultdict(list)
    for e in edges:
        out_by[e["src"]].append(e)
        if e["kind"] == "hrs_section":
            in_by[e["target"]].append(e)

    os.makedirs(STATUTES, exist_ok=True)
    written, skipped, conflicts = 0, 0, []

    for sid, s in sections.items():
        path = os.path.join(STATUTES, slug(sid) + ".md")
        curated, had, exists = curated_of(path)
        if exists and not had:
            conflicts.append(path)
            skipped += 1
            continue

        _, body = read_raw(os.path.join(RAW, s["raw_file"]))
        parts = split_section(body)

        # depth is derived, never asserted: a page is 'annotated' only if the
        # curated block actually holds prose (comments and blanks do not count).
        prose = re.sub(r"<!--.*?-->", "", curated, flags=re.S).strip()
        depth = "annotated" if prose else "harvested"

        catch = s["catchline"] or "(untitled)"
        title = f"HRS §{sid} — {catch}"
        aliases = [f"HRS {sid}", sid, f"§{sid}", f"HRS §{sid}"]

        fm = [
            "---", "type: statute", f'title: "{title}"',
            "aliases: " + json.dumps(aliases, ensure_ascii=False),
            "status: verified",
            f"depth: {depth}",
            f"last_verified: {s['retrieved']}",
            f'authority: "HRS §{sid}"',
            f'chapter: "{s["chapter"]}"',
        ]
        if s.get("part"):
            fm.append(f'part: "{s["part"]}"')
        if s.get("subpart"):
            fm.append(f'subpart: "{s["subpart"]}"')
        fm += [f"repealed: {str(s['repealed']).lower()}",
               "tags: [" + ", ".join(tags_for(s)) + "]",
               f'sources: ["[[{CORPUS_SRC}]]"]', "---", ""]

        L = fm
        L.append(f"# HRS §{sid} — {catch}")
        L.append("")
        if depth == "annotated":
            L.append("> [!note] Annotated page")
            L.append("> Verbatim statute text retrieved from capitol.hawaii.gov on "
                     f"{s['retrieved']}. Cross-references extracted mechanically. "
                     "A hand-written operational reading appears below, clearly separated "
                     "from the statute's own words.")
        else:
            L.append("> [!abstract] Machine-harvested page")
            L.append("> Verbatim statute text below, retrieved from capitol.hawaii.gov on "
                     f"{s['retrieved']}. Cross-references are extracted mechanically from that text.")
            L.append("> `depth: harvested` means **no operational interpretation has been "
                     "written yet** — the quote is primary-source, the reading of it is not "
                     "here. See [[INDEX]].")
        L.append("")

        loc = [f"[[hrs-ch{s['chapter'].lower()}|HRS ch. {s['chapter']} — {s['chapter_title']}]]"]
        if s.get("part"):
            loc.append(s["part"])
        if s.get("subpart"):
            loc.append(s["subpart"])
        L.append("**Where this sits:** " + " › ".join(loc))
        if s["repealed"]:
            L.append("")
            L.append("> [!warning] Repealed or reserved. Kept because the citation still appears "
                     "in other sections and in older filings.")
        L.append("")

        L.append("## Statute text (verbatim)")
        L.append("")
        quoted = parts["operative"] or "(no text retrieved)"
        for line in quoted.split("\n"):
            L.append(("> " + line) if line.strip() else ">")
        L.append("")

        for zone, heading, blurb in (
            ("operative", "References out — in the statute text",
             "Citations that appear inside §%s itself. This is the law pointing at other law." % sid),
            ("annotation", "References out — in the revisor's notes",
             "Citations from Case Notes, Cross References and other editorial apparatus "
             "appended after the source note. **Not statutory text.**"),
        ):
            rows = [e for e in out_by.get(sid, []) if e["zone"] == zone]
            if not rows:
                continue
            L.append(f"## {heading}")
            L.append("")
            L.append(blurb)
            L.append("")
            L.append("| Target | Kind | As written |")
            L.append("|---|---|---|")
            seen = set()
            for e in rows:
                k = (e["target"], e["raw"])
                if k in seen:
                    continue
                seen.add(k)
                L.append(f"| {target_link(e['kind'], e['target'], sections)} "
                         f"| {KIND_LABEL.get(e['kind'], e['kind'])} | {e['raw']} |")
            L.append("")

        inc = in_by.get(sid, [])
        if inc:
            L.append("## Referenced by")
            L.append("")
            op = sorted({e["src"] for e in inc if e["zone"] == "operative"}, key=sec_sort_key)
            an = sorted({e["src"] for e in inc if e["zone"] == "annotation"}, key=sec_sort_key)
            if op:
                L.append("**In statute text:** " + ", ".join(
                    f"[[{slug(x)}|§{x}]]" for x in op))
                L.append("")
            if an:
                L.append("**In revisor's notes:** " + ", ".join(
                    f"[[{slug(x)}|§{x}]]" for x in an))
                L.append("")

        if s["history"]:
            L.append("## Amendment history")
            L.append("")
            L.append(f"`{s['history']}`")
            L.append("")
            hist = sorted({e["target"] for e in out_by.get(sid, [])
                           if e["zone"] == "history" and e["kind"] == "hrs_section"},
                          key=sec_sort_key)
            if hist:
                L.append("**Prior numbering:** this section previously appeared as "
                         + ", ".join(f"§{h}" for h in hist)
                         + ". That is renumbering provenance from the source note, "
                           "**not** a cross-reference to another statute.")
                L.append("")
            L.append("*What each act actually changed is not traced on this page.*")
            L.append("")

        L.append(BEGIN)
        if curated:
            L.append(curated)
        else:
            L.append("")
            L.append("<!-- Hand-written analysis goes here. Everything between these two markers")
            L.append("     survives `python tools/build_pages.py`. Everything outside is regenerated. -->")
            L.append("")
        L.append(END)
        L.append("")

        L.append("## Provenance")
        L.append("")
        L.append(f"- Source: <{s['url']}>")
        L.append(f"- Retrieved: {s['retrieved']} · Raw copy: `raw/hrs/{s['raw_file']}`")
        L.append(f"- Corpus source page: [[{CORPUS_SRC}]]")
        L.append("")

        if not args.dry_run:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("\n".join(L))
        written += 1

    # ---- chapter hub pages -------------------------------------------------
    by_chap = defaultdict(list)
    for sid, s in sections.items():
        by_chap[s["chapter"]].append(sid)

    for chap, _vol, _d, ctitle in CHAPTERS:
        sids = sorted(by_chap.get(chap, []), key=sec_sort_key)
        path = os.path.join(STATUTES, f"hrs-ch{chap.lower()}.md")
        curated, had, exists = curated_of(path)
        if exists and not had:
            conflicts.append(path)
            continue

        L = ["---", "type: synthesis", f'title: "HRS Chapter {chap} — {ctitle}"',
             "aliases: " + json.dumps([f"HRS ch. {chap}", f"chapter {chap}", f"HRS Chapter {chap}"]),
             "status: verified", "depth: harvested", f"last_verified: {built}",
             f'authority: "HRS ch. {chap}"', f'chapter: "{chap}"',
             f"tags: [hrs, ch-{chap.lower()}, chapter-index]",
             f'sources: ["[[{CORPUS_SRC}]]"]', "---", "",
             f"# HRS Chapter {chap} — {ctitle}", "",
             f"Index of every section harvested from chapter {chap}. "
             f"{len(sids)} sections, retrieved {built}.", ""]

        if not sids:
            L += ["> [!warning] No sections. The chapter is listed on the Office of Elections "
                  "election-laws page but capitol.hawaii.gov serves no section files for it, "
                  "which is consistent with the chapter having been repealed in full.", ""]
        else:
            cur = None
            L += ["| Section | Catchline | Refs out | Refs in |", "|---|---|---:|---:|"]
            for sid in sids:
                s = sections[sid]
                grp = " › ".join(x for x in [s.get("part"), s.get("subpart")] if x)
                if grp != cur:
                    cur = grp
                    if grp:
                        L.append(f"| **{grp}** | | | |")
                nout = len({(e['kind'], e['target']) for e in out_by.get(sid, [])
                            if e["zone"] == "operative"})
                nin = len({e["src"] for e in in_by.get(sid, []) if e["zone"] == "operative"})
                cl = s["catchline"] or "(untitled)"
                if s["repealed"]:
                    cl = f"~~{cl}~~"
                L.append(f"| [[{slug(sid)}\\|§{sid}]] | {cl} | {nout or ''} | {nin or ''} |")
            L.append("")

        L += [BEGIN, curated if curated else "", END, "", "## Provenance", "",
              f"- Generated from `graph/sections.json`, built {built}.",
              f"- Corpus source page: [[{CORPUS_SRC}]]", ""]
        if not args.dry_run:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("\n".join(L))

    print(f"statute pages written {written}   skipped(existing, no markers) {skipped}")
    print(f"chapter hubs written  {len(CHAPTERS)}")
    if conflicts:
        print("\nNOT OVERWRITTEN - hand-written page without curated markers:")
        for c in conflicts:
            print("   ", os.path.relpath(c, VAULT))


if __name__ == "__main__":
    main()
