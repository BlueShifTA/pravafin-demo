"""Comparison feature (integration, fake LLM): grounded by construction.

The LLM is a FakeListChatModel — deterministic, no Ollama required.
Auto-skips when Postgres is down (`just stack-up` to run).
"""

import asyncio
import json

import asyncpg
import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models import FakeListChatModel

from coresat.db.schema import apply_schema
from coresat.main import app
from coresat.services.comparison import ComparisonService

ADMIN_DSN = "postgresql://postgres:postgres@localhost:5434/coresat"
APP_URL = "postgresql+asyncpg://coresat_app:coresat_app@localhost:5434/coresat"

_GOOD_VERDICT = json.dumps(
    {
        "per_criterion": [
            {
                "criterion": "valuation",
                "winner": "TSTA",
                "reasoning": "TSTA trades at P/E 10.0 versus 40.0 for TSTB.",
            }
        ],
        "summary": "TSTA is cheaper on earnings; TSTB grows faster.",
        "caveats": ["Snapshot data; no forward estimates."],
    }
)

_FABRICATED_VERDICT = json.dumps(
    {
        "per_criterion": [
            {
                "criterion": "valuation",
                "winner": "TSTA",
                "reasoning": "TSTA revenue of 987654321000 dwarfs TSTB.",
            }
        ],
        "summary": "TSTA wins.",
        "caveats": [],
    }
)


async def _connect_or_skip() -> asyncpg.Connection:
    try:
        return await asyncpg.connect(ADMIN_DSN, timeout=3)
    except OSError, asyncpg.PostgresError, TimeoutError:
        pytest.skip("postgres not running — just stack-up")


async def _prepare() -> int:
    conn = await _connect_or_skip()
    await apply_schema(ADMIN_DSN)
    await conn.execute(
        "DELETE FROM fundamentals WHERE instrument_id IN "
        "(SELECT id FROM instruments WHERE ticker IN ('TSTA','TSTB'))"
    )
    await conn.execute("DELETE FROM instruments WHERE ticker IN ('TSTA','TSTB')")
    ids = {
        ticker: await conn.fetchval(
            "INSERT INTO instruments (ticker, name, type) VALUES ($1, $2, 'stock') RETURNING id",
            ticker,
            name,
        )
        for ticker, name in (("TSTA", "Alpha Corp"), ("TSTB", "Beta Corp"))
    }
    await conn.execute(
        "INSERT INTO fundamentals (instrument_id, pe_trailing, revenue, net_profit) VALUES "
        "($1, 10.0, 5000000, 500000), ($2, 40.0, 9000000, 200000)",
        ids["TSTA"],
        ids["TSTB"],
    )
    portfolio_id = await conn.fetchval(
        "INSERT INTO portfolios (name, initial_capital) VALUES ('CmpTest', 1000) RETURNING id"
    )
    await conn.close()
    return int(portfolio_id)


def _client_with_fake_llm(responses: list[str]) -> TestClient:
    test_client = TestClient(app)
    test_client.__enter__()
    fake = FakeListChatModel(responses=responses)
    state = test_client.app.state  # type: ignore[union-attr]
    state.comparison_service = ComparisonService(engine=state.app_engine, llm=fake)
    return test_client


@pytest.fixture
def portfolio_id() -> int:
    return asyncio.run(_prepare())


def test_comparison_returns_grounded_verdict(portfolio_id: int) -> None:
    client = _client_with_fake_llm([_GOOD_VERDICT])
    try:
        response = client.post(
            "/api/compare", json={"tickers": ["TSTA", "TSTB"], "portfolio_id": portfolio_id}
        )
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["per_criterion"][0]["winner"] == "TSTA"
        assert "cheaper" in result["summary"]
    finally:
        client.__exit__(None, None, None)


def test_fabricated_number_is_rejected_after_retry(portfolio_id: int) -> None:
    client = _client_with_fake_llm([_FABRICATED_VERDICT, _FABRICATED_VERDICT])
    try:
        response = client.post(
            "/api/compare", json={"tickers": ["TSTA", "TSTB"], "portfolio_id": portfolio_id}
        )
        assert response.status_code == 422
        assert "fabricat" in response.json()["detail"].lower()
    finally:
        client.__exit__(None, None, None)


def test_unknown_ticker_is_422(portfolio_id: int) -> None:
    client = _client_with_fake_llm([_GOOD_VERDICT])
    try:
        response = client.post(
            "/api/compare", json={"tickers": ["TSTA", "NOPE"], "portfolio_id": portfolio_id}
        )
        assert response.status_code == 422
    finally:
        client.__exit__(None, None, None)


def test_comparison_writes_audit_row(portfolio_id: int) -> None:
    client = _client_with_fake_llm([_GOOD_VERDICT])
    try:
        client.post(
            "/api/compare", json={"tickers": ["TSTA", "TSTB"], "portfolio_id": portfolio_id}
        )
    finally:
        client.__exit__(None, None, None)

    async def _count() -> int:
        conn = await asyncpg.connect(ADMIN_DSN, timeout=3)
        try:
            return int(
                await conn.fetchval(
                    "SELECT count(*) FROM llm_audit_log "
                    "WHERE portfolio_id = $1 AND feature = 'comparison'",
                    portfolio_id,
                )
            )
        finally:
            await conn.close()

    assert asyncio.run(_count()) == 1
