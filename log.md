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
