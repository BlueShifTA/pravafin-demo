# CoreSat V1 — Build Plan

Goal: working product in ~4 evenings. Complete UI + simple ingestion pipeline + LangChain comparison.
**Not in V1**: LangGraph copilot, RAG/pgvector/rerank, chat, sentiment, fx, 10y financials history, docs. All V2 (see ARCHITECTURE.md).

## 0. Scaffold (30 min)

```bash
cp -r ~/Projects/project-instruction ~/Projects/coresat && cd ~/Projects/coresat
just bootstrap            # rename placeholders → coresat
just template-check       # exit 0
just template-reset-history
just install && just test # green baseline before writing a line
```
Structure inherited: `projects/backend` (FastAPI), `projects/frontend` (Next.js + MUI + React Query + Orval), justfile, CI, pre-commit, TDD rules from CLAUDE.md.

Add to docker-compose: `postgres:16` (pgvector image fine — extension unused until V2). Add deps: `langchain`, `langchain-openai` (or ollama), `yfinance` (not needed at runtime V1 — data pre-downloaded).

## 1. Schema + RLS (evening 1, first half)

Fact (shared, no RLS): `instruments`, `prices_daily` (PK instrument_id+date, OHLCV), `funds` (ter, fund_size, valid_from/to), `fundamentals` (1 row/ticker snapshot: pe, revenue, net_profit, margin, roe, ebit, nwc, ppe_net, cash, debt, shares, fcf).
Portfolio (RLS): `portfolios`, `sleeves`, `positions`. Plus `llm_audit_log` (RLS) for comparison calls.
Ops: `ingest_runs`, `ingest_quarantine`.

RLS hardened from day 1: `SET LOCAL app.portfolio_id` in request transaction, `current_setting(..., true)`, `USING` + `WITH CHECK`, app role without BYPASSRLS.
**Test first**: integration test — 2 portfolios seeded, each sees only its rows (API path). This is the test that matters.

## 2. Ingestion pipeline — simple but real (evening 1, second half + evening 2 first half)

```
POST /ingest/{adapter}  (explicit dispatch — provenance IS the routing)
  → SourceAdapter.parse() → pydantic contract → valid → staging → gate (row count, sums) → fact tables
                                              → invalid → ingest_quarantine(reason, run_id)
  → ingest_runs row per run (rows in/ok/quarantined, checksum → idempotent re-run)
```
Adapters (3): `universe_csv` (→instruments), `yfinance_daily_csv` (→prices_daily, glob over etops-demo-data/prices/daily/), `ishares_holdings_csv` (→funds + demo of quirky format), `fundamentals_csv` (→fundamentals + funds TER). CLI: `just ingest-all` seeds everything from ~/Projects/etops-demo-data.
**Tests**: contract violation → quarantine row; re-run same file → no dupes (checksum); sums gate.

## 3. Analytics — on the fly, zero LLM (evening 2, second half)

Endpoints (all computed from prices_daily + fundamentals at request time):
- `GET /portfolios/{id}/summary` — allocation pie data, current value (amount × latest close), drift vs targets, projection 10/20y (CAGR net of TER, contribution formula, ±1% band)
- `GET /market/candles/{ticker}?range=1y` — OHLCV for chart
- `GET /market/screener?sort=magic_rank` — **magic formula computed on the fly**: earnings_yield = EBIT/EV, ROIC = EBIT/(NWC+PPE), rank in SQL window functions. No stored ranking.
- `GET /market/ter-drag?fund=IWDA&years=20` — projection with/without TER
**Tests**: golden-set — known inputs → exact projection numbers (pin the formulas).

## 4. Comparison feature — LangChain, grounded by construction (evening 3, first half)

`POST /compare {tickers: [..], portfolio_id?}` →
1. SQL fetch fundamentals rows (deterministic)
2. LangChain: PromptTemplate (facts injected as markdown table) | llm | PydanticOutputParser
   → `ComparisonResult{per_criterion: [{criterion, winner, reasoning}], summary, caveats}`
3. Guard: every number in output must appear in input facts (regex extract + set check) → else single retry → else 422 with honest error
4. Log tokens/cost → llm_audit_log
Provider behind one boundary class (OpenAI or Ollama — pravafin pattern upgraded).
**Tests**: parser rejects malformed LLM output; number-echo guard catches fabricated figure (mock LLM).

## 5. UI — complete (evenings 3 second half + 4)

Reuse pravafin frontend components where they fit (DataGrid screener, dialogs); template already has MUI + Orval typegen.
- **Wizard** (MUI Stepper): capital/contribution → core ETF pick (funds table compare: TER, size, CAGR) → satellite stock picks (screener with on-the-fly magic rank) → review/save
- **Dashboard**: allocation pie · projection chart with horizon slider · current value/drift cards
- **Core page**: fund comparison table, TER-drag chart
- **Satellite page**: positions DataGrid, candle chart (add `lightweight-charts` — MUI x-charts has no candlestick), **Compare Selected → comparison dialog** (LangChain feature)
- **Ingestion page**: ingest_runs table + quarantine viewer (the pipeline demo surface)
- Left drawer: Main | Core | Satellite | Ingestion + portfolio selector + New Portfolio → wizard
- Copilot drawer: V2 — render disabled placeholder ("Copilot — coming in V2") so the UI shape is complete
Orval regen after every backend API change (`just generate-frontend-types`).

## 6. Definition of done (V1)

- [ ] `just ci` green (lint, typecheck, tests both sides)
- [ ] RLS isolation test passes API-side
- [ ] Malformed CSV → visible quarantine row with reason (demo moment)
- [ ] Re-ingest same file → zero duplicates
- [ ] Wizard → dashboard → screener → comparison flow clickable end to end
- [ ] Comparison output shows criterion verdicts + no fabricated numbers (guard test proves it)
- [ ] Screenshot set for interview backup (if live demo dies)

## V2 (next): LangGraph copilot (port LocalAI agent), RAG branch (docs → chunk → embed → hybrid → rerank), chat with per-portfolio isolation, sentiment tiles, fx/CHF, financials 10y history.

Data source: `~/Projects/etops-demo-data/` (751 files ready — universe, daily candles ×541, fundamentals, holdings).
