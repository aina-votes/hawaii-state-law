"""Harvest HAR chapter PDFs across all 24 title sites into raw/har/_pdf/.

    python tools/har_harvest.py [--titles 2,5,7] [--dry-run]

Work-list assembly, three sources, in trust order:

  1. .tmp/recon/title-NN.json link lists — the 2026-07-25 reconnaissance that
     built graph/har-sources.json. Used as recorded EXCEPT where recon is known
     truncated or unrecursed (below).
  2. Live re-enumeration, needed where recon under-recorded:
       * title 11 (Health): recon saved a 10-link sample of ~161. The index
         page is re-fetched and every PDF href taken.
       * title 12 (Labor): six divisional find-a-law subpages were never
         recursed. Each is fetched and its PDF links taken.
  3. EXTRAS — documents outside the LRB-directory recon entirely:
       * HAR 3-170 (Elections Commission) and 3-177 (Office of Elections),
         published on elections.hawaii.gov, not on the DAGS/AGS pages.

Downloads are polite: sequential, paused, resumable (a file already present
whose bytes start with %PDF and whose size matches the manifest is skipped).
Every download is verified to be a PDF by magic number — an agency error page
saved as .pdf silently corrupts a harvest (schema rule 0's class of failure).

Provenance: raw/har/_pdf/_downloads.json — url, source page, title, chapter
hint (from recon/link text/filename; VERIFIED AT PARSE TIME against the PDF's
own printed chapter number, never trusted), bytes, SHA-256, retrieval date,
status. The PDFs themselves stay gitignored; the hash is the provenance.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from har_lib import RAW_PDF, UA, VAULT, fetch

RECON = os.path.join(VAULT, ".tmp", "recon")
MANIFEST = os.path.join(RAW_PDF, "_downloads.json")

# recon under-recorded these; re-enumerate live
LIVE_ENUM = {
    8: ["https://boe.hawaii.gov/administrative-rules/"],   # recon names stale: 21 of 55 were 404s
    11: ["https://health.hawaii.gov/opppd/department-of-health-administrative-rules-title-11/"],
    12: ["https://labor.hawaii.gov/ui/find-a-law/",
         "https://labor.hawaii.gov/dcd/find-a-law/",
         "https://labor.hawaii.gov/wsd/find-a-law/",
         "https://labor.hawaii.gov/hlrb/find-a-law/",
         "https://labor.hawaii.gov/hcrc/find-a-law/",
         "https://labor.hawaii.gov/lirab/find-a-law/"],
}

# documents that exist outside the LRB-directory recon
EXTRAS = [
    {"title": 3, "hint": "3-170",
     "url": "https://elections.hawaii.gov/wp-content/uploads/HAR-Elections-Commission-1.pdf",
     "source_page": "https://elections.hawaii.gov/resources/election-laws/",
     "text": "HAR Elections Commission"},
    {"title": 3, "hint": "3-177",
     "url": "https://elections.hawaii.gov/wp-content/uploads/HAR-Office-of-Elections-1.pdf",
     "source_page": "https://elections.hawaii.gov/resources/election-laws/",
     "text": "HAR Office of Elections"},
]

PDF_HREF = re.compile(r'href="([^"]+\.pdf)"', re.I)


def norm_hint(raw, title):
    """Normalise a chapter hint to 'T-C' form, or None. Never trusted as
    identity — the parser reads the chapter number out of the PDF itself."""
    if not raw:
        return None
    s = str(raw).strip().upper().replace("HAR", "").strip("-— ").strip()
    m = re.match(r"^(\d+)-(\d+(?:\.\d+)?)$", s)
    if m:
        return f"{int(m.group(1))}-{m.group(2)}"
    m = re.match(r"^(\d+(?:\.\d+)?)$", s)
    if m:
        return f"{title}-{m.group(1)}"
    return None


def hint_from_name(href, text, title):
    """Derive a chapter hint from link text or filename patterns actually
    observed on the agency sites: 'Chapter 1: ...', 'ch28.pdf', '11-100.1.pdf',
    '8-19...pdf'."""
    for src in (text or "", os.path.basename(urllib.parse.urlparse(href).path)):
        m = re.search(r"\b(\d+)-(\d+(?:\.\d+)?)\b", src)
        if m and int(m.group(1)) == title:
            return f"{title}-{m.group(2)}"
        m = re.search(r"(?i)\bchapter[-\s_]*0*(\d+(?:\.\d+)?)\b", src)
        if m:
            return f"{title}-{m.group(1)}"
        m = re.search(r"(?i)\bch[-_\s]*0*(\d+(?:\.\d+)?)\.pdf$", src)
        if m:
            return f"{title}-{m.group(1)}"
    return None


def recon_links(title):
    path = os.path.join(RECON, f"title-{title:02d}.json")
    if not os.path.exists(path):
        return []
    raw = open(path, "rb").read().decode("utf-8-sig", errors="replace")
    try:
        d = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.S)
        d = json.loads(m.group(0)) if m else {}
    out = []
    for l in d.get("links") or []:
        href = l.get("href") or ""
        ct = (l.get("content_type") or "").lower()
        if not href or ("pdf" not in ct and not href.lower().endswith(".pdf")):
            continue
        out.append({"title": title, "url": href,
                    "source_page": d.get("url"),
                    "text": l.get("text"),
                    "hint": norm_hint(l.get("har_chapter"), title)
                            or hint_from_name(href, l.get("text"), title),
                    "bytes_recon": l.get("bytes")})
    return out


def live_links(title, pages):
    out = []
    for page in pages:
        try:
            html, final = fetch(page)
        except Exception as e:                              # noqa: BLE001
            print(f"  ENUM FAIL {page}: {e}", file=sys.stderr)
            continue
        for href in PDF_HREF.findall(html):
            href = urllib.parse.urljoin(final, href)
            out.append({"title": title, "url": href, "source_page": page,
                        "text": None,
                        "hint": hint_from_name(href, None, title)})
        time.sleep(0.4)
    return out


def curl_fetch(url, dest):
    r = subprocess.run(["curl", "-sSL", "--fail", "-A", UA, "-o", dest, url],
                       capture_output=True, timeout=300)
    return r.returncode == 0


def polite_fetch(url):
    """har_lib.fetch with 429-aware backoff: a host that says Too Many
    Requests gets a long sleep and another chance, not a hammering."""
    for attempt in range(4):
        try:
            return fetch(url, binary=True)
        except Exception as e:                              # noqa: BLE001
            if "429" in str(e) and attempt < 3:
                time.sleep(20 * (attempt + 1))
                continue
            raise


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--titles", help="comma list, default all")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    want = ([int(x) for x in args.titles.split(",")] if args.titles
            else list(range(1, 25)))

    manifest = {}
    if os.path.exists(MANIFEST):
        manifest = json.load(open(MANIFEST, encoding="utf-8"))

    # ---- assemble work-list ------------------------------------------------
    work, seen = [], set()
    for t in want:
        links = ([] if t in LIVE_ENUM else recon_links(t))
        if t in LIVE_ENUM:
            print(f"title {t}: live enumeration...")
            links = live_links(t, LIVE_ENUM[t])
        for l in links:
            if l["url"] not in seen:
                seen.add(l["url"])
                work.append(l)
    for x in EXTRAS:
        if x["title"] in want and x["url"] not in seen:
            seen.add(x["url"])
            work.append(dict(x))
    print(f"work-list: {len(work)} documents across titles {want[0]}-{want[-1]}")
    if args.dry_run:
        for w in work:
            print(f"  t{w['title']:02d} {w.get('hint') or '?':>10} {w['url']}")
        return

    # ---- download ----------------------------------------------------------
    today = time.strftime("%Y-%m-%d")
    ok = fail = skip = 0
    for i, w in enumerate(work):
        tdir = os.path.join(RAW_PDF, f"t{w['title']:02d}")
        os.makedirs(tdir, exist_ok=True)
        base = os.path.basename(urllib.parse.urlparse(w["url"]).path) or "doc.pdf"
        dest = os.path.join(tdir, base)
        key = f"t{w['title']:02d}/{base}"
        # basename collision with a DIFFERENT url -> disambiguate by url hash
        if key in manifest and manifest[key]["url"] != w["url"]:
            h8 = hashlib.sha256(w["url"].encode()).hexdigest()[:8]
            base = re.sub(r"\.pdf$", f"-{h8}.pdf", base, flags=re.I)
            dest = os.path.join(tdir, base)
            key = f"t{w['title']:02d}/{base}"

        prior = manifest.get(key)
        if (prior and prior.get("status") == "ok" and os.path.exists(dest)
                and os.path.getsize(dest) == prior.get("bytes")):
            skip += 1
            continue

        err = None
        try:
            data, _ = polite_fetch(w["url"])
            with open(dest, "wb") as fh:
                fh.write(data)
        except Exception as e:                              # noqa: BLE001
            err = str(e)
            if not curl_fetch(w["url"], dest):
                manifest[key] = {"url": w["url"], "title": w["title"],
                                 "hint": w.get("hint"), "text": w.get("text"),
                                 "source_page": w.get("source_page"),
                                 "status": "fetch_failed", "error": err,
                                 "retrieved": today}
                fail += 1
                print(f"[{i+1}/{len(work)}] FAIL {key}: {err}", file=sys.stderr)
                continue

        with open(dest, "rb") as fh:
            magic = fh.read(5)
        if magic != b"%PDF-":
            manifest[key] = {"url": w["url"], "title": w["title"],
                             "hint": w.get("hint"), "text": w.get("text"),
                             "source_page": w.get("source_page"),
                             "status": "not_a_pdf",
                             "magic": magic.decode("latin1"),
                             "bytes": os.path.getsize(dest), "retrieved": today}
            fail += 1
            print(f"[{i+1}/{len(work)}] NOT-PDF {key}", file=sys.stderr)
            continue

        manifest[key] = {"url": w["url"], "title": w["title"],
                         "hint": w.get("hint"), "text": w.get("text"),
                         "source_page": w.get("source_page"), "status": "ok",
                         "bytes": os.path.getsize(dest),
                         "sha256": sha256_file(dest), "retrieved": today}
        ok += 1
        if (i + 1) % 25 == 0 or i + 1 == len(work):
            print(f"[{i+1}/{len(work)}] ok={ok} skip={skip} fail={fail}")
            with open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(manifest, fh, indent=1, ensure_ascii=False)
        time.sleep(0.7)

    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(f"DONE ok={ok} skip={skip} fail={fail} manifest={len(manifest)}")


if __name__ == "__main__":
    main()
