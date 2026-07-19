"""Portfolio draft agent: stateless chat that proposes and, on confirmation,
creates a portfolio through the existing service path.

No portfolio exists yet, so there is no RLS scope, no persisted history, and
no audit row — the conversation lives in the client and is echoed back per
request. The only write is portfolio creation, and it goes through
PortfolioService.create with the user-confirmed draft, never SQL the LLM wrote.
"""

import json
import logging
from collections.abc import AsyncIterator
from typing import Protocol

from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from coresat.domain.agent import DraftPosition, PortfolioDraft, ToolName
from coresat.domain.draft import ChatTurn
from coresat.domain.portfolio import CorePick, PortfolioCreate, SatellitePick
from coresat.services.agent.agent import (
    AnswerReady,
    EvidenceGathered,
    GroundedAgent,
    PlanEmitted,
)
from coresat.services.agent.tools import FactSqlTool, Tool
from coresat.services.portfolios import UnknownTickerError

log = logging.getLogger(__name__)

_WEIGHT_TOLERANCE = 0.01


class PortfolioCreator(Protocol):
    async def create(self, spec: PortfolioCreate) -> int: ...


def _sse(event: str, payload: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


def _render_context(history: list[ChatTurn]) -> str:
    if not history:
        return "(new conversation)"
    return "\n".join(f"{turn.role}: {turn.content}" for turn in history)


def _normalize_draft(draft: PortfolioDraft) -> PortfolioDraft:
    # A small model's proposed weights often miss summing to 1 (e.g. 1.06). Scale
    # core + satellites so they sum to 1 before the user sees or builds the draft,
    # so a good recommendation is never rejected by the create weight check.
    total = draft.core_weight + sum(position.weight for position in draft.satellites)
    if total <= 0 or abs(total - 1.0) <= _WEIGHT_TOLERANCE:
        return draft
    return draft.model_copy(
        update={
            "core_weight": draft.core_weight / total,
            "satellites": [
                position.model_copy(update={"weight": position.weight / total})
                for position in draft.satellites
            ],
        }
    )


def _draft_to_spec(draft: PortfolioDraft) -> PortfolioCreate:
    return PortfolioCreate(
        name=draft.name,
        initial_capital=draft.initial_capital,
        monthly_contribution=draft.monthly_contribution,
        core=CorePick(fund_ticker=draft.core_fund_ticker, weight=draft.core_weight),
        satellites=[
            SatellitePick(ticker=position.ticker, weight=position.weight, acquired_at=None)
            for position in draft.satellites
        ],
    )


class DraftService:
    def __init__(
        self,
        engine: AsyncEngine,
        agent: GroundedAgent,
        portfolios: PortfolioCreator,
        rag_tool: Tool,
    ) -> None:
        self._engine: AsyncEngine = engine
        self._agent: GroundedAgent = agent
        self._portfolios: PortfolioCreator = portfolios
        self._rag_tool: Tool = rag_tool

    async def stream_chat(
        self,
        message: str,
        history: list[ChatTurn],
        proposed_draft: PortfolioDraft | None,
        confirm: bool,
    ) -> AsyncIterator[str]:
        # Explicit user confirmation of a shown proposal → create deterministically,
        # no LLM turn. The model designs the portfolio; the user's click builds it.
        if confirm and proposed_draft is not None:
            async for chunk in self._create(proposed_draft):
                yield chunk
            return
        context = _render_context(history)
        tools: dict[ToolName, Tool] = {
            ToolName.RUN_SQL: FactSqlTool(engine=self._engine),
            ToolName.RAG_SEARCH: self._rag_tool,
        }
        answer = None
        try:
            async for event in self._agent.run(message, context, tools):
                if isinstance(event, PlanEmitted):
                    yield _sse("plan", {"steps": [step.model_dump() for step in event.plan.steps]})
                elif isinstance(event, EvidenceGathered):
                    yield _sse(
                        "evidence", {"items": [item.model_dump() for item in event.evidence]}
                    )
                elif isinstance(event, AnswerReady):
                    answer = event.answer
        except Exception:
            # reach the client as a typed event, never a half-closed response.
            log.exception("draft agent graph failed")
            yield _sse("error", {"message": "the assistant failed to process this message"})
            return
        if answer is None:
            yield _sse("error", {"message": "assistant produced no answer"})
            return

        # Create only on an explicit confirmation of a proposal the client was
        # actually shown, and build from THAT draft — not the LLM's echo — so
        # the model can trigger the action but never mutate the payload.
        if answer.action == "create" and proposed_draft is not None:
            async for chunk in self._create(proposed_draft):
                yield chunk
            return

        draft: PortfolioDraft | None = None
        note = ""
        if answer.draft is not None:
            resolved, resolve_note = await self._resolve_draft(answer.draft)
            if resolved is not None:
                draft = _normalize_draft(resolved)
            if resolve_note is not None:
                note = f" ({resolve_note})"
        payload: dict[str, object] = {
            "text": answer.text + note,
            "action": "propose" if draft is not None else "chat",
            "draft": draft.model_dump() if draft is not None else None,
        }
        yield _sse("answer", payload)

    async def _resolve_draft(
        self, draft: PortfolioDraft
    ) -> tuple[PortfolioDraft | None, str | None]:
        # The model often names a ticker that is not exactly in the DB — a
        # dropped exchange suffix (CSPX for CSPX.L) or a stock as the core (HD).
        # Resolve the core against funds and each satellite against instruments
        # (exact, else the same base plus an exchange suffix, else company name).
        # Unresolved satellites are excluded with a note; if that leaves none —
        # or the core cannot be resolved to a real fund — don't propose a broken
        # draft (a lone core rescaled to 100% is not what the user asked for),
        # fall back to chat with the reason.
        async with self._engine.connect() as conn:
            core = (
                await conn.execute(
                    text(
                        "SELECT ticker FROM funds WHERE upper(ticker) = upper(:t) "
                        "OR upper(ticker) LIKE upper(:t) || '.%' "
                        "ORDER BY (upper(ticker) = upper(:t)) DESC LIMIT 1"
                    ),
                    {"t": draft.core_fund_ticker},
                )
            ).scalar()
            if core is None:
                return None, f"no ETF in the database matches the core '{draft.core_fund_ticker}'"
            satellites: list[DraftPosition] = []
            dropped: list[str] = []
            for position in draft.satellites:
                resolved = (
                    await conn.execute(
                        text(
                            "SELECT ticker FROM instruments WHERE type = 'stock' AND "
                            "(upper(ticker) = upper(:t) OR upper(ticker) LIKE upper(:t) || '.%' "
                            "OR upper(name) = upper(:t) OR upper(name) LIKE upper(:t) || '%') "
                            "ORDER BY (upper(ticker) = upper(:t)) DESC, "
                            "(upper(name) = upper(:t)) DESC LIMIT 1"
                        ),
                        {"t": position.ticker},
                    )
                ).scalar()
                if resolved is not None:
                    satellites.append(position.model_copy(update={"ticker": resolved}))
                else:
                    dropped.append(position.ticker)
        if draft.satellites and not satellites:
            return None, (
                "could not match any requested holdings to tradable stocks: "
                + ", ".join(dropped)
                + " — please use exact tickers"
            )
        note = (
            "excluded holdings not found as tradable stocks: " + ", ".join(dropped)
            if dropped
            else None
        )
        return (
            draft.model_copy(update={"core_fund_ticker": core, "satellites": satellites}),
            note,
        )

    async def _create(self, draft: PortfolioDraft) -> AsyncIterator[str]:
        total = draft.core_weight + sum(position.weight for position in draft.satellites)
        if abs(total - 1.0) > _WEIGHT_TOLERANCE:
            yield _sse(
                "error",
                {"message": f"weights must sum to 1 (core + satellites = {total:.3f})"},
            )
            return
        try:
            spec = _draft_to_spec(draft)
        except ValidationError as error:
            yield _sse("error", {"message": f"draft is invalid: {error.errors()[0]['msg']}"})
            return
        try:
            portfolio_id = await self._portfolios.create(spec)
        except UnknownTickerError as error:
            yield _sse("error", {"message": str(error)})
            return
        yield _sse("created", {"portfolio_id": portfolio_id, "name": draft.name})
