"""Adapter parsing (unit): typed records out, malformed rows rejected with reasons."""

from coresat.services.ingestion.adapters import (
    DailyPricesCsvAdapter,
    FundamentalsCsvAdapter,
    FundsCsvAdapter,
    ISharesHoldingsCsvAdapter,
    UniverseCsvAdapter,
)

UNIVERSE_CSV = b"""ticker,type,sector,industry
NVDA,stock,semiconductor,Semiconductors
IWDA.AS,etf,World core,
,stock,broken-row,
"""

YFINANCE_DAILY_CSV = b"""Price,Close,High,Low,Open,Volume
Ticker,NVDA,NVDA,NVDA,NVDA,NVDA
Date,,,,,
2024-01-02,48.17,49.10,47.50,48.00,411254000
2024-01-03,47.58,48.20,47.10,47.90,320896000
not-a-date,1,2,3,4,5
"""

ISHARES_CSV = (
    "﻿".encode()
    + b""""iShares Core MSCI World UCITS ETF"
"Fund Holdings as of","14-Jul-2026"
"Inception Date","25-Sep-2009"

Ticker,Name,Sector,Asset Class,Market Value,Weight (%),Notional Value,Shares,Price,Location,Exchange,Currency,FX Rate,Market Currency
NVDA,NVIDIA CORP,Information Technology,Equity,"5,872,410,110.53",5.61,"5,872,410,110.53","32,564,927.00",180.33,United States,NASDAQ,USD,1.00,USD
MSFT,MICROSOFT CORP,Information Technology,Equity,"4,101,220,010.11",3.92,"4,101,220,010.11","8,212,331.00",499.40,United States,NASDAQ,USD,1.00,USD
BADROW,Broken Corp,Tech,Equity,not-a-number,also-bad,x,y,z,US,N,USD,1.00,USD
"""
)

FUNDAMENTALS_CSV = b"""ticker,sector_demo,name,market_cap,pe_trailing,revenue,net_profit,profit_margin,roe,dividend_yield,beta,price_to_book,debt_to_equity,free_cashflow,cagr_5y,cagr_10y,ebit,nwc,ppe_net,cash,total_debt,shares
NVDA,semiconductor,NVIDIA Corporation,3200000000000,55.2,96307000000,53008000000,0.55,0.91,0.0003,1.68,50.1,17.2,39000000000,0.71,0.62,71033000000,52299000000,5200000000,25000000000,11056000000,24500000000
BROKEN,,Missing Numbers Inc,not-a-number,,,,,,,,,,,,,,,,,
"""

FUNDS_CSV = b"""ticker,name,provider,category,currency,fund_size,ter,ter_alt,dist_yield,beta_3y,cagr_5y,cagr_10y
IWDA.AS,iShares Core MSCI World UCITS ETF USD (Acc),BlackRock,,EUR,,0.2,,,,0.1226,0.1034
VOO,Vanguard S&P 500 ETF,Vanguard,Large Blend,USD,1300000000000,0.03,,,0.99,0.152,0.129
,No Ticker Fund,X,,USD,,,,,,,
"""


def test_universe_adapter_splits_valid_and_rejects() -> None:
    valid, rejects = UniverseCsvAdapter().parse(UNIVERSE_CSV, None)
    assert [r.ticker for r in valid] == ["NVDA", "IWDA.AS"]
    assert valid[0].type == "stock"
    assert len(rejects) == 1
    assert "ticker" in rejects[0].reason


def test_daily_prices_adapter_handles_yfinance_multiheader() -> None:
    valid, rejects = DailyPricesCsvAdapter().parse(YFINANCE_DAILY_CSV, None)
    assert len(valid) == 2
    assert valid[0].ticker == "NVDA"
    assert str(valid[0].date) == "2024-01-02"
    assert valid[0].close == 48.17
    assert len(rejects) == 1
    assert "date" in rejects[0].reason.lower()


FLAT_DAILY_CSV = b"""Date,Open,High,Low,Close,Volume,Dividends,Stock Splits
2024-01-02 00:00:00-05:00,290.10,295.00,289.50,294.30,1204500,0.0,0.0
2024-01-03 00:00:00-05:00,294.00,296.20,292.10,295.80,980400,0.0,0.0
"""


def test_daily_prices_adapter_handles_flat_history_format() -> None:
    valid, rejects = DailyPricesCsvAdapter().parse(FLAT_DAILY_CSV, "AON")
    assert len(valid) == 2
    assert valid[0].ticker == "AON"
    assert str(valid[0].date) == "2024-01-02"
    assert valid[0].close == 294.30
    assert rejects == []


def test_ishares_adapter_strips_bom_and_preamble() -> None:
    valid, rejects = ISharesHoldingsCsvAdapter().parse(ISHARES_CSV, "IWDA.AS")
    assert [h.ticker for h in valid] == ["NVDA", "MSFT"]
    assert valid[0].fund_ticker == "IWDA.AS"
    assert valid[0].fund_name == "iShares Core MSCI World UCITS ETF"
    assert valid[0].weight == 5.61
    assert len(rejects) == 1


def test_fundamentals_adapter_rejects_non_numeric() -> None:
    valid, rejects = FundamentalsCsvAdapter().parse(FUNDAMENTALS_CSV, None)
    assert len(valid) == 1
    assert valid[0].ticker == "NVDA"
    assert valid[0].ebit == 71033000000
    assert len(rejects) == 1


def test_funds_adapter_requires_ticker() -> None:
    valid, rejects = FundsCsvAdapter().parse(FUNDS_CSV, None)
    assert [f.ticker for f in valid] == ["IWDA.AS", "VOO"]
    assert valid[0].ter == 0.2
    assert len(rejects) == 1
