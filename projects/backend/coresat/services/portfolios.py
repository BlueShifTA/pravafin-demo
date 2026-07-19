"""Portfolio creation and listing (wizard backend)."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

import coresat.db as csdb
import coresat.domain as csd


class UnknownTickerError(ValueError):
    """Requested fund/instrument ticker is not in the fact tables."""


class PortfolioService:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def list(self) -> list[csd.PortfolioListItem]:
        async with self._engine.connect() as conn:
            rows = await conn.execute(text("SELECT * FROM list_portfolios()"))
            return [csd.PortfolioListItem(**row) for row in rows.mappings()]

    async def create(self, spec: csd.PortfolioCreate) -> int:
        async with self._engine.begin() as conn:
            fund_id = (
                await conn.execute(
                    text("SELECT id FROM funds WHERE ticker = :ticker"),
                    {"ticker": spec.core.fund_ticker},
                )
            ).scalar()
            if fund_id is None:
                raise UnknownTickerError(f"unknown fund: {spec.core.fund_ticker}")
            tickers = [satellite.ticker for satellite in spec.satellites]
            instrument_ids: dict[str, int] = {}
            if tickers:
                rows = await conn.execute(
                    text("SELECT ticker, id FROM instruments WHERE ticker = ANY(:tickers)"),
                    {"tickers": tickers},
                )
                instrument_ids = {row.ticker: row.id for row in rows}
            missing = set(tickers) - set(instrument_ids)
            if missing:
                raise UnknownTickerError(f"unknown instruments: {sorted(missing)}")
            portfolio_id: int = (
                await conn.execute(
                    text("SELECT create_portfolio(:name, :capital, :monthly)"),
                    {
                        "name": spec.name,
                        "capital": spec.initial_capital,
                        "monthly": spec.monthly_contribution,
                    },
                )
            ).scalar_one()

        satellite_weight = sum(satellite.weight for satellite in spec.satellites)
        async with csdb.portfolio_scope(self._engine, portfolio_id) as conn:
            core_sleeve = (
                await conn.execute(
                    text(
                        "INSERT INTO sleeves (portfolio_id, kind, target_weight) "
                        "VALUES (:pid, 'core', :weight) RETURNING id"
                    ),
                    {"pid": portfolio_id, "weight": spec.core.weight},
                )
            ).scalar_one()
            satellite_sleeve = (
                await conn.execute(
                    text(
                        "INSERT INTO sleeves (portfolio_id, kind, target_weight) "
                        "VALUES (:pid, 'satellite', :weight) RETURNING id"
                    ),
                    {"pid": portfolio_id, "weight": satellite_weight},
                )
            ).scalar_one()
            await conn.execute(
                text(
                    "INSERT INTO positions (portfolio_id, sleeve_id, fund_id, target_weight, "
                    "invested_amount) VALUES (:pid, :sleeve, :fund, :weight, :invested)"
                ),
                {
                    "pid": portfolio_id,
                    "sleeve": core_sleeve,
                    "fund": fund_id,
                    "weight": spec.core.weight,
                    "invested": spec.initial_capital * spec.core.weight,
                },
            )
            for satellite in spec.satellites:
                await conn.execute(
                    text(
                        "INSERT INTO positions (portfolio_id, sleeve_id, instrument_id, "
                        "target_weight, invested_amount, acquired_at) VALUES "
                        "(:pid, :sleeve, :instrument, :weight, :invested, "
                        "COALESCE(:acquired, current_date))"
                    ),
                    {
                        "pid": portfolio_id,
                        "sleeve": satellite_sleeve,
                        "instrument": instrument_ids[satellite.ticker],
                        "weight": satellite.weight,
                        "invested": spec.initial_capital * satellite.weight,
                        "acquired": satellite.acquired_at,
                    },
                )
        return portfolio_id
