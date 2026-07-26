"""Generate one wiki page per HAR section from graph/har-rules.json.

    python tools/har_build_pages.py            # write pages to har/
    python tools/har_build_pages.py --dry-run

Same contract as build_pages.py: idempotent, everything outside the CURATED
markers regenerates, a pre-existing page without markers is never overwritten.
`depth` is derived from whether the curated block holds prose.
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from har_lib import GRAPH, HAR_PAGES, VAULT, sec_sort_key, slug
from build_pages import curated_of

BEGIN, END = "<!-- BEGIN CURATED -->", "<!-- END CURATED -->"
SRC_PAGE = "src-2026-07-25-csc-har-rules"

TAGS = {
    "3-160": ["har", "csc", "campaign-finance"],
    "3-161": ["har", "csc", "campaign-finance", "procedure"],
}


def hrs_link(target, hrs_sections):
    if target.startswith("ch:"):
        ch = target[3:]
        known = os.path.exists(os.path.join(VAULT, "statutes",
                                            f"hrs-ch{ch.lower()}.md"))
        return (f"[[hrs-ch{ch.lower()}|HRS ch. {ch}]]" if known
                else f"HRS ch. {ch}  *(chapter not in corpus)*")
    mark = "" if target in hrs_sections else "  *(not yet ingested)*"
    return f"[[hrs-{target.lower()}|HRS §{target}]]{mark}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    R = json.load(open(os.path.join(GRAPH, "har-rules.json"), encoding="utf-8"))
    hrs_sections = {k.upper() for k in json.load(
        open(os.path.join(GRAPH, "sections.json"), encoding="utf-8"))["sections"]}

    out_by, in_by = defaultdict(list), defaultdict(list)
    for e in R["edges"]:
        out_by[e["src"]].append(e)
        if e["kind"] == "har_section":
            in_by[e["target"]].append(e)

    os.makedirs(HAR_PAGES, exist_ok=True)
    written, skipped, conflicts = 0, 0, []

    for chap, C in R["chapters"].items():
        for sid, s in C["sections"].items():
            path = os.path.join(HAR_PAGES, slug(sid) + ".md")
            curated, had, exists = curated_of(path)
            if exists and not had:
                conflicts.append(path)
                skipped += 1
                continue

            prose = re.sub(r"<!--.*?-->", "", curated, flags=re.S).strip()
            depth = "annotated" if prose else "harvested"
            catch = s["catchline"] or "(untitled)"
            title = f"HAR §{sid} — {catch}"

            fm = ["---", "type: rule", f'title: "{title}"',
                  "aliases: " + json.dumps(
                      [f"HAR {sid}", sid, f"§{sid}", f"HAR §{sid}"]),
                  "status: verified", f"depth: {depth}",
                  f"last_verified: {C['retrieved']}",
                  f'authority: "HAR §{sid}"', f'chapter: "{chap}"']
            if s["subchapter"]:
                fm.append(f'subchapter: "{s["subchapter"]}"')
            fm += [f"repealed: {str(s['repealed']).lower()}",
                   "tags: [" + ", ".join(
                       TAGS[chap] + (["repealed"] if s["repealed"] else [])) + "]",
                   f'sources: ["[[{SRC_PAGE}]]"]', "---", "",
                   f"# HAR §{sid} — {catch}", ""]
            L = fm

            if depth == "annotated":
                L += ["> [!note] Annotated page",
                      "> Verbatim rule text retrieved from ags.hawaii.gov on "
                      f"{C['retrieved']}. A hand-written operational reading "
                      "appears below, clearly separated from the rule's own words.", ""]
            else:
                L += ["> [!abstract] Machine-harvested page",
                      "> Verbatim rule text below, extracted from the CSC's "
                      f"chapter PDF (retrieved {C['retrieved']}). Citations are "
                      "extracted mechanically. `depth: harvested` means **no "
                      "operational interpretation has been written yet**. See [[INDEX]].", ""]

            loc = [f"[[{slug(chap)}|HAR ch. {chap} — {C['catchline']}]]"]
            if s["subchapter"]:
                loc.append(s["subchapter"])
            L.append("**Where this sits:** " + " › ".join(loc))
            if s["repealed"]:
                L += ["", "> [!warning] Repealed. Kept because citations to it "
                          "survive elsewhere and in older filings."]
            L.append("")

            if not s["repealed"]:
                L += ["## Rule text (verbatim)", ""]
                for line in (s["operative"] or "(no text)").split("\n"):
                    L.append(("> " + line) if line.strip() else ">")
                L.append("")

            for zone, heading, blurb in (
                ("auth", "Authority (Auth:)",
                 "The statutes the agency asserts **authorised** it to adopt this "
                 "rule. A court asking whether the rule exceeds the commission's "
                 "authority looks here. The agency's own assertion, not the "
                 "revisor's or a court's."),
                ("imp", "Implements (Imp:)",
                 "The statutes the agency asserts this rule **implements or "
                 "interprets**. The agency's own assertion."),
            ):
                rows = [e for e in out_by.get(f"har:{sid}", []) if e["zone"] == zone]
                as_printed = s["auth_raw"] if zone == "auth" else s["imp_raw"]
                if not rows and not as_printed:
                    continue
                L += [f"## {heading}", "", blurb, ""]
                if as_printed:
                    L += [f"As printed: `({'Auth' if zone == 'auth' else 'Imp'}: "
                          f"{as_printed})`", ""]
                targets = sorted({e["target"] for e in rows}, key=sec_sort_key)
                if targets:
                    L += ["Maps to: " + ", ".join(
                        hrs_link(t, hrs_sections) for t in targets), ""]

            rows = [e for e in out_by.get(f"har:{sid}", []) if e["zone"] == "operative"]
            if rows:
                L += ["## References out — in the rule text", "",
                      "| Target | Kind | As written |", "|---|---|---|"]
                seen = set()
                for e in rows:
                    k = (e["target"], e["raw"])
                    if k in seen:
                        continue
                    seen.add(k)
                    if e["kind"] == "har_section":
                        t = e["target"][4:]
                        cell = f"[[{slug(t)}|HAR §{t}]]"
                        if not re.match(r"^3-16[01]-", t):
                            cell += "  *(other title, not ingested)*"
                        kind = "HAR section"
                    elif e["kind"] == "har_chapter":
                        t = e["target"].split(":")[-1]
                        cell = f"[[{slug(t)}|HAR ch. {t}]]"
                        kind = "HAR chapter"
                    elif e["kind"] == "hrs_section":
                        cell = hrs_link(e["target"], hrs_sections)
                        kind = "HRS section"
                    elif e["kind"] == "hrs_chapter":
                        cell = hrs_link(e["target"], hrs_sections)
                        kind = "HRS chapter"
                    else:
                        cell, kind = f"`{e['target']}`", e["kind"]
                    L.append(f"| {cell} | {kind} | {e['raw']} |")
                L.append("")

            inc = sorted({e["src"][4:] for e in in_by.get(f"har:{sid}", [])},
                         key=sec_sort_key)
            if inc:
                L += ["## Referenced by", "",
                      "**In rule text:** " + ", ".join(
                          f"[[{slug(x)}|§{x}]]" for x in inc), ""]

            if s["source_note"] or s["effective"]:
                L += ["## Source note", ""]
                if s["source_note"]:
                    L.append(f"`{s['source_note']}`")
                if s["effective"]:
                    L.append("")
                    L.append(f"Current text effective **{s['effective']}** "
                             "(compilation date; the printed received-stamp is "
                             "normalised — see the source page for the print-"
                             "defect log).")
                L.append("")

            L += [BEGIN]
            if curated:
                L.append(curated)
            else:
                L += ["", "<!-- Hand-written analysis goes here. Everything "
                          "between these two markers survives "
                          "`python tools/har_build_pages.py`. -->", ""]
            L += [END, "", "## Provenance", "",
                  f"- Source PDF: <{C['url']}> (SHA-256 `{C['sha256_pdf'][:16]}…`)",
                  f"- Retrieved: {C['retrieved']} · Extracted text: "
                  f"`raw/har/har-{chap}.txt`",
                  f"- Source page: [[{SRC_PAGE}]]", ""]

            if not args.dry_run:
                with open(path, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write("\n".join(L))
            written += 1

        # ---- chapter hub ---------------------------------------------------
        path = os.path.join(HAR_PAGES, slug(chap) + ".md")
        curated, had, exists = curated_of(path)
        if exists and not had:
            conflicts.append(path)
            continue
        sids = sorted(C["sections"], key=sec_sort_key)
        L = ["---", "type: synthesis",
             f'title: "HAR Chapter {chap} — {C["catchline"]}"',
             "aliases: " + json.dumps([f"HAR ch. {chap}", f"chapter {chap}",
                                       f"HAR {chap}"]),
             "status: verified", "depth: harvested",
             f"last_verified: {C['retrieved']}", f'authority: "HAR ch. {chap}"',
             "tags: [" + ", ".join(TAGS[chap] + ["chapter-index"]) + "]",
             f'sources: ["[[{SRC_PAGE}]]"]', "---", "",
             f"# HAR Chapter {chap} — {C['catchline']}", "",
             f"The Campaign Spending Commission's rules, effective "
             f"{C['effective_as_printed']}. {len(sids)} sections. "
             f"Typed edges to statute: [[har-citation-graph]].", ""]
        cur = None
        L += ["| Section | Catchline | Imp targets |", "|---|---|---|"]
        for sid in sids:
            s = C["sections"][sid]
            if s["subchapter"] != cur:
                cur = s["subchapter"]
                if cur:
                    L.append(f"| **{cur}** | | |")
            cl = s["catchline"] or "(untitled)"
            if s["repealed"]:
                cl = f"~~{cl}~~"
            imps = sorted({e["target"] for e in out_by.get(f"har:{sid}", [])
                           if e["zone"] == "imp" and e["kind"] == "hrs_section"},
                          key=sec_sort_key)
            L.append(f"| [[{slug(sid)}\\|§{sid}]] | {cl} | "
                     f"{', '.join('§' + t for t in imps)} |")
        L += ["", "## Historical note (as printed)", "",
              f"> {C.get('historical_note', '')}", "",
              BEGIN, curated if curated else "", END, "",
              "## Provenance", "",
              f"- Source PDF: <{C['url']}> (SHA-256 `{C['sha256_pdf'][:16]}…`)",
              f"- Retrieved {C['retrieved']}; generated from `graph/har-rules.json`.",
              f"- Source page: [[{SRC_PAGE}]]", ""]
        if not args.dry_run:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\n".join(L))

    print(f"rule pages written {written}   skipped(existing, no markers) {skipped}")
    print(f"chapter hubs written {len(R['chapters'])}")
    if conflicts:
        print("\nNOT OVERWRITTEN - hand-written page without curated markers:")
        for c in conflicts:
            print("   ", os.path.relpath(c, VAULT))


if __name__ == "__main__":
    main()
