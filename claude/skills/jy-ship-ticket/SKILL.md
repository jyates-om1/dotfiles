---
name: jy-ship-ticket
description: Take one Jira ticket from refinement to a review-ready PR by orchestrating subagents — grill (refine) → implement → code-review loop → fable validation → fix-up → local UI check → verify → summarize (plus an on-request deployed check after merge). Use only when the user explicitly asks; it spawns many subagents and uses significant tokens.
disable-model-invocation: true
---

# Ship a ticket

An orchestration loop that takes ONE ticket from refinement to a review-ready PR. Subagents do the heavy lifting; you stay in the loop at the decision points and you verify everything they claim. Run only on explicit request.

Phase 0 is interactive (you and the user). Phases 2–5.5 are subagent-driven. You own Phase 1, Phase 3's judgment, and Phase 6. Phase 7 runs only on request.

## Phase 0 — Refine (interactive: `grilling`)
Invoke the `grilling` skill on the ticket. Ground every question in the codebase FIRST — dispatch Explore subagents to find facts; never ask the user something you can look up. Work the design tree in rounds (one round at a time, each question with your recommended answer). Surface data gaps you discover (a field the AC assumes but the lake doesn't have, etc.). Let the grill's length match the design surface — a prescriptive "ready-for-agent" ticket may need only 1–2 rounds. When the frontier is empty, write the refined spec + ACs and get the user's explicit confirmation before acting.
- **Read only current code.** Before any code read, `git fetch` and `git merge-base --is-ancestor origin/main HEAD` in every repo you touch. On a stale checkout, read via `git grep origin/main` or a fresh worktree. A stale read once produced a wrong design decision.
- **Map ownership before scoping.** Find who owns every table, grant, procedure, view and consumer the ticket touches. For example, `PHENOM_CATALOG` tables, promote procedures and reader grants live in the orchestration repo's Terraform, not platform-lite, and phenom-health reads a view. A second repo means two PRs and a deploy order (infra applied before the code that writes to it). Re-point the ticket if needed.
- **When code contradicts a recorded design decision**, stop and raise it with evidence. Don't quietly pick a different approach. Once the user decides, correct the decision record and PRD. Deferred or split-out work becomes a new ticket under the epic, with `Blocks` links and story points (`customfield_10025`).
- **Check API norms for any new endpoint:** resource naming (the PhenOM API uses singular prefixes), `XxxRequest` models with `extra="forbid"`, pagination, and deployed limits. The stage WAF blocks query strings over 2,048 bytes, so ID lists go in a POST body.

## Phase 1 — Ticket setup (Jira; you do this)
After the spec is confirmed:
- Update the description with the refined spec + ACs. `contentFormat: markdown`, PURE Markdown (no `h2.`/`{code}` wiki tokens — they render literally).
- Assign to the user (accountId), set the sprint (`customfield_10010` = the active sprint id; find it by reading an issue already in `sprint in openSprints()`), and transition to In Progress (walk `getTransitionsForJiraIssue` — the path may be one hop ("Start Work") or two (Refinement → Ready to Start → Start Work)).
- File follow-up tickets (`createJiraIssue`, parent = the epic) for anything the refinement deferred (data gaps, out-of-scope).

## Phase 2 — Implement (subagent)
First set up a worktree per repo (see **Worktrees** below). Spawn a `general-purpose` implementation subagent, one per repo; different repos can run in parallel. Give it the full refined spec plus concrete file:line anchors from the exploration. It MUST:
- Branch off fresh `origin/main`. To build on an unmerged parent PR, branch off the parent's branch and open the PR with `--base <parent-branch>`. GitHub retargets it to `main` when the parent merges.
- Run backend tests (`docker exec -u om1 <api-container> bash -lc 'cd /usr/src/backend && uv run pytest ...'`), frontend tests (jest in the frontend container), and the lint/format gate; fix what it breaks. (If the obt devcontainer isn't up and `sudo -n true` fails, so an agent can't start it, run ruff directly in the api container: `uv run ruff check <files> && uv run ruff format --check <files>`; the commit's pre-commit hooks are the real gate.)
- COMMIT FROM INSIDE THE DEVCONTAINER as `om1`, NEVER `--no-verify`. Subject `TICKET: ...`. End the body with the `Co-Authored-By` line for the model actually running, as the system reminder gives it. Keep code comments short and about the why; no Jira IDs in code comments or docstrings. After each commit, check that `git rev-parse --abbrev-ref HEAD` is the branch; commits can land on a detached HEAD.
- **Alembic migrations get a RANDOM revision id** (`uuid4().hex[:12]`), never "the next one" in a pattern: two PRs once collided on `e9f0a1b2c3d4`. Chain from the current single head, and verify on a scratch Postgres database, never the shared dev one (upgrade, downgrade -1, upgrade). CI builds test databases with `create_all` and never runs Alembic; `test_alembic_history.py` is the guard.
- A new response or preview field on a payload that's cached (for example `catalog_diff.result` JSONB) defaults to a value, so rows cached before the deploy still deserialize. If the repo records per-table counts in an audit table (`catalog_operation_log`), a new table gets its column plus a migration, as the existing ones did.
- **Finish the job in one turn.** Run the full suite SYNCHRONOUSLY (foreground) — do NOT background a long suite and then stop. If a suite must run in the background, COMMIT AND PUSH FIRST. Never end the turn with uncommitted/unpushed work while a background task is pending. (These agents habitually emit a premature "awaiting the background suite / I'll push after" and stop with the work uncommitted — forbid that explicitly.)
- Push and open a PR. For a cross-repo ticket, both PR descriptions state the deploy order at the top. Report branch, PR#, files (one line each), and test results.

## Phase 3 — Code-review loop (until a round is clean)
Per round, against the current PR head:
1. Verify the PR is real: `gh pr view` (head SHA, not draft, no prior review from you).
2. Spawn 5 parallel review lenses (`model: sonnet`): (a) CLAUDE.md compliance, (b) shallow bug scan of the diff, (c) git blame/history, (d) prior-PR review comments on these files, (e) code-comment/docstring guidance. Give each the diff (`gh pr diff N`) + focused context on the risky logic. For a follow-up ticket, point lens (d) at the PR whose review spawned it. For a cross-repo ticket, give each lens both PRs in one round.
3. Collect all five. A finding raised by ≥2 lenses is high-confidence. Keep only real, in-scope findings at **confidence ≥ 50**; drop pre-existing / unmodified-line / linter-catchable issues. Apply your own judgment — never relay raw agent claims.
4. Post ONE consolidated review comment (permalinks at the full head SHA).
5. If findings: fix (focused subagent or inline), re-run affected + full suites, then re-review with a lighter round (correctness re-verify + adversarial "try to break the fix"). For a new test that proves a fix, confirm it FAILS without the fix. Repeat until a round is clean. If the design itself is in question, take it to Phase 4 rather than thrashing.

## Phase 4 — Fable validation (subagent, `model: fable`)
Spawn a validation subagent with `model: fable`. Give it the ACs + the PR + any open review items. Ask for: AC-by-AC PASS/FAIL with evidence (file:line or test), validated severity/confidence of findings, a DECISIVE recommendation on any design question (with options + reasoning + the exact change), and a prioritized must/should/nice fix list specific enough to implement. Fable is for the hard design calls and honest AC verification. Tell it a validation pass does NOT need to run the full suite (the ingest/targeted subset + your own first-party run suffice) — otherwise it will background a suite and stall like the others. If it stalls before delivering its verdict, `SendMessage` it: "deliver your verdict now, don't wait on the suite." Also ask whether the contract fits the tickets that build on this one, and write what it finds into those tickets' descriptions.

## Phase 5 — Fix-up (subagent)
Spawn a fix-up subagent to implement fable's prioritized list (same devcontainer/commit rules + the same finish-in-one-turn rule as Phase 2). Prefer fixes that PRESERVE already-settled user decisions; flag it if a fix would reverse one.

## Phase 5.5 — UI check (only if the ticket has UI ACs)
Run in the ticket's worktree stack (`task app:preview`; the domain is in the worktree's `.env`), never the main checkout. Admin uses the preview test-token; basic uses a route stub on the app's effective-scopes endpoint. Seed through the API on the worktree DB only. For each scenario, declare the expected result *before* looking, then fill `| AC | expected | observed | pass/fail |` with one line of evidence plus a screenshot. No prose verdicts. Note the blind spots (mock auth, wildcard tenant, no WAF/Auth0). A FAIL goes back to Phase 5 as a must-fix. Never run against deployed environments; deployed-only checks stay in the human QA checkpoint.

**Script first, MCP to explore.** Playwright MCP is token-hungry: most actions return the page's accessibility-tree snapshot (often thousands of tokens), and the agent re-reads the page after nearly every click. POM-569's 10-scenario MCP check cost about 127k subagent tokens over 70 tool calls; POM-568's script-first check ran 12 scenarios in about 102k tokens over 26 calls. Reading the component source for selectors can replace most MCP exploration. So the subagent:
1. **Explores briefly with MCP.** It opens each screen the ACs touch, once, to learn selectors, roles and dialog structure. It doesn't run scenarios this way.
2. **Writes one script** to `<evidence-dir>/ui-check.mjs`, in plain `playwright-core`, with no test runner. The script:
   - seeds through the API, using the same auth the browser uses;
   - runs every scenario, with the expected text in the script, so the expectations are fixed before anything is observed;
   - saves a screenshot per key state with `page.screenshot({path})`;
   - asserts with exact text or role queries;
   - writes `results.json` and the markdown results table;
   - cleans up the seed data in a `finally`, then checks the row counts against the baseline.
3. **Runs it with one Bash call** and reads only the table and the failing scenarios. It opens a screenshot only when a scenario fails or the table needs visual evidence. Every screenshot goes on the evidence page anyway.
4. **On a failure, switches to MCP** to investigate the live page. It then fixes the script, or reports the bug, and re-runs. A re-check after a code fix is one re-run of the script.
5. **Launches the browser with `chromium.launch({executablePath})`,** pointing at the cached headless shell (`~/.cache/ms-playwright/chromium_headless_shell-*/chrome-linux/headless_shell`). That way the script doesn't depend on which `playwright-core` version it loads. It imports `playwright-core` from a scratch install (`npm i --prefix <evidence-dir>/runner playwright-core`), never the app's `package.json`.
6. **Layout checks:** measure with `getBoundingClientRect` in the script, comparing the dialog's right edge with the furthest descendant's, at desktop width (1280×720) and phone width (400×800). Don't eyeball screenshots for this.

The script stays in the evidence folder, so later checks on the ticket re-run it instead of re-driving the browser.

Setup that has bitten us:
- **Switch the worktree to its own stack first.** Set its `.git` to the ABSOLUTE gitdir (obt mounts the main `.git` at its host path). Delete the shared-container shims: the `frontend/node_modules` symlink (it loops in a worktree-only container) and `backend/.venv`. Keep `.tasks/`, which `task` needs on the host. From then on, commit from the worktree stack's own container.
- **Start the preview yourself when sudo is passwordless.** Check with `sudo -n true`. If it succeeds, run the preview as a background Bash task. If it fails, the user runs it in a separate terminal, because it needs interactive sudo.
  - **Start the stack with `PORT` unset first, then run the preview.** The compose file maps the frontend to `"${PORT-}:8000"`, and `preview.sh` exports `PORT` before cold-starting the stack. So a cold `PORT=8010 task app:preview` gives the frontend 8010 and then fails with "Bind for 0.0.0.0:8010 failed: port is already allocated".
  - **The two commands:** `cd <worktree> && env -u PORT devcontainer up --workspace-folder . --config .devcontainer/dev/devcontainer.json`, which gives the frontend a random host port, then `PORT=8010 task app:preview`, which attaches to the running stack. `preview.sh` never recreates a running stack.
  - **If a frontend already holds 8010:** `docker rm -f <project>-frontend-1`, then `env -u PORT docker compose -p <project> -f .devcontainer/docker-compose.{obt,app,dev,app-dev}.yml --profile '*' up -d --no-deps frontend`.
  - **Before starting, stop any older worktree stack still holding 8000 or 8010:** `docker ps --filter name=<old>-wt -q | xargs -r docker stop`. Ctrl-C on a preview reaps only its proxy, not the stack.
  - **Readiness:** the frontend answers 200 with HTML on any path, so wait until `/__svc/api/api/openapi.json` parses as JSON.
- **Playwright MCP tools only load at session start.** These are needed for the exploration step only; the scripted run doesn't need them.
  - **If `mcp__playwright__*` isn't listed,** the user restarts with `claude --continue`; the preview keeps running.
  - **The browser:** the revision must match MCP's bundled `playwright-core`, and the server must be registered with `--browser chromium`, because its default is system Chrome, which the devenv doesn't have. Dotfiles setup §9 handles both.
  - **"Chromium distribution 'chrome' is not found":** a server started before that flag was added is still running. Check `ps -eo args | grep playwright/mcp` for `--browser chromium`. The fix is `/mcp`, then reconnect `playwright`, with no restart needed.
  - **If MCP is unavailable,** explore with short scripted probes instead, and say so in the blind spots.
- **Confirm the stack serves the PR head:** `git rev-parse` inside the worktree api container, and the new field present in `/__svc/api/api/openapi.json` (`/__svc/api/openapi.json` is a 404). Through the preview, the API is at `http://localhost:PORT/__svc/api/api/…`, and the test-token user is admin. For platform-lite the effective-scopes endpoint to stub is `**/admin-users/me/scopes`.
- **Seed** through the API. Catalogue rows the API can't create (outcomes arrive via forge ingest) may be inserted with SQL into the worktree database only, prefixed `ui`. Record everything seeded, delete it at the end, and confirm the counts are back to where they started.
- **Evidence goes on an Artifact page:** the table, the screenshots embedded, the seed list and the blind spots. Screenshots are embedded as data URIs, since a page can't load outside images. Link it from ONE PR comment that also carries the table; `gh` can't attach images. Publishing makes the page private, and Claude can't change sharing, so ask the user to share it with the company from the page's Share menu, or reviewers can't open the link.
- `devcontainer up` leaves an untracked `.devcontainer/dev/devcontainer-lock.json`; never commit it.

## Phase 6 — Verify + summarize (you do this)
- **Trust but verify every subagent, and assume the first "done" may be stale.** These agents routinely (a) stop before committing/pushing with a premature "awaiting the suite" message, then (b) finish on a later resume — so their first completion notification often understates reality, and a *later* duplicate notification for the same task may report the true final state. Never act on the words; check the ground truth: `git rev-parse HEAD` vs `origin/<branch>`, `git status` clean, and grep the claimed change in the *pushed* file (`git show origin/<branch>:<file> | grep ...`). If the work isn't committed/pushed, TAKE OVER: run the suite from the devcontainer, commit as `om1` (no `--no-verify`), push. Re-run the full suite yourself for a first-party number regardless.
- One agent touches the repo at a time. Stay hands-off the working tree while a subagent runs, or a concurrent-commit race ensues. Isolate parallel mutators in worktrees.
- Post a final review-resolution comment. Fix PR descriptions that later commits have made wrong (test counts, "no migration", apply steps).
- Move the ticket to **Under Review** (transition "Submit for Review"), not Done. Done is the user's call after merge.
- If the epic keeps a `progress.md`, add a line: ticket, PR, merge commit, first-party test numbers, and lessons for later tickets.
- If this ticket completes a QA checkpoint, write `qa-checkpoint-<letter>.md` as an executable script for claude-in-chrome. For each step give the role, URL, action and expected result, and end with the evidence-table template. The user runs it from Claude Desktop on their laptop against deployed dev after logging in with SSO. Claude never drives deployed dev from the devenv.
- Summarize the whole run: Jira state, PR#, each phase's outcome, first-party test numbers, and what's left (team review/merge, follow-up tickets).

## Phase 7 — Merge and deployed check (on request, after the user merges)
- **Before a migration PR merges,** and especially a stacked or retargeted one: rebase on CURRENT `origin/main` and re-run `alembic heads` plus a scratch-database upgrade. Another PR may have added a migration.
- **Terraform across Atlantis roots:** `parallel_apply` is on, so never a bare `atlantis apply` when a change spans roots. Apply the roots that create objects first, e.g. `-d terraform/environments/{development,staging,production}` before `-d terraform/environments/common` for promotion grants. After apply, check as ENGINEERING with `SHOW GRANTS ON TABLE …`. The bodies of `EXECUTE AS OWNER` procedures are hidden from ENGINEERING, so confirm those from the Atlantis apply output.
- **After merge:** confirm the 🛳 Release run actually completed. The amd64 runner has left a Release queued for about 23 hours, with nothing shipped. If a rebase changed the merged commit's hash, compare its files with what you reviewed. Then follow the rollout. For app-factory prod, use the `factory-prod` SSO profile: `aws eks update-kubeconfig --name app-factory-prod`, then `kubectl -n <app> get jobs,pods,deploy`. Check that the `db-migration-N` job is Completed, the deployment's image is the new `main-N`, and `alembic current` in a pod shows the head. CloudWatch Logs Insights isn't available to that role. Deploy failures show up in `#app-factory-alerts`; successes aren't posted.
- **Deployed checks (only when the user asks):** script the ACs only a deployment can prove, such as endpoints behind the WAF, warehouse grants and refusal bodies. Use a real token, no browser. Writes go only to the `phenom-test-cus` tenant; record what you created and delete it at the end. Report `| check | expected | observed | pass/fail |`. A FAIL becomes a follow-up ticket (or a POM-516 entry during the phenom-health phase), not a force-push to main.

## Worktrees (one per ticket per repo)
- `git worktree add --no-track -b <branch> .pomNNN-wt origin/main` (or the parent PR's branch), created under the repo root.
- **To use the SHARED main-checkout devcontainer,** which mounts the repo root at `/usr/src` and sees the worktree as `/usr/src/.pomNNN-wt`: set the worktree's `.git` file to the RELATIVE `gitdir: ../.git/worktrees/-pomNNN-wt`. Keep the admin file `.git/worktrees/-pomNNN-wt/gitdir` ABSOLUTE, because git 2.43 marks a relative one as prunable. Never `git worktree prune`. Never run `devcontainer up` / `task app:preview` from a worktree set up this way; that's what the Phase 5.5 switch is for.
- If the shared container is stopped, start it from the MAIN checkout (`./obt devcontainer-up`), never from the worktree. It needs sudo, so an agent can run it only when `sudo -n true` succeeds; otherwise the user runs it.
- Pre-commit hooks in a worktree need `.tasks/`: relative symlinks into the main checkout's `.devcontainer-data/tasks/...`. Frontend jest in a worktree can symlink `frontend/node_modules` to `/usr/src/frontend/node_modules`, if `package*.json` matches `main`. None of this is committed.
- **The orchestration repo's services** pin `phenom-shared-models @ file:///usr/src/shared_models`, which is the MAIN checkout. In a worktree: `VIRTUAL_ENV=.venv uv pip install --reinstall --no-deps /usr/src/<wt>/shared_models`, then `uv run --no-sync pytest`. Plain `uv run` and `./obt test` re-sync from the main checkout and give false failures. Revert any `uv.lock` changes.
- Snowflake key paths for any devcontainer come from `~/.config/obt/container-env-config`, which dotfiles setup §3b symlinks with the devenv paths.

## Hard-won conventions (do not relearn these)
- Devcontainer commits as `-u om1`, never `--no-verify`; the commit's pre-commit hooks are the lint/format gate. `SKIP=<hook>` is a bypass too. If a hook fails for environmental reasons, fix the environment, or re-run the hooks in the right container with `pre-commit run --from-ref origin/main --to-ref HEAD`; never skip. Platform-lite's `mcp-scopes-lint` reads `/usr/src/config.json`, which in the SHARED container is the main checkout's config, so it fails to bootstrap. Commit changes to `backend/src/app/mcp/` from the worktree's own stack. `docker exec` default root will root-own `.git` — always `-u om1`.
- Subagent claims (esp. "I ran the review", "tests pass", "pushed", "awaiting the suite") are unreliable — verify via the posted PR comment and the pushed head, or re-check yourself. See [[subagent-code-review-claims-unreliable]] and [[verify-pushed-commit-not-worktree]].
- `git status` before every push; a fix living only in the working tree passes YOUR local run but CI/the-merge uses the pushed commit.
- Code-review confidence threshold is **50** for this user.
- Frontend has flaky, suite-load-dependent tests (Radix-select timeouts) — re-run a lone failure in isolation before calling it a regression.
- Jira: descriptions and corrections go in the body (Markdown), not comments. The sprint field is `customfield_10010` and story points are `customfield_10025`; keep an active-sprint id handy from a prior lookup.
- A new `PHENOM_CATALOG` table is readable by the deployed role only through the `always_apply` `ON ALL TABLES` grant with the table in its `depends_on`. It fails silently in deployed environments and works in localdev. See [[phenom-catalog-grant-on-all-tables-gotcha]].
- Shared-workflow and outward actions (cancelling or re-running CI, posting to Slack, Atlantis applies) need the user's go-ahead.
