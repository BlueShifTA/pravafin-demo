"""Tool boundary consumed by the executor, and the CoreSat concretions.

run_sql executes planner-written SQL on the request's RLS-scoped connection
inside a READ ONLY transaction with a statement timeout — the database, not
prompt text, enforces isolation and read-only-ness. get_projection returns
deterministic analytics output; the LLM never computes a number.
"""

from decimal import Decimal
from typing import Protocol

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from coresat.db.session import portfolio_scope
from coresat.domain.agent import Evidence, Step
from coresat.domain.portfolio import PortfolioSummary
from coresat.services.grounding import six_significant_figures

_MAX_ROWS = 50
_STATEMENT_TIMEOUT_MS = 5000


class Tool(Protocol):
    async def run(self, step: Step) -> Evidence: ...


def _render_sql_value(value: object) -> object:
    # aggregate results carry numeric noise (SUM of numeric → 40-digit
    # Decimals); round to 6 significant figures so the synthesiser quotes a
    # human-readable figure and the grounding validator sees the same one
    if isinstance(value, (Decimal, float)) and value == value:  # NaN-safe
        return format(six_significant_figures(Decimal(str(value)).normalize()), "f")
    return value


class SummaryProvider(Protocol):
    async def summary(self, portfolio_id: int) -> PortfolioSummary | None: ...


class RunSqlTool:
    def __init__(self, engine: AsyncEngine, portfolio_id: int) -> None:
        self._engine: AsyncEngine = engine
        self._portfolio_id: int = portfolio_id

    async def run(self, step: Step) -> Evidence:
        if step.sql is None or not step.sql.strip():
            return Evidence(
                step_id=step.id, source="run_sql", content="", error="step carries no SQL"
            )
        try:
            async with portfolio_scope(self._engine, self._portfolio_id) as conn:
                await conn.execute(text("SET LOCAL transaction_read_only = on"))
                await conn.execute(text(f"SET LOCAL statement_timeout = {_STATEMENT_TIMEOUT_MS}"))
                result = await conn.execute(text(step.sql))
                rows = result.mappings().fetchmany(_MAX_ROWS)
                truncated = result.fetchone() is not None
        except (DBAPIError, SQLAlchemyError) as exc:
            cause = getattr(exc, "orig", None) or exc
            return Evidence(
                step_id=step.id, source="run_sql", content="", error=f"SQL failed: {cause}"
            )
        lines = [
            ", ".join(f"{key}={_render_sql_value(value)}" for key, value in row.items())
            for row in rows
        ]
        if not lines:
            lines = ["(no rows)"]
        if truncated:
            lines.append(f"(truncated to first {_MAX_ROWS} rows)")
        return Evidence(step_id=step.id, source="run_sql", content="\n".join(lines), error=None)


class GetProjectionTool:
    def __init__(self, summaries: SummaryProvider, portfolio_id: int) -> None:
        self._summaries: SummaryProvider = summaries
        self._portfolio_id: int = portfolio_id

    async def run(self, step: Step) -> Evidence:
        summary = await self._summaries.summary(self._portfolio_id)
        if summary is None:
            return Evidence(
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
        return Evidence(
            step_id=step.id, source="get_projection", content="\n".join(lines), error=None
        )
