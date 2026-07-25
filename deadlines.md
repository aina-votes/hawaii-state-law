---
type: synthesis
title: Deadlines — 2026 cycle
aliases: ["dates", "calendar", "election dates"]
status: verified
last_verified: 2026-07-24
tags: [elections, deadlines, gotv]
sources: ["[[src-2026-07-24-oe-election-dates-2026]]", "[[src-2026-07-24-hrs-11-102]]", "[[src-2026-07-24-hrs-election-law-corpus]]"]
---

# Deadlines — 2026 cycle

**Rule: use the State's published dates. Never compute them from the statute.** The published
general-election registration deadline does not equal election day minus ten days, because
[[hrs-11-24|§11-24(a)]] rolls a weekend or holiday closing forward to the next working day.
Computing the raw offset produces a date *earlier* than the real one, which would make us tell
voters they had missed a deadline they had not. See the reconciliation below.

Source of truth: Office of Elections, retrieved 2026-07-24 — [[src-2026-07-24-oe-election-dates-2026]].

## Published dates

| What | Primary | General |
|---|---|---|
| **Election day** (ballots must be *received* by county elections division, 7:00 p.m.) | **Sat Aug 8, 2026** | **Tue Nov 3, 2026** |
| Ballots arrive in mail by | Tue Jul 21, 2026 | Fri Oct 16, 2026 |
| **Paper registration deadline** (last day to register and still be mailed a ballot) | **Wed Jul 29, 2026** | **Mon Oct 26, 2026** |
| Absentee / alternate-address request (address update) | Sat Aug 1, 2026 | Tue Oct 27, 2026 |
| Voter service centers open (same-day registration + in-person voting) | Jul 27 – Aug 8, 2026 | Oct 20 – Nov 3, 2026 |

Postmarks never count. Received by 7:00 p.m. on election day, or it does not count.

## Where we are today

**Today is 2026-07-24.** The primary registration cutoff is **Wed Jul 29 — 5 days out.**

From **Thu Jul 30** onward, no one newly registering gets a ballot mailed for the primary. Any GOTV
copy running on or after Jul 30 must stop telling unregistered voters to watch their mailbox and
must point them at a **Voter Service Center** (open Jul 27 – Aug 8). See
[[mail-ballot-registration-cutoff]].

## Reconciliation against the statute

[[hrs-11-102|HRS §11-102(b)]] sets the rules as *ten days before* (registration) and *seven days
before* (address update); the 18-day figure is the receipt target. Computing those offsets against
the published dates:

| Offset | Computed | Published | Match? |
|---|---|---|---|
| Primary − 18 | Tue Jul 21 | Jul 21 | ✅ |
| Primary − 10 | Wed Jul 29 | Jul 29 | ✅ |
| Primary − 7 | **Sat** Aug 1 | Aug 1 | ✅ (published on a Saturday) |
| General − 18 | Fri Oct 16 | Oct 16 | ✅ |
| General − 10 | **Sat Oct 24** | **Mon Oct 26** | ❌ **2 days later than computed** |
| General − 7 | Tue Oct 27 | Oct 27 | ✅ |

### ✅ Resolved 2026-07-24 — the divergence is [[hrs-11-24|HRS §11-24(a)]]

The rollover rule exists. It is just not in §11-102, which is why two earlier passes missed it.
[[hrs-11-24|§11-24(a)]] governs **closing the general county register**:

> at 4:30 p.m. on the tenth day before each election, **but if the day is a Saturday, Sunday, or
> holiday then at 4:30 p.m. on the first working day immediately thereafter**, the general county
> register shall be closed to registration

[[hrs-11-102|§11-102(b)]]'s seven-day address-update deadline contains **no** equivalent clause.
Two rules, two sections, two behaviours — which is exactly why a single tidy explanation kept
failing:

| Deadline | Governing section | Computed | Rollover clause? | Published |
|---|---|---|---|---|
| Primary, register closes | §11-24(a) | Wed Jul 29 | yes, not triggered | Jul 29 ✅ |
| Primary, address update | §11-102(b) | **Sat Aug 1** | **none** | Aug 1 ✅ |
| General, register closes | §11-24(a) | **Sat Oct 24** | **yes, rolls forward** | **Mon Oct 26** ✅ |
| General, address update | §11-102(b) | Tue Oct 27 | none, not triggered | Oct 27 ✅ |

Every published 2026 date is now accounted for.

**The practical rule does not change: publish the State's date, never compute one.** §11-24(b) adds
further softening (electronic, NVRA-agency, and postmarked applications), and holidays vary, so
the offset is still not a safe thing to compute by hand. What changed is that a future divergence
is now diagnosable rather than mysterious.

## Maintenance

- Re-verify against elections.hawaii.gov at the start of each cycle and after any election-law
  session takes effect.
- When this cycle closes, mark this page `superseded` and start a new one. Do not overwrite —
  prior-cycle dates are useful for comparison.

## Related

- [[hrs-11-102]] · [[hrs-11-24]] · [[hrs-11-15.2]] · [[hrs-11-15.3]] · [[hrs-11-92.1]] ·
  [[mail-ballot-registration-cutoff]] · [[ballot-package]] · [[county-clerks]]
