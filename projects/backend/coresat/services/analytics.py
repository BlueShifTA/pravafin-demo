"""Portfolio + market analytics — deterministic, computed on the fly from fact tables."""

import datetime
import math
import statistics
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import RowMapping, text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from coresat.db.session import portfolio_scope
from coresat.domain.portfolio import (
    AllocationSlice,
    CandleBar,
    FundRow,
    HealthCriterion,
    PortfolioHealth,
    PortfolioSummary,
    ProjectionOut,
    ScreenerRow,
    SleeveDrift,
    TerDrag,
    TerDragPoint,
    YearlyFinancials,
)
from coresat.services.projection import project

_HORIZONS = (10, 20)

# Health-radar anchors (g_good, g_bad) — lower raw metric is better for all six.
_ALLOC_GOOD, _ALLOC_BAD = 0.0, 0.10
_SECTOR_GOOD, _SECTOR_BAD = 0.20, 0.60
_REGION_GOOD, _REGION_BAD = 0.30, 0.80
_COST_GOOD, _COST_BAD = 0.001, 0.006
_OVERLAP_GOOD, _OVERLAP_BAD = 0.0, 0.30
_VOL_GOOD, _VOL_BAD = 0.12, 0.30
_TRADING_DAYS = 252
# Realized-volatility look-through window (calendar days ≈ 3y of trading) and the
# minimum aligned observations before a volatility estimate is trustworthy.
_VOL_WINDOW_DAYS = 1100
_VOL_MIN_OBS = 60


def _normalize(label: str | None) -> str:
    cleaned = (label or "").strip().lower()
    return cleaned or "unknown"


def _linear_score(value: float, g_good: float, g_bad: float) -> float:
    return max(0.0, min(10.0, 10.0 * (g_bad - value) / (g_bad - g_good)))


def _criterion(
    key: str, label: str, value: float | None, g_good: float, g_bad: float
) -> HealthCriterion:
    score = None if value is None else _linear_score(value, g_good, g_bad)
    green = value is not None and value <= g_good
    return HealthCriterion(key=key, label=label, value=value, score=score, green=green)


def _allocation_value(drift: Sequence[SleeveDrift]) -> float:
    return max((abs(item.drift) for item in drift), default=0.0)


def _sector_value(rows: Sequence[RowMapping]) -> float:
    satellites = [row for row in rows if row["kind"] == "satellite"]
    sat_invested = sum(float(row["invested_amount"]) for row in satellites)
    if sat_invested <= 0:
        return 0.0
    weights: dict[str, float] = {}
    for row in satellites:
        sector = _normalize(row["instrument_sector"])
        weights[sector] = weights.get(sector, 0.0) + float(row["invested_amount"]) / sat_invested
    return max(weights.values(), default=0.0)


def _region_value(
    rows: Sequence[RowMapping], holdings: Sequence[RowMapping], total_invested: float
) -> float:
    if total_invested <= 0:
        return 0.0
    holdings_by_fund: dict[int, list[RowMapping]] = {}
    for holding in holdings:
        holdings_by_fund.setdefault(int(holding["fund_id"]), []).append(holding)
    weights: dict[str, float] = {}
    for row in rows:
        share = float(row["invested_amount"]) / total_invested
        if row["fund_id"] is not None:
            fund_holdings = holdings_by_fund.get(int(row["fund_id"]), [])
            holdings_total = sum(float(h["weight"] or 0.0) for h in fund_holdings)
            if holdings_total > 0:
                for holding in fund_holdings:
                    region = _normalize(holding["region"])
                    fraction = float(holding["weight"] or 0.0) / holdings_total
                    weights[region] = weights.get(region, 0.0) + share * fraction
            else:
                weights["unknown"] = weights.get("unknown", 0.0) + share
        elif row["instrument_id"] is not None:
            region = _normalize(row["instrument_region"])
            weights[region] = weights.get(region, 0.0) + share
    return max(weights.values(), default=0.0)


def _cost_value(rows: Sequence[RowMapping], total_invested: float) -> float:
    if total_invested <= 0:
        return 0.0
    total = 0.0
    for row in rows:
        if row["fund_id"] is not None and row["fund_ter"] is not None:
            share = float(row["invested_amount"]) / total_invested
            total += share * float(row["fund_ter"]) / 100.0
    return total


def _overlap_value(
    rows: Sequence[RowMapping], holdings: Sequence[RowMapping], total_invested: float
) -> float:
    if total_invested <= 0:
        return 0.0
    core_tickers = {str(holding["ticker"]).strip().upper() for holding in holdings}
    total = 0.0
    for row in rows:
        if row["kind"] == "satellite" and str(row["label"]).strip().upper() in core_tickers:
            total += float(row["invested_amount"]) / total_invested
    return total


@dataclass(frozen=True)
class _LookLeg:
    weight: float  # fraction of the whole portfolio (all legs sum to ~1)
    instrument_id: int | None
    beta: float | None


def _daily_returns(prices: Sequence[RowMapping]) -> dict[int, dict[datetime.date, float]]:
    closes: dict[int, list[tuple[datetime.date, float]]] = {}
    for price in prices:
        closes.setdefault(int(price["instrument_id"]), []).append(
            (price["date"], float(price["close"]))
        )
    returns: dict[int, dict[datetime.date, float]] = {}
    for instrument_id, series in closes.items():
        series.sort(key=lambda point: point[0])
        daily: dict[datetime.date, float] = {}
        for index in range(1, len(series)):
            prev_close = series[index - 1][1]
            if prev_close:
                daily[series[index][0]] = series[index][1] / prev_close - 1
        if daily:
            returns[instrument_id] = daily
    return returns


def _lookthrough_legs(rows: Sequence[RowMapping], holdings: Sequence[RowMapping]) -> list[_LookLeg]:
    # Decompose the portfolio into single-name legs whose weights sum to 1: a
    # core fund position becomes its fund_holdings basket (leg weight = the
    # fund's portfolio weight * the holding's share of the basket), so the
    # diversified core counts toward risk instead of being dropped. Satellites
    # are one leg each. Basket shares are normalised within the fund, which is
    # scale-agnostic — real iShares holdings are percent-scale, the test
    # fixtures fraction-scale.
    total = sum(float(row["invested_amount"]) for row in rows)
    if total <= 0:
        return []
    holdings_by_fund: dict[int, list[RowMapping]] = {}
    for holding in holdings:
        holdings_by_fund.setdefault(int(holding["fund_id"]), []).append(holding)
    legs: list[_LookLeg] = []
    for row in rows:
        weight = float(row["invested_amount"]) / total
        if row["fund_id"] is not None:
            fund_holdings = holdings_by_fund.get(int(row["fund_id"]), [])
            basket = sum(float(holding["weight"] or 0.0) for holding in fund_holdings)
            if basket <= 0:
                legs.append(_LookLeg(weight=weight, instrument_id=None, beta=None))
                continue
            for holding in fund_holdings:
                fraction = float(holding["weight"] or 0.0) / basket
                instrument_id = holding["instrument_id"]
                legs.append(
                    _LookLeg(
                        weight=weight * fraction,
                        instrument_id=int(instrument_id) if instrument_id is not None else None,
                        beta=float(holding["beta"]) if holding["beta"] is not None else None,
                    )
                )
        elif row["instrument_id"] is not None:
            legs.append(
                _LookLeg(
                    weight=weight,
                    instrument_id=int(row["instrument_id"]),
                    beta=float(row["stock_beta"]) if row["stock_beta"] is not None else None,
                )
            )
    return legs


def _volatility_value(legs: Sequence[_LookLeg], prices: Sequence[RowMapping]) -> float | None:
    # Full-portfolio realized volatility over the look-through legs. Priced legs
    # (a real instrument with a price series) contribute their own daily return;
    # unpriced legs (foreign names, an unpriced core) keep their weight and
    # contribute beta * the market factor built from the priced legs — so a name
    # is never dropped and the surviving weights are never rescaled to 100%
    # (the exact bug that let the diversified 60% core vanish from the number).
    returns = _daily_returns(prices)
    priced_weight: dict[int, float] = {}
    unpriced_beta_weight = 0.0
    for leg in legs:
        if leg.instrument_id is not None and leg.instrument_id in returns:
            priced_weight[leg.instrument_id] = (
                priced_weight.get(leg.instrument_id, 0.0) + leg.weight
            )
        else:
            unpriced_beta_weight += leg.weight * (leg.beta if leg.beta is not None else 1.0)
    if not priced_weight:
        return None
    # Per-date weighted return of the priced sub-portfolio; a name absent on a
    # given day just does not contribute that day (robust to a single missing
    # print across a 100+ name basket, unlike a zero-tolerance date intersection).
    dates: set[datetime.date] = set()
    for instrument_id in priced_weight:
        dates |= set(returns[instrument_id])
    combined: list[float] = []
    for day in sorted(dates):
        priced_return = 0.0
        present_weight = 0.0
        for instrument_id, weight in priced_weight.items():
            daily = returns[instrument_id].get(day)
            if daily is not None:
                priced_return += weight * daily
                present_weight += weight
        if present_weight <= 0:
            continue
        market_factor = priced_return / present_weight
        combined.append(priced_return + market_factor * unpriced_beta_weight)
    if len(combined) < _VOL_MIN_OBS:
        return None
    return statistics.stdev(combined) * math.sqrt(_TRADING_DAYS)


def _compute_health(
    rows: Sequence[RowMapping],
    holdings: Sequence[RowMapping],
    prices: Sequence[RowMapping],
    drift: Sequence[SleeveDrift],
) -> PortfolioHealth:
    total_invested = sum(float(row["invested_amount"]) for row in rows)
    criteria = [
        _criterion(
            "allocation_discipline",
            "Allocation discipline",
            _allocation_value(drift),
            _ALLOC_GOOD,
            _ALLOC_BAD,
        ),
        _criterion(
            "sector_concentration",
            "Sector concentration",
            _sector_value(rows),
            _SECTOR_GOOD,
            _SECTOR_BAD,
        ),
        _criterion(
            "region_concentration",
            "Region concentration",
            _region_value(rows, holdings, total_invested),
            _REGION_GOOD,
            _REGION_BAD,
        ),
        _criterion(
            "cost_efficiency",
            "Cost efficiency",
            _cost_value(rows, total_invested),
            _COST_GOOD,
            _COST_BAD,
        ),
        _criterion(
            "overlap",
            "Core/satellite overlap",
            _overlap_value(rows, holdings, total_invested),
            _OVERLAP_GOOD,
            _OVERLAP_BAD,
        ),
        _criterion(
            "volatility",
            "Volatility",
            _volatility_value(_lookthrough_legs(rows, holdings), prices),
            _VOL_GOOD,
            _VOL_BAD,
        ),
    ]
    scores = [criterion.score for criterion in criteria if criterion.score is not None]
    headline = round(sum(scores) / len(scores), 1) if scores else 0.0
    return PortfolioHealth(headline=headline, criteria=criteria)


_POSITIONS_SQL = """
SELECT
    s.kind,
    s.target_weight AS sleeve_target,
    pos.invested_amount,
    pos.instrument_id,
    pos.fund_id,
    fi.id        AS core_instrument_id,
    i.sector     AS instrument_sector,
    i.region     AS instrument_region,
    COALESCE(i.ticker, fd.ticker) AS label,
    entry.close  AS entry_close,
    latest.close AS latest_close,
    fu.beta      AS stock_beta,
    fu.cagr_10y  AS stock_cagr,
    fd.cagr_10y  AS fund_cagr,
    fd.ter       AS fund_ter
FROM positions pos
JOIN sleeves s        ON s.id = pos.sleeve_id
LEFT JOIN instruments i  ON i.id = pos.instrument_id
LEFT JOIN funds fd       ON fd.id = pos.fund_id
LEFT JOIN instruments fi ON fi.ticker = fd.ticker
LEFT JOIN fundamentals fu ON fu.instrument_id = pos.instrument_id
LEFT JOIN LATERAL (
    SELECT close FROM prices_daily
    WHERE instrument_id = COALESCE(pos.instrument_id, fi.id) AND date <= pos.acquired_at
    ORDER BY date DESC LIMIT 1
) entry ON true
LEFT JOIN LATERAL (
    SELECT close FROM prices_daily
    WHERE instrument_id = COALESCE(pos.instrument_id, fi.id)
    ORDER BY date DESC LIMIT 1
) latest ON true
"""

_SCREENER_SQL = """
WITH base AS (
    SELECT i.ticker, i.name, i.sector, f.market_cap, f.pe_trailing, f.cagr_10y,
           f.ebit / NULLIF(f.market_cap + COALESCE(f.total_debt, 0) - COALESCE(f.cash, 0), 0)
               AS earnings_yield,
           f.ebit / NULLIF(f.nwc + f.ppe_net, 0) AS roic
    FROM fundamentals f
    JOIN instruments i ON i.id = f.instrument_id
    WHERE f.ebit IS NOT NULL AND f.market_cap IS NOT NULL
),
ranked AS (
    SELECT *,
           RANK() OVER (ORDER BY earnings_yield DESC)
         + RANK() OVER (ORDER BY roic DESC) AS rank_sum
    FROM base
    WHERE earnings_yield IS NOT NULL AND roic IS NOT NULL AND roic > 0
)
SELECT ticker, name, sector, market_cap, pe_trailing, cagr_10y, earnings_yield, roic,
       CAST(RANK() OVER (ORDER BY rank_sum) AS int) AS magic_rank
FROM ranked
ORDER BY magic_rank
LIMIT :limit
"""


class AnalyticsService:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def summary(self, portfolio_id: int) -> PortfolioSummary | None:
        async with portfolio_scope(self._engine, portfolio_id) as conn:
            portfolio = (
                (
                    await conn.execute(
                        text(
                            "SELECT name, initial_capital, monthly_contribution "
                            "FROM portfolios WHERE id = :pid"
                        ),
                        {"pid": portfolio_id},
                    )
                )
                .mappings()
                .first()
            )
            if portfolio is None:
                return None
            rows = (await conn.execute(text(_POSITIONS_SQL))).mappings().all()
            core_fund_ids = [int(row["fund_id"]) for row in rows if row["fund_id"] is not None]
            holdings = await self._fetch_core_holdings(conn, core_fund_ids)
            # Volatility is computed on the full look-through set: satellite stocks
            # plus every priced underlying of the core basket, so the diversified
            # core is part of the risk number instead of being dropped.
            price_ids = {
                int(row["instrument_id"]) for row in rows if row["instrument_id"] is not None
            }
            price_ids |= {
                int(holding["instrument_id"])
                for holding in holdings
                if holding["instrument_id"] is not None
            }
            prices = await self._fetch_prices(conn, sorted(price_ids))

        allocation: list[AllocationSlice] = []
        weighted_rate = 0.0
        for row in rows:
            invested = float(row["invested_amount"])
            entry, latest = row["entry_close"], row["latest_close"]
            value = invested * float(latest) / float(entry) if entry and latest else invested
            allocation.append(
                AllocationSlice(
                    label=row["label"], kind=row["kind"], invested=invested, value=value, weight=0.0
                )
            )
        total = sum(item.value for item in allocation)
        invested_total = sum(item.invested for item in allocation)
        allocation = [
            item.model_copy(update={"weight": item.value / total if total else 0.0})
            for item in allocation
        ]

        # sleeve-weighted growth rate: stock CAGR, or fund CAGR net of TER (ter is in %)
        for item, row in zip(allocation, rows, strict=True):
            rate = row["stock_cagr"]
            if rate is None and row["fund_cagr"] is not None:
                rate = float(row["fund_cagr"]) - float(row["fund_ter"] or 0) / 100
            weighted_rate += item.weight * float(rate or 0)

        targets: dict[str, float] = {}
        actuals: dict[str, float] = {}
        for item, row in zip(allocation, rows, strict=True):
            targets[item.kind] = float(row["sleeve_target"])
            actuals[item.kind] = actuals.get(item.kind, 0.0) + item.weight
        drift = [
            SleeveDrift(
                kind=kind,
                target_weight=targets[kind],
                actual_weight=actual,
                drift=actual - targets[kind],
            )
            for kind, actual in actuals.items()
        ]

        projections = [
            ProjectionOut(
                years=result.years,
                annual_rate=result.annual_rate,
                expected=result.expected,
                low=result.low,
                high=result.high,
            )
            for result in (
                project(
                    capital=total,
                    monthly_contribution=float(portfolio["monthly_contribution"]),
                    annual_rate=weighted_rate,
                    years=years,
                )
                for years in _HORIZONS
            )
        ]
        return PortfolioSummary(
            portfolio_id=portfolio_id,
            name=portfolio["name"],
            initial_capital=float(portfolio["initial_capital"]),
            monthly_contribution=float(portfolio["monthly_contribution"]),
            invested_total=invested_total,
            current_value=total,
            allocation=allocation,
            drift=drift,
            projections=projections,
            health=_compute_health(rows, holdings, prices, drift),
        )

    async def _fetch_core_holdings(
        self, conn: AsyncConnection, fund_ids: list[int]
    ) -> list[RowMapping]:
        if not fund_ids:
            return []
        result = await conn.execute(
            text(
                "SELECT fh.fund_id, fh.ticker, fh.region, fh.weight, "
                "i.id AS instrument_id, fu.beta "
                "FROM fund_holdings fh "
                "LEFT JOIN instruments i ON upper(trim(i.ticker)) = upper(trim(fh.ticker)) "
                "LEFT JOIN fundamentals fu ON fu.instrument_id = i.id "
                "WHERE fh.fund_id = ANY(:ids)"
            ),
            {"ids": fund_ids},
        )
        return list(result.mappings().all())

    async def _fetch_prices(
        self, conn: AsyncConnection, instrument_ids: list[int]
    ) -> list[RowMapping]:
        if not instrument_ids:
            return []
        result = await conn.execute(
            text(
                "SELECT instrument_id, date, close FROM prices_daily "
                "WHERE instrument_id = ANY(:ids) AND date >= "
                "(SELECT max(date) FROM prices_daily WHERE instrument_id = ANY(:ids)) "
                "- CAST(:window AS integer) "
                "ORDER BY instrument_id, date"
            ),
            {"ids": instrument_ids, "window": _VOL_WINDOW_DAYS},
        )
        return list(result.mappings().all())

    async def candles(self, ticker: str, days: int | None) -> list[CandleBar]:
        async with self._engine.connect() as conn:
            rows = await conn.execute(
                text(
                    "SELECT date, open, high, low, close, volume FROM prices_daily p "
                    "JOIN instruments i ON i.id = p.instrument_id WHERE i.ticker = :ticker "
                    "AND (CAST(:days AS int) IS NULL OR p.date >= current_date - CAST(:days AS int)) "
                    "ORDER BY p.date"
                ),
                {"ticker": ticker, "days": days},
            )
            return [CandleBar(**row) for row in rows.mappings()]

    async def yearly_financials(self, ticker: str) -> list[YearlyFinancials]:
        async with self._engine.connect() as conn:
            rows = (
                await conn.execute(
                    text(
                        "SELECT fy, revenue, net_income, net_margin, ocf, capex, fcf, shares "
                        "FROM financials_yearly f JOIN instruments i ON i.id = f.instrument_id "
                        "WHERE i.ticker = :ticker ORDER BY fy"
                    ),
                    {"ticker": ticker},
                )
            ).mappings()
            return [
                YearlyFinancials(
                    fy=row["fy"],
                    revenue=row["revenue"],
                    net_income=row["net_income"],
                    net_margin=row["net_margin"],
                    ocf=row["ocf"],
                    capex=row["capex"],
                    fcf=row["fcf"],
                    cf_per_share=(
                        float(row["ocf"]) / float(row["shares"])
                        if row["ocf"] is not None and row["shares"]
                        else None
                    ),
                )
                for row in rows
            ]

    async def screener(self, limit: int) -> list[ScreenerRow]:
        async with self._engine.connect() as conn:
            rows = await conn.execute(text(_SCREENER_SQL), {"limit": limit})
            return [ScreenerRow(**row) for row in rows.mappings()]

    async def funds(self) -> list[FundRow]:
        async with self._engine.connect() as conn:
            rows = await conn.execute(
                text(
                    "SELECT ticker, name, provider, currency, fund_size, ter, dist_yield, "
                    "cagr_5y, cagr_10y FROM funds WHERE valid_to IS NULL ORDER BY ticker"
                )
            )
            return [FundRow(**row) for row in rows.mappings()]

    async def compare_funds(self, tickers: Sequence[str]) -> list[FundRow]:
        async with self._engine.connect() as conn:
            rows = await conn.execute(
                text(
                    "SELECT ticker, name, provider, currency, fund_size, ter, dist_yield, "
                    "cagr_5y, cagr_10y FROM funds "
                    "WHERE valid_to IS NULL AND ticker = ANY(:tickers) ORDER BY ticker"
                ),
                {"tickers": list(tickers)},
            )
            return [FundRow(**row) for row in rows.mappings()]

    async def ter_drag(self, fund_ticker: str, capital: float, years: int) -> TerDrag | None:
        async with self._engine.connect() as conn:
            fund = (
                (
                    await conn.execute(
                        text("SELECT ter, cagr_10y FROM funds WHERE ticker = :ticker"),
                        {"ticker": fund_ticker},
                    )
                )
                .mappings()
                .first()
            )
        if fund is None or fund["cagr_10y"] is None:
            return None
        ter = float(fund["ter"] or 0)
        rate = float(fund["cagr_10y"])
        gross = capital * (1 + rate) ** years
        net = capital * (1 + rate - ter / 100) ** years
        series = [
            TerDragPoint(
                year=year,
                gross_value=capital * (1 + rate) ** year,
                net_value=capital * (1 + rate - ter / 100) ** year,
            )
            for year in range(years + 1)
        ]
        return TerDrag(
            fund_ticker=fund_ticker,
            ter=ter,
            cagr_10y=rate,
            years=years,
            capital=capital,
            gross_value=gross,
            net_value=net,
            drag=gross - net,
            series=series,
        )
