"""Ingestion pipeline (integration): quarantine, idempotency, run bookkeeping.

Auto-skips when Postgres is down (`just stack-up` to run).
"""

from collections.abc import AsyncIterator

import asyncpg
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from coresat.db.schema import apply_schema
from coresat.db.session import create_engine
from coresat.services.ingestion.pipeline import IngestionPipeline, build_registry

ADMIN_DSN = "postgresql://postgres:postgres@localhost:5434/coresat_test"
ADMIN_SQLA_URL = "postgresql+asyncpg://postgres:postgres@localhost:5434/coresat_test"

UNIVERSE_CSV = b"""ticker,type,sector,industry
TSTN,stock,semiconductor,Semiconductors
,stock,broken-row,
"""

FUNDAMENTALS_CSV = b"""ticker,name,pe_trailing,revenue
TSTN,Test Semi Corp,12.5,1000000
"""


async def _admin_or_skip() -> asyncpg.Connection:
    try:
        return await asyncpg.connect(ADMIN_DSN, timeout=3)
    except OSError, asyncpg.PostgresError, TimeoutError:
        pytest.skip("postgres not running — just stack-up")


@pytest.fixture
async def clean_db() -> AsyncIterator[None]:
    admin = await _admin_or_skip()
    await apply_schema(ADMIN_DSN)
    await admin.execute("TRUNCATE ingest_quarantine, ingest_runs RESTART IDENTITY CASCADE")
    await admin.execute("DELETE FROM instruments WHERE ticker IN ('TSTN')")
    yield
    await admin.close()


@pytest.fixture
async def pipeline() -> AsyncIterator[IngestionPipeline]:
    engine: AsyncEngine = create_engine(ADMIN_SQLA_URL)
    yield IngestionPipeline(engine=engine, registry=build_registry())
    await engine.dispose()


@pytest.mark.usefixtures("clean_db")
async def test_malformed_rows_land_in_quarantine_with_reason(
    pipeline: IngestionPipeline,
) -> None:
    report = await pipeline.run("universe_csv", UNIVERSE_CSV)
    assert report.rows_in == 2
    assert report.rows_ok == 1
    assert report.rows_quarantined == 1
    async with pipeline.engine.connect() as conn:
        reason = (
            await conn.execute(text("SELECT reason FROM ingest_quarantine LIMIT 1"))
        ).scalar_one()
    assert "ticker" in reason


@pytest.mark.usefixtures("clean_db")
async def test_reingest_same_payload_skips_and_creates_no_duplicates(
    pipeline: IngestionPipeline,
) -> None:
    first = await pipeline.run("universe_csv", UNIVERSE_CSV)
    second = await pipeline.run("universe_csv", UNIVERSE_CSV)
    assert first.status == "succeeded"
    assert second.status == "skipped"
    async with pipeline.engine.connect() as conn:
        count = (
            await conn.execute(text("SELECT count(*) FROM instruments WHERE ticker = 'TSTN'"))
        ).scalar_one()
    assert count == 1


@pytest.mark.usefixtures("clean_db")
async def test_all_rows_invalid_marks_run_failed(pipeline: IngestionPipeline) -> None:
    report = await pipeline.run("universe_csv", b"ticker,type\n,stock\n,etf\n")
    assert report.status == "failed"
    assert report.rows_ok == 0


@pytest.mark.usefixtures("clean_db")
async def test_unknown_adapter_raises(pipeline: IngestionPipeline) -> None:
    with pytest.raises(KeyError):
        await pipeline.run("no_such_adapter", b"x")


@pytest.mark.usefixtures("clean_db")
async def test_fundamentals_backfill_stub_instrument_names(
    pipeline: IngestionPipeline,
) -> None:
    # fundamentals arrive before any universe file: the instrument is created
    # as a ticker-named stub and must pick up the real company name
    report = await pipeline.run("fundamentals_csv", FUNDAMENTALS_CSV)
    assert report.status == "succeeded"
    async with pipeline.engine.connect() as conn:
        name = (
            await conn.execute(text("SELECT name FROM instruments WHERE ticker = 'TSTN'"))
        ).scalar_one()
    assert name == "Test Semi Corp"


@pytest.mark.usefixtures("clean_db")
async def test_fundamentals_do_not_clobber_universe_names(
    pipeline: IngestionPipeline,
) -> None:
    await pipeline.run(
        "universe_csv", b"ticker,type,name,sector,industry\nTSTN,stock,Authoritative Name,x,y\n"
    )
    await pipeline.run("fundamentals_csv", FUNDAMENTALS_CSV)
    async with pipeline.engine.connect() as conn:
        name = (
            await conn.execute(text("SELECT name FROM instruments WHERE ticker = 'TSTN'"))
        ).scalar_one()
    assert name == "Authoritative Name"
