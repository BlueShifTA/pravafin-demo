"""LLM boundary: AgentLLM protocol and the LangChain chat-model concretion.

The three LLM-calling nodes of the copilot graph (scope guard, planner,
synthesiser) go through this boundary; everything else in the graph is
deterministic code. Every call reports token usage for the per-node audit.
"""

import logging
from typing import NamedTuple, Protocol

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel

from coresat.domain.agent import Answer, Evidence, Plan, ScopeVerdict

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

PLANNER_SYSTEM = """You are the planner of a portfolio-manager copilot.
Decompose the user query into the smallest set of atomic sub-questions.
Assign each sub-question exactly one tool:
- "run_sql": read data with one SELECT statement (fill the step's sql field).
  Fact tables: instruments(id, ticker, name, type, sector, region, currency),
  prices_daily(instrument_id, date, open, high, low, close, volume),
  funds(id, ticker, name, ter, fund_size), fund_holdings,
  fundamentals(instrument_id, pe_trailing, market_cap, revenue, net_profit,
  roe, ...), financials_yearly.
  Portfolio tables (already filtered to the user's portfolio): portfolios,
  sleeves(id, kind, target_weight), positions(sleeve_id, instrument_id,
  fund_id, target_weight, invested_amount).
  Joins: positions.instrument_id = instruments.id (stocks),
  positions.fund_id = funds.id (ETFs), positions.sleeve_id = sleeves.id.
- "get_projection": the portfolio's current value, invested total, and 10/20y
  growth projection. Use it for "what is my portfolio worth", "current value",
  "how will it grow", "prospects".
- "gap": no tool can answer this; flag it instead of guessing.
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

SYNTHESISER_SYSTEM = """You are the synthesiser of a portfolio-manager copilot.
Combine the evidence into one answer to the user query.
Rules:
- Quote every figure VERBATIM as it appears in the evidence — never compute,
  convert, round, or abbreviate numbers.
- Cite every factual claim by listing the evidence ids (e.g. "run_sql#1") in
  citations.
- List sub-questions nothing could answer in gaps; never invent facts.
- When no evidence was gathered, answer directly from the conversation:
  greet back, explain where an earlier answer came from, or ask what the
  user wants to know about their portfolio. Never mention missing evidence
  for greetings or small talk.
- Set needs_replan=true only when the evidence shows the plan missed the
  actual question; otherwise false."""


class Usage(NamedTuple):
    tokens_in: int
    tokens_out: int


class AgentLLM(Protocol):
    async def classify_scope(self, query: str, context: str) -> tuple[ScopeVerdict, Usage]: ...

    async def plan(
        self, query: str, context: str, replan_error: str | None
    ) -> tuple[Plan, Usage]: ...

    async def synthesise(
        self, query: str, context: str, evidence: list[Evidence]
    ) -> tuple[Answer, Usage]: ...


def _render_evidence(evidence: list[Evidence]) -> str:
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

    def __init__(self, model: BaseChatModel) -> None:
        self._model: BaseChatModel = model

    async def _structured[SchemaT: BaseModel](
        self, schema: type[SchemaT], messages: list[SystemMessage | HumanMessage]
    ) -> tuple[SchemaT, Usage]:
        parser: PydanticOutputParser[SchemaT] = PydanticOutputParser(pydantic_object=schema)
        prompt = [
            *messages,
            HumanMessage(
                content=(
                    "Respond ONLY with JSON matching this schema — no prose around it.\n"
                    f"{parser.get_format_instructions()}"
                )
            ),
        ]
        tokens_in = tokens_out = 0
        last_error: Exception | None = None
        for _ in range(2):  # one retry on malformed output
            message = await self._model.ainvoke(prompt)
            usage = _usage_of(message)
            tokens_in += usage.tokens_in
            tokens_out += usage.tokens_out
            try:
                return parser.parse(str(message.content)), Usage(
                    tokens_in=tokens_in, tokens_out=tokens_out
                )
            except Exception as exc:  # noqa: BLE001 — malformed model output is
                # routine for small local models; one retry recovers most cases.
                last_error = exc
                log.warning("structured output unparsed (%s); retrying", exc)
        raise last_error if last_error is not None else RuntimeError("structured call failed")

    async def classify_scope(self, query: str, context: str) -> tuple[ScopeVerdict, Usage]:
        messages: list[SystemMessage | HumanMessage] = [
            SystemMessage(content=SCOPE_SYSTEM),
            HumanMessage(
                content=f"Conversation so far:\n{context}\n\nLatest user message: {query}"
            ),
        ]
        try:
            return await self._structured(ScopeVerdict, messages)
        except Exception:
            # turn; fail open to the planner, the grounding validator still guards.
            log.exception("scope classification unusable after retry; assuming in scope")
            return ScopeVerdict(in_scope=True), Usage(tokens_in=0, tokens_out=0)

    async def plan(self, query: str, context: str, replan_error: str | None) -> tuple[Plan, Usage]:
        note = (
            f"\n\nPrevious attempt failed validation: {replan_error}\n"
            "Plan again with different or additional steps."
            if replan_error is not None
            else ""
        )
        messages: list[SystemMessage | HumanMessage] = [
            SystemMessage(content=PLANNER_SYSTEM),
            HumanMessage(content=f"Conversation so far:\n{context}\n\nUser query: {query}{note}"),
        ]
        try:
            return await self._structured(Plan, messages)
        except Exception:
            # synthesiser answers from conversation alone instead of failing.
            log.exception("planner output unusable after retry; degrading to empty plan")
            return Plan(steps=[]), Usage(tokens_in=0, tokens_out=0)

    async def synthesise(
        self, query: str, context: str, evidence: list[Evidence]
    ) -> tuple[Answer, Usage]:
        messages: list[SystemMessage | HumanMessage] = [
            SystemMessage(content=SYNTHESISER_SYSTEM),
            HumanMessage(
                content=(
                    f"Conversation so far:\n{context}\n\n"
                    f"User query: {query}\n\n"
                    f"Evidence:\n{_render_evidence(evidence)}"
                )
            ),
        ]
        return await self._structured(Answer, messages)
