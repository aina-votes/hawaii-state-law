"""Extract verbatim text from every harvested HAR PDF, in parallel.

    python tools/har_extract_all.py [--workers 8]

Reads  raw/har/_pdf/_downloads.json     (tools/har_harvest.py)
Writes raw/har/txt/tNN/<basename>.txt   verbatim pdfplumber extract_text,
                                        one page per formfeed (\\f). NOT
                                        cleaned — running headers, page
                                        numbers, stamps all present, dashes
                                        NOT normalised. Cleaning is a
                                        parse-time concern (har_parse_all.py)
                                        so a parser fix never forces
                                        re-extraction.
       raw/har/txt/_extract.json        per-doc: pages, chars, sha256 of the
                                        source PDF at extraction time, errors.

Idempotent and resumable: a doc whose txt exists and whose recorded PDF hash
matches is skipped. Extraction is CPU-bound and local, so parallelism is
polite — no network involved.
"""
import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from har_lib import RAW_HAR, RAW_PDF, sha256_file

TXT = os.path.join(RAW_HAR, "txt")
MANIFEST = os.path.join(RAW_PDF, "_downloads.json")
EXTRACT = os.path.join(TXT, "_extract.json")


def extract_one(key):
    """Worker: extract one PDF. Returns (key, record)."""
    import pdfplumber                       # import in worker
    pdf_path = os.path.join(RAW_PDF, key.replace("/", os.sep))
    out_path = os.path.join(TXT, key.replace("/", os.sep)[:-4] + ".txt")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    try:
        pages = []
        with pdfplumber.open(pdf_path) as pdf:
            for p in pdf.pages:
                pages.append(p.extract_text() or "")
        text = "\f".join(pages)
        with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        return key, {"status": "ok", "pages": len(pages), "chars": len(text),
                     "sha256_pdf": sha256_file(pdf_path),
                     "empty_pages": sum(1 for p in pages if not p.strip())}
    except Exception as e:                                  # noqa: BLE001
        return key, {"status": "extract_failed", "error": str(e)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    os.makedirs(TXT, exist_ok=True)
    done = {}
    if os.path.exists(EXTRACT):
        done = json.load(open(EXTRACT, encoding="utf-8"))

    todo = []
    for key, m in manifest.items():
        if m.get("status") not in ("ok", "ok_archived"):
            continue
        prior = done.get(key)
        if (prior and prior.get("status") == "ok"
                and prior.get("sha256_pdf") == m.get("sha256")
                and os.path.exists(os.path.join(
                    TXT, key.replace("/", os.sep)[:-4] + ".txt"))):
            continue
        todo.append(key)
    print(f"{len(todo)} to extract ({len(done)} already done)")

    n = 0
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(extract_one, k): k for k in todo}
        for fut in as_completed(futs):
            key, rec = fut.result()
            done[key] = rec
            n += 1
            if rec["status"] != "ok":
                print(f"  FAIL {key}: {rec.get('error')}", file=sys.stderr)
            if n % 25 == 0 or n == len(todo):
                print(f"[{n}/{len(todo)}]")
                with open(EXTRACT, "w", encoding="utf-8", newline="\n") as fh:
                    json.dump(done, fh, indent=1, ensure_ascii=False)

    with open(EXTRACT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(done, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    ok = sum(1 for r in done.values() if r["status"] == "ok")
    bad = [k for k, r in done.items() if r["status"] != "ok"]
    empt = [k for k, r in done.items()
            if r["status"] == "ok" and r.get("chars", 0) < 500]
    print(f"DONE ok={ok} failed={len(bad)} suspiciously_small={len(empt)}")
    for k in bad[:10]:
        print("  failed:", k)
    for k in empt[:10]:
        print("  small (likely scan, no text layer):", k)


if __name__ == "__main__":
    main()
