---
name: autoresearch
description: Autonomous goal-directed iteration. ONLY activate when user explicitly requests it. MAX 20 iterations — never run unbounded loops.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Agent
argument-hint: "[goal] Iterations: N"
---

Autonomous goal-directed iteration loop. Runs bounded cycles of analyze, plan, execute, verify, and decide (continue or stop).

**Goal:** `$ARGUMENTS`

Parse the goal and iteration count from arguments. If no iteration count is specified, default to 10. Maximum is 20 — refuse anything higher.

## Subcommands

The first token after `/autoresearch` selects the mode. Default is general-purpose.

| Invocation | Mode | Goal template |
|---|---|---|
| `/autoresearch [goal] Iterations: N` | General | Achieve the stated goal autonomously |
| `/autoresearch:plan [feature]` | Architecture planning | Produce an architecture plan with pros/cons/alternatives |
| `/autoresearch:debug [symptom]` | Bug hunting | Find the root cause of the described symptom |
| `/autoresearch:fix [issue]` | Fix iteration | Iterate test-fix-test until the issue is resolved |
| `/autoresearch:security [scope]` | Security audit | Find and fix security vulnerabilities in scope |
| `/autoresearch:ship [scope]` | Ship readiness | Iterate lint, test, build, docs until all pass cleanly |
| `/autoresearch:scenario [question]` | Scenario exploration | Explore what-if scenarios and document findings |
| `/autoresearch:predict [change]` | Consequence prediction | Predict downstream effects of a proposed change |

## Setup Protocol (Before Iteration 1)

1. **Verify tools** — confirm required CLI tools are available (git, test runners, linters as needed).
2. **Create branch** — `git checkout -b autoresearch/<slug>` from current HEAD. All work happens on this branch.
3. **Initial analysis** — read relevant files, run tests/lint to establish baseline state. Record baseline in the first commit message.
4. **Log iteration plan** — commit a short plan as the first commit: goal, scope, max iterations, success criteria.

## Iteration Loop (Repeat Until Done or Max Reached)

Each iteration follows 8 phases:

### Phase 1: Review
- Run `git log --oneline -20` to read recent history (git is your memory).
- Summarize current state: what has been done, what remains, any regressions.

### Phase 2: Ideate
- Generate 2-5 hypotheses or approaches for the next step.
- Pick the single most promising one. Justify the choice briefly.

### Phase 3: Modify
- Make ONE focused change. Do not combine unrelated changes.
- Keep the diff small and reviewable.

### Phase 4: Commit
- `git add` the changed files (specific files, not `-A`).
- Write a descriptive commit message: what changed and why.
- Include `[autoresearch N/M]` in the message (current iteration / max).

### Phase 5: Verify
- Run the appropriate verification for the change type:
  - Code changes: tests, linter, type checker
  - Config changes: validation command or dry-run
  - Documentation: spelling/link check if available
- Record pass/fail status.

### Phase 6: Guard
- Check for regressions: did anything that was passing before now fail?
- If regression detected: `git revert HEAD` (preserve history, never force-push or reset).
- After revert, return to Phase 2 with the regression as new context.

### Phase 7: Decide
- **Stop conditions** (any one triggers stop):
  - Goal achieved and verified
  - Max iterations reached
  - Stuck: same approach failed twice with no new hypotheses
  - User-defined success criteria met
- If not stopping, proceed to next iteration.

### Phase 8: Log
- Print a concise iteration summary:
  ```
  [Iteration N/M] <status: pass|fail|revert>
  Changed: <files>
  Result: <what happened>
  Next: <plan for next iteration or "DONE">
  ```

## Completion Protocol

When the loop ends (success or max iterations):

1. **Final verification** — run full test/lint/build suite one last time.
2. **Summary report** — print:
   - Goal and whether it was achieved
   - Total iterations used (N of M)
   - Key changes made (list commits)
   - Any remaining issues or follow-up work
   - Branch name for review
3. **Do NOT merge** — leave the branch for the user to review and merge.

## Rules

- **Never exceed the iteration cap.** If max is reached, stop and report partial progress.
- **Never run unbounded loops.** Every loop must have a counter and a max.
- **Git revert for rollbacks.** Never use `git reset --hard` or `git checkout .` — always `git revert` to preserve history.
- **One change per iteration.** Resist the urge to fix multiple things at once.
- **Read git log every iteration.** Your memory resets between turns — git history is your continuity.
- **Fail loudly.** If a phase fails, log it clearly and decide whether to revert or adapt.
