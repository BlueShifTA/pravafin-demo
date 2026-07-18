"""Copilot orchestration: run the graph, stream SSE, persist chat and audit.

Every request builds its own tools bound to the request's portfolio — the
RLS-scoped connection is the isolation boundary, so a prompt-injected SQL
step still cannot read another portfolio.
"""

import json
import logging
import uuid
from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from coresat.db.session import portfolio_scope
from coresat.domain.agent import Answer, Evidence, ToolName
from coresat.domain.chat import AuditEntry, ChatMessageOut, Citation
from coresat.services.agent.agent import (
    AnswerReady,
    EvidenceGathered,
    GroundedAgent,
    PlanEmitted,
)
from coresat.services.agent.graph import CANNOT_ANSWER_TEXT, OFF_TOPIC_TEXT, NodeUsage
from coresat.services.agent.tools import (
    GetProjectionTool,
    RunSqlTool,
    SummaryProvider,
    Tool,
)

log = logging.getLogger(__name__)

_CONTEXT_MESSAGES = 10


class PortfolioNotFoundError(ValueError):
    """Chat addressed to a portfolio that does not exist."""


def _sse(event: str, payload: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


def _citations_of(answer: Answer, evidence: list[Evidence]) -> list[Citation]:
    bodies = {f"{item.source}#{item.step_id}": item.content for item in evidence}
    return [
        Citation(id=citation_id, content=bodies[citation_id])
        for citation_id in answer.citations
        if citation_id in bodies
    ]


class CopilotService:
    def __init__(
        self,
        engine: AsyncEngine,
        agent: GroundedAgent,
        summaries: SummaryProvider,
        rag_tool: Tool,
        model_name: str,
    ) -> None:
        self._engine: AsyncEngine = engine
        self._agent: GroundedAgent = agent
        self._summaries: SummaryProvider = summaries
        self._rag_tool: Tool = rag_tool
        self.model_name: str = model_name

    async def history(self, portfolio_id: int) -> list[ChatMessageOut]:
        async with portfolio_scope(self._engine, portfolio_id) as conn:
            rows = (
                (
                    await conn.execute(
                        text(
                            "SELECT id, role, content, citations, tokens_in, tokens_out, "
                            "created_at FROM chat_messages ORDER BY id"
                        )
                    )
                )
                .mappings()
                .all()
            )
        return [
            ChatMessageOut(
                id=row["id"],
                role=row["role"],
                content=row["content"],
                citations=[Citation(**entry) for entry in row["citations"]],
                tokens_in=row["tokens_in"],
                tokens_out=row["tokens_out"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    async def audit(self, portfolio_id: int) -> list[AuditEntry]:
        async with portfolio_scope(self._engine, portfolio_id) as conn:
            rows = (
                (
                    await conn.execute(
                        text(
                            "SELECT id, feature, model, node, graph_run_id, tokens_in, "
                            "tokens_out, created_at FROM llm_audit_log ORDER BY id"
                        )
                    )
                )
                .mappings()
                .all()
            )
        return [AuditEntry(**dict(row)) for row in rows]

    async def clear_history(self, portfolio_id: int) -> None:
        async with portfolio_scope(self._engine, portfolio_id) as conn:
            await conn.execute(text("DELETE FROM chat_messages"))

    async def record_user_message(self, portfolio_id: int, message: str) -> None:
        try:
            async with portfolio_scope(self._engine, portfolio_id) as conn:
                await conn.execute(
                    text(
                        "INSERT INTO chat_messages (portfolio_id, role, content) "
                        "VALUES (:pid, 'user', :content)"
                    ),
                    {"pid": portfolio_id, "content": message},
                )
        except IntegrityError as error:
            raise PortfolioNotFoundError(f"portfolio {portfolio_id} not found") from error

    async def stream_chat(self, portfolio_id: int, message: str) -> AsyncIterator[str]:
        context = self._render_context(await self.history(portfolio_id))
        tools: dict[ToolName, Tool] = {
            ToolName.RUN_SQL: RunSqlTool(engine=self._engine, portfolio_id=portfolio_id),
            ToolName.GET_PROJECTION: GetProjectionTool(
                summaries=self._summaries, portfolio_id=portfolio_id
            ),
            ToolName.RAG_SEARCH: self._rag_tool,
        }
        answer: Answer | None = None
        evidence: list[Evidence] = []
        usage: list[NodeUsage] = []
        try:
            async for event in self._agent.run(message, context, tools):
                if isinstance(event, PlanEmitted):
                    yield _sse("plan", {"steps": [step.model_dump() for step in event.plan.steps]})
                elif isinstance(event, EvidenceGathered):
                    evidence = event.evidence
                    yield _sse("evidence", {"items": [item.model_dump() for item in evidence]})
                elif isinstance(event, AnswerReady):
                    answer = event.answer
                    evidence = event.evidence
                    usage = event.usage
        except Exception:
            # reach the client as a typed event, never a half-closed response.
            log.exception("copilot graph failed for portfolio %d", portfolio_id)
            yield _sse("error", {"message": "the copilot failed to process this question"})
            return
        if answer is None:  # a graph bug, not a user error — surface loudly
            yield _sse("error", {"message": "agent produced no answer"})
            return
        citations = _citations_of(answer, evidence)
        tokens_in = sum(entry["tokens_in"] for entry in usage)
        tokens_out = sum(entry["tokens_out"] for entry in usage)
        stored = await self._persist_turn(
            portfolio_id, answer, citations, tokens_in, tokens_out, usage
        )
        yield _sse("answer", {"message": stored.model_dump(mode="json")})

    def _render_context(self, messages: list[ChatMessageOut]) -> str:
        # canned texts stay visible in the UI history but never reach the
        # model again — a small model treats a past "Hi → refusal" pair as
        # precedent and keeps refusing (context poisoning)
        canned = {OFF_TOPIC_TEXT, CANNOT_ANSWER_TEXT}
        informative = [entry for entry in messages if entry.content not in canned]
        recent = informative[-_CONTEXT_MESSAGES:]
        if not recent:
            return "(new conversation)"
        return "\n".join(f"{entry.role}: {entry.content}" for entry in recent)

    async def _persist_turn(
        self,
        portfolio_id: int,
        answer: Answer,
        citations: list[Citation],
        tokens_in: int,
        tokens_out: int,
        usage: list[NodeUsage],
    ) -> ChatMessageOut:
        graph_run_id = uuid.uuid4().hex
        async with portfolio_scope(self._engine, portfolio_id) as conn:
            row = (
                await conn.execute(
                    text(
                        "INSERT INTO chat_messages (portfolio_id, role, content, citations, "
                        "tokens_in, tokens_out) VALUES (:pid, 'assistant', :content, "
                        "CAST(:citations AS jsonb), :tokens_in, :tokens_out) "
                        "RETURNING id, created_at"
                    ),
                    {
                        "pid": portfolio_id,
                        "content": answer.text,
                        "citations": json.dumps([c.model_dump() for c in citations]),
                        "tokens_in": tokens_in,
                        "tokens_out": tokens_out,
                    },
                )
            ).one()
            for entry in usage:
                await conn.execute(
                    text(
                        "INSERT INTO llm_audit_log (portfolio_id, feature, model, node, "
                        "graph_run_id, tokens_in, tokens_out) VALUES (:pid, 'copilot', "
                        ":model, :node, :run_id, :tokens_in, :tokens_out)"
                    ),
                    {
                        "pid": portfolio_id,
                        "model": self.model_name,
                        "node": entry["node"],
                        "run_id": graph_run_id,
                        "tokens_in": entry["tokens_in"],
                        "tokens_out": entry["tokens_out"],
                    },
                )
        return ChatMessageOut(
            id=row.id,
            role="assistant",
            content=answer.text,
            citations=citations,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            created_at=row.created_at,
        )
