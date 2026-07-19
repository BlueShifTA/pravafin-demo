"""Portfolio + analytics API (integration): wizard create, summary math, market data.

Deterministic: uses synthetic instruments/prices seeded by the fixture, not live data.
Auto-skips when Postgres is down (`just stack-up` to run).
"""

import asyncio
from collections.abc import Iterator

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


async def _prepare() -> None:
    conn = await _connect_or_skip()
    await csdb.apply_schema(ADMIN_DSN)
    await conn.execute("DELETE FROM fund_holdings WHERE ticker LIKE 'TST%'")
    await conn.execute(
        "DELETE FROM fundamentals WHERE instrument_id IN "
        "(SELECT id FROM instruments WHERE ticker LIKE 'TST%')"
    )
    await conn.execute(
        "DELETE FROM prices_daily WHERE instrument_id IN "
        "(SELECT id FROM instruments WHERE ticker LIKE 'TST%')"
    )
    await conn.execute(
        "DELETE FROM positions WHERE instrument_id IN "
        "(SELECT id FROM instruments WHERE ticker LIKE 'TST%') OR fund_id IN "
        "(SELECT id FROM funds WHERE ticker LIKE 'TST%')"
    )
    await conn.execute("DELETE FROM instruments WHERE ticker LIKE 'TST%'")
    await conn.execute("DELETE FROM funds WHERE ticker LIKE 'TST%'")
    stock = await conn.fetchval(
        "INSERT INTO instruments (ticker, name, type, sector) "
        "VALUES ('TSTP', 'Test Pharma', 'stock', 'healthcare') RETURNING id"
    )
    etf_instrument = await conn.fetchval(
        "INSERT INTO instruments (ticker, name, type) "
        "VALUES ('TSTF', 'Test Fund Tracker', 'etf') RETURNING id"
    )
    await conn.execute(
        "INSERT INTO funds (ticker, name, ter, cagr_10y) "
        "VALUES ('TSTF', 'Test World Fund', 0.5, 0.10)"
    )
    etf2_instrument = await conn.fetchval(
        "INSERT INTO instruments (ticker, name, type) "
        "VALUES ('TSTG', 'Test Fund Two Tracker', 'etf') RETURNING id"
    )
    await conn.execute(
        "INSERT INTO funds (ticker, name, ter, cagr_10y) "
        "VALUES ('TSTG', 'Test Bond Fund', 0.2, 0.06)"
    )
    await conn.execute(
        "INSERT INTO prices_daily (instrument_id, date, open, high, low, close, volume) VALUES "
        "($1, '2024-01-02', 99, 101, 98, 100, 1000), "
        "($1, '2026-01-02', 109, 111, 108, 110, 1000), "
        "($2, '2024-01-02', 50, 50, 50, 50, 1000), "
        "($2, '2026-01-02', 55, 55, 55, 55, 1000), "
        "($3, '2024-01-02', 20, 20, 20, 20, 1000), "
        "($3, '2026-01-02', 22, 22, 22, 22, 1000)",
        stock,
        etf_instrument,
        etf2_instrument,
    )
    await conn.execute(
        "INSERT INTO fundamentals (instrument_id, market_cap, ebit, nwc, ppe_net, cash, "
        "total_debt, cagr_10y) VALUES ($1, 1000, 500, 100, 100, 50, 100, 0.15)",
        stock,
    )
    await conn.close()


@pytest.fixture
def client() -> Iterator[TestClient]:
    asyncio.run(_prepare())
    with TestClient(app) as test_client:
        yield test_client


def _create_portfolio(client: TestClient) -> int:
    response = client.post(
        "/api/portfolios",
        json={
            "name": "Demo",
            "initial_capital": 10_000,
            "monthly_contribution": 100,
            "core": [{"fund_ticker": "TSTF", "weight": 0.8}],
            "satellites": [{"ticker": "TSTP", "weight": 0.2, "acquired_at": "2024-01-02"}],
        },
    )
    assert response.status_code == 201, response.text
    portfolio_id: int = response.json()["id"]
    return portfolio_id


def test_wizard_creates_portfolio_and_lists_it(client: TestClient) -> None:
    portfolio_id = _create_portfolio(client)
    listing = client.get("/api/portfolios").json()
    assert any(item["id"] == portfolio_id for item in listing)


def test_summary_values_positions_from_prices(client: TestClient) -> None:
    portfolio_id = _create_portfolio(client)
    summary = client.get(f"/api/portfolios/{portfolio_id}/summary").json()
    # satellite: invested 2000 @ close 100 on 2024-01-02 -> 20 units -> 20 x 110 = 2200
    satellite = next(s for s in summary["allocation"] if s["label"] == "TSTP")
    assert satellite["value"] == pytest.approx(2200)
    # core: invested 8000, acquired today -> entry = latest close -> value stays 8000
    core = next(s for s in summary["allocation"] if s["label"] == "TSTF")
    assert core["value"] == pytest.approx(8000)
    assert summary["current_value"] == pytest.approx(10_200)
    # per-year projection points (1..20) so the chart has one per year, with bands
    horizons = {p["years"] for p in summary["projections"]}
    assert horizons == set(range(1, 21))
    ten = next(p for p in summary["projections"] if p["years"] == 10)
    assert ten["low"] < ten["expected"] < ten["high"]


def test_wizard_creates_multiple_core_etfs(client: TestClient) -> None:
    response = client.post(
        "/api/portfolios",
        json={
            "name": "Two-core",
            "initial_capital": 10_000,
            "monthly_contribution": 0,
            "core": [
                {"fund_ticker": "TSTF", "weight": 0.5},
                {"fund_ticker": "TSTG", "weight": 0.3},
            ],
            "satellites": [{"ticker": "TSTP", "weight": 0.2, "acquired_at": "2024-01-02"}],
        },
    )
    assert response.status_code == 201, response.text
    portfolio_id = response.json()["id"]
    summary = client.get(f"/api/portfolios/{portfolio_id}/summary").json()
    core_labels = {s["label"] for s in summary["allocation"] if s["kind"] == "core"}
    assert core_labels == {"TSTF", "TSTG"}
    core_drift = next(d for d in summary["drift"] if d["kind"] == "core")
    assert core_drift["target_weight"] == pytest.approx(0.8)


def test_unknown_ticker_in_wizard_is_422(client: TestClient) -> None:
    response = client.post(
        "/api/portfolios",
        json={
            "name": "Bad",
            "initial_capital": 1000,
            "monthly_contribution": 0,
            "core": [{"fund_ticker": "NOFUND", "weight": 0.8}],
            "satellites": [],
        },
    )
    assert response.status_code == 422


def test_candles_endpoint_returns_ohlcv(client: TestClient) -> None:
    bars = client.get("/api/market/candles/TSTP").json()
    assert len(bars) == 2
    assert bars[0]["close"] == 100
    assert bars[1]["high"] == 111


def test_candles_resampled_by_month_buckets_ohlcv(client: TestClient) -> None:
    # interval=1M resamples daily bars into monthly buckets (open=first, high=max,
    # low=min, close=last, date=bucket start). TSTP's two bars fall in different
    # months, so each becomes one bucket carrying that day's OHLC.
    bars = client.get("/api/market/candles/TSTP", params={"interval": "1M"}).json()
    assert len(bars) == 2
    assert [b["date"] for b in bars] == ["2024-01-01", "2026-01-01"]
    assert [b["open"] for b in bars] == [99, 109]
    assert [b["high"] for b in bars] == [101, 111]
    assert [b["low"] for b in bars] == [98, 108]
    assert [b["close"] for b in bars] == [100, 110]


def test_screener_computes_magic_formula_on_the_fly(client: TestClient) -> None:
    rows = client.get("/api/market/screener").json()
    tstp = next(row for row in rows if row["ticker"] == "TSTP")
    # EV = 1000 + 100 - 50 = 1050 -> EY = 500/1050 ; ROIC = 500/(100+100)
    assert tstp["earnings_yield"] == pytest.approx(500 / 1050, rel=1e-6)
    assert tstp["roic"] == pytest.approx(2.5, rel=1e-6)
    assert isinstance(tstp["magic_rank"], int)


def test_ter_drag_compares_gross_and_net(client: TestClient) -> None:
    drag = client.get(
        "/api/market/ter-drag", params={"fund": "TSTF", "capital": 10_000, "years": 10}
    ).json()
    assert drag["gross_value"] == pytest.approx(10_000 * 1.10**10, rel=1e-9)
    assert drag["net_value"] == pytest.approx(10_000 * (1.10 - 0.005) ** 10, rel=1e-9)
    assert drag["drag"] == pytest.approx(drag["gross_value"] - drag["net_value"], rel=1e-9)


def test_ter_drag_returns_yearly_series(client: TestClient) -> None:
    drag = client.get(
        "/api/market/ter-drag", params={"fund": "TSTF", "capital": 10_000, "years": 10}
    ).json()
    series = drag["series"]
    assert len(series) == 11  # year 0 through year 10
    assert series[0] == {"year": 0, "gross_value": 10_000, "net_value": 10_000}
    assert series[-1]["year"] == 10
    assert series[-1]["gross_value"] == pytest.approx(drag["gross_value"], rel=1e-9)
    assert series[-1]["net_value"] == pytest.approx(drag["net_value"], rel=1e-9)
    assert all(point["net_value"] <= point["gross_value"] for point in series)
