"""Harvest ALL of the CSC's advisory opinions — the operative interpretive
gloss on campaign finance. The Commission enforces on these, so in practice
they bind, whatever their formal weight.

    python tools/harvest_csc_aos.py [--refresh]

Two publication forms, discovered 2026-07-26 (memory said "14 PDFs" — wrong
twice: 13 PDFs, and ~40 MORE opinions from 1996-2009 published as HTML pages
under /campaign/guidance/advisory-opinions/):

  * 2010-2026: PDFs. Seven of the 2011-2016 PDFs are SCANS with no text
    layer — recorded as text_layer=false and queued for OCR, not failed.
  * 1996-2009: HTML pages, body in <div class="primary-content">.

The index's own <li> list is the ground-truth count. Subjects come from the
index parentheticals ("(Contribution limits for trade associations)").

Ids: 'csc_ao:07-01', amendments 'csc_ao:98-05-amendment'.
Citations: HAR triples masked first, then the shared HRS extractor.
"""
import argparse
import hashlib
import html as htmlmod
import json
import os
import re
import sys
from datetime import date

import pdfplumber

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hrs_lib import GRAPH, VAULT, extract_citations, normalize_dashes
from har_lib import fetch

INDEX = "https://ags.hawaii.gov/campaign/legal-resources/advisory-opinions/"
RAW = os.path.join(VAULT, "raw", "opinions")
PDF_DIR = os.path.join(RAW, "_pdf")

_ANYHARSEC = r"\d+[A-Z]?-\d+(?:\.\d+)?-\d+(?:\.\d+)?"

LI_ENTRY = re.compile(
    r'<li>\s*<a[^>]*href="(?P<url>https://ags\.hawaii\.gov/campaign/[^"]+)"[^>]*>'
    r'\s*Advisory Opinion\s+(?P<num>\d{2}-\d{2})(?P<amend>,\s*Amendment)?\s*</a>'
    r'\s*(?:\((?P<subject>[^)]*)\))?', re.I)
PRIMARY = re.compile(r'<div class="primary-content">(.*?)<div id="sidebar', re.S)
DATE_RE = re.compile(r"(January|February|March|April|May|June|July|August|"
                     r"September|October|November|December)\s+\d{1,2},\s+\d{4}")


def strip_tags(seg):
    seg = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", seg, flags=re.S | re.I)
    seg = re.sub(r"<[^>]+>", " ", seg)
    return " ".join(htmlmod.unescape(seg).split())


def cites_for(sid, flat, edges):
    masked = flat
    for m in list(re.finditer(_ANYHARSEC, masked)):
        edges.append({"src": sid, "target": f"har:{m.group(0)}",
                      "kind": "har_section", "raw": m.group(0)})
        masked = masked[:m.start()] + " " * (m.end() - m.start()) + masked[m.end():]
    for m in list(re.finditer(r"\bchapters?\s+(\d+[A-Z]?-\d+(?:\.\d+)?)\b",
                              masked, re.I)):
        edges.append({"src": sid, "target": f"har:ch:{m.group(1)}",
                      "kind": "har_chapter", "raw": m.group(0)})
        masked = masked[:m.start()] + " " * (m.end() - m.start()) + masked[m.end():]
    for e in extract_citations(masked):
        edges.append({"src": sid, "target": e["target"], "kind": e["kind"],
                      "raw": e["raw"]})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    os.makedirs(PDF_DIR, exist_ok=True)

    idx, _ = fetch(INDEX)
    entries = []
    seen = set()
    for m in LI_ENTRY.finditer(idx):
        num = m.group("num")
        oid = num + ("-amendment" if m.group("amend") else "")
        if oid in seen:
            continue
        seen.add(oid)
        entries.append({"oid": oid, "num": num, "url": m.group("url"),
                        "subject": (m.group("subject") or "").strip(),
                        "form": "pdf" if m.group("url").endswith(".pdf") else "html"})
    print(f"index lists {len(entries)} opinions "
          f"({sum(1 for e in entries if e['form']=='pdf')} pdf, "
          f"{sum(1 for e in entries if e['form']=='html')} html)")

    opinions, edges, problems = [], [], []
    failed = 0
    for ent in entries:
        sid = f"csc_ao:{ent['oid']}"
        try:
            process(ent, sid, opinions, edges, problems, args)
        except Exception as e:                              # noqa: BLE001
            # the index links pages that 404 (AO 06-02) — a source defect,
            # recorded and skipped, never a crash
            failed += 1
            problems.append({"kind": "fetch_failed", "id": sid,
                             "url": ent["url"], "error": str(e)[:160]})
    print(f"fetch failures: {failed}")
    _finish(entries, opinions, edges, problems)


def process(ent, sid, opinions, edges, problems, args):
        if ent["form"] == "pdf":
            pdf_path = os.path.join(PDF_DIR, f"AO{ent['oid']}.pdf")
            if args.refresh or not os.path.exists(pdf_path):
                data, _ = fetch(ent["url"], binary=True)
                open(pdf_path, "wb").write(data)
            sha = hashlib.sha256(open(pdf_path, "rb").read()).hexdigest()
            with pdfplumber.open(pdf_path) as pdf:
                pages = [(p.extract_text() or "") for p in pdf.pages]
            body = "\f".join(pages)
            text_layer = len(body.strip()) >= 500
            npages = len(pages)
        else:
            cache = os.path.join(RAW, f"AO{ent['oid']}.html")
            if args.refresh or not os.path.exists(cache):
                page, _ = fetch(ent["url"])
                open(cache, "w", encoding="utf-8", newline="\n").write(page)
            page = open(cache, encoding="utf-8").read()
            sha = hashlib.sha256(page.encode()).hexdigest()
            m = PRIMARY.search(page)
            if not m:
                problems.append({"kind": "no_primary_content", "id": sid})
                return
            body = strip_tags(m.group(1))
            # drop the repeated page title
            body = re.sub(r"^Advisory Opinion \d{2}-\d{2}(?:, Amendment)?\s*",
                          "", body)
            text_layer = True
            npages = None

        txt_path = os.path.join(RAW, f"AO{ent['oid']}.txt")
        with open(txt_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)

        flat = normalize_dashes(" ".join(body.split()))
        dm = DATE_RE.search(flat)
        opinions.append({
            "id": sid, "number": ent["oid"], "kind": "csc_advisory",
            "form": ent["form"], "text_layer": text_layer,
            "date": dm.group(0) if dm else "",
            "subject": ent["subject"] or flat[:180],
            "body": body if text_layer else "",
            "url": ent["url"], "sha256": sha, "pages": npages,
        })
        if text_layer:
            cites_for(sid, flat, edges)
        else:
            problems.append({"kind": "image_only_pdf_needs_ocr", "id": sid,
                             "url": ent["url"]})


def _finish(entries, opinions, edges, problems):
    n_failed = sum(1 for p in problems if p["kind"] == "fetch_failed")
    if len(opinions) + n_failed != len(entries):
        problems.append({"kind": "count_mismatch",
                         "expected": len(entries),
                         "got": len(opinions) + n_failed})

    out = {"built": date.today().isoformat(), "retrieved": date.today().isoformat(),
           "index_url": INDEX, "opinions": opinions, "edges": edges,
           "problems": problems}
    with open(os.path.join(GRAPH, "csc-aos.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)

    n_img = sum(1 for o in opinions if not o["text_layer"])
    print(f"{len(opinions)} opinions ({n_img} image-only awaiting OCR), "
          f"{len(edges)} citation edges, {len(problems)} problems")
    hard = [p for p in problems if p["kind"] in ("no_primary_content",
                                                 "count_mismatch")]
    for p in hard:
        print("  HARD", p)
    if hard:
        sys.exit(1)


if __name__ == "__main__":
    main()
