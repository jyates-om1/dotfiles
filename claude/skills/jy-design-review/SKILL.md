---
name: jy-design-review
description: Turn a design conversation into a review-ready Claude Doc that asks named stakeholders for decisions, with diagrams seeded first, per-stakeholder question tables (lean, "If not", Ref links, Decision dropdown) and a Reference tab. Use when the user wants a design draft, design doc or review doc built from the current session's design work, or asks to package a design for stakeholder feedback.
---

# Design review doc

Build one Claude Doc from the design work in this session. The doc exists to get **decisions** back from named people quickly. Every section serves that: a reader sees the shape, sees what's decided, finds the questions addressed to them, and answers in place.

Files in this skill (read each when its step says to):
- [structure.md](structure.md): the doc's sections, tables, ID and status rules, writing rules.
- [birth.md](birth.md): the one-call doc skeleton (two tabs, both enums).
- [diagrams.md](diagrams.md): the diagram kit and the patterns that pass the validator.
- [docs-quirks.md](docs-quirks.md): Claude Docs API behaviour that costs retries if you don't know it.
- [slack.md](slack.md): the per-stakeholder message format.
- [diagram_kit.py](diagram_kit.py): Python helpers that emit validator-safe diagram modules (bands, markers).

## Steps

### 1. Inventory
Read the session's working files (decision logs, research notes, prior docs) and the conversation. Write `design-inventory.md` in the topic's working dir under `/mnt/devdata/ai-dev/` with:
- goals (numbered) and not-goals;
- the **shape**: components, who owns each, the main flow between them;
- decisions, each with an ID, a status (Decided / Proposed / Open), the person who decides, a lean, and an "If not";
- forks big enough for an "Alternative considered" section (usually 0–2): the rejected option and its numbered consequences;
- stakeholders: name, role, what changes in their area, which IDs they own;
- items that need no decision (answered by testing, onboarding or later work);
- evidence: file:line refs pinned to a commit, links, [V]/[I]/[U] tags;
- size: tickets, points, and a calendar line from measured velocity if the session has it.

Done when every decision has status, owner, lean and "If not", and every stakeholder has at least one ID. If a decision lacks an owner or lean, ask the user before building.

### 2. Birth
Read [birth.md](birth.md) and [docs-quirks.md](docs-quirks.md). Send the birth batch: both tabs, every section as a pending block, both enums. Open the doc for the user with the Artifact tool. Then load the `anthropic-skills:docs` skill (the Docs connector requires a docs skill before further calls).

Done when the ack returns the doc link, both tab ids, both body ids and both enum ids, and you've recorded them in the inventory file.

### 3. Seed the diagrams first
Read [diagrams.md](diagrams.md). Generate each module with [diagram_kit.py](diagram_kit.py), which writes the literal ids and words the validator needs. Fill the Shape section with the shape diagram before any prose, then each "Alternative considered" diagram. Screenshot every diagram and fix overlaps, clipped text and arrows through labels before moving on.

Done when each diagram is published, screenshotted once after its last change, and has a one-line caption saying what it shows.

### 4. Fill the Overview tab
Read [structure.md](structure.md). Replace each pending block in reading order: lead, Goals, Decisions, the Shape prose under the diagram, alternatives, one "What we need from you" subsection per stakeholder, No decision needed, Out of scope.

Write each table with its dropdown chips inline and plain Ref labels. Add the Ref links with format ops after step 5, once the Reference headings exist ([docs-quirks.md](docs-quirks.md)).

Done when no pending block remains in the tab, every question row has a Lean ending in **If not:**, a Ref that links to a block, and a Decision dropdown.

### 5. Fill the Reference tab
Changes since last review, Glossary, one section per component (evidence-tagged), Acceptance checks, Tickets and size, References.

Then add the Ref links from step 4 with format ops, using the Reference heading ids from the fill's ack.

Done when every Ref label carries a link to a Reference heading, and every acceptance check is a testable statement.

### 6. Verify
- Read both tabs' outlines. Check that IDs are unique, that superseded IDs say "Superseded by", and that no pending block remains.
- Ask the user to click one Ref link and confirm it opens the Reference section (cross-tab links are unverified).
- Re-screenshot any diagram whose labels changed.

Done when all three checks pass.

### 7. Stakeholder messages
Read [slack.md](slack.md). Write one draft per stakeholder to `slack-drafts.md` beside the inventory. Never send; the user sends.

Done when each stakeholder with at least one ID has a draft whose first lines are their asks.

## Rules
- **Never edit an existing review doc** unless the user names it. A new run makes a new doc.
- Follow `no-ai-slop` for all prose: short sentences, no filler, numbers over adjectives.
- Prefer a picture over a paragraph whenever the content has a shape (flow, layers, ownership, a fork).
- One source of truth per fact: the Overview states a decision once; detail lives in Reference and is linked, not repeated.
