"""Hand-written operational readings, injected into the curated block of a
statute page.

This file is the source of truth for annotations written in bulk.  Everything
here is Claude's reading of statute text that was actually read, kept strictly
separate from the statute's own words on the page.  Run:

    python tools/annotations.py        # inject, then rerun build_pages.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hrs_lib import STATUTES, slug

BEGIN, END = "<!-- BEGIN CURATED -->", "<!-- END CURATED -->"

A = {}

A["11-24"] = """
## What it means operationally

**This section resolves the deadline-arithmetic question the wiki had open.** The
weekend-rollover rule for voter registration is here, in §11-24(a), not in
[[hrs-11-102|§11-102]] where everyone was looking:

> at 4:30 p.m. on the tenth day before each election, **but if the day is a Saturday, Sunday, or
> holiday then at 4:30 p.m. on the first working day immediately thereafter**, the general county
> register shall be closed

That single clause explains all four of the State's published 2026 dates, and explains why they
looked inconsistent:

| Deadline | Governing section | Ten/seven days out | Rollover clause? | State publishes |
|---|---|---|---|---|
| Primary, register closes | §11-24(a) | Wed Jul 29 | yes (not triggered) | **Jul 29** |
| Primary, address update | [[hrs-11-102\\|§11-102(b)]] | **Sat Aug 1** | **none** | **Aug 1** |
| General, register closes | §11-24(a) | **Sat Oct 24** | **yes, rolls forward** | **Oct 26** |
| General, address update | [[hrs-11-102\\|§11-102(b)]] | Tue Oct 27 | none (not triggered) | **Oct 27** |

So there is a weekend rollover, but it attaches to **closing the register**, not to the
address-update deadline. §11-102(b) contains no rollover language, which is why a Saturday
address-update deadline (Aug 1) stands as a Saturday. Two different rules in two different
sections, which is exactly how a plausible-sounding single explanation gets it wrong.

**The practical rule does not change: publish the State's date, never compute one.** What changes
is that we now know the mechanism, so a divergence in a future cycle is diagnosable instead of
mysterious. See [[deadlines]] and [[open-questions]].

- **§11-24(b) is a second, softer extension.** An application still counts if it arrived
  electronically through online registration ([[hrs-11-15.3|§11-15.3]]) on the tenth day, or came
  through a driver's licensing transaction or another NVRA designated agency, or is **postmarked**
  on or before the tenth day. Postmark counts for *registering*. Postmark never counts for
  *returning a ballot*.
- **Closing the register is not the end of registering.** §11-24(a) is expressly "subject to
  change only as provided in sections 11-15.2, 11-21(c), 11-22, 11-25, 11-26". The first of those,
  [[hrs-11-15.2|§11-15.2]], is same-day registration at a voter service center, which is the path
  that stays open through election day.
"""

A["12-31"] = """
## What it means operationally

**This section is not what the wiki's ingest queue assumed it was.** It had been carried as "the
wording constraint that governs vote-page copy." §12-31 is actually *Selection of party ballot;
voting*, and it carries a sharper hazard.

- **No voter can be made to declare a party.** "No person eligible to vote in any primary or
  special primary election shall be required to state a party preference or nonpartisanship as a
  condition of voting." Hawaiʻi's primary is open. Every voter is issued **every** party's ballot
  plus the nonpartisan ballot.
- **Voting more than one party's ballot voids it.** "A voter shall be entitled to vote only for
  candidates of one party or only for nonpartisan candidates. If the primary or special primary
  ballot is marked contrary to this paragraph, **the ballot shall not be counted**."

That second point is the live copy risk, and it is the opposite of the usual GOTV instinct to say
"fill it all out." In an all-mail primary a voter holds a packet containing several party ballots.
Marking across two parties does not spoil one race, it spoils **the ballot**. Any voter guide,
carousel, phonebank script, or text blast that covers the primary has to say: pick one party's
ballot, complete only that one.

- **Past primaries do not bind future ones.** A voter may take any party's ballot "regardless of
  which ballot the voter voted in any preceding primary." Useful when someone worries that voting
  in one party's primary registers them with that party. It does not.

Nothing in this section restricts *how a campaign describes* the ballot, so the "wording
constraint" the queue was chasing is either a different provision or came from a non-statutory
source. Recorded in [[open-questions]].
"""

A["11-15.2"] = """
## What it means operationally

**Confirms a cite the wiki had flagged as unverified.** Prior working notes attributed same-day
registration to §11-15.2 without having read it. The text says exactly that, so the citation is
good and can be used in voter-facing copy.

- **The path that stays open after the mail cutoffs.** Registration closes under
  [[hrs-11-24|§11-24]], but "notwithstanding" that closing, an unregistered person may register
  **in person at any voter service center on or before election day**, or electronically under
  [[hrs-11-15.3|§11-15.3]]. This is why "you missed the deadline" is never the right message: the
  ask simply changes from *watch your mailbox* to *go to a voter service center*.
- **Any voter service center, not an assigned one.** The statute says "any voter service center."
- **The voter signs a sworn affirmation** covering qualification to vote, that they have not voted
  and will not vote again in that election (including no absentee ballot under chapter 15), and an
  acknowledgement that false information is a **class C felony, up to $10,000 or five years**.
  Worth stating plainly to anyone we help register late, and a reason never to encourage someone
  unsure of their status to "just register again."
- **Same-day registrants can end up on a provisional ballot.** Under (c), if the clerk needs more
  time or information to validate the application, "the applicant shall be provided a provisional
  ballot." So same-day registration is not a guaranteed counted vote in the way a
  registered-and-mailed ballot is. Register early where possible; treat the voter service center
  as the backstop it is.
- Residence allegations may be taken as prima facie evidence unless contested by a qualified
  voter, per [[hrs-11-15|§11-15(b)]].
"""

A["11-92.1"] = """
## What it means operationally

The section that puts voter service centers and drop boxes on the ground. [[hrs-11-102|§11-102(d)]]
points here.

- **The county clerk decides where and when, and must proclaim it.** Locations, days open, and
  hours all come from a clerk's proclamation, which may be issued jointly with the
  [[hrs-11-91|§11-91]] election proclamation. There is no statewide statutory list, so the count
  and hours differ by county and by election. **Never state a voter service center's hours from
  memory or from a prior cycle. Pull the current proclamation.**
- **The clerk must find or build a site if no public building is available**, and equip it. A
  county pleading lack of venue is not a statutory excuse.
- **Precinct boundaries freeze early**: no change later than 4:30 p.m. on the tenth day before the
  close of filing.
- **Natural-disaster carve-out.** Under (c) and [[hrs-15-2.5|§15-2.5]], the clerk is not required
  to establish voter service centers for precincts affected by natural disasters. In a hurricane or
  lava year, the in-person backstop that [[hrs-11-15.2|§11-15.2]] relies on can legally disappear
  for an affected precinct.
"""

A["11-391"] = """
## What it means operationally

**A live compliance constraint on our own outbound work, not background reading.** Subsection (a)
reaches any advertisement "broadcast, televised, circulated, published, distributed, **or otherwise
communicated, including by electronic means**." A political text blast, an Instagram carousel, and
a boosted post are all inside that language.

Every advertisement must:

1. **Carry the name and address of whoever paid for it.** Address, not just name. On a character-
   limited SMS this has to be planned for, not bolted on.
2. **Carry an approval notice in a prominent location**, stating either that the candidate approved
   it or that the candidate did not. There is an express carve-out: an ad paid for by a **candidate,
   candidate committee, or ballot issue committee does not need the notice**. A noncandidate
   committee does.
3. **Not contain false information about the time, date, place, or means of voting.**

That third clause is the one to watch in GOTV copy, and it connects directly to the mail-ballot
cutoff problem: telling an unregistered voter after [[hrs-11-24|§11-24]]'s deadline to "watch your
mailbox for your ballot" is false information about the means of voting. The exposure is not
theoretical.

**Penalties are asymmetric.** Up to $25 per non-compliant advertisement and $5,000 aggregate,
**but for a noncandidate committee the fine is no less than $150 per advertisement.** A
noncandidate committee running a large blast with a defective disclaimer is exposed per message
at a statutory floor, with no cap named in this subsection below the aggregate.

Before any blast goes out, the disclaimer question is: which committee is paying, is it a
candidate or noncandidate committee, and does the creative carry name plus address plus (if
required) the approval notice. Relevant tooling: the `twilio-mms-blast` and `moho-carousel`
skills. This page holds the law; those hold the runbook.
"""

A["11-302"] = """
## What it means operationally

The vocabulary that the whole of Part XIII runs on. Reading any contribution, expenditure, or
reporting section without this one produces confident errors.

- **"Candidate" is broader than filing papers.** A person is a candidate if they file nomination
  papers **or** receive contributions, make expenditures, or incur financial obligations of more
  than **$100** toward nomination or election, **or** consent to someone else doing so on their
  behalf, **or** are certified as a candidate. Crossing $100 makes someone a candidate whether or
  not they have filed anything.
- **Candidacy ends only at termination of registration**, not on election day: "An individual
  remains a candidate until the individual's candidate committee terminates registration with the
  commission." Obligations persist after a loss.
- **"Advertisement" turns on a two-part test.** It must identify a candidate or ballot question
  *and* advocate or support nomination, opposition, election, passage, or defeat. Bumper stickers
  and similar sundry items are excluded by name. The definition feeds [[hrs-11-391|§11-391]]'s
  disclaimer duty.
- **"Campaign funds" is wider than contributions** and expressly includes interest, rebates,
  refunds, loans, and advances.
- **"Ballot issue committee"** is a species of noncandidate committee with the *exclusive* purpose
  of ballot-question activity. The exclusivity matters: mixed-purpose activity moves an
  organisation out of the definition.

**A note on scope.** This section defines terms "when used in **this part**," meaning Part XIII.
That is narrower than [[hrs-11-1|§11-1]], which defines terms for the entire title. When a
campaign finance term and a title-wide term collide, check which one is doing the work.

Referenced statutes worth knowing: [[hrs-11-61|§11-61]] ("political party" defined),
[[hrs-11-324|§11-324]] (treasurer), [[hrs-11-372|§11-372]] (loan reporting), and §572C-3
(reciprocal beneficiaries) which is outside the corpus and sits in [[citation-queue]].
"""

A["11-357"] = """
## What it means operationally

The contribution limits, per contributor, **per election period**.

| Office sought | Limit |
|---|---|
| Two-year office | **$2,000** |
| Four-year nonstatewide office | **$4,000** |
| Four-year statewide office | **$6,000** |

- **The tier follows the office's *usual* term, not the term actually being served.** Subsection
  (b) is explicit: length of term is "the usual length of term of the office as unaffected by
  reapportionment, a special election to fill a vacancy, or any other factor." A special election
  to fill the remainder of a four-year seat is still a four-year-office limit.
- **The limit is an aggregate across the election period**, not per transaction, and it applies to
  contributions to the candidate *or* the candidate committee, so the two cannot be used to double
  up.
- **"Person" is doing heavy lifting here** and is defined in [[hrs-11-302|§11-302]]. Whether two
  related entities are one person or two is the usual place this goes wrong.
- This section has never been amended: `[L 2010, c 211, pt of §2]`. The dollar figures are the
  2010 figures and are **not** indexed to inflation on the face of the statute.

**What this page does not tell you:** what an "election period" is, and how contributions are
allocated between a primary and a general. That is defined elsewhere in Part XIII and has not been
annotated yet. Do not compute a limit from this page alone.

Downstream: [[hrs-11-359|§11-359]], [[hrs-11-364|§11-364]] and [[hrs-11-381|§11-381]] all cite this
section.
"""

A["11-1"] = """
## What it means operationally

**The definitions here govern the entire title, not just chapter 11.** The opening words are
"Whenever used in **this title**," so chapters 12 through 19 inherit them unless a chapter supplies
its own. Any reading of a term in the primary-election, absentee, voting-systems, or election-
offenses chapters starts here.

This makes §11-1 the most structurally load-bearing section in the corpus even though the citation
graph understates it: most sections rely on these definitions without citing them, so the inbound
edge count is far lower than the real dependency.

Contrast [[hrs-11-302|§11-302]], which defines the campaign finance vocabulary only "when used in
**this part**" (Part XIII). Where both could apply, the Part XIII definition is the specific one.
"""

A["11-15.3"] = """
## What it means operationally

The statutory basis for online voter registration, and the reason a common piece of GOTV copy is
wrong.

- **It is permissive, not mandatory**: the clerk of each county **may** permit electronic
  registration. It also requires "valid government-issued identification that is capable of
  electronic confirmation," so a voter without qualifying ID cannot use this path.
- **Registering online is still registering, and the deadline still applies.** Under
  [[hrs-11-24|§11-24(b)]] an online application counts if received on or before the tenth day. The
  State's own dates widget pairs a "Paper Registration Deadline" with "voters may register online
  at any time," and read together those mislead badly: after the register closes, **registering
  online does not get a ballot mailed.** The late path is a voter service center under
  [[hrs-11-15.2|§11-15.2]]. See [[mail-ballot-registration-cutoff]].
- **Using the online form consents to a database signature lookup**, and that retrieved signature
  may be used to validate the voter's identity "in any election-related matter in which a signature
  is necessary" — including, in practice, return-envelope signature matching.
"""


A["11-334"] = """
## What it means operationally

The candidate committee filing calendar. This is the section the `csc-filer` and
`csc-reconciliation` skills operate against; the law lives here, the runbook lives there.

**Preliminary reports, §11-334(a)(1):**

| Trigger | Due |
|---|---|
| (A) | February 28 of a general election year |
| (B) | April 30 of a general election year |
| (C) | 30 calendar days before a primary / initial special / initial nonpartisan election |
| (D) | 10 calendar days before that same election |
| (E) | October 1 of a general election year |
| (F) | 10 calendar days before a general / subsequent special / subsequent nonpartisan election |

**(E) and (F) are excused** for a candidate who lost the primary, or who was *elected outright* in
the primary. Winning in the primary ends the preliminary sequence, it does not extend it.

**The "current through" dates are not the filing dates**, and this is where reconciliation goes
wrong:

- the (C) report is current through **June 30**;
- every other preliminary report is current through the **fifth calendar day before its own filing
  deadline**, not through the filing date.

**Final reports, (a)(2) and (a)(3):**

- Final primary report: **20 calendar days after** the primary, current through election day.
- Final election period report: **30 calendar days after** the general, current through election
  day. This one is filed by the primary losers and primary-elected winners who were excused from
  (E) and (F).
- **Early swearing-in accelerates it**: a candidate sworn into office sooner than 30 days after
  the election files the final election period report **three business days before** being sworn in.

**Supplemental reports, (a)(4):** January 31 annually, and July 31 after an election year. These
are the ones that keep applying to a committee that has stopped campaigning but has not terminated
registration, which under [[hrs-11-302|§11-302]] means the person is still a candidate.

Deadlines here are **calendar days** on the face of the statute. Do not assume the
[[hrs-11-24|§11-24]] weekend rollover carries over; that clause is written for closing the register
and is not repeated here.
"""

A["19-3"] = """
## What it means operationally

The election fraud offences. Broad, and several clauses reach ordinary campaign conduct if handled
carelessly.

- **Anything of value offered to induce a vote is bribery**, including "office or place of
  employment," offered "directly or indirectly, personally or through another." Paying, offering,
  or *agreeing to* offer all count, and so does acting "on account of any person having voted."
  This is the clause that makes prize draws, gift cards, and "thank you for voting" incentives a
  live legal question rather than a marketing one. Treat any voter-facing giveaway tied to voting
  as lawyer territory before it ships.
- **Receiving is an offence too**, under (a)(3), so the voter is exposed as well as the campaign.
- **Intimidation is defined broadly** and expressly includes conduct that "impedes, prevents, or
  otherwise interferes with the free exercise of the elective franchise."
- **A concrete bright line worth knowing:** the statute says the practice of intimidation
  "includes, among other actions, the **unconcealed carry of any dangerous instrument, including a
  firearm, at or within two hundred feet of any voter service center, place of deposit, or polling
  place**." Subsection (b) defines "concealed," "unconcealed," and borrows "dangerous instrument"
  from §707-700 (penal code, outside the corpus, see [[citation-queue]]). Useful for poll-watching
  and voter-protection briefings.
- **Impersonation and double voting** under (a)(5) expressly reach voting more than once "regardless
  of whether one of the elections is in a state or territory of the United States outside of
  Hawaii," which is the interstate double-voting case.

Penalties are in [[hrs-19-4|§19-4]], not here.
"""

A["11-1.52"] = """
## What it means operationally

**New law, and current.** Act 190 (2024) directed the Office of Elections to apply for membership
in the Electronic Registration Information Center (ERIC) **no later than June 30, 2025**, to keep
that membership, and to budget for the dues annually beginning FY 2025-26.

Why it matters to us: ERIC is the multi-state data consortium used to cross-check registration
rolls, flag voters who have moved or died, and identify eligible-but-unregistered people. The
statute requires the Office of Elections to **share the information and services with each county**
and requires both the State and each county elections office to **use** it to verify their rolls.

Practical consequences to watch:

- Roll accuracy should be improving over the 2026 cycle, which affects how much stale-address
  attrition to expect in a mail-heavy universe. That bears directly on the
  [[hrs-11-102|§11-102]] rule that a ballot is never mailed to a flagged bad address.
- **Whether Hawaiʻi actually joined, and when, is not established by this page.** The statute sets
  the obligation; it does not report compliance. ERIC membership has been politically volatile in
  other states. Confirm current membership status with the Office of Elections before relying on
  it. Logged in [[open-questions]].

`[L 2024, c 190, §2]` — never amended, and the section number is revisor-supplied (bracketed).
"""


def main():
    done, missing = 0, []
    for sid, text in A.items():
        path = os.path.join(STATUTES, slug(sid) + ".md")
        if not os.path.exists(path):
            missing.append(sid)
            continue
        src = open(path, encoding="utf-8").read()
        i, j = src.find(BEGIN), src.find(END)
        if i == -1 or j == -1:
            missing.append(sid + " (no markers)")
            continue
        new = src[:i + len(BEGIN)] + "\n" + text.strip() + "\n" + src[j:]
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new)
        done += 1
    print(f"annotations injected: {done}")
    if missing:
        print("  !! missing:", ", ".join(missing))


if __name__ == "__main__":
    main()
