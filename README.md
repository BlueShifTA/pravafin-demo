# CoreSat

Personal portfolio manager built on the **Core-Satellite strategy** — a low-cost passive ETF
core plus a small set of active stock picks. Interview demo showcasing data ingestion,
on-the-fly analytics, and a grounded LLM feature over real public market data.

FastAPI + PostgreSQL (RLS) backend · Next.js/MUI frontend · local Ollama LLM.

## What it demonstrates

| Concern | How |
|---|---|
| Data ingestion | Adapter registry + pydantic contracts; invalid rows → quarantine with reason; checksummed idempotent runs. 5 adapters over real feeds (yfinance CSVs ×2 layouts, iShares BOM/preamble exports, SEC-derived fundamentals) |
| Isolation | Postgres Row-Level Security per portfolio (`SET LOCAL` transaction context, `WITH CHECK`, SECURITY DEFINER creation) — data *and* LLM audit rows |
| Analytics | Everything derived at query time: position values from price series, 10/20y projections (weighted CAGR net of TER, ±1% band), magic formula as SQL window functions, technical indicators (SMA/EMA/RSI/MACD) as one-pass series over `prices_daily` |
| Grounded LLM | Stock comparison (`/api/compare`) and single-stock analysis (`/api/analysis/stock`): facts fetched by SQL and injected; LLM quotes, never computes; fabrication guard rejects numbers not in the facts; per-call token audit. Local Ollama only |
| V2 slot | Copilot drawer reserved for the LangGraph agent (see `ARCHITECTURE.md`) |

## Quickstart

```bash
just install          # deps + pre-commit
just stack-up         # Postgres 16 (pgvector image) on :5434 + Adminer on :8080
just ingest-all       # seed from ../etops-demo-data (541 tickers, 1.3M price rows)
just run-backend      # FastAPI on :8000  (needs Ollama for /api/compare)
just run-frontend     # Next.js on :3000
```

Tests: `just test` (integration tests auto-skip without Postgres; they use a
dedicated `coresat_test` database). Full gate: `just run-ci`. The real-LLM
comparison test is opt-in: `CORESAT_REAL_LLM=1 just test-backend -k real_llm`
(needs Ollama serving `qwen3.5:4b`).

## Data

Public sources staged in `../etops-demo-data/` (see its README for provenance and
re-download recipes): S&P 500 universe with GICS sectors, 10y daily OHLCV for 541
tickers, fundamentals + SEC XBRL 10-year financials, iShares fund holdings.

## Documents

- `V1-PLAN.md` — build plan for this version
- `ARCHITECTURE.md` — full architecture incl. V2 (LangGraph agent, RAG branch)
- `docs/overview.html` — visual architecture (serve with any static server)
- `reviews/` — external design review notes
