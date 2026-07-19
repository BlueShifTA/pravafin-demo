"""Real-LLM routing eval: 20 hard SQL-vs-RAG prompts. Gated behind CORESAT_REAL_LLM=1.

Drives the actual draft-agent planner (qwen) on the boundary that matters: a
figure or a table column must route to run_sql; a qualitative or document-only
fact must route to rag_search. These are deliberately difficult — a TER or a
fund size looks document-ish but is a column; a benchmark or a strategy looks
number-ish but lives only in the prospectus. A small local model will miss
some; the pass rate is the signal, not a green checkmark. Skips without the env
flag + Ollama serving the configured chat model.
"""

import os

import pytest

import coresat.core as csc
import coresat.domain as csd
import coresat.services.agent as csa

pytestmark = pytest.mark.skipif(
    os.environ.get("CORESAT_REAL_LLM") != "1",
    reason="real-LLM test: set CORESAT_REAL_LLM=1 with Ollama serving the configured model",
)


def _planner() -> csa.ChatModelAgentLLM:
    settings = csc.get_settings()
    return csa.ChatModelAgentLLM(
        csa.build_chat_model(settings.draft_agent_provider, settings), csa.DRAFT_PROMPTS
    )


# Figures and fields that live in the fact tables → run_sql.
_SQL_PROMPTS = [
    "What is NVDA's trailing P/E ratio?",
    "List the top 10 stocks by market cap.",
    "Which sector is Apple in?",
    "What is the TER of the IWDA ETF?",
    "Show me healthcare stocks with the highest ROE.",
    "What stocks do you have in the database?",
    "How big is the CSPX fund?",
    "What is Microsoft's revenue?",
    "Which ETFs have the lowest expense ratio?",
    "Give me 5 semiconductor stocks I could use as satellites.",
]

# Qualitative / document-only facts → rag_search.
_RAG_PROMPTS = [
    "What is IWDA's investment strategy according to its factsheet?",
    "Does the CSPX prospectus mention controversial-weapons exclusions?",
    "Summarize the risk factors described in the IWDA KID.",
    "What replication method does the IWDA fund use?",
    "What does the factsheet say about currency hedging?",
    "Explain the fund's stated investment objective.",
    "How does the fund approach ESG, according to its documents?",
    "What are the key risks listed in the KID document?",
    "According to the prospectus, how are dividends handled?",
    "What benchmark does IWDA track, as described in its factsheet?",
]


@pytest.mark.parametrize("prompt", _SQL_PROMPTS)
async def test_figure_prompts_route_to_run_sql(prompt: str) -> None:
    plan, _ = await _planner().plan(prompt, "", None)
    tools = {step.tool for step in plan.steps}
    assert csd.ToolName.RUN_SQL in tools, f"expected run_sql, planned {tools} for {prompt!r}"


@pytest.mark.parametrize("prompt", _RAG_PROMPTS)
async def test_document_prompts_route_to_rag_search(prompt: str) -> None:
    plan, _ = await _planner().plan(prompt, "", None)
    tools = {step.tool for step in plan.steps}
    assert csd.ToolName.RAG_SEARCH in tools, f"expected rag_search, planned {tools} for {prompt!r}"
