"""Shared helpers for the HAR (Hawaii Administrative Rules) pipeline.

Nothing in here interprets law. It fetches bytes, extracts PDF text, and
normalises rule-citation strings. All legal judgment happens on the wiki pages.

HAR differs from HRS in ways that drive every design choice below:

  * There is no central full-text source. Rules are federated across ~20
    department websites, mostly as PDFs, each with its own layout.
  * Titles are numbered by DEPARTMENT, not by subject: title 3 is DAGS,
    title 11 is Health, title 19 is Transportation.
  * A rule section carries THREE informational notes, and two of them are
    citations to statute that mean different things.  See ZONES below.
"""
import hashlib
import os
import re
import time
import urllib.request

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_HAR = os.path.join(VAULT, "raw", "har")
RAW_PDF = os.path.join(VAULT, "raw", "har", "_pdf")     # gitignored; cache only
GRAPH = os.path.join(VAULT, "graph")
HAR_PAGES = os.path.join(VAULT, "har")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# ---------------------------------------------------------------------------
# The 24 HAR titles.  Department names and the canonical rules URL are taken
# from the Legislative Reference Bureau's own directory (2025 edition,
# published July 2026), NOT from guesswork or from the Lt. Governor's index,
# which omits titles 1, 9, 21 and 22 entirely.
#
# Verified 2026-07-24 against
# lrb.hawaii.gov/wp-content/uploads/2025AdminRules_Supplement.pdf pp. 121-157.
# The URL column is filled in by tools/har_directory.py, which reads it out of
# that PDF rather than hardcoding it here - so a re-run tracks the LRB.
# ---------------------------------------------------------------------------
TITLES = {
    1: "Office of the Governor",
    2: "Office of the Lieutenant Governor",
    3: "Department of Accounting and General Services",
    4: "Department of Agriculture and Biosecurity",
    5: "Department of the Attorney General",
    6: "Department of Budget and Finance",
    7: "Department of Defense",
    8: "Department of Education",
    9: "Office of Hawaiian Affairs",
    10: "Department of Hawaiian Home Lands",
    11: "Department of Health",
    12: "Department of Labor and Industrial Relations",
    13: "Department of Land and Natural Resources",
    14: "Department of Human Resources Development",
    15: "Department of Business, Economic Development, and Tourism",
    16: "Department of Commerce and Consumer Affairs",
    17: "Department of Human Services",
    18: "Department of Taxation",
    19: "Department of Transportation",
    20: "University of Hawaii",
    21: "Legislative Service Agencies",
    22: "Judiciary",
    23: "Department of Corrections and Rehabilitation",
    24: "Department of Law Enforcement",
}

# ---------------------------------------------------------------------------
# ZONES.  An HRS section page has three zones (operative / history /
# annotation) and merging them manufactures phantom edges.  A HAR *section*
# has FOUR, because the revisor's format puts two structurally different
# statutory citations in two different notes:
#
#   operative  - the rule's own text.  Rule pointing at rule, or at statute.
#   source     - the bracketed source note: [Eff 7/1/81; am 3/4/94; comp ...].
#                Effective dates and amendment history.  NOT a reference.
#   auth       - "(Auth: HRS §§11-193, 11-194)".  The statutes the agency
#                asserts AUTHORISED it to adopt this rule.  Delegation.
#   imp        - "(Imp: HRS §11-191)".  The statutes the agency asserts this
#                rule IMPLEMENTS or interprets.  Execution.
#
# Auth and Imp are NOT the same relation and must never be collapsed into one
# edge type.  A rule can be authorised by a general rulemaking grant while
# implementing an entirely different substantive section; a court reviewing
# whether a rule exceeds its authority cares only about Auth.  Both are also
# the ADOPTING AGENCY'S ASSERTION, not the revisor's and not a court's - the
# LRB says so expressly (2025 ed. p. 1, cautionary instruction (2)).
# ---------------------------------------------------------------------------
ZONES = ("operative", "source", "auth", "imp", "annotation")

# Edge relations.  The HRS graph has one untyped `cites`.  Adding HAR is the
# moment to type edges, because "statute delegates to rule" and "rule
# implements statute" are opposite directions with different meanings and
# re-deriving the whole graph later is expensive.
RELATIONS = (
    "cites",            # generic reference, direction only
    "authorized_by",    # HAR section -> HRS section   (from Auth:)
    "implements",       # HAR section -> HRS section   (from Imp:)
    "delegates_to",     # HRS section -> HAR chapter   (statute says "the
                        #   department shall adopt rules"; inverse of the above
                        #   but independently attested, so stored separately)
    "renumbered_from",  # from a source note "ren §11-2"
)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def fetch(url, tries=3, pause=0.4, binary=False):
    """GET with a browser UA.

    Several hawaii.gov hosts 403 a bare client and several apex hosts 301 to
    www, so a UA and redirect-following are both mandatory.  A sub-200-byte
    HTTP 200 is treated as a failure: csc.hawaii.gov answers 200 with a
    135-byte <META HTTP-EQUIV="Refresh"> body, which is not an HTTP redirect,
    so urllib reports success and hands back an empty document.
    """
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml,application/pdf,*/*",
                "Accept-Language": "en-US,en;q=0.9",
            })
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
                final = r.geturl()
            time.sleep(pause)
            if len(data) < 200:
                m = re.search(rb'(?i)<meta[^>]+http-equiv=["\']?refresh[^>]+url=([^"\'>\s]+)',
                              data)
                if m:
                    raise RuntimeError(
                        "meta-refresh stub (%d bytes) -> %s"
                        % (len(data), m.group(1).decode("ascii", "replace")))
                raise RuntimeError("suspiciously small body: %d bytes" % len(data))
            if binary:
                return data, final
            enc = "utf-8"
            m = re.search(rb"charset=([\w\-]+)", data[:3000], re.I)
            if m:
                enc = m.group(1).decode("ascii", "ignore")
            try:
                return data.decode(enc), final
            except (UnicodeDecodeError, LookupError):
                return data.decode("utf-8", errors="replace"), final
        except Exception as e:                              # noqa: BLE001
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"fetch failed {url}: {last}")


# capitol.hawaii.gov and several PDF producers emit U+2011 NON-BREAKING
# HYPHEN and friends inside rule and section numbers.  Left alone this
# silently drops real cross-references.  Normalised at PARSE time only -
# raw/ stays byte-faithful to what the State served.
_DASHES = {0x2010: "-", 0x2011: "-", 0x2012: "-", 0x2013: "-",
           0x2014: "-", 0x2015: "-", 0x2212: "-", 0x00ad: ""}


def normalize_dashes(s):
    return s.translate(_DASHES)


# ---------------------------------------------------------------------------
# Rule identifiers
#
# A HAR citation is TITLE-CHAPTER-SECTION: HAR §3-160-20 is title 3,
# chapter 160, section 20.  Chapters and sections both take decimal suffixes
# (§11-55-34.08, chapter 11-260.1), so a bare split on "-" is wrong.
# ---------------------------------------------------------------------------
CHAP_RE = re.compile(r"^(\d+)-(\d+(?:\.\d+)?)$")
SEC_RE = re.compile(r"^(\d+)-(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?[A-Za-z]?)$")


def chapter_id(title, number):
    """(3, '160') -> '3-160'.  Number may already carry its own title prefix,
    which happens in the LRB directory for chapters that moved between
    departments and kept their original numbers (e.g. '17-2015' listed under
    title 15).  Those are returned unchanged - renumbering them would invent
    a citation the law does not use."""
    number = str(number).strip()
    if CHAP_RE.match(number):
        return number
    return f"{title}-{number}"


def sec_sort_key(rid):
    """Sort '11-55-34.08' after '11-55-9' and before '11-55-35'."""
    parts = []
    for chunk in str(rid).split("-"):
        m = re.match(r"^(\d+)(?:\.(\d+))?([A-Za-z]*)$", chunk)
        if m:
            parts.append((int(m.group(1)), int(m.group(2) or -1), m.group(3)))
        else:
            parts.append((10 ** 9, 0, chunk))
    return parts


def chap_sort_key(cid):
    return sec_sort_key(cid)


def slug(rid):
    """Canonical wiki page basename.  Decimal points are KEPT: HAR §11-55-34.08
    is har-11-55-34.08.md and links as [[har-11-55-34.08]].  Obsidian strips
    only the final .md, so this resolves, and it matches the citation instead
    of re-spelling it."""
    return "har-" + str(rid).lower()
