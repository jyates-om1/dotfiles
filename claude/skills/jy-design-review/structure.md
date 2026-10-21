# Doc structure

Two tabs. **Overview** answers the ask on its own: a reviewer can decide everything from it. **Reference** holds the evidence and detail that Overview links to.

## Overview tab

1. **Title + byline.** Byline is exactly the as-of date chip and the author mention.
2. **Lead** (2–4 sentences): what we're building and for whom, size and who builds it, and **who we need what from**, by name. End with how to respond: "Pick Agree / Change / Discuss in each Decision column; comment on the row for Change or Discuss."
3. **Goals.** A numbered list of outcomes, then one bold line: **Not goals:** …
4. **Shape.** The shape diagram (seeded first, see diagrams.md), then 2–4 sentences that walk the picture. No new facts that aren't in the picture.
5. **Decisions.** Table `ID | Decision | Status`. Decision cell = **bold lead-in.** plus 1–2 sentences. Status = a Status dropdown preset to Decided, Proposed or Open. One line above the table: "Decided items set direction. Proposed and Open items are still open for change." Each Proposed or Open row also appears in a stakeholder table below.
6. **Alternative considered: <name>** (0–2 of these, only for big forks). The alternative's diagram with numbered markers, a numbered list of consequences matching the markers, then one sentence on why we chose otherwise.
7. **What we need from you.** One `###` subsection per stakeholder: "For <Name> (<role>)".
   - First line: **Changes in your area:** a short list of what this design changes that they own.
   - Then the table `ID | Question | Lean | Ref | Decision`:
     - Question: one sentence, answerable by that person.
     - Lean: **bold lean.** + why in 1–3 sentences + **If not:** what happens if they pick the other way, including cost.
     - Ref: specific links into Reference (`§R3 Middleware · §R5 Tickets`), never a bare section number.
     - Decision: Decision dropdown, unset.
   - A "Together" subsection for questions two people must agree on.
8. **No decision needed.** Table `ID | Item | How it gets answered | Ref`: things settled by testing, onboarding or whoever builds the next piece.
9. **Out of scope.** Bullets.

## Reference tab

1. **Changes since last review.** Dated bullets, newest first. Omit on the first version.
2. **Glossary.** Table `Term | Meaning here`, 10–25 terms a non-specialist reviewer would trip on.
3. **R1…Rn, one section per component.** Headings `R<n> <component>`. Current state [V] with `file:line @ <short sha>`; design; gotchas; alternatives rejected. Tag claims [V] verified, [I] inferred, [U] unknown.
4. **Acceptance checks.** A `- [ ]` checklist of testable statements ("A launch from an unregistered `iss` gets `frame-ancestors 'self'`"). These become ticket acceptance criteria.
5. **Tickets and size.** Table `Ticket | Repo | Contents | Pts`, a total row, then one line converting points to engineer-sprints at the measured velocity and naming the calendar window.
6. **References.** Links, code refs pinned to commits.

## IDs and status

- If the items already have IDs from earlier review rounds or Slack threads, keep them; continuity beats the scheme.
- Otherwise use one ID scheme for the whole doc, never renumbered: **D#** decisions, **Q#** open questions, **N#** no-decision items. A superseded item keeps its ID, moves to No decision needed, and says "Superseded by D#".
- Two separate status axes: the author's **Status** (Decided / Proposed / Open) and the reviewer's **Decision** (Agree / Change / Discuss). Never merge them.

## Writing rules

- Each fact once. Overview states it; Reference proves it; links connect them.
- Name people. "Eric reviews the Actions", not "platform team review".
- Numbers over adjectives: points, bytes, minutes.
- A lean is a recommendation, not a survey. One option in bold, the other in "If not".
- Keep table cells to what fits a glance; push detail to Reference and link it.
