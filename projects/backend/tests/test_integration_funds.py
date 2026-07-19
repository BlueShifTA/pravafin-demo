"""Fund comparison endpoint (integration): GET /api/market/funds?compare=.

Auto-skips when Postgres is down (`just stack-up` to run).
"""

import asyncio

import asyncpg
import pytest
from fastapi.testclient import TestClient

import coresat.db as csdb
from coresat.main import app

ADMIN_DSN = "postgresql://postgres:postgres@localhost:5434/coresat_test"


async def _connect_or_skip() -> asyncpg.Connection:
    try:
        return await asyncpg.connect(ADMIN_DSN, timeout=3)
    except OSError, asyncpg.PostgresError, TimeoutError:
        pytest.skip("postgres not running — just stack-up")


async def _seed() -> None:
    conn = await _connect_or_skip()
    await csdb.apply_schema(ADMIN_DSN)
    await conn.execute("DELETE FROM funds WHERE ticker IN ('CMPA.AS', 'CMPB.L', 'CMPC.DE')")
    await conn.execute(
        "INSERT INTO funds (ticker, name, ter, cagr_10y) VALUES "
        "('CMPA.AS', 'Compare Fund A', 0.20, 0.11), "
        "('CMPB.L', 'Compare Fund B', 0.07, 0.13), "
        "('CMPC.DE', 'Compare Fund C', 0.30, 0.09)"
    )
    await conn.close()


@pytest.fixture(autouse=True)
def seeded() -> None:
    asyncio.run(_seed())


def _client() -> TestClient:
    client = TestClient(app)
    client.__enter__()
    return client


def test_compare_returns_only_requested_funds() -> None:
    client = _client()
    try:
        response = client.get("/api/market/funds", params={"compare": "CMPA.AS,CMPB.L"})
        assert response.status_code == 200, response.text
        tickers = {row["ticker"] for row in response.json()}
        assert tickers == {"CMPA.AS", "CMPB.L"}  # C excluded
    finally:
        client.__exit__(None, None, None)


def test_compare_ignores_unknown_tickers() -> None:
    client = _client()
    try:
        response = client.get("/api/market/funds", params={"compare": "CMPA.AS,NOPE.XX"})
        assert response.status_code == 200
        tickers = {row["ticker"] for row in response.json()}
        assert tickers == {"CMPA.AS"}  # unknown silently dropped
    finally:
        client.__exit__(None, None, None)


def test_no_compare_lists_all_funds() -> None:
    client = _client()
    try:
        response = client.get("/api/market/funds")
        assert response.status_code == 200
        tickers = {row["ticker"] for row in response.json()}
        assert {"CMPA.AS", "CMPB.L", "CMPC.DE"} <= tickers  # all seeded funds present
    finally:
        client.__exit__(None, None, None)
