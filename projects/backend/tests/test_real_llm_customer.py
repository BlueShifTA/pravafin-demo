"""Real-LLM customer journeys: 20 people asking for a portfolio suggestion.

Gated behind CORESAT_REAL_LLM=1. Each test plays a potential customer sending a
realistic request to the draft agent (POST /api/portfolio-draft/chat) driven by
the real qwen model over a seeded universe. The invariants hold whatever qwen
words back: the agent must not error, must return a terminal answer, and any
portfolio it proposes must be grounded — every ticker it names has to exist in
the database, never invented. Skips without the env flag + Ollama + Postgres.
"""

import asyncio
import json
import os

import asyncpg
import pytest
from fastapi.testclient import TestClient

import coresat.db as csdb
from coresat.main import app

pytestmark = pytest.mark.skipif(
    os.environ.get("CORESAT_REAL_LLM") != "1",
    reason="real-LLM test: set CORESAT_REAL_LLM=1 with Ollama serving the configured model",
)

ADMIN_DSN = "postgresql://postgres:postgres@localhost:5434/coresat_test"

# (ticker, name, sector, market_cap, pe_trailing, roe, free_cashflow)
_STOCKS = [
    ("NVDA", "NVIDIA Corporation", "Information Technology", 3_400_000, 65.0, 0.90, 60_000),
    ("AAPL", "Apple Inc.", "Information Technology", 3_300_000, 34.0, 1.50, 100_000),
    ("MSFT", "Microsoft Corporation", "Information Technology", 3_100_000, 36.0, 0.39, 70_000),
    ("AVGO", "Broadcom Inc.", "Information Technology", 800_000, 40.0, 0.25, 18_000),
    ("UNH", "UnitedHealth Group", "Health Care", 500_000, 18.0, 0.25, 20_000),
    ("JNJ", "Johnson & Johnson", "Health Care", 400_000, 15.0, 0.23, 18_000),
    ("LLY", "Eli Lilly and Company", "Health Care", 700_000, 60.0, 0.55, 8_000),
    ("JPM", "JPMorgan Chase & Co.", "Financials", 650_000, 12.0, 0.17, 40_000),
    ("V", "Visa Inc.", "Financials", 550_000, 30.0, 0.45, 18_000),
    ("XOM", "Exxon Mobil Corporation", "Energy", 500_000, 13.0, 0.18, 30_000),
    ("CVX", "Chevron Corporation", "Energy", 300_000, 14.0, 0.12, 20_000),
    ("AMZN", "Amazon.com, Inc.", "Consumer Discretionary", 2_000_000, 42.0, 0.22, 35_000),
]
# (ticker, name, ter)
_FUNDS = [
    ("IWDA.AS", "iShares Core MSCI World UCITS ETF", 0.20),
    ("CSPX.L", "iShares Core S&P 500 UCITS ETF", 0.07),
]
_STOCK_TICKERS = {ticker for ticker, *_ in _STOCKS}
_FUND_TICKERS = {ticker for ticker, *_ in _FUNDS}


async def _seed() -> None:
    try:
        conn = await asyncpg.connect(ADMIN_DSN, timeout=3)
    except OSError, asyncpg.PostgresError, TimeoutError:
        pytest.skip("postgres not running — just stack-up")
    await csdb.apply_schema(ADMIN_DSN)
    await conn.execute("TRUNCATE positions, sleeves, portfolios RESTART IDENTITY CASCADE")
    for ticker, name, sector, market_cap, pe, roe, fcf in _STOCKS:
        await conn.execute(
            "INSERT INTO instruments (ticker, name, type, sector) VALUES ($1, $2, 'stock', $3) "
            "ON CONFLICT (ticker) DO UPDATE SET name = EXCLUDED.name, sector = EXCLUDED.sector",
            ticker,
            name,
            sector,
        )
        await conn.execute(
            "INSERT INTO fundamentals (instrument_id, market_cap, pe_trailing, roe, free_cashflow) "
            "SELECT id, $2, $3, $4, $5 FROM instruments WHERE ticker = $1 "
            "ON CONFLICT (instrument_id) DO UPDATE SET market_cap = EXCLUDED.market_cap, "
            "pe_trailing = EXCLUDED.pe_trailing, roe = EXCLUDED.roe, "
            "free_cashflow = EXCLUDED.free_cashflow",
            ticker,
            market_cap,
            pe,
            roe,
            fcf,
        )
    for ticker, name, ter in _FUNDS:
        await conn.execute(
            "INSERT INTO funds (ticker, name, ter) VALUES ($1, $2, $3) "
            "ON CONFLICT (ticker) DO UPDATE SET name = EXCLUDED.name, ter = EXCLUDED.ter",
            ticker,
            name,
            ter,
        )
    await conn.close()


@pytest.fixture(scope="module", autouse=True)
def seeded_universe() -> None:
    asyncio.run(_seed())


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


_CUSTOMERS = [
    "I have $10,000 to invest. Can you suggest a portfolio?",
    "I'm new to investing and want a simple core-satellite portfolio.",
    "Build me an aggressive tech-focused portfolio with $50,000.",
    "I want a conservative portfolio, mostly a world ETF.",
    "Suggest three satellite stocks in healthcare.",
    "What core ETF would you recommend for a beginner?",
    "I like NVIDIA and Apple. Build a portfolio around them.",
    "Give me a diversified portfolio with $25,000 and $500 a month.",
    "Which stocks in your database have the best fundamentals?",
    "I'm 30, moderate risk, and want growth. What do you suggest?",
    "Compare IWDA and CSPX as a core holding for me.",
    "What semiconductor stocks could I add as satellites?",
    "Recommend a portfolio focused on financial-sector stocks.",
    "I want 70% in a core ETF and 30% in individual stocks. Suggest picks.",
    "List the biggest companies I could invest in.",
    "Help me pick a core ETF and two energy stocks.",
    "I have $100k. Suggest a balanced core-satellite split.",
    "What are some high-ROE stocks for my satellite sleeve?",
    "Design a starter portfolio for someone investing $5,000.",
    "Suggest a tech-heavy portfolio and explain the picks.",
]


@pytest.mark.parametrize("message", _CUSTOMERS)
def test_customer_gets_a_grounded_response(message: str) -> None:
    client = TestClient(app)
    client.__enter__()
    try:
        response = client.post("/api/portfolio-draft/chat", json={"message": message})
        assert response.status_code == 200, response.text
        events = _events(response.text)
        names = [name for name, _ in events]
        assert "error" not in names, f"agent errored on {message!r}: {events}"
        assert events, f"no SSE events for {message!r}"
        terminal_name, terminal_payload = events[-1]
        assert terminal_name in {"answer", "created"}, f"unexpected terminal {terminal_name}"
        if terminal_name == "answer":
            assert terminal_payload.get("text"), f"empty answer for {message!r}"
            draft = terminal_payload.get("draft")
            if isinstance(draft, dict):
                # a proposal must be grounded: no invented tickers
                assert draft["core_fund_ticker"] in _FUND_TICKERS, (
                    f"invented core fund {draft['core_fund_ticker']!r}"
                )
                satellites = draft["satellites"]
                assert isinstance(satellites, list)
                for satellite in satellites:
                    assert satellite["ticker"] in _STOCK_TICKERS, (
                        f"invented satellite {satellite['ticker']!r}"
                    )
    finally:
        client.__exit__(None, None, None)
