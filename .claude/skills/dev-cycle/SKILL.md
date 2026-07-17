---
name: dev-cycle
description: Full development cycle — audit, plan, parallel fix, test, critic review. Use when user says "dev cycle", "fix cycle", or "audit and fix".
allowed-tools: Bash, Read, Grep, Glob, Agent, Write, Edit
argument-hint: [target-path]
---

Run a complete development cycle: audit the codebase, plan fixes, execute in parallel, verify, and re-review.

## Non-Negotiables (override everything else on conflict; canonical: `CLAUDE.md`)

- **No flattery, no filler.** Start each phase with its output, not preamble.
- **Disagree when you disagree.** If the audit or critic is wrong about an issue, say so before dispatching a fix.
- **Never fabricate.** No invented findings, priority levels, or verification results. Every issue cites `file:line`.
- **Stop when confused.** If workstream grouping is ambiguous (e.g. files overlap), ask — do not silently merge or split.
- **Touch only what you must.** Each workstream edits only its assigned files. Zero overlap is mandatory.

Target path: `$ARGUMENTS` (defaults to project root)

## Agent Roster

| Phase | Agent | Runtime |
|-------|-------|---------|
| 1 — Audit | Claude `Explore` sub-agent (read-only) | Sonnet 4.6, xhigh effort |
| 2 — Plan | Orchestrator (inline) | — |
| 3 — Fix | `.claude/agents/code-fixer.md` | Sonnet, one per workstream |
| 4 — Verify | Bash (`just` commands) | — |
| 5 — Critic | Codex (`~/node_modules/.bin/codex`) | Adversarial, ephemeral |
| 6 — Report | Orchestrator (inline) | — |

## Phase 1: Audit (Critic Review)

Spawn a **critic agent** (`subagent_type: Explore` — read-only by design, `model: sonnet`) — claude-sonnet-4-6, xhigh effort — to review the target path exhaustively:

- Read every file in the target path; do not skip or summarise — full coverage required
- Scan for bugs, code smells, type errors, security issues, dead code, SOLID violations, TypedDict misuse, banned import patterns
- Also flag **Karpathy-principle violations** (see `instruction/reference/CODING_PRINCIPLES.md`): speculative features / over-engineering (Simplicity First), drive-by edits unrelated to the stated goal (Surgical Changes), untested claims of behavior (Goal-Driven Execution), silent assumptions or hidden tradeoffs (Think Before Coding)
- Classify each issue: **P0** (breaks functionality), **P1** (significant bug/smell), **P2** (minor improvement), **P3** (nit/style)
- Output a structured issues list with file paths, line numbers, and descriptions
- Save the audit report to a temporary file for Phase 2

## Phase 2: Plan (Group into Workstreams)

Analyze the audit report and group issues into **workstreams by file overlap**:

- Each workstream owns a **disjoint set of files** — zero overlap between workstreams
- If two issues touch the same file, they must be in the same workstream
- Assign a clear description and issue list to each workstream
- Limit to 4-5 parallel workstreams maximum

## Phase 3: Parallel Fix

Spawn one **`code-fixer` agent** (`.claude/agents/code-fixer.md`) per workstream (`bypassPermissions: true`):

- Pass each agent: workstream description, full issue list with file:line references, and the exact files it owns
- Each agent fixes all issues in priority order (P0 → P1 → P2 → P3), editing only its assigned files
- Agents must NOT touch files outside their workstream — zero overlap is mandatory
- `bypassPermissions` is required so agents can edit files without approval prompts

Wait for all fix agents to complete before proceeding.

## Phase 4: Verify

Run the full verification suite:

```bash
just test
just lint
just typecheck
```

If any check fails:
- Identify which workstream's changes caused the failure
- Spawn a targeted **`code-fixer` agent** for those files only
- Re-run verification until all checks pass

## Phase 5: Final Critic Review

Run **Codex** as adversarial reviewer via Bash:

```bash
~/node_modules/.bin/codex exec "Adversarial code review. Review the git diff below and classify every issue P0–P3 (P0=breaks functionality, P1=significant bug/smell, P2=minor, P3=nit). Be hostile — assume the author missed things. Focus on: logic errors, type safety, SOLID violations, security, banned patterns (from __future__ import annotations, if TYPE_CHECKING, print(), module-level mutable instances), and Karpathy-principle violations (speculative features / over-engineering, drive-by edits unrelated to the stated goal, untested behavior claims, silent assumptions). Output file:line for every finding.\n\n$(git diff HEAD~1)" --dangerously-bypass-approvals-and-sandbox --ephemeral 2>&1
```

- If **any P0 issues** are found, loop back to Phase 3 with a new workstream for those issues
- P1–P3 issues are noted in the report but do not block completion

## Phase 6: Report

Produce a summary report:

| Metric | Value |
|--------|-------|
| Issues found (audit) | count by severity |
| Issues fixed | count |
| Tests before/after | pass/fail counts |
| Remaining P1+ issues | list if any |
| Files modified | list |

## Rules

- **Zero file overlap** between parallel agents is mandatory — violations cause merge conflicts
- **Always run verification** after fixes — never skip Phase 4
- **P0 in final review triggers re-fix** — the cycle does not complete with P0s outstanding
- **Do not modify test files** unless the issue is specifically about broken tests
- **Preserve existing code style** — match indentation, naming conventions, import patterns
