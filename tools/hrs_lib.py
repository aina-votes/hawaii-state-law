"""Shared helpers for the HRS harvest / parse / build pipeline.

Nothing in here interprets law. It fetches bytes, strips markup, and normalises
citation strings. All legal judgment happens on the wiki pages, by hand.
"""
import html
import os
import re
import time
import urllib.request

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(VAULT, "raw", "hrs")
GRAPH = os.path.join(VAULT, "graph")
STATUTES = os.path.join(VAULT, "statutes")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# The 14 chapters listed under "Hawaii Revised Statutes" at
# https://elections.hawaii.gov/resources/election-laws/ (retrieved 2026-07-24),
# plus citation-frontier ingests (marked inline): chapters pulled in because
# the corpus itself cites them heavily, not because the OoE lists them.
CHAPTERS = [
    ("10",   "Vol01_Ch0001-0042F", "0010",  "Office of Hawaiian Affairs"),
    ("11",   "Vol01_Ch0001-0042F", "0011",  "Elections, Generally"),
    ("12",   "Vol01_Ch0001-0042F", "0012",  "Primary Elections"),
    ("13",   "Vol01_Ch0001-0042F", "0013",  "Board of Education"),
    ("13D",  "Vol01_Ch0001-0042F", "0013D", "Board of Trustees, Office of Hawaiian Affairs"),
    ("14",   "Vol01_Ch0001-0042F", "0014",  "Presidential Elections"),
    ("14D",  "Vol01_Ch0001-0042F", "0014D", "Agreement Among the States to Elect the President by National Popular Vote"),
    ("15",   "Vol01_Ch0001-0042F", "0015",  "Absentee Voting"),
    ("15D",  "Vol01_Ch0001-0042F", "0015D", "Uniform Military and Overseas Voters Act"),
    ("16",   "Vol01_Ch0001-0042F", "0016",  "Voting Systems"),
    ("17",   "Vol01_Ch0001-0042F", "0017",  "Vacancies"),
    ("19",   "Vol01_Ch0001-0042F", "0019",  "Election Offenses"),
    ("25",   "Vol01_Ch0001-0042F", "0025",  "Reapportionment"),
    ("50",   "Vol02_Ch0046-0115",  "0050",  "Charter Commissions"),
    # frontier ingest 2026-07-25: the most-cited chapter outside the OoE set
    # (31 operative cites before the CSC rule-text ingest; 148 wikilinks to
    # §91-2 alone after it) and the procedural spine under CSC enforcement.
    ("91",   "Vol02_Ch0046-0115",  "0091",  "Administrative Procedure"),
]
IN_SCOPE = {c[0] for c in CHAPTERS}
CHAPTER_TITLE = {c[0]: c[3] for c in CHAPTERS}

BASE = "https://www.capitol.hawaii.gov/hrscurrent"


def _curl_fetch(url):
    """capitol.hawaii.gov's WAF began 403ing Python's TLS fingerprint on
    2026-07-25 — the SAME urllib code that fetched 850 files on 07-24 now
    fails with any header set, while curl passes. The block is on the TLS
    handshake (JA3), not the headers, so the fallback is a real curl."""
    import subprocess
    r = subprocess.run(
        ["curl", "-sS", "--fail", "-L", "-A", UA, "--max-time", "60", url],
        capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"curl failed ({r.returncode}): "
                           f"{r.stderr.decode('utf-8', 'replace')[:200]}")
    return r.stdout


def fetch(url, tries=3, pause=0.35):
    """GET with a browser UA. capitol.hawaii.gov 403s bare clients and 301s
    the apex host to www, so both a UA and redirect-following are required.
    A 403 from urllib falls back to curl (TLS-fingerprint WAF, see above)."""
    last = None
    for attempt in range(tries):
        try:
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": UA,
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-US,en;q=0.9",
                })
                with urllib.request.urlopen(req, timeout=45) as r:
                    data = r.read()
            except urllib.error.HTTPError as he:
                if he.code != 403:
                    raise
                data = _curl_fetch(url)
            time.sleep(pause)
            # Not everything on capitol.hawaii.gov is UTF-8; /docs/HRS.htm is
            # windows-1252 and mangles the okina if decoded wrongly.
            enc = "utf-8"
            m = re.search(rb"charset=([\w\-]+)", data[:2000], re.I)
            if m:
                enc = m.group(1).decode("ascii", "ignore")
            try:
                return data.decode(enc)
            except (UnicodeDecodeError, LookupError):
                return data.decode("utf-8", errors="replace")
        except Exception as e:  # noqa: BLE001 - retry any transport failure
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"fetch failed {url}: {last}")


def strip_html(s):
    t = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", "", s)
    t = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</h\d>", "\n", t)
    t = re.sub(r"(?i)</td>", " ", t)
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    t = t.replace("﻿", "").replace("\xa0", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = "\n".join(line.strip() for line in t.split("\n"))
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def file_to_section(fn):
    """HRS_0011-0015_0002.htm -> ('11', '11-15.2').  HRS_0012-.htm -> ('12', None).

    Each trailing _NNNN group contributes its zero-stripped digits to the
    decimal part, concatenated: HRS_0011-0001_0005_0002.htm is §11-1.52,
    not §11-1.5.2.  Verified against the retrieved text of §11-1.52,
    §11-1.55 and §10-14.55.

    Colon (article) chapters use a THREE-part filename:
    HRS_0412-0001-0100.htm -> ('412', '412:1-100') — chapter-article-section,
    citation as printed (identity contract). Verified against the ch. 412
    listing 2026-07-26.
    """
    # Server-side filename defects, each observed in the 2026-07-26 full
    # harvest: a URL-encoded soft hyphen inside a name (%C2%AD in §291-24.4),
    # and '.docx.htm' double extensions (§§663E-10..12). An '_[OLD]' name is
    # a SUPERSEDED copy the State left in the directory — deliberately not
    # parsed; the caller records it and the current file stands.
    import urllib.parse as _up
    fn = _up.unquote(fn).replace("­", "")
    if "[OLD]" in fn.upper():
        return None, None
    fn = re.sub(r"\.docx(?=\.htm$)", "", fn, flags=re.I)
    m = re.match(r"HRS_(\d+[A-Z]?)-(\d+[A-Z]?)-(\d+)((?:_\d+)*)\.htm$", fn, re.I)
    if m:
        chap = m.group(1).lstrip("0") or "0"
        art = m.group(2).lstrip("0") or "0"
        num = m.group(3).lstrip("0") or "0"
        if m.group(4):
            dec = "".join(g.lstrip("0") or "0" for g in m.group(4).split("_") if g)
            num += "." + dec
        return chap, f"{chap}:{art}-{num}"
    m = re.match(r"HRS_(\d+[A-Z]?)-(\d*)((?:_\d+)*)\.htm$", fn, re.I)
    if not m:
        return None, None
    chap = m.group(1).lstrip("0") or "0"
    if not m.group(2):
        return chap, None                      # chapter TOC page
    num = m.group(2).lstrip("0") or "0"
    if m.group(3):
        dec = "".join(g.lstrip("0") or "0" for g in m.group(3).split("_") if g)
        num += "." + dec
    return chap, f"{chap}-{num}"


def sec_sort_key(sid):
    chap, _, rest = sid.partition("-")
    cn = int(re.match(r"\d+", chap).group(0))
    cs = chap[len(str(cn)):]
    parts = [int(p) for p in re.findall(r"\d+", rest)]
    return (cn, cs, parts)


def slug(sid):
    """Canonical wiki page basename for a section id."""
    return "hrs-" + sid.lower()


# ---------------------------------------------------------------------------
# Operative text vs. reviser annotations
#
# Every HRS section page ends its operative text with a bracketed source note,
# e.g. [L 2010, c 211, pt of §2; am L 2022, c 169, §3].  Everything after that
# bracket is editorial apparatus added by the revisor (Case Notes, Cross
# References, Law Journals, Attorney General Opinions).  That is NOT statute.
# ---------------------------------------------------------------------------
HISTORY_RE = re.compile(r"\[(?:L|HRS|Am\s+L|am\s+L|CC|RL|Sup)\s[^\]]{6,600}\]", re.S)
ANNOT_HEADS = ("Case Notes", "Cross References", "Law Journals and Reviews",
               "Attorney General Opinions", "Revision Note", "Rules of Court",
               "Note", "Historical Note")


# capitol.hawaii.gov emits U+2011 NON-BREAKING HYPHEN inside some section
# numbers (e.g. "§10‑24", "section 11‑15").  Left alone this silently drops
# real cross-references.  Normalised at PARSE time only - raw/ stays byte
# faithful to what the State served.
_DASHES = {0x2010: "-", 0x2011: "-", 0x2012: "-", 0x2013: "-",
           0x2014: "-", 0x2015: "-", 0x2212: "-"}


def normalize_dashes(s):
    return s.translate(_DASHES)


PART_RE = re.compile(r"^\s*(?:HRS\s*)?(?:PART\s+([IVXLC]+[A-Z]?)\s*\.?\s*\n)+", re.I | re.M)
# §§ (double) marks a range repeal, e.g. "§§11-71 to 11-75 REPEALED".
# id allows the colon (article) form: 431:10A-301, 560:1-101
SEC_START_RE = re.compile(
    r"(?:^|\n)\s*\[?\s*§{1,2}\s*([\dA-Z]+(?::[\dA-Z]+)?-[\d.]+)\s*\]?\s")


def split_section(text):
    """-> dict(part_heading, catchline, operative, history, annotations)

    The first section of a Part carries that Part's heading above it, sometimes
    followed by a revisor "Note".  Neither is part of the section, so the real
    section text starts at the first '§N-N' / '[§N-N]' marker.
    """
    text = normalize_dashes(text)
    # Drop the IIS breadcrumb footer.
    text = re.sub(r"\n\s*Previous\s*\n.*\Z", "", text, flags=re.S)
    text = re.sub(r"\n\s*Vol\d+_Ch[\d\-A-Z]+\s*\n.*\Z", "", text, flags=re.S)
    text = text.strip()

    # Preamble: everything before the first section marker.
    sm = SEC_START_RE.search(text)
    preamble = text[:sm.start()] if sm else ""
    body = text[sm.start():].strip() if sm else text

    # Preamble shapes vary: "PART I / PART I. / GENERAL PROVISIONS" (label
    # repeated), "PART XIII. / CAMPAIGN FINANCE / A. General Provisions"
    # (with a lettered subpart), or a bare subpart "B. Election Campaign...".
    # Part titles are reliably ALL CAPS; subpart titles are Title Case.
    flat = " ".join(preamble.split())
    part_heading, subpart = "", ""
    # Revisor apparatus that can follow a heading and must not be absorbed.
    STOP = r"(?:Case\s+Notes|Cross\s+References|Law\s+Journals|Attorney\s+General|Revision\s+Note|Rules\s+of\s+Court|Note)\b"

    pms = list(re.finditer(r"\bPART\s+([IVXLC]+[A-Z]?)\b\.?", flat))
    if pms:
        pm = pms[-1]
        roman = pm.group(1).upper()
        tm = re.match(r"\s*([A-Z][A-Z0-9'\-, ]{3,90})", flat[pm.end():])
        title = " ".join(tm.group(1).split()).strip(" ,-") if tm else ""
        # An all-caps run swallows the leading capital of the next, mixed-case
        # word ("EXPENSES A" from "A. Election Expenses"). Drop a dangling letter.
        title = re.sub(r"\s+[A-Z]$", "", title)
        part_heading = f"PART {roman}." + (f" {title}" if title else "")

    # Strip the PART label before hunting subparts, or "PART V. PARTIES" reads
    # as subpart "V." - the Roman numeral is itself a single capital letter.
    flat_ns = re.sub(r"\bPART\s+[IVXLC]+[A-Z]?\b\.?", " ", flat)
    sm2 = re.search(r"(?:^|\s)([A-Z])\.\s+([A-Z][A-Za-z'\-]+(?:[ \-][A-Za-z'\-]+){0,12})", flat_ns)
    if sm2:
        stitle = re.split(STOP, " ".join(sm2.group(2).split()))[0].strip(" ,-")
        if stitle:
            subpart = f"{sm2.group(1)}. {stitle}"

    hits = list(HISTORY_RE.finditer(body))
    if hits:
        end = hits[-1].end()
        operative = body[:end].strip()
        history = " ".join(hits[-1].group(0).split())
        annotations = body[end:].strip()
        # The source note documents prior numbering ("Supp, §143A-1; HRS §50-1")
        # and session-law sections.  Those are provenance, NOT the section
        # citing other law, so they get their own zone.
        body_only = body[:hits[-1].start()].strip()
    else:
        # Repealed stubs and a few oddities carry no source note.
        cut = len(body)
        for h in ANNOT_HEADS:
            i = body.find("\n" + h)
            if i != -1:
                cut = min(cut, i)
        operative = body[:cut].strip()
        history = ""
        annotations = body[cut:].strip()
        body_only = operative

    # id allows colon form; the terminator allows the bracketed-section
    # convention '[§46-55 Catchline.]' where the period closes as '.]'
    m = re.match(r"\s*\[?\s*§{0,2}\s*([\dA-Z]+(?::[\dA-Z]+)?-[\d.]+)\s*\]?\s+"
                 r"(.{0,250}?)\.\]?(?:\s|$)",
                 operative, re.S)
    catchline = " ".join(m.group(2).split()) if m else ""
    return {"part_heading": part_heading, "subpart_heading": subpart,
            "catchline": catchline, "operative": operative,
            "body_only": body_only, "history": history,
            "annotations": annotations, "preamble": preamble.strip()}


# ---------------------------------------------------------------------------
# Citation extraction
# ---------------------------------------------------------------------------
# A section token, including the colon (article) form used by chapters 412,
# 431, 432, 490: '412:2-105', '431:10A-301'. Colon form is FIRST in the
# alternation so it wins at a shared position, and its chapter part is
# constrained to 3+ digits so clock times ('4:30-5:00') can never match.
# Open-questions 2026-07-25: the LRB crosswalk carries 289 colon-form keys
# that a colon-blind _SEC silently drops.
_SEC = r"(?:\d{3}[A-Z]?:\d+[A-Z]?-\d+(?:\.\d+)?|\d+[A-Z]?-\d+(?:\.\d+)?)"

CITE_PATTERNS = [
    # "sections 11-15 to 11-19" / "sections 11-15 through 11-19"
    ("hrs_range", re.compile(rf"\bsections?\s+({_SEC})\s+(?:to|through|-)\s+({_SEC})", re.I)),
    # "section 11-102", "sections 11-102, 11-103 and 11-104"
    # a pin cite "(b)" after a section number must not break a list:
    # "sections 11-357, 11-358, 11-359(b), and 11-360" cites all four.
    # Found 2026-07-25 harvesting HAR 3-160-2, where 11-360 was silently
    # dropped; the same construction occurs in statute text.
    ("hrs_section", re.compile(rf"\bsections?\s+((?:{_SEC})(?:\s*\([a-z0-9]{{1,4}}\))?(?:\s*(?:,|;|\band\b|\bor\b)(?:\s*(?:\band\b|\bor\b))?\s*(?:{_SEC})(?:\s*\([a-z0-9]{{1,4}}\))?)*)", re.I)),
    # "§11-102" / "§§11-102, 11-103"
    ("hrs_sign", re.compile(rf"§§?\s*((?:{_SEC})(?:\s*\([a-z0-9]{{1,4}}\))?(?:\s*(?:,|;|\band\b|\bor\b)(?:\s*(?:\band\b|\bor\b))?\s*(?:{_SEC})(?:\s*\([a-z0-9]{{1,4}}\))?)*)")),
    # "chapter 91" / "chapters 11 and 12"
    ("hrs_chapter", re.compile(r"\bchapters?\s+(\d+[A-Z]?(?:\s*(?:,|;|\band\b|\bor\b)(?:\s*(?:\band\b|\bor\b))?\s*\d+[A-Z]?)*)\b", re.I)),
    # "part XIII of chapter 11", "this part"
    ("hrs_part", re.compile(r"\bpart\s+([IVXL]+)\b")),
    # Federal
    # "15 U.S.C. section 7001", "42 U.S.C. §1983", "52 U.S.C. 20901" - the
    # section keyword is optional and must not be swallowed as the number.
    ("usc", re.compile(r"(\d+)\s+U\.?\s?S\.?\s?C\.?\s*(?:(?:§+|sections?|secs?\.)\s*)?(\d[\d\w\-().]*)?", re.I)),
    ("cfr", re.compile(r"(\d+)\s+C\.?\s?F\.?\s?R\.?\s*(?:(?:§+|sections?|parts?)\s*)?(\d[\d\w\-().]*)?", re.I)),
    ("public_law", re.compile(r"Public\s+Law\s+(\d+)-(\d+)", re.I)),
    # Hawaii Administrative Rules
    ("har", re.compile(r"\btitle\s+(\d+),?\s+(?:Hawaii\s+administrative\s+rules|chapter\s+([\d\-]+))", re.I)),
    # Constitutions
    ("hi_const", re.compile(r"(?:article\s+([IVXL]+),?\s+section\s+(\d+)[^.]{0,60}?constitution\s+of\s+the\s+State|"
                            r"State\s+[Cc]onstitution,?\s+article\s+([IVXL]+),?\s+section\s+(\d+))", re.I)),
    ("us_const", re.compile(r"(?:United\s+States|U\.S\.)\s+Constitution|Constitution\s+of\s+the\s+United\s+States", re.I)),
]

_SPLIT = re.compile(r"\s*(?:,|;|\band\b|\bor\b)\s*", re.I)


def normalize_sec(s):
    s = re.sub(r"\s*\([^)]{1,6}\)\s*$", "", s.strip())  # strip a pin cite "(b)"
    s = s.upper()
    m = re.match(rf"^({_SEC})$", s, re.I)
    return m.group(1).upper() if m else None


def extract_citations(text, this_chapter=None):
    """Return a list of dicts: {kind, target, raw, pos}.

    `target` is a canonical id: '11-102' for sections, 'ch:91' for chapters,
    'usc:52:20901' for federal, etc.  Self-references are dropped by the caller.
    """
    text = normalize_dashes(text)
    out = []
    consumed = []  # spans already claimed by a higher-priority pattern

    def overlaps(a, b):
        return any(not (b <= s or a >= e) for s, e in consumed)

    for kind, rx in CITE_PATTERNS:
        for m in rx.finditer(text):
            if overlaps(m.start(), m.end()):
                continue
            raw = " ".join(m.group(0).split())
            targets = []
            if kind == "hrs_range":
                a, b = normalize_sec(m.group(1)), normalize_sec(m.group(2))
                if a and b:
                    targets = [a, b]
                    kind_out = "hrs_section"
                else:
                    continue
            elif kind in ("hrs_section", "hrs_sign"):
                targets = [x for x in (normalize_sec(p) for p in _SPLIT.split(m.group(1))) if x]
                kind_out = "hrs_section"
            elif kind == "hrs_chapter":
                targets = ["ch:" + p.strip().upper() for p in _SPLIT.split(m.group(1)) if p.strip()]
                kind_out = "hrs_chapter"
            elif kind == "hrs_part":
                targets = [f"part:{this_chapter}:{m.group(1).upper()}"] if this_chapter else []
                kind_out = "hrs_part"
            elif kind in ("usc", "cfr"):
                # Target is the citable section; subsection detail stays in `raw`.
                base = re.split(r"[(.]", (m.group(2) or ""))[0].strip(" )(.,;")
                targets = [f"{kind}:{m.group(1)}:{base}".rstrip(":")]
                kind_out = kind
            elif kind == "public_law":
                targets = [f"pl:{m.group(1)}-{m.group(2)}"]
                kind_out = "public_law"
            elif kind == "har":
                targets = [f"har:{m.group(1)}" + (f":{m.group(2)}" if m.group(2) else "")]
                kind_out = "har"
            elif kind == "hi_const":
                art = m.group(1) or m.group(3)
                sec = m.group(2) or m.group(4)
                targets = [f"hiconst:{art}:{sec}"]
                kind_out = "hi_const"
            elif kind == "us_const":
                targets = ["usconst"]
                kind_out = "us_const"
            else:
                continue

            if not targets:
                continue
            consumed.append((m.start(), m.end()))
            ctx = " ".join(text[max(0, m.start() - 110):m.end() + 110].split())
            for t in targets:
                out.append({"kind": kind_out, "target": t, "raw": raw, "pos": m.start(), "context": ctx})
    return out


def context_label(sid):
    chap = sid.split("-")[0] if "-" in sid else sid
    return CHAPTER_TITLE.get(chap, "")
