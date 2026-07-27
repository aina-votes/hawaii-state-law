"""Fetch title 20 (University of Hawaii) HAR PDFs from the Internet Archive.

    python tools/har_t20_wayback.py

`www.hawaii.edu` resets connections to automation (urllib AND curl, TCP-level
— verified twice 2026-07-26), so the primary is unreachable from this
machine. The Wayback Machine holds archived copies of the same PDFs. This is
an ALTERNATE SOURCE, recorded as such: the manifest entry's url becomes the
memento URL, `archived_from` keeps the primary, and status is `ok_archived`
so nothing can mistake an archive fetch for a live agency fetch. The bytes
are still the agency's own PDF as captured; the SHA-256 proves what we read.

Wayback resolves https://web.archive.org/web/2/<url> to the latest capture
via redirects — curl -L follows them (real HTTP redirects, not meta-refresh).
Polite: sequential, 1.5s pause, 28 requests total.
"""
import hashlib
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from har_lib import RAW_PDF, UA

MANIFEST = os.path.join(RAW_PDF, "_downloads.json")


def main():
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    targets = {k: v for k, v in manifest.items()
               if k.startswith("t20/") and v.get("status") != "ok"}
    print(f"{len(targets)} title-20 documents to try via Wayback")
    today = time.strftime("%Y-%m-%d")
    ok = fail = 0
    for key, m in sorted(targets.items()):
        dest = os.path.join(RAW_PDF, key.replace("/", os.sep))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        wb = "https://web.archive.org/web/2/" + m["url"]
        # archive.org rate-limits hard (429 at 1.5s pacing, observed
        # 2026-07-26): slow pace + long backoff, never a retry-hammer
        for attempt in range(3):
            r = subprocess.run(
                ["curl", "-sSL", "--fail", "-A", UA, "--max-time", "120",
                 "-o", dest, "-w", "%{url_effective}", wb],
                capture_output=True, text=True)
            if r.returncode == 0 or "429" not in (r.stderr or ""):
                break
            time.sleep(75 * (attempt + 1))
        magic = b""
        if r.returncode == 0 and os.path.exists(dest):
            with open(dest, "rb") as fh:
                magic = fh.read(5)
        if r.returncode != 0 or magic != b"%PDF-":
            m.update({"status": "wayback_failed",
                      "error": (r.stderr or "not a pdf")[:150],
                      "retried": today})
            fail += 1
            print(f"  FAIL {key}")
        else:
            h = hashlib.sha256(open(dest, "rb").read()).hexdigest()
            m.update({"status": "ok_archived", "archived_from": m["url"],
                      "url": r.stdout.strip(), "bytes": os.path.getsize(dest),
                      "sha256": h, "retrieved": today,
                      "note": "primary TCP-resets automation; archived copy"})
            ok += 1
            print(f"  ok   {key}  ({m['bytes']} bytes)")
        manifest[key] = m
        time.sleep(10)
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(f"DONE ok_archived={ok} failed={fail}")


if __name__ == "__main__":
    main()
