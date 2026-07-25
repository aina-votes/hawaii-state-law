---
type: source
title: "2026 Election Dates & Deadline widget — Office of Elections"
status: verified
last_verified: 2026-07-24
tags: [primary-source, agency-publication, deadlines]
---

# Source — Office of Elections, "2026 Election Dates & Deadline"

## Provenance

| | |
|---|---|
| Publisher | State of Hawaii, Office of Elections |
| URL | https://elections.hawaii.gov/voting/ (site-wide sidebar widget) |
| Retrieved | 2026-07-24 |
| Tier | **Primary for published dates** (the agency's own calendar is the operative date), **secondary for legal rules** (it describes the statute, it is not the statute) |
| Raw file | `raw/2026-07-24-oe-2026-election-dates.md` |
| Retrieval method | `curl` with a browser User-Agent |

**Gotcha:** `elections.hawaii.gov/election-information/` returns **404**. The dates widget lives in
the sidebar of ordinary pages such as `/voting/`.

## Extracted claims

| Claim | Note |
|---|---|
| Election day — Primary Aug 8, 2026; General Nov 3, 2026. Ballots must be **received** by the County Elections Division by 7:00 p.m. | Receipt, not postmark |
| Paper Registration Deadline — Primary Jul 29, 2026; General Oct 26, 2026 | Submitted **to the County Elections Division** |
| "Voters may register online at any time or in-person at a voter service center." | Literally true, **misleading in context** — see below |
| Absentee Ballot Request (alternate address) — Primary Aug 1, 2026; General Oct 27, 2026 | Aligns exactly with the §11-102(b) 7-day address-update rule |
| Ballots Arrive in Mail — Primary Jul 21, 2026; General Oct 16, 2026 | Exactly 18 days out, matching the §11-102(b) receipt target |
| Voter Service Centers — open 10 business days prior; Primary Jul 27–Aug 8, General Oct 20–Nov 3; offer accessible voting, in-person voting, **same-day registration**; established and operated by the County Elections Divisions | |

## Notable — the juxtaposition problem

The widget pairs "Paper Registration Deadline" with "Voters may register online at any time."
A reader infers that registering online after the deadline still yields a mailed ballot. It does
not — [[hrs-11-102|§11-102(b)]] governs when the *clerk stops mailing*, not which form was used.
Written up on [[mail-ballot-registration-cutoff]].

## Notable — one date does not match the statutory offset

General-election registration deadline is published as **Mon Oct 26**, but Nov 3 − 10 days is
**Sat Oct 24**. Every other published date matches its statutory offset exactly, including a
Saturday one (Aug 1). Reconciliation table on [[deadlines]]; unresolved in [[open-questions]].

## Pages touched

Created: [[deadlines]]. Updated: [[mail-ballot-registration-cutoff]], [[ballot-package]],
[[county-clerks]].

## Open questions raised

- What produces Oct 26 rather than Oct 24?
- Is the same-day-registration authority §11-15.2 (per prior working notes) — needs a primary pull.
- Per-county VSC locations and hours are not in this widget.
