"""Parse ALL extracted HAR rule text into sections, zones, and typed edges.

    python tools/har_parse_all.py [--titles 2,5,7]

Reads  raw/har/txt/tNN/<doc>.txt        (tools/har_extract_all.py)
       raw/har/_pdf/_downloads.json     provenance per doc
       graph/har-universe.json          LRB chapter enumeration (catchlines)
       graph/har-edges.json             LRB Imp crosswalk (healing + cross-check)
       graph/sections.json              harvested HRS corpus (healing corroboration)
Writes graph/har-rules.json             sections + typed edges, ALL chapters
       graph/har_text_problems.json     every validation exception + quarantine

Generalises tools/har_rules.py (the 3-160/3-161 parser) to the whole HAR.
Everything that parser learned from the CSC PDFs is kept; what changes is
parameterisation and honesty at scale:

  * CHAPTER IDENTITY COMES FROM THE PDF ITSELF: the T-C prefixes of the
    section headers found in the document. The harvest manifest's hint is a
    cross-check only; a mismatch is a problem entry, never silently resolved.
  * One document may carry many chapters (titles 21 and 23 print whole-title
    compilations). Sections are grouped by their own chapter prefix.
  * TOC/body split is chosen, not assumed: among candidate split points the
    one minimising TOC-vs-body disagreement wins. Chapters with no TOC parse
    body-only and are RECORDED as toc_absent — the ground-truth check did not
    run for them and coverage must say so.
  * OCR-era defects heal ONLY with corroboration, every heal logged:
      - a TOC id missing from the body is re-sought under OCR distortions of
        its own header ('§2-1-6' printed as '52-1-6') — the chapter's own TOC
        is the attestation;
      - a cite the LRB Table expects heals under l/1, O/0 and spacing
        distortions ('92F-ll', '9 2 -1. 5') — the Table is the attestation;
      - uncorroborated residue stays flagged, never guessed.
  * A document with no HAR section headers is classified no_har_sections
    (agency ancillaries: fee schedules, species lists, amendment memos) and
    skipped — recorded, never guessed at.
  * QUARANTINE, NOT BATCH DEATH — but only for parse-integrity failures:
    sweep misses, majority-empty operative text, or TOC disagreement above
    20% after repairs. Small residual mismatches are per-section problem
    entries on a kept chapter.
  * Colon-form HRS cites (412:2-105, 431:10A-301) are claimed and masked
    BEFORE any other tokenizer runs: hrs_lib's _SEC would shred them into
    phantom sections (open-questions, 2026-07-25).

Auth and Imp remain distinct relations, both the ADOPTING AGENCY'S assertion
(schema rule 11). The Imp label is matched OCR-tolerantly ('(1mp:') — the
CSC-era dropped-paren guard survives alongside it.
"""
import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from har_lib import GRAPH, RAW_HAR, RAW_PDF, normalize_dashes, sec_sort_key
import hrs_lib

TXT = os.path.join(RAW_HAR, "txt")

_SEC = r"\d+[A-Z]?-\d+(?:\.\d+)?"                       # an HRS section token
# colon-form HRS cite: chapter:article-section. The hyphen part is REQUIRED —
# without it the pattern matches clock times ('4:30 p.m.') and mints phantoms.
_COLON = r"\d+[A-Z]?:\d+[A-Z]?-\d+(?:\.\d+)?"
_HARSEC = r"\d+-\d+(?:\.\d+)?-\d+(?:\.\d+)?[a-z]?"      # any HAR section
HARSEC_RE = re.compile(r"^(\d+)-(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?[a-z]?)$")

SECTION_START = re.compile(r"(?m)^\s*[§S]\s*(" + _HARSEC + r")\s+(\S.*)$")
SUBCHAPTER = re.compile(r"(?mi)^SUBCHAPTER\s+(\d+)\s+(.+?)\s*$")
CITE_SHAPED = re.compile(r"\d+[A-Z]?-\d+")
TINY_JUNK = re.compile(r"^[^A-Za-z]{1,3}$")
TRAILING_JUNK = re.compile(r"^[\W\d]*[A-Za-z]{0,2}[\W\d]*$")
DATE_TOKEN = re.compile(r"\d{1,2}/\d{1,2}/\d{2,4}")
# a physical received/filing stamp, any month, OCR-mangled freely. The first
# letter is unreliable ('nEC 09 2016'); the LAST TWO letters of a month
# abbreviation are unique across all twelve months, so the month is read from
# them and the stamp NORMALISES TO A DATE rather than vanishing — the stamp is
# the compilation date, the last event in the section's amendment history.
STAMP_ANY = re.compile(
    r"\b([A-Za-z]{2,4})\s*([O0-9])\s*(\d)\s*[,.]?\s*([12]\s*[09]\s*\d\s*\d)\b")
_MONTH_BY_TAIL = {"an": 1, "eb": 2, "ar": 3, "pr": 4, "ay": 5, "un": 6,
                  "ul": 7, "ug": 8, "ep": 9, "ct": 10, "ov": 11, "ec": 12}


def stamp_to_date(m):
    """'DEC 0 9 2016' -> '12/9/2016'; unrecognisable months blank out."""
    month = _MONTH_BY_TAIL.get(m.group(1)[-2:].lower())
    if not month:
        return " "
    day = int((m.group(2).replace("O", "0").replace("o", "0")) + m.group(3))
    year = re.sub(r"\s", "", m.group(4))
    return f"{month}/{day}/{year}"
NOTE_LABEL = {"Auth": r"[Aa]uth", "Imp": r"[I1l]mp"}
# federal cite shapes as they appear in Auth/Imp notes; the tail must start
# with a digit or the pattern eats the following word ('42 U.S.C. and')
_USC_RE = re.compile(
    r"(\d+)\s*U\.?\s?S\.?\s?C\.?A?\.?\s*(?:§§?\s*)?(\d[\w.]*(?:-[\w.]+)?)?")
_CFR_RE = re.compile(
    r"(\d+)\s*C\.?\s?F\.?\s?R\.?\s*(?:§§?|[Pp]arts?)?\s*(\d[\w.]*(?:-[\w.]+)?)?")
_PL_RE = re.compile(r"P(?:ub)?\.?\s?L(?:aw)?\.?\s?(?:No\.?)?\s*(\d+-\d+)")


def mask_federal(s):
    """Blank every federal-cite span; the sweep uses this so a P.L. number is
    not mistaken for a missed HRS section token."""
    for rx in (_USC_RE, _CFR_RE, _PL_RE):
        s = rx.sub(lambda m: " " * len(m.group(0)), s)
    return s


def header_repairs(chapter):
    """Print-defect repairs parameterised by chapter, from har_rules.py.
    Applied at parse time only; every hit is logged."""
    c = re.escape(chapter)
    return [
        # digits split inside a section number: '§3-160-4 0 Expenditures'
        (re.compile(r"(?m)^§(" + c + r"-\d+)\s(\d(?:\.\d+)?)\s+(?=[A-Z(\"'])"),
         r"§\1\2 "),
        # a hyphen dropped/space-mangled inside the id: '§3 161-41', '§3-161 51'
        (re.compile(r"(?m)^§\s*" + c.replace(r"\-", r"[\s-]") +
                    r"[\s-](\d+(?:\.\d+)?[a-z]?)\b"),
         "§" + chapter + r"-\1"),
    ]


def strip_page(page_text, chapter_nums):
    """Remove running header / page number / stamp junk from one page.
    Handles bare-id headers ('§3-160-4'), bare chapter ids, and TRUNCATED
    running headers ('§4-41-')."""
    lines = page_text.split("\n")
    if lines:
        head = lines[0].strip()
        # bare-id running headers, including the truncated '§4-41-' and the
        # misprinted '§-160-31' (title digit dropped) forms
        if re.match(r"^[§S]?\s*\d+-\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?[a-z]?|-)?\s*$",
                    head) or re.match(r"^[§S]\s*-\d+-\d+(?:\.\d+)?\s*$", head):
            lines = lines[1:]
    page_num = re.compile(
        r"^(?:" + "|".join(re.escape(c) for c in chapter_nums) + r")-\d+[a-z]?$"
    ) if chapter_nums else re.compile(r"$^")

    # Walk the tail upward. The chapter-relative page number ('160-16') is the
    # DEFINITIVE cut: it is the last thing printed on the page, so everything
    # below it in extraction order is stamp garbage ('3211', '~/10') and it
    # and they all go, while everything above it survives — including a
    # wrapped citation tail like '361)' sitting just above it. Without a page
    # number, trim only trailing junk that cannot be a wrapped citation.
    def junk(s):
        return (not s or TINY_JUNK.match(s)
                or (len(s) <= 8 and TRAILING_JUNK.match(s)
                    and not CITE_SHAPED.search(s)
                    and not re.match(r"^\d+\)", s)))
    i = len(lines) - 1
    floor = max(0, len(lines) - 5)
    cut = None
    while i >= floor:
        s = lines[i].strip()
        if page_num.match(s):
            cut = i
            break
        if not junk(s):
            break
        i -= 1
    if cut is not None:
        lines = lines[:cut]
    else:
        while lines and junk(lines[-1].strip()) and lines[-1].strip():
            lines = lines[:-1]
    return "\n".join(lines)


def dewrap(s):
    s = " ".join(s.split())
    return re.sub(r"-\s+(?=\d)", "-", s)


def balanced_span(text, start):
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return i + 1
    return None


def find_note(joined, label):
    """Locate '(Auth: ...)' / '(Imp: ...)' with balanced parens and an
    OCR-tolerant label ('(1mp:'). Returns (content, start, end) or Nones."""
    lbl = NOTE_LABEL[label]
    m = re.search(r"\(\s*" + lbl + r"\s*:", joined)
    if not m:
        return None, None, None
    end = balanced_span(joined, m.start())
    nxt = re.search(r"\(\s*" + NOTE_LABEL["Imp"] + r"\s*:", joined[m.end():])
    nxt_abs = m.end() + nxt.start() if nxt else None
    if label == "Auth" and nxt_abs is not None and (end is None or end > nxt_abs):
        content = joined[m.end():nxt_abs].strip().rstrip(")( ").strip()
        return content, m.start(), nxt_abs
    if end is None:
        return None, None, None
    return joined[m.end():end - 1].strip(), m.start(), end


def tokenize_note(content):
    """Every HRS cite in an Auth/Imp note, exhaustively. Colon-form is claimed
    FIRST (else _SEC shreds '431:10A-301' into a phantom '10A-301').
    Returns (tokens, leftover): digit-bearing residue the tokenizer could not
    claim surfaces as a problem, never vanishes."""
    out = []
    masked = content

    def consume(m, kind, target):
        nonlocal masked
        out.append((kind, target, m.group(0)))
        masked = masked[:m.start()] + " " * (m.end() - m.start()) + masked[m.end():]

    for m in list(re.finditer(_COLON, masked)):
        consume(m, "hrs_section", m.group(0).upper())
    # federal cites are REAL Auth/Imp relations in health and human-services
    # rules (a DOH chapter implementing 42 C.F.R.) — claimed before the HRS
    # pass so '42 U.S.C. §247d' cannot shred into a phantom
    for m in list(_USC_RE.finditer(masked)):
        base = re.split(r"[(.]", m.group(2) or "")[0].strip(" .,;")
        consume(m, "usc", f"usc:{m.group(1)}" + (f":{base}" if base else ""))
    for m in list(_CFR_RE.finditer(masked)):
        base = re.split(r"[(]", m.group(2) or "")[0].strip(" .,;")
        consume(m, "cfr", f"cfr:{m.group(1)}" + (f":{base}" if base else ""))
    for m in list(_PL_RE.finditer(masked)):
        consume(m, "public_law", f"pl:{m.group(1)}")
    # 'chapter 91', 'ch. 92F', 'chs. 91, 92' — but NOT 'chapter 21-7', which
    # is a hyphenated (HAR-style) chapter a bare match would half-claim,
    # leaving the sweep to find the token the tokenizer masked
    for m in list(re.finditer(r"\bch(?:apters?|s?\.)\s+(\d+[A-Z]?)\b(?!-)",
                              masked, re.I)):
        consume(m, "hrs_chapter", "ch:" + m.group(1).upper())
    for m in re.finditer(_SEC, masked):
        out.append(("hrs_section", m.group(0).upper(), m.group(0)))
    masked = re.sub(_SEC, " ", masked)
    masked = STAMP_ANY.sub(" ", masked)
    residue = re.sub(r"(?i)\bHRS\b|\bHawaii Revised Statutes\b|\(\s*\d+\s*\)|"
                     r"\.\d+|\band\b|\bor\b|\bet\s+seq\b|[§,;()'\s]", " ", masked)
    leftover = " ".join(residue.split())
    leftover = leftover if re.search(r"\d", leftover) else ""
    return out, leftover


def fuzzy_cite_rx(want):
    """Regex matching `want` under the OCR distortions actually observed:
    l/I/| for 1, O for 0, junk or spaces where the hyphen goes, spaces or
    stray dots between every character ('92F-ll', '9 2 -1. 5')."""
    parts = []
    for ch in want:
        if ch == "1":
            parts.append(r"[1Il|]")
        elif ch == "0":
            parts.append(r"[0O]")
        elif ch == "-":
            # junk where the hyphen goes, INCLUDING a stray stamp digit or
            # OCR'd I/l ('11- I 407', '11-1 410') — the CSC-era distortion.
            # Safe only because the sought cite is externally attested.
            parts.append(r"[-\s.·]{1,4}(?:[Il1|][\s.·]{0,2})?")
        elif ch == ".":
            parts.append(r"[.\s]{1,3}")
        elif ch.isalpha():
            # OCR mangles the letter freely ('92Y-ll' for 92F-11); with the
            # digits and shape pinned and the cite externally attested, any
            # single letter in the slot is the same cite
            parts.append(r"[A-Za-z]")
        else:
            parts.append(re.escape(ch))
    return re.compile(r"[\s.·]{0,2}".join(parts))


def heal_note(content, sid, zone, lrb_expected, hrs_sections, problems,
              chapter, doc):
    """Corroboration-only repair of print/OCR-broken citations. Attestors:
    the LRB Table (Imp) or the harvested HRS corpus. Every heal logged."""
    def log(before, after):
        problems.append({"doc": doc, "chapter": chapter, "section": sid,
                         "zone": zone, "kind": "note_cite_healed",
                         "as_printed": before, "read_as": after})

    have = {t.upper() for t in re.findall(_SEC, content)}
    for want in sorted(lrb_expected - have):
        if not re.match(r"^\d+[A-Z]?-\d+(?:\.\d+)?$", want):
            continue
        # stamp digit glued straight onto the cite: '11-4071' for 11-407 —
        # checked BEFORE the fuzzy pass so the glued digit is consumed with
        # the cite instead of surviving as leftover residue
        rx2 = re.compile(re.escape(want) + r"(\d)\b")
        hit2 = rx2.search(content)
        if hit2 and hit2.group(0).upper() not in hrs_sections:
            log(hit2.group(0), want)
            content = content[:hit2.start()] + want + " " + content[hit2.end():]
            continue
        hit = fuzzy_cite_rx(want).search(content)
        if hit and len(hit.group(0)) <= len(want) * 3:
            log(hit.group(0).strip(), want)
            content = content[:hit.start()] + " " + want + " " + content[hit.end():]
    # generic dropped hyphen, corpus-corroborated (covers Auth, no LRB there)
    def _join(m):
        cand = f"{m.group(1)}-{m.group(2)}".upper()
        if cand in hrs_sections:
            log(m.group(0), cand)
            return " " + cand
        return m.group(0)
    content = re.sub(r"\b(\d+[A-Z]?)\s+(\d+(?:\.\d+)?)\b(?!\s*U\.?S)", _join,
                     content)
    return content


def best_split(matches):
    """Choose the TOC/body split point that minimises disagreement between
    the two id sets. Returns (split_index, toc_present). split_index 0 means
    no TOC (all matches are body)."""
    ids = [m.group(1) for m in matches]
    if len(set(ids)) == len(ids):
        return 0, False                     # nothing repeats: no TOC
    best_i, best_score = 0, None
    for i in range(1, len(ids)):
        toc, body = set(ids[:i]), set(ids[i:])
        if not body:
            break
        score = len(toc ^ body)
        if best_score is None or score < best_score:
            best_i, best_score = i, score
    # a "TOC" is only a TOC if it substantially re-appears in the body:
    # sparse duplicates (running headers that survive stripping, cross-refs
    # reprinting a header) must not hallucinate one and shred the chapter
    toc, body = set(ids[:best_i]), set(ids[best_i:])
    if best_i == 0 or len(toc & body) < max(2, len(toc) * 0.4):
        return 0, False
    return best_i, True


def repair_missing_headers(text, chap, missing, problems, doc):
    """TOC-corroborated header repair: a TOC id absent from the body is
    re-sought under OCR distortions of its own header line — '§' printed as
    '5', 'S' or '$', digits spaced or l-for-1. The TOC's own listing is the
    attestation. Returns (text, n_repaired)."""
    n = 0
    for sid in missing:
        core = fuzzy_cite_rx(sid).pattern
        rx = re.compile(r"(?m)^[\s]{0,4}(?:[§S5$]\s*)?(" + core +
                        r")\s+(?=[A-Z(\"'(])")
        for m in rx.finditer(text):
            got = re.sub(r"[\s.·]", "", m.group(1))
            got = got.replace("l", "1").replace("I", "1").replace("|", "1")
            got = got.replace("O", "0").replace("o", "0")
            if got != sid:
                continue
            problems.append({"doc": doc, "chapter": chap, "section": sid,
                             "kind": "header_repaired_from_toc",
                             "as_printed": m.group(0).strip()[:60]})
            text = text[:m.start()] + "§" + sid + " " + text[m.end():]
            n += 1
            break
    return text, n


def parse_chapter(chap, text, all_starts, matches, meta, extract_meta,
                  universe_catchlines, lrb_by_rule, hrs_sections,
                  problems, doc):
    """Parse one chapter's matches out of a document's text. Returns a
    chapter record (with '_edges') or None if quarantined."""
    split_i, toc_present = best_split(matches)
    toc_ids = [m.group(1) for m in matches[:split_i]]
    body_matches = matches[split_i:]
    body_ids = [m.group(1) for m in body_matches]

    mark = len(problems)
    toc_only = sorted(set(toc_ids) - set(body_ids))
    body_only = sorted(set(body_ids) - set(toc_ids))
    if toc_present and (toc_only or body_only):
        problems.append({"doc": doc, "chapter": chap,
                         "kind": "toc_body_mismatch",
                         "toc_only": toc_only, "body_only": body_only})
    if not toc_present:
        problems.append({"doc": doc, "chapter": chap, "kind": "toc_absent",
                         "note": "body-only parse; TOC ground-truth check "
                                 "unavailable"})
    dupes = {x for x in body_ids if body_ids.count(x) > 1}
    if dupes:
        problems.append({"doc": doc, "chapter": chap,
                         "kind": "duplicate_section", "ids": sorted(dupes)})

    subchapters = [(m.start(), f"Subchapter {m.group(1)} — {m.group(2).strip()}")
                   for m in SUBCHAPTER.finditer(text)]
    hist_m = re.search(r"Historical note:[^\n]*(?:\n(?!\s*[§S]\s*\d)[^\n]*)*",
                       text)
    historical_note = dewrap(hist_m.group(0)) if hist_m else ""

    def seg_end(m):
        i = all_starts.index(m.start())
        return all_starts[i + 1] if i + 1 < len(all_starts) else len(text)

    # duplicates: keep the occurrence with the most content (a TOC stray or a
    # running header that survived stripping is short; the real body is long)
    chosen = {}
    for m in body_matches:
        sid = m.group(1)
        length = seg_end(m) - m.start()
        if sid not in chosen or length > chosen[sid][1]:
            chosen[sid] = (m, length)

    sections, edges = {}, []
    for sid, (m, _len) in sorted(chosen.items(),
                                 key=lambda kv: sec_sort_key(kv[0])):
        seg = text[m.start():seg_end(m)]
        header = seg.split("\n", 1)[0]
        catch_m = re.match(r"[§S]\s*" + re.escape(sid) + r"\s+([^.]*(?:\.|$))",
                           header.strip())
        catchline = dewrap(catch_m.group(1).rstrip(".")) if catch_m else ""
        repealed = bool(re.match(r"(?i)^\(?\s*repealed", catchline.strip()))

    # (loop continues below — kept flat for readability)
        sub = ""
        for pos, label in subchapters:
            if pos < m.start():
                sub = label

        joined = dewrap(seg)
        auth_c, auth_s, auth_e = find_note(joined, "Auth")
        imp_c, imp_s, imp_e = find_note(joined, "Imp")

        src_note, src_span = "", None
        for sm in re.finditer(r"\[[^\]\[]*\]", joined):
            src_note, src_span = sm.group(0), (sm.start(), sm.end())
        if not src_span and auth_s is not None:
            sm = (re.search(r"\[[^\]\[]*?(?=\s*\(" + NOTE_LABEL["Auth"] + r")",
                            joined)
                  or re.search(r"(?:(?<=\.)|(?<=\s))(?:Eff|R)\b[^()\[\]]{0,150}?"
                               r"(?=\s*\(" + NOTE_LABEL["Auth"] + r")", joined))
            if sm:
                src_note, src_span = sm.group(0), (sm.start(), sm.end())
                problems.append({"doc": doc, "chapter": chap, "section": sid,
                                 "kind": "unbracketed_source_note",
                                 "as_printed": src_note[:120]})

        op_end = (src_span[0] if src_span
                  else auth_s if auth_s is not None else len(joined))
        operative = joined[:op_end]
        operative = re.sub(r"^[§S]\s*" + re.escape(sid) + r"\s+[^.]*\.\s*", "",
                           operative).strip()

        annotation = joined[imp_e:].strip() if imp_e else ""
        annotation = re.sub(r"(?i)\bSUBCHAPTER\s+\d+\s+[A-Z0-9 ,;-]+$", "",
                            annotation).strip()
        if annotation and re.match(r"^[§S]\s*" + _HARSEC, annotation):
            annotation = ""
        if annotation:
            problems.append({"doc": doc, "chapter": chap, "section": sid,
                             "kind": "trailing_annotation",
                             "text": annotation[:200]})

        effective = ""
        if src_note:
            dm = DATE_TOKEN.findall(STAMP_ANY.sub(stamp_to_date, src_note))
            if dm:
                effective = dm[-1]

        if not repealed:
            for cond, kind in ((not auth_c, "missing_auth"),
                              (not imp_c, "missing_imp"),
                              (not operative, "empty_operative")):
                if cond:
                    problems.append({"doc": doc, "chapter": chap,
                                     "section": sid, "kind": kind})

        healed = {}
        for zone, rel, content in (("auth", "authorized_by", auth_c),
                                   ("imp", "implements", imp_c)):
            if content:
                content = heal_note(content, sid, zone,
                                    lrb_by_rule.get(sid, set())
                                    if zone == "imp" else set(),
                                    hrs_sections, problems, chap, doc)
            healed[zone] = content or ""
            tokens, leftover = tokenize_note(content or "")
            if leftover:
                problems.append({"doc": doc, "chapter": chap, "section": sid,
                                 "kind": "note_leftover_digits",
                                 "zone": zone, "leftover": leftover,
                                 "note": content})
            for kind, target, rawtok in tokens:
                edges.append({"src": f"har:{sid}", "target": target,
                              "kind": kind, "relation": rel, "zone": zone,
                              "raw": rawtok})

        # ---- operative-zone citations -------------------------------------
        masked = operative

        def mask(mm):
            nonlocal masked
            masked = (masked[:mm.start()] + " " * (mm.end() - mm.start())
                      + masked[mm.end():])

        for mm in list(re.finditer(r"(?:sections?|§§?)?\s*(" + _COLON + r")",
                                   masked)):
            t = mm.group(1).upper()
            if ":" in t:
                edges.append({"src": f"har:{sid}", "target": t,
                              "kind": "hrs_section", "relation": "cites",
                              "zone": "operative", "raw": dewrap(mm.group(0))})
                mask(mm)
        for mm in list(re.finditer(r"(?:sections?|§§?)\s*(" + _HARSEC +
                                   r")\s+(?:to|through)\s+(" + _HARSEC + r")",
                                   masked, re.I)):
            for t in (mm.group(1), mm.group(2)):
                if t != sid:
                    edges.append({"src": f"har:{sid}", "target": f"har:{t}",
                                  "kind": "har_section", "relation": "cites",
                                  "zone": "operative", "raw": dewrap(mm.group(0))})
            mask(mm)
        for mm in list(re.finditer(r"(?:(?:sections?|§§?)\s*)?(" + _HARSEC +
                                   r"(?:\s*(?:,|;|\band\b|\bor\b)\s*" +
                                   _HARSEC + r")*)", masked, re.I)):
            for t in re.findall(_HARSEC, mm.group(1)):
                if t != sid:
                    edges.append({"src": f"har:{sid}", "target": f"har:{t}",
                                  "kind": "har_section", "relation": "cites",
                                  "zone": "operative", "raw": dewrap(mm.group(0))})
            mask(mm)
        for mm in list(re.finditer(r"\bchapters?\s+(\d+[A-Z]?-\d+(?:\.\d+)?"
                                   r"(?:\s*(?:,|;|\band\b|\bor\b)\s*"
                                   r"\d+[A-Z]?-\d+(?:\.\d+)?)*)\b", masked, re.I)):
            for t in re.findall(r"\d+[A-Z]?-\d+(?:\.\d+)?", mm.group(1)):
                if t != chap:
                    edges.append({"src": f"har:{sid}", "target": f"har:ch:{t}",
                                  "kind": "har_chapter", "relation": "cites",
                                  "zone": "operative", "raw": dewrap(mm.group(0))})
            mask(mm)
        for e in hrs_lib.extract_citations(masked):
            edges.append({"src": f"har:{sid}", "target": e["target"],
                          "kind": e["kind"], "relation": "cites",
                          "zone": "operative", "raw": e["raw"]})

        sections[sid] = {
            "catchline": catchline, "subchapter": sub, "repealed": repealed,
            "operative": operative, "source_note": src_note,
            "auth_raw": auth_c or "", "imp_raw": imp_c or "",
            "auth_healed": healed.get("auth", ""),
            "imp_healed": healed.get("imp", ""),
            "annotation": annotation, "effective": effective,
        }

    # ---- strict sweep: zero missed Auth/Imp tokens -------------------------
    edge_set = {(e["src"], e["target"], e["zone"]) for e in edges}
    sweep_missed = 0
    for sid, s in sections.items():
        for zone, content in (("auth", s["auth_healed"]),
                              ("imp", s["imp_healed"])):
            for tok in re.findall(_SEC,
                                  mask_federal(re.sub(_COLON, " ", content))):
                if (f"har:{sid}", tok.upper(), zone) not in edge_set:
                    sweep_missed += 1
                    problems.append({"doc": doc, "chapter": chap,
                                     "section": sid,
                                     "kind": "sweep_missed_token",
                                     "zone": zone, "token": tok})

    # ---- quarantine: parse-integrity failures only -------------------------
    n_live = sum(1 for s in sections.values() if not s["repealed"])
    n_empty = sum(1 for s in sections.values()
                  if not s["repealed"] and not s["operative"])
    hard = []
    if sweep_missed:
        hard.append(f"sweep_missed_token x{sweep_missed}")
    if n_live and n_empty > n_live * 0.3:
        hard.append(f"majority_empty_operative {n_empty}/{n_live}")
        problems.append({"doc": doc, "chapter": chap,
                         "kind": "majority_empty_operative",
                         "empty": n_empty, "live": n_live})
    if toc_present and toc_ids and len(toc_only) > max(2, len(set(toc_ids)) * 0.2):
        hard.append(f"toc_unmatched {len(toc_only)}/{len(set(toc_ids))}")
    if not sections:
        hard.append("no_sections")
    if hard:
        problems.append({"doc": doc, "chapter": chap, "kind": "QUARANTINED",
                         "why": hard, "sections_lost": len(sections)})
        return None

    return {
        "catchline": universe_catchlines.get(chap, ""),
        "retrieved": meta.get("retrieved"),
        "url": meta.get("url"),
        "sha256_pdf": extract_meta.get("sha256_pdf"),
        "source_doc": doc,
        "toc_checked": toc_present,
        "toc_unmatched": toc_only,
        "effective_as_printed": "",
        "historical_note": historical_note,
        "sections": sections,
        "_edges": edges,
    }


def parse_document(key, meta, extract_meta, universe_catchlines,
                   lrb_by_rule, hrs_sections, problems):
    """Parse one extracted document, possibly holding several chapters."""
    txt_path = os.path.join(TXT, key.replace("/", os.sep)[:-4] + ".txt")
    raw = open(txt_path, encoding="utf-8").read()

    pre_ids = [m.group(1) for m in SECTION_START.finditer(normalize_dashes(raw))]
    chapter_nums = set()
    for sid in pre_ids:
        m = HARSEC_RE.match(sid)
        if m:
            chapter_nums.add(f"{m.group(1)}-{m.group(2)}")
    if not chapter_nums:
        problems.append({"doc": key, "kind": "no_har_sections",
                         "chars": len(raw), "hint": meta.get("hint"),
                         "note": "ancillary or amendment memo"})
        return {}

    pages = [strip_page(p, {c.split('-', 1)[1] for c in chapter_nums})
             for p in raw.split("\f")]
    text = normalize_dashes("\n".join(pages))

    for chap in sorted(chapter_nums, key=sec_sort_key):
        for rx, repl in header_repairs(chap):
            def _repair(m, _repl=repl):
                fixed = m.expand(_repl)
                if fixed != m.group(0):
                    problems.append({"doc": key, "chapter": chap,
                                     "kind": "source_misprint_repaired",
                                     "as_printed": m.group(0).strip(),
                                     "read_as": fixed.strip()})
                return fixed
            text = rx.sub(_repair, text)

    # two passes: parse, then TOC-corroborated header repair, then re-parse
    out = {}
    for attempt in range(2):
        all_matches = list(SECTION_START.finditer(text))
        all_starts = sorted(m.start() for m in all_matches)
        by_chapter = defaultdict(list)
        for m in all_matches:
            hm = HARSEC_RE.match(m.group(1))
            if hm:
                by_chapter[f"{hm.group(1)}-{hm.group(2)}"].append(m)

        if attempt == 0:
            hint = meta.get("hint")
            if hint and by_chapter and hint not in by_chapter:
                problems.append({"doc": key, "kind": "hint_mismatch",
                                 "hint": hint,
                                 "found": sorted(by_chapter, key=sec_sort_key)})
            # find repairs needed
            repaired = 0
            for chap, matches in by_chapter.items():
                split_i, toc_present = best_split(matches)
                if not toc_present:
                    continue
                toc_ids = set(m.group(1) for m in matches[:split_i])
                body_ids = set(m.group(1) for m in matches[split_i:])
                missing = sorted(toc_ids - body_ids)
                if missing:
                    text, n = repair_missing_headers(text, chap, missing,
                                                     problems, key)
                    repaired += n
            if repaired == 0:
                pass            # nothing to redo; fall through to final parse
        # final pass (or first pass when no repairs applied)
        if attempt == 1 or repaired == 0:
            scratch = []
            for chap, matches in sorted(by_chapter.items(),
                                        key=lambda kv: sec_sort_key(kv[0])):
                rec = parse_chapter(chap, text, all_starts, matches, meta,
                                    extract_meta, universe_catchlines,
                                    lrb_by_rule, hrs_sections, problems, key)
                if rec is not None:
                    out[chap] = rec
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--titles", help="comma list, default all")
    args = ap.parse_args()
    want = set(int(x) for x in args.titles.split(",")) if args.titles else None

    manifest = json.load(open(os.path.join(RAW_PDF, "_downloads.json"),
                              encoding="utf-8"))
    extract = json.load(open(os.path.join(TXT, "_extract.json"),
                             encoding="utf-8"))

    uni = json.load(open(os.path.join(GRAPH, "har-universe.json"),
                         encoding="utf-8-sig"))
    universe_catchlines, universe_chapters = {}, set()
    tt = uni["titles"]
    for t in (tt.values() if isinstance(tt, dict) else tt):
        for ch in t.get("chapters", []):
            cid = str(ch["chapter"])
            universe_chapters.add(cid)
            universe_catchlines.setdefault(cid, ch.get("catchline") or "")

    lrb = json.load(open(os.path.join(GRAPH, "har-edges.json"),
                         encoding="utf-8-sig"))
    lrb_by_rule = defaultdict(set)
    for e in lrb.get("edges", []):
        if e.get("rel") == "implements" and e.get("dst_kind") == "hrs_section":
            lrb_by_rule[str(e["src"])].add(str(e["dst"]).upper())

    hrs_sections = {k.upper() for k in json.load(
        open(os.path.join(GRAPH, "sections.json"),
             encoding="utf-8"))["sections"]}

    problems = []
    chapters, edges_by_chap = {}, {}
    doc_count = 0
    for key, meta in sorted(manifest.items()):
        if meta.get("status") not in ("ok", "ok_archived"):
            continue
        if want and meta.get("title") not in want:
            continue
        ex = extract.get(key)
        if not ex or ex.get("status") != "ok":
            problems.append({"doc": key, "kind": "no_extraction",
                             "detail": (ex or {}).get("error", "missing")})
            continue
        if ex.get("chars", 0) < 500:
            problems.append({"doc": key, "kind": "no_text_layer",
                             "chars": ex.get("chars", 0),
                             "hint": meta.get("hint"),
                             "note": "likely a scan; needs OCR"})
            continue
        doc_count += 1
        got = parse_document(key, meta, ex, universe_catchlines,
                             lrb_by_rule, hrs_sections, problems)
        # an out-of-universe chapter with a handful of sections, minted from
        # a document that also parsed a real (LRB-listed) chapter, is an OCR
        # distortion of that chapter's headers, not a discovery — drop it,
        # recorded. Substantial out-of-universe chapters are KEPT (the Table
        # trails the rules it compiles) and recorded separately.
        best_known = max((len(r["sections"]) for c, r in got.items()
                          if c in universe_chapters), default=0)
        for chap in [c for c in got
                     if c not in universe_chapters
                     and len(got[c]["sections"]) <= 3
                     and best_known > len(got[c]["sections"])]:
            problems.append({"kind": "chapter_ocr_suspect", "chapter": chap,
                             "doc": key,
                             "sections": sorted(got[chap]["sections"]),
                             "note": "out-of-universe stray beside a parsed "
                                     "LRB-listed chapter; dropped"})
            del got[chap]
        for chap, rec in got.items():
            edges = rec.pop("_edges")
            if chap in chapters:
                prev = chapters[chap]
                keep_new = len(rec["sections"]) > len(prev["sections"])
                problems.append({"kind": "chapter_duplicate_docs",
                                 "chapter": chap,
                                 "docs": [prev["source_doc"], rec["source_doc"]],
                                 "kept": rec["source_doc"] if keep_new
                                         else prev["source_doc"]})
                if not keep_new:
                    continue
            if chap not in universe_chapters:
                problems.append({"kind": "chapter_not_in_lrb_universe",
                                 "chapter": chap, "doc": rec["source_doc"]})
            chapters[chap] = rec
            edges_by_chap[chap] = edges
    all_edges = [e for chap in sorted(edges_by_chap, key=sec_sort_key)
                 for e in edges_by_chap[chap]]

    # ---- LRB crosswalk cross-check (two attestations; disagreement = finding)
    # Compared ONLY for sections actually read: a section we never parsed
    # cannot attest anything, so an LRB entry for it is a COVERAGE GAP
    # (chapter_partial_vs_lrb), not a disagreement. Excerpt documents (fee
    # amendments carrying 2 of a chapter's 58 sections) surface here.
    ours_by_rule = defaultdict(set)
    for e in all_edges:
        if e["zone"] == "imp" and e["kind"] == "hrs_section":
            ours_by_rule[e["src"][4:]].add(e["target"])
    parsed_sections = {sid for c in chapters.values() for sid in c["sections"]}
    agree = disagree = 0
    missing_by_chap = defaultdict(list)
    for rule in sorted(set(lrb_by_rule) | set(ours_by_rule)):
        hm = HARSEC_RE.match(rule)
        if not hm or f"{hm.group(1)}-{hm.group(2)}" not in chapters:
            continue
        if rule not in parsed_sections:
            missing_by_chap[f"{hm.group(1)}-{hm.group(2)}"].append(rule)
            continue
        a, b = lrb_by_rule.get(rule, set()), ours_by_rule.get(rule, set())
        if a == b:
            agree += 1
        else:
            disagree += 1
            problems.append({"kind": "lrb_crosswalk_disagreement", "rule": rule,
                             "lrb_only": sorted(a - b),
                             "rule_text_only": sorted(b - a)})
    for chap, missing in sorted(missing_by_chap.items()):
        n_lrb = sum(1 for r in lrb_by_rule
                    if HARSEC_RE.match(r)
                    and r.rsplit("-", 1)[0] == chap)
        problems.append({"kind": "chapter_partial_vs_lrb", "chapter": chap,
                         "doc": chapters[chap]["source_doc"],
                         "sections_read": len(chapters[chap]["sections"]),
                         "lrb_expects": n_lrb,
                         "missing": missing[:20],
                         "n_missing": len(missing)})

    n_secs = sum(len(c["sections"]) for c in chapters.values())
    quarantined = [p for p in problems if p["kind"] == "QUARANTINED"]
    print(f"docs parsed: {doc_count}; chapters kept: {len(chapters)} "
          f"({n_secs} sections, {len(all_edges)} edges); "
          f"quarantined: {len(quarantined)}; "
          f"LRB cross-check: {agree} agree / {disagree} differ; "
          f"problems: {len(problems)}")

    out = {"built": time.strftime("%Y-%m-%d"), "chapters": chapters,
           "edges": all_edges}
    with open(os.path.join(GRAPH, "har-rules.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    with open(os.path.join(GRAPH, "har_text_problems.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(problems, fh, indent=1, ensure_ascii=False)
        fh.write("\n")

    if not chapters:
        print("NOTHING PARSED — batch fails", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
