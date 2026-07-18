"""RLS isolation (integration): portfolio rows are invisible across portfolios.

Auto-skips when Postgres is down (`just stack-up` to run).
"""

from collections.abc import AsyncIterator

import asyncpg
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine

from coresat.db.schema import apply_schema
from coresat.db.session import create_engine, portfolio_scope
from coresat.domain.agent import Step, ToolName
from coresat.services.agent.tools import RunSqlTool

ADMIN_DSN = "postgresql://postgres:postgres@localhost:5434/coresat_test"
APP_URL = "postgresql+asyncpg://coresat_app:coresat_app@localhost:5434/coresat_test"

Seeded = tuple[int, int, int, int]  # portfolio1, portfolio2, sleeve1, sleeve2


async def _admin_or_skip() -> asyncpg.Connection:
    try:
        return await asyncpg.connect(ADMIN_DSN, timeout=3)
    except OSError, asyncpg.PostgresError, TimeoutError:
        pytest.skip("postgres not running — just stack-up")


@pytest.fixture
async def seeded() -> AsyncIterator[Seeded]:
    admin = await _admin_or_skip()
    await apply_schema(ADMIN_DSN)
    await admin.execute(
        "TRUNCATE positions, sleeves, llm_audit_log, portfolios RESTART IDENTITY CASCADE"
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
        "VALUES ($1, 'core', 0.8) RETURNING id",
        p1,
    )
    s2 = await admin.fetchval(
        "INSERT INTO sleeves (portfolio_id, kind, target_weight) "
        "VALUES ($1, 'core', 0.8) RETURNING id",
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
    yield p1, p2, s1, s2
    await admin.close()


@pytest.fixture
async def app_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_engine(APP_URL)
    yield engine
    await engine.dispose()


async def test_portfolio_sees_only_its_own_rows(seeded: Seeded, app_engine: AsyncEngine) -> None:
    p1, p2, _, _ = seeded
    async with portfolio_scope(app_engine, p1) as conn:
        owners = {
            row[0] for row in (await conn.execute(text("SELECT portfolio_id FROM positions"))).all()
        }
    assert owners == {p1}, f"portfolio {p1} must see only its rows, saw {owners}"

    async with portfolio_scope(app_engine, p2) as conn:
        owners = {
            row[0] for row in (await conn.execute(text("SELECT portfolio_id FROM positions"))).all()
        }
    assert owners == {p2}


@pytest.mark.usefixtures("seeded")
async def test_unscoped_connection_sees_nothing(app_engine: AsyncEngine) -> None:
    async with app_engine.connect() as conn:
        rows = (await conn.execute(text("SELECT id FROM positions"))).all()
    assert rows == [], "without portfolio context the app role must see zero rows"


@pytest.mark.usefixtures("seeded")
async def test_app_role_can_create_portfolio_then_read_it_scoped(
    app_engine: AsyncEngine,
) -> None:
    async with app_engine.connect() as conn, conn.begin():
        new_id = (await conn.execute(text("SELECT create_portfolio('Fresh', 500)"))).scalar_one()
    async with portfolio_scope(app_engine, new_id) as conn:
        name = (await conn.execute(text("SELECT name FROM portfolios"))).scalar_one()
    assert name == "Fresh"


async def test_write_cannot_smuggle_foreign_portfolio_id(
    seeded: Seeded, app_engine: AsyncEngine
) -> None:
    p1, p2, _, s2 = seeded
    async with portfolio_scope(app_engine, p1) as conn:
        inst = (await conn.execute(text("SELECT id FROM instruments LIMIT 1"))).scalar_one()
        with pytest.raises(DBAPIError):
            await conn.execute(
                text(
                    "INSERT INTO positions (portfolio_id, sleeve_id, instrument_id, "
                    "target_weight, invested_amount) VALUES (:p, :s, :i, 0.1, 100)"
                ),
                {"p": p2, "s": s2, "i": inst},
            )


async def test_agent_run_sql_tool_is_isolated_per_portfolio(
    seeded: Seeded, app_engine: AsyncEngine
) -> None:
    # The copilot's run_sql tool runs planner-written SQL on the request's
    # RLS-scoped connection. Even a SELECT over ALL positions returns only the
    # scoped portfolio's rows — the isolation lives below the tool.
    p1, p2, _, _ = seeded
    step = Step(
        id=1,
        question="all invested amounts",
        tool=ToolName.RUN_SQL,
        sql="SELECT portfolio_id, invested_amount FROM positions ORDER BY portfolio_id",
    )
    ev1 = await RunSqlTool(engine=app_engine, portfolio_id=p1).run(step)
    ev2 = await RunSqlTool(engine=app_engine, portfolio_id=p2).run(step)
    assert ev1.error is None and ev2.error is None
    assert f"portfolio_id={p1}" in ev1.content and f"portfolio_id={p2}" not in ev1.content
    assert f"portfolio_id={p2}" in ev2.content and f"portfolio_id={p1}" not in ev2.content


async def test_agent_run_sql_injected_foreign_id_returns_no_rows(
    seeded: Seeded, app_engine: AsyncEngine
) -> None:
    # A prompt-injected WHERE targeting another portfolio still yields nothing —
    # RLS on the scoped connection filters it out, not the SQL text.
    p1, p2, _, _ = seeded
    step = Step(
        id=1,
        question="peek at the other portfolio",
        tool=ToolName.RUN_SQL,
        sql=f"SELECT invested_amount FROM positions WHERE portfolio_id = {p2}",
    )
    evidence = await RunSqlTool(engine=app_engine, portfolio_id=p1).run(step)
    assert evidence.error is None
    assert "no rows" in evidence.content.lower()
