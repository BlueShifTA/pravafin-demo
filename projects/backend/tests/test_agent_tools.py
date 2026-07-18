"""Agent tools: read-only RLS-scoped SQL and deterministic projections.

SQL tests auto-skip when Postgres is down (`just stack-up` to run).
"""

from collections.abc import AsyncIterator

import asyncpg
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from coresat.db.schema import apply_schema
from coresat.db.session import create_engine
from coresat.domain.agent import Step, ToolName
from coresat.domain.portfolio import PortfolioHealth, PortfolioSummary, ProjectionOut
from coresat.services.agent.tools import GetProjectionTool, RunSqlTool

ADMIN_DSN = "postgresql://postgres:postgres@localhost:5434/coresat_test"
APP_URL = "postgresql+asyncpg://coresat_app:coresat_app@localhost:5434/coresat_test"


async def _admin_or_skip() -> asyncpg.Connection:
    try:
        return await asyncpg.connect(ADMIN_DSN, timeout=3)
    except OSError, asyncpg.PostgresError, TimeoutError:
        pytest.skip("postgres not running — just stack-up")


@pytest.fixture
async def seeded_portfolios() -> AsyncIterator[tuple[int, int]]:
    admin = await _admin_or_skip()
    await apply_schema(ADMIN_DSN)
    await admin.execute(
        "TRUNCATE chat_messages, positions, sleeves, llm_audit_log, portfolios "
        "RESTART IDENTITY CASCADE"
    )
    inst = await admin.fetchval(
        "INSERT INTO instruments (ticker, name, type) VALUES ('TSTX', 'Test Corp', 'stock') "
        "ON CONFLICT (ticker) DO UPDATE SET name = excluded.name RETURNING id"
    )
    p1 = await admin.fetchval(
        "INSERT INTO portfolios (name, initial_capital) VALUES ('P1', 10000) RETURNING id"
    )
    p2 = await admin.fetchval(
        "INSERT INTO portfolios (name, initial_capital) VALUES ('P2', 20000) RETURNING id"
    )
    s1 = await admin.fetchval(
        "INSERT INTO sleeves (portfolio_id, kind, target_weight) "
        "VALUES ($1, 'satellite', 0.2) RETURNING id",
        p1,
    )
    s2 = await admin.fetchval(
        "INSERT INTO sleeves (portfolio_id, kind, target_weight) "
        "VALUES ($1, 'satellite', 0.2) RETURNING id",
        p2,
    )
    await admin.execute(
        "INSERT INTO positions (portfolio_id, sleeve_id, instrument_id, target_weight, "
        "invested_amount) VALUES ($1, $2, $3, 0.5, 5000), ($4, $5, $3, 0.5, 9000)",
        p1,
        s1,
        inst,
        p2,
        s2,
    )
    yield p1, p2
    await admin.close()


@pytest.fixture
async def app_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_engine(APP_URL)
    yield engine
    await engine.dispose()


def _sql_step(sql: str | None) -> Step:
    return Step(id=1, question="q", tool=ToolName.RUN_SQL, sql=sql)


async def test_run_sql_returns_fact_rows(
    seeded_portfolios: tuple[int, int], app_engine: AsyncEngine
) -> None:
    p1, _ = seeded_portfolios
    tool = RunSqlTool(engine=app_engine, portfolio_id=p1)
    evidence = await tool.run(
        _sql_step("SELECT ticker, name FROM instruments WHERE ticker = 'TSTX'")
    )
    assert evidence.error is None
    assert "TSTX" in evidence.content
    assert "Test Corp" in evidence.content


async def test_run_sql_is_rls_scoped_to_own_portfolio(
    seeded_portfolios: tuple[int, int], app_engine: AsyncEngine
) -> None:
    p1, _ = seeded_portfolios
    tool = RunSqlTool(engine=app_engine, portfolio_id=p1)
    evidence = await tool.run(_sql_step("SELECT invested_amount FROM positions"))
    assert evidence.error is None
    assert "5000" in evidence.content
    assert "9000" not in evidence.content


async def test_run_sql_rejects_writes(
    seeded_portfolios: tuple[int, int], app_engine: AsyncEngine
) -> None:
    p1, _ = seeded_portfolios
    admin = await _admin_or_skip()
    tool = RunSqlTool(engine=app_engine, portfolio_id=p1)
    evidence = await tool.run(
        _sql_step("INSERT INTO instruments (ticker, name, type) VALUES ('EVIL', 'x', 'stock')")
    )
    assert evidence.error is not None
    count = await admin.fetchval("SELECT count(*) FROM instruments WHERE ticker = 'EVIL'")
    await admin.close()
    assert count == 0


async def test_run_sql_without_sql_is_error_evidence(
    seeded_portfolios: tuple[int, int], app_engine: AsyncEngine
) -> None:
    p1, _ = seeded_portfolios
    tool = RunSqlTool(engine=app_engine, portfolio_id=p1)
    evidence = await tool.run(_sql_step(None))
    assert evidence.error is not None


async def test_run_sql_rounds_noisy_numerics_to_six_significant_figures(
    seeded_portfolios: tuple[int, int], app_engine: AsyncEngine
) -> None:
    p1, _ = seeded_portfolios
    tool = RunSqlTool(engine=app_engine, portfolio_id=p1)
    evidence = await tool.run(
        _sql_step("SELECT 100000.0000000000018189894035458564::numeric AS total")
    )
    assert evidence.error is None
    assert "total=100000" in evidence.content
    assert "100000.0000000000018" not in evidence.content


async def test_run_sql_caps_returned_rows(
    seeded_portfolios: tuple[int, int], app_engine: AsyncEngine
) -> None:
    p1, _ = seeded_portfolios
    tool = RunSqlTool(engine=app_engine, portfolio_id=p1)
    evidence = await tool.run(_sql_step("SELECT generate_series(1, 500) AS n"))
    assert evidence.error is None
    assert evidence.content.count("\n") < 60


class _FakeSummaries:
    def __init__(self, summary: PortfolioSummary | None) -> None:
        self._summary: PortfolioSummary | None = summary

    async def summary(self, portfolio_id: int) -> PortfolioSummary | None:
        return self._summary


def _summary(portfolio_id: int) -> PortfolioSummary:
    return PortfolioSummary(
        portfolio_id=portfolio_id,
        name="P1",
        initial_capital=10000,
        monthly_contribution=200,
        invested_total=10000,
        current_value=12345.67,
        allocation=[],
        drift=[],
        projections=[
            ProjectionOut(years=10, annual_rate=0.07, expected=152340.55, low=1e5, high=2e5),
        ],
        health=PortfolioHealth(headline=0.0, criteria=[]),
    )


async def test_get_projection_renders_summary_numbers() -> None:
    tool = GetProjectionTool(summaries=_FakeSummaries(_summary(1)), portfolio_id=1)
    evidence = await tool.run(Step(id=1, question="projection?", tool=ToolName.GET_PROJECTION))
    assert evidence.error is None
    assert "12345.67" in evidence.content
    assert "152340.55" in evidence.content
    assert "10" in evidence.content


async def test_get_projection_missing_portfolio_is_error() -> None:
    tool = GetProjectionTool(summaries=_FakeSummaries(None), portfolio_id=99)
    evidence = await tool.run(Step(id=1, question="projection?", tool=ToolName.GET_PROJECTION))
    assert evidence.error is not None
