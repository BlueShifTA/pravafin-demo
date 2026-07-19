"""Ingestion pipeline (integration): quarantine, idempotency, run bookkeeping.

Auto-skips when Postgres is down (`just stack-up` to run).
"""

import asyncio
from collections.abc import AsyncIterator

import asyncpg
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

import coresat.db as csdb
import coresat.services.ingestion as csi
from coresat.main import app

ADMIN_DSN = "postgresql://postgres:postgres@localhost:5434/coresat_test"
ADMIN_SQLA_URL = "postgresql+asyncpg://postgres:postgres@localhost:5434/coresat_test"


class _FakeEmbedder:
    """CSV adapters never embed; the pdf adapter's embedder is unused here."""

    async def embed(self, query: str) -> list[float]:
        return [0.0] * 768


UNIVERSE_CSV = b"""ticker,type,sector,industry
TSTN,stock,semiconductor,Semiconductors
,stock,broken-row,
"""

FUNDAMENTALS_CSV = b"""ticker,name,pe_trailing,revenue
TSTN,Test Semi Corp,12.5,1000000
"""

FINANCIALS_YEARLY_CSV = b"""ticker,fy,revenue,opex,net_income,net_margin,ocf,capex,fcf,shares
TSTN,2023,1000000,,80000,0.08,150000,30000,120000,10000
TSTN,2024,,,,,200000,,,10000
TSTN,,missing-fy-row,,,,,,,
"""


async def _admin_or_skip() -> asyncpg.Connection:
    try:
        return await asyncpg.connect(ADMIN_DSN, timeout=3)
    except OSError, asyncpg.PostgresError, TimeoutError:
        pytest.skip("postgres not running — just stack-up")


@pytest.fixture
async def clean_db() -> AsyncIterator[None]:
    admin = await _admin_or_skip()
    await csdb.apply_schema(ADMIN_DSN)
    await admin.execute("TRUNCATE ingest_quarantine, ingest_runs RESTART IDENTITY CASCADE")
    await admin.execute("DELETE FROM instruments WHERE ticker IN ('TSTN')")
    yield
    await admin.close()


@pytest.fixture
async def pipeline() -> AsyncIterator[csi.IngestionPipeline]:
    engine: AsyncEngine = csdb.create_engine(ADMIN_SQLA_URL)
    yield csi.IngestionPipeline(engine=engine, registry=csi.build_registry(_FakeEmbedder()))
    await engine.dispose()


@pytest.mark.usefixtures("clean_db")
async def test_malformed_rows_land_in_quarantine_with_reason(
    pipeline: csi.IngestionPipeline,
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
    pipeline: csi.IngestionPipeline,
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
async def test_all_rows_invalid_marks_run_failed(pipeline: csi.IngestionPipeline) -> None:
    report = await pipeline.run("universe_csv", b"ticker,type\n,stock\n,etf\n")
    assert report.status == "failed"
    assert report.rows_ok == 0


@pytest.mark.usefixtures("clean_db")
async def test_unknown_adapter_raises(pipeline: csi.IngestionPipeline) -> None:
    with pytest.raises(KeyError):
        await pipeline.run("no_such_adapter", b"x")


@pytest.mark.usefixtures("clean_db")
async def test_fundamentals_backfill_stub_instrument_names(
    pipeline: csi.IngestionPipeline,
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
async def test_yearly_financials_load_with_missing_values_as_null(
    pipeline: csi.IngestionPipeline,
) -> None:
    report = await pipeline.run("financials_yearly_csv", FINANCIALS_YEARLY_CSV)
    assert report.rows_ok == 2
    assert report.rows_quarantined == 1  # row without fiscal year
    async with pipeline.engine.connect() as conn:
        rows = (
            await conn.execute(
                text(
                    "SELECT fy, revenue, ocf, capex FROM financials_yearly f "
                    "JOIN instruments i ON i.id = f.instrument_id "
                    "WHERE i.ticker = 'TSTN' ORDER BY fy"
                )
            )
        ).all()
    assert [row.fy for row in rows] == [2023, 2024]
    assert float(rows[0].revenue) == 1_000_000
    assert rows[1].revenue is None  # missing -> NULL
    assert float(rows[1].ocf) == 200_000
    assert rows[1].capex is None


def test_financials_endpoint_returns_series_with_gaps() -> None:
    payload = b"""ticker,fy,revenue,net_income,net_margin,ocf,capex,fcf,shares
TSTQ,2023,1000000,80000,0.08,150000,30000,120000,10000
TSTQ,2024,,,,200000,,,10000
"""

    async def _seed() -> None:
        admin = await _admin_or_skip()
        await csdb.apply_schema(ADMIN_DSN)
        await admin.execute("TRUNCATE ingest_quarantine, ingest_runs RESTART IDENTITY CASCADE")
        await admin.execute("DELETE FROM instruments WHERE ticker = 'TSTQ'")
        await admin.close()
        engine = csdb.create_engine(ADMIN_SQLA_URL)
        try:
            pipeline = csi.IngestionPipeline(
                engine=engine, registry=csi.build_registry(_FakeEmbedder())
            )
            await pipeline.run("financials_yearly_csv", payload)
        finally:
            await engine.dispose()

    asyncio.run(_seed())
    with TestClient(app) as client:
        response = client.get("/api/market/financials/TSTQ")
        assert response.status_code == 200, response.text
        series = response.json()
        assert [point["fy"] for point in series] == [2023, 2024]
        assert series[0]["revenue"] == 1_000_000
        assert series[0]["cf_per_share"] == 15.0  # ocf / shares
        assert series[1]["revenue"] is None
        assert series[1]["cf_per_share"] == 20.0

        assert client.get("/api/market/financials/NOPE").status_code == 404


@pytest.mark.usefixtures("clean_db")
async def test_fundamentals_do_not_clobber_universe_names(
    pipeline: csi.IngestionPipeline,
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
