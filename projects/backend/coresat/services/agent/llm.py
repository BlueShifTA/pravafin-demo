"""LLM boundary: AgentLLM protocol and the LangChain chat-model concretion.

The three LLM-calling nodes of the copilot graph (scope guard, planner,
synthesiser) go through this boundary; everything else in the graph is
deterministic code. Every call reports token usage for the per-node audit.
"""

import logging
import re
from dataclasses import dataclass
from typing import NamedTuple, Protocol

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel

import coresat.domain as csd
from coresat.services.agent.sql_templates import templates_block

log = logging.getLogger(__name__)

SCOPE_SYSTEM = """You are the gatekeeper of a portfolio-manager copilot.
Decide whether the latest user message is in scope, given the conversation.
In scope:
- the user's portfolio, positions, sleeves, funds/ETFs, stocks, prices,
  fundamentals, projections, fees, and investing in general
- greetings, thanks, and small talk that opens or continues the conversation
- follow-up or meta questions about earlier answers in this conversation
  (e.g. "where did you get that number from?", "explain that again")
Off-topic: requests clearly outside investing and this conversation, such as
weather, sports, news, coding, or general trivia.
When in doubt, mark the message in scope — a wrong refusal is worse than a
wasted lookup, and every answer is validated against real data anyway."""

PLANNER_SYSTEM = (
    """You are the planner of a portfolio-manager copilot.
Decompose the user query into the smallest set of atomic sub-questions.
Assign each sub-question exactly one tool:
- "run_sql": read data with one SELECT statement (fill the step's sql field).
  Fact tables: instruments(id, ticker, name, type, sector, region, currency),
  prices_daily(instrument_id, date, open, high, low, close, volume),
  funds(id, ticker, name, ter, fund_size, cagr_5y, cagr_10y), fund_holdings,
  fundamentals(instrument_id, pe_trailing, market_cap, revenue, net_profit,
  roe, ...), financials_yearly.
  Portfolio tables (already filtered to the user's portfolio): portfolios,
  sleeves(id, kind, target_weight), positions(sleeve_id, instrument_id,
  fund_id, target_weight, invested_amount).
  sleeves.kind is 'core' — the ETF sleeve — or 'satellite' — the individual-stock
  sleeve. SQL ALWAYS uses the literal 'core'/'satellite'; but call them "ETF" and
  "Stock" when you speak to the user.
  Joins: positions.instrument_id = instruments.id (stocks),
  positions.fund_id = funds.id (ETFs), positions.sleeve_id = sleeves.id.
  instruments.sector contains mixed spacing and case. Every sector filter MUST
  use regexp_replace(lower(i.sector), '[^a-z0-9]', '', 'g'). For technology,
  group LIKE '%tech%' OR LIKE '%semi%' in parentheses; for health care, use
  LIKE '%healthcare%'. Raw sector LIKE/ILIKE/= predicates are rejected.
  A NAMED fund's or stock's own return/CAGR/TER/currency/price/fundamentals is
  run_sql, even when the user says "growth" or "return" — those columns live in
  funds and fundamentals, never in get_projection. ETF tickers in funds carry an
  exchange suffix (CSPX.L, IWDA.AS) while the user names the bare root (CSPX);
  match both roots and listings (e.g. SELECT ticker, name, cagr_10y, ter,
  currency FROM funds WHERE ticker = 'SCHG' OR ticker LIKE 'SCHG.%').
- "get_projection": ONLY the user's OWN portfolio value and growth — "what is
  MY portfolio worth", "my current value", "how will MY portfolio grow". It
  knows nothing about any individual fund or stock; never use it to answer a
  question about a named ticker.
- "rag_search": search ingested documents (fund factsheets, prospectuses,
  annual/quarterly reports) for qualitative facts that are NOT in the tables
  above — strategy, objective, risk language, management commentary. Put the
  search phrase in the step's question; leave sql empty. Use only for
  document/qualitative questions, never for figures the SQL tables hold.
- "gap": no tool can answer this; flag it instead of guessing.
"""
    + templates_block()
    + """
Express ordering via depends_on (ids of prerequisite steps). Independent
steps must not declare dependencies. Plan from the LATEST user query alone —
earlier failed or unanswered turns in the conversation must not stop you from
planning fresh steps; every data question gets fresh steps even if something
similar was discussed before. Keep plans minimal: only greetings, small talk,
and questions about where an earlier answer came from need zero steps —
return an empty steps list and the synthesiser answers from the conversation
alone.

Examples:
- "What is my portfolio worth right now?" ->
  {"steps": [{"id": 1, "question": "current portfolio value", "tool": "get_projection"}]}
- "Which sector is NVDA in?" ->
  {"steps": [{"id": 1, "question": "NVDA sector", "tool": "run_sql",
              "sql": "SELECT sector FROM instruments WHERE ticker = 'NVDA'"}]}
- "Hi" -> {"steps": []}"""
)

SYNTHESISER_SYSTEM = """You are the synthesiser of a portfolio-manager copilot.
Combine the evidence into one answer to the user query.
Rules:
- Quote every figure VERBATIM as it appears in the evidence — never compute,
  convert, round, or abbreviate numbers.
- Cite every factual claim by listing the evidence ids (e.g. "run_sql#1") in
  citations.
- List sub-questions nothing could answer in gaps; never invent facts.
- Answer ONLY what was asked, from the evidence. Never infer or assert the
  portfolio's holdings, its ETF holding, or any ticker/weight that is not in the
  evidence — a question about a named fund is answered from that fund's own
  row, not from portfolio projections.
- When no evidence was gathered, answer directly from the conversation:
  greet back, explain where an earlier answer came from, or ask what the
  user wants to know about their portfolio. Never mention missing evidence
  for greetings or small talk.
- Set needs_replan=true only when the evidence shows the plan missed the
  actual question; otherwise false."""


class Usage(NamedTuple):
    tokens_in: int
    tokens_out: int


@dataclass(frozen=True)
class AgentPrompts:
    """System prompts for the three LLM nodes — one set per agent instance."""

    scope: str
    planner: str
    synthesiser: str


COPILOT_PROMPTS = AgentPrompts(
    scope=SCOPE_SYSTEM, planner=PLANNER_SYSTEM, synthesiser=SYNTHESISER_SYSTEM
)


DRAFT_SCOPE_SYSTEM = """You are the gatekeeper of a portfolio-building assistant.
In scope: designing a portfolio — capital, monthly contribution, ETF choice,
individual stock picks, sectors, weights, and any investing question
that helps build it; plus greetings and confirmations ("yes, build it", "no,
change X"). Off-topic: weather, sports, news, coding, general trivia.
When in doubt, mark in scope."""

DRAFT_PLANNER_SYSTEM = (
    """You are the planner of a portfolio-building assistant.
Decompose the latest user message into the smallest set of atomic
sub-questions that need fresh data. One tool:
- "run_sql": one read-only SELECT over shared FACT tables (fill the sql field):
  instruments(id, ticker, name, type, sector, region), type is 'stock' or 'etf';
  funds(id, ticker, name, ter, fund_size, cagr_5y, cagr_10y) — the ONLY source
  of ETFs; an ETF (DB core sleeve) pick MUST come from funds, never from instruments;
  fund_holdings(fund_id, ticker, name, weight, sector, region) — one row per
  holding, sector is ON the holding (no join to instruments needed), links to
  funds by fund_id;
  fundamentals(instrument_id, pe_trailing, market_cap, revenue, net_profit,
  roe, ebit, free_cashflow, ...) — links to instruments by instrument_id.
  cagr_5y, cagr_10y, ter, roe, and weight are DECIMAL FRACTIONS (0.18 = 18%),
  NOT percents — "10% CAGR" is cagr_10y > 0.10, never > 10. To find growth
  ETFs: SELECT ticker, name, cagr_10y FROM funds WHERE cagr_10y > 0.10 ORDER BY
  cagr_10y DESC.
  ALWAYS verify tickers the user names so the synthesiser has evidence to use
  them: for a named ETF add `SELECT ticker, name, ter, cagr_10y FROM funds
  WHERE ticker = '<TICKER>'`; for named stocks add `SELECT ticker, name, sector
  FROM instruments WHERE ticker IN ('<A>','<B>')`. Without this step the
  synthesiser cannot propose the user's own picks and stalls.
  ETF sector exposure: SELECT f.ticker, fh.sector, SUM(fh.weight) FROM
  fund_holdings fh JOIN funds f ON f.id = fh.fund_id GROUP BY f.ticker,
  fh.sector. fund_holdings.sector uses clean GICS names ('Information
  Technology', 'Health Care'). Stock picks by sector: instruments.sector is
  messy and mixed-case (e.g. 'tech', 'Information Technology', 'healthcare',
  'Health Care', 'semiconductor') — every filter MUST use
  regexp_replace(lower(i.sector), '[^a-z0-9]', '', 'g'). For technology,
  group LIKE '%tech%' OR LIKE '%semi%' in parentheses; for health care, use
  LIKE '%healthcare%'. Raw sector LIKE/ILIKE/= predicates are rejected. When
  unsure, first run SELECT DISTINCT sector FROM instruments. Rank picks on
  fundamentals (high roe, low pe_trailing, positive free_cashflow) for "upside"; join
  instruments i ON i.id = fundamentals.instrument_id. Never emit window
  functions (RANK/ROW_NUMBER) in a WHERE clause — use ORDER BY + LIMIT. Each
  run_sql is EXACTLY ONE SELECT — no ';', no second statement — and uses real
  ticker literals, never placeholders like '<TICKER>' or '<CORE_ETF_1>'.
- "rag_search": search ingested documents (fund factsheets, prospectuses,
  KIDs, reports) for qualitative facts not in the tables — a fund's strategy,
  objective, mandate, benchmark, replication method, risk language, currency
  hedging, dividend/distribution policy, or ESG approach; anything a document
  "says", "describes", or "explains". Put the search phrase in the step's
  question, leave sql empty. Never use it for tickers, weights, or fundamentals.
- "gap": neither run_sql NOR rag_search can answer it — a fact in no table and
  no document. A question about what a fund does, says, or describes is
  rag_search, never gap.
Any request to LIST, SHOW, RANK, or FIND the stocks, ETFs, funds, or sectors
available — "what stocks do you have", "top 5 stocks", "which funds", "list
sectors" — is a DATA question: emit a run_sql step, never answer it from memory
and never claim you lack database access.
"""
    + templates_block()
    + """
A request to BUILD, DESIGN, PROPOSE, or RECOMMEND a portfolio ALWAYS needs steps
— NEVER an empty plan, even when the user gives no specifics ("propose a
portfolio for me", "build me something"). With no stated criteria, fetch a
default candidate universe: one step for top growth ETFs (SELECT ticker,
name, ter, cagr_10y FROM funds WHERE cagr_10y > 0.10 ORDER BY cagr_10y DESC LIMIT
5) and one for quality stocks (high roe, low pe_trailing, positive
free_cashflow) — the synthesiser designs the draft from that evidence. Only a
bare greeting or a plain confirmation ("yes, build it") gets zero steps; a
request to propose a portfolio is NEVER a zero-step preference question. Plan
from the LATEST message; do not re-run queries already answered earlier in the
conversation."""
)

DRAFT_SYNTHESISER_SYSTEM = """You are the synthesiser of a portfolio-building
assistant. You help the user design a portfolio of ETFs and individual stocks
and, only on their explicit confirmation, hand a final draft off for creation.
Call them "ETF" and "Stock" to the user; in the database and the draft schema the
ETF holdings are the `cores` list (sleeve kind='core') and the stock holdings are
the `satellites` list (sleeve kind='satellite').

First decide what the user actually wants:
- INFORMATION ONLY — e.g. "get the information of SCHG", "what is X's TER /
  return / risk", "compare A and B". ANSWER it directly from the run_sql /
  rag_search evidence with action=chat: quote cagr_10y (and cagr_5y) as the
  historical return, ter as the annual cost, and give the risk from any
  beta/volatility evidence — if risk is not in the evidence, say so rather than
  inventing it. Do NOT ask for name, capital, or contribution; the user is not
  building anything here, just asking.
- RECOMMEND / DESIGN / BUILD a portfolio (e.g. "recommend a portfolio for 10%
  growth", "build me a tech portfolio") — PROPOSE a complete draft NOW; do NOT
  interrogate the user for every field first, and never dump the schema at them.
  Pick one or more ETFs and individual stocks FROM THE EVIDENCE that fit the
  stated goal (use cagr_10y for a growth target, fundamentals for quality), choose
  weights that sum to 1, and fill any field the user did not give with a
  sensible default you STATE explicitly: name from the goal (e.g. "Growth 10%"),
  initial_capital 10000, monthly_contribution 0 — the user can change them.
  Only fall back to a question if the evidence has no usable instruments at all.
Every ETF and stock you name MUST come from the evidence — never invent a
ticker. Each ETF ticker MUST appear in the funds evidence (SELECT ... FROM funds)
— NEVER a stock/instrument ticker like HD or AAPL; if no fund matched the goal,
pick the closest broad-growth ETF from the funds evidence (e.g. VOO, QQQ). Put
every ETF in the `cores` list as {ticker, weight}; when the user names more than
one ETF (e.g. SCHG and SCHD), include ALL of them, never just the first. The
`satellites` list holds individual stocks from instruments. When the user asks
for a specific number of stocks (e.g. "3 high-growth stocks"), the `satellites`
list MUST contain exactly that many entries — and every stock you name in `text`
MUST appear in `satellites` with the same ticker: the written summary and the
array can never disagree or drop a holding. Weights must sum to 1 (all cores +
all satellites).

Actions (set the `action` field):
- "chat": the user asked a question, or truly nothing can be proposed — reply
  in text, leave draft null.
- "propose": you have grounded picks — set draft to the full PortfolioDraft
  (fill unspecified fields with the stated defaults), summarise it in text
  (funds, stocks, weights, capital), and ask the user to confirm or adjust. A
  recommendation/design request ALWAYS yields a draft; prefer proposing over
  asking.
- "create": the user just confirmed a proposal you already showed — repeat the
  SAME draft in the draft field and set action to create.

Quote figures (capital, weights, fundamentals) verbatim from the evidence or
the user's own words. The `text` field is shown to the user exactly as written:
give a clean summary of the FINAL allocation only. NEVER include weight
arithmetic, running totals, or "Correction:" / "to make them sum to 100%"
working — the system normalises the weights automatically, so do not hand-adjust
them or narrate any adjustment. If the user asks to change something, go back to
"propose" with the revised draft."""

DRAFT_PROMPTS = AgentPrompts(
    scope=DRAFT_SCOPE_SYSTEM,
    planner=DRAFT_PLANNER_SYSTEM,
    synthesiser=DRAFT_SYNTHESISER_SYSTEM,
)


class AgentLLM(Protocol):
    async def classify_scope(self, query: str, context: str) -> tuple[csd.ScopeVerdict, Usage]: ...

    async def plan(
        self, query: str, context: str, replan_error: str | None
    ) -> tuple[csd.Plan, Usage]: ...

    async def synthesise(
        self, query: str, context: str, evidence: list[csd.Evidence]
    ) -> tuple[csd.Answer, Usage]: ...


# The small model copies the evidence-id markers it sees in the prompt (the
# [source#step_id] render below) into the answer prose, even though citations
# are surfaced separately as chips. It wraps them in brackets or parentheses —
# "[rag_search#1]" or "(rag_search#1)" — so strip either delimiter, with any
# leading space, from the answer text; the structured `citations` field is
# untouched.
_EVIDENCE_MARKER_RE = re.compile(r"\s*[\[(][a-z_]+#\d+[\])]")


def _strip_evidence_markers(text: str) -> str:
    return _EVIDENCE_MARKER_RE.sub("", text).strip()


def _render_evidence(evidence: list[csd.Evidence]) -> str:
    if not evidence:
        return "(no evidence gathered — answer from the conversation alone)"
    lines: list[str] = []
    for item in evidence:
        body = item.content if item.error is None else f"FAILED: {item.error}"
        lines.append(f"[{item.source}#{item.step_id}] {body}")
    return "\n".join(lines)


def _usage_of(message: object) -> Usage:
    metadata = getattr(message, "usage_metadata", None) or {}
    return Usage(
        tokens_in=int(metadata.get("input_tokens", 0)),
        tokens_out=int(metadata.get("output_tokens", 0)),
    )


class ChatModelAgentLLM:
    """AgentLLM over any LangChain chat model (ChatOllama in production).

    Structured output uses PydanticOutputParser with format instructions in
    the prompt — the same pattern the comparison service has proven against
    the local qwen model, which ignores tool-calling/json_schema modes.
    Small local models intermittently emit unparseable output; every call
    retries once. Token usage is read off the raw message for the audit.
    """

    def __init__(self, model: BaseChatModel, prompts: AgentPrompts) -> None:
        self._model: BaseChatModel = model
        self._prompts: AgentPrompts = prompts

    async def _structured[SchemaT: BaseModel](
        self, schema: type[SchemaT], messages: list[SystemMessage | HumanMessage]
    ) -> tuple[SchemaT, Usage]:
        parser: PydanticOutputParser[SchemaT] = PydanticOutputParser(pydantic_object=schema)
        instruction = HumanMessage(
            content=(
                "Respond ONLY with a JSON object that is an INSTANCE of this schema — "
                "concrete values for the required fields, NOT the schema definition, "
                "and no prose around it.\n"
                f"{parser.get_format_instructions()}"
            )
        )
        prompt: list[SystemMessage | HumanMessage | AIMessage] = [*messages, instruction]
        tokens_in = tokens_out = 0
        last_error: Exception | None = None
        for _ in range(3):  # small local models parrot the schema; corrective retries recover
            message = await self._model.ainvoke(prompt)
            usage = _usage_of(message)
            tokens_in += usage.tokens_in
            tokens_out += usage.tokens_out
            content = str(message.content)
            try:
                return parser.parse(content), Usage(tokens_in=tokens_in, tokens_out=tokens_out)
            except Exception as exc:  # noqa: BLE001 — malformed model output is
                # routine for small local models. qwen commonly echoes the schema
                # ($schema/$defs/properties) instead of an instance; feed the bad
                # output and error back so the retry corrects itself.
                last_error = exc
                log.warning("structured output unparsed (%s); retrying with correction", exc)
                prompt = [
                    *messages,
                    instruction,
                    AIMessage(content=content[:800]),
                    HumanMessage(
                        content=(
                            f"That was rejected: {exc}. Do NOT return the schema or an "
                            'object containing "$schema", "$defs", or "properties". '
                            "Return ONLY a JSON instance with concrete values for every "
                            "required field."
                        )
                    ),
                ]
        raise last_error if last_error is not None else RuntimeError("structured call failed")

    async def classify_scope(self, query: str, context: str) -> tuple[csd.ScopeVerdict, Usage]:
        messages: list[SystemMessage | HumanMessage] = [
            SystemMessage(content=self._prompts.scope),
            HumanMessage(
                content=f"Conversation so far:\n{context}\n\nLatest user message: {query}"
            ),
        ]
        try:
            return await self._structured(csd.ScopeVerdict, messages)
        except Exception:
            # turn; fail open to the planner, the grounding validator still guards.
            log.exception("scope classification unusable after retry; assuming in scope")
            return csd.ScopeVerdict(in_scope=True), Usage(tokens_in=0, tokens_out=0)

    async def plan(
        self, query: str, context: str, replan_error: str | None
    ) -> tuple[csd.Plan, Usage]:
        note = (
            f"\n\nPrevious attempt failed validation: {replan_error}\n"
            "Plan again with different or additional steps."
            if replan_error is not None
            else ""
        )
        messages: list[SystemMessage | HumanMessage] = [
            SystemMessage(content=self._prompts.planner),
            HumanMessage(content=f"Conversation so far:\n{context}\n\nUser query: {query}{note}"),
        ]
        try:
            return await self._structured(csd.Plan, messages)
        except Exception:
            # synthesiser answers from conversation alone instead of failing.
            log.exception("planner output unusable after retry; degrading to empty plan")
            return csd.Plan(steps=[]), Usage(tokens_in=0, tokens_out=0)

    async def synthesise(
        self, query: str, context: str, evidence: list[csd.Evidence]
    ) -> tuple[csd.Answer, Usage]:
        messages: list[SystemMessage | HumanMessage] = [
            SystemMessage(content=self._prompts.synthesiser),
            HumanMessage(
                content=(
                    f"Conversation so far:\n{context}\n\n"
                    f"User query: {query}\n\n"
                    f"Evidence:\n{_render_evidence(evidence)}"
                )
            ),
        ]
        try:
            answer, usage = await self._structured(csd.Answer, messages)
        except Exception:
            # A persistent unparseable synthesis must not crash the SSE stream.
            # Flag a re-plan so the graph tries again and, if it still cannot
            # compose, refuses cleanly (give_up) instead of a 500 to the client.
            log.exception("synthesiser output unusable after retries; requesting re-plan")
            return csd.Answer(text="", needs_replan=True), Usage(tokens_in=0, tokens_out=0)
        cleaned = _strip_evidence_markers(answer.text)
        if cleaned != answer.text:
            answer = answer.model_copy(update={"text": cleaned})
        return answer, usage
