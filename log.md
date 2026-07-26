# Log

Append-only. Newest at the bottom. Entry headers use a fixed prefix so the file stays greppable:
`grep "^## \[" log.md | tail -5`.

Kinds: `schema` · `fetch` · `ingest` · `query` · `lint`

---

## [2026-07-24] schema | wiki initialized

Scope set with Sam: **Hawaiʻi election and campaign law** (HRS Ch. 11–13, campaign finance,
TCPA/texting, 501(c) electoral rules). Sourcing mode: Sam drops files **+** Claude fetches official
sources **+** seed from existing `Firefly's Path` work.

Created `CLAUDE.md` (schema), `index.md`, `log.md`, `overview.md`, `deadlines.md`,
`open-questions.md`, and the folder conventions: `raw/`, `sources/`, `statutes/`, `agencies/`,
`concepts/`, `procedures/`, `opinions/`, `questions/`.

Key schema decisions: `status` frontmatter as an honesty flag (`verified` / `derived` /
`unverified` / `contested` / `superseded`); quoted statute text kept strictly separate from
interpretation; pin cites required; permanent rules stored separately from published dates;
`superseded` instead of deletion.

## [2026-07-24] fetch | capitol.hawaii.gov + elections.hawaii.gov

Retrieved HRS §11-102 and the OoE "2026 Election Dates & Deadline" widget into `raw/`.

**Gotchas recorded:** `capitol.hawaii.gov` returns **HTTP 403 to WebFetch** — use `curl` with a
browser User-Agent and strip HTML. `elections.hawaii.gov/election-information/` **404s**; the dates
widget lives in the sidebar of ordinary pages such as `/voting/`.

## [2026-07-24] ingest | HRS §11-102 — procedures for conducting elections by mail

Sources: [[src-2026-07-24-hrs-11-102]], [[src-2026-07-24-oe-election-dates-2026]].

**Created (9):** [[hrs-11-102]], [[mail-ballot-registration-cutoff]], [[ballot-package]],
[[county-clerks]], [[deadlines]], plus both source pages and the root scaffolding.

**Flagged:**
- **Contradiction found.** The published general-election registration deadline (Mon Oct 26, 2026)
  is two days later than the statutory ten-day offset (Sat Oct 24). A weekend-rollover explanation
  fails, because the primary's Saturday address-update deadline (Aug 1) was *not* rolled. Logged in
  [[open-questions]]; reconciliation table on [[deadlines]]. This corrects the rationale in a prior
  repo memory note — the dates there are right, the reason given is not.
- **Copy risk, live.** Primary registration cutoff is **Wed Jul 29, 2026 — 5 days out**. From Jul 30
  on, GOTV copy must stop saying "watch your mailbox" to unregistered voters and point them to a
  Voter Service Center (Jul 27 – Aug 8).
- **Verification debt.** Act 213 (2021) §18 and Act 166 (2022) §2 amended §11-102; what they changed
  is untraced. [[county-clerks]] is `derived` from one statute. The §11-15.2 same-day-registration
  cite is from working notes, not yet confirmed against the statute.

**Next queue** (in [[open-questions]]): HRS §12-31 → §11-302 definitions → §11-357/§11-358 limits →
§11-334 reporting schedule → HAR Title 3 Ch. 160.

## [2026-07-24] schema | merged the vault's pre-existing founding note

A hand-written `INDEX.md` already existed in the vault and was **not** overwritten. Windows
case-insensitivity meant a new `index.md` would have silently replaced it — caught before any loss.

Folded forward into [[INDEX]]: the "a statute note without a citation is worse than no note"
standing rule, the official-sources-only rule, and the load-bearing-provisions table (now carrying
ingest status per row). Added to [[open-questions]]: **HRS §12-31** (wording constraint on live
vote-page copy — promoted to the top of the ingest queue, since it binds public text today),
**escheat of unused campaign funds** (`projects/escheat-investigation/`), and **TCPA as applied in
Hawaiʻi** (still owed).

**Convention set:** the catalog file is `INDEX.md`, capitalized, linked as `[[INDEX]]`. Never
create a second `index.md`.

Removed Obsidian's stock `Welcome.md`.

## [2026-07-24] schema | session close — state handoff

Vault is self-describing: `CLAUDE.md` (schema) → [[INDEX]] (catalog) → [[open-questions]] (work
queue) → this log (history). A fresh session should read those four and needs nothing else.

**Standing state**
- 1 ingest complete. 2 sources, 9 pages, 1 statute. No procedures, opinions, or question pages yet.
- Next ingest: **HRS §12-31**, promoted above the campaign-finance queue because it constrains live
  public copy on mohoaina.com/vote today.
- Live date pressure: primary registration cutoff **Wed Jul 29, 2026**. From Jul 30, GOTV copy must
  stop telling unregistered voters to watch the mail. See [[mail-ballot-registration-cutoff]].

**Awaiting Sam**
- Whether to commit this vault to the `Firefly's Path` git repo (currently untracked) or keep it out.

## [2026-07-24] ingest | HRS election-law corpus — 14 chapters, 393 sections, full citation graph

Source: [[src-2026-07-24-hrs-election-law-corpus]]. Discovered from the Office of Elections
[election-laws page](https://elections.hawaii.gov/resources/election-laws/); text from
capitol.hawaii.gov.

**Harvested:** all 14 HRS chapters that page lists — 10, 11, 12, 13, 13D, 14, 14D, 15, 15D, 16, 17,
19, 25, 50. **393 sections**, 407 raw files, one retrieval stamp, zero fetch failures.

**Created:** 393 statute pages + 14 chapter hubs in `statutes/`; [[citation-queue]];
[[hrs-citation-graph]]; the corpus source page; `tools/` (6 scripts) and `graph/`
(sections.json, edges.json, unresolved.json, repealed_ranges.json, parse_problems.json, hrs.db).

**Updated:** [[INDEX]] (rebuilt around chapter hubs), [[deadlines]], [[open-questions]] (rewritten),
[[hrs-11-102]] (converted to the curated-block format, analysis preserved verbatim), `CLAUDE.md`
(§2 directories, §3 `depth` + curated-block contract, rule 0 expanded, new rule 10, new §5.4).

**Citation graph:** 484 edges in three zones that are never merged — **409 operative** (the law
pointing at law), **15 history** (prior numbering), **60 annotation** (revisor Case Notes).
Validated: an independent strict-regex sweep of both zones across all 393 sections found **zero**
missed citations. `parse_problems.json` is empty.

### Resolved

- **✅ The Oct 26 / Oct 24 contradiction, open since the first ingest.** The weekend-rollover rule
  is [[hrs-11-24|§11-24(a)]] (closing the register), not §11-102. §11-102(b)'s seven-day
  address-update deadline has no rollover clause, which is why Sat Aug 1 stood and Sat Oct 24
  rolled to Mon Oct 26. **All four published 2026 dates now reconcile exactly.** Both prior
  explanations were wrong, in opposite directions, and both were looking only at §11-102.
- **✅ §11-15.2 confirmed** as the same-day in-person registration authority. Safe to cite.

### Corrected

- **⚠️ §12-31 is not "the wording constraint on vote-page copy."** That description came from a
  skill's memory, not the statute. It is *Selection of party ballot; voting*, and it carries a
  sharper hazard: **a primary ballot marked across more than one party is not counted at all.**
  Any primary GOTV copy needs checking against it. Logged in [[open-questions]].

### Flagged

- **Live compliance exposure.** [[hrs-11-391|§11-391]] disclaimer duties reach any advertisement
  "communicated by electronic means" — text blasts and social creative included. Name **and
  address** of the payer, plus an approval notice unless paid by a candidate/candidate/ballot-issue
  committee. Noncandidate committees face a **$150 floor per advertisement**. Touches the
  `twilio-mms-blast` and `moho-carousel` skills.
- **HRS ch. 91 (Administrative Procedure) is the most-cited body of law outside the corpus** — 31
  operative citations, and the procedural spine under CSC enforcement. Top of [[citation-queue]].
- **Chapter 13 (Board of Education) serves no sections**, only a stub. Consistent with full repeal;
  repealing act not traced.
- **[[hrs-11-1|§11-1]] defines terms for the whole title**, not just chapter 11, so chapters 12–19
  inherit them. The graph understates this: most sections rely on it without citing it.
- **117 of 359 live sections are isolated** (cite nothing, cited by nothing). Election statutes are
  largely self-contained procedure, not a dense web.
- **Depth is honest:** 380 pages are `depth: harvested` (verbatim + graph, no reading), 13 are
  `annotated`. Sam approved ~30; 13 are done to a real standard and the remaining tranche is
  ordered in [[open-questions]] rather than padded out.

**Fetch gotchas recorded** (all silent-corruption failures, now in `CLAUDE.md` rule 0): apex host
301s to `www` so `-L` is mandatory; `/docs/HRS.htm` is windows-1252; decimal filename suffixes
concatenate (`_0005_0002` = `.52`); U+2011 non-breaking hyphens hid 11 real cross-references.

### Queued

[[citation-queue]] — 17 whole chapters, 45 sections, 4 federal citations, 2 constitutional, all
with official titles pulled from the State's master index. Also unharvested from the same OoE page:
U.S. Constitution excerpts, HAVA, Hawaiʻi Constitution excerpts, and the two HAR PDFs (ch. 3-170,
ch. 3-177). Campaign finance HAR (title 3 ch. 160) is not on that page at all.

## [2026-07-24] schema | corpus conventions recorded

`depth: harvested | annotated` added as a second honesty axis beside `status`, derived
automatically from whether a page's curated block holds prose. Curated-block contract
(`<!-- BEGIN CURATED -->`) added so a 393-page corpus stays regenerable without ever destroying
hand-written analysis; a page with no markers is refused, not overwritten. Rule 10 added on the
three citation zones. §5.4 added for bulk corpus ingest. Decimal section filenames keep the dot
(`hrs-11-15.2.md`).

## [2026-07-24] query | escheat provisions located via the citation graph

Running `hrs_refs.py 11-357 --both --depth 2` surfaced [[hrs-11-364|§11-364]] *Excess
contribution; return; escheat* as an inbound citer. A catchline search then found the rest:
[[hrs-11-384|§11-384]] (disposition of campaign funds; termination of registration) and
[[hrs-11-326|§11-326]] (termination of registration).

Escheat had been carried as an open item since the vault's founding note, described as "not yet
located in Part XIII." It was in the corpus within minutes of the corpus existing. Updated
[[open-questions]]. All three sections are still `depth: harvested` — located is not read.

## [2026-07-24] schema | definitions layer — scope-resolved term lookup

Built in response to the architectural problem that the same term is defined
differently across HRS and a definition without its scope is worse than none.

**The statute declares scope explicitly, every time**, in about five phrasings:
"whenever used in this title" ([[hrs-11-1]]), "when used in this part"
([[hrs-11-302]]), "as used in this chapter" ([[hrs-15-1]]), "in this chapter, if not
inconsistent with the context" ([[hrs-10-2]]), "for the purposes of this section"
([[hrs-19-3]], [[hrs-11-341]]). All machine-extractable.

New `graph/definitions.json` + `definition` table: term, defining section, declared
scope type and key, verbatim text, and any import ("as defined in section 11-1").
New `tools/hrs_define.py` resolves a term **at a section**, walking outward
section → subpart → part → chapter → title. First hit controls; everything it
shadows is printed, because the shadowed ones are what you would otherwise quote.

**151 terms, 139 distinct, 11 defined in more than one scope** — in only 1.7% of HRS.
"Office" already has three competing definitions: [[hrs-10-2]] (ch. 10, the Office of
Hawaiian Affairs), [[hrs-11-1]] (Title 2, "an elective public office"), and
[[hrs-11-302]] (Part XIII, excludes federal and neighborhood board). All three are
correct; which one applies depends entirely on where you are standing.

Two extraction bugs found and fixed, both silent:
- Scope was bound from a fixed look-back window, so only the **first** term in a
  definitions list got the declared scope and the rest fell back to chapter default.
  Now every scope declaration in a section is tracked in order and each term binds to
  the last one before it, which also handles mid-section shifts like §19-3(b).
- [[hrs-11-1]] uses older drafting with **no verb at all** (`"Office", an elective
  public office.`). Its terms were being swallowed into the preceding definition.
  Comma-form extraction added, trusted only inside sections catchlined "Definitions".

Added `title_group` to the section table. Title-scoped definitions reach every chapter
in the title, so without it [[hrs-11-1]] failed to resolve for chapters 12 through 19 —
exactly the inheritance flagged as most important in the corpus ingest.

## [2026-07-24] fetch | enumerated the whole HRS

`tools/enumerate_hrs.py` → `graph/hrs-universe.json`. **14 volumes, 1,108 chapters,
22,973 sections**, 293 chapters empty or repealed. Directory listings only, no section
text. The current election corpus is **1.7%** of HRS. No bulk download exists;
`/hrscurrent/hrs.zip` and `/legislation/` both 404 and `/docs/` is a rendered page,
so a full harvest is ~24,000 individual requests.

## [2026-07-24] schema | corpus split into its own repo

The vault now lives at `C:\Law\hawaii-state-law` as an independent git repo, junctioned into
`Firefly's Path` at `LLM Wikis/Hawaii State Law` so every path, skill, and doc reference keeps
resolving. Moved with `git subtree split`, full history preserved (4 commits), all 858 tracked
blob hashes verified identical before anything was removed from the parent.

Reason: this is a corpus vault. Its bulk comes from ingestion, not from writing. HRS Title 2 alone
is 393 sections; all of HRS is 22,973 across 1,108 chapters, roughly 240MB. Inside the workspace
repo that would slow every clone permanently and grow with every session.

Flagged:
- `graph/hrs.db` was never actually tracked, despite `.gitignore` carrying a comment saying it was
  deliberately kept. The parent repo had a blanket `*.db` rule that silently won. Now tracked here.
- `mklink /J` refuses an existing path, and the emptied directory could not be removed: Obsidian
  held the vault open and it was also the session's own working directory. Set the reparse point
  on the empty directory directly via `FSCTL_SET_REPARSE_POINT`, which is what mklink does
  internally. Recorded in the `repo-split` skill.

## [2026-07-24] fetch | mapped the layers of Hawaiʻi law beyond HRS

Question: what comprises state law other than HRS and administrative rules, and does case law
belong here. Probed each candidate primary source rather than asserting from memory.

Created: `sources-of-law.md` — eight layers, verified primary source per layer, what this wiki
holds of each, and a sequencing table ranked by operative value per unit of work.

Verified live 2026-07-24: Hawaiʻi Constitution at `lrb.hawaii.gov/constitution/` (200, 236KB);
session laws at `capitol.hawaii.gov/slh/`; HAR index at `ltgov.hawaii.gov/the-office/administrative-rules/`,
organised by department title; Judiciary opinions at `courts.state.hi.us/opinions_and_orders/opinions`.

Findings:
- **The Hawaiʻi Constitution is not in the HRS master index.** A crawl of `hrscurrent/` looks
  complete while omitting the supreme state authority. Article II is the elections article.
- **`csc.hawaii.gov` is a dead 135-byte meta-refresh stub** pointing at `ags.hawaii.gov/campaign/`.
  A meta-refresh is not an HTTP redirect, so `curl -L` does not follow it and a fetcher receives
  HTTP 200 with an empty document. Same silent-corruption class as the 403 and the apex-redirect
  stub. Added to schema rule 0; rule 1's source list replaced with a per-layer table.
- **112 case citations across 58 sections are already in `raw/`**, in the annotation zone, along
  with Attorney General Opinions and Law Journals and Reviews headings. Case law joins the graph as
  inbound edges and needs no new crawl to start.
- AG opinions index not located; two candidate paths 404.

Updated: `CLAUDE.md` (rule 0 gotcha, rule 1 rewritten as a source table), `open-questions.md`
(sources section), `INDEX.md` (start-here row).

Position taken: finishing HRS is the largest available crawl and **not** the highest-value next
move. The unanswered election-law questions sit in the constitution, the rules, the counties, and
the cases, not in HRS chapters 431 or 490.

## [2026-07-25] ingest | the whole HAR corpus, enumerated and cross-referenced

Goal was all of HAR, not the election slice. Delivered: the **enumeration** and the **cross-layer
edge layer**. Not delivered: rule text. That split is deliberate and is the honest state — see
"What is not done" below.

**The whole job turned on one document.** There is no central full-text source for HAR and no
verified title count: `ltgov.hawaii.gov` omits titles 1, 9, 21 and 22, `ags.hawaii.gov` is DAGS's
own rules only, Justia 403s to any client, Lexis is paywalled. The authoritative enumeration turned
out to be a single LRB PDF whose filename actively misleads — `2025AdminRules_Supplement.pdf` is
not a supplement, it is the *2025 Table of Statutory Sections Implemented **and Directory***,
published July 2026, covering rules filed before 2026-01-01, and it "replaces all of the Tables
published before this date." Reading its foreword before crawling anything saved the whole approach.

Created:
- `tools/har_lib.py`, `tools/har_directory.py`, `tools/har_crosswalk.py`, `tools/har_sources.py`
- `graph/har-universe.json` — **24 titles, 1,595 chapters, 991 live**, each with catchline,
  subtitle/part, repealed/reserved, and the department's canonical rules URL as the LRB publishes it
- `graph/har-edges.json` — **42,002** HRS to HAR `implements` edges across **4,431** HRS sections and
  **19,633** HAR sections; **455** session-law edges; 63 LRB footnotes
- `graph/har-sources.json` — per-title publication shape, doc counts, bytes, size estimate
- `sources/src-2026-07-25-lrb-har-table-and-directory.md`
- `har-citation-graph.md`

Updated: `CLAUDE.md` (rules 11-14, four new rule-0 gotchas, HAR pipeline, directory map),
`INDEX.md` (HAR layer section, tooling, sources), `open-questions.md`, `.gitignore`.

**Corpus size, for the criterion-B threshold:** 750 documents / **249 MB measured** across 19 of 24
titles and 792 of 991 live chapters. Median 0.34 MB per live chapter projects **~317 MB** for the
whole download, but bytes-per-chapter ranges 0.01 MB (DLNR) to 6.88 MB (Taxation, scanned), so that
is an order-of-magnitude figure, not a budget. **Only extracted text plus a SHA-256 per PDF
gets committed — roughly 3-8% of that.** The download figure is not the repository figure.

### Findings that change what this wiki says

- **HAR title 2 subtitle 4 "Elections" is entirely repealed** — chapters 34-38, 40, 50-54, plus
  2-14.1 and 2-14.2. The Campaign Spending Commission rules the 2001 crosswalk points at (2-51,
  2-14.1) are dead; CSC rules are now 3-160 and 3-161 under DAGS. This is why an earlier session
  could not find 2-51 on ltgov. **The 2001 crosswalk is superseded and was used for no edge.**
- **HAR 3-160 carries 141 `implements` edges** into HRS chapter 11's campaign-finance part —
  sections 11-302, 11-311, 11-314, 11-321 to 11-326, 11-331, 11-333, 11-334. That is the
  statute-to-rule map for what Sam actually files under. 2-51 has zero.
- **`Auth:` and `Imp:` are two different relations** and the handoff was right to flag it, but there
  are *two* delegation-ish relations, not one. A rule's bracketed source note gives dates; `(Auth:)`
  gives what authorised it; `(Imp:)` gives what it implements. A court asking whether a rule exceeds
  authority looks only at `Auth:`. Merged, the graph cannot answer whether a rule is *valid*. HAR
  therefore has **five zones** to HRS's three, and edges are now **typed** (`cites`,
  `authorized_by`, `implements`, `delegates_to`, `renumbered_from`). Schema rules 11-13.
  **`Auth:` is not in the graph at all** — the LRB table carries only `Imp:`. It needs rule text.
- **AG opinions index located**, and it is LRB-published, not AG-published, which is why every
  `ag.hawaii.gov` path 404s: `lrb.hawaii.gov/wp-content/uploads/AGOpinions.pdf`. General pattern
  worth keeping: when a Hawaii index is missing from the agency that owns the subject, look at the
  LRB.
- **CSC advisory opinions index located**:
  `ags.hawaii.gov/campaign/legal-resources/advisory-opinions/`, 14 PDFs, AO10-01 through AO26-02.
- **`tools/hrs_lib.py` will silently drop colon-form HRS citations.** Chapters 412, 431 and 490
  number sections `412:2-105`, `431:10A-301`. `_SEC` does not match a colon. 289 crosswalk keys use
  the form. Harmless today (corpus is chapters 10-50), silently lossy the moment a harvest reaches
  412 or 431. Filed in `open-questions.md`.

### Validation, because a count is not a check

`graph/har_directory_problems.json` holds 6 entries and `graph/har_crosswalk_problems.json` holds
14; **every one is a defect in the LRB source, not a parse failure**, and each is named on the
source page:
- Title 15 lists chapters 210, 211, 301, 310, 321 **twice** under different subtitles, and the two
  listings give **different catchlines** for 301 and 310. Title 19 lists chapter **150 both live
  ("Autonomous Vehicle Regulations") and repealed**. Chapter numbers are unique within a title, so
  the compilation contradicts itself. Both listings kept and flagged; deduping would pick a winner
  arbitrarily and hide a real conflict. 19-150 is now an open question.
- Ten crosswalk keys are malformed in the source (`92F-__`, `189-)3.5`, `431:7-`, `157.31`), leaving
  three HAR citations unreachable. Not guessed at — a fabricated pin cite is worse than a gap.
- HAR 23-700 has no catchline, only footnote 64: "Title probably should be 'Hawaii Paroling
  Authority'."

The strict independent sweep went **458 missed citations to 3**, and all 3 trace to those source
typos. Six things were caught only because the sweep existed, each of which fails silently rather
than loudly:
1. `pdftotext -layout` interleaves a two-column table, landing a wrapped cell on another entry's row.
2. Chapter numbers are **right-aligned**, so wide cross-title numbers (`17-2015`) cross the gutter
   leftward. Columns must split on word **centre**, not left edge.
3. `X-Y` in the chapter column is two different things: X in 1..24 is a chapter that moved
   departments and kept its number (`2-71` OIP under title 3, `6-60` PUC under title 16, `15-185`
   HPHA under title 17); otherwise it is a section range inside chapter X (`1454-1 to 1454-56`).
   Conflating them invents chapters 1454-1 and 72-13, which do not exist. **Never renumbered** —
   schema rule 13.
4. A 6.96pt superscript glues to the number: `70064` is chapter 700 + footnote 64.
5. The PDF splits keywords (`S ubtitle 6`), silently reassigning every chapter below it.
6. **A run of continuation rows crosses page boundaries** — a rule list started in the right column
   of one page continues in the left column of the next. Resetting state per page silently dropped
   ~5,000 edges and the output still looked plausible.

Also: the rules cell is compressed with an **implicit prefix** — `13-275-1, 2, 5 to 14` means
sections 13-275-1, -2, -5 through -14 — and HAR section numbers run to four parts
(`18-231-9.9-07`) and occasionally five (`11-54-9.1.01`). A too-tight pattern drops citations
without erroring.

### On delegation

24 Haiku recon agents mapped the department sites in parallel; that was right for breadth and it
produced the byte counts. It also produced three confident falsehoods, all caught by checking
against the LRB rather than by asking another agent: title 21 "has no rules" (they are the **State
Ethics Commission's**, 10 chapters, 2 PDFs, 12.5 MB — the agent had been pointed at LRB/Auditor/
Ombudsman); title 19 "serves University of Hawaii rules, no DOT rules" (**false** — 32 DOT
chapters, verified on retry); title 22 "none" (LRB lists 21 live chapters, still unresolved).
Recorded in `graph/har-sources.json` under `url_disagreements`; the LRB wins every time.

New gotcha, cost five agent runs: **PowerShell writes UTF-8 with a BOM by default and `json.load`
rejects it outright** (`Unexpected UTF-8 BOM`). Anything a subagent writes on Windows via
redirection, `Out-File` or `Set-Content` needs `encoding="utf-8-sig"` on the way back in, or should
be written through Python instead. Added to rule 0.

### What is not done

The rule **text**. `graph/har-sources.json` is the target map for it; the remaining work is the
harvester with per-department adapters, the `Auth:`/`Imp:`/source-note parser, the time axis from
`Eff`/`am`/`comp`/`R`, and `har/` pages on the curated-block contract. Title 22 needs a human look.
Storage policy holds unchanged: at this scale, text plus hashes is the only sane thing to track.

## [2026-07-25] ingest | CSC rule text — HAR 3-160 + 3-161 in full, first rule pages, first Auth edges

The first rule **text** in the corpus: both Campaign Spending Commission chapters, from the
chapter PDFs on `ags.hawaii.gov/campaign/legal-resources/hawaii-administrative-rules/`
(eff. 2016-12-09, retrieved 2026-07-25). 121 sections (48 + 73, six repealed) parsed into the
five zones of schema rule 11 and written as `har/` pages on the curated-block contract;
**1,047 typed edges** including the graph's first `authorized_by`. Pipeline:
`har_text.py` (PDF → verbatim `raw/har/*.txt` + SHA-256 manifest) → `har_rules.py`
(zones + edges + validation) → `har_build_pages.py`.

Created: [[src-2026-07-25-csc-har-rules]], [[har-3-160]], [[har-3-161]], 121 rule pages,
`graph/har-rules.json`, `graph/har_text_problems.json`, the three tools.
Updated: CLAUDE.md (type `rule`, slug example fix, HAR text pipeline), [[INDEX]],
[[har-citation-graph]] (claims 1 and 4 narrowed), [[open-questions]].

What the ingest established:

- **Validity questions now answerable for CSC rules.** Nearly every rule's `Auth:` is
  §11-314(8) (general rulemaking); 3-161's procedural rules add §91-2. `Imp:` maps each rule
  to the campaign-finance sections it interprets.
- **The print fights extraction**: a rubber received-stamp bleeds into the text layer on
  nearly every page. ~40 of 121 source notes lose a bracket to OCR; three section numbers
  misprint (`§3-160-4 0`, `§3 161-41`, `§3-161 51`); citations inside notes drop hyphens
  (`11 336`), grow stamp digits (`11-4071`), or take an OCR'd `I` (`11- I 407`). 17 cites
  healed, every one corroborated first — by the LRB Table's edge for that same rule (Imp) or
  by existence in the harvested HRS corpus (Auth) — and logged in
  `graph/har_text_problems.json`. Uncorroborated residue stays flagged, never guessed.
- **Validation stack**: TOC-vs-body assertion (each chapter's own TOC as ground truth, zero
  mismatch after repairs); exhaustive Auth/Imp token sweep (963 tokens, zero missed);
  two-attestation cross-check of rule-text `Imp:` vs the LRB Table — **115/116 rules agree**.
- **The one disagreement is an LRB defect**: the 2025 Table lists repealed §3-161-84 as
  implementing §11-314. Stale edge; filed in [[open-questions]].
- **The shared HRS citation extractor had two silent-loss defects**, found here, fixed for
  both layers: a pin cite broke list parsing (`11-359(b), and 11-360` dropped 11-360) and an
  Oxford comma broke the separator. Regenerating the HRS graph recovered **8 silently missing
  edges** (484 → 492); all 393 statute pages rebuilt, all 13 curated blocks preserved.
- **Cross-title cite caught**: §3-160-10 charges record-search fees under HAR §2-71-31 — the
  OIP records rules, a title-2 chapter hosted under title 3. Queued in [[open-questions]].
- The CSC also posts its own **HRS compilation updated July 2026** (`HRS-JUL2026.pdf`) — the
  natural check for post-2016 amendment currency, queued.

## [2026-07-26] ingest | HRS ch. 91 (Administrative Procedure) — first citation-frontier chapter

The most-cited body of law outside the corpus, pulled in because the corpus itself demanded it:
31 operative cites before the CSC rule-text ingest, 148 wikilinks to §91-2 alone after it. This
is HAPA — how agencies (including the CSC) adopt rules, run contested cases, and get reviewed.

28 sections harvested from `capitol.hawaii.gov/hrscurrent/Vol02_Ch0046-0115/HRS0091/`, zero
parse problems. Corpus now **421 sections / 15 chapters / 638 edges**. All ch. 91 wikilinks
from [[har-3-161]] resolve; the citation queue's new leaders are §92-16 (Sunshine Law) and
ch. 92F (UIPA).

Created: [[src-2026-07-26-hrs-ch91]], [[hrs-ch91]] + 28 statute pages.
Updated: `hrs_lib.py` CHAPTERS (frontier-ingest convention, marked inline), `build_pages.py`
(per-chapter source attribution via SRC_BY_CHAPTER), [[INDEX]], [[open-questions]],
CLAUDE.md rule 0.

Two mechanics found the hard way:

- **capitol.hawaii.gov's WAF now 403s Python's TLS fingerprint** — the same urllib code that
  fetched 850 files on 07-24 fails with any header set, while curl passes. Block is on the
  TLS handshake (JA3), not headers. `hrs_lib.fetch` falls back to a `curl` subprocess on 403;
  recorded as a rule-0 gotcha.
- **`harvest_hrs.py --only` rebuilt `_manifest.json` with only the processed chapter**,
  silently dropping the other 393 entries. Caught same-session; a full cached run (cheap, no
  fetches) restores it, and the docstring now warns.

## [2026-07-26] schema | scope widened to ALL of Hawaii law, every surface

Sam's call, correcting the recorded charter: the ambition is a graph-mapped database of the
whole body of Hawaii law — constitution, HRS, session laws, HAR, case law, agency opinions,
county charters/ordinances, federal overlay — not the election/campaign slice alone. The
election slice stays the sequencing beachhead (it serves live filing work) but is not the
boundary. CLAUDE.md "What this is" rewritten; [[sources-of-law]] is now the coverage ledger,
its table split into **mapped** vs **read** per layer and brought current (HAR fully mapped,
CSC chapters + ch. 91 read, both opinion indexes located, AG-index stale line fixed).
Decision recorded in the parent OS decision log 2026-07-26.
