---
name: karpathy-check
description: Review code against the 4 Karpathy-inspired coding principles (Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution). Use when user says "karpathy check", "principle review", or before finalizing a change to catch over-engineering, drive-by edits, speculative features, or untested claims.
allowed-tools: Bash, Read, Grep, Glob
argument-hint: "[target-path|--changed]"
---

Scan the target for violations of the 4 coding principles in `instruction/reference/CODING_PRINCIPLES.md`. Report findings grouped by principle — do **not** fix anything (review-only). Fixing is the user's call after seeing the report.

## Non-Negotiables (override everything else on conflict; canonical: `CLAUDE.md`)

- **No flattery, no filler.** Start with the findings table.
- **Disagree when you disagree.** If the diff is clean, say so — do not manufacture findings.
- **Never fabricate.** Every finding cites `file:line` and quotes evidence. No invented violations.
- **Stop when confused.** If intent behind a change is unclear, flag it — do not guess.
- **Touch only what you must.** Review-only: never edit files, never run verification. That's other skills' jobs.

**Target:** `$ARGUMENTS`

## Step 1: Identify Scope

- **`--changed`** (or no argument) — review files changed since the last commit:
  ```bash
  git diff --name-only HEAD
  git diff --name-only --cached
  ```
  Combine staged + unstaged. For each file, also capture the diff (`git diff HEAD -- <file>`) so you can judge whether each change traces to the stated request.

- **`[target-path]`** — review all source files under the path.

Skip binaries, lockfiles, generated files, `node_modules`, `.venv`, `__pycache__`.

Print the file list and total line count before proceeding.

## Step 2: Scan for Violations

For each file in scope, check against every principle. A single finding = `file:line — [principle] — description`.

### Principle 1 — Think Before Coding

Look for evidence the author skipped stating assumptions or surfacing tradeoffs:
- Magic numbers or thresholds with no comment explaining the choice
- Silent defaults inside business logic (e.g. `timeout or 30`, `limit or 100`) that hide a decision
- Functions with ambiguous names where two interpretations are plausible (e.g. `process_user`, `handle_data`) — flag for clarification
- New branches that assume a condition without checking it (e.g. `if x: do_thing()` where `x` is never validated upstream)

### Principle 2 — Simplicity First

Look for speculative complexity:
- New abstractions (ABC, Protocol, factory, registry, dispatcher) used by exactly one caller
- Configuration knobs / flags that have only one value in the codebase
- Wrapper functions that just forward arguments
- Try/except blocks catching errors that can't be raised by the wrapped code
- Classes with one method (candidate: replace with function)
- Extracted helpers smaller than their call sites' duplication × number of sites (violates the refactor ROI rule in `CLAUDE.md`)
- Comments explaining WHAT the code does (well-named identifiers already do that)

### Principle 3 — Surgical Changes

Requires diff context — only meaningful with `--changed` or when comparing against a stated task:
- Formatting/whitespace changes in files whose logic wasn't touched for the task
- Renamed variables / reordered imports in unrelated files
- "Improvements" to adjacent code (comments, docstrings, type annotations) that weren't requested
- Deletions of pre-existing dead code not produced by the current change
- Test-file edits when the stated task was a non-test change

For each finding, quote the user's request (if known) or the commit message / PR title, and show why the change doesn't trace back.

### Principle 4 — Goal-Driven Execution

Look for unverifiable / unverified claims:
- Bug fixes without a regression test
- New features without tests exercising the new code path
- Implementation commits that claim "fixes X" but no test reproduces X
- Refactor commits without contract tests pinned first (see `CLAUDE.md` → "Refactor Discipline → Pin the contract before refactoring")
- `TODO` / `FIXME` comments added alongside the change (unfinished work)
- Functions where the docstring promises behavior the tests don't check

## Step 3: Report

Print a grouped summary. No fixes, no file edits — this skill is review-only.

```
## Karpathy Principle Review

**Scope:** [N] files, [L] lines  (diff: [D] lines added, [R] removed)

### 1. Think Before Coding  ([count] findings)
- file:line — [short description]
- ...

### 2. Simplicity First  ([count] findings)
- file:line — [short description]  (suggested: remove / inline / collapse)
- ...

### 3. Surgical Changes  ([count] findings)
- file:line — [short description]  (unrelated to stated task: [task])
- ...

### 4. Goal-Driven Execution  ([count] findings)
- file:line — [short description]  (missing: test / verification)
- ...

### Summary
| Principle | Findings |
|-----------|----------|
| Think Before Coding | N |
| Simplicity First | N |
| Surgical Changes | N |
| Goal-Driven Execution | N |
| **Total** | N |

### Recommended Next Step
- [one-line recommendation: e.g. "inline the single-use Protocol in foo.py, then re-run"]
```

If there are zero findings, say so plainly. Do not manufacture findings to look thorough.

## Rules

- **Review-only.** Never edit files. Never run `just lint` / `just format` / tests — that's the `verify` or `dev-cycle` skill's job.
- **Every finding cites file:line.** No hand-wavy "there might be over-engineering somewhere."
- **Quote the evidence.** For Surgical Changes findings, show the diff hunk. For Goal-Driven findings, show the missing test.
- **Do not re-flag issues already covered by `simplify` or `verify`.** This skill focuses on principle violations, not general code smells — if something is already caught by ruff / mypy / the `simplify` skill, skip it.
- **Short over comprehensive.** A 10-finding report that's all real beats a 40-finding report padded with low-confidence guesses.
