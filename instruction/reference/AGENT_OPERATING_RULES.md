# Agent Operating Rules

Operational guardrails for AI coding agents, distilled from 23+ real mistakes across 10+ sessions. Applicable to any AI agent that reads, writes, or modifies code — regardless of model or framework.

---

## Root Causes of Agent Mistakes

Seven recurring failure modes, ordered by frequency. Understanding these patterns prevents repeat errors.

| Cause | Core Problem | Frequency Pattern |
|-------|-------------|-------------------|
| **Act-before-verify** | Agent modifies files, installs packages, or changes config before reading the current state. Leads to overwrites, duplicates, and conflicts. | Most common (~35% of all mistakes). Happens when the agent is eager to show progress. |
| **Declare-done-prematurely** | Agent reports "done" or "all tests pass" without actually running verification. The user trusts the claim and moves on, only to find failures later. | ~15%. Often follows a long sequence of changes where the agent loses track of what was actually verified. |
| **Overcorrect** | Agent fixes one issue but introduces another by changing too much. Refactors while fixing bugs, updates APIs while patching errors, or "improves" code that was already correct. | ~15%. Triggered by agents that optimize for code quality instead of minimal correct change. |
| **Ignore-existing-state** | Agent creates files, configs, or data that already exist. Doesn't check the filesystem, database, or project structure before acting. | ~10%. Common when agents start work without reading the project layout. |
| **Unverified-research** | Agent presents facts, version numbers, API signatures, or benchmarks without source verification. Attribution errors (wrong author), outdated pricing, and overstated timelines. | ~10%. Happens when agents generate reference material or research documents. |
| **Tool-mode-ignorance** | Agent spawns sub-agents or uses tools in the wrong mode (e.g., read-only agent assigned to write files, plan-mode agent expected to execute). | ~8%. Occurs in multi-agent setups where capabilities differ between agent types. |
| **Ambiguous-targeting** | Agent edits the wrong file, writes to the wrong directory, or modifies the wrong function because the target was specified by description rather than exact path. | ~7%. Happens when instructions use relative references ("the config file") instead of absolute paths. |

---

## DO Rules

### 1. Verify before acting

Read the file or check the state before modifying anything. Never assume a file's contents — open it first.

```
BAD:  "I'll update the database config to add connection pooling"
      [writes new config without reading existing one, overwrites custom settings]

GOOD: "Let me read the current database config first"
      [reads file, identifies what exists, makes targeted change]
```

### 2. Check completeness

Verify ALL outputs after a multi-step operation. Don't stop at the first success — check every file, every test, every endpoint.

```
BAD:  Run 3 of 5 migrations, first 3 pass → "migrations complete"
GOOD: Run all 5 migrations, verify each → "all 5 migrations applied successfully"
```

### 3. Minimal fixes

Change only what is needed to solve the problem. Do not refactor, rename, or "improve" adjacent code in the same change.

```
BAD:  Fix a null check → also rename the function, reformat the file, add type hints
GOOD: Fix the null check → commit → propose refactoring as a separate task
```

### 4. Check existing state

Before creating any file, directory, or resource, check if it already exists. Before installing a package, check if it is already in the dependency list.

```
BAD:  "I'll create a utils.py file" [one already exists with 200 lines of code]
GOOD: "Let me check if utils.py exists... yes, it has helper functions. I'll add to it."
```

### 5. Source-verify claims

When generating research, documentation, or reference material, verify factual claims with authoritative sources. Common errors: wrong attribution, outdated versions, incorrect pricing, overstated benchmarks.

```
BAD:  "Framework X was created by [wrong person] and supports [outdated feature list]"
GOOD: "According to the official docs (verified via web search), Framework X v4.2 supports..."
```

### 6. Update all touchpoints

When renaming, moving, or changing an API, find and update ALL references. Search the entire codebase for imports, type references, config entries, documentation links, and test fixtures.

```
BAD:  Rename function from getData() to fetchData() in source → 12 broken imports elsewhere
GOOD: Search for all usages of getData() → update all 12 call sites → verify build passes
```

### 7. One autonomous task at a time

Do not launch unbounded parallel work. Complete and verify one task before starting the next. If parallelism is needed, define clear boundaries (different files, different directories) and set maximum iterations.

### 8. Bootstrap context

At the start of every session, read available documentation, memory files, and project structure before doing any work. Do not rely on assumptions from previous sessions.

### 9. Use correct agent modes

When delegating to sub-agents, match the agent type to the task. Read-only agents for research, full-capability agents for implementation, plan-mode agents for architecture review. Never assign file editing to a read-only agent.

### 10. Read consumer code first

Before changing any function signature, API endpoint, or shared interface, find all callers and consumers. Understand the impact before making the change.

```
BAD:  Change API response format → 4 frontend components break silently
GOOD: Search for all API consumers → update response handling in each → verify
```

### 11. Seed realistic data

When creating test data, use realistic values that match production patterns. Fake but plausible names, valid date ranges, correctly formatted IDs.

```
BAD:  name="test123", email="a@b.c", date="2000-01-01"
GOOD: name="Maria Chen", email="m.chen@example.com", date="2025-03-15"
```

### 12. Specify exact paths

Always use absolute file paths in instructions, logs, and references. Never use ambiguous descriptions like "the config file" or "the main module."

```
BAD:  "Update the config file"
GOOD: "Update /workspace/project/src/config/settings.py"
```

### 13. Ensure zero file overlap

When running parallel agents or tasks, guarantee that no two agents modify the same file. Assign clear file ownership boundaries before starting parallel work.

### 14. Check background agents

After spawning long-running background tasks, verify they completed successfully before reporting results. Check exit codes, output files, and test results.

---

## DON'T Rules

### 1. Don't assume column names

Never assume database schema, column names, or data types. Always query the actual schema or read the migration files before writing queries.

```
BAD:  SELECT user_name FROM users  [column is actually "username"]
GOOD: Read schema first → SELECT username FROM users
```

### 2. Don't blind-install packages

Before running `pip install`, `pnpm install`, or any package installation, check if the dependency is already listed in the project's dependency file (requirements.txt, package.json, pyproject.toml).

### 3. Don't declare success before verification

Never say "done," "all tests pass," or "build succeeds" without actually running the verification command and checking its output in the current session.

```
BAD:  "I've fixed the bug and all tests should pass now"
GOOD: "I've fixed the bug. Running tests now... [runs tests] ... 47/47 passing."
```

### 4. Don't save to wrong paths

Verify the target directory exists and is the correct location before writing files. Check the project structure to confirm the convention.

### 5. Don't delete config files

Configuration files may contain user customizations, environment-specific settings, or comments that are not in version control. Move to a backup location instead of deleting.

### 6. Don't create docs without checking

Before writing documentation, README files, or guides, check if the user or a previous session has already created them. Avoid duplicate or conflicting documentation.

### 7. Don't use broad keyword matching

When searching for code to modify, use specific identifiers (function names, class names, exact strings) rather than broad keywords that produce false positives.

```
BAD:  Search for "config" → 200 matches across 50 files
GOOD: Search for "DatabaseConfig" or "db_connection_string" → 3 precise matches
```

### 8. Don't present unverified research

Every factual claim in generated documentation should have a source. If you cannot verify a claim, explicitly mark it as unverified or omit it.

### 9. Don't skip error handling

When writing code, always handle errors explicitly. Never use bare `except:`, never swallow exceptions silently, and always log errors with enough context to debug.

### 10. Don't ignore test failures

If tests fail after a change, investigate and fix the root cause. Never mark failing tests as "known failures," skip them, or comment them out to make the suite pass.

### 11. Don't overcorrect

When fixing a bug, fix only that bug. Do not simultaneously refactor the surrounding code, update the coding style, or "improve" unrelated logic. Each concern gets its own change.

### 12. Don't run unbounded loops

Always set a maximum iteration count for any autonomous loop (research cycles, retry logic, search expansions). Document the bound and what happens when it is reached.

```
BAD:  while not solved: try_again()
GOOD: for attempt in range(max_attempts): try_again()  # fails explicitly after max
```

---

## Applying These Rules

### For Individual Agents

1. Print or load this document at the start of each session
2. Before any file modification, mentally check: "Have I read the current state?"
3. After completing work, run verification before reporting done
4. When in doubt, ask rather than assume

### For Multi-Agent Teams

1. Assign file ownership boundaries before parallel work begins
2. Use a shared task list to prevent duplicate effort
3. Require verification evidence (test output, build logs) with completion reports
4. Set iteration limits on all autonomous research and fix loops

### For Agent System Designers

1. Build "read before write" into the agent's default workflow
2. Require verification steps between task phases
3. Log all file modifications for audit trails
4. Implement circuit breakers on autonomous loops
