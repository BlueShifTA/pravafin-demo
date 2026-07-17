"""Indicators endpoint (integration): per-day series from prices_daily.

Auto-skips when Postgres is down (`just stack-up` to run).
"""

import asyncio
import datetime

import asyncpg
import pytest
from fastapi.testclient import TestClient

from coresat.db.schema import apply_schema
from coresat.main import app

ADMIN_DSN = "postgresql://postgres:postgres@localhost:5434/coresat_test"


async def _connect_or_skip() -> asyncpg.Connection:
    try:
        return await asyncpg.connect(ADMIN_DSN, timeout=3)
    except OSError, asyncpg.PostgresError, TimeoutError:
        pytest.skip("postgres not running — just stack-up")


async def _seed_prices(days: int) -> None:
    conn = await _connect_or_skip()
    await apply_schema(ADMIN_DSN)
    await conn.execute(
        "DELETE FROM prices_daily WHERE instrument_id IN "
        "(SELECT id FROM instruments WHERE ticker = 'TSTI')"
    )
    await conn.execute("DELETE FROM instruments WHERE ticker = 'TSTI'")
    instrument_id = await conn.fetchval(
        "INSERT INTO instruments (ticker, name, type) VALUES ('TSTI', 'Indicator Corp', 'stock') "
        "RETURNING id"
    )
    today = datetime.datetime.now(datetime.UTC).date()
    await conn.executemany(
        "INSERT INTO prices_daily (instrument_id, date, open, high, low, close, volume) "
        "VALUES ($1, $2, $3, $3, $3, $3, 1000)",
        [
            (instrument_id, today - datetime.timedelta(days=days - i), 100.0 + i)
            for i in range(days)
        ],
    )
    await conn.close()


def test_indicator_series_endpoint() -> None:
    asyncio.run(_seed_prices(60))
    with TestClient(app) as client:
        response = client.get("/api/market/indicators/TSTI")
        assert response.status_code == 200, response.text
        points = response.json()
        assert len(points) == 60
        last = points[-1]
        assert last["close"] == 159.0
        assert last["sma_20"] is not None
        assert last["ema_12"] is not None
        assert last["rsi"] == 100.0  # strictly rising prices
        assert last["macd"] is not None
        assert points[0]["sma_50"] is None  # warm-up window


def test_indicators_days_param_slices_tail() -> None:
    asyncio.run(_seed_prices(60))
    with TestClient(app) as client:
        response = client.get("/api/market/indicators/TSTI?days=10")
        assert response.status_code == 200
        points = response.json()
        assert len(points) == 10
        # indicators computed over full history, then sliced: still present
        assert points[0]["sma_20"] is not None


def test_indicators_unknown_ticker_is_404() -> None:
    asyncio.run(_seed_prices(5))
    with TestClient(app) as client:
        response = client.get("/api/market/indicators/NOPE")
        assert response.status_code == 404
