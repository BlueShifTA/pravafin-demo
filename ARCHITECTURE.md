# CoreSat — Personal Portfolio Manager (Etops interview demo)

Core-Satellite portfolio management with grounded AI copilot.
Demonstrates: data integration/ingestion, analysis, LangGraph agentic AI, hallucination control, multi-portfolio isolation.

---

## 1. Product scope

- Multi-portfolio: user creates portfolios via guided wizard; each fully isolated (data + chat).
- Wizard: (1) initial capital + monthly contribution → (2) Core sleeve: pick ETF from fund database, compare funds, set weight → (3) Satellite: pick stocks, weights → (4) review & save.
- Main dashboard: allocation pie, current situation, growth projection (10/20y), portfolio health radar.
- Core page: fund comparison (TER, CAGR, size, region mix), TER-drag simulation, fund documents.
- Satellite page: positions, per-stock performance vs core benchmark, 10-K insights.
- Copilot (right drawer): per-portfolio chat, grounded answers with citations, token/cost display.

## 2. Public data sources

| Source | Content | Role |
|---|---|---|
| iShares/Vanguard product pages | Holdings CSV per ETF (quirky headers/footers) | Fund database values + ingestion adapter #1 (CSV) |
| ETF factsheets + UCITS KIDs (PDF, public) | TER, objective, risk class, region/sector mix | Document knowledge base (RAG) + parsed values |
| yfinance | Prices, dividends, historical series | CAGR estimation, projections, volatility; adapter #2 (API) |
| SEC EDGAR | 10-K PDFs of satellite stocks | RAG corpus for stock questions; adapter #3 optional (13F JSON) |
| FinanceBench (150 public rows) | Q/A/evidence on 10-Ks | Eval set for grounding validator accuracy |

Fund database = `funds` table populated by ingestion: one row per ETF (ticker, name, TER, fund_size, replication, distribution policy, region weights JSON, sector weights JSON) + linked documents.

## 3. Database (Postgres 16 + pgvector)

**Isolation: Row-Level Security.** `portfolio_id` on every portfolio-scoped table; middleware sets `app.portfolio_id` per request; RLS policy enforces. LLM `run_sql` tool uses same connection → physically cannot cross portfolios. Chat history isolated the same way.

```
-- fact tables (shared, read-all — no RLS): market/reference data
funds(id, ticker, isin, name, ter, fund_size, replication, distribution, region_mix jsonb, sector_mix jsonb,
      valid_from, valid_to)                       -- TER/mix are time-variant; current row = valid_to IS NULL
instruments(id, ticker, isin, name, type, sector, region, currency)
fx_rates(base_ccy, quote_ccy, date, rate)         -- CHF base; demo seeds USD/CHF, EUR/CHF
prices_daily(instrument_id, date, open, high, low, close, volume)   -- candles, yfinance
financials(instrument_id, fy, revenue, opex, net_income, net_margin, ocf, capex, fcf, ebit, nwc, ppe_net, ...)
sentiment(index_name, date, value)                                   -- CNN F&G, crypto F&G, VIX
magic_formula(instrument_id, fy, earnings_yield, roic, magic_rank, ...)
doc_chunks(id, source_doc, instrument_id?, fund_id?, page, text, embedding vector(768))

-- portfolio-scoped (RLS on portfolio_id):
portfolios(id, name, initial_capital, monthly_contribution, created_at)
sleeves(id, portfolio_id, kind core|satellite, target_weight)
positions(id, portfolio_id, sleeve_id, instrument_id|fund_id, weight, amount)
chat_messages(id, portfolio_id, role, content, citations jsonb, tokens_in, tokens_out, created_at)
llm_audit_log(id, portfolio_id, graph_run_id, node, model, tokens_in, tokens_out, cost, created_at)

-- ingestion:
staging_fund_holdings(...), ingest_quarantine(id, source, payload jsonb, reason, created_at)
```

RLS sketch (hardened per Codex review):
```sql
ALTER TABLE positions ENABLE ROW LEVEL SECURITY;
CREATE POLICY per_portfolio ON positions
  USING      (portfolio_id = current_setting('app.portfolio_id', true)::int)   -- missing_ok: unset GUC = no rows, not error
  WITH CHECK (portfolio_id = current_setting('app.portfolio_id', true)::int);  -- writes can't smuggle other ids
```
- Middleware: `SET LOCAL app.portfolio_id = :id` **inside the request transaction** — transaction-scoped, dies at commit, pooled-connection reuse cannot leak it.
- App role: no BYPASSRLS, no catalog write, `statement_timeout`, row limit.
- One integration test proves isolation: seed 2 portfolios, query as each, assert zero cross-reads (both API and agent paths).
- Demo simplification, stated openly: single-user, portfolio_id set by trusted middleware; prod adds `users` + `portfolio_memberships` and keys RLS on membership.

## 4. Data flows

### Ingestion pipeline (problem 1: integrating new data sources) — 8 stages, typed routing
```
sources (CSV / REST / PDF / JSON)
  → 1 landing zone (raw + checksum, idempotent replay)
  → 2 adapter dispatch (registry → SourceAdapter, ~30 lines/source)
  → 3 contract check (pydantic per record) ──invalid──→ 4 quarantine (reason + run id, replayable)
  → 5 staging + quality gates (sums, counts, freshness)
  → 6 router by data class (one PostgreSQL, two table groups):
       fact tables (shared, read-all)   — instruments, funds, prices/candles, financials 10y, sentiment, magic formula
       portfolio tables (RLS-protected) — portfolios, sleeves, positions, chat_messages, llm_audit_log
       documents → 7 doc branch: parse → chunk (page provenance) → embed → doc_chunks (pgvector, fact table)
  → 8 lineage: ingest_runs (source, adapter version, rows in/ok/quarantined) → UI ingestion page
```
- Orchestration: demo = `POST /ingest/{adapter}` + CLI; prod = one Airflow DAG per source, same stages as tasks.
- Adapters: `ishares_csv`, `yfinance_prices`, `edgar_facts`, `sentiment_feed`, `pdf_document`.
- Ingestion and retrieval (§agent RAG pipeline) share the chunk/embedding contract.
- Agent SQL tool: single `run_sql` (read-only) — fact tables visible to all portfolios, portfolio tables filtered by RLS on the request's connection.
- Scale-out note (verbal, not built): at ~100× data volume, route analytical workloads to a columnar engine (DuckDB/ClickHouse) reading parquet in place.

### Analytics (deterministic — no LLM)
- CAGR: from 10y yfinance history per instrument/fund.
- Projection: `FV = capital·(1+r)^n + contrib·[((1+r)^n −1)/r]`, r net of TER. 10/20y horizons, per sleeve + combined. Sensitivity: ±1% CAGR band.
- TER drag: projection with/without TER, delta highlighted.
- Evaluation criteria (computed, feeds radar 0–10 + traffic details):
  | Criterion | Metric | Green threshold |
  |---|---|---|
  | Allocation discipline | drift from core/sat target | ±5% |
  | Sector concentration | max sector weight in satellite (HHI alt.) | <40% |
  | Region concentration | max region weight combined | US <65% |
  | Cost efficiency | weighted TER | <0.40% |
  | Core-satellite overlap | satellite tickers' weight inside core ETF | <20% |
  | Volatility | annualized σ of combined backfilled series | <18% |
  Headline score = mean of criterion scores.

### Agent (problem 2: hallucination control) — LangGraph, orchestrator-centric (armlab.io diagram style)

> **Status:** shipped in `services/agent/` (graph, tools, SSE chat, per-node audit). The
> RAG pipeline branch is not wired yet — documents are not ingested (build order §8 item 6);
> the planner's tool set is `run_sql` / `get_projection` / `gap` until then. The
> orchestrator node is named `planner` in code.
```
question → scope_guard ──in scope──→ orchestrator ──docs──→ RAG pipeline: embed → hybrid search → rerank
              │off-topic                  │  │data──→ run_sql / get_projection
              └→ canned refusal (≈0 tok)  │  (or both)          │
                                          ↑          evidence   ↓
                        re-plan ×1 ←─ grounding_validator ← synthesiser
                                              │pass → END
```
- **scope_guard**: cheap classifier (tiny model) — intent + leak guard. Off-topic → canned refusal before any expensive call.
- **orchestrator**: LLM router — decides docs / data / both, emits typed tool calls.
- **RAG pipeline** (deterministic once triggered): embed (nomic-embed-text or text-embedding-3, 768-d) → hybrid search (pgvector cosine + tsvector BM25-ish, weights 0.7/0.3) → rerank (bge-reranker-v2-m3) → top-k chunks with page provenance.
- **Query data tools**: `run_sql` (read-only role, RLS-scoped connection) · `get_projection` (analytics service — LLM never computes numbers).
- **synthesiser**: LLM writes answer with [n] citations from evidence.
- **grounding_validator** (plain code): every numeric claim must appear in SQL rows / projections / chunks → fail injects errors → one re-plan → still failing → "cannot answer from data".
- LLM calls in exactly 3 nodes: scope_guard, orchestrator, synthesiser. Everything else deterministic.
- Every node logs to `llm_audit_log` → per-run cost trace in copilot footer.

### Second LLM surface — stock comparison (plain LangChain, no agent)
Fixed-shape question → no graph needed. `/api/compare?tickers=NVDA,ASML`:
```
fetch fundamentals + magic_formula rows (deterministic SQL)
  → LangChain chain: prompt template (facts injected as table) + pydantic output parser
  → comparison narrative + verdict per criterion; numbers ECHOED from input, never computed
  → logged to llm_audit_log (same cost accounting)
```
- Grounded by construction: input-controlled (all facts supplied), not tool-controlled. Cheap regex check that output numbers ⊆ input numbers.
- Evolves pravafin's `compare_stocks` (prompt-stuffing, unvalidated) into its grounded form — before/after story in git history.
- Interview line: "two integration patterns — single-call chain for fixed-shape questions, agent graph for open-ended ones. Choosing the small tool is the skill."

## 5. UI (Next.js + TS + MUI, orval-generated client — pravafin frontend base)

```
┌─────┬───────────────────────────┬────────────────┐
│ ☰   │  MAIN DASHBOARD           │ 🤖 Copilot     │
│ Main│  Portfolio: [Port1 ▾]     │ (Port1 scope)  │
│ Core│  ◔ allocation pie         │ chat + [n]     │
│ Sat  │  ▁▃▅█ projection 10/20y  │ citations      │
│     │  current value / drift    │ tokens+cost    │
│     │  health radar 7.2/10      │                │
└─────┴───────────────────────────┴────────────────┘
```
- Left drawer: Main | Core | Satellite (+ portfolio selector, + "New portfolio" → wizard).
- Wizard: MUI Stepper, 4 steps, validates each step.
- Main: pie (core/sat/cash), projection chart with horizon slider, situation cards, health radar + warning chips.
- Core: fund comparison table (from `funds`), TER-drag chart, document list with ingest status.
- Satellite: positions DataGrid, perf vs core benchmark, doc insights.
- Copilot drawer: chat scoped to selected portfolio (`chat_messages` RLS), citation popovers (SQL text / doc chunk + page), cost footer. Switching portfolio switches history — Port2 never sees Port1 queries.
- Eval: radar + score cards on Main; traffic-light detail rows on Core/Sat pages (criteria table above).

## 6. API surface (FastAPI)

```
POST /api/portfolios                    create (wizard submit)
GET  /api/portfolios                    list
GET  /api/portfolios/{id}/summary       situation + projection + evaluation
GET  /api/funds?compare=IWDA,VWRL       fund comparison
POST /api/ingest/{adapter}              run adapter (file upload or trigger)
GET  /api/ingest/quarantine             quarantine viewer
POST   /api/portfolios/{id}/chat        SSE stream: plan → evidence → answer + citations
GET    /api/portfolios/{id}/chat        history (RLS-scoped)
DELETE /api/portfolios/{id}/chat        clear chat context (RLS-scoped)
GET    /api/portfolios/{id}/audit       token/cost log
GET    /api/copilot/info                configured model name
```
Middleware: resolve portfolio_id → `SET app.portfolio_id` on the request's DB connection.

## 7. Reuse map

| From | Take |
|---|---|
| pravafin `projects/backend` | FastAPI scaffold, routers, async SQLAlchemy, yfinance service, magic_formula/technical_indicators (satellite screening bonus) |
| pravafin `projects/frontend` | Next.js+MUI+orval pipeline, DataGrid/dialog components |
| LocalAI `services/agent/` + `domain/agent.py` | LangGraph graph, Plan/Step/Evidence/Answer, AgentLLM boundary, executor pattern |
| LocalAI infra | docker-compose (Postgres+pgvector, Ollama), justfile patterns |
| New | RLS migration, adapters+quarantine, scope_guard, grounding_validator, funds ingestion, projections/evaluation analytics, wizard+dashboard pages, copilot drawer |

## 8. Build order (each step demoable)

1. Postgres+pgvector compose, schema + RLS, seed script — ½ evening
2. Ingestion: ishares_csv + yfinance adapters, contracts, quarantine + funds table — 1 evening
3. Analytics: CAGR/projection/TER-drag/evaluation + summary endpoint — 1 evening
4. Agent port: graph + tools + scope_guard + grounding_validator + audit log — 1–1½ evenings
5. Frontend: wizard, drawer nav, dashboard, copilot drawer — 1½ evenings
6. Docs ingestion (factsheets/10-Ks) + FinanceBench mini-eval — ½ evening
7. Polish + rehearse demo script — ½ evening

Total ≈ 6–7 evenings. Cut line if short: drop EDGAR 13F adapter and FinanceBench eval (mention verbally).

## 9. Demo script moments (interview)

1. Wizard → dashboard: product sense.
2. Feed malformed CSV → quarantine with reason: ingestion discipline.
3. Add new adapter live (30 lines): integration extensibility.
4. Copilot: "which satellite drags my 20y projection?" → plan trace + citations + verified numbers.
5. Ask off-topic → instant guardrail refusal, near-zero tokens.
6. Ask something not in data → "gap" honest refusal.
7. Switch portfolio → chat history isolated; show RLS policy in psql: isolation below app layer.
8. Audit page: per-node token/cost — unit-economics story.
