# Repository Guidelines

**CoreSat** — Core-Satellite portfolio manager (interview demo). FastAPI + PostgreSQL-with-RLS backend, Next.js frontend (MUI, React Query, Orval), local Ollama LLM, orchestrated with `just`.

Domain vocabulary: a **portfolio** owns **sleeves** (`core` = passive ETF, `satellite` = stock picks) holding **positions**; **fact tables** (instruments, prices_daily, funds, fund_holdings, fundamentals) are shared read-all, **portfolio tables** are RLS-scoped via `SET LOCAL app.portfolio_id`. The **ingestion pipeline** (adapter registry → pydantic contracts → quarantine → loaders, checksummed `ingest_runs`) writes fact tables with the admin engine; the API uses the RLS-enforced app engine. Its expanded source covers 1,000 stocks plus 200 ETFs; latest-year SEC values supplement missing comparison fields, and sparse fundamentals upserts preserve existing non-null facts. Analytics (projections, magic formula, TER drag, technical indicators SMA/EMA/RSI/MACD, and the 6-criterion **portfolio health radar** on `/summary`, whose **volatility** and **sector-concentration** criteria are full-portfolio **look-through**: the core ETF is decomposed into its `fund_holdings` basket (sector concentration falls back to the fund's `category` when a fund discloses no holdings), unpriced names keep their weight via a beta × market-factor proxy, and the surviving priced names are never rescaled to 100% — so a concentrated or undiversified core actually counts instead of being invisible) are always computed on the fly — no stored derived tables. Fund comparison: `GET /api/market/funds?compare=A,B`. The **grounded LLM features** — stock **comparison** (`/api/compare`) and single-stock **analysis** (`/api/analysis/stock`) — share `services/grounding.py`: facts injected as vertical key-value blocks rounded to 6 significant figures, output numbers guarded against the injected set, one retry, audited in `llm_audit_log`. The **copilot** (right drawer) chats over a **LangGraph agent** (`services/agent/`): `scope_guard → planner → executor → synthesiser → grounding validator`, up to 3 self-correcting re-plans (each validation error — fabricated figure, failed run_sql, flagged miss — is fed back to the planner) then a single `rag_search` fallback then honest refusal; planner SQL is guided by the vetted patterns in `services/agent/sql_templates.py` (one source of truth, executed by `test_sql_templates`); LLM calls in exactly those three LLM nodes via the `AgentLLM` protocol (`PydanticOutputParser` prompting — the small local model ignores tool-calling/json_schema modes). Executor tools: `run_sql` (planner-written SELECT on the RLS-scoped, READ ONLY, timeout-capped connection; sanitized first — ```sql fences stripped, only the first statement kept, placeholder tokens like `<TICKER>` rejected — so small-model drift never reaches the DB), `get_projection` (deterministic analytics), and `rag_search` (deterministic embed → hybrid pgvector∪full-text pool → cross-encoder rerank over the shared `doc_chunks` fact table; the step's question is the query). Chat: `POST /api/portfolios/{id}/chat` (SSE: plan → evidence → answer), history GET, clear-context DELETE, audit GET, `GET /api/copilot/info` (model name); `chat_messages` is RLS-scoped; `llm_audit_log` carries `graph_run_id` + `node` per copilot run. Canned refusal texts are filtered out of the LLM context (a small model treats past refusals as precedent and keeps refusing). The **RAG branch has landed**: PDFs ingest through the same pipeline (`pdf` adapter → per-page pypdf chunks → nomic-embed-text 768-d embeddings → `doc_chunks`, a shared read-all fact table with pgvector HNSW + generated full-text indexes, checksum-idempotent), and both agents plan over the shared `rag_search` tool; an empty corpus simply yields a gap. A second **draft agent** (`services/agent/draft_service.py`, `POST /api/portfolio-draft/chat`) reuses the same `GroundedAgent` core to build a portfolio from natural language and create it (on explicit confirmation) through `PortfolioService.create` (satellite names/tickers are resolved against `instruments` by ticker, exchange-suffix, or company name; if none resolve it refuses to propose a lone 100%-core draft); provider per agent is config (`COPILOT_PROVIDER`/`DRAFT_AGENT_PROVIDER` = ollama|openai) via `services/agent/provider.py`. See `ARCHITECTURE.md` §4.

Key extra commands: `just stack-up` (Postgres :5434 + Adminer web UI :8080), `just db-apply`, `just ingest-all [data_dir]`. Tests run against the dedicated `coresat_test` database and auto-skip without Postgres; the real-LLM comparison test is gated behind `CORESAT_REAL_LLM=1` (needs Ollama serving `gemma4:e4b`).

Before anything on a dev laptop: verify RTK is active (`rtk --version && rtk gain`). See `~/.claude/RTK.md`.

## Project Layout

- `projects/backend/coresat` — FastAPI app: `main.py` entrypoint, `api/` routers, `core/config.py` settings; `projects/backend/tests`
- `projects/frontend` — Next.js app: `src/app/` routes, `src/components/layout/AppProviders.tsx` (MUI + React Query), `src/lib/generated/` (Orval client — never hand-edit), `orval.config.ts`, `next.config.ts` (rewrites)
- `devops/` — pre-commit config, bootstrap/cleanup scripts, custom lint checks, CI Docker
- `docs/` — Sphinx docs; `instruction/` — role templates, coding profiles, guides, reference rules
- `justfile` — all automation; `.github/workflows/ci.yml` — CI

## Build / Run / Dev

All commands via `just` — `just --list`. Install: `just install`. Delete deps/build/tool caches: `just clean` (restore with `just install`).

| Task | Command |
| ---- | ------- |
| Backend (http://127.0.0.1:8000) | `just run-backend` |
| Frontend (http://localhost:3000) | `just run-frontend` |
| Tests (backend + frontend, both mandatory) | `just test` |
| Single backend test | `just test-backend -k <test>` |
| Format (ruff + prettier + eslint --fix) | `just format` |
| Lint everything (whole-repo pre-commit) | `just lint` |
| Typecheck (mypy + pyright + tsc) | `just typecheck` |
| Mirror GitHub CI locally | `just run-ci` |
| Regenerate frontend API client (backend must run) | `just generate-frontend-types` |
| Tag + push release (empty = auto patch bump) | `just create-version [X.Y.Z]` |

### Generated API client

FastAPI serves `openapi.json` → frontend downloads it → Orval generates types + React Query hooks into `src/lib/generated/`. Derived artifacts — never hand-edit. After any backend API change: `just run-backend`, then `just generate-frontend-types`.

### Template lifecycle

When this template is copied into a new project, de-templating is mandatory — not optional polish:

1. `just setup` — one-shot scaffold: renames placeholders, installs everything, prints the de-templating checklist. (Pieces: `just bootstrap --project-name "My App" --project-slug my-app --python-package my_app --non-interactive` for automation.)
2. After first successful build: change, adjust, or delete **everything still template-related** — demo surface (`POST /api/example/echo`, demo homepage sections), example tests, `instruction/profiles/surapat/`, template wording in docs.
3. `just template-check` — deterministic remnant scan (brand strings + demo surface, file:line). Re-run until it exits 0.
4. Update `README.md` to describe the real project.
5. **Rewrite this `CLAUDE.md`** so it describes the new project — its layout, domain vocabulary, and commands. A CLAUDE.md that still describes the template is doc drift.
6. **Finally, `just template-reset-history`** — wipes template git history into a single clean initial commit (destructive, asks for confirmation). Immediately after it runs, delete the `template-reset-history` recipe from the `justfile` (and its mentions in README and the bootstrap checklist), then `git add -A && git commit --amend --no-edit` — the new repo must not ship a history-wiping command. Then point `origin` at the new project repo and force-push. The new project's history starts at zero — no template commits.

## Documentation

Docs drift constantly — treat them as first-class. Cross-check before and after every non-trivial change; fix whichever side is wrong.

Doc surfaces: `CLAUDE.md`, `README.md`, `docs/` (Sphinx), `instruction/`, `projects/backend/README.md`, docstrings.

- **Before editing**: read docs covering the area. Surface any drift instead of silently picking a side.
- **After editing**: `grep -r` for every renamed/removed symbol, route, command, env var, file path; update each hit.
- **New behaviour, flags, routes, env vars, commands** → doc update in the same commit. No "docs later".
- **Customer-visible changes** → once the project ships customer-facing docs (e.g. `projects/frontend/public/documentation/`), update them + add a release note in the same commit.
- Don't fabricate doc references. If no doc covers the area, say so.
- Code vs. documented contract: pick the authoritative one deliberately and update the other — never leave the contradiction.

## Core Principles (Karpathy-inspired)

Apply to every coding task. Bias toward caution over speed; for trivial tasks use judgment. Full rationale: [instruction/reference/CODING_PRINCIPLES.md](instruction/reference/CODING_PRINCIPLES.md).

1. **Think Before Coding** — don't assume; don't hide confusion. State assumptions explicitly. If multiple interpretations exist, present them — don't pick silently. If a simpler approach exists, say so; push back when warranted. If something is unclear, stop and ask before implementing.
2. **Simplicity First** — minimum code that solves the problem. No features beyond what was asked, no abstractions for single-use code, no unrequested configurability, no error handling for impossible scenarios. If you write 200 lines and it could be 50, rewrite. Ask: "Would a senior engineer say this is overcomplicated?"
3. **Surgical Changes** — touch only what you must. No "improving" adjacent code, no drive-by refactoring, match existing style. Remove orphans YOUR change created; leave pre-existing dead code (mention it instead). Every changed line traces to the request.
4. **Goal-Driven Execution** — define verifiable success criteria before starting. "Fix bug" → "write a failing test that reproduces it, make it pass". For multi-step work, state a brief plan with a verify step per item. Loop until verified.

## Workflow — TDD

Every change: **Red → Green → Refactor**. Never write implementation before the test exists; if you can't test it, redesign until you can.

1. **Research** — affected files, dependencies, existing patterns (`rg`, `git log`)
2. **Plan** — approach, edge cases, error paths; for refactors present alternatives and pin contract tests first
3. **Test first** — failing tests defining expected behavior → confirm RED
4. **Implement** — minimum code to pass → confirm GREEN
5. **Refactor** — clean up while tests stay green
6. **Validate** — `just lint && just typecheck && just test` before every commit

## Coding Style — Python

Full rules: [instruction/reference/PYTHON_STYLE.md](instruction/reference/PYTHON_STYLE.md). Enforced summary:

- `snake_case` functions/vars, `PascalCase` classes, `CONSTANT_CASE` module constants, `_private` prefix for internal.
- All imports at module top. No lazy/wildcard imports, no `from __future__ import annotations`, no `if TYPE_CHECKING:` blocks (all three hook-enforced). Relative imports within a directory, absolute across modules, no `from ..`.
- Type-annotate every `__init__` parameter and attribute; return `-> None`. No `Any` unless justified.
- `@dataclass` for data structures; `TypedDict` for JSON shapes (all keys required, `X | None` for nullable — no `NotRequired`, no `total=False`, no `dict[str, object]`/`dict[str, Any]`).
- `typing.Protocol` for interfaces, not ABCs. No module-level mutable service instances (module constants and `app = create_app()` are fine).
- Avoid default/optional arguments. Prefer explicit params or typed config. Exception: documented library-API defaults.
- `async`/`await` for all I/O; `asyncio.sleep()` not `time.sleep()`. `logging.getLogger(__name__)`, never `print()`. Catch specific exceptions — never silent `except Exception`.
- Always `zip(a, b, strict=True)`.
- No `sys.path` mutation in source (hook-enforced).

**SOLID is mandatory** — SRP, OCP, LSP, ISP, DIP; `Protocol`-based polymorphism with concretions injected at the composition root is the primary DIP mechanism. Extended examples: [instruction/reference/SOLID_PRINCIPLES.md](instruction/reference/SOLID_PRINCIPLES.md).

Architecture: thin `api/` handlers → `services/` business logic → `domain/` Pydantic models → `core/` config/middleware. Middleware order, lifespan resources, bounded executors, shared CLI error boundary: [instruction/reference/FASTAPI_PATTERNS.md](instruction/reference/FASTAPI_PATTERNS.md).

## Coding Style — Frontend

- Format/lint via Prettier + ESLint (`just format`).
- Data fetching through the generated React Query hooks — not hand-rolled fetch, hardcoded paths, or `useEffect`. Avoid `useEffect` in general.
- Components `PascalCase.tsx` in `src/components/` (shared UI in `components/ui/`), pages in `src/app/`; props `camelCase`.
- Static navigation → `next/link`, not `router.push`.
- Downloads: `<a href=…>`, not custom JS/blob fetches.
- Prefer shared UI wrappers (`components/ui/` — e.g. `AppButton`, `AppTextField`) over repeating raw MUI config inline.
- Never use emojis in UI or generated text — use `@mui/icons-material` icons (version must match the `@mui/material` major).
- Numbers through `src/lib/format.ts` (`formatNumber`, `formatMoney`, `formatPercent`) — compact ≥1M (`$7M`, `141.6B`), max 2 decimals, `n/a` for null.
- Only titles may be bold (700); outside of titles use semibold (600).
- Render with real providers (theme + React Query) — single composition point: `AppProviders`.

## Testing

Full rules and banned shapes: [instruction/reference/REFACTOR_AND_TESTING.md](instruction/reference/REFACTOR_AND_TESTING.md).

- **Functional tests only** — exercise a real code path through the public interface; assert on observable behavior (response body, status code, DOM text, exit code, side effect). Structural tests are banned: no isinstance-after-construction, no `callable()` checks, no parametrize-over-the-same-set, no `inspect.signature` existence checks.
- Backend: `TestClient` / real invocation. Frontend: render with real providers, assert user-facing DOM. CLI: `CliRunner.invoke` / `subprocess.run` only.
- Priority: error paths and edge cases first, happy path second, regression test for every bug fix.
- Coverage floor **80%** (CI-enforced); core logic 95%+, routes 90%+, services 85%+.
- `just test` runs pytest + vitest — neither optional. Single test: `just test-backend -k <test>`.

## Refactor Discipline

Full rules: [instruction/reference/REFACTOR_AND_TESTING.md](instruction/reference/REFACTOR_AND_TESTING.md). Non-negotiables:

- **Pin the contract first** — functional tests capturing current observed behavior of any consumed surface (API, CLI, exit codes, message formats), committed before the refactor starts.
- **Measure the metric you're selling** ("simpler"/"smaller"/"faster") every iteration; name trade-offs upfront if it moves the wrong way.
- **Helper-extraction ROI**: `helper_size < duplication_per_site × sites` — else keep the duplication.
- **Preserve every defensive fallback branch** from the old code, not just the happy path.
- **Adversarial review per iteration** (Codex or second session); findings are to-fix items.

## Do Not

- Bypass hooks (`--no-verify`, `SKIP=<hook>`). Fix the root cause.
- Hand-edit generated clients (`src/lib/generated/`) or lock files.
- Write implementation before the failing test.
- Use `print()` (use `logging`), `Any` without justification, or `useEffect` for data fetching.
- Read, cat, print, or log `.env` / `.env.local` contents — ever. Only `.env.example` and `.env.test` may be read. To check a var is set: `test -f .env && grep -c "VAR_NAME" .env` (count only). Create `.env` files via Write with placeholders only.
- Commit a backend API change without regenerating frontend types.
- Claim a UI change works without browsing it.
- Fabricate anything — file paths, commit hashes, API names, test results, library functions. Read the file, run the command, or say "I don't know, let me check."
- Open with flattery or filler ("Great question", "You're absolutely right", "I'd be happy to"). Start with the answer or the action.
- Ship code that contradicts existing docs (`README.md`, `docs/`, `instruction/`) without updating them in the same commit.
- Declare a task finished without the user's confirmation — present verified results and wait for sign-off.
- Skip the drift check — always cross-check code against docs (`CLAUDE.md`, `README.md`, `docs/`, `instruction/`) and surface mismatches.

## Verification Checklist

Pre-commit handles formatting, ruff, mypy, pyright, prettier, eslint, tsc, and the custom bans (sys.path mutation, future annotations, TYPE_CHECKING). Before a PR also verify:

- [ ] `just test` green; regression test included for bug fixes
- [ ] No dead code, no unused imports; internal methods `_`-prefixed
- [ ] TypedDict discipline (no `dict[str, Any]`, `NotRequired`, `total=False`, `cast(T, {...})`)
- [ ] No tautological tests; CLI tests via `CliRunner.invoke`
- [ ] SOLID: SRP/OCP/LSP/ISP/DIP hold; interfaces minimal; concretions injected
- [ ] Refactors: contract tests pinned, metric measured, fallbacks preserved
- [ ] `just run-ci` passes locally

## Pre-commit & Commits

Pre-commit installed by `just install`; whole-repo run: `just lint`. Config: [devops/.pre-commit-config.yaml](devops/.pre-commit-config.yaml). Enforced — on failure, fix and make a new commit (`--amend` after a failed hook is wrong: the commit never happened).

Commit messages: imperative mood, lead with root cause, one concern per commit. Never add `Co-Authored-By` trailers or AI-attribution footers ("Generated with…") — the message describes the change, not the tooling.

```
<action> <what> [<detail>]

- problem: <root cause>
- <what changed>
- <impact/testing notes>
```

Semantic versioning; tag releases with `just create-version` — empty arg auto-increments PATCH (fixes/small features); pass `X.Y.Z` explicitly for MINOR (new modules/API additions) or MAJOR (breaking changes) bumps. Confirms interactively, then creates the annotated tag `vX.Y.Z` and pushes it. Tag when shipping, not per commit.

## Agents & Skills

Claude is the primary agent; Codex (`~/node_modules/.bin/codex`) is secondary for reviews/critiques and small isolated fixes (1–2 files). When in doubt → Claude. Prefer existing skills (`/verify`, `/ci`, `/format-code`, `/dev-cycle`, `/karpathy-check`, …) and `just` recipes over open-coding commands. Full routing tables, Codex invocation, and the skills/agents catalog: [instruction/reference/AGENT_ROUTING.md](instruction/reference/AGENT_ROUTING.md).

## Pushback & Adversarial Review

Act like a senior coworker. Challenge wrong approaches, propose better ones with reasoning, ask when ambiguous, surface risks. Don't manufacture dissent — when the user is right, say so and move on.

Assume every diff is read by a skeptic. Reviewers look for bugs, shortcuts, weakened tests, scope creep, rule violations. Don't silence failing checks; don't leave TODOs where fixes belong; don't narrow assertions to match buggy output.

## Failures Are Yours

Any failing check — test, typecheck, import cycle, lint — is yours to fix, related to your change or not. The base is failure-free by assumption; if it's broken, your branch broke it.

**Never investigate provenance.** "Mine or preexisting?" changes nothing — you fix it either way — so the check is pure waste and usually a dodge. Banned however framed: `git stash` + re-run, checkout `main`/base to reproduce, "test normal entry vs. base", bisect-to-blame, any A/B against a clean tree.

These thoughts mean STOP — fix the root cause instead:
- "Check if pre-existing or mine"
- "Test the base/main to see if it reproduces"
- "This error is probably unrelated to my change"
- "Stash and confirm first"

## Instructional Documentation

`instruction/README.md` is the navigation entrypoint: role templates (`templates/`), coding profiles (`profiles/`), workflow guides (`guides/`), and reference rules (`reference/` — security patterns, audit checklists, agentic architectures, and the style/testing references linked above). `instruction/profiles/surapat/` is an example profile — replace or delete after bootstrapping.
