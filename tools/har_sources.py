"""Build graph/har-sources.json: where the text of each HAR title actually lives.

There is no central full-text source for HAR.  The rules are federated across
~20 department websites, each with its own layout and its own idea of whether a
chapter is one PDF or twenty.  A harvester therefore needs a per-title map
before it can fetch anything, and that map is what this produces.

TWO INPUTS, DIFFERENT AUTHORITY, DELIBERATELY NOT MERGED BLINDLY
  * graph/har-universe.json - the LRB's own Directory.  AUTHORITATIVE for the
    department name, the chapter list, and the canonical rules URL.  The LRB
    publishes a URL per title; the Lt. Governor's index omits titles 1, 9, 21
    and 22 entirely and is stale where it disagrees.
  * .tmp/recon/title-NN.json - per-department reconnaissance: publication shape,
    document count, bytes.  Useful, and NOT authoritative: a reconnaissance
    agent reports a wrong answer with complete confidence.  Title 21's rules are
    the State Ethics Commission's (per the LRB), not the LRB's or the Auditor's,
    and an agent told to check the latter concluded "no rules exist".  Every
    such disagreement is recorded as a disagreement, and the LRB wins.

    python tools/har_sources.py
"""
import datetime as dt
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from har_lib import GRAPH, TITLES, VAULT

RECON = os.path.join(VAULT, ".tmp", "recon")


def load_recon(path):
    """Recon files were written by agents on Windows, where PowerShell's default
    output encoding is UTF-8 *with a BOM* and json.load rejects it outright.
    Read with utf-8-sig, and fall back to salvaging the first JSON object if the
    agent prefixed prose."""
    raw = open(path, "rb").read().decode("utf-8-sig", errors="replace")
    try:
        return json.loads(raw), None
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.S)
        if m:
            try:
                return json.loads(m.group(0)), "salvaged from surrounding prose"
            except json.JSONDecodeError as e:
                return None, f"unparseable: {e}"
        return None, "no JSON object found"


def main():
    uni = json.load(open(os.path.join(GRAPH, "har-universe.json"),
                         encoding="utf-8"))
    stamp = dt.date.today().isoformat()
    out, disagreements, gaps = {}, [], []

    for t in sorted(TITLES):
        u = uni["titles"][str(t)]
        rec = {
            "title": t,
            "department": u["department"],
            "url": u["url"] or None,
            "url_authority": "LRB 2025 Directory",
            "chapters": u["chapter_count"],
            "live_chapters": u["live_count"],
            "no_rules_per_lrb": u["no_rules"],
            "shape": None,
            "render": None,
            "doc_count": None,
            "total_bytes": None,
            "bytes_complete": None,
            "recon_status": "not run",
            "notes": "",
        }
        path = os.path.join(RECON, f"title-{t:02d}.json")
        if os.path.exists(path):
            r, err = load_recon(path)
            if r is None:
                rec["recon_status"] = f"failed ({err})"
            else:
                rec["recon_status"] = "ok" + (f" ({err})" if err else "")
                rec["shape"] = r.get("shape")
                rec["render"] = r.get("render")
                links = r.get("links") or []
                rec["doc_count"] = r.get("pdf_count", len(links))
                sizes = [l.get("bytes") for l in links
                         if isinstance(l, dict) and isinstance(l.get("bytes"), int)]
                rec["total_bytes"] = r.get("total_bytes") or (sum(sizes) or None)
                rec["bytes_complete"] = (bool(links) and len(sizes) == len(links))
                rec["notes"] = (r.get("notes") or "")[:600]
                ru = (r.get("url") or "").rstrip("/")
                lu = (rec["url"] or "").rstrip("/")
                if ru and lu and ru != lu:
                    disagreements.append({"title": t, "lrb": lu, "recon": ru,
                                          "resolution": "LRB URL kept"})
                    rec["recon_url"] = ru
                if not ru and lu:
                    disagreements.append({
                        "title": t, "lrb": lu, "recon": None,
                        "resolution": "LRB URL kept; recon found nothing, which "
                                      "is a claim to re-check, not a fact"})
        if rec["recon_status"] != "ok" or rec["doc_count"] in (None, 0):
            if not rec["no_rules_per_lrb"] and rec["live_chapters"]:
                gaps.append({"title": t, "department": rec["department"],
                             "live_chapters": rec["live_chapters"],
                             "why": rec["recon_status"] if rec["recon_status"] != "ok"
                                    else "recon found no documents"})
        out[str(t)] = rec

    # ---- size estimate ---------------------------------------------------
    # Extrapolating a mean bytes-per-chapter is misleading here: title 18
    # (Taxation, scanned) runs ~7 MB per live chapter while title 13 (DLNR) runs
    # ~0.07 MB. So report the measured floor and a median-based projection, and
    # say plainly how much of the corpus each rests on.
    measured = {t: r for t, r in out.items()
                if r["total_bytes"] and r["live_chapters"]}
    per_chap = sorted(r["total_bytes"] / r["live_chapters"]
                      for r in measured.values())
    median = (per_chap[len(per_chap) // 2] if per_chap else 0)
    covered_live = sum(r["live_chapters"] for r in measured.values())
    all_live = sum(r["live_chapters"] for r in out.values())
    measured_bytes = sum(r["total_bytes"] for r in measured.values())
    unmeasured_live = all_live - covered_live

    est = {
        "titles_measured": len(measured),
        "titles_total": len(out),
        "live_chapters_measured": covered_live,
        "live_chapters_total": all_live,
        "measured_bytes": measured_bytes,
        "measured_docs": sum(r["doc_count"] or 0 for r in out.values()),
        "median_bytes_per_live_chapter": round(median),
        "projected_total_bytes": round(measured_bytes + median * unmeasured_live),
        "spread_warning": (
            "bytes per live chapter ranges from "
            f"{per_chap[0]/1e6:.2f} MB to {per_chap[-1]/1e6:.2f} MB across "
            "measured titles, so the projection is an order-of-magnitude "
            "figure, not a budget"),
        "extracted_text_expectation": (
            "Only extracted text and a SHA-256 per source PDF get committed, so "
            "the tracked cost is roughly 3-8% of the PDF bytes. The PDF bytes "
            "are the download cost, not the repository cost."),
    }

    payload = {"built": stamp,
               "size_estimate": est,
               "url_disagreements": disagreements,
               "recon_gaps": gaps,
               "titles": out}
    with open(os.path.join(GRAPH, "har-sources.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)

    print(f"{'T':>2} {'department':32} {'live':>4} {'shape':20} {'docs':>5} "
          f"{'MB':>7} {'recon':>8}")
    for t in sorted(TITLES):
        r = out[str(t)]
        mb = (r["total_bytes"] or 0) / 1e6
        print(f"{t:>2} {r['department'][:32]:32} {r['live_chapters']:>4} "
              f"{str(r['shape'] or '-')[:20]:20} {str(r['doc_count'] or '-'):>5} "
              f"{mb:>7.1f} {r['recon_status'][:8]:>8}")
    print(f"\nmeasured: {est['measured_docs']} docs, "
          f"{est['measured_bytes']/1e6:.0f} MB across {est['titles_measured']} "
          f"titles / {est['live_chapters_measured']} of {est['live_chapters_total']} "
          f"live chapters")
    print(f"median {est['median_bytes_per_live_chapter']/1e6:.2f} MB per live "
          f"chapter -> projected whole-HAR download "
          f"~{est['projected_total_bytes']/1e6:.0f} MB")
    print(f"  {est['spread_warning']}")
    print(f"\nurl disagreements {len(disagreements)}   recon gaps {len(gaps)}")
    for g in gaps:
        print(f"   T{g['title']:<3} {g['department'][:38]:38} "
              f"{g['live_chapters']:>4} live  {g['why'][:38]}")


if __name__ == "__main__":
    main()
