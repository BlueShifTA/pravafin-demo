# Agent Routing — Claude + Codex + Project Skills

How work is divided between Claude (primary agent), Codex (secondary agent), and the project's local skills/agents. Summary lives in `CLAUDE.md`; this file is the full reference.

## Codex Policy

**Codex CLI** (`~/node_modules/.bin/codex`, authenticated) serves as a secondary agent for specific task types. Claude remains the primary agent for complex work.

### Agent Routing Table

| Task type | Agent | Notes |
|-----------|-------|-------|
| Adversarial review, code critique, design challenges | **Codex** | Always use Codex for reviews/critiques |
| Simple/small features, minor fixes, isolated tasks | **Codex** | 1–2 files, clear scope |
| Dev-cycle Phase 1 (audit) and Phase 6 (critic) | **Codex** | Review stages only |
| Multi-file architecture, complex features (>3 files) | **Claude** | Cross-cutting concerns |
| Research, web search, deep analysis | **Claude** | Needs tool orchestration |
| Writing (proposals, emails, documentation) | **Claude** | Needs conversation context |
| Planning, coordination (dev-cycle Phases 2–5) | **Claude** | Multi-step reasoning |
| Tasks needing MCP tools, APIs, or memory | **Claude** | Tool access required |

### Routing Decision Tree

1. Is it a review, critique, or adversarial challenge? → **Codex**
2. Is it a small, isolated change (1–2 files, clear scope)? → **Codex**
3. Does it need web search, MCP tools, or multi-step reasoning? → **Claude**
4. Does it touch >3 files or require architecture decisions? → **Claude**
5. Is it research, writing, or planning? → **Claude**
6. When in doubt → **Claude** (Codex is the secondary agent, not the default)

### How to Invoke Codex

```bash
# General task
~/node_modules/.bin/codex exec "<prompt with full context>" --dangerously-bypass-approvals-and-sandbox --ephemeral 2>&1

# Code review on uncommitted changes
~/node_modules/.bin/codex exec review --uncommitted --dangerously-bypass-approvals-and-sandbox --ephemeral 2>&1
```

Pass project-specific instructions inline or reference the project's CLAUDE.md. Codex runs in the same workspace and can read/write files.

### Installation

```bash
# Install Codex CLI
pnpm add -g @openai/codex

# Authenticate
codex login
# Follow browser auth flow

# Install Claude Code plugin (in Claude Code REPL)
/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex
/reload-plugins
/codex:setup
```

**Plugin skills available after install:**
- `/codex:review` — standard code review
- `/codex:adversarial-review` — challenge design decisions
- `/codex:rescue` — delegate a task to Codex in background
- `/codex:status` / `/codex:result` / `/codex:cancel` — manage Codex tasks

## Project Skills & Agents

Local skills live in `.claude/skills/<name>/SKILL.md`; local agents in `.claude/agents/<name>.md`. The harness surfaces them at session start — use this table as the routing map when a task matches.

**Always prefer an existing skill or `just` recipe over open-coding the equivalent commands.** If the task has a skill, call it instead of retyping the Bash.

### Skills (invoke with `/<name>`)

| Skill | Use when | Under the hood |
|-------|----------|----------------|
| `/install-deps` | Setting up, after pulling, imports fail | `just install` |
| `/run-dev` | Start backend/frontend servers | `just run-backend` / `run-frontend` |
| `/generate-types` | After changing backend API shape | `just generate-frontend-types` |
| `/format-code` | Before commit, after writing code, lint fails | `just format` |
| `/verify` | Confirm tests + types + lint pass | `just test` + `typecheck` + `lint` |
| `/ci` | Final check before PR | `just run-ci` |
| `/karpathy-check` | Catch over-engineering, drive-by edits, untested claims | `git diff` + `rg` (review-only) |
| `/simplify` | Kill dead code, DRY violations, quality issues | git + Edit, per-file lint, then `just test` + `typecheck` + `lint` |
| `/brutal-critic` | Adversarial review (`code`, `ux`, `architecture`, `security`) | spawns `read-only` agent; `ux` also calls `/screenshot` |
| `/dev-cycle` | Full audit → fix → verify → critic pass | chains `code-fixer` agents + Codex |
| `/research` | Deep source-backed doc on a topic | `WebFetch` (prefer) / `WebSearch` |
| `/autoresearch` | Bounded goal-directed iteration (≤20 rounds) | git branch + per-iteration verify |
| `/screenshot` | Visual QA or before UX review | Playwright (desktop + mobile) |
| `/seed-data` | Populate a fresh DB for testing/demo | OpenAPI + `curl` |

### Agents (spawn via `Agent(subagent_type=…)`)

| Agent | Purpose |
|-------|---------|
| `code-fixer` | Fix one disjoint workstream from a dev-cycle audit — edits only its assigned files. |
| `template-maintainer` | Maintain the template scaffold (bootstrap, cleanup, docs sync). |

### Routing shortcuts

- **Bug fix** → write failing test → fix → `/verify` → `/karpathy-check` (triage drift)
- **New feature** → TDD → `/verify` → `/format-code` → `/ci`
- **Cleanup sweep** → `/simplify` (already chains `/format-code` + `/verify`)
- **Before PR** → `/ci`
- **After backend API change** → `/generate-types`
- **Second opinion** → `/brutal-critic` or Codex (`~/node_modules/.bin/codex exec review --uncommitted ...`)
