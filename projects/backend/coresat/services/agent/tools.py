"""Tool boundary consumed by the executor, and the CoreSat concretions.

run_sql executes planner-written SQL on the request's RLS-scoped connection
inside a READ ONLY transaction with a statement timeout — the database, not
prompt text, enforces isolation and read-only-ness. get_projection returns
deterministic analytics output; the LLM never computes a number.
"""

import logging
import re
from collections.abc import Sequence
from decimal import Decimal
from typing import Protocol

from sqlalchemy import RowMapping, text
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

import coresat.db as csdb
import coresat.domain as csd
from coresat.services.agent.retrieval import Retriever
from coresat.services.grounding import six_significant_figures

log = logging.getLogger(__name__)

_MAX_ROWS = 50
_STATEMENT_TIMEOUT_MS = 5000


# The planner LLM (esp. a small/cheap model) drifts in three deterministic ways
# a DB round-trip should not have to catch: it wraps SQL in ```sql fences, emits
# two statements separated by ';' (asyncpg rejects multiple commands in one
# prepared statement), and leaves placeholder tokens like '<TICKER>'. Clean the
# first two and reject the third with a clear message the retry loop feeds back.
_PLACEHOLDER_RE = re.compile(r"<[A-Za-z0-9_ ]+>")


def _prepare_sql(raw: str | None) -> tuple[str | None, str | None]:
    """Return (clean_single_statement_sql, None) or (None, error message)."""
    if raw is None or not raw.strip():
        return None, "step carries no SQL"
    sql = raw.strip()
    if sql.startswith("```"):
        sql = sql.strip("`").strip()
        if sql[:3].lower() == "sql":
            sql = sql[3:].strip()
    # keep only the first statement — a trailing ';' or a second SELECT would
    # otherwise fail as "cannot insert multiple commands into a prepared statement"
    sql = sql.split(";", 1)[0].strip()
    if not sql:
        return None, "step carries no SQL"
    if _PLACEHOLDER_RE.search(sql):
        return None, "SQL still has placeholder tokens like '<TICKER>' — use real values"
    return sql, None


class Tool(Protocol):
    async def run(self, step: csd.Step) -> csd.Evidence: ...


def _render_sql_value(value: object) -> object:
    # aggregate results carry numeric noise (SUM of numeric → 40-digit
    # Decimals); round to 6 significant figures so the synthesiser quotes a
    # human-readable figure and the grounding validator sees the same one
    if isinstance(value, (Decimal, float)) and value == value:  # NaN-safe
        return format(six_significant_figures(Decimal(str(value)).normalize()), "f")
    return value


class SummaryProvider(Protocol):
    async def summary(self, portfolio_id: int) -> csd.PortfolioSummary | None: ...


def _rows_to_content(rows: Sequence[RowMapping], truncated: bool) -> str:
    lines = [
        ", ".join(f"{key}={_render_sql_value(value)}" for key, value in row.items()) for row in rows
    ]
    if not lines:
        lines = ["(no rows)"]
    if truncated:
        lines.append(f"(truncated to first {_MAX_ROWS} rows)")
    return "\n".join(lines)


class RunSqlTool:
    def __init__(self, engine: AsyncEngine, portfolio_id: int) -> None:
        self._engine: AsyncEngine = engine
        self._portfolio_id: int = portfolio_id

    async def run(self, step: csd.Step) -> csd.Evidence:
        sql, error = _prepare_sql(step.sql)
        if sql is None:
            return csd.Evidence(step_id=step.id, source="run_sql", content="", error=error)
        log.info("run_sql (portfolio %d): %s", self._portfolio_id, sql)
        try:
            async with csdb.portfolio_scope(self._engine, self._portfolio_id) as conn:
                await conn.execute(text("SET LOCAL transaction_read_only = on"))
                await conn.execute(text(f"SET LOCAL statement_timeout = {_STATEMENT_TIMEOUT_MS}"))
                result = await conn.execute(text(sql))
                rows = result.mappings().fetchmany(_MAX_ROWS)
                truncated = result.fetchone() is not None
        except (DBAPIError, SQLAlchemyError) as exc:
            cause = getattr(exc, "orig", None) or exc
            log.warning("run_sql failed: %s | sql=%s", cause, sql)
            return csd.Evidence(
                step_id=step.id, source="run_sql", content="", error=f"SQL failed: {cause}"
            )
        return csd.Evidence(
            step_id=step.id, source="run_sql", content=_rows_to_content(rows, truncated), error=None
        )


class FactSqlTool:
    """run_sql for pre-creation agents: fact tables only, no portfolio scope.

    Runs without SET LOCAL app.portfolio_id, so RLS policies on portfolio
    tables return zero rows — the draft agent physically cannot read any
    existing portfolio's data. Fact tables (funds, instruments, fundamentals,
    prices) are read-all and remain visible. Same READ ONLY + timeout guards.
    """

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine: AsyncEngine = engine

    async def run(self, step: csd.Step) -> csd.Evidence:
        sql, error = _prepare_sql(step.sql)
        if sql is None:
            return csd.Evidence(step_id=step.id, source="run_sql", content="", error=error)
        log.info("run_sql (facts): %s", sql)
        try:
            async with self._engine.connect() as conn, conn.begin():
                await conn.execute(text("SET LOCAL transaction_read_only = on"))
                await conn.execute(text(f"SET LOCAL statement_timeout = {_STATEMENT_TIMEOUT_MS}"))
                result = await conn.execute(text(sql))
                rows = result.mappings().fetchmany(_MAX_ROWS)
                truncated = result.fetchone() is not None
        except (DBAPIError, SQLAlchemyError) as exc:
            cause = getattr(exc, "orig", None) or exc
            log.warning("run_sql failed: %s | sql=%s", cause, sql)
            return csd.Evidence(
                step_id=step.id, source="run_sql", content="", error=f"SQL failed: {cause}"
            )
        return csd.Evidence(
            step_id=step.id, source="run_sql", content=_rows_to_content(rows, truncated), error=None
        )


def _chunk_line(chunk: csd.RetrievedChunk) -> str:
    where = f"{chunk.source_doc} p.{chunk.page}" if chunk.page is not None else chunk.source_doc
    return f"[{where}] {chunk.text}"


class RagSearchTool:
    """Retrieves ingested-document chunks for the step's question.

    Deterministic (embed → hybrid search → rerank, no LLM). Chunks are rendered
    with source_doc + page so the synthesiser can cite them; an empty result is
    reported as a normal 'no documents' evidence, never an error.
    """

    def __init__(self, retriever: Retriever, k: int) -> None:
        self._retriever: Retriever = retriever
        self._k: int = k

    async def run(self, step: csd.Step) -> csd.Evidence:
        chunks = await self._retriever.retrieve(step.question, self._k)
        content = (
            "\n".join(_chunk_line(chunk) for chunk in chunks)
            if chunks
            else "(no matching documents)"
        )
        return csd.Evidence(step_id=step.id, source="rag_search", content=content, error=None)


class GetProjectionTool:
    def __init__(self, summaries: SummaryProvider, portfolio_id: int) -> None:
        self._summaries: SummaryProvider = summaries
        self._portfolio_id: int = portfolio_id

    async def run(self, step: csd.Step) -> csd.Evidence:
        summary = await self._summaries.summary(self._portfolio_id)
        if summary is None:
            return csd.Evidence(
                step_id=step.id,
                source="get_projection",
                content="",
                error="portfolio not found or has no positions",
            )
        lines = [
            f"portfolio={summary.name}",
            f"initial_capital={summary.initial_capital:.2f}",
            f"monthly_contribution={summary.monthly_contribution:.2f}",
            f"invested_total={summary.invested_total:.2f}",
            f"current_value={summary.current_value:.2f}",
        ]
        for projection in summary.projections:
            lines.append(
                f"projection_{projection.years}y: expected={projection.expected:.2f}, "
                f"low={projection.low:.2f}, high={projection.high:.2f}, "
                f"annual_rate={projection.annual_rate * 100:.2f}%"
            )
        return csd.Evidence(
            step_id=step.id, source="get_projection", content="\n".join(lines), error=None
        )
