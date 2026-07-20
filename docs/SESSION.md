# Etops Interview Prep — Session Log

Claude Code session ID: `94b4c7c7-5b21-4360-8c67-8b9505d6cb4d`
Date: 2026-07-16

## Context

Interview: Senior Data Engineer (Python & AI) at Etops Group AG, Cham ZG.
Round: Chief Delivery Officer — Markus Paszt.

## Plans produced this session

### 1. Company research
- Etops: wealthtech SaaS + managed services (multi-bank data aggregation since 2010, founder Pius Stucki, ex-ZKB).
- Merged with niiio finance group Aug 2024; Pollen Street Capital majority owner; Stucki CEO of combined group.
- ~300 staff, ~2,000 clients, €500B on platform. Named clients: Swissquote, Swiss Life, Zurich, ZKB.
- Revenue: SaaS subscriptions (modular, enterprise pricing) + managed services/BPO + implementation services.

### 2. Interviewer intel — Markus Paszt (CDO)
- Career: Axon Insight AG (Head of Products & Analytics Services), axeed AG (CIO/board, manufacturing BI, Etops Group company), co-founder Selli AG (~2021, AI sales assistant, Etops-incubated, Bratislava office).
- Read: product-analytics builder, entrepreneurial, AI-forward but hype-skeptical, runs distributed delivery (CH/DE/LU/SK/GE/UA).
- Strategy: builder-to-builder tone, concrete systems detail, Swiss-German directness, no self-promotion polish.

### 3. Speculated Etops pain points (interview ammo)
- Data pipelines: custodian feed chaos, reconciliation drift, non-bankable asset data, niiio merger platform debt.
- AI in product: prototype→production gap, entitlement-aware RAG, hallucination liability in regulated domain, German financial docs, missing eval discipline.
- Token economics: no per-tenant cost attribution, no model routing, context stuffing, EU data residency / self-hosting.

### 4. Demo plan — CoreSat
- Full architecture: `ARCHITECTURE.md`
- Visual overview: `docs/overview.html` (serve: `python3 -m http.server 8080` in docs/)
- Reuse: pravafin backend/frontend scaffold (`~/Projects/pravafin/projects/{backend,frontend}`), LocalAI LangGraph agent core (`~/Projects/LocalAI/projects/backend/localai/services/agent/`).
- Agent: scope_guard → orchestrator → RAG pipeline (embed → hybrid search → rerank) | run_sql/get_projection → synthesiser → grounding_validator (re-plan ×1).
- Isolation: Postgres RLS per portfolio (data + chat + agent's run_sql).
- UI: wizard → dashboard (pie, projection, health radar), left drawer nav (Main/Core/Satellite + portfolio selector), right copilot drawer with citations + token cost.

### 5. Public data (downloads in ../etops-demo-data/)
- iShares ETF holdings CSV + factsheet/KID PDFs (fund DB + RAG corpus)
- yfinance price history (CAGR/projection/volatility)
- SEC EDGAR 10-K filings for satellite stocks (RAG)
- FinanceBench open-source rows (grounding-validator eval)
- Optional: EDGAR 13F, NBIM full holdings

## Memory

Persistent memory: `~/.claude/projects/-home-armywander-Projects/memory/etops-interview.md`
