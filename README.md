# CoreSat

Personal portfolio manager built on the **Core-Satellite strategy** — a low-cost passive ETF
core plus a small set of active stock picks. Interview demo showcasing data ingestion,
on-the-fly analytics, and a grounded LLM feature over real public market data.

FastAPI + PostgreSQL (RLS) backend · Next.js/MUI frontend · local Ollama LLM.

## What it demonstrates

| Concern | How |
|---|---|
| Data ingestion | Adapter registry + pydantic contracts; invalid rows → quarantine with reason; checksummed idempotent runs. 6 adapters over real feeds (yfinance CSVs ×2 layouts, iShares BOM/preamble exports, SEC-derived fundamentals, and PDFs → page-provenance `doc_chunks` for RAG) |
| Isolation | Postgres Row-Level Security per portfolio (`SET LOCAL` transaction context, `WITH CHECK`, SECURITY DEFINER creation) — data *and* LLM audit rows |
| Analytics | Everything derived at query time: position values from price series, 10/20y projections (weighted CAGR net of TER, ±1% band), magic formula as SQL window functions, technical indicators (SMA/EMA/RSI/MACD) as one-pass series over `prices_daily` |
| Grounded LLM | Stock comparison (`/api/compare`) and single-stock analysis (`/api/analysis/stock`): facts fetched by SQL and injected; LLM quotes, never computes; fabrication guard rejects numbers not in the facts; per-call token audit. Local Ollama only |
| Agentic AI | Copilot drawer chats over a LangGraph graph (`scope_guard → planner → executor → synthesiser → grounding validator`, up to 3 self-correcting re-plans then a `rag_search` fallback then honest refusal). Tools: `run_sql` (read-only, RLS-scoped transaction; SQL guided by vetted `sql_templates`), `get_projection` (deterministic analytics), and `rag_search` (embed → hybrid pgvector∪full-text → cross-encoder rerank over `doc_chunks`). Answers stream over SSE with citations; every node's tokens land in `llm_audit_log` per graph run. A second **draft agent** reuses the same core to build a portfolio from natural language (see `ARCHITECTURE.md`) |

## Quickstart

```bash
just install          # deps + pre-commit
just stack-up         # Postgres 16 (pgvector image) on :5434 + Adminer on :8080
just ingest-all       # seed from ../etops-demo-data (1,200 instruments, 2.9M price rows)
just run-backend      # FastAPI on :8000  (needs Ollama for /api/compare)
just run-frontend     # Next.js on :3000
```

Tests: `just test` (integration tests auto-skip without Postgres; they use a
dedicated `coresat_test` database). Full gate: `just run-ci`. The real-LLM
comparison and copilot tests are opt-in: `CORESAT_REAL_LLM=1 just test-backend
-k real_llm` (needs Ollama serving `gemma4:e4b`).

## Data

Public sources staged in `../etops-demo-data/` (see its README for provenance and
re-download recipes): 1,000 stocks plus 200 ETFs, 10y daily OHLCV, full-universe
stock fundamentals with SEC XBRL fallbacks, and iShares fund holdings.

## Documents

- `V1-PLAN.md` — build plan for this version
- `ARCHITECTURE.md` — full architecture; LangGraph copilot shipped, RAG branch pending
- `docs/overview.html` — visual architecture (serve with any static server)
- `reviews/` — external design review notes
