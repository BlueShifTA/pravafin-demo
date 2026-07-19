"""backfill_market_cap (integration): derive market_cap from latest close x shares.

Auto-skips when Postgres is down (`just stack-up` to run).
"""

import asyncio

import asyncpg
import pytest
import sqlalchemy as sa
from sqlalchemy.exc import InterfaceError, OperationalError

import coresat.db as csdb
from coresat.services.ingestion.loaders import backfill_market_cap

ADMIN_DSN = "postgresql://postgres:postgres@localhost:5434/coresat_test"


async def _run() -> object:
    await csdb.apply_schema(ADMIN_DSN)
    engine = csdb.create_engine(csdb.to_async_url(ADMIN_DSN))
    try:
        async with engine.begin() as conn:
            await conn.execute(sa.text("DELETE FROM instruments WHERE ticker = 'TSTMC'"))
            instrument_id = (
                await conn.execute(
                    sa.text(
                        "INSERT INTO instruments (ticker, name, type) "
                        "VALUES ('TSTMC', 'Market Cap Test', 'stock') RETURNING id"
                    )
                )
            ).scalar_one()
            await conn.execute(
                sa.text(
                    "INSERT INTO prices_daily (instrument_id, date, open, high, low, close, volume) "
                    "VALUES (:i, '2025-01-02', 9, 9, 9, 9, 10), (:i, '2026-01-02', 12, 12, 12, 12, 10)"
                ),
                {"i": instrument_id},
            )
            # market_cap left NULL, shares present -> should be derived
            await conn.execute(
                sa.text("INSERT INTO fundamentals (instrument_id, shares) VALUES (:i, 1000000)"),
                {"i": instrument_id},
            )
        async with engine.begin() as conn:
            filled = await backfill_market_cap(conn)
        async with engine.connect() as conn:
            market_cap = (
                await conn.execute(
                    sa.text("SELECT market_cap FROM fundamentals WHERE instrument_id = :i"),
                    {"i": instrument_id},
                )
            ).scalar_one()
        return filled, market_cap
    finally:
        await engine.dispose()


def test_backfill_market_cap_uses_latest_close_times_shares() -> None:
    try:
        filled, market_cap = asyncio.run(_run())  # type: ignore[misc]
    except OSError, asyncpg.PostgresError, OperationalError, InterfaceError, TimeoutError:
        pytest.skip("postgres not running — just stack-up")
    assert filled >= 1
    assert market_cap == 12 * 1_000_000  # latest close (12), not the older 9


def test_backfill_market_cap_leaves_existing_cap_untouched() -> None:
    async def _run_existing() -> object:
        await csdb.apply_schema(ADMIN_DSN)
        engine = csdb.create_engine(csdb.to_async_url(ADMIN_DSN))
        try:
            async with engine.begin() as conn:
                await conn.execute(sa.text("DELETE FROM instruments WHERE ticker = 'TSTMC2'"))
                instrument_id = (
                    await conn.execute(
                        sa.text(
                            "INSERT INTO instruments (ticker, name, type) "
                            "VALUES ('TSTMC2', 'Existing Cap', 'stock') RETURNING id"
                        )
                    )
                ).scalar_one()
                await conn.execute(
                    sa.text(
                        "INSERT INTO prices_daily (instrument_id, date, open, high, low, close, "
                        "volume) VALUES (:i, '2026-01-02', 5, 5, 5, 5, 10)"
                    ),
                    {"i": instrument_id},
                )
                await conn.execute(
                    sa.text(
                        "INSERT INTO fundamentals (instrument_id, market_cap, shares) "
                        "VALUES (:i, 999, 1000000)"
                    ),
                    {"i": instrument_id},
                )
            async with engine.begin() as conn:
                await backfill_market_cap(conn)
            async with engine.connect() as conn:
                return (
                    await conn.execute(
                        sa.text("SELECT market_cap FROM fundamentals WHERE instrument_id = :i"),
                        {"i": instrument_id},
                    )
                ).scalar_one()
        finally:
            await engine.dispose()

    try:
        market_cap = asyncio.run(_run_existing())
    except OSError, asyncpg.PostgresError, OperationalError, InterfaceError, TimeoutError:
        pytest.skip("postgres not running — just stack-up")
    assert market_cap == 999  # snapshot cap preserved, not overwritten by 5 x shares
