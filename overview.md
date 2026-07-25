---
type: synthesis
title: Overview — Hawaiʻi election & campaign law
aliases: ["home", "start here"]
status: derived
last_verified: 2026-07-24
tags: [overview]
---

# Overview — Hawaiʻi election & campaign law

The front door. Six territories, with honest coverage status. See [[INDEX]] for the catalog,
[[hrs-citation-graph]] to query cross-references, and [[open-questions]] for the work queue.

**As of the 2026-07-24 corpus ingest the statutory text for most of this map is now in the vault**
— 393 sections across 14 chapters. What is mostly *not* here is the reading of it: 380 pages are
`depth: harvested` (verbatim text plus citation graph, no interpretation) and 13 are `annotated`.
The territory ratings below track **annotation**, not whether the text exists.

> Not legal advice. Every page points at a primary source; when a question turns on real legal
> judgment, this wiki says so instead of guessing.

---

## 1. Voting and election administration — 🟢 text complete, partly annotated

Who is on the rolls, how ballots reach them, how they get counted. State law, county execution.

- **Annotated:** [[hrs-11-102]] (all-mail mechanics), [[hrs-11-24]] (closing the register + the
  rollover rule that explains the published dates), [[hrs-11-15.2]] (same-day registration),
  [[hrs-11-15.3]] (online registration), [[hrs-11-92.1]] (voter service centers),
  [[hrs-11-1.52]] (ERIC), plus [[ballot-package]], [[mail-ballot-registration-cutoff]],
  [[deadlines]], [[county-clerks]].
- **Harvested, not yet read:** [[hrs-ch15]] (absentee), [[hrs-ch15d]] (military/overseas),
  [[hrs-ch16]] (voting systems), chapter 11 Parts II-XI — signature verification and cure,
  boards of registration, recounts and contests.
- **Still missing entirely:** [[office-of-elections]] and [[campaign-spending-commission]] agency
  pages; the two HAR chapters (3-170, 3-177) linked from the OoE page as PDFs.

## 2. Candidacy and ballot access — 🟡 text complete, unannotated

Getting a name on the ballot and keeping it there. HRS Ch. 12 ([[hrs-ch12]], 17 sections, all
harvested), plus [[hrs-ch17]] (vacancies) and [[hrs-ch14]] (presidential).
**[[hrs-12-31]] is annotated** and carries a live copy hazard: a primary ballot marked across more
than one party is not counted at all.

- Qualifications for office, nomination papers and signature counts, filing deadlines and fees,
  partisan vs nonpartisan races (relevant to county council and OHA), withdrawal, ballot name
  formatting, party primaries.

## 3. Campaign finance — 🟡 text complete, 4 of 86 annotated

HRS Ch. 11 Part XIII, §11-301 to §11-435, **all 86 sections harvested**, in ten subparts:
A General Provisions · B Campaign Spending Commission · C Registration · D Reporting and Filing ·
E Contributions · F Loans · G Expenditures · H Advertisements · I Enforcement · J Partial Public
Financing. Administered by the [[campaign-spending-commission]].

- **Annotated:** [[hrs-11-302]] (definitions), [[hrs-11-357]] (contribution limits),
  [[hrs-11-334]] (the reporting calendar), [[hrs-11-391]] (advertisement disclaimers).
- **The rules are still missing.** HAR Title 3 Ch. 160 is *not* linked from the Office of
  Elections page; the CSC publishes separately. That is now the highest-value campaign finance gap.

- Committee registration and organizational reports; contribution limits by office and by donor
  type; prohibited sources; in-kind and non-monetary contributions; independent expenditures and
  noncandidate committees; the reporting calendar; Schedules A/B/C/D; surplus and termination;
  loans and candidate self-funding; fronted expenses and reimbursement; penalties.
- Live tooling already exists in `Firefly's Path` — the `hawaii-campaign-finance`, `csc-filer`,
  and `csc-reconciliation` skills. The wiki should hold the **law and the why**; those skills hold
  the **runbook**. Ingesting the statutes here is what lets a filing question get answered from
  authority rather than from accumulated habit.

## 4. Political communications — 🟡 state side started, federal side untouched

Mixed state and **federal** layer. Do not let one answer the other.

- State: **[[hrs-11-391]] is annotated** and is a live constraint on our own outbound work — its
  disclaimer duty expressly reaches advertisements "communicated by electronic means," which
  includes text blasts and social creative. Electioneering communications (§11-341) and sign rules
  are harvested but unread.
- Federal: TCPA and FCC rules on texting and robocalls, 10DLC/carrier registration, consent and
  opt-out. Directly load-bearing for the text-blast operation.

## 5. Nonprofits and electoral activity — 🔴 not started

Federal tax law intersecting state electoral law.

- 501(c)(3) absolute prohibition on candidate intervention; 501(c)(4) permissible political
  activity and its limits; when an entity becomes a noncandidate committee under state law;
  coordination; nonpartisan voter education as a safe harbor.

## 6. Enforcement and remedies — 🟡 text complete, 1 annotated

- **Annotated:** [[hrs-19-3]] (election frauds, bribery, intimidation — including the 200-foot
  unconcealed-carry rule at voter service centers).
- **Harvested:** Part XIII subpart I ([[hrs-11-401]]-[[hrs-11-412]], CSC enforcement),
  [[hrs-ch19]] offences and penalties, chapter 11 Part XI election contests.
- **Missing:** HRS ch. 91 (Administrative Procedure) is the procedural spine under CSC contested
  cases and is the single most-cited chapter outside the corpus. Top of [[citation-queue]].

---

## How this connects to the rest of Firefly's Path

| Wiki holds | Skill holds |
|---|---|
| The statute, the cite, the reasoning, the contradiction | The runbook, the portal quirks, the gotchas |
| [[hrs-11-102]], [[hrs-11-24]], [[hrs-12-31]], [[mail-ballot-registration-cutoff]] | `moho-vote-page` (the live /vote guide) |
| [[hrs-11-302]], [[hrs-11-357]], [[hrs-11-334]] | `csc-filer`, `csc-reconciliation`, `hawaii-campaign-finance` |
| [[hrs-11-391]] (disclaimers on electronic ads) | `twilio-mms-blast`, `moho-carousel` |
| Legislative process law *(pending)* | `projects/hi-leg-db/` (bill and roll-call data) |

Cross-link, do not duplicate.
