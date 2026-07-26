"""Harvest every section of the chapters in hrs_lib.CHAPTERS into raw/hrs/,
one file per section, each with a provenance header. The list is the 14 HRS
chapters from the Office of Elections "Election Laws" page plus citation-
frontier ingests (marked in hrs_lib).

NOTE: --only rebuilds _manifest.json from just the processed chapter; follow
any --only run with a full (cached, cheap) run to restore the complete
manifest.

raw/ is immutable under the vault schema.  This script only creates files that
do not already exist unless --refresh is passed; it never edits one in place.

    python tools/harvest_hrs.py            # fetch what is missing
    python tools/harvest_hrs.py --refresh  # re-fetch everything (statute amended)
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hrs_lib import (BASE, CHAPTERS, RAW, fetch, file_to_section, sec_sort_key,
                     split_section, strip_html)

SOURCE_PAGE = "https://elections.hawaii.gov/resources/election-laws/"


def listing(vol, chdir):
    """The chapter directory is served as an IIS listing; it is the authoritative
    manifest of which sections exist."""
    url = f"{BASE}/{vol}/HRS{chdir}/"
    html_ = fetch(url)
    files = re.findall(r'href="[^"]*/(HRS_[^"/]+\.htm)"', html_, re.I)
    seen, out = set(), []
    for f in files:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return url, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--only", help="restrict to one chapter, e.g. 11")
    args = ap.parse_args()

    os.makedirs(RAW, exist_ok=True)
    today = dt.date.today().isoformat()
    manifest, n_new, n_skip, n_fail = [], 0, 0, 0

    for chap, vol, chdir, title in CHAPTERS:
        if args.only and chap != args.only:
            continue
        try:
            dir_url, files = listing(vol, chdir)
        except Exception as e:  # noqa: BLE001
            print(f"  !! chapter {chap} listing failed: {e}")
            n_fail += 1
            continue

        secs = []
        for fn in files:
            c, sid = file_to_section(fn)
            secs.append((fn, c, sid))

        print(f"Ch {chap:4s} {title[:44]:46s} {len(secs):3d} files")

        for fn, c, sid in secs:
            url = f"{BASE}/{vol}/HRS{chdir}/{fn}"
            name = f"hrs-{sid.lower()}.md" if sid else f"hrs-ch{chap.lower()}-toc.md"
            path = os.path.join(RAW, name)

            if os.path.exists(path) and not args.refresh:
                n_skip += 1
                manifest.append({"section": sid, "chapter": chap, "file": name, "url": url})
                continue
            try:
                raw_html = fetch(url)
            except Exception as e:  # noqa: BLE001
                print(f"    !! {sid or chap+' TOC'}: {e}")
                n_fail += 1
                continue

            text = strip_html(raw_html)
            if "Page Not Found" in text[:400] or len(text) < 20:
                print(f"    !! {sid or chap+' TOC'}: page not found / empty")
                n_fail += 1
                continue

            # Provenance only. Catchline, part and citation data are DERIVED and
            # live in graph/, never in an immutable raw header - otherwise a
            # parser fix silently requires re-fetching the whole corpus.
            header = (
                "---\n"
                f"retrieved: {today}\n"
                f"url: {url}\n"
                "publisher: Hawaii State Legislature (capitol.hawaii.gov)\n"
                f"chapter: \"{chap}\"\n"
                + (f"section: \"{sid}\"\n" if sid else "kind: chapter-toc\n")
                + f"discovered_via: {SOURCE_PAGE}\n"
                "method: urllib GET with browser User-Agent, redirects followed, HTML stripped\n"
                "---\n\n"
                "<!-- PROVENANCE HEADER ABOVE. VERBATIM RETRIEVED TEXT BELOW. DO NOT EDIT. -->\n\n"
            )
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(header + text + "\n")
            n_new += 1
            manifest.append({"section": sid, "chapter": chap, "file": name, "url": url})

    manifest = [m for m in manifest if m["section"]]
    manifest.sort(key=lambda m: sec_sort_key(m["section"]))
    with open(os.path.join(RAW, "_manifest.json"), "w", encoding="utf-8") as fh:
        json.dump({"retrieved": today, "source_page": SOURCE_PAGE,
                   "sections": manifest}, fh, indent=1)

    print(f"\nfetched {n_new}  cached {n_skip}  failed {n_fail}  "
          f"sections in manifest {len(manifest)}")


if __name__ == "__main__":
    main()
