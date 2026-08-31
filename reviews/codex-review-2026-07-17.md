# Codex review of ARCHITECTURE.md — 2026-07-17 (gpt-5.4, reasoning high)

Verdict: "too much agent theater, too little data-model and operational rigor."

## Accepted → plan changed
1. RLS: `SET LOCAL` transaction-scoped GUC, `missing_ok`, `WITH CHECK`, pool-reuse safety, one integration test proving no cross-portfolio leakage.
2. `run_sql` free-form SQL → typed query tools over approved read-only views (statement timeout, row limit, no catalog access).
3. Time-variance: `valid_from/valid_to` on funds; TER/region-mix are time-variant, not static.
4. Instrument master: add ISIN + currency; FX awareness (fx_rates fact table, CHF base).
5. Grounding validator claims softened: tolerance-bounded numeric matching; derived aggregates routed through get_projection, not re-derived by LLM.
6. Prompt injection: retrieved chunks framed as data-only; tool outputs never interpreted as instructions.
7. Scope re-tiered: MVP vs stretch, realistic estimate raised.

## Prepare verbal answers (don't build)
- Why pgvector not Elasticsearch (their stack): demo simplicity, one engine; in production hybrid retrieval could live in ES — know both.
- Oracle absence: golden source in Oracle → CDC/read-replica pattern, same contracts.
- Corporate actions/benchmark methodology: yfinance auto_adjust=True = split/dividend-adjusted closes; state definition of "performance vs benchmark" (total return, same currency).
- users/authn: single-user demo deliberately; RLS keyed on portfolio_id set by trusted middleware; prod = users + portfolio_memberships.
- FinanceBench alignment: validates doc-QA grounding only, not portfolio isolation — say so before they do.
- Demo vs prod: be explicit about what is intentionally faked.

## Rejected for demo (with reason)
- Full transactions/lots/cost-basis/cash-ledger model — right for product, kills demo timeline; acknowledge verbally.
- Table-cell-level citations — page+snippet is demo-adequate; mention limitation.
- Dropping LangGraph for plain tool router — the graph IS the showcase requirement (user wants LangGraph shown).

## Full findings (verbatim, abridged headers)
See conversation; key probes to rehearse:
- pooled connections + GUC reuse; who may set the GUC
- XBRL taxonomy mapping, restatements, units
- claim extraction/normalization/tolerance in validator
- one re-plan arbitrariness
- 0.7/0.3 hybrid weights untuned
- ingestion "~30 lines" credibility
- stale prices, market holidays, adjusted-close semantics
- realistic effort: 10-15 evenings, cut list: FinanceBench eval, reranker, quarantine UI, audit page, live-adapter theater
