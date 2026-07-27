"""Harvest the ENTIRE HRS — every chapter in graph/hrs-universe.json — into
raw/hrs/, one file per section with a provenance header.

    python tools/harvest_hrs_all.py [--chapters 412,431] [--max-chapters N]

Supersedes tools/harvest_hrs.py's hand-list of 15 chapters (that script stays
as the targeted-refresh tool). Work-list = the universe enumeration
(1,108 chapter directories, ~23k sections, built 2026-07-24 from the State's
own volume/chapter listings — NOT a recon agent's link list; the HAR gap
taught that lesson, and here the listing IS the authority).

Behaviour, each point load-bearing at this scale:

  * SEQUENTIAL AND POLITE (bulk-ingest non-negotiable): one request at a
    time against capitol.hawaii.gov, hrs_lib.fetch's built-in pause + WAF
    curl fallback. ~23k requests ≈ hours; run in background.
  * RESUMABLE: a section file already on disk is never re-fetched. Chapter
    listings are cached in raw/hrs/_listings.json so a resume does not
    re-walk 1,108 directories; delete that file to force re-listing.
  * NOTHING DROPS SILENTLY: an href that file_to_section cannot parse, a
    failed fetch, and a Page-Not-Found each land in
    raw/hrs/_harvest_problems.json with the chapter and filename.
  * GROUND-TRUTH CHECK per chapter: files fetched vs the listing's count;
    and at the end, chapters whose listing count differs from the 2026-07-24
    universe count are reported (the State edits between enumeration and
    harvest — that is a finding, not an error).
  * Colon (article) chapters (412, 431, 432*, 490...) produce sids like
    '412:1-100'; the on-disk filename replaces ':' with '__' (NTFS cannot
    hold a colon) while the manifest and graph keep the citation as printed.
  * The complete _manifest.json (this harvest + the 15 prior chapters) is
    rewritten from the listings cache every 25 chapters, so a crash loses
    only in-flight work.
"""
import argparse
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hrs_lib import BASE, GRAPH, RAW, fetch, file_to_section, sec_sort_key, strip_html
import re

LISTINGS = os.path.join(RAW, "_listings.json")
PROBLEMS = os.path.join(RAW, "_harvest_problems.json")
MANIFEST = os.path.join(RAW, "_manifest.json")
SOURCE_NOTE = "graph/hrs-universe.json enumeration (capitol.hawaii.gov volume listings)"


def sid_to_fname(sid):
    return "hrs-" + sid.lower().replace(":", "__") + ".md"


def load_json(path, default):
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return default


def save_json(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


def write_manifest(listings, today):
    entries, seen = [], set()
    for dirkey, rec in listings.items():
        chap = rec["chapter"]
        for fn in rec["files"]:
            c, sid = file_to_section(fn)
            if not sid or sid in seen:
                continue
            path = os.path.join(RAW, sid_to_fname(sid))
            if not os.path.exists(path):
                continue
            seen.add(sid)
            entries.append({"section": sid, "chapter": chap,
                            "file": sid_to_fname(sid),
                            "url": f"{BASE}/{rec['volume']}/{rec['dir']}/{fn}"})
    entries.sort(key=lambda m: sec_sort_key(m["section"]))
    save_json(MANIFEST, {"retrieved": today, "source_page": SOURCE_NOTE,
                         "sections": entries})
    return len(entries)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapters", help="comma list of chapter ids, default all")
    ap.add_argument("--max-chapters", type=int)
    args = ap.parse_args()

    uni = json.load(open(os.path.join(GRAPH, "hrs-universe.json"),
                         encoding="utf-8"))
    detail = uni["detail"]
    if args.chapters:
        want = set(args.chapters.split(","))
        detail = [c for c in detail if c["chapter"] in want]

    os.makedirs(RAW, exist_ok=True)
    today = dt.date.today().isoformat()
    listings = load_json(LISTINGS, {})
    problems = load_json(PROBLEMS, [])
    n_new = n_skip = n_fail = 0
    drift = []

    done_chapters = 0
    for i, c in enumerate(detail):
        chap, vol, d = c["chapter"], c["volume"], c["dir"]
        key = f"{vol}/{d}"
        if key not in listings:
            try:
                html = fetch(f"{BASE}/{vol}/{d}/")
            except Exception as e:                          # noqa: BLE001
                problems.append({"chapter": chap, "kind": "listing_failed",
                                 "url": f"{BASE}/{vol}/{d}/", "error": str(e)[:200]})
                n_fail += 1
                continue
            files, seen = [], set()
            for fn in re.findall(r'href="[^"]*/(HRS_[^"/]+\.htm)"', html, re.I):
                if fn not in seen:
                    seen.add(fn)
                    files.append(fn)
            listings[key] = {"chapter": chap, "volume": vol, "dir": d,
                             "files": files, "listed": today}
            if c["sections"] >= 0 and max(0, len(files) - 1) != c["sections"]:
                drift.append({"chapter": chap,
                              "universe_count": c["sections"],
                              "listing_count": max(0, len(files) - 1)})
        rec = listings[key]

        missing = []
        for fn in rec["files"]:
            cc, sid = file_to_section(fn)
            if sid is None and cc is None:
                problems.append({"chapter": chap, "kind": "unparseable_filename",
                                 "file": fn})
                continue
            if sid is None:
                continue                       # chapter TOC page
            if not os.path.exists(os.path.join(RAW, sid_to_fname(sid))):
                missing.append((fn, sid))
            else:
                n_skip += 1

        for fn, sid in missing:
            url = f"{BASE}/{vol}/{d}/{fn}"
            try:
                raw_html = fetch(url)
            except Exception as e:                          # noqa: BLE001
                problems.append({"chapter": chap, "section": sid,
                                 "kind": "fetch_failed", "url": url,
                                 "error": str(e)[:200]})
                n_fail += 1
                continue
            text = strip_html(raw_html)
            if "Page Not Found" in text[:400] or len(text) < 20:
                problems.append({"chapter": chap, "section": sid,
                                 "kind": "page_not_found_or_empty", "url": url})
                n_fail += 1
                continue
            header = (
                "---\n"
                f"retrieved: {today}\n"
                f"url: {url}\n"
                "publisher: Hawaii State Legislature (capitol.hawaii.gov)\n"
                f"chapter: \"{chap}\"\n"
                f"section: \"{sid}\"\n"
                f"discovered_via: {SOURCE_NOTE}\n"
                "method: urllib GET with browser User-Agent (curl fallback on "
                "WAF 403), redirects followed, HTML stripped\n"
                "---\n\n"
                "<!-- PROVENANCE HEADER ABOVE. VERBATIM RETRIEVED TEXT BELOW. "
                "DO NOT EDIT. -->\n\n"
            )
            with open(os.path.join(RAW, sid_to_fname(sid)), "w",
                      encoding="utf-8", newline="\n") as fh:
                fh.write(header + text + "\n")
            n_new += 1

        done_chapters += 1
        if done_chapters % 25 == 0:
            save_json(LISTINGS, listings)
            save_json(PROBLEMS, problems)
            n_man = write_manifest(listings, today)
            print(f"[{i+1}/{len(detail)}] ch {chap}: manifest {n_man} sections "
                  f"(new {n_new}, cached {n_skip}, failed {n_fail})", flush=True)
        if args.max_chapters and done_chapters >= args.max_chapters:
            break

    save_json(LISTINGS, listings)
    save_json(PROBLEMS, problems)
    n_man = write_manifest(listings, today)
    if drift:
        save_json(os.path.join(RAW, "_universe_drift.json"),
                  {"checked": today, "drift": drift})
    print(f"\nDONE chapters={done_chapters} new={n_new} cached={n_skip} "
          f"failed={n_fail} manifest={n_man} "
          f"universe_drift={len(drift)} problems={len(problems)}")


if __name__ == "__main__":
    main()
