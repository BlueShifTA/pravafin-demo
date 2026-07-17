"""Portfolio + market analytics — deterministic, computed on the fly from fact tables."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from coresat.db.session import portfolio_scope
from coresat.domain.portfolio import (
    AllocationSlice,
    CandleBar,
    FundRow,
    PortfolioSummary,
    ProjectionOut,
    ScreenerRow,
    SleeveDrift,
    TerDrag,
    TerDragPoint,
)
from coresat.services.projection import project

_HORIZONS = (10, 20)

_POSITIONS_SQL = """
SELECT
    s.kind,
    s.target_weight AS sleeve_target,
    pos.invested_amount,
    COALESCE(i.ticker, fd.ticker) AS label,
    entry.close  AS entry_close,
    latest.close AS latest_close,
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
        )

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
