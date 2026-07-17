---
name: simplify
description: Review changed code for reuse, quality, and efficiency, then fix any issues found.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
argument-hint: "[target-path|--changed]"
---

Code simplification and quality review. Scans for reuse opportunities, quality issues, and efficiency problems, then fixes them.

## Non-Negotiables (override everything else on conflict; canonical: `CLAUDE.md`)

- **No flattery, no filler.** Start with the finding or the diff.
- **Disagree when you disagree.** If a "simplification" would harm clarity or behavior, refuse it and say why.
- **Never fabricate.** No invented callers, dead-code claims, or duplication counts. Grep first.
- **Stop when confused.** If a fix has two defensible shapes, report both — do not pick silently.
- **Touch only what you must.** Every changed line must trace to a reported issue. No drive-by reformatting.

**Target:** `$ARGUMENTS`

## Step 1: Identify Scope

Determine what code to review:

- **`--changed`** (or no argument) — review files changed since the last commit:
  ```bash
  git diff --name-only HEAD
  git diff --name-only --cached
  ```
  Combine both lists (staged + unstaged changes).

- **`[target-path]`** — review all files under the specified path.

Filter to source code files only (skip images, binaries, lockfiles, generated files, `node_modules`, `.venv`, `__pycache__`).

Print the file list and total line count before proceeding.

## Step 2: Scan for Issues

Read each file in scope and check for these categories:

### 2a. Dead Code
- Unused imports
- Unreachable code (after return/raise/break)
- Commented-out code blocks (more than 3 lines)
- Functions/classes with zero callers (use Grep to verify across the codebase)
- Unused variables

### 2b. Duplicate Logic (DRY Violations)
- Functions or blocks with near-identical logic (>10 lines of similarity)
- Copy-pasted patterns that should be a shared utility
- Repeated error handling patterns that could be a decorator or middleware
- Duplicate type definitions or constants

### 2c. Complexity
- Functions longer than 50 lines (candidates for extraction)
- Deeply nested conditionals (>3 levels)
- Functions with more than 5 parameters
- Classes with more than 10 methods (god classes)
- Cyclomatic complexity concerns (many branches)

### 2d. Efficiency
- N+1 query patterns (loop with individual DB/API calls)
- Redundant API calls or fetches (same data fetched multiple times)
- Missing memoization for expensive computations
- Unnecessary re-renders (React: missing useMemo/useCallback where deps are stable)
- Synchronous I/O in async contexts
- Large objects created in hot loops

For each issue found, record:
- File and line number
- Category (dead code / DRY / complexity / efficiency)
- Severity (high / medium / low)
- Proposed fix

## Step 3: Plan Fixes

1. Group issues by file.
2. Sort by severity (high first).
3. Print the issue table:
   ```
   | # | File | Line | Category | Severity | Issue | Fix |
   |---|------|------|----------|----------|-------|-----|
   ```
4. Estimate total lines to be removed/changed.

## Step 4: Apply Fixes

For each issue (grouped by file to minimize edits):

1. Make the fix using Edit.
2. After each file is modified, run a quick verification:
   - Python: `ruff check <file>` or equivalent linter
   - TypeScript: `pnpm exec tsc --noEmit` on the file or `pnpm exec eslint <file>`
3. If the fix introduces errors, revert the change and skip it with a note.

**Fix guidelines:**
- Extract shared utilities rather than just removing duplicates (create the abstraction).
- When removing dead code, verify zero callers first (Grep the entire codebase).
- When simplifying functions, preserve the public API (same function signature, same return type).
- Add a brief comment if the simplification is non-obvious.

## Step 5: Verify

Run the project verification suite to ensure no regressions:
- Tests: `just test` (or the project's test command)
- Lint: `just lint` (or the project's lint command)
- Type check: `just typecheck` (or the project's type check command)

If any check fails:
1. Identify which fix caused the failure.
2. Revert that specific fix.
3. Re-run verification to confirm green.
4. Note the reverted fix in the report.

## Step 6: Report

Print a summary:

```
## Simplification Report

**Scope:** [files reviewed] files, [lines scanned] lines
**Issues found:** [N]
**Issues fixed:** [M]
**Issues skipped:** [K] (with reasons)

### Changes by Category
| Category | Found | Fixed | Lines Removed |
|----------|-------|-------|---------------|
| Dead code | | | |
| DRY violations | | | |
| Complexity | | | |
| Efficiency | | | |

### Before/After
- Lines of code: [before] → [after] ([diff])
- Files modified: [N]

### Skipped Issues
- [file:line] — [reason it was skipped]

### Follow-up Recommendations
- [any larger refactors that were out of scope]
```

## Rules

- **Never change public API signatures** unless explicitly asked. Simplification is internal.
- **Verify zero callers before removing** any function, class, or export.
- **One fix at a time.** Do not batch unrelated changes into a single edit.
- **Revert on failure.** If a fix breaks tests, revert it — do not debug the test to accommodate the simplification.
- **Preserve behavior.** The codebase must behave identically after simplification. No functional changes.
- **Report honestly.** If no meaningful issues are found, say so. Do not manufacture busywork.
