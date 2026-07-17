# Portfolio Draft Agent — Design

Date: 2026-07-17
Status: approved-pending-review

## Purpose

Second grounded agent on the New Portfolio page: a chat alternative to the
stepper wizard. The user describes a portfolio in natural language ("60% core
ETF in tech and medical, 40% five high-upside stocks from different
sectors"); the agent grounds every pick in the database, proposes a complete
draft, and — only after explicit in-chat confirmation — creates the
portfolio through the existing service path.

## Architecture: one class, two instances

The copilot's generic core is extracted into a single reusable class; both
agents are instances of it with different configuration.

```
services/agent/agent.py (new)
  class GroundedAgent:
      def __init__(self, llm: AgentLLM) -> None
      def run(query, context, tools: dict[ToolName, Tool])
          -> AsyncIterator[AgentEvent]     # plan / evidence / answer + usage
      # per run: Executor + LangGraph graph, scope_guard → planner →
      # execute → synthesise → grounding validator, one re-plan.
      # Identical policy for every instance — a fix here fixes both agents.
```

- Prompts live in the `AgentLLM` instance: `ChatModelAgentLLM` gains a
  constructor `prompts` parameter (scope / planner / synthesiser texts).
  Copilot keeps its current texts; the draft agent gets goal-directed ones.
- `CopilotService` becomes thin glue (RLS persistence, chat_messages, audit,
  per-portfolio tools) around instance #1. Its contract is pinned by the
  existing integration tests, which must stay green unchanged.
- New `DraftService`: stateless glue around instance #2.

## Provider switching: model as protocol

`AgentLLM` (Protocol) → `ChatModelAgentLLM` → any LangChain `BaseChatModel`.
Local vs API is configuration, not code:

```
COPILOT_PROVIDER=ollama         # or openai
DRAFT_AGENT_PROVIDER=openai     # or ollama
OLLAMA_BASE_URL / OLLAMA_MODEL  # existing
OPENAI_API_KEY / OPENAI_MODEL   # new; default model gpt-5-mini
```

`main.py` gains `build_chat_model(provider, settings) -> BaseChatModel`
('ollama' → ChatOllama, 'openai' → ChatOpenAI). Missing/empty
`OPENAI_API_KEY` while a provider is `openai` fails at startup, not
mid-chat. `.env.example` documents the new variables with placeholders;
real keys never enter the repo. New dependency: `langchain-openai`.

## Draft flow

Domain additions (`domain/agent.py` or `domain/draft.py`):

```
class DraftPosition(BaseModel):  ticker, weight
class PortfolioDraft(BaseModel): name, initial_capital, monthly_contribution,
                                 core_fund_ticker, core_weight,
                                 satellites: list[DraftPosition]
class Answer(...):               + action: Literal["chat","propose","create"] = "chat"
                                 + draft: PortfolioDraft | None = None
```

Copilot ignores the new fields (defaults). Draft agent's synthesiser prompt:

- gather requirements conversationally; every ETF/stock pick must come from
  run_sql evidence (sector exposure via fund_holdings ⨝ instruments.sector;
  "high upside" via magic-formula screener columns);
- when the draft is complete → `action: "propose"` + full draft + summary
  prose; ask the user to build or change;
- when the user confirms a shown proposal → `action: "create"` + the
  confirmed draft;
- on change requests → refine and re-propose.

## API

```
POST /api/portfolio-draft/chat      SSE: plan → evidence → answer [→ created]
  body: { message: str,
          history: [{role, content}],          # frontend-held; no DB row yet
          proposed_draft: PortfolioDraft | null }  # last shown proposal
```

Stateless: no portfolio exists, so no RLS scope, no chat_messages row, and
no llm_audit_log row (portfolio_id is NOT NULL) — accepted, documented gap.

Create rails — the only LLM-adjacent write in the system:
1. `action: "create"` is honored only when `proposed_draft` is present in
   the request (a proposal was actually shown); otherwise degraded to
   propose.
2. The draft must pass deterministic validation: tickers/fund exist in DB
   (existing `UnknownTickerError` path), core_weight + satellite weights sum
   to 1 (tolerance 0.001), capital > 0.
3. Creation goes through the existing `PortfolioService.create` — the agent
   never writes SQL. Success emits SSE `created {portfolio_id}`; failure
   emits `error` and the conversation continues.

## Frontend (wizard page)

- Toggle "Wizard | Assistant" on `/wizard`; assistant pane reuses the
  copilot drawer chat pattern (SSE reader, bubbles, typing dots).
- `answer.action == "propose"` renders a draft summary card (allocation
  table: core fund + weight, satellites + weights, capital, monthly).
- SSE `created` → set active portfolio to the new id (existing
  portfolio-context), invalidate the portfolio-list query (wizard-fix
  pattern), navigate to the dashboard.
- Conversation history lives in component state and is echoed back per
  request.

## Grounding

The validator's grounded-number set is evidence numbers ∪ numbers extracted
from the user's query and conversation context — capital, contributions, and
weights are user-stated facts that appear in no SQL evidence and must not
trip the fabrication guard. This union applies to `GroundedAgent`
generically (the copilot benefits identically: "is 60% of 100000 enough"
no longer risks a false fabrication hit on 100000).

DB-only. The RAG pipeline does not exist yet (no doc_chunks, no pgvector,
no ingested documents) — the tool slot stays reserved exactly as in the
copilot; when the docs branch lands (ARCHITECTURE.md §8 item 6) both agents
gain the tool through `GroundedAgent` without structural change.

## Testing

- `GroundedAgent` extraction: existing 117-test suite stays green unchanged
  (contract pin for the refactor).
- Unit/graph tests with scripted LLM: propose flow emits draft; create
  without prior proposal is degraded; grounding validator still applies to
  draft numbers.
- Integration (fake LLM): full propose → confirm → created round trip
  against coresat_test; ticker-validation failure path; weights-sum failure
  path.
- Frontend: assistant pane renders proposal card; created event switches
  portfolio. Real-OpenAI e2e test gated behind CORESAT_REAL_LLM=1 plus a
  set OPENAI_API_KEY, skipped otherwise.

## Out of scope

RAG pipeline construction, chat persistence for pre-creation conversations,
audit rows for draft chats, streaming token-by-token output.
