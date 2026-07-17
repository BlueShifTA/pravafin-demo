"""Loaders publish validated records into fact tables (idempotent upserts)."""

from collections.abc import Sequence
from typing import Protocol, cast

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from coresat.domain.ingestion import (
    FundamentalsRecord,
    FundRecord,
    HoldingRecord,
    InstrumentRecord,
    PriceRecord,
)

_CHUNK = 5000


class Loader(Protocol):
    async def __call__(self, conn: AsyncConnection, records: Sequence[BaseModel]) -> None: ...


async def _ensure_instruments(conn: AsyncConnection, tickers: set[str]) -> dict[str, int]:
    # ponytail: unknown tickers get a stock stub; a later universe_csv run upserts the truth
    await conn.execute(
        text(
            "INSERT INTO instruments (ticker, name, type) VALUES (:ticker, :ticker, 'stock') "
            "ON CONFLICT (ticker) DO NOTHING"
        ),
        [{"ticker": ticker} for ticker in sorted(tickers)],
    )
    rows = await conn.execute(
        text("SELECT ticker, id FROM instruments WHERE ticker = ANY(:tickers)"),
        {"tickers": list(tickers)},
    )
    return {row.ticker: row.id for row in rows}


async def load_instruments(conn: AsyncConnection, records: Sequence[BaseModel]) -> None:
    instruments = cast(Sequence[InstrumentRecord], records)
    await conn.execute(
        text(
            "INSERT INTO instruments (ticker, name, type, sector, industry) "
            "VALUES (:ticker, :name, :type, :sector, :industry) "
            "ON CONFLICT (ticker) DO UPDATE SET name = excluded.name, type = excluded.type, "
            "sector = excluded.sector, industry = excluded.industry"
        ),
        [record.model_dump() for record in instruments],
    )


async def load_prices(conn: AsyncConnection, records: Sequence[BaseModel]) -> None:
    prices = cast(Sequence[PriceRecord], records)
    ids = await _ensure_instruments(conn, {record.ticker for record in prices})
    rows = [
        {"instrument_id": ids[record.ticker], **record.model_dump(exclude={"ticker"})}
        for record in prices
    ]
    for start in range(0, len(rows), _CHUNK):
        await conn.execute(
            text(
                "INSERT INTO prices_daily (instrument_id, date, open, high, low, close, volume) "
                "VALUES (:instrument_id, :date, :open, :high, :low, :close, :volume) "
                "ON CONFLICT (instrument_id, date) DO NOTHING"
            ),
            rows[start : start + _CHUNK],
        )


async def load_holdings(conn: AsyncConnection, records: Sequence[BaseModel]) -> None:
    holdings = cast(Sequence[HoldingRecord], records)
    if not holdings:
        return
    fund_ticker = holdings[0].fund_ticker
    fund_id = (
        await conn.execute(
            text(
                "INSERT INTO funds (ticker, name) VALUES (:ticker, :name) "
                "ON CONFLICT (ticker) DO UPDATE SET name = excluded.name RETURNING id"
            ),
            {"ticker": fund_ticker, "name": holdings[0].fund_name},
        )
    ).scalar_one()
    await conn.execute(
        text(
            "INSERT INTO fund_holdings (fund_id, ticker, name, sector, weight) "
            "VALUES (:fund_id, :ticker, :name, :sector, :weight) "
            "ON CONFLICT (fund_id, ticker) DO UPDATE SET weight = excluded.weight, "
            "name = excluded.name, sector = excluded.sector"
        ),
        [
            {"fund_id": fund_id, **record.model_dump(exclude={"fund_ticker", "fund_name"})}
            for record in holdings
        ],
    )


_FUNDAMENTALS_COLUMNS = (
    "market_cap, pe_trailing, pe_forward, revenue, net_profit, profit_margin, roe, "
    "dividend_yield, beta, price_to_book, debt_to_equity, free_cashflow, cagr_5y, cagr_10y, "
    "ebit, nwc, ppe_net, cash, total_debt, shares"
)
_FUNDAMENTALS_VALUES = ", ".join(
    f":{column.strip()}" for column in _FUNDAMENTALS_COLUMNS.split(",")
)
_FUNDAMENTALS_UPDATES = ", ".join(
    f"{column.strip()} = excluded.{column.strip()}" for column in _FUNDAMENTALS_COLUMNS.split(",")
)


async def load_fundamentals(conn: AsyncConnection, records: Sequence[BaseModel]) -> None:
    fundamentals = cast(Sequence[FundamentalsRecord], records)
    ids = await _ensure_instruments(conn, {record.ticker for record in fundamentals})
    # backfill company names onto ticker-named stubs only — a universe_csv run
    # remains the authority and is never overwritten here
    named = [
        {"instrument_id": ids[record.ticker], "name": record.name}
        for record in fundamentals
        if record.name and record.name != record.ticker
    ]
    if named:
        await conn.execute(
            text("UPDATE instruments SET name = :name WHERE id = :instrument_id AND name = ticker"),
            named,
        )
    await conn.execute(
        text(
            f"INSERT INTO fundamentals (instrument_id, {_FUNDAMENTALS_COLUMNS}) "
            f"VALUES (:instrument_id, {_FUNDAMENTALS_VALUES}) "
            f"ON CONFLICT (instrument_id) DO UPDATE SET {_FUNDAMENTALS_UPDATES}"
        ),
        [
            {
                "instrument_id": ids[record.ticker],
                **record.model_dump(exclude={"ticker", "name"}),
            }
            for record in fundamentals
        ],
    )


async def load_funds(conn: AsyncConnection, records: Sequence[BaseModel]) -> None:
    funds = cast(Sequence[FundRecord], records)
    await conn.execute(
        text(
            "INSERT INTO funds (ticker, name, provider, category, currency, fund_size, ter, "
            "dist_yield, cagr_5y, cagr_10y) VALUES (:ticker, :name, :provider, :category, "
            ":currency, :fund_size, :ter, :dist_yield, :cagr_5y, :cagr_10y) "
            "ON CONFLICT (ticker) DO UPDATE SET name = excluded.name, ter = excluded.ter, "
            "provider = excluded.provider, category = excluded.category, "
            "currency = excluded.currency, fund_size = excluded.fund_size, "
            "dist_yield = excluded.dist_yield, cagr_5y = excluded.cagr_5y, "
            "cagr_10y = excluded.cagr_10y"
        ),
        [record.model_dump() for record in funds],
    )
