"""Copilot chat API (integration, fake LLM): SSE stream, persistence, audit.

Auto-skips when Postgres is down (`just stack-up` to run).
The final test runs the real Ollama model and is gated behind CORESAT_REAL_LLM=1.
"""

import asyncio
import json
import os

import asyncpg
import pytest
from fastapi.testclient import TestClient

from coresat.db.schema import apply_schema
from coresat.domain.agent import Answer, Evidence, Plan, ScopeVerdict, Step, ToolName
from coresat.main import app
from coresat.services.agent.agent import GroundedAgent
from coresat.services.agent.graph import CANNOT_ANSWER_TEXT, OFF_TOPIC_TEXT
from coresat.services.agent.llm import Usage
from coresat.services.agent.service import CopilotService

ADMIN_DSN = "postgresql://postgres:postgres@localhost:5434/coresat_test"

_USAGE = Usage(tokens_in=11, tokens_out=7)


class ScriptedAgentLLM:
    def __init__(self, in_scope: bool, plans: list[Plan], answers: list[Answer]) -> None:
        self.in_scope: bool = in_scope
        self.plans: list[Plan] = plans
        self.answers: list[Answer] = answers
        self.plan_calls: int = 0
        self.contexts_seen: list[str] = []

    async def classify_scope(self, query: str, context: str) -> tuple[ScopeVerdict, Usage]:
        self.contexts_seen.append(context)
        return ScopeVerdict(in_scope=self.in_scope), _USAGE

    async def plan(self, query: str, context: str, replan_error: str | None) -> tuple[Plan, Usage]:
        plan = self.plans[min(self.plan_calls, len(self.plans) - 1)]
        self.plan_calls += 1
        return plan, _USAGE

    async def synthesise(
        self, query: str, context: str, evidence: list[Evidence]
    ) -> tuple[Answer, Usage]:
        index = min(self.plan_calls - 1, len(self.answers) - 1)
        return self.answers[index], _USAGE


async def _connect_or_skip() -> asyncpg.Connection:
    try:
        return await asyncpg.connect(ADMIN_DSN, timeout=3)
    except OSError, asyncpg.PostgresError, TimeoutError:
        pytest.skip("postgres not running — just stack-up")


async def _prepare() -> int:
    conn = await _connect_or_skip()
    await apply_schema(ADMIN_DSN)
    await conn.execute(
        "TRUNCATE chat_messages, positions, sleeves, llm_audit_log, portfolios "
        "RESTART IDENTITY CASCADE"
    )
    inst = await conn.fetchval(
        "INSERT INTO instruments (ticker, name, type) VALUES ('TSTX', 'Test Corp', 'stock') "
        "ON CONFLICT (ticker) DO UPDATE SET name = excluded.name RETURNING id"
    )
    portfolio_id = await conn.fetchval(
        "INSERT INTO portfolios (name, initial_capital) VALUES ('ChatP', 10000) RETURNING id"
    )
    sleeve = await conn.fetchval(
        "INSERT INTO sleeves (portfolio_id, kind, target_weight) "
        "VALUES ($1, 'satellite', 0.2) RETURNING id",
        portfolio_id,
    )
    await conn.execute(
        "INSERT INTO positions (portfolio_id, sleeve_id, instrument_id, target_weight, "
        "invested_amount) VALUES ($1, $2, $3, 1.0, 5000)",
        portfolio_id,
        sleeve,
        inst,
    )
    await conn.close()
    return int(portfolio_id)


@pytest.fixture
def portfolio_id() -> int:
    return asyncio.run(_prepare())


def _sql_plan() -> Plan:
    return Plan(
        steps=[
            Step(
                id=1,
                question="invested?",
                tool=ToolName.RUN_SQL,
                sql="SELECT invested_amount FROM positions",
            )
        ]
    )


def _client(llm: ScriptedAgentLLM) -> TestClient:
    test_client = TestClient(app)
    test_client.__enter__()
    state = test_client.app.state  # type: ignore[union-attr]
    state.copilot_service = CopilotService(
        engine=state.app_engine,
        agent=GroundedAgent(llm),
        summaries=state.analytics_service,
        rag_tool=state.rag_tool,
        model_name="scripted",
    )
    return test_client


def _events(body: str) -> list[tuple[str, dict[str, object]]]:
    events: list[tuple[str, dict[str, object]]] = []
    for block in body.split("\n\n"):
        name = data = None
        for line in block.splitlines():
            if line.startswith("event: "):
                name = line.removeprefix("event: ")
            elif line.startswith("data: "):
                data = json.loads(line.removeprefix("data: "))
        if name is not None and isinstance(data, dict):
            events.append((name, data))
    return events


def test_clear_chat_wipes_only_own_history(portfolio_id: int) -> None:
    answer = Answer(text="You invested 5000.", citations=["run_sql#1"])
    client = _client(ScriptedAgentLLM(in_scope=True, plans=[_sql_plan()], answers=[answer]))
    try:
        posted = client.post(
            f"/api/portfolios/{portfolio_id}/chat", json={"message": "how much invested?"}
        )
        assert posted.status_code == 200

        async def _second_portfolio_with_history() -> int:
            conn = await _connect_or_skip()
            other = await conn.fetchval(
                "INSERT INTO portfolios (name, initial_capital) VALUES ('Keep', 500) RETURNING id"
            )
            await conn.execute(
                "INSERT INTO chat_messages (portfolio_id, role, content) "
                "VALUES ($1, 'user', 'keep me')",
                other,
            )
            await conn.close()
            return int(other)

        other_id = asyncio.run(_second_portfolio_with_history())
        cleared = client.delete(f"/api/portfolios/{portfolio_id}/chat")
        assert cleared.status_code == 204
        assert client.get(f"/api/portfolios/{portfolio_id}/chat").json() == []
        other_history = client.get(f"/api/portfolios/{other_id}/chat").json()
        assert [message["content"] for message in other_history] == ["keep me"]
    finally:
        client.__exit__(None, None, None)


def test_copilot_info_reports_configured_model() -> None:
    client = TestClient(app)
    client.__enter__()
    try:
        response = client.get("/api/copilot/info")
        assert response.status_code == 200
        assert response.json()["model"] == "qwen3.5:4b"
    finally:
        client.__exit__(None, None, None)


def test_chat_streams_plan_evidence_answer_and_persists(portfolio_id: int) -> None:
    answer = Answer(text="You invested 5000.", citations=["run_sql#1"])
    client = _client(ScriptedAgentLLM(in_scope=True, plans=[_sql_plan()], answers=[answer]))
    try:
        response = client.post(
            f"/api/portfolios/{portfolio_id}/chat", json={"message": "how much invested?"}
        )
        assert response.status_code == 200, response.text
        events = _events(response.text)
        names = [name for name, _ in events]
        assert names == ["plan", "evidence", "answer"]
        answer_payload = events[-1][1]["message"]
        assert isinstance(answer_payload, dict)
        assert answer_payload["content"] == "You invested 5000."
        citations = answer_payload["citations"]
        assert isinstance(citations, list)
        assert citations[0]["id"] == "run_sql#1"
        assert "5000" in citations[0]["content"]

        history = client.get(f"/api/portfolios/{portfolio_id}/chat")
        assert history.status_code == 200
        roles = [message["role"] for message in history.json()]
        assert roles == ["user", "assistant"]

        audit = client.get(f"/api/portfolios/{portfolio_id}/audit")
        assert audit.status_code == 200
        rows = audit.json()
        copilot_rows = [row for row in rows if row["feature"] == "copilot"]
        assert {row["node"] for row in copilot_rows} == {"scope_guard", "planner", "synthesiser"}
        run_ids = {row["graph_run_id"] for row in copilot_rows}
        assert len(run_ids) == 1 and None not in run_ids
    finally:
        client.__exit__(None, None, None)


def test_off_topic_chat_refuses_without_plan_event(portfolio_id: int) -> None:
    client = _client(ScriptedAgentLLM(in_scope=False, plans=[_sql_plan()], answers=[]))
    try:
        response = client.post(
            f"/api/portfolios/{portfolio_id}/chat", json={"message": "weather tomorrow?"}
        )
        assert response.status_code == 200
        events = _events(response.text)
        names = [name for name, _ in events]
        assert "plan" not in names
        answer_payload = events[-1][1]["message"]
        assert isinstance(answer_payload, dict)
        assert answer_payload["content"] == OFF_TOPIC_TEXT
    finally:
        client.__exit__(None, None, None)


def test_chat_to_unknown_portfolio_is_404(portfolio_id: int) -> None:
    answer = Answer(text="irrelevant")
    client = _client(ScriptedAgentLLM(in_scope=True, plans=[_sql_plan()], answers=[answer]))
    try:
        response = client.post("/api/portfolios/999999/chat", json={"message": "hi"})
        assert response.status_code == 404
    finally:
        client.__exit__(None, None, None)


def test_history_of_fresh_portfolio_is_empty(portfolio_id: int) -> None:
    answer = Answer(text="irrelevant")
    client = _client(ScriptedAgentLLM(in_scope=True, plans=[_sql_plan()], answers=[answer]))
    try:
        response = client.get(f"/api/portfolios/{portfolio_id}/chat")
        assert response.status_code == 200
        assert response.json() == []
    finally:
        client.__exit__(None, None, None)


def test_canned_refusals_are_excluded_from_llm_context(portfolio_id: int) -> None:
    # a prior off-topic refusal must not poison later scope decisions: the
    # canned text is stored in history but never fed back to the model
    refusing = _client(ScriptedAgentLLM(in_scope=False, plans=[], answers=[]))
    try:
        first = refusing.post(f"/api/portfolios/{portfolio_id}/chat", json={"message": "Hi"})
        assert first.status_code == 200
    finally:
        refusing.__exit__(None, None, None)

    async def _seed_cannot_answer() -> None:
        conn = await _connect_or_skip()
        await conn.execute(
            "INSERT INTO chat_messages (portfolio_id, role, content) VALUES ($1, 'assistant', $2)",
            portfolio_id,
            CANNOT_ANSWER_TEXT,
        )
        await conn.close()

    asyncio.run(_seed_cannot_answer())

    answering_llm = ScriptedAgentLLM(
        in_scope=True, plans=[Plan(steps=[])], answers=[Answer(text="Hello!")]
    )
    answering = _client(answering_llm)
    try:
        second = answering.post(f"/api/portfolios/{portfolio_id}/chat", json={"message": "Hi"})
        assert second.status_code == 200
        assert len(answering_llm.contexts_seen) == 1
        assert OFF_TOPIC_TEXT not in answering_llm.contexts_seen[0]
        assert CANNOT_ANSWER_TEXT not in answering_llm.contexts_seen[0]
        assert "user: Hi" in answering_llm.contexts_seen[0]
    finally:
        answering.__exit__(None, None, None)


def test_chat_history_and_audit_are_isolated_between_portfolios(portfolio_id: int) -> None:
    async def _second_portfolio() -> int:
        conn = await _connect_or_skip()
        other = await conn.fetchval(
            "INSERT INTO portfolios (name, initial_capital) VALUES ('OtherP', 500) RETURNING id"
        )
        await conn.close()
        return int(other)

    other_id = asyncio.run(_second_portfolio())
    answer = Answer(text="You invested 5000.", citations=["run_sql#1"])
    client = _client(ScriptedAgentLLM(in_scope=True, plans=[_sql_plan()], answers=[answer]))
    try:
        response = client.post(
            f"/api/portfolios/{portfolio_id}/chat", json={"message": "how much invested?"}
        )
        assert response.status_code == 200
        own_history = client.get(f"/api/portfolios/{portfolio_id}/chat").json()
        other_history = client.get(f"/api/portfolios/{other_id}/chat").json()
        assert len(own_history) == 2
        assert other_history == []
        other_audit = client.get(f"/api/portfolios/{other_id}/audit").json()
        assert other_audit == []
    finally:
        client.__exit__(None, None, None)


@pytest.mark.skipif(
    os.environ.get("CORESAT_REAL_LLM") != "1",
    reason="real-LLM test: set CORESAT_REAL_LLM=1 with Ollama serving the configured model",
)
def test_chat_real_llm_answers_grounded(portfolio_id: int) -> None:
    client = TestClient(app)
    client.__enter__()
    try:
        response = client.post(
            f"/api/portfolios/{portfolio_id}/chat",
            json={"message": "How much did I invest in total?"},
        )
        assert response.status_code == 200, response.text
        events = _events(response.text)
        assert events[-1][0] == "answer"
        answer_payload = events[-1][1]["message"]
        assert isinstance(answer_payload, dict)
        assert answer_payload["content"]
    finally:
        client.__exit__(None, None, None)
