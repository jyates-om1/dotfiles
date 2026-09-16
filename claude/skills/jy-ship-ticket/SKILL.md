---
name: jy-ship-ticket
description: Take one Jira ticket from refinement to a review-ready PR by orchestrating subagents — grill (refine) → implement → code-review loop → fable validation → fix-up → verify → summarize. Use only when the user explicitly asks; it spawns many subagents and uses significant tokens.
disable-model-invocation: true
---

# Ship a ticket

An orchestration loop that takes ONE ticket from refinement to a review-ready PR. Subagents do the heavy lifting; you stay in the loop at the decision points and you verify everything they claim. Run only on explicit request.

Phase 0 is interactive (you and the user). Phases 2–5 are subagent-driven. You own Phase 1, Phase 3's judgment, and Phase 6.

## Phase 0 — Refine (interactive: `grilling`)
Invoke the `grilling` skill on the ticket. Ground every question in the codebase FIRST — dispatch Explore subagents to find facts; never ask the user something you can look up. Work the design tree in rounds (one round at a time, each question with your recommended answer). Surface data gaps you discover (a field the AC assumes but the lake doesn't have, etc.). Let the grill's length match the design surface — a prescriptive "ready-for-agent" ticket may need only 1–2 rounds. When the frontier is empty, write the refined spec + ACs and get the user's explicit confirmation before acting.

## Phase 1 — Ticket setup (Jira; you do this)
After the spec is confirmed:
- Update the description with the refined spec + ACs. `contentFormat: markdown`, PURE Markdown (no `h2.`/`{code}` wiki tokens — they render literally).
- Assign to the user (accountId), set the sprint (`customfield_10010` = the active sprint id; find it by reading an issue already in `sprint in openSprints()`), and transition to In Progress (walk `getTransitionsForJiraIssue` — the path may be one hop ("Start Work") or two (Refinement → Ready to Start → Start Work)).
- File follow-up tickets (`createJiraIssue`, parent = the epic) for anything the refinement deferred (data gaps, out-of-scope).

## Phase 2 — Implement (subagent)
Spawn a `general-purpose` implementation subagent. Give it the full refined spec + concrete file:line anchors from the exploration. It MUST:
- Branch off fresh `origin/main`.
- Run backend tests (`docker exec -u om1 <api-container> bash -lc 'cd /usr/src/backend && uv run pytest ...'`), frontend tests (jest in the frontend container), and the lint/format gate; fix what it breaks. (If the obt devcontainer isn't up — it needs interactive sudo an agent can't do — run ruff directly in the api container: `uv run ruff check <files> && uv run ruff format --check <files>`; the commit's pre-commit hooks are the real gate.)
- COMMIT FROM INSIDE THE DEVCONTAINER as `om1`, NEVER `--no-verify`. Subject `TICKET: ...`; end the body with `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`. Short "why" comments; NO Jira IDs in code comments/docstrings.
- **Finish the job in one turn.** Run the full suite SYNCHRONOUSLY (foreground) — do NOT background a long suite and then stop. If a suite must run in the background, COMMIT AND PUSH FIRST. Never end the turn with uncommitted/unpushed work while a background task is pending. (These agents habitually emit a premature "awaiting the background suite / I'll push after" and stop with the work uncommitted — forbid that explicitly.)
- Push and open a PR. Report branch, PR#, files (one-line each), test results.

## Phase 3 — Code-review loop (until a round is clean)
Per round, against the current PR head:
1. Verify the PR is real: `gh pr view` (head SHA, not draft, no prior review from you).
2. Spawn 5 parallel review lenses (`model: sonnet`): (a) CLAUDE.md compliance, (b) shallow bug scan of the diff, (c) git blame/history, (d) prior-PR review comments on these files, (e) code-comment/docstring guidance. Give each the diff (`gh pr diff N`) + focused context on the risky logic. For a follow-up ticket, point lens (d) at the PR whose review spawned it.
3. Collect all five. A finding raised by ≥2 lenses is high-confidence. Keep only real, in-scope findings at **confidence ≥ 50**; drop pre-existing / unmodified-line / linter-catchable issues. Apply your own judgment — never relay raw agent claims.
4. Post ONE consolidated review comment (permalinks at the full head SHA).
5. If findings: fix (focused subagent or inline), re-run affected + full suites, then re-review with a lighter round (correctness re-verify + adversarial "try to break the fix"). Repeat until a round is clean. If the design itself is in question, take it to Phase 4 rather than thrashing.

## Phase 4 — Fable validation (subagent, `model: fable`)
Spawn a validation subagent with `model: fable`. Give it the ACs + the PR + any open review items. Ask for: AC-by-AC PASS/FAIL with evidence (file:line or test), validated severity/confidence of findings, a DECISIVE recommendation on any design question (with options + reasoning + the exact change), and a prioritized must/should/nice fix list specific enough to implement. Fable is for the hard design calls and honest AC verification. Tell it a validation pass does NOT need to run the full suite (the ingest/targeted subset + your own first-party run suffice) — otherwise it will background a suite and stall like the others. If it stalls before delivering its verdict, `SendMessage` it: "deliver your verdict now, don't wait on the suite."

## Phase 5 — Fix-up (subagent)
Spawn a fix-up subagent to implement fable's prioritized list (same devcontainer/commit rules + the same finish-in-one-turn rule as Phase 2). Prefer fixes that PRESERVE already-settled user decisions; flag it if a fix would reverse one.

## Phase 6 — Verify + summarize (you do this)
- **Trust but verify every subagent, and assume the first "done" may be stale.** These agents routinely (a) stop before committing/pushing with a premature "awaiting the suite" message, then (b) finish on a later resume — so their first completion notification often understates reality, and a *later* duplicate notification for the same task may report the true final state. Never act on the words; check the ground truth: `git rev-parse HEAD` vs `origin/<branch>`, `git status` clean, and grep the claimed change in the *pushed* file (`git show origin/<branch>:<file> | grep ...`). If the work isn't committed/pushed, TAKE OVER: run the suite from the devcontainer, commit as `om1` (no `--no-verify`), push. Re-run the full suite yourself for a first-party number regardless.
- One agent touches the repo at a time. Stay hands-off the working tree while a subagent runs, or a concurrent-commit race ensues. Isolate parallel mutators in worktrees.
- Post a final review-resolution comment.
- Summarize the whole run: Jira state, PR#, each phase's outcome, first-party test numbers, and what's left (team review/merge, follow-up tickets).

## Hard-won conventions (do not relearn these)
- Devcontainer commits as `-u om1`, never `--no-verify`; the commit's pre-commit hooks are the lint/format gate. `docker exec` default root will root-own `.git` — always `-u om1`.
- Subagent claims (esp. "I ran the review", "tests pass", "pushed", "awaiting the suite") are unreliable — verify via the posted PR comment and the pushed head, or re-check yourself. See [[subagent-code-review-claims-unreliable]] and [[verify-pushed-commit-not-worktree]].
- `git status` before every push; a fix living only in the working tree passes YOUR local run but CI/the-merge uses the pushed commit.
- Code-review confidence threshold is **50** for this user.
- Frontend has flaky, suite-load-dependent tests (Radix-select timeouts) — re-run a lone failure in isolation before calling it a regression.
- Jira: descriptions/corrections go in the body (Markdown), not comments; sprint field is `customfield_10010`; keep an active-sprint id handy from a prior lookup.
