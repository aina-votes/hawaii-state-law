"""Parse extracted HAR rule text into sections, zones, and typed edges.

    python tools/har_rules.py

Reads  raw/har/har-<chapter>.txt  (verbatim, from tools/har_text.py)
Writes graph/har-rules.json          sections + typed edges
       graph/har_text_problems.json  every validation exception, or []

Zones (schema rule 11): operative / source / auth / imp / annotation.
Auth and Imp are different relations and never merge (authorized_by vs
implements). Both are the ADOPTING AGENCY'S assertion, not the revisor's.

Design notes, each from something observed in the actual PDFs:

* Furniture is stripped at PARSE time; raw/ stays verbatim. Every body page
  carries a running header (a bare "§3-160-4" line, once misprinted
  "§-160-31"), a printed page number ("160-5", drifting between y=688 and
  y=720), and a large received-date stamp that extracts as garbage ("3210",
  "} 11"). A junk-shaped trailing line is only dropped when it cannot be a
  wrapped citation fragment - "11-410)" at a page break must survive.
* Auth/Imp notes are citation lists BY CONSTRUCTION, so they are tokenised
  exhaustively rather than pattern-matched: the print drops list commas
  ("11-314 (7) 11-407"), and a grammar-based matcher silently loses the
  tail of the list. The strict sweep asserts zero tokens missed.
* Auth/Imp spans need balanced-paren scanning: "(Auth: HRS §11-314 (8))"
  nests. A [^)]* regex truncates at the pin cite.
* HAR self-references are extracted and MASKED before running the HRS
  citation extractor: hrs_lib's section regex would read "3-160-14" as
  HRS §3-160 plus debris.
* The received-date stamp bleeds into source notes as "DEC 0 9 2016" or
  "DEC092016" (a physical stamp, not typeset text). Normalised only in the
  derived `effective` field; the note itself stays as printed.
"""
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from har_lib import GRAPH, RAW_HAR, normalize_dashes
import hrs_lib

CHAPTER_FILES = ["har-3-160.txt", "har-3-161.txt"]

_SEC = r"\d+[A-Z]?-\d+(?:\.\d+)?"          # an HRS section token
_HARSEC = r"3-16[01]-\d+(?:\.\d+)?"        # a HAR section in these chapters

RUNNING_HEADER = re.compile(r"^§\s*\d*-16[01]-\d+(?:\.\d+)?\s*$")
PAGE_NUMBER = re.compile(r"^16[01]-\d+$")
# junk that cannot be a wrapped citation: no letters beyond 2, short, and NOT
# shaped like a section number ("11-410)" survives, "3210" and "} 11" do not)
TRAILING_JUNK = re.compile(r"^[\W\d]*[A-Za-z]{0,2}[\W\d]*$")
CITE_SHAPED = re.compile(r"\d+[A-Z]?-\d+")
TINY_JUNK = re.compile(r"^[^A-Za-z]{1,3}$")

SECTION_START = re.compile(r"(?m)^§(" + _HARSEC + r")\s+(\S.*)$")
# TOC prints "Subchapter 1 General Provisions"; the body prints
# "SUBCHAPTER 2 REGISTRATION, ..." in caps. Match both.
SUBCHAPTER = re.compile(r"(?mi)^SUBCHAPTER\s+(\d+)\s+(.+?)\s*$")
# any three-component cite is HAR, never HRS — including cross-title ones
# like "section 2-71-31, Hawaii Administrative Rules" (OIP records rules,
# cited from §3-160-10). Masked before the HRS extractor runs, which would
# otherwise mint a phantom HRS §2-71.
_ANYHARSEC = r"\d+[A-Z]?-\d+(?:\.\d+)?-\d+(?:\.\d+)?"

# the physical received stamp: DEC092016, DEC 0 9 2016, DECO 9 2016,
# nEC 09 2016 ... — a rubber stamp, so the OCR mangles it a new way on
# nearly every page. First letter and 0/O are both unreliable.
STAMP = re.compile(r"\b[A-Za-z]EC\s*[O0]\s*9\s*[,.]?\s*2\s*0\s*1\s*6")

# Text-layer misprints in the source PDF that break section segmentation.
# Repaired at parse time ONLY (raw/ stays verbatim), and every repair is
# logged to the problems file. Same policy as the LRB directory defects:
# a targeted, recorded repair beats both silent loss and silent guessing.
HEADER_REPAIRS = [
    # digits split inside a section number: "§3-160-4 0 Expenditures"
    (re.compile(r"(?m)^§(3-16[01]-\d+)\s(\d(?:\.\d+)?)\s+(?=[A-Z(\"'])"),
     r"§\1\2 "),
    # a hyphen dropped from the id: "§3 161-41 ..." / "§3-161 51 ..."
    (re.compile(r"(?m)^§\s*3[\s-]16([01])[\s-](\d+(?:\.\d+)?)\b"),
     r"§3-16\1-\2"),
]


def strip_page(page_text):
    """Remove running header / page number / stamp from one page's lines."""
    lines = page_text.split("\n")
    if lines and RUNNING_HEADER.match(lines[0].strip()):
        lines = lines[1:]
    # walk the tail: cut at a page-number line in the last 3 lines if present
    tail_start = max(0, len(lines) - 3)
    cut = None
    for i in range(len(lines) - 1, tail_start - 1, -1):
        if PAGE_NUMBER.match(lines[i].strip()):
            cut = i
            break
    if cut is not None:
        # a stray stamp digit sometimes sits just above the page number
        if cut > 0 and TINY_JUNK.match(lines[cut - 1].strip()):
            cut -= 1
        lines = lines[:cut]
    else:
        last = lines[-1].strip() if lines else ""
        if (len(last) <= 8 and TRAILING_JUNK.match(last)
                and not CITE_SHAPED.search(last)):
            lines = lines[:-1]
    return "\n".join(lines)


def dewrap(s):
    """Whitespace-join and heal hyphen-wrapped section numbers: '11-\\n359'."""
    s = " ".join(s.split())
    return re.sub(r"-\s+(?=\d)", "-", s)


def balanced_span(text, start):
    """Return end index of the paren group opening at text[start] == '('."""
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
    """Locate '(Auth: ...)' / '(Imp: ...)' with balanced parens.
    Returns (content, start, end) or (None, None, None)."""
    m = re.search(r"\(\s*" + label + r"\s*:", joined)
    if not m:
        return None, None, None
    end = balanced_span(joined, m.start())
    # print defect (§3-160-10): the Auth note drops its closing paren, so a
    # balanced scan runs off into the Imp note. '(Imp:' always closes Auth.
    nxt = re.search(r"\(\s*Imp\s*:", joined[m.end():])
    nxt_abs = m.end() + nxt.start() if nxt else None
    if label == "Auth" and nxt_abs is not None and (end is None or end > nxt_abs):
        content = joined[m.end():nxt_abs].strip().rstrip(")( ").strip()
        return content, m.start(), nxt_abs
    if end is None:
        return None, None, None
    content = joined[m.end():end - 1].strip()
    return content, m.start(), end


def tokenize_note(content):
    """Every HRS section / chapter cite in an Auth/Imp note, exhaustively.
    Returns (tokens, leftover): leftover holds any digit-bearing residue the
    tokenizer could not claim — a dropped-hyphen cite like '91 4.2' must
    surface as a problem, not vanish (both the grammar and a same-regex sweep
    would miss it identically)."""
    out = []
    masked = content
    for m in re.finditer(r"\bchapters?\s+(\d+[A-Z]?)\b", content, re.I):
        out.append(("hrs_chapter", "ch:" + m.group(1).upper(), m.group(0)))
        masked = masked[:m.start()] + " " * (m.end() - m.start()) + masked[m.end():]
    masked2 = masked
    for m in re.finditer(_SEC, masked):
        out.append(("hrs_section", m.group(0).upper(), m.group(0)))
    masked2 = re.sub(_SEC, " ", masked2)
    # strip everything that legitimately surrounds cites; digits that survive
    # are an unclaimed citation fragment. Pin cites "(8)" must be claimed as a
    # unit BEFORE the char class can eat the parens and orphan the digit.
    residue = re.sub(r"(?i)\bHRS\b|\bHawaii Revised Statutes\b|\(\s*\d+\s*\)|"
                     r"\.\d+|\band\b|\bor\b|[§,;()'\s]", " ", masked2)
    leftover = " ".join(residue.split())
    leftover = leftover if re.search(r"\d", leftover) else ""
    return out, leftover


def heal_note(content, sid, zone, lrb_expected, hrs_sections, problems, chapter):
    """Repair print-defect-broken citations inside an Auth/Imp note, with
    corroboration only — never a guess:

    1. LRB-driven: if the LRB Table lists a cite for this rule that the note's
       tokens miss, and a tolerant match (up to 4 junk chars where the hyphen
       should be) finds it in the note, canonicalise it. Consumes glued stamp
       digits too: '11-4071' and '11-1 410' both heal to the LRB's cite.
    2. Corpus-driven: 'A B' with a space heals to 'A-B' only if A-B is a
       section our harvested HRS corpus actually contains.

    Every heal is logged to the problems file."""
    def log(before, after):
        problems.append({"chapter": chapter, "section": sid, "zone": zone,
                         "kind": "note_cite_healed",
                         "as_printed": before, "read_as": after})

    have = {t.upper() for t in re.findall(_SEC, content)}
    for want in sorted(lrb_expected - have):
        m = re.match(r"^(\d+[A-Z]?)-(\d+(?:\.\d+)?)$", want)
        if not m:
            continue
        head, tail = m.group(1), m.group(2)
        rx = re.compile(re.escape(head) + r"(?:-?\s?[Il1]?\s?[-\s]|\s)" +
                        re.escape(tail).replace(r"\.", r"\.") + r"(\d?)\b")
        hit = rx.search(content)
        if hit:
            log(hit.group(0).strip(), want)
            content = content[:hit.start()] + " " + want + " " + content[hit.end():]
        else:
            # stamp digit glued straight onto the cite: '11-4071' for 11-407
            rx2 = re.compile(re.escape(want) + r"(\d)\b")
            hit2 = rx2.search(content)
            if hit2 and hit2.group(0).upper() not in hrs_sections:
                log(hit2.group(0), want)
                content = content[:hit2.start()] + want + " " + content[hit2.end():]
    # generic dropped hyphen, corpus-corroborated (covers Auth, no LRB there)
    def _join(m):
        cand = f"{m.group(1)}-{m.group(2)}".upper()
        if cand in hrs_sections:
            log(m.group(0), cand)
            return " " + cand
        return m.group(0)
    content = re.sub(r"\b(\d+[A-Z]?)\s+(\d+(?:\.\d+)?)\b(?!\s*U\.?S)", _join, content)
    return content


def parse_chapter(fname, problems, lrb_by_rule, hrs_sections):
    chapter = fname[len("har-"):-len(".txt")]
    raw = open(os.path.join(RAW_HAR, fname), encoding="utf-8").read()
    pages = [strip_page(p) for p in raw.split("\f")]
    text = normalize_dashes("\n".join(pages))

    for rx, repl in HEADER_REPAIRS:
        def _repair(m, _rx=rx, _repl=repl):
            fixed = m.expand(_repl)
            if fixed != m.group(0):
                problems.append({"chapter": chapter,
                                 "kind": "source_misprint_repaired",
                                 "as_printed": m.group(0).strip(),
                                 "read_as": fixed.strip()})
            return fixed
        text = rx.sub(_repair, text)

    # ---- segment on section headers ---------------------------------------
    # TOC and body both use "§3-160-N Catchline" lines; the chapter-level
    # "Historical note:" paragraph sits between them and belongs to neither.
    hist_pos = text.find("Historical note:")
    if hist_pos == -1:
        problems.append({"chapter": chapter, "kind": "no_body_found",
                         "detail": "no 'Historical note:' TOC/body divider"})
        return chapter, {}, [], ""

    starts = list(SECTION_START.finditer(text))
    segments = []
    for i, m in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
        segments.append((m.group(1), m.start(), end))

    toc_ids = [sid for sid, a, b in segments if a < hist_pos]
    body_segs = [(sid, a, b) for sid, a, b in segments if a > hist_pos]
    body_ids = [sid for sid, a, b in body_segs]
    hist_end = body_segs[0][1] if body_segs else len(text)
    historical_note = dewrap(text[hist_pos:hist_end])

    # ground truth: the chapter's own table of contents
    if set(toc_ids) != set(body_ids):
        problems.append({
            "chapter": chapter, "kind": "toc_body_mismatch",
            "toc_only": sorted(set(toc_ids) - set(body_ids)),
            "body_only": sorted(set(body_ids) - set(toc_ids)),
        })
    dupes = {x for x in body_ids if body_ids.count(x) > 1}
    if dupes:
        problems.append({"chapter": chapter, "kind": "duplicate_section",
                         "ids": sorted(dupes)})

    # subchapter headings, positional
    subchapters = [(m.start(), f"Subchapter {m.group(1)} — {m.group(2).strip()}")
                   for m in SUBCHAPTER.finditer(text)
                   if m.start() >= body_segs[0][1]]

    sections, edges = {}, []
    for sid, a, b in body_segs:
        seg = text[a:b]
        header = seg.split("\n", 1)[0]
        catch_m = re.match(r"§" + re.escape(sid) + r"\s+([^.]*(?:\.|$))", header)
        catchline = dewrap(catch_m.group(1).rstrip(".")) if catch_m else ""
        repealed = catchline.strip().lower().startswith("repealed")

        sub = ""
        for pos, label in subchapters:
            if pos < a:
                sub = label

        joined = dewrap(seg)

        auth_c, auth_s, auth_e = find_note(joined, "Auth")
        imp_c, imp_s, imp_e = find_note(joined, "Imp")

        # source note: the LAST [...] group. Two observed OCR failures need
        # fallbacks: the closing "]" prints as "l" (§3-160-39), and the
        # opening "[" vanishes entirely (§3-161-31). Both logged.
        src_note, src_span = "", None
        for m in re.finditer(r"\[[^\]\[]*\]", joined):
            src_note, src_span = m.group(0), (m.start(), m.end())
        if not src_span and auth_s is not None:
            m = (re.search(r"\[[^\]\[]*?(?=\s*\(Auth)", joined)
                 or re.search(r"(?:(?<=\.)|(?<=\s))(?:Eff|R)\b[^()\[\]]{0,150}?"
                              r"(?=\s*\(Auth)", joined))
            if m:
                src_note, src_span = m.group(0), (m.start(), m.end())
                problems.append({"chapter": chapter, "section": sid,
                                 "kind": "unbracketed_source_note",
                                 "as_printed": src_note[:120]})

        op_end = (src_span[0] if src_span
                  else auth_s if auth_s is not None else len(joined))
        operative = joined[:op_end]
        operative = re.sub(r"^§" + re.escape(sid) + r"\s+[^.]*\.\s*", "",
                           operative).strip()

        annotation = joined[imp_e:].strip() if imp_e else ""
        # a subchapter heading between sections is structure, not annotation
        annotation = re.sub(r"(?i)\bSUBCHAPTER\s+\d+\s+[A-Z0-9 ,;-]+$", "",
                            annotation).strip()
        if annotation:
            problems.append({"chapter": chapter, "section": sid,
                             "kind": "trailing_annotation",
                             "text": annotation[:200]})

        effective = ""
        if src_note:
            norm = STAMP.sub("12/9/2016", src_note)
            dm = re.findall(r"\d{1,2}/\d{1,2}/\d{2,4}", norm)
            if dm:
                effective = dm[-1]      # last event in the note = current text

        if not repealed:
            if not auth_c:
                problems.append({"chapter": chapter, "section": sid,
                                 "kind": "missing_auth"})
            if not imp_c:
                problems.append({"chapter": chapter, "section": sid,
                                 "kind": "missing_imp"})
            if not operative:
                problems.append({"chapter": chapter, "section": sid,
                                 "kind": "empty_operative"})

        healed = {}
        for zone, rel, content in (("auth", "authorized_by", auth_c),
                                   ("imp", "implements", imp_c)):
            if content:
                content = heal_note(content, sid, zone,
                                    lrb_by_rule.get(sid, set()) if zone == "imp"
                                    else set(),
                                    hrs_sections, problems, chapter)
            healed[zone] = content or ""
            tokens, leftover = tokenize_note(content or "")
            if leftover:
                problems.append({"chapter": chapter, "section": sid,
                                 "kind": "note_leftover_digits",
                                 "zone": zone, "leftover": leftover,
                                 "note": content})
            for kind, target, rawtok in tokens:
                edges.append({"src": f"har:{sid}", "target": target,
                              "kind": kind, "relation": rel, "zone": zone,
                              "raw": rawtok})

        # ---- operative-zone citations -------------------------------------
        # HAR cites are claimed and masked FIRST: any three-component number
        # is HAR, and the HRS extractor would shred it into phantom edges.
        masked = operative

        def mask(m):
            nonlocal masked
            masked = masked[:m.start()] + " " * (m.end() - m.start()) + masked[m.end():]

        # ranges: "sections 3-161-32 to 3-161-51"
        for m in list(re.finditer(r"(?:sections?|§§?)\s*(" + _ANYHARSEC +
                                  r")\s+(?:to|through)\s+(" + _ANYHARSEC + r")",
                                  masked, re.I)):
            for t in (m.group(1), m.group(2)):
                if t != sid:
                    edges.append({"src": f"har:{sid}", "target": f"har:{t}",
                                  "kind": "har_section", "relation": "cites",
                                  "zone": "operative", "raw": dewrap(m.group(0))})
            mask(m)
        # singles/lists, with or without a section/§ prefix
        for m in list(re.finditer(r"(?:(?:sections?|§§?)\s*)?(" + _ANYHARSEC +
                                  r"(?:\s*(?:,|;|\band\b|\bor\b)\s*" +
                                  _ANYHARSEC + r")*)", masked, re.I)):
            for t in re.findall(_ANYHARSEC, m.group(1)):
                if t != sid:
                    edges.append({"src": f"har:{sid}", "target": f"har:{t}",
                                  "kind": "har_section", "relation": "cites",
                                  "zone": "operative", "raw": dewrap(m.group(0))})
            mask(m)
        # HAR chapter refs: hyphenated chapter numbers are HAR, never HRS
        for m in list(re.finditer(r"\bchapters?\s+(\d+[A-Z]?-\d+(?:\.\d+)?"
                                  r"(?:\s*(?:,|;|\band\b|\bor\b)\s*"
                                  r"\d+[A-Z]?-\d+(?:\.\d+)?)*)\b", masked, re.I)):
            for t in re.findall(r"\d+[A-Z]?-\d+(?:\.\d+)?", m.group(1)):
                if t != chapter:
                    edges.append({"src": f"har:{sid}", "target": f"har:ch:{t}",
                                  "kind": "har_chapter", "relation": "cites",
                                  "zone": "operative", "raw": dewrap(m.group(0))})
            mask(m)
        # bare self-chapter mentions like "this chapter" carry no target; skip.
        # now the HRS extractor on the masked text
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
    swept = 0
    edge_set = {(e["src"], e["target"], e["zone"]) for e in edges}
    for sid, s in sections.items():
        for zone, content in (("auth", s["auth_healed"]), ("imp", s["imp_healed"])):
            for tok in re.findall(_SEC, content):
                swept += 1
                if (f"har:{sid}", tok.upper(), zone) not in edge_set:
                    problems.append({"chapter": chapter, "section": sid,
                                     "kind": "sweep_missed_token",
                                     "zone": zone, "token": tok})
    print(f"{chapter}: {len(sections)} sections "
          f"({sum(1 for s in sections.values() if s['repealed'])} repealed), "
          f"{len(edges)} edges, sweep checked {swept} note tokens")
    return chapter, sections, edges, historical_note


def load_lrb_by_rule():
    lrb = json.load(open(os.path.join(GRAPH, "har-edges.json"),
                         encoding="utf-8-sig"))
    out = defaultdict(set)
    for e in lrb.get("edges", []):
        if (e.get("rel") == "implements" and e.get("dst_kind") == "hrs_section"
                and re.match(r"^3-16[01]-", str(e.get("src", "")))):
            out[str(e["src"])].add(str(e["dst"]).upper())
    return out


def main():
    problems = []
    chapters, all_edges = {}, []
    lrb_by_rule = load_lrb_by_rule()
    hrs_sections = {k.upper() for k in json.load(
        open(os.path.join(GRAPH, "sections.json"),
             encoding="utf-8"))["sections"]}
    for fname in CHAPTER_FILES:
        chapter, sections, edges, historical_note = parse_chapter(
            fname, problems, lrb_by_rule, hrs_sections)
        manifest = json.load(open(os.path.join(RAW_HAR, "_manifest.json"),
                                  encoding="utf-8"))
        meta = manifest[fname.replace(".txt", "") + ".txt"]
        chapters[chapter] = {
            "catchline": meta["catchline"], "retrieved": meta["retrieved"],
            "url": meta["url"], "sha256_pdf": meta["sha256_pdf"],
            "effective_as_printed": meta["effective_as_printed"],
            "historical_note": historical_note,
            "sections": sections,
        }
        all_edges.extend(edges)

    # ---- cross-check imp edges against the LRB crosswalk -------------------
    # Two independent attestations of the same relation: the rule's own note
    # (parsed here) vs the LRB's 2025 Table (graph/har-edges.json). Where they
    # disagree that is a FINDING to report, never normalise (schema rule 12).
    ours_by_rule = defaultdict(set)
    for e in all_edges:
        if e["zone"] == "imp" and e["kind"] == "hrs_section":
            ours_by_rule[e["src"][4:]].add(e["target"])
    agree = disagree = 0
    for rule in sorted(set(lrb_by_rule) | set(ours_by_rule)):
        a, b = lrb_by_rule.get(rule, set()), ours_by_rule.get(rule, set())
        if a == b:
            agree += 1
        else:
            disagree += 1
            problems.append({"kind": "lrb_crosswalk_disagreement",
                             "rule": rule,
                             "lrb_only": sorted(a - b),
                             "rule_text_only": sorted(b - a)})
    print(f"LRB crosswalk cross-check: {agree} rules agree, {disagree} differ "
          f"(differences are findings, kept in problems file)")

    out = {"built": "2026-07-25", "chapters": chapters, "edges": all_edges}
    with open(os.path.join(GRAPH, "har-rules.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    with open(os.path.join(GRAPH, "har_text_problems.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(problems, fh, indent=1, ensure_ascii=False)
        fh.write("\n")

    hard = [p for p in problems if p["kind"] in
            ("toc_body_mismatch", "duplicate_section", "sweep_missed_token",
             "no_body_found", "empty_operative")]
    print(f"problems: {len(problems)} total, {len(hard)} hard")
    if hard:
        for p in hard[:20]:
            print("  HARD:", p)
        sys.exit(1)


if __name__ == "__main__":
    main()
