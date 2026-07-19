"""Comparison feature (integration, fake LLM): grounded by construction.

The LLM is a FakeListChatModel — deterministic, no Ollama required.
Auto-skips when Postgres is down (`just stack-up` to run).

The final test runs against the real Ollama model (default app wiring) and is
gated behind CORESAT_REAL_LLM=1 — needs Ollama serving gemma4:e4b.
"""

import asyncio
import json
import os

import asyncpg
import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models import FakeListChatModel

import coresat.db as csdb
import coresat.services as css
from coresat.main import app

ADMIN_DSN = "postgresql://postgres:postgres@localhost:5434/coresat_test"
APP_URL = "postgresql+asyncpg://coresat_app:coresat_app@localhost:5434/coresat_test"

_GOOD_VERDICT = json.dumps(
    {
        "per_criterion": [
            {
                "criterion": "valuation",
                "winner": "TSTA",
                "reasoning": "TSTA trades at P/E 10.0 versus 40.0 for TSTB.",
            }
        ],
        "per_ticker": [
            {
                "ticker": "TSTA",
                "pros": ["Cheap at P/E 10.0"],
                "cons": ["Smaller revenue of 5M"],
            },
            {
                "ticker": "TSTB",
                "pros": ["Larger revenue of 9M"],
                "cons": ["Expensive at P/E 40.0"],
            },
        ],
        "recommendation": "TSTA is the better magic-formula candidate at these prices.",
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
        "per_ticker": [
            {"ticker": "TSTA", "pros": ["Revenue of 987654321000"], "cons": []},
            {"ticker": "TSTB", "pros": [], "cons": ["Dwarfed"]},
        ],
        "recommendation": "TSTA wins.",
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
    await csdb.apply_schema(ADMIN_DSN)
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
        "INSERT INTO fundamentals (instrument_id, pe_trailing, revenue, net_profit, "
        "market_cap, profit_margin, roe, beta, ebit) VALUES "
        "($1, 10.0, 5000000, 500000, 60000000, 0.1, 0.25, 1.1, 800000), "
        "($2, 40.0, 9000000, 200000, 150000000, 0.022, 0.08, 1.4, 400000)",
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
    state.comparison_service = css.ComparisonService(engine=state.app_engine, llm=fake)
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
        tickers_assessed = {entry["ticker"] for entry in result["per_ticker"]}
        assert tickers_assessed == {"TSTA", "TSTB"}
        assert result["per_ticker"][0]["pros"]
        assert result["per_ticker"][0]["cons"]
        assert result["recommendation"]
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


@pytest.mark.skipif(
    os.environ.get("CORESAT_REAL_LLM") != "1",
    reason="real-LLM test — set CORESAT_REAL_LLM=1 with Ollama serving gemma4:e4b",
)
def test_real_llm_comparison_end_to_end(portfolio_id: int) -> None:
    client = TestClient(app)
    client.__enter__()
    try:
        response = client.post(
            "/api/compare", json={"tickers": ["TSTA", "TSTB"], "portfolio_id": portfolio_id}
        )
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["model"] == "gemma4:e4b"
        assert result["per_criterion"]
        assert result["per_ticker"]
        assert result["recommendation"]
        assert result["summary"]
    finally:
        client.__exit__(None, None, None)
