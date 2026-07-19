"""Real-LLM routing + end-to-end RAG. Gated behind CORESAT_REAL_LLM=1.

These exercise the actual planner (qwen) deciding rag_search vs run_sql vs
get_projection, and a full ingest-a-PDF → copilot-answers-from-it round trip.
They need Ollama serving the configured chat model, nomic-embed-text, and will
download the fastembed reranker on first use. All skip without the env flag;
DB-backed ones additionally skip when Postgres is down.
"""

import json
import os

import pytest
from _pdfgen import make_text_pdf
from fastapi.testclient import TestClient

import coresat.core as csc
import coresat.domain as csd
import coresat.services.agent as csa
from coresat.main import app

pytestmark = pytest.mark.skipif(
    os.environ.get("CORESAT_REAL_LLM") != "1",
    reason="real-LLM test: set CORESAT_REAL_LLM=1 with Ollama serving the configured models",
)


def _planner() -> csa.ChatModelAgentLLM:
    settings = csc.get_settings()
    return csa.ChatModelAgentLLM(
        csa.build_chat_model(settings.copilot_provider, settings), csa.COPILOT_PROMPTS
    )


async def test_document_query_routes_to_rag_search() -> None:
    plan, _ = await _planner().plan(
        "What does the IWDA fund factsheet say about its investment objective and strategy?",
        "",
        None,
    )
    tools = {step.tool for step in plan.steps}
    assert csd.ToolName.RAG_SEARCH in tools, f"expected rag_search, planned {tools}"


async def test_fundamentals_query_routes_to_run_sql_not_rag() -> None:
    plan, _ = await _planner().plan("What is NVDA's trailing P/E ratio?", "", None)
    tools = {step.tool for step in plan.steps}
    assert csd.ToolName.RUN_SQL in tools, f"expected run_sql, planned {tools}"
    assert csd.ToolName.RAG_SEARCH not in tools, (
        f"a fundamentals figure should not go to rag: {tools}"
    )


async def test_portfolio_value_query_routes_to_get_projection() -> None:
    plan, _ = await _planner().plan("What is my portfolio worth right now?", "", None)
    tools = {step.tool for step in plan.steps}
    assert csd.ToolName.GET_PROJECTION in tools, f"expected get_projection, planned {tools}"


async def test_named_fund_cagr_routes_to_run_sql_not_projection() -> None:
    # A named fund's own return lives in funds.cagr_10y — a run_sql lookup, not
    # the whole-portfolio projection. Regression guard for the SCHG mis-route.
    plan, _ = await _planner().plan("What is the 10-year CAGR of the SCHG fund?", "", None)
    tools = {step.tool for step in plan.steps}
    assert csd.ToolName.RUN_SQL in tools, f"a named fund's CAGR is a funds lookup: {tools}"
    assert csd.ToolName.GET_PROJECTION not in tools, f"get_projection is portfolio-only: {tools}"


def _events(body: str) -> list[tuple[str, object]]:
    events: list[tuple[str, object]] = []
    for block in body.split("\n\n"):
        name = data = None
        for line in block.splitlines():
            if line.startswith("event: "):
                name = line[len("event: ") :]
            elif line.startswith("data: "):
                data = json.loads(line[len("data: ") :])
        if name is not None:
            events.append((name, data))
    return events


def test_copilot_answers_from_ingested_pdf() -> None:
    # Ingest a PDF carrying a fact that lives in no SQL table, then ask the
    # copilot a question only that document can answer.
    pdf = make_text_pdf(
        [
            "The CoreSat World ETF follows a full replication strategy and "
            "excludes companies involved in controversial weapons."
        ]
    )
    client = TestClient(app)
    client.__enter__()
    try:
        ingest = client.post(
            "/api/ingest/pdf",
            params={"source_ref": "coresat_world_factsheet.pdf"},
            files={"file": ("coresat_world_factsheet.pdf", pdf, "application/pdf")},
        )
        assert ingest.status_code == 200, ingest.text
        assert ingest.json()["rows_ok"] >= 1

        # a portfolio is required by the chat route; any existing one works
        portfolios = client.get("/api/portfolios").json()
        if not portfolios:
            pytest.skip("no portfolio seeded to chat against")
        portfolio_id = portfolios[0]["id"]

        response = client.post(
            f"/api/portfolios/{portfolio_id}/chat",
            json={"message": "What replication strategy does the CoreSat World ETF use?"},
        )
        assert response.status_code == 200, response.text
        events = _events(response.text)
        names = [name for name, _ in events]
        assert "plan" in names
        assert events[-1][0] == "answer"
        answer = events[-1][1]
        assert isinstance(answer, dict)
        assert answer["message"]["content"]
    finally:
        client.__exit__(None, None, None)
