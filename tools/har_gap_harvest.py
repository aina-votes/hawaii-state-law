"""Gap-directed HAR harvest: fetch the live chapters the first pass missed.

    python tools/har_gap_harvest.py [--titles 13,3]

THE INVERSION THAT FIXES THE 2026-07-26 MISS: the first harvest's work-list
was "what the recon-walked pages linked", and 322 live chapters never entered
it. Here the work-list is the TARGET LIST — graph/har-gap-chapters.json,
derived from the LRB universe — and discovery serves it: for each title with
gaps, walk the agency's rules pages live (seed = the LRB title URL + the
recon subpages), one level of same-.gov rules-ish links deep, collect every
PDF link, hint-map to chapters, and download the ones on the target list.
A target chapter no walked page links is recorded UNFOUND, per title, with
the pages searched — absence becomes a fact, not a silence.

Discovery inventory (every PDF link seen, hinted or not) is saved to
raw/har/_gap_discovery.json for audit. Downloads append to the SAME
_downloads.json manifest as the first pass (field `pass: gap`), so
har_extract_all / har_parse_all / db_build run unchanged.

Polite per host: sequential, paused, resumable, 429 backoff. Runs safely in
parallel with the capitol.hawaii.gov HRS harvest — no shared host.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from har_lib import GRAPH, RAW_PDF, fetch
from har_harvest import PDF_HREF, curl_fetch, hint_from_name, norm_hint, polite_fetch

MANIFEST = os.path.join(RAW_PDF, "_downloads.json")
DISCOVERY = os.path.join(RAW_PDF, "_gap_discovery.json")

SUBPAGE_HREF = re.compile(r'href="([^"#]+)"', re.I)
RULESISH = re.compile(r"(?i)rule|admin|chapter|\bhar\b|statute|law")
# titles whose gaps live on multi-board sites: extra seeds beyond the LRB URL
EXTRA_SEEDS = {
    3: ["https://spo.hawaii.gov/references/procurement-rules/",
        "https://ags.hawaii.gov/administrative-rules/"],
}


def load_recon_subpages(title):
    path = os.path.join(os.path.dirname(GRAPH), ".tmp", "recon",
                        f"title-{title:02d}.json")
    if not os.path.exists(path):
        return []
    raw = open(path, "rb").read().decode("utf-8-sig", errors="replace")
    try:
        d = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.S)
        d = json.loads(m.group(0)) if m else {}
    out = []
    for s in d.get("subpages") or []:
        out.append(s if isinstance(s, str) else s.get("url"))
    return [s for s in out if s], d.get("url")


def discover_title(title, seeds, inventory):
    """Walk seeds + one level of rules-ish same-.gov links; collect PDF links."""
    visited, queue, pdfs = set(), [(s, 0) for s in seeds if s], []
    while queue and len(visited) < 40:
        page, depth = queue.pop(0)
        if page in visited:
            continue
        visited.add(page)
        try:
            html, final = fetch(page)
        except Exception as e:                              # noqa: BLE001
            inventory.setdefault("page_failures", []).append(
                {"title": title, "page": page, "error": str(e)[:150]})
            continue
        time.sleep(0.5)
        for href in PDF_HREF.findall(html):
            url = urllib.parse.urljoin(final, href)
            pdfs.append({"url": url, "found_on": page,
                         "hint": hint_from_name(url, None, title)})
        if depth == 0:
            base_host = urllib.parse.urlparse(final).netloc
            for href in SUBPAGE_HREF.findall(html):
                url = urllib.parse.urljoin(final, href)
                p = urllib.parse.urlparse(url)
                if (p.scheme in ("http", "https")
                        and (p.netloc == base_host
                             or p.netloc.endswith(".hawaii.gov"))
                        and not url.lower().endswith(
                            (".pdf", ".jpg", ".png", ".doc", ".docx", ".zip"))
                        and RULESISH.search(url)
                        and url not in visited):
                    queue.append((url, 1))
    inventory.setdefault("pages_walked", {})[str(title)] = sorted(visited)
    return pdfs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--titles", help="comma list, default all titles with gaps")
    args = ap.parse_args()

    gaps = json.load(open(os.path.join(GRAPH, "har-gap-chapters.json"),
                          encoding="utf-8"))["chapters"]
    by_title = {}
    for ch in gaps:
        by_title.setdefault(int(ch.split("-")[0]), set()).add(ch)
    want = ([int(x) for x in args.titles.split(",")] if args.titles
            else sorted(by_title))

    src = json.load(open(os.path.join(GRAPH, "har-sources.json"),
                         encoding="utf-8"))["titles"]
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    have_urls = {v["url"] for v in manifest.values()}
    inventory = {"run": time.strftime("%Y-%m-%d"), "targets": len(gaps)}
    today = time.strftime("%Y-%m-%d")

    found_total, unfound = 0, {}
    for t in want:
        targets = by_title.get(t, set())
        if not targets:
            continue
        subpages, recon_url = load_recon_subpages(t)
        seeds = [src.get(str(t), {}).get("url"), recon_url] + subpages \
            + EXTRA_SEEDS.get(t, [])
        seeds = list(dict.fromkeys(s for s in seeds if s))
        print(f"title {t}: {len(targets)} target chapters, "
              f"{len(seeds)} seed pages", flush=True)
        pdfs = discover_title(t, seeds, inventory)
        inventory.setdefault("pdf_links", {})[str(t)] = pdfs

        matched = {}
        for l in pdfs:
            h = norm_hint(l["hint"], t)
            if h in targets and h not in matched:
                matched[h] = l
        print(f"  discovered {len(pdfs)} pdf links; matched "
              f"{len(matched)}/{len(targets)} targets", flush=True)

        for ch, l in sorted(matched.items()):
            if l["url"] in have_urls:
                continue
            base = os.path.basename(urllib.parse.urlparse(l["url"]).path) or "doc.pdf"
            key = f"t{t:02d}/{base}"
            if key in manifest and manifest[key].get("url") != l["url"]:
                h8 = hashlib.sha256(l["url"].encode()).hexdigest()[:8]
                base = re.sub(r"\.pdf$", f"-{h8}.pdf", base, flags=re.I)
                key = f"t{t:02d}/{base}"
            dest = os.path.join(RAW_PDF, f"t{t:02d}", base)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            entry = {"url": l["url"], "title": t, "hint": ch,
                     "source_page": l["found_on"], "pass": "gap",
                     "retrieved": today}
            try:
                data, _ = polite_fetch(l["url"])
                with open(dest, "wb") as fh:
                    fh.write(data)
            except Exception as e:                          # noqa: BLE001
                if not curl_fetch(l["url"], dest):
                    entry.update({"status": "fetch_failed",
                                  "error": str(e)[:150]})
                    manifest[key] = entry
                    continue
            with open(dest, "rb") as fh:
                magic = fh.read(5)
            if magic != b"%PDF-":
                entry.update({"status": "not_a_pdf",
                              "bytes": os.path.getsize(dest)})
            else:
                entry.update({"status": "ok",
                              "bytes": os.path.getsize(dest),
                              "sha256": hashlib.sha256(
                                  open(dest, "rb").read()).hexdigest()})
                found_total += 1
            manifest[key] = entry
            have_urls.add(l["url"])
            time.sleep(0.7)

        miss = sorted(targets - set(matched))
        if miss:
            unfound[str(t)] = miss
        with open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(manifest, fh, indent=1, ensure_ascii=False)

    inventory["unfound_by_title"] = unfound
    inventory["downloaded"] = found_total
    with open(DISCOVERY, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(inventory, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    n_unfound = sum(len(v) for v in unfound.values())
    print(f"\nDONE downloaded={found_total} unfound={n_unfound} "
          f"(inventory: raw/har/_pdf/_gap_discovery.json)")


if __name__ == "__main__":
    main()
