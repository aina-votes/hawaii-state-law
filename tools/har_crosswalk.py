"""Parse the LRB's two cross-layer tables into graph/har-edges.json.

  Table of the HRS Sections Implemented by Administrative Rules
  Table of Hawaii Session Laws Implemented by Administrative Rules

These are the edge direction the HRS citation graph structurally cannot see.
An HRS section page tells you what the statute cites; it never tells you which
agency rules execute it.  Nothing in raw/hrs/ could produce these edges.

WHAT THE EDGES DO AND DO NOT MEAN
The LRB states the limits expressly (2025 ed. p. 1), and they are recorded on
every edge rather than buried in a source page:
  1. Only rules converted to the HAR format and filed with the Lieutenant
     Governor appear.  A rule never converted, or exempt from HRS chapter 91,
     is absent - so absence of an edge is NOT evidence that no rule implements
     a section.
  2. "Whether or not a particular rule section is said to implement a
     particular statutory section is a determination made solely by the
     administrative agency that adopted the rule."  These are the AGENCY'S
     assertions, compiled by the LRB.  Not the revisor's, and not a court's.

THE COMPRESSION THAT WILL SILENTLY LOSE CITATIONS
A rules cell is a compressed list in which only the FIRST entry carries its
title-chapter prefix and every later bare number inherits it:
    13-275-1, 2, 5 to 14   ->  13-275-1, 13-275-2, 13-275-5 ... 13-275-14
    3-177-51, 58           ->  3-177-51, 3-177-58
Reading those bare numbers as chapters, or dropping them, loses most of the
table.  Ranges are expanded only when both endpoints are plain integers.

    python tools/har_crosswalk.py
"""
import datetime as dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from har_lib import (GRAPH, RAW_PDF, sec_sort_key, sha256_file)
from har_directory import (FOOTNOTE_RE, PDF_NAME, PDF_URL, lines_of,
                           render, strip_footnote_mark)

# Four columns: HRS section | rules | HRS section | rules.  Values sit at
# x0 77 / 191 / 320 / 434, with later tokens of a cell running rightward.
COLS = [("key", 70.0, 185.0), ("val", 185.0, 317.0),
        ("key", 317.0, 430.0), ("val", 430.0, 700.0)]

HRS_TABLE_HEAD = "TABLE OF THE HAWAII REVISED STATUTES SECTIONS"
SLH_TABLE_HEAD = "TABLE OF HAWAII SESSION LAWS IMPLEMENTED"

# A full HAR section.  All three parts are messier than they look:
#   chapter may carry a letter or a decimal - 16-89C-35, 18-237D-4, 11-200.1-3
#   section may carry a decimal, a letter, OR A FOURTH PART - the Taxation
#     rules use four: HAR 18-231-9.9-07.
# A too-narrow pattern here does not error, it drops the citation.
HAR_FULL = re.compile(
    r"^(\d{1,2})-(\d+[A-Z]*(?:\.\d+)?)"
    r"-(\d+(?:\.\d+)?[A-Za-z]?(?:-\d+(?:\.\d+)?)?)$")
# Two parts only is a CHAPTER-level reference, e.g. 3-181.1.
HAR_CHAP = re.compile(r"^(\d{1,2})-(\d+[A-Z]*(?:\.\d+)?)$")
BARE = re.compile(r"^(\d+(?:\.\d+)?[A-Za-z]?)$")

# Left-column keys come in several shapes and only the first is an HRS section.
KEY_PATTERNS = [
    # The table pin-cites to SUBSECTION level - "174C-101(a)" - so a pattern
    # that stops at the section number rejects the key, discards its whole rule
    # list, and loses every edge on that row.
    ("hrs_section",
     re.compile(r"^(\d+[A-Z]?-\d+(?:\.\d+)?[A-Za-z]?(?:\([\w.]+\))*)$")),
    # Some HRS chapters number sections article:section rather than
    # chapter-section: HRS 412:2-105 (Code of Financial Institutions),
    # 431:10A-301 (Insurance Code), 490:2-201 (UCC).  These are 93% of the keys
    # this table uses that a chapter-section pattern rejects, and rejecting the
    # key throws away every rule on the row.  Note tools/hrs_lib.py does not
    # recognise this form either - see open-questions.md.
    ("hrs_section_colon",
     re.compile(r"^(\d+[A-Z]?:\d+[A-Z]?-\d+(?:\.\d+)?[A-Za-z]?(?:\([\w.]+\))*)$")),
    # The same citation with the colon lost to extraction ("412-2-105").
    ("hrs_section_colon",
     re.compile(r"^(\d+[A-Z]?-\d+[A-Z]?-\d+(?:\.\d+)?[A-Za-z]?)$")),
    ("hrs_chapter", re.compile(r"^(\d+[A-Z]?)$")),
    ("hhca", re.compile(r"^HHCA(?:\s+(\d+[\w.\-]*))?$")),
    ("hi_const", re.compile(r"^(?:Art\.?\s*([IVXLC]+)\b(.*)|Preamble)$")),
]


def restore_dash(txt):
    """The chapter-section dash is sometimes lost to extraction, leaving
    "206E 4" or "342D6.5".  Restored only where the boundary is unambiguous: a
    letter followed by a digit, or a space.  A purely numeric "157.31" is NOT
    guessed at - it stays a reported problem rather than a fabricated cite."""
    m = re.match(r"^(\d+[A-Z]+)\s*(\d+(?:\.\d+)?[A-Za-z]?)$", txt)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    m = re.match(r"^(\d+)\s+(\d+(?:\.\d+)?[A-Za-z]?)$", txt)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    return txt


# Column headers repeated on every page, and the group headings the table uses
# to separate the statutory series (HRS proper, the Constitution, the Hawaiian
# Homes Commission Act).  Neither is a key; both must be skipped rather than
# reported, or a real problem gets lost in 200 header rows.
SKIP_KEY = re.compile(r"^(HRS\s+Section|Section|Sections?|Administrative\s+Rules"
                      r"|[A-Z]|Page)$")
# Prose: the cover date, the legend, and footnote bodies. Recorded, not errored.
PROSE = re.compile(r"[a-z]{3}")
# "C 15" is HRS *chapter* 15; "15-3.5 [R]" flags a REPEALED HRS section, which
# the LRB marks because rules still claim to implement it.
C_CHAP = re.compile(r"^C\s+(\d+[A-Z]?)$")
# "C 286, pt XVI" - a chapter-and-part key. Recorded at chapter granularity;
# the part is kept in the raw key so the pin cite is not silently coarsened.
C_CHAP_PART = re.compile(r"^C\s+(\d+[A-Z]?),?\s*pt\s+([IVXLC]+)$")
REPEALED_MARK = re.compile(r"\s*\[R\]\s*$")
GROUP_KEY = re.compile(r"^(Hawaii\s+Constitution|Hawaiian\s+Homes\s+Commission"
                       r"\s+Act|United\s+States\s+Constitution)$", re.I)


def classify_key(txt):
    txt = txt.strip().rstrip(".,;")
    if not txt or SKIP_KEY.match(txt):
        return "skip", txt, False
    if GROUP_KEY.match(txt):
        return "group", txt, False
    repealed = bool(REPEALED_MARK.search(txt))
    txt = REPEALED_MARK.sub("", txt).strip()
    m = C_CHAP_PART.match(txt)
    if m:
        return "hrs_chapter_part", f"{m.group(1)} pt {m.group(2)}", repealed
    m = C_CHAP.match(txt)
    if m:
        return "hrs_chapter", m.group(1), repealed
    for kind, rx in KEY_PATTERNS:
        if rx.match(txt):
            return kind, txt, repealed
    txt = restore_dash(txt)
    for kind, rx in KEY_PATTERNS:
        if rx.match(txt):
            return kind, txt, repealed
    if " " in txt and PROSE.search(txt):
        return "prose", txt, False
    return None, txt, repealed


def parse_rules(tokens):
    """Compressed rule list -> list of full HAR section ids.

    Returns (ids, leftovers).  `leftovers` is anything unrecognised, so a
    silent drop is impossible: the caller asserts it is empty.
    """
    ids, leftovers = [], []
    prefix = None            # "13-275" - inherited by later bare numbers
    i = 0
    # Normalise the separators the table uses between entries.
    # Split on separators AND whitespace: a cell arrives as one string, and
    # "8-19-1 to 3" must become three tokens or the range is never seen and the
    # whole entry is silently dropped.
    toks = []
    for t in tokens:
        for part in re.split(r"[,;\s]+", t.strip()):
            part = part.strip(".").rstrip("-")
            if part:
                toks.append(part)
    while i < len(toks):
        t = toks[i]
        if t.lower() == "to" and ids and i + 1 < len(toks):
            # range: previous id .. next number
            nxt = toks[i + 1]
            m = HAR_FULL.match(nxt)
            hi = m.group(3) if m else (nxt if BARE.match(nxt) else None)
            lo = ids[-1].rsplit("-", 1)[1]
            pfx = ids[-1].rsplit("-", 1)[0]
            if hi is not None and lo.isdigit() and hi.isdigit():
                for n in range(int(lo) + 1, int(hi) + 1):
                    ids.append(f"{pfx}-{n}")
                prefix = pfx
                i += 2
                continue
            # A decimal or lettered endpoint cannot be safely enumerated; keep
            # both ends and record the span rather than inventing members.
            if hi is not None:
                ids.append(f"{pfx}-{hi}")
                i += 2
                continue
            leftovers.append(nxt)
            i += 2
            continue
        m = HAR_FULL.match(t)
        if m:
            prefix = f"{m.group(1)}-{m.group(2)}"
            ids.append(t)
            i += 1
            continue
        m = HAR_CHAP.match(t)
        if m:
            # A chapter-level reference. Keep the prefix so a following bare
            # number still resolves, but emit the chapter as-is.
            prefix = t
            ids.append(t)
            i += 1
            continue
        if BARE.match(t) and prefix:
            ids.append(f"{prefix}-{t}")
            i += 1
            continue
        leftovers.append(t)
        i += 1
    return ids, leftovers


def cells(pg):
    """-> (rows, footnotes); each row is 4 strings, in column order.

    Like the Directory, this table carries superscript footnote marks glued to
    a key ('9-9' + tiny '1') and 10pt numbered footnotes at the page foot.  The
    footnotes are the LRB flagging defects in what the agencies asserted -
    "No such HRS section" - so they are captured, not discarded.
    """
    ws = [w for w in pg.extract_words(extra_attrs=["size"])
          if 95 <= w["top"] <= 735]
    rows, footnotes, fn_mode = [], [], False
    for top, lw in lines_of(ws, tol=3.0):
        small = min((w.get("size", 11.04) for w in lw), default=11.04)
        txt_all = render(lw)
        if small <= 10.5 and (FOOTNOTE_RE.match(txt_all) or fn_mode):
            if FOOTNOTE_RE.match(txt_all):
                m = FOOTNOTE_RE.match(txt_all)
                footnotes.append({"number": int(m.group(1)), "text": m.group(2)})
                fn_mode = True
            elif footnotes:
                footnotes[-1]["text"] += " " + txt_all
            continue
        lw, _mark = strip_footnote_mark(lw)
        if not lw:
            continue
        row = []
        for _, lo, hi in COLS:
            got = [w for w in lw if lo <= (w["x0"] + w["x1"]) / 2.0 < hi]
            row.append(render(got))
        if any(row):
            rows.append(row)
    return rows, footnotes


def main():
    import pdfplumber

    path = os.path.join(RAW_PDF, PDF_NAME)
    if not os.path.exists(path):
        sys.exit("run tools/har_directory.py first to fetch the PDF")

    edges, slh_edges, problems = [], [], []
    footnotes, prose = [], []
    stamp = dt.date.today().isoformat()

    with pdfplumber.open(path) as pdf:
        hrs_pages, slh_pages = [], []
        mode = None
        for i, pg in enumerate(pdf.pages):
            head = " ".join((pg.extract_text() or "")[:150].split())
            if head.startswith(HRS_TABLE_HEAD):
                mode = "hrs"
            elif head.startswith(SLH_TABLE_HEAD):
                mode = "slh"
            elif head.startswith("HAWAII ADMINISTRATIVE RULES DIRECTORY"):
                mode = None
            if mode == "hrs":
                hrs_pages.append(i)
            elif mode == "slh":
                slh_pages.append(i)
        print(f"HRS->HAR table: pages {hrs_pages[0]}..{hrs_pages[-1]} "
              f"({len(hrs_pages)})")
        print(f"session-law table: pages {slh_pages[0]}..{slh_pages[-1]} "
              f"({len(slh_pages)})")

        # ---- HRS sections implemented -------------------------------------
        # A blank key cell means "still the section above", and that run does
        # NOT stop at a column or page boundary: a rule list started in the
        # right column of one page continues in the left column of the next.
        # So the current key persists across the whole table in reading order
        # (page N pair 0, page N pair 1, page N+1 pair 0, ...).  Resetting it
        # per page silently drops every leading continuation row.
        cur, kind, group = None, None, ""
        cur_repealed = False
        buf = []
        for pi in hrs_pages:
            rows, fns = cells(pdf.pages[pi])
            for f in fns:
                f["page"] = pi
                f["table"] = "hrs"
            footnotes.extend(fns)
            for pair in (0, 1):
                for row in rows:
                    k, v = row[pair * 2], row[pair * 2 + 1]
                    if k:
                        if cur is not None and buf:
                            ids, left = parse_rules(buf)
                            for d in ids:
                                edges.append({"src": d, "src_kind": "har_section",
                                              "rel": "implements",
                                              "dst": cur, "dst_kind": kind,
                                              "dst_repealed": cur_repealed,
                                              "group": group, "page": pi})
                            if left:
                                problems.append({"page": pi, "key": cur,
                                                 "unparsed": left})
                        nk, nv, nrep = classify_key(k)
                        if nk == "prose":
                            prose.append({"page": pi, "text": nv})
                            continue
                        if nk == "skip":
                            continue                 # repeated column header
                        if nk == "group":
                            group = nv               # statutory series heading
                            cur, kind, buf = None, None, []
                            continue
                        if nk is None:
                            problems.append({"page": pi, "issue": "unclassified key",
                                             "text": k})
                            cur, kind, buf = None, None, []
                            continue
                        cur, kind, buf = nv, nk, ([v] if v else [])
                        cur_repealed = nrep
                    elif v:
                        buf.append(v)
        # One final flush for the last key in the table; flushing per page would
        # cut every run that crosses a page boundary and double-count the rest.
        if cur is not None and buf:
            ids, left = parse_rules(buf)
            for d in ids:
                edges.append({"src": d, "src_kind": "har_section",
                              "rel": "implements", "dst": cur,
                              "dst_kind": kind, "dst_repealed": cur_repealed,
                              "group": group, "page": hrs_pages[-1]})
            if left:
                problems.append({"page": hrs_pages[-1], "key": cur,
                                 "unparsed": left})

        # ---- session laws implemented -------------------------------------
        year_re = re.compile(r"^(19|20)\d{2}$")
        act_re = re.compile(r"^Act\s+(\d+)\s*(.*)$")
        for pi in slh_pages:
            rows, fns = cells(pdf.pages[pi])
            for f in fns:
                f["page"] = pi
                f["table"] = "session_laws"
            footnotes.extend(fns)
            for pair in (0, 1):
                year, cur, buf = None, None, []
                for row in rows:
                    k, v = row[pair * 2], row[pair * 2 + 1]
                    if k and year_re.match(k):
                        year = k
                        continue
                    if k:
                        if cur and buf:
                            ids, left = parse_rules(buf)
                            for d in ids:
                                slh_edges.append({"src": d,
                                                  "src_kind": "har_section",
                                                  "rel": "implements",
                                                  "dst": cur,
                                                  "dst_kind": "session_law",
                                                  "page": pi})
                            if left:
                                problems.append({"page": pi, "key": cur,
                                                 "unparsed": left})
                        _nk, _nv, _r = classify_key(k)
                        if _nk == "prose":
                            prose.append({"page": pi, "text": _nv})
                            continue
                        m = act_re.match(k)
                        cur = (f"{year} Act {m.group(1)}"
                               + (f" {m.group(2)}" if m.group(2) else "")) if m \
                            else (f"{year} {k}" if year else k)
                        buf = [v] if v else []
                    elif v:
                        buf.append(v)
                if cur and buf:
                    ids, left = parse_rules(buf)
                    for d in ids:
                        slh_edges.append({"src": d, "src_kind": "har_section",
                                          "rel": "implements", "dst": cur,
                                          "dst_kind": "session_law", "page": pi})

        # ---- validation: independent sweep for full HAR cites -------------
        # Every TITLE-CHAPTER-SECTION token on a table page must appear as an
        # edge source.  The HRS parser's first pass silently dropped 11 real
        # cross-references; this is the equivalent guard.
        # Two sources of false alarm have to be excluded or the guard cries
        # wolf and stops meaning anything:
        #   - an HRS colon-form key whose colon was lost ("412-2-105") looks
        #     exactly like a HAR section but sits in the KEY column;
        #   - a four-part Taxation cite ("18-231-9.9-07") contains a valid
        #     three-part prefix that is not itself a citation.
        got = {e["src"] for e in edges} | {e["src"] for e in slh_edges}
        covered = set(got)
        for g in got:
            parts = g.split("-")
            for n in range(3, len(parts)):
                covered.add("-".join(parts[:n]))
            # A five-part cite such as 11-54-9.1.01 contains 11-54-9.1, which is
            # a prefix and not a separate citation.
            if "." in parts[-1]:
                bits = parts[-1].split(".")
                for n in range(1, len(bits)):
                    covered.add("-".join(parts[:-1] + [".".join(bits[:n])]))
        strict = set()
        for pi in hrs_pages + slh_pages:
            rows, _ = cells(pdf.pages[pi])
            keys = " ".join(r[0] + " " + r[2] for r in rows)
            vals = " ".join(r[1] + " " + r[3] for r in rows)
            for m in re.finditer(r"\b(\d{1,2}-\d+(?:\.\d+)?-\d+(?:\.\d+)?)\b",
                                 vals):
                if m.group(1) not in keys:
                    strict.add(m.group(1))
        missed = sorted(strict - covered, key=sec_sort_key)
        if missed:
            problems.append({"issue": "full HAR cites present in the text but "
                                      "absent from the edge list",
                             "count": len(missed), "examples": missed[:40]})

    out = {
        "built": stamp,
        "source": {
            "publisher": "Hawaii Legislative Reference Bureau",
            "publication": ("Hawaii Administrative Rules 2025 Table of Statutory "
                            "Sections Implemented and Directory"),
            "url": PDF_URL,
            "sha256": sha256_file(path),
            "retrieved": stamp,
        },
        "relation_semantics": {
            "implements": ("The adopting agency asserts this HAR section "
                           "implements that HRS section or session law. Compiled "
                           "by the LRB from the rule's own 'Imp:' note. Agency "
                           "assertion, not revisor or judicial determination."),
            "completeness": ("Covers only rules converted to HAR format and filed "
                             "with the Lieutenant Governor before 2026-01-01. "
                             "Absence of an edge is not evidence that no rule "
                             "implements a section."),
            "not_included": ("The 'Auth:' relation - which statutes authorised a "
                             "rule - is a DIFFERENT relation and is not in this "
                             "table. It can only be read off the rule text."),
        },
        "totals": {
            "hrs_edges": len(edges),
            "session_law_edges": len(slh_edges),
            "distinct_hrs_targets": len({e["dst"] for e in edges}),
            "distinct_har_sources": len({e["src"] for e in edges}),
        },
        "footnotes": footnotes,
        "prose_lines": prose,
        "edges": edges,
        "session_law_edges": slh_edges,
    }
    os.makedirs(GRAPH, exist_ok=True)
    with open(os.path.join(GRAPH, "har-edges.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    with open(os.path.join(GRAPH, "har_crosswalk_problems.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"built": stamp, "problems": problems}, fh, indent=1,
                  ensure_ascii=False)

    print(f"\nHRS->HAR edges        {len(edges)}")
    print(f"  distinct HRS targets {out['totals']['distinct_hrs_targets']}")
    print(f"  distinct HAR sources {out['totals']['distinct_har_sources']}")
    print(f"session-law edges     {len(slh_edges)}")
    print(f"footnotes             {len(footnotes)}")
    print(f"prose lines skipped   {len(prose)}")
    print(f"problems              {len(problems)}")
    for p in problems[:6]:
        print("   ", json.dumps(p, ensure_ascii=False)[:150])


if __name__ == "__main__":
    main()
