"""Parse the LRB's Hawaii Administrative Rules DIRECTORY into graph/har-universe.json.

Source: lrb.hawaii.gov 2025 Table of Statutory Sections Implemented and
Directory (published July 2026, covering rules filed before 2026-01-01).
The Directory is the only authoritative enumeration of HAR that exists: it
lists every chapter under every title, with its catchline, its subtitle/part
placement, whether it is repealed or reserved, and the department's own
canonical rules URL.  There is no central full-text source for HAR, so this
PDF is to HAR what the /hrscurrent/ directory listings are to HRS.

WHY GEOMETRY AND NOT TEXT
`pdftotext -layout` flattens the Directory's two-column layout into lines that
interleave the columns, and a wrapped cell in one column lands on the row of a
different entry in the other.  That does not fail loudly - it silently
mis-attributes catchlines.  So this reads word coordinates and rebuilds the
columns before reading anything.

    python tools/har_directory.py            # parse the cached PDF
    python tools/har_directory.py --fetch    # (re-)download it first
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from har_lib import (GRAPH, RAW_PDF, TITLES, chap_sort_key, chapter_id, fetch,
                     normalize_dashes, sha256_file)

PDF_URL = ("https://lrb.hawaii.gov/wp-content/uploads/"
           "2025AdminRules_Supplement.pdf")
PDF_NAME = "lrb-2025-har-table-and-directory.pdf"

# The gutter between the two columns.  Words are assigned by their CENTRE, not
# their left edge: chapter numbers are right-aligned in their field, so a wide
# cross-title number like "17-2015" starts at x0=314.9 - left of the gutter -
# while belonging to the right column.  Splitting on x0 glues it onto the end
# of the left column's line ("181 Repealed 17-2015") and loses the entry.
GUTTER = 317.0
# A chapter number must start at or left of these; anything further right on
# the line is a wrapped continuation of the entry above it.
NUM_BAND = {"L": 120.0, "R": 370.0}
# The subtitle indent: left of the wrapped-catchline indent (130 / 382) and
# right of the "Chapter" label (72 / 324).  Used only for headings printed
# without a "Subtitle N" prefix.
# Kept clear of where catchline text begins after a chapter number (122 left,
# 374 right), or a long catchline's first line reads as a heading.
SUB_BAND = {"L": (94.0, 112.0), "R": (344.0, 360.0)}
# Body text is 11.04pt.  URLs and footnotes are 10pt; footnote reference marks
# are 6.96pt superscripts glued to the chapter number ("70064" = ch 700, fn 64).
SUPERSCRIPT_MAX = 9.0
FOOTNOTE_RE = re.compile(r"^(\d+)\.\s+(.*)$")

# A chapter "number" is 1, 181.1, a cross-title 17-2015, or a range 84 to 88.
_N = r"\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?"
CHAP_ROW = re.compile(rf"^({_N})(?:\s+to\s+({_N}))?\s+(.+)$")
RESERVED = re.compile(r"^\(?\s*reserved\s*\)?\.?$", re.I)
REPEALED = re.compile(r"^repealed\.?$", re.I)


def lines_of(words, tol=3.5):
    """Cluster words into visual lines by their top coordinate."""
    out = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if out and abs(w["top"] - out[-1][0]) <= tol:
            out[-1][1].append(w)
        else:
            out.append([w["top"], [w]])
    return [(top, sorted(ws, key=lambda w: w["x0"])) for top, ws in out]


def render(ws):
    return normalize_dashes(" ".join(w["text"] for w in ws)).strip()


def unsplit_keyword(txt):
    """The PDF sometimes emits a structural keyword as two words: 'S ubtitle 6'
    on p. 148 is one heading, not a chapter catchline.  Left alone the heading
    is swallowed into the previous chapter's catchline and every chapter after
    it inherits the wrong subtitle.  Tolerates a break anywhere in the word.
    """
    for kw in ("Subtitle", "Chapter", "Part"):
        m = re.match(r"\s*".join(map(re.escape, kw)) + r"\b", txt)
        if m:
            return kw + txt[m.end():]
    return txt


def strip_footnote_mark(lw):
    """Pull a superscript footnote reference out of a line's words.

    The Directory glues the mark to the chapter number with no space ('70064'
    is chapter 700 carrying footnote 64).  Because extract_words is called with
    extra_attrs=["size"], pdfplumber already splits on the font-size change, so
    the mark arrives as its own 6.96pt all-digit word.  Left in place it reads
    as the chapter's catchline, and chapter 23-700 gets the catchline "64".
    Returns (remaining_words, footnote_number_or_None).
    """
    marks = [w for w in lw
             if w.get("size", 11.04) < SUPERSCRIPT_MAX and w["text"].isdigit()]
    if not marks:
        return lw, None
    keep = [w for w in lw if w not in marks]
    return keep, int(marks[0]["text"])


def directory_pages(pdf):
    """Locate the Directory: from the page headed 'HAWAII ADMINISTRATIVE RULES
    / DIRECTORY' through the end of the document."""
    start = None
    for i, pg in enumerate(pdf.pages):
        t = pg.extract_text() or ""
        head = " ".join(t[:120].split())
        if head.startswith("HAWAII ADMINISTRATIVE RULES DIRECTORY"):
            start = i
            break
    if start is None:
        raise RuntimeError("could not locate the Directory heading")
    return start, len(pdf.pages) - 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    args = ap.parse_args()

    import pdfplumber

    os.makedirs(RAW_PDF, exist_ok=True)
    path = os.path.join(RAW_PDF, PDF_NAME)
    if args.fetch or not os.path.exists(path):
        print(f"fetching {PDF_URL}")
        data, final = fetch(PDF_URL, binary=True)
        with open(path, "wb") as fh:
            fh.write(data)
        print(f"  {len(data)} bytes from {final}")
    digest = sha256_file(path)

    titles = {}          # int -> record
    problems = []
    footnotes = []
    unnumbered = []
    cur_t = None         # current title number
    # Per-column parse state has to persist ACROSS pages and columns, because a
    # subtitle's chapter list routinely runs from the right column of one page
    # into the left column of the next.
    st = {"subtitle": "", "part": "", "pending": None, "hdr": None}

    def title_rec(n):
        return titles.setdefault(n, {
            "title": n,
            "department": TITLES.get(n, ""),
            "department_as_printed": "",
            "url": "",
            "no_rules": False,
            "chapters": [],
            "notes": [],
        })

    def flush_hdr():
        """Finish a TITLE header block: department name lines + URL lines."""
        h = st["hdr"]
        st["hdr"] = None
        if not h:
            return
        rec = title_rec(h["n"])
        if h["name"]:
            rec["department_as_printed"] = " ".join(" ".join(h["name"]).split())
        if h["url"]:
            # The URL wraps mid-token at a hyphen or a dot, so the pieces
            # concatenate with NO separator.
            rec["url"] = "".join(h["url"])
        if h["no_rules"]:
            rec["no_rules"] = True

    def add_chapter(num, num_hi, catchline):
        if cur_t is None:
            problems.append({"issue": "chapter before any TITLE", "text": f"{num} {catchline}"})
            return
        rec = title_rec(cur_t)
        catchline = " ".join(catchline.split())

        # A two-part number in the chapter column is one of two different
        # things, and the leading part tells them apart:
        #   leading part is a valid HAR title (1-24) -> a chapter that moved
        #     departments and kept its original number, e.g. '17-2015' listed
        #     under title 15 (Barbers Point, formerly under DHS), '6-60' under
        #     title 16 (PUC, formerly under Budget and Finance), '2-71' under
        #     title 3 (Office of Information Practices, formerly under Lt Gov).
        #   otherwise -> a SECTION or section range inside the chapter named by
        #     the leading part, e.g. '1454-1 to 1454-56 Repealed' under title 17
        #     is §§17-1454-1 to 17-1454-56, and chapter 17-1454 is listed
        #     separately one line above.  Recording those as chapters invents
        #     chapters 1454-1 and 72-13, which do not exist.
        m2 = re.match(r"^(\d+)-(\d+(?:\.\d+)?)$", str(num))
        if m2 and int(m2.group(1)) not in TITLES:
            rec.setdefault("section_notes", []).append({
                "chapter": chapter_id(cur_t, m2.group(1)),
                "sections": str(num) + (f" to {num_hi}" if num_hi else ""),
                "catchline": catchline,
                "subtitle": st["subtitle"],
                "repealed": bool(REPEALED.match(catchline)),
            })
            st["pending"] = rec["section_notes"][-1]
            return rec["section_notes"][-1]

        entry = {
            "chapter": chapter_id(cur_t, num),
            "title": cur_t,
            "number": num,
            "catchline": catchline,
            "subtitle": st["subtitle"],
            "part": st["part"],
            "repealed": bool(REPEALED.match(catchline)),
            "reserved": bool(RESERVED.match(catchline)),
            "range_to": chapter_id(cur_t, num_hi) if num_hi else None,
            # A chapter printed with its own title prefix under a DIFFERENT
            # title moved departments and kept its original number.  Flagged,
            # never renumbered - renumbering invents a citation.
            "foreign_title": bool(re.match(r"^\d+-", str(num)))
                             and not str(num).startswith(f"{cur_t}-"),
        }
        rec["chapters"].append(entry)
        st["pending"] = entry
        return entry

    with pdfplumber.open(path) as pdf:
        first, last = directory_pages(pdf)
        print(f"Directory: pdf pages {first}..{last}  ({last - first + 1} pages)")
        for pi in range(first, last + 1):
            pg = pdf.pages[pi]
            ws = [w for w in pg.extract_words(use_text_flow=False,
                                              extra_attrs=["size"])
                  if 60 <= w["top"] <= 730]
            # Drop the centred document heading on the first Directory page;
            # it straddles the gutter and would corrupt the column split.
            drop = set()
            for top, lw in lines_of(ws):
                if render(lw) in ("HAWAII ADMINISTRATIVE RULES", "DIRECTORY"):
                    drop.update(id(w) for w in lw)
            ws = [w for w in ws if id(w) not in drop]

            # Footnotes: 10pt, numbered, below the body text.  Pulled out before
            # column splitting so they never read as chapter rows.
            fn_words, body = [], []
            for top, lw in lines_of(ws):
                txt = render(lw)
                sz = min(w.get("size", 11.04) for w in lw)
                if sz <= 10.5 and top > 650 and FOOTNOTE_RE.match(txt):
                    fn_words.append((top, lw))
                elif fn_words and sz <= 10.5 and top > fn_words[-1][0]:
                    fn_words.append((top, lw))       # wrapped footnote text
                else:
                    body.extend(lw)
            if fn_words:
                cur_fn = None
                for top, lw in fn_words:
                    txt = render(lw)
                    m = FOOTNOTE_RE.match(txt)
                    if m:
                        cur_fn = {"page": pi, "number": int(m.group(1)),
                                  "text": m.group(2), "title": cur_t}
                        footnotes.append(cur_fn)
                    elif cur_fn:
                        cur_fn["text"] = (cur_fn["text"] + " " + txt).strip()
            ws = body

            for side in ("L", "R"):
                col = [w for w in ws
                       if ((w["x0"] + w["x1"]) / 2.0 < GUTTER if side == "L"
                           else (w["x0"] + w["x1"]) / 2.0 >= GUTTER)]
                for top, lw in lines_of(col):
                    lw, fn_mark = strip_footnote_mark(lw)
                    if not lw:
                        continue
                    txt = unsplit_keyword(render(lw))
                    if not txt:
                        continue
                    x0 = lw[0]["x0"]

                    m = re.match(r"^TITLE\s+(\d+)\b(.*)$", txt)
                    if m and not m.group(2).strip():
                        flush_hdr()
                        cur_t = int(m.group(1))
                        title_rec(cur_t)
                        st.update(subtitle="", part="", pending=None,
                                  hdr={"n": cur_t, "name": [], "url": [],
                                       "no_rules": False})
                        continue

                    if st["hdr"] is not None:
                        h = st["hdr"]
                        if txt.startswith("http") or (h["url"] and
                                                      not re.match(r"^[A-Z(]", txt)):
                            h["url"].append(txt)
                            continue
                        if re.match(r"^\(No rules\)", txt, re.I):
                            h["no_rules"] = True
                            continue
                        if txt.isupper() or re.match(r"^[A-Z][A-Z ,\-‘ʻ']+$", txt):
                            h["name"].append(txt)
                            continue
                        flush_hdr()

                    m = re.match(r"^Subtitle\s+(\S+?)\.?\s+(.*)$", txt)
                    if m:
                        st["subtitle"] = f"Subtitle {m.group(1)}. {m.group(2)}".strip()
                        st["part"] = ""
                        st["pending"] = ("subtitle", None)
                        continue
                    m = re.match(r"^Part\s+([IVXLC]+|\d+[A-Za-z]?)\.?\s+(.*)$", txt)
                    if m:
                        st["part"] = f"Part {m.group(1)}. {m.group(2)}".strip()
                        st["pending"] = ("part", None)
                        continue
                    if txt == "Chapter":
                        st["pending"] = None
                        continue
                    m = re.match(r"^See\s+Title\s+(\d+)\b[:.]?\s*(.*)$", txt)
                    if m:
                        if cur_t is not None:
                            title_rec(cur_t)["notes"].append({
                                "subtitle": st["subtitle"],
                                "see_title": int(m.group(1)),
                                "text": txt,
                            })
                        st["pending"] = ("note", title_rec(cur_t)["notes"][-1]
                                         if cur_t is not None else None)
                        continue

                    # A subtitle heading printed WITHOUT its "Subtitle N"
                    # prefix, e.g. a bare "Office of Information Practices" on
                    # p. 123.  It sits at the subtitle indent, which is left of
                    # the wrapped-catchline indent, and starts with a letter, so
                    # it cannot be confused with a chapter row or a wrap.  Left
                    # unhandled it is absorbed into the previous chapter's
                    # catchline and every chapter below it inherits the wrong
                    # subtitle.
                    # Only when we are not already mid-heading: a subtitle,
                    # part or See-Title heading wraps onto a second line that
                    # can also land in this band, and that wrap is a
                    # continuation, not a new heading.
                    if (re.match(r"^[A-Z]", txt) and SUB_BAND[side][0] <= x0
                            <= SUB_BAND[side][1]
                            and (st["pending"] is None
                                 or isinstance(st["pending"], dict))):
                        st["subtitle"] = txt
                        st["part"] = ""
                        st["pending"] = ("subtitle", None)
                        unnumbered.append({"page": pi, "title": cur_t,
                                           "heading": txt})
                        continue

                    m = CHAP_ROW.match(txt)
                    if m and x0 <= NUM_BAND[side]:
                        e = add_chapter(m.group(1), m.group(2), m.group(3))
                        if e is not None and fn_mark:
                            e["footnote"] = fn_mark
                        continue
                    # A chapter whose catchline is only a footnote mark leaves
                    # the number alone on its line.
                    if re.fullmatch(_N, txt) and x0 <= NUM_BAND[side]:
                        e = add_chapter(txt, None, "")
                        if e is not None and fn_mark:
                            e["footnote"] = fn_mark
                        continue

                    # Anything else is the wrapped remainder of whatever came
                    # last: a chapter catchline, a subtitle/part name, a note.
                    p = st["pending"]
                    if isinstance(p, dict):
                        p["catchline"] = (p["catchline"] + " " + txt).strip()
                        p["repealed"] = bool(REPEALED.match(p["catchline"]))
                        p["reserved"] = bool(RESERVED.match(p["catchline"]))
                    elif isinstance(p, tuple) and p[0] == "subtitle":
                        st["subtitle"] = (st["subtitle"] + " " + txt).strip()
                    elif isinstance(p, tuple) and p[0] == "part":
                        st["part"] = (st["part"] + " " + txt).strip()
                    elif isinstance(p, tuple) and p[0] == "note" and p[1]:
                        p[1]["text"] = (p[1]["text"] + " " + txt).strip()
                    else:
                        problems.append({"page": pi, "side": side,
                                         "title": cur_t, "issue": "orphan line",
                                         "text": txt[:160]})
        flush_hdr()

    # ---------------- validation ----------------
    # 1. A chapter number listed twice within one title.  HAR chapter numbers
    #    are unique within a title, so this is a defect in the LRB's own
    #    Directory, not a parse error - verified by hand against pp. 142-144
    #    (title 15 lists chs 210, 211, 301, 310, 321 under two different
    #    subtitles, and the two listings give DIFFERENT catchlines for 301 and
    #    310) and p. 152 (title 19 ch 150 appears both live and repealed).
    #    Both listings are kept and flagged.  Silently deduping would pick a
    #    winner arbitrarily and hide a real contradiction in the source.
    for n, rec in titles.items():
        seen = {}
        for c in rec["chapters"]:
            seen.setdefault(c["chapter"], []).append(c)
        for cid, group in seen.items():
            if len(group) < 2:
                continue
            for i, c in enumerate(group):
                c["duplicate_listing"] = True
                c["listing_index"] = i
            cats = [c["catchline"] for c in group]
            problems.append({
                "title": n, "chapter": cid,
                "issue": "listed more than once in the LRB Directory",
                "verdict": "source defect, both listings kept",
                "catchlines_agree": len(set(cats)) == 1,
                "listings": [{"catchline": c["catchline"],
                              "subtitle": c["subtitle"],
                              "repealed": c["repealed"]} for c in group],
            })
    # 2. Every title we know about should have been seen in the Directory.
    for n in TITLES:
        if n not in titles:
            problems.append({"title": n, "issue": "title absent from Directory"})

    # Footnotes are collected per page, before that page's TITLE headers are
    # read, so attribute each one to the chapter that actually carries its
    # superscript mark rather than to whichever title was current.
    for fn in footnotes:
        fn["title"] = None
        for n, rec in titles.items():
            for c in rec["chapters"]:
                if c.get("footnote") == fn["number"]:
                    fn["title"] = n
                    fn["chapter"] = c["chapter"]
                    c["footnote_text"] = fn["text"]
        if fn["title"] is None:
            problems.append({"issue": "footnote with no referring chapter",
                             "footnote": fn["number"], "text": fn["text"]})

    total = sum(len(r["chapters"]) for r in titles.values())
    for rec in titles.values():
        rec["chapters"].sort(key=lambda c: chap_sort_key(c["chapter"]))
        rec["chapter_count"] = len(rec["chapters"])
        rec["live_count"] = sum(1 for c in rec["chapters"]
                                if not c["repealed"] and not c["reserved"])

    stamp = dt.date.today().isoformat()
    out = {
        "built": stamp,
        "source": {
            "publisher": "Hawaii Legislative Reference Bureau",
            "publication": ("Hawaii Administrative Rules 2025 Table of Statutory "
                            "Sections Implemented and Directory"),
            "published": "July 2026",
            "covers_rules_filed_before": "2026-01-01",
            "url": PDF_URL,
            "retrieved": stamp,
            "sha256": digest,
            "pdf_bytes": os.path.getsize(path),
            "caveat": ("The Directory lists only rules converted to the Hawaii "
                       "Administrative Rules format and filed with the Office of "
                       "the Lieutenant Governor. Rules never converted, or exempt "
                       "from HRS chapter 91, do not appear. Chapter placement and "
                       "catchlines are the LRB's compilation, not the agency's."),
        },
        "totals": {
            "titles": len(titles),
            "chapters": total,
            "live_chapters": sum(r["live_count"] for r in titles.values()),
        },
        "footnotes": footnotes,
        "unnumbered_subtitle_headings": unnumbered,
        "titles": {str(k): titles[k] for k in sorted(titles)},
    }
    os.makedirs(GRAPH, exist_ok=True)
    with open(os.path.join(GRAPH, "har-universe.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    with open(os.path.join(GRAPH, "har_directory_problems.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"built": stamp, "problems": problems}, fh, indent=1,
                  ensure_ascii=False)

    print(f"\n{'title':>5}  {'chapters':>8} {'live':>5}  department")
    for k in sorted(titles):
        r = titles[k]
        flag = "  (No rules)" if r["no_rules"] else ""
        print(f"{k:>5}  {r['chapter_count']:>8} {r['live_count']:>5}  "
              f"{r['department'][:44]}{flag}")
    print(f"\ntitles {len(titles)}   chapters {total}   "
          f"live {out['totals']['live_chapters']}")
    print(f"problems {len(problems)}"
          + ("  <-- MUST be explained in log.md" if problems else ""))


if __name__ == "__main__":
    main()
