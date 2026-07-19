"""Portfolio health-radar (integration): the six on-the-fly criterion scores.

Seeds fact + portfolio tables with the admin asyncpg pattern (see
tests/test_integration_rls.py) and asserts on the health block returned by
AnalyticsService.summary(). Auto-skips when Postgres is down (`just stack-up`).
"""

import datetime
import math
import statistics
from collections.abc import AsyncIterator

import asyncpg
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

import coresat.db as csdb
import coresat.services as css

ADMIN_DSN = "postgresql://postgres:postgres@localhost:5434/coresat_test"
APP_URL = "postgresql+asyncpg://coresat_app:coresat_app@localhost:5434/coresat_test"

# All seeded rows carry this ticker prefix so the fact tables (shared, read-all)
# can be cleaned between runs without touching other suites' fixtures.
_PREFIX = "HLTH"
# One deterministic close series, ~70 points (above the _VOL_MIN_OBS=60 floor),
# shared by every priced look-through instrument (the core basket's underlyings
# AND the satellites). When every leg tracks the same series the full-portfolio
# combined return equals that single series, so the expected volatility is
# exactly its annualised stdev.
_N = 70
_CLOSES = tuple(100.0 + (index % 7) - (index % 3) for index in range(_N))
_DATES = tuple(datetime.date(2025, 9, 1) + datetime.timedelta(days=index) for index in range(_N))
_ACQUIRED = _DATES[-1]  # == last price date => entry == latest => value == invested


def _expected_volatility() -> float:
    returns = [_CLOSES[i] / _CLOSES[i - 1] - 1 for i in range(1, len(_CLOSES))]
    return statistics.stdev(returns) * math.sqrt(252)


async def _admin_or_skip() -> asyncpg.Connection:
    try:
        return await asyncpg.connect(ADMIN_DSN, timeout=3)
    except OSError, asyncpg.PostgresError, TimeoutError:
        pytest.skip("postgres not running — just stack-up")


async def _reset(admin: asyncpg.Connection) -> None:
    await csdb.apply_schema(ADMIN_DSN)
    await admin.execute(
        "TRUNCATE positions, sleeves, chat_messages, llm_audit_log, portfolios "
        "RESTART IDENTITY CASCADE"
    )
    await admin.execute(f"DELETE FROM fund_holdings WHERE ticker LIKE '{_PREFIX}%'")
    await admin.execute(
        f"DELETE FROM prices_daily WHERE instrument_id IN "
        f"(SELECT id FROM instruments WHERE ticker LIKE '{_PREFIX}%')"
    )
    await admin.execute(f"DELETE FROM funds WHERE ticker LIKE '{_PREFIX}%'")
    await admin.execute(f"DELETE FROM instruments WHERE ticker LIKE '{_PREFIX}%'")


async def _seed_prices(admin: asyncpg.Connection, instrument_id: int) -> None:
    # ON CONFLICT: an instrument may be seeded from both the core basket and a
    # satellite (the deliberate overlap), so prices must not double-insert.
    await admin.executemany(
        "INSERT INTO prices_daily (instrument_id, date, close) VALUES ($1, $2, $3) "
        "ON CONFLICT DO NOTHING",
        [(instrument_id, date, close) for date, close in zip(_DATES, _CLOSES, strict=True)],
    )


async def _ensure_instrument(
    admin: asyncpg.Connection, ticker: str, type_: str, sector: str | None, region: str | None
) -> int:
    instrument_id = await admin.fetchval(
        "INSERT INTO instruments (ticker, name, type, sector, region) VALUES ($1, $2, $3, $4, $5) "
        "ON CONFLICT (ticker) DO NOTHING RETURNING id",
        ticker,
        f"Name {ticker}",
        type_,
        sector,
        region,
    )
    if instrument_id is None:
        instrument_id = await admin.fetchval("SELECT id FROM instruments WHERE ticker = $1", ticker)
    return int(instrument_id)


async def _seed_core_fund(admin: asyncpg.Connection, with_prices: bool) -> int:
    """Create the core ETF (fund + holdings). The ETF instrument itself has no
    price series — real ETFs never do — so look-through volatility must price
    the basket's underlyings. Returns fund id."""
    await admin.execute(
        f"INSERT INTO instruments (ticker, name, type) "
        f"VALUES ('{_PREFIX}C', 'Core ETF', 'etf') ON CONFLICT (ticker) DO NOTHING"
    )
    fund_id = await admin.fetchval(
        f"INSERT INTO funds (ticker, name, ter, cagr_10y) "
        f"VALUES ('{_PREFIX}C', 'Core World Fund', 0.20, 0.10) RETURNING id"
    )
    # region mix: us 0.7 / europe 0.3. '{_PREFIX}A' also overlaps satellite A.
    await admin.execute(
        "INSERT INTO fund_holdings (fund_id, ticker, name, weight, sector, region) VALUES "
        f"($1, '{_PREFIX}A', 'Holding A', 0.7, 'Information Technology', 'us'), "
        f"($1, '{_PREFIX}E', 'Holding E', 0.3, 'Health Care', 'europe')",
        fund_id,
    )
    # The basket's underlyings are the priced names look-through volatility uses.
    if with_prices:
        for suffix, sector, region in (("A", "Healthcare", "us"), ("E", "Health Care", "europe")):
            instrument_id = await _ensure_instrument(
                admin, f"{_PREFIX}{suffix}", "stock", sector, region
            )
            await _seed_prices(admin, instrument_id)
    return fund_id


async def _seed_satellite(
    admin: asyncpg.Connection,
    suffix: str,
    sector: str,
    region: str,
    with_prices: bool,
) -> int:
    instrument_id = await _ensure_instrument(admin, f"{_PREFIX}{suffix}", "stock", sector, region)
    if with_prices:
        await _seed_prices(admin, instrument_id)
    return instrument_id


async def _make_portfolio(admin: asyncpg.Connection, name: str) -> int:
    return await admin.fetchval(
        "INSERT INTO portfolios (name, initial_capital, monthly_contribution) "
        "VALUES ($1, 10000, 100) RETURNING id",
        name,
    )


async def _add_sleeve(
    admin: asyncpg.Connection, portfolio_id: int, kind: str, target: float
) -> int:
    return await admin.fetchval(
        "INSERT INTO sleeves (portfolio_id, kind, target_weight) VALUES ($1, $2, $3) RETURNING id",
        portfolio_id,
        kind,
        target,
    )


async def _add_core_position(
    admin: asyncpg.Connection, portfolio_id: int, sleeve_id: int, fund_id: int, invested: float
) -> None:
    await admin.execute(
        "INSERT INTO positions (portfolio_id, sleeve_id, fund_id, target_weight, "
        "invested_amount, acquired_at) VALUES ($1, $2, $3, 1.0, $4, $5)",
        portfolio_id,
        sleeve_id,
        fund_id,
        invested,
        _ACQUIRED,
    )


async def _add_satellite_position(
    admin: asyncpg.Connection,
    portfolio_id: int,
    sleeve_id: int,
    instrument_id: int,
    invested: float,
) -> None:
    await admin.execute(
        "INSERT INTO positions (portfolio_id, sleeve_id, instrument_id, target_weight, "
        "invested_amount, acquired_at) VALUES ($1, $2, $3, 0.5, $4, $5)",
        portfolio_id,
        sleeve_id,
        instrument_id,
        invested,
        _ACQUIRED,
    )


@pytest.fixture
async def app_engine() -> AsyncIterator[AsyncEngine]:
    engine = csdb.create_engine(APP_URL)
    yield engine
    await engine.dispose()


async def _seed_full(admin: asyncpg.Connection, with_prices: bool) -> int:
    """Core 6000 (ter 0.20%), sat A 2000 (healthcare/us, overlaps core), sat B 2000 (tech/europe)."""
    fund_id = await _seed_core_fund(admin, with_prices)
    sat_a = await _seed_satellite(admin, "A", "Healthcare", "us", with_prices)
    sat_b = await _seed_satellite(admin, "B", "tech", "europe", with_prices)
    portfolio_id = await _make_portfolio(admin, "Full")
    core_sleeve = await _add_sleeve(admin, portfolio_id, "core", 0.65)
    sat_sleeve = await _add_sleeve(admin, portfolio_id, "satellite", 0.35)
    await _add_core_position(admin, portfolio_id, core_sleeve, fund_id, 6000)
    await _add_satellite_position(admin, portfolio_id, sat_sleeve, sat_a, 2000)
    await _add_satellite_position(admin, portfolio_id, sat_sleeve, sat_b, 2000)
    return portfolio_id


def _by_key(summary: object) -> dict[str, object]:
    criteria = summary.health.criteria  # type: ignore[attr-defined]
    return {c.key: c for c in criteria}


async def test_full_portfolio_scores_each_criterion(app_engine: AsyncEngine) -> None:
    admin = await _admin_or_skip()
    await _reset(admin)
    portfolio_id = await _seed_full(admin, with_prices=True)
    await admin.close()

    summary = await css.AnalyticsService(app_engine).summary(portfolio_id)
    assert summary is not None
    crit = _by_key(summary)

    # allocation_discipline: core value-weight 0.6 vs target 0.65 -> |drift| 0.05; sat 0.4 vs 0.35.
    assert crit["allocation_discipline"].value == pytest.approx(0.05)
    assert crit["allocation_discipline"].score == pytest.approx(5.0)
    assert crit["allocation_discipline"].green is False

    # sector_concentration (look-through): the core basket's IT holding is the
    # largest single sector across the whole portfolio — 0.6 core * 0.7 = 0.42.
    assert crit["sector_concentration"].value == pytest.approx(0.42)
    assert crit["sector_concentration"].score == pytest.approx(4.5)

    # region_concentration: us = sat A 0.2 + core 0.6*0.7 = 0.62 (max region).
    assert crit["region_concentration"].value == pytest.approx(0.62)
    assert crit["region_concentration"].score == pytest.approx(3.6)

    # cost_efficiency: 0.6 * 0.20%/100 = 0.0012.
    assert crit["cost_efficiency"].value == pytest.approx(0.0012)
    assert crit["cost_efficiency"].score == pytest.approx(9.6)

    # overlap: satellite A ticker is a core holding -> its 0.2 whole-portfolio weight.
    assert crit["overlap"].value == pytest.approx(0.2)
    assert crit["overlap"].score == pytest.approx(10.0 / 3.0)

    # volatility: identical series across all three holdings -> combined return == the series.
    assert crit["volatility"].value == pytest.approx(_expected_volatility())
    assert crit["volatility"].score is not None

    scores = [c.score for c in summary.health.criteria if c.score is not None]
    assert summary.health.headline == round(sum(scores) / len(scores), 1)
    assert len(scores) == 6


async def test_volatility_unavailable_without_prices(app_engine: AsyncEngine) -> None:
    admin = await _admin_or_skip()
    await _reset(admin)
    portfolio_id = await _seed_full(admin, with_prices=False)
    await admin.close()

    summary = await css.AnalyticsService(app_engine).summary(portfolio_id)
    assert summary is not None
    crit = _by_key(summary)

    # No prices for any holding -> volatility is unavailable, not zero.
    assert crit["volatility"].value is None
    assert crit["volatility"].score is None
    assert crit["volatility"].green is False

    # ... and it is excluded from the headline mean (only the other five count).
    scores = [c.score for c in summary.health.criteria if c.score is not None]
    assert len(scores) == 5
    assert summary.health.headline == round(sum(scores) / len(scores), 1)


async def test_empty_portfolio_is_perfect_and_does_not_crash(app_engine: AsyncEngine) -> None:
    admin = await _admin_or_skip()
    await _reset(admin)
    # A portfolio with zero positions -> zero invested; every concentration metric is 0.
    portfolio_id = await _make_portfolio(admin, "Empty")
    await admin.close()

    summary = await css.AnalyticsService(app_engine).summary(portfolio_id)
    assert summary is not None
    crit = _by_key(summary)

    for key in (
        "allocation_discipline",
        "sector_concentration",
        "region_concentration",
        "cost_efficiency",
        "overlap",
    ):
        assert crit[key].value == pytest.approx(0.0), key
        assert crit[key].score == pytest.approx(10.0), key
        assert crit[key].green is True, key
    assert crit["volatility"].value is None
    assert summary.health.headline == pytest.approx(10.0)


async def test_core_only_portfolio_single_sleeve(app_engine: AsyncEngine) -> None:
    admin = await _admin_or_skip()
    await _reset(admin)
    fund_id = await _seed_core_fund(admin, with_prices=True)
    portfolio_id = await _make_portfolio(admin, "CoreOnly")
    core_sleeve = await _add_sleeve(admin, portfolio_id, "core", 1.0)
    await _add_core_position(admin, portfolio_id, core_sleeve, fund_id, 10000)
    await admin.close()

    summary = await css.AnalyticsService(app_engine).summary(portfolio_id)
    assert summary is not None
    crit = _by_key(summary)

    # Look-through: the core basket's largest sector (IT 0.7) is now the sector
    # concentration — a sector-heavy core is penalised, not scored perfect.
    assert crit["sector_concentration"].value == pytest.approx(0.7)
    assert crit["sector_concentration"].score == pytest.approx(0.0)
    assert crit["overlap"].value == pytest.approx(0.0)
    assert crit["overlap"].score == pytest.approx(10.0)
    # region: whole 1.0 core weight through the us 0.7 / europe 0.3 mix -> max 0.7.
    assert crit["region_concentration"].value == pytest.approx(0.7)
    assert crit["region_concentration"].score == pytest.approx(2.0)
    # cost: full weight on the 0.20% fund -> 0.002.
    assert crit["cost_efficiency"].value == pytest.approx(0.002)
    assert crit["cost_efficiency"].score == pytest.approx(8.0)
    # allocation: single sleeve at target 1.0 -> no drift.
    assert crit["allocation_discipline"].value == pytest.approx(0.0)
    assert crit["volatility"].value == pytest.approx(_expected_volatility())


async def test_nonexistent_portfolio_returns_none(app_engine: AsyncEngine) -> None:
    admin = await _admin_or_skip()
    await _reset(admin)
    await admin.close()
    # No scope will ever match id 999999 -> RLS yields no portfolio row.
    summary = await css.AnalyticsService(app_engine).summary(999999)
    assert summary is None
