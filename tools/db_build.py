"""Build hawaii-law.db — THE artifact — from the pipeline's parse outputs.

    python tools/db_build.py            # (re)build the DB at the vault root
    python tools/db_build.py --check    # build to a temp file and validate only

Architecture (decided 2026-07-26, see Brain/Decisions/log.md and the
brainstorm capture): the corpus is a single SQLite database on disk, snapshotted
to DO Spaces after each ingest, with a read-only serving copy on the droplet
once the public surface exists. Git holds the project (schema doc, tools, log,
open-questions); the DB holds the law. Obsidian and the generated markdown
pages are retired.

Pipeline shape: harvest -> parse (graph/*.json intermediates, gitignored) ->
db_build.py folds everything into the DB. Parsers stay untouched; this tool is
the single load step. Idempotent: rebuilds from scratch every run (fast at
current scale); hand-written content (annotations, doctrine) is INPUT to this
tool from its own tables when they are the source of truth — see --preserve.

Identity contract (shared with hi-leg-db):
  * section ids are the citation as printed, lowercased layer prefix:
    'hrs:11-357', 'hrs:11-15.2', 'hrs:412:2-105', 'har:3-160-2'
  * chapter/title units: 'hrs:ch:11', 'har:ch:3-160', 'har:title:3'
  * never zero-padded, never renumbered.

Edges carry ATTESTATION, never merged (schema rule 12):
  * 'hrs_text'  — parsed from statute text (zone says which zone)
  * 'rule_text' — parsed from the rule's own printed notes
  * 'lrb2025'   — the LRB 2025 Table & Directory
Where two attestations disagree, both rows exist; that is a finding.
"""
import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hrs_lib import RAW as RAW_HRS, VAULT, GRAPH, split_section
from build_graph import read_raw

DB_PATH = os.path.join(VAULT, "hawaii-law.db")

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);

-- enumerated universes: every unit of law we KNOW EXISTS (mapped),
-- whether or not its text is in (read).
CREATE TABLE units (
  id TEXT PRIMARY KEY,            -- 'hrs:ch:11' | 'har:title:3' | 'har:ch:3-160'
  layer TEXT NOT NULL,            -- 'hrs' | 'har'
  kind TEXT NOT NULL,             -- 'chapter' | 'title'
  num TEXT NOT NULL,
  title TEXT,
  parent TEXT,                    -- har chapter -> 'har:title:3'
  repealed INTEGER DEFAULT 0,
  reserved INTEGER DEFAULT 0,
  url TEXT,
  extra TEXT                      -- JSON: volume/dir/subtitle/dept/section counts...
);

CREATE TABLE sections (
  id TEXT PRIMARY KEY,            -- 'hrs:11-357' | 'har:3-160-2'
  layer TEXT NOT NULL,
  num TEXT NOT NULL,              -- '11-357' | '3-160-2'
  chapter TEXT NOT NULL,          -- '11' | '3-160'
  catchline TEXT,
  unit_path TEXT,                 -- part/subpart or subchapter, ' › '-joined
  repealed INTEGER DEFAULT 0,
  effective TEXT,                 -- HAR: current-text date from the source note
  url TEXT,
  retrieved TEXT,
  last_verified TEXT,
  source_id TEXT                  -- provenance registry row
);

-- verbatim text, one row per zone. HRS zones: preamble|operative|history|annotation.
-- HAR zones: operative|source_note|auth|imp|annotation (healed form; as-printed
-- variants and every repair live in problems).
CREATE TABLE zones (
  section_id TEXT NOT NULL REFERENCES sections(id),
  zone TEXT NOT NULL,
  body TEXT NOT NULL,
  PRIMARY KEY (section_id, zone)
);

CREATE TABLE edges (
  id INTEGER PRIMARY KEY,
  src TEXT NOT NULL,              -- section/unit id
  dst TEXT NOT NULL,              -- section/unit id, or namespaced external:
                                  --   'usc:52:20901' 'cfr:11:100' 'pl:107-252'
                                  --   'hiconst:II:4' 'usconst' 'slh:2013:287'
  dst_kind TEXT NOT NULL,         -- hrs_section|hrs_chapter|har_section|har_chapter|
                                  --   usc|cfr|public_law|hi_const|us_const|session_law|case|...
  relation TEXT NOT NULL,         -- cites|authorized_by|implements|delegates_to|renumbered_from
  zone TEXT,                      -- which zone of src asserted it
  attestation TEXT NOT NULL,      -- hrs_text|rule_text|lrb2025
  raw TEXT,                       -- as written in the source
  context TEXT
);
CREATE INDEX idx_edges_src ON edges(src);
CREATE INDEX idx_edges_dst ON edges(dst);
CREATE INDEX idx_edges_rel ON edges(relation);

-- the mechanical concept backbone: statute-declared, scope-resolved terms
CREATE TABLE definitions (
  term TEXT NOT NULL,
  term_norm TEXT NOT NULL,
  section_id TEXT NOT NULL,
  scope_type TEXT,                -- chapter|part|section|title...
  scope_key TEXT,
  scope_rank INTEGER,
  verb TEXT,                      -- means|includes...
  body TEXT NOT NULL
);
CREATE INDEX idx_def_norm ON definitions(term_norm);

-- hand-written interpretive reading on a section. THE non-regenerable layer.
CREATE TABLE annotations (
  section_id TEXT PRIMARY KEY REFERENCES sections(id),
  body TEXT NOT NULL,
  created TEXT,
  updated TEXT
);

-- demand-created doctrine / agency / synthesis entries (Hawaii delta only,
-- never generic legal explainers — grill decision Q4).
CREATE TABLE doctrine (
  slug TEXT PRIMARY KEY,
  kind TEXT NOT NULL,             -- doctrine|agency|synthesis|question
  title TEXT,
  body TEXT NOT NULL,
  created TEXT,
  updated TEXT
);

-- agency opinions and other interpretive documents (CSC advisory opinions
-- first; AG opinions and cases join as their layers land). Binding-in-
-- practice interpretive gloss; body verbatim; text_layer=0 marks scanned
-- PDFs awaiting OCR (recorded absence, per rule 8).
CREATE TABLE opinions (
  id TEXT PRIMARY KEY,            -- 'csc_ao:07-01', 'csc_ao:98-05-amendment'
  kind TEXT NOT NULL,             -- 'csc_advisory' | 'ag' | ...
  number TEXT,
  opinion_date TEXT,
  subject TEXT,
  body TEXT,
  form TEXT,                      -- 'pdf' | 'html'
  text_layer INTEGER DEFAULT 1,
  url TEXT,
  sha256 TEXT,
  retrieved TEXT
);

-- provenance registry: every fetched source
CREATE TABLE sources (
  id TEXT PRIMARY KEY,
  url TEXT,
  publisher TEXT,
  retrieved TEXT,
  sha256 TEXT,
  note TEXT
);

-- validation exceptions and corroborated repairs, per pipeline run.
CREATE TABLE problems (
  origin TEXT NOT NULL,           -- which problems file / pipeline stage
  item TEXT NOT NULL              -- the JSON entry, verbatim
);

CREATE VIRTUAL TABLE fts USING fts5(
  section_id UNINDEXED, zone UNINDEXED, catchline, body
);

-- the coverage ledger, DERIVED so it cannot go stale (grill decision Q3)
CREATE VIEW coverage AS
  SELECT u.layer, u.kind,
         COUNT(*) AS mapped,
         SUM(CASE WHEN u.repealed=1 OR u.reserved=1 THEN 1 ELSE 0 END) AS dead,
         (SELECT COUNT(DISTINCT s.chapter) FROM sections s WHERE s.layer=u.layer) AS chapters_read
  FROM units u GROUP BY u.layer, u.kind;
"""


def jload(name):
    return json.load(open(os.path.join(GRAPH, name), encoding="utf-8-sig"))


def norm_dst(kind, target):
    """Map the parsers' target ids onto the DB id namespace."""
    t = str(target)
    if kind == "hrs_section":
        return "hrs:" + t
    if kind == "hrs_chapter":
        return "hrs:ch:" + t.split(":")[-1]
    if kind == "hrs_part":
        return "hrs:" + t                      # 'part:11:XIII' -> opaque, kept
    if kind in ("har_section",):
        return "har:" + t.split(":")[-1] if not t.startswith("har:") else t
    if kind in ("har_chapter", "har"):
        p = t.split(":")
        return "har:ch:" + p[-1] if len(p) > 1 else "har:" + t
    if kind == "hi_const" and t.strip().lower() == "preamble":
        return "hiconst:preamble"
    if kind == "hi_const" and not t.startswith("hiconst:"):
        # the LRB Table writes 'Art. I §1' / 'Art. XIV'; normalise to the
        # hiconst namespace so these edges join the harvested sections
        m = re.match(r"Art\.?\s+([IVXL]+)(?:\s*§\s*(\d+(?:\.\d+)?))?", t)
        if m:
            return (f"hiconst:{m.group(1)}:{m.group(2)}" if m.group(2)
                    else f"hiconst:art:{m.group(1)}")
    return t                                    # usc:/cfr:/pl:/hiconst:/usconst/...


def preserve_handwritten(db_path):
    """Read the hand-written tables out of the existing DB before a rebuild.
    THE contract: the generator never destroys hand-written rows. A rebuild
    is from-scratch for every mechanical table; annotations and doctrine are
    carried over. (Added after the validation caught a rebuild wiping them —
    the page-era source was gone and the old code re-read from pages.)"""
    if not os.path.exists(db_path):
        return [], []
    try:
        old = sqlite3.connect(db_path)
        ann = old.execute("SELECT section_id, body, created, updated "
                          "FROM annotations").fetchall()
        doc = old.execute("SELECT slug, kind, title, body, created, updated "
                          "FROM doctrine").fetchall()
        old.close()
        return ann, doc
    except sqlite3.Error:
        return [], []


def build(db_path):
    preserved_ann, preserved_doc = preserve_handwritten(db_path)
    if os.path.exists(db_path):
        os.remove(db_path)
    for wal in (db_path + "-wal", db_path + "-shm"):
        if os.path.exists(wal):
            os.remove(wal)
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)
    cur = con.cursor()
    today = date.today().isoformat()

    # ---- sources registry --------------------------------------------------
    manifest = json.load(open(os.path.join(RAW_HRS, "_manifest.json"),
                              encoding="utf-8"))
    cur.execute("INSERT INTO sources VALUES (?,?,?,?,?,?)",
                ("hrs-harvest", "https://www.capitol.hawaii.gov/hrscurrent/",
                 "Hawaii State Legislature", manifest["retrieved"], None,
                 "per-section fetches; discovered via " + manifest["source_page"]))
    # one sources row per HAR chapter, from the scale-harvest provenance
    # (tools/har_harvest.py + har_parse_all.py). Publisher = the owning
    # department per the LRB title map.
    from har_lib import TITLES as HAR_TITLES
    har_rules = json.load(open(os.path.join(GRAPH, "har-rules.json"),
                               encoding="utf-8"))
    for chap, C in har_rules["chapters"].items():
        title_num = int(chap.split("-", 1)[0])
        cur.execute("INSERT OR REPLACE INTO sources VALUES (?,?,?,?,?,?)",
                    (f"har-{chap}", C.get("url"),
                     HAR_TITLES.get(title_num, f"HAR title {title_num}"),
                     C.get("retrieved"), C.get("sha256_pdf"),
                     f"chapter PDF; extracted text from raw/har/txt/"
                     f"{C.get('source_doc')}"
                     + ("" if C.get("toc_checked")
                        else "; parsed without a TOC ground-truth check")))
    cur.execute("INSERT INTO sources VALUES (?,?,?,?,?,?)",
                ("lrb-2025-table",
                 "https://lrb.hawaii.gov/wp-content/uploads/2025AdminRules_Supplement.pdf",
                 "Legislative Reference Bureau", "2026-07-25", None,
                 "2025 Table of Statutory Sections Implemented and Directory; "
                 "authoritative HAR enumeration + Imp crosswalk"))

    # ---- units: HRS chapters ----------------------------------------------
    hu = jload("hrs-universe.json")
    for ch in hu["detail"]:
        cur.execute("INSERT OR REPLACE INTO units VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (f"hrs:ch:{ch['chapter']}", "hrs", "chapter", ch["chapter"],
                     ch.get("title"), None, 0, 0,
                     f"https://www.capitol.hawaii.gov/hrscurrent/{ch['volume']}/{ch['dir']}/",
                     json.dumps({k: ch[k] for k in ("volume", "dir", "sections",
                                                    "hrs_title_group") if k in ch})))

    # ---- units: HAR titles + chapters -------------------------------------
    haru = jload("har-universe.json")
    titles = haru["titles"]
    har_listings = {}
    for t in (titles.values() if isinstance(titles, dict) else titles):
        cur.execute("INSERT OR REPLACE INTO units VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (f"har:title:{t['title']}", "har", "title", str(t["title"]),
                     t.get("department"), None, 0, 0, t.get("url"),
                     json.dumps({"no_rules": t.get("no_rules"),
                                 "notes": t.get("notes")})))
        # collect listings first: the LRB double-lists some chapters (title 15
        # under two subtitles, 19-150 both live and repealed). Preserving both
        # is the rule — deduping would pick a winner arbitrarily and hide a
        # real conflict. Conflicting listings land in extra.listings.
        for ch in t.get("chapters", []):
            har_listings.setdefault(ch["chapter"], []).append((t["title"], ch))

    for cid, listings in har_listings.items():
        title_num, ch = listings[0]
        extra = {k: ch[k] for k in ("subtitle", "part", "range_to",
                                    "foreign_title") if ch.get(k)}
        if len(listings) > 1:
            extra["contested"] = True
            extra["listings"] = [
                {"title": tn, **{k: c[k] for k in
                 ("catchline", "subtitle", "repealed", "reserved") if k in c}}
                for tn, c in listings]
        cur.execute("INSERT INTO units VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (f"har:ch:{cid}", "har", "chapter", cid,
                     ch.get("catchline"), f"har:title:{title_num}",
                     int(bool(ch.get("repealed"))),
                     int(bool(ch.get("reserved"))), None,
                     json.dumps(extra, ensure_ascii=False)))
    cur.execute("INSERT INTO meta VALUES ('har_chapter_listings',?)",
                (str(sum(len(v) for v in har_listings.values())),))
    cur.execute("INSERT INTO meta VALUES ('har_chapter_contested',?)",
                (str(sum(1 for v in har_listings.values() if len(v) > 1)),))

    # ---- HRS sections + zones + fts ---------------------------------------
    S = jload("sections.json")["sections"]
    n_zones = 0
    for sid, s in S.items():
        _, body = read_raw(os.path.join(RAW_HRS, s["raw_file"]))
        parts = split_section(body)
        unit_path = " › ".join(x for x in
                               (s.get("part"), s.get("subpart")) if x)
        cur.execute("INSERT INTO sections VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (f"hrs:{sid}", "hrs", sid, s["chapter"], s["catchline"],
                     unit_path, int(s["repealed"]), None, s["url"],
                     s["retrieved"], s["retrieved"], "hrs-harvest"))
        for zone, text in (("preamble", parts["preamble"]),
                           ("operative", parts["operative"]),
                           ("history", parts["history"]),
                           ("annotation", parts["annotations"])):
            if text and text.strip():
                cur.execute("INSERT INTO zones VALUES (?,?,?)",
                            (f"hrs:{sid}", zone, text))
                cur.execute("INSERT INTO fts VALUES (?,?,?,?)",
                            (f"hrs:{sid}", zone, s["catchline"] or "", text))
                n_zones += 1

    # ---- HRS edges ---------------------------------------------------------
    for e in jload("edges.json")["edges"]:
        rel = "renumbered_from" if e["zone"] == "history" else "cites"
        cur.execute("INSERT INTO edges (src,dst,dst_kind,relation,zone,attestation,raw,context) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (f"hrs:{e['src']}", norm_dst(e["kind"], e["target"]),
                     e["kind"], rel, e["zone"], "hrs_text",
                     e.get("raw"), e.get("context")))

    # ---- HAR sections + zones + edges --------------------------------------
    R = jload("har-rules.json")
    for chap, C in R["chapters"].items():
        cur.execute("UPDATE units SET extra=json_set(coalesce(extra,'{}'),"
                    "'$.historical_note', ?) WHERE id=?",
                    (C.get("historical_note", ""), f"har:ch:{chap}"))
        for num, s in C["sections"].items():
            cur.execute("INSERT INTO sections VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (f"har:{num}", "har", num, chap, s["catchline"],
                         s.get("subchapter") or "", int(s["repealed"]),
                         s.get("effective"), C["url"], C["retrieved"],
                         C["retrieved"], f"har-{chap}"))
            for zone, text in (("operative", s.get("operative")),
                               ("source_note", s.get("source_note")),
                               ("auth", s.get("auth_healed") or s.get("auth_raw")),
                               ("imp", s.get("imp_healed") or s.get("imp_raw")),
                               ("annotation", s.get("annotation"))):
                if text and text.strip():
                    cur.execute("INSERT INTO zones VALUES (?,?,?)",
                                (f"har:{num}", zone, text))
                    cur.execute("INSERT INTO fts VALUES (?,?,?,?)",
                                (f"har:{num}", zone, s["catchline"] or "", text))
                    n_zones += 1
    for e in R["edges"]:
        cur.execute("INSERT INTO edges (src,dst,dst_kind,relation,zone,attestation,raw) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (norm_dst("har_section", e["src"]),
                     norm_dst(e["kind"], e["target"]), e["kind"],
                     e["relation"], e["zone"], "rule_text", e.get("raw")))

    # ---- LRB crosswalk edges (independent attestation, never merged) -------
    lrb = jload("har-edges.json")
    for e in lrb["edges"]:
        cur.execute("INSERT INTO edges (src,dst,dst_kind,relation,zone,attestation,raw) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (f"har:{e['src']}",
                     norm_dst(e["dst_kind"], e["dst"]), e["dst_kind"],
                     e.get("rel", "implements"), None, "lrb2025", None))
    for e in lrb.get("session_law_edges", []):
        raw = json.dumps(e, ensure_ascii=False)
        src = e.get("har") or e.get("src")
        act = e.get("act") or e.get("dst") or ""
        cur.execute("INSERT INTO edges (src,dst,dst_kind,relation,zone,attestation,raw) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (f"har:{src}", f"slh:{act}", "session_law",
                     "implements", None, "lrb2025", raw))

    # ---- Hawaii Constitution (layer: hiconst) ------------------------------
    hc_path = os.path.join(GRAPH, "hiconst.json")
    if os.path.exists(hc_path):
        hc = json.load(open(hc_path, encoding="utf-8-sig"))
        cur.execute("INSERT OR REPLACE INTO sources VALUES (?,?,?,?,?,?)",
                    ("hiconst", hc["url"], "Legislative Reference Bureau",
                     hc["retrieved"], None,
                     "the whole Constitution on one LRB page; NOT in the HRS "
                     "index on capitol.hawaii.gov"))
        for a in hc["articles"]:
            cur.execute("INSERT OR REPLACE INTO units VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (f"hiconst:art:{a['roman']}", "hiconst", "article",
                         a["roman"], a["title"], None, 0, 0, hc["url"], None))
        for sid, s in hc["sections"].items():
            cur.execute("INSERT OR REPLACE INTO sections VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (sid, "hiconst", s["num"] or "preamble", s["article"],
                         s["catchline"], "", int(s["repealed"]), None,
                         hc["url"], hc["retrieved"], hc["retrieved"], "hiconst"))
            for zone, text in (("operative", s["operative"]),
                               ("history", s["history"])):
                if text and text.strip():
                    cur.execute("INSERT OR REPLACE INTO zones VALUES (?,?,?)",
                                (sid, zone, text))
                    cur.execute("INSERT INTO fts VALUES (?,?,?,?)",
                                (sid, zone, s["catchline"] or "", text))
        for e in hc["edges"]:
            cur.execute("INSERT INTO edges (src,dst,dst_kind,relation,zone,"
                        "attestation,raw) VALUES (?,?,?,?,?,?,?)",
                        (e["src"], norm_dst(e["kind"], e["target"]), e["kind"],
                         "cites", "operative", "const_text", e.get("raw")))
        for key, note_list in hc.get("publisher_notes", {}).items():
            cur.execute("INSERT INTO problems VALUES (?,?)",
                        ("hiconst_publisher_note",
                         json.dumps({"at": key, "notes": note_list},
                                    ensure_ascii=False)))

    # ---- CSC advisory opinions ---------------------------------------------
    ao_path = os.path.join(GRAPH, "csc-aos.json")
    if os.path.exists(ao_path):
        ao = json.load(open(ao_path, encoding="utf-8-sig"))
        for o in ao["opinions"]:
            cur.execute("INSERT OR REPLACE INTO opinions VALUES "
                        "(?,?,?,?,?,?,?,?,?,?,?)",
                        (o["id"], o["kind"], o["number"], o.get("date"),
                         o.get("subject"), o.get("body"), o.get("form"),
                         int(bool(o.get("text_layer"))), o["url"],
                         o.get("sha256"), ao["retrieved"]))
            if o.get("body"):
                cur.execute("INSERT INTO fts VALUES (?,?,?,?)",
                            (o["id"], "opinion", o.get("subject") or "",
                             o["body"]))
        for e in ao["edges"]:
            cur.execute("INSERT INTO edges (src,dst,dst_kind,relation,zone,"
                        "attestation,raw) VALUES (?,?,?,?,?,?,?)",
                        (e["src"], norm_dst(e["kind"], e["target"]), e["kind"],
                         "cites", "operative", "opinion_text", e.get("raw")))
        for p in ao.get("problems", []):
            cur.execute("INSERT INTO problems VALUES (?,?)",
                        ("csc-aos", json.dumps(p, ensure_ascii=False)))

    # ---- annotation-zone citations: cases / AG ops / law reviews -----------
    # The revisor's Case Notes as edges — leads, not authority (attestation
    # 'revisor_note'). Produced by tools/case_cites.py; optional so a fresh
    # clone can build before running that stage.
    ac_path = os.path.join(GRAPH, "annotation-cites.json")
    if os.path.exists(ac_path):
        ac = json.load(open(ac_path, encoding="utf-8-sig"))
        for e in ac["edges"]:
            cur.execute("INSERT INTO edges (src,dst,dst_kind,relation,zone,"
                        "attestation,raw,context) VALUES (?,?,?,?,?,?,?,?)",
                        (e["src"], e["dst"], e["dst_kind"], e["relation"],
                         "annotation", ac.get("attestation", "revisor_note"),
                         e.get("raw"), e.get("context")))

    # ---- act -> statute edges (layer 4, Session Laws) -----------------------
    # Which acts touched a section, from the sibling hi-leg-db. Produced by
    # tools/act_bridge.py; optional, like the case cites, so a clone without
    # hi-leg-db present still builds. Two attestations are carried
    # unmerged -- 'act_text' (the act's own operative sentence, precise) and
    # 'bill_refs' (hi-leg-db's citation extraction, broader and looser).
    ae_path = os.path.join(GRAPH, "act-edges.json")
    if os.path.exists(ae_path):
        ae = json.load(open(ae_path, encoding="utf-8-sig"))
        for e in ae["edges"]:
            cur.execute("INSERT INTO edges (src,dst,dst_kind,relation,zone,"
                        "attestation,raw,context) VALUES (?,?,?,?,?,?,?,?)",
                        (e["src"], e["dst"], e["dst_kind"], e["relation"],
                         None, e["attestation"], e.get("raw"),
                         e.get("context")))
        cur.execute("INSERT INTO meta VALUES ('act_edges',?)",
                    (str(len(ae["edges"])),))
        cur.execute("INSERT INTO meta VALUES ('act_edges_built',?)",
                    (ae.get("built", ""),))

    # ---- definitions --------------------------------------------------------
    for d in jload("definitions.json")["definitions"]:
        cur.execute("INSERT INTO definitions VALUES (?,?,?,?,?,?,?,?)",
                    (d["term"], d["term_norm"], f"hrs:{d['section']}",
                     d.get("scope_type"), d.get("scope_key"),
                     d.get("scope_rank"), d.get("verb"), d["text"]))

    # ---- problems -----------------------------------------------------------
    for fname in ("parse_problems.json", "har_text_problems.json",
                  "har_directory_problems.json", "har_crosswalk_problems.json"):
        data = jload(fname)
        items = data.get("problems", data) if isinstance(data, dict) else data
        if isinstance(items, list):
            for it in items:
                cur.execute("INSERT INTO problems VALUES (?,?)",
                            (fname, json.dumps(it, ensure_ascii=False)))

    # ---- restore hand-written rows (the contract) ---------------------------
    for row in preserved_ann:
        cur.execute("INSERT OR REPLACE INTO annotations VALUES (?,?,?,?)", row)
    for row in preserved_doc:
        cur.execute("INSERT OR REPLACE INTO doctrine VALUES (?,?,?,?,?,?)", row)

    cur.execute("INSERT INTO meta VALUES ('schema_version','1')")
    cur.execute("INSERT INTO meta VALUES ('built',?)", (today,))
    con.commit()
    return con, n_zones


BEGIN, END = "<!-- BEGIN CURATED -->", "<!-- END CURATED -->"


def migrate_handwritten(con, base=VAULT):
    """One-time pull of hand-written content out of the retiring page layer:
    curated blocks -> annotations; concepts/agencies/synthesis -> doctrine.
    Safe to re-run only while the pages still exist; after the pages are
    stripped, annotations/doctrine tables ARE the source of truth."""
    cur = con.cursor()
    today = date.today().isoformat()
    n_ann = 0
    stat_dir = os.path.join(base, "statutes")
    if os.path.isdir(stat_dir):
        for fn in os.listdir(stat_dir):
            path = os.path.join(stat_dir, fn)
            txt = open(path, encoding="utf-8").read()
            i, j = txt.find(BEGIN), txt.find(END)
            if i == -1 or j == -1:
                continue
            body = re.sub(r"<!--.*?-->", "", txt[i + len(BEGIN):j],
                          flags=re.S).strip()
            if not body:
                continue
            m = re.search(r'authority: "HRS §([^"]+)"', txt)
            if not m:
                continue
            cur.execute("INSERT OR REPLACE INTO annotations VALUES (?,?,?,?)",
                        (f"hrs:{m.group(1)}", body, today, today))
            n_ann += 1
    n_doc = 0
    for folder, kind in (("concepts", "doctrine"), ("agencies", "agency")):
        d = os.path.join(base, folder)
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if not fn.endswith(".md"):
                continue
            body = open(os.path.join(d, fn), encoding="utf-8").read()
            tm = re.search(r'title:\s*"?([^"\n]+)"?', body)
            cur.execute("INSERT OR REPLACE INTO doctrine VALUES (?,?,?,?,?,?)",
                        (fn[:-3], kind, tm.group(1).strip() if tm else fn[:-3],
                         body, today, today))
            n_doc += 1
    dl = os.path.join(base, "deadlines.md")
    if os.path.exists(dl):
        cur.execute("INSERT OR REPLACE INTO doctrine VALUES (?,?,?,?,?,?)",
                    ("deadlines", "synthesis", "Deadlines — date-driven obligations",
                     open(dl, encoding="utf-8").read(), today, today))
        n_doc += 1
    con.commit()
    return n_ann, n_doc


def validate(con):
    cur = con.cursor()
    checks = []
    def q(sql):
        return cur.execute(sql).fetchone()[0]
    checks.append(("sections", q("SELECT COUNT(*) FROM sections"), 34912))
    checks.append(("hiconst sections", q("SELECT COUNT(*) FROM sections WHERE layer='hiconst'"), 172))
    checks.append(("hiconst articles", q("SELECT COUNT(*) FROM units WHERE layer='hiconst'"), 18))
    checks.append(("csc advisory opinions", q("SELECT COUNT(*) FROM opinions WHERE kind='csc_advisory'"), 56))
    checks.append(("opinions w/ text", q("SELECT COUNT(*) FROM opinions WHERE text_layer=1"), 49))
    checks.append(("hrs sections", q("SELECT COUNT(*) FROM sections WHERE layer='hrs'"), 22972))
    checks.append(("har sections", q("SELECT COUNT(*) FROM sections WHERE layer='har'"), 11768))
    checks.append(("definitions", q("SELECT COUNT(*) FROM definitions"), 12146))
    checks.append(("annotations", q("SELECT COUNT(*) FROM annotations"), 13))
    checks.append(("hrs_text edges", q("SELECT COUNT(*) FROM edges WHERE attestation='hrs_text'"), 38759))
    checks.append(("rule_text edges", q("SELECT COUNT(*) FROM edges WHERE attestation='rule_text'"), 56559))
    checks.append(("lrb edges >", q("SELECT COUNT(*) FROM edges WHERE attestation='lrb2025'"), 42000))
    checks.append(("hrs chapter units >", q("SELECT COUNT(*) FROM units WHERE layer='hrs'"), 1000))
    checks.append(("har title units", q("SELECT COUNT(*) FROM units WHERE layer='har' AND kind='title'"), 24))
    checks.append(("har chapter units", q("SELECT COUNT(*) FROM units WHERE layer='har' AND kind='chapter'"), 1583))
    checks.append(("har listings (meta)", q("SELECT CAST(value AS INT) FROM meta WHERE key='har_chapter_listings'"), 1595))
    # Optional stage: only asserted once the bridge has been run, so a clone
    # without the sibling hi-leg-db still validates clean.
    if q("SELECT COUNT(*) FROM meta WHERE key='act_edges'"):
        checks.append(("act edges >", q(
            "SELECT COUNT(*) FROM edges WHERE dst_kind='session_law' "
            "AND attestation IN ('act_text','bill_refs')"), 8000))
        checks.append(("acts represented >", q(
            "SELECT COUNT(DISTINCT dst) FROM edges WHERE dst_kind='session_law' "
            "AND attestation IN ('act_text','bill_refs')"), 2700))
    ok = True
    for name, got, want in checks:
        good = got >= want if name.endswith(">") else got == want
        ok &= good
        print(f"  {'OK ' if good else 'FAIL'} {name:18s} {got}  (expect {'≥' if name.endswith('>') else ''}{want})")
    # spot query: the §11-314 inbound rule map
    n = q("SELECT COUNT(DISTINCT src) FROM edges WHERE dst='hrs:11-314' "
          "AND relation='authorized_by'")
    print(f"  spot: rules authorized by §11-314 -> {n} (expect >100)")
    ok &= n > 100
    # fts smoke test
    n = q("SELECT COUNT(*) FROM fts WHERE fts MATCH 'expressly advocating'")
    print(f"  spot: FTS 'expressly advocating' -> {n} rows (expect >0)")
    ok &= n > 0
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    path = DB_PATH + ".check" if args.check else DB_PATH
    con, n_zones = build(path)
    n_ann, n_doc = migrate_handwritten(con)
    print(f"built {os.path.basename(path)}: {n_zones} zone rows, "
          f"{n_ann} annotations, {n_doc} doctrine rows")
    ok = validate(con)
    con.close()
    if args.check:
        os.remove(path)
    if not ok:
        sys.exit(1)
    print("VALID")


if __name__ == "__main__":
    main()
