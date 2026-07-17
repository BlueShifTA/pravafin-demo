"""Portfolio and analytics API models."""

import datetime

from pydantic import BaseModel, Field


class CorePick(BaseModel):
    fund_ticker: str = Field(min_length=1)
    weight: float = Field(gt=0, le=1)


class SatellitePick(BaseModel):
    ticker: str = Field(min_length=1)
    weight: float = Field(gt=0, le=1)
    acquired_at: datetime.date | None = None


class PortfolioCreate(BaseModel):
    name: str = Field(min_length=1)
    initial_capital: float = Field(gt=0)
    monthly_contribution: float = Field(ge=0)
    core: CorePick
    satellites: list[SatellitePick]


class PortfolioCreated(BaseModel):
    id: int


class PortfolioListItem(BaseModel):
    id: int
    name: str
    created_at: datetime.datetime


class AllocationSlice(BaseModel):
    label: str
    kind: str
    invested: float
    value: float
    weight: float


class SleeveDrift(BaseModel):
    kind: str
    target_weight: float
    actual_weight: float
    drift: float


class ProjectionOut(BaseModel):
    years: int
    annual_rate: float
    expected: float
    low: float
    high: float


class PortfolioSummary(BaseModel):
    portfolio_id: int
    name: str
    initial_capital: float
    monthly_contribution: float
    invested_total: float
    current_value: float
    allocation: list[AllocationSlice]
    drift: list[SleeveDrift]
    projections: list[ProjectionOut]


class CandleBar(BaseModel):
    date: datetime.date
    open: float | None
    high: float | None
    low: float | None
    close: float
    volume: int | None


class IndicatorPoint(BaseModel):
    date: datetime.date
    close: float
    sma_20: float | None
    sma_50: float | None
    sma_200: float | None
    ema_12: float | None
    ema_26: float | None
    rsi: float | None
    macd: float | None
    macd_signal: float | None


class ScreenerRow(BaseModel):
    ticker: str
    name: str | None
    sector: str | None
    market_cap: float | None
    pe_trailing: float | None
    cagr_10y: float | None
    earnings_yield: float
    roic: float
    magic_rank: int


class FundRow(BaseModel):
    ticker: str
    name: str
    provider: str | None
    currency: str | None
    fund_size: float | None
    ter: float | None
    dist_yield: float | None
    cagr_5y: float | None
    cagr_10y: float | None


class YearlyFinancials(BaseModel):
    fy: int
    revenue: float | None
    net_income: float | None
    net_margin: float | None
    ocf: float | None
    capex: float | None
    fcf: float | None
    cf_per_share: float | None


class TerDragPoint(BaseModel):
    year: int
    gross_value: float
    net_value: float


class TerDrag(BaseModel):
    fund_ticker: str
    ter: float
    cagr_10y: float
    years: int
    capital: float
    gross_value: float
    net_value: float
    drag: float
    series: list[TerDragPoint]
