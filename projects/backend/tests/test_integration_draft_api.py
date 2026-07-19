"""Portfolio draft agent (integration, fake LLM): propose → confirm → create.

Auto-skips when Postgres is down (`just stack-up` to run).
"""

import asyncio
import json

import asyncpg
import pytest
from fastapi.testclient import TestClient

import coresat.db as csdb
import coresat.domain as csd
import coresat.services.agent as csa
from coresat.main import app

ADMIN_DSN = "postgresql://postgres:postgres@localhost:5434/coresat_test"

_USAGE = csa.Usage(tokens_in=9, tokens_out=4)

_VALID_DRAFT = csd.PortfolioDraft(
    name="AI Growth",
    initial_capital=100000,
    monthly_contribution=500,
    core_fund_ticker="IWDA.AS",
    core_weight=0.6,
    satellites=[
        {"ticker": "NVDA", "weight": 0.2},
        {"ticker": "UNH", "weight": 0.2},
    ],
)


class ScriptedAgentLLM:
    def __init__(self, in_scope: bool, answers: list[csd.Answer]) -> None:
        self.in_scope: bool = in_scope
        self.answers: list[csd.Answer] = answers
        self.calls: int = 0

    async def classify_scope(self, query: str, context: str) -> tuple[csd.ScopeVerdict, csa.Usage]:
        return csd.ScopeVerdict(in_scope=self.in_scope), _USAGE

    async def plan(
        self, query: str, context: str, replan_error: str | None
    ) -> tuple[csd.Plan, csa.Usage]:
        self.calls += 1
        return csd.Plan(steps=[]), _USAGE

    async def synthesise(
        self, query: str, context: str, evidence: list[csd.Evidence]
    ) -> tuple[csd.Answer, csa.Usage]:
        return self.answers[min(self.calls - 1, len(self.answers) - 1)], _USAGE


async def _connect_or_skip() -> asyncpg.Connection:
    try:
        return await asyncpg.connect(ADMIN_DSN, timeout=3)
    except OSError, asyncpg.PostgresError, TimeoutError:
        pytest.skip("postgres not running — just stack-up")


async def _seed() -> None:
    conn = await _connect_or_skip()
    await csdb.apply_schema(ADMIN_DSN)
    await conn.execute("TRUNCATE positions, sleeves, portfolios RESTART IDENTITY CASCADE")
    for ticker, name, kind in (("NVDA", "NVIDIA", "stock"), ("UNH", "UnitedHealth", "stock")):
        await conn.execute(
            "INSERT INTO instruments (ticker, name, type) VALUES ($1, $2, $3) "
            "ON CONFLICT (ticker) DO NOTHING",
            ticker,
            name,
            kind,
        )
    await conn.execute(
        "INSERT INTO funds (ticker, name, ter) VALUES ('IWDA.AS', 'iShares Core MSCI World', 0.2) "
        "ON CONFLICT (ticker) DO NOTHING"
    )
    await conn.close()


@pytest.fixture(autouse=True)
def seeded() -> None:
    asyncio.run(_seed())


def _client(llm: ScriptedAgentLLM) -> TestClient:
    test_client = TestClient(app)
    test_client.__enter__()
    state = test_client.app.state  # type: ignore[union-attr]
    state.draft_service = csa.DraftService(
        engine=state.app_engine,
        agent=csa.GroundedAgent(llm),
        portfolios=state.portfolio_service,
        rag_tool=state.rag_tool,
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


def test_propose_emits_draft_without_creating() -> None:
    answer = csd.Answer(text="Here is a portfolio.", action="propose", draft=_VALID_DRAFT)
    client = _client(ScriptedAgentLLM(in_scope=True, answers=[answer]))
    try:
        response = client.post(
            "/api/portfolio-draft/chat", json={"message": "build me a tech portfolio"}
        )
        assert response.status_code == 200, response.text
        events = _events(response.text)
        answer_event = next(payload for name, payload in events if name == "answer")
        assert answer_event["action"] == "propose"
        draft = answer_event["draft"]
        assert isinstance(draft, dict)
        assert draft["core_fund_ticker"] == "IWDA.AS"
        assert {s["ticker"] for s in draft["satellites"]} == {"NVDA", "UNH"}
        assert not any(name == "created" for name, _ in events)
    finally:
        client.__exit__(None, None, None)


def test_propose_normalizes_weights_that_do_not_sum_to_one() -> None:
    # A small model routinely proposes weights that miss summing to 1 (here
    # 0.7 + 0.2 + 0.2 = 1.1). The shown draft must be rescaled to sum to 1 so
    # the recommendation is actually buildable.
    bad = csd.PortfolioDraft(
        name="AI Growth",
        initial_capital=100000,
        monthly_contribution=500,
        core_fund_ticker="IWDA.AS",
        core_weight=0.7,
        satellites=[{"ticker": "NVDA", "weight": 0.2}, {"ticker": "UNH", "weight": 0.2}],
    )
    answer = csd.Answer(text="Here is a portfolio.", action="propose", draft=bad)
    client = _client(ScriptedAgentLLM(in_scope=True, answers=[answer]))
    try:
        response = client.post("/api/portfolio-draft/chat", json={"message": "recommend one"})
        assert response.status_code == 200, response.text
        events = _events(response.text)
        draft = next(payload for name, payload in events if name == "answer")["draft"]
        assert isinstance(draft, dict)
        total = float(draft["core_weight"]) + sum(float(s["weight"]) for s in draft["satellites"])
        assert abs(total - 1.0) < 1e-6
    finally:
        client.__exit__(None, None, None)


def test_propose_resolves_a_core_ticker_missing_its_exchange_suffix() -> None:
    # the model routinely drops the exchange suffix (IWDA for IWDA.AS); the
    # resolver must map it back to the real fund so "build it" doesn't fail with
    # "unknown fund".
    draft = csd.PortfolioDraft(
        name="Suffix Fix",
        initial_capital=10000,
        monthly_contribution=0,
        core_fund_ticker="IWDA",
        core_weight=0.6,
        satellites=[{"ticker": "NVDA", "weight": 0.2}, {"ticker": "UNH", "weight": 0.2}],
    )
    answer = csd.Answer(text="Here is a portfolio.", action="propose", draft=draft)
    client = _client(ScriptedAgentLLM(in_scope=True, answers=[answer]))
    try:
        response = client.post("/api/portfolio-draft/chat", json={"message": "recommend one"})
        assert response.status_code == 200, response.text
        events = _events(response.text)
        emitted = next(payload for name, payload in events if name == "answer")
        assert emitted["action"] == "propose"
        assert isinstance(emitted["draft"], dict)
        assert emitted["draft"]["core_fund_ticker"] == "IWDA.AS"
    finally:
        client.__exit__(None, None, None)


def test_propose_with_unknown_core_falls_back_to_chat() -> None:
    # a core the DB has no fund for must not be offered as a broken build.
    draft = csd.PortfolioDraft(
        name="Bad Core",
        initial_capital=10000,
        monthly_contribution=0,
        core_fund_ticker="ZZZZ",
        core_weight=1.0,
        satellites=[],
    )
    answer = csd.Answer(text="Here.", action="propose", draft=draft)
    client = _client(ScriptedAgentLLM(in_scope=True, answers=[answer]))
    try:
        response = client.post("/api/portfolio-draft/chat", json={"message": "recommend one"})
        assert response.status_code == 200, response.text
        events = _events(response.text)
        emitted = next(payload for name, payload in events if name == "answer")
        assert emitted["action"] == "chat"
        assert emitted["draft"] is None
    finally:
        client.__exit__(None, None, None)


def test_propose_with_all_satellites_unresolvable_falls_back_to_chat() -> None:
    # gemma sometimes fills satellites with company names ("NVIDIA CORP") or a
    # second ETF — none resolve to a tradable stock. They must NOT be silently
    # dropped into a misleading 100%-core proposal; fall back to chat + say why.
    draft = csd.PortfolioDraft(
        name="Names Not Tickers",
        initial_capital=10000,
        monthly_contribution=0,
        core_fund_ticker="IWDA.AS",
        core_weight=0.35,
        satellites=[
            {"ticker": "ZZZZ", "weight": 0.35},
            {"ticker": "NONEXISTENT HOLDINGS CO", "weight": 0.30},
        ],
    )
    answer = csd.Answer(text="Here is a portfolio.", action="propose", draft=draft)
    client = _client(ScriptedAgentLLM(in_scope=True, answers=[answer]))
    try:
        response = client.post("/api/portfolio-draft/chat", json={"message": "recommend one"})
        assert response.status_code == 200, response.text
        emitted = next(p for n, p in _events(response.text) if n == "answer")
        assert emitted["action"] == "chat"
        assert emitted["draft"] is None
        assert "ZZZZ" in str(emitted["text"])
    finally:
        client.__exit__(None, None, None)


def test_propose_drops_one_unresolvable_satellite_with_a_note() -> None:
    draft = csd.PortfolioDraft(
        name="One Bad Sat",
        initial_capital=10000,
        monthly_contribution=0,
        core_fund_ticker="IWDA.AS",
        core_weight=0.6,
        satellites=[{"ticker": "NVDA", "weight": 0.2}, {"ticker": "ZZZZ", "weight": 0.2}],
    )
    answer = csd.Answer(text="Here.", action="propose", draft=draft)
    client = _client(ScriptedAgentLLM(in_scope=True, answers=[answer]))
    try:
        response = client.post("/api/portfolio-draft/chat", json={"message": "recommend one"})
        assert response.status_code == 200, response.text
        emitted = next(p for n, p in _events(response.text) if n == "answer")
        assert emitted["action"] == "propose"
        assert isinstance(emitted["draft"], dict)
        assert {s["ticker"] for s in emitted["draft"]["satellites"]} == {"NVDA"}
        assert "ZZZZ" in str(emitted["text"])
    finally:
        client.__exit__(None, None, None)


def test_propose_resolves_a_satellite_by_company_name() -> None:
    # gemma sometimes emits a company name instead of a ticker; resolve it
    # against instruments.name so the holding is not dropped.
    draft = csd.PortfolioDraft(
        name="By Name",
        initial_capital=10000,
        monthly_contribution=0,
        core_fund_ticker="IWDA.AS",
        core_weight=0.6,
        satellites=[{"ticker": "NVIDIA", "weight": 0.2}, {"ticker": "UnitedHealth", "weight": 0.2}],
    )
    answer = csd.Answer(text="Here.", action="propose", draft=draft)
    client = _client(ScriptedAgentLLM(in_scope=True, answers=[answer]))
    try:
        response = client.post("/api/portfolio-draft/chat", json={"message": "recommend one"})
        assert response.status_code == 200, response.text
        emitted = next(p for n, p in _events(response.text) if n == "answer")
        assert emitted["action"] == "propose"
        assert isinstance(emitted["draft"], dict)
        assert {s["ticker"] for s in emitted["draft"]["satellites"]} == {"NVDA", "UNH"}
    finally:
        client.__exit__(None, None, None)


def test_confirm_creates_portfolio_in_database() -> None:
    answer = csd.Answer(text="Building it now.", action="create")
    client = _client(ScriptedAgentLLM(in_scope=True, answers=[answer]))
    try:
        response = client.post(
            "/api/portfolio-draft/chat",
            json={
                "message": "yes, build it",
                "history": [{"role": "assistant", "content": "here is a proposal"}],
                "proposed_draft": _VALID_DRAFT.model_dump(),
            },
        )
        assert response.status_code == 200, response.text
        events = _events(response.text)
        created = next(payload for name, payload in events if name == "created")
        portfolio_id = created["portfolio_id"]
        assert isinstance(portfolio_id, int)

        listed = client.get("/api/portfolios").json()
        assert any(p["id"] == portfolio_id and p["name"] == "AI Growth" for p in listed)
    finally:
        client.__exit__(None, None, None)


def test_confirm_flag_creates_deterministically_without_llm() -> None:
    # the "build it" button sends confirm=true; creation must happen even when
    # the LLM would never emit a create action (here it only chats)
    chatty = csd.Answer(text="Sure, what else?", action="chat")
    llm = ScriptedAgentLLM(in_scope=True, answers=[chatty])
    client = _client(llm)
    try:
        response = client.post(
            "/api/portfolio-draft/chat",
            json={
                "message": "Yes, build this portfolio.",
                "proposed_draft": _VALID_DRAFT.model_dump(),
                "confirm": True,
            },
        )
        assert response.status_code == 200, response.text
        events = _events(response.text)
        assert any(name == "created" for name, _ in events)
        assert llm.calls == 0  # confirm short-circuits before any LLM turn
    finally:
        client.__exit__(None, None, None)


def test_create_action_without_prior_proposal_does_not_create() -> None:
    answer = csd.Answer(text="Building it now.", action="create")
    client = _client(ScriptedAgentLLM(in_scope=True, answers=[answer]))
    try:
        response = client.post(
            "/api/portfolio-draft/chat",
            json={"message": "just make one", "proposed_draft": None},
        )
        assert response.status_code == 200
        events = _events(response.text)
        assert not any(name == "created" for name, _ in events)
    finally:
        client.__exit__(None, None, None)


def test_confirm_with_weights_not_summing_to_one_errors() -> None:
    bad_draft = _VALID_DRAFT.model_copy(update={"satellites": [{"ticker": "NVDA", "weight": 0.1}]})
    answer = csd.Answer(text="Building it now.", action="create")
    client = _client(ScriptedAgentLLM(in_scope=True, answers=[answer]))
    try:
        response = client.post(
            "/api/portfolio-draft/chat",
            json={"message": "yes", "proposed_draft": bad_draft.model_dump()},
        )
        assert response.status_code == 200
        events = _events(response.text)
        error = next(payload for name, payload in events if name == "error")
        assert "weights" in str(error["message"]).lower()
        assert not any(name == "created" for name, _ in events)
    finally:
        client.__exit__(None, None, None)


def test_confirm_with_unknown_ticker_errors() -> None:
    bad_draft = _VALID_DRAFT.model_copy(update={"satellites": [{"ticker": "ZZZZ", "weight": 0.4}]})
    answer = csd.Answer(text="Building it now.", action="create")
    client = _client(ScriptedAgentLLM(in_scope=True, answers=[answer]))
    try:
        response = client.post(
            "/api/portfolio-draft/chat",
            json={"message": "yes", "proposed_draft": bad_draft.model_dump()},
        )
        assert response.status_code == 200
        events = _events(response.text)
        error = next(payload for name, payload in events if name == "error")
        assert "ZZZZ" in str(error["message"])
        assert not any(name == "created" for name, _ in events)
    finally:
        client.__exit__(None, None, None)
