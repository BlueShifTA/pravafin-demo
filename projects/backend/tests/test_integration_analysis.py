"""Single-stock analysis feature (integration, fake LLM): grounded by construction.

Mirrors the comparison tests: FakeListChatModel, dedicated coresat_test DB,
auto-skips when Postgres is down. Real-LLM run is gated behind CORESAT_REAL_LLM=1.
"""

import asyncio
import json
import os

import asyncpg
import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models import FakeListChatModel

import coresat.services as css
from coresat.main import app
from tests.test_integration_comparison import ADMIN_DSN, _prepare

_GOOD_NARRATIVE = json.dumps(
    {
        "summary": "Alpha Corp trades at P/E 10 with revenue of 5M.",
        "strengths": ["Cheap on earnings at P/E 10", "Profitable with net profit 500000"],
        "weaknesses": ["Small revenue base of 5M"],
        "caveats": ["Snapshot data only."],
    }
)

_FABRICATED_NARRATIVE = json.dumps(
    {
        "summary": "Alpha Corp revenue of 987654321000 dominates.",
        "strengths": ["Huge"],
        "weaknesses": [],
        "caveats": [],
    }
)


def _client_with_fake_llm(responses: list[str]) -> TestClient:
    test_client = TestClient(app)
    test_client.__enter__()
    fake = FakeListChatModel(responses=responses)
    state = test_client.app.state  # type: ignore[union-attr]
    state.analysis_service = css.AnalysisService(
        engine=state.app_engine, llm=fake, analytics=state.analytics_service
    )
    return test_client


@pytest.fixture
def portfolio_id() -> int:
    return asyncio.run(_prepare())


def test_analysis_returns_grounded_narrative(portfolio_id: int) -> None:
    client = _client_with_fake_llm([_GOOD_NARRATIVE])
    try:
        response = client.post(
            "/api/analysis/stock", json={"ticker": "TSTA", "portfolio_id": portfolio_id}
        )
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["ticker"] == "TSTA"
        assert "P/E 10" in result["summary"]
        assert result["strengths"]
        assert result["magic_formula_match"] in {"Excellent", "Good", "Fair", "Poor", "Unrated"}
    finally:
        client.__exit__(None, None, None)


def test_fabricated_analysis_is_rejected(portfolio_id: int) -> None:
    client = _client_with_fake_llm([_FABRICATED_NARRATIVE, _FABRICATED_NARRATIVE])
    try:
        response = client.post(
            "/api/analysis/stock", json={"ticker": "TSTA", "portfolio_id": portfolio_id}
        )
        assert response.status_code == 422
        assert "fabricat" in response.json()["detail"].lower()
    finally:
        client.__exit__(None, None, None)


def test_analysis_unknown_ticker_is_422(portfolio_id: int) -> None:
    client = _client_with_fake_llm([_GOOD_NARRATIVE])
    try:
        response = client.post(
            "/api/analysis/stock", json={"ticker": "NOPE", "portfolio_id": portfolio_id}
        )
        assert response.status_code == 422
    finally:
        client.__exit__(None, None, None)


def test_analysis_writes_audit_row(portfolio_id: int) -> None:
    client = _client_with_fake_llm([_GOOD_NARRATIVE])
    try:
        client.post("/api/analysis/stock", json={"ticker": "TSTA", "portfolio_id": portfolio_id})
    finally:
        client.__exit__(None, None, None)

    async def _count() -> int:
        conn = await asyncpg.connect(ADMIN_DSN, timeout=3)
        try:
            return int(
                await conn.fetchval(
                    "SELECT count(*) FROM llm_audit_log "
                    "WHERE portfolio_id = $1 AND feature = 'analysis'",
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
def test_real_llm_analysis_end_to_end(portfolio_id: int) -> None:
    client = TestClient(app)
    client.__enter__()
    try:
        response = client.post(
            "/api/analysis/stock", json={"ticker": "TSTA", "portfolio_id": portfolio_id}
        )
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["model"] == "gemma4:e4b"
        assert result["summary"]
        assert result["strengths"]
    finally:
        client.__exit__(None, None, None)
