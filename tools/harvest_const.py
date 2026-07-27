"""Harvest the Hawaiʻi Constitution from the LRB — the supreme state
authority, published as ONE page (and deliberately NOT in the HRS index on
capitol.hawaii.gov, which is the trap this ingest closes).

    python tools/harvest_const.py [--refresh]

raw/hiconst/constitution.html   verbatim fetched page (cache)
graph/hiconst.json              articles, sections, zones, citations

Page shape (verified 2026-07-26): <h3 id="articleii">Article II</h3> +
<h4>Suffrage And Elections</h4>; a TOC of <ol> lists up front (one <li> per
section, in order — the ground truth for the TOC-vs-body assertion); body
sections are '<p>CAPS CATCHLINE</p>' then '<p><strong>Section N.</strong>
text [history]</p>'. Amendment history rides in the trailing bracket
([Am Const Con 1978 and election Nov 7, 1978]) — provenance, not reference.

Ids: 'hiconst:II:4' (article roman, section number), preamble =
'hiconst:preamble'. Matches the namespace hrs_lib's extractor already emits.
"""
import argparse
import html as htmlmod
import json
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hrs_lib import GRAPH, VAULT, fetch, extract_citations, normalize_dashes

URL = "https://lrb.hawaii.gov/constitution/"
RAW_DIR = os.path.join(VAULT, "raw", "hiconst")

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
         "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII"]

H3 = re.compile(r'<h3[^>]*id="(article[ivxl]+|preamble)"[^>]*>(.*?)</h3>', re.I | re.S)
H4 = re.compile(r'<h4[^>]*>(.*?)</h4>', re.S)
PARA = re.compile(r'<p[^>]*>(.*?)</p>', re.S)
BLOCK = re.compile(r'<p[^>]*>(.*?)</p>|<ol[^>]*>(.*?)</ol>', re.S)
# <strong> is optional: Art XVII §5 prints without it; §[24]-style brackets
# are the revisor's unofficial numbering — both are publisher inconsistencies.
SECTION_P = re.compile(r'^\s*(?:<strong>\s*)?Section\s+\[?(\d+(?:\.\d+)?)\]?\.?'
                       r'(?:\s*</strong>)?\s*(.*)$', re.S)
HISTORY = re.compile(r'\[((?:Add|Am|Ren(?:\s|and|um)|Repeal|R\b|Hst)[^\]]*)\]\s*$')
TOC_OL = re.compile(r'<a href="#(article[ivxl]+)">([^<]+)</a></p>\s*<ol[^>]*>(.*?)</ol>', re.I | re.S)
LI = re.compile(r'<li[^>]*>(.*?)</li>', re.S)


def clean(s):
    s = re.sub(r'<br\s*/?>', '\n', s)
    s = re.sub(r'<[^>]+>', '', s)
    s = htmlmod.unescape(s)
    return " ".join(s.split())


def caps_ratio(s):
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if c.isupper()) / len(letters)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()

    os.makedirs(RAW_DIR, exist_ok=True)
    cache = os.path.join(RAW_DIR, "constitution.html")
    if args.refresh or not os.path.exists(cache):
        page, final = fetch(URL)
        with open(cache, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(page)
        print(f"fetched {len(page)} bytes from {final}")
    page = open(cache, encoding="utf-8").read()
    body = normalize_dashes(page)

    # ---- TOC (ground truth): one <ol> per article --------------------------
    toc = {}
    for m in TOC_OL.finditer(body):
        art = m.group(1).replace("article", "").upper()
        toc[art] = [clean(x) for x in LI.findall(m.group(3))]

    # ---- body: split on h3 anchors ----------------------------------------
    anchors = list(H3.finditer(body))
    articles, sections, problems = [], {}, []
    notes = {}
    for i, m in enumerate(anchors):
        seg_end = anchors[i + 1].start() if i + 1 < len(anchors) else len(body)
        seg = body[m.end():seg_end]
        aid = m.group(1).lower()
        if aid == "preamble":
            text = clean(" ".join(PARA.findall(seg)))
            sections["hiconst:preamble"] = {
                "article": "preamble", "num": "", "catchline": "Preamble",
                "operative": text, "history": "", "repealed": False}
            continue
        art = aid.replace("article", "").upper()
        h4 = H4.search(seg)
        articles.append({"roman": art, "title": clean(h4.group(1)) if h4 else ""})

        pending_catch = ""
        cur = None      # (num, catchline, [text parts])
        def flush():
            nonlocal cur
            if not cur:
                return
            num, catch, parts = cur
            joined = " ".join(p for p in parts if p).strip()
            hist = ""
            hm = HISTORY.search(joined)
            if hm:
                hist = hm.group(1)
                joined = joined[:hm.start()].strip()
            repealed = bool(re.match(r"(?i)^\s*Repealed\b", joined))
            sections[f"hiconst:{art}:{num}"] = {
                "article": art, "num": num, "catchline": catch,
                "operative": joined, "history": hist, "repealed": repealed}
            cur = None

        for pm in BLOCK.finditer(seg):
            raw_p, raw_ol = pm.group(1), pm.group(2)
            if raw_ol is not None:
                # an <ol> inside a section: numbered clauses, and sometimes the
                # trailing history bracket rides in the last <li> (Art I §25)
                if cur:
                    for n, li in enumerate(LI.findall(raw_ol), 1):
                        cur[2].append(f"({n}) {clean(li)}")
                continue
            sp = SECTION_P.match(raw_p.strip())
            if sp:
                flush()
                cur = (sp.group(1), pending_catch, [clean(sp.group(2))])
                pending_catch = ""
                continue
            if re.match(r"\s*<strong>\s*Note:", raw_p):
                # publisher's editorial note, not constitutional text
                notes.setdefault(f"{art}:{cur[0] if cur else pending_catch}",
                                 []).append(clean(raw_p))
                continue
            text = clean(raw_p)
            if not text:
                continue
            if caps_ratio(text) > 0.9 and len(text) < 220 and "SECTION" not in text:
                # a catchline for the NEXT section
                if cur:
                    flush()
                pending_catch = text.title() if text.isupper() else text
                continue
            if cur:
                cur[2].append(text)
        flush()

    # ---- TOC-vs-body assertion --------------------------------------------
    ok = True
    for art, entries in toc.items():
        body_nums = sorted(int(s["num"]) for k, s in sections.items()
                           if s["article"] == art and s["num"] and "." not in s["num"])
        want = list(range(1, len(entries) + 1))
        if body_nums != want:
            ok = False
            problems.append({"article": art, "kind": "toc_body_mismatch",
                             "toc_entries": len(entries), "body_nums": body_nums})
    # every parsed article seen in TOC and vice versa
    body_arts = {s["article"] for s in sections.values() if s["article"] != "preamble"}
    if set(toc) != body_arts:
        ok = False
        problems.append({"kind": "article_set_mismatch",
                         "toc_only": sorted(set(toc) - body_arts),
                         "body_only": sorted(body_arts - set(toc))})

    # ---- citations out of operative text ----------------------------------
    edges = []
    for sid, s in sections.items():
        for e in extract_citations(s["operative"]):
            edges.append({"src": sid, "target": e["target"], "kind": e["kind"],
                          "raw": e["raw"]})

    out = {"built": date.today().isoformat(), "url": URL,
           "retrieved": date.today().isoformat(),
           "articles": articles, "sections": sections,
           "edges": edges, "problems": problems, "publisher_notes": notes}
    with open(os.path.join(GRAPH, "hiconst.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)

    n_rep = sum(1 for s in sections.values() if s["repealed"])
    print(f"{len(articles)} articles, {len(sections)} sections "
          f"({n_rep} repealed), {len(edges)} citations out, "
          f"{len(problems)} problems")
    for p in problems[:10]:
        print("  PROBLEM", p)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
