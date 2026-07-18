"""Typed ingestion records — contracts enforced at the trust boundary."""

import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class InstrumentRecord(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    ticker: str = Field(min_length=1)
    type: Literal["stock", "etf"]
    name: str | None = None
    sector: str | None = None
    industry: str | None = None


class PriceRecord(BaseModel):
    ticker: str = Field(min_length=1)
    date: datetime.date
    close: float
    open: float | None = None
    high: float | None = None
    low: float | None = None
    volume: int | None = None


class HoldingRecord(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    fund_ticker: str = Field(min_length=1)
    fund_name: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    name: str | None = None
    sector: str | None = None
    weight: float | None = None


class YearlyFinancialsRecord(BaseModel):
    ticker: str = Field(min_length=1)
    fy: int
    revenue: float | None = None
    net_income: float | None = None
    net_margin: float | None = None
    ocf: float | None = None
    capex: float | None = None
    fcf: float | None = None
    shares: float | None = None


class FundamentalsRecord(BaseModel):
    ticker: str = Field(min_length=1)
    name: str | None = None
    market_cap: float | None = None
    pe_trailing: float | None = None
    pe_forward: float | None = None
    revenue: float | None = None
    net_profit: float | None = None
    profit_margin: float | None = None
    roe: float | None = None
    dividend_yield: float | None = None
    beta: float | None = None
    price_to_book: float | None = None
    debt_to_equity: float | None = None
    free_cashflow: float | None = None
    cagr_5y: float | None = None
    cagr_10y: float | None = None
    ebit: float | None = None
    nwc: float | None = None
    ppe_net: float | None = None
    cash: float | None = None
    total_debt: float | None = None
    shares: float | None = None


class FundRecord(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    ticker: str = Field(min_length=1)
    name: str = Field(min_length=1)
    provider: str | None = None
    category: str | None = None
    currency: str | None = None
    fund_size: float | None = None
    ter: float | None = None
    dist_yield: float | None = None
    cagr_5y: float | None = None
    cagr_10y: float | None = None


class DocChunkRecord(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    source_doc: str = Field(min_length=1)
    doc_type: str = Field(min_length=1)
    page: int | None = None
    chunk_index: int
    text: str = Field(min_length=1)


class RejectedRow(BaseModel):
    row: dict[str, str | None]
    reason: str


class IngestReport(BaseModel):
    run_id: int | None
    source: str
    status: Literal["succeeded", "failed", "skipped"]
    rows_in: int
    rows_ok: int
    rows_quarantined: int
