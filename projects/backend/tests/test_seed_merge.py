"""Fundamentals merge (unit): valuation snapshot + latest-FY SEC inputs."""

import csv
import io

import coresat.services.ingestion as csi

STOCKS_CSV = b"""ticker,name,market_cap,pe_trailing,cagr_10y
NVDA,NVIDIA Corporation,3200000000000,55.2,0.62
KO,Coca-Cola,280000000000,24.1,0.08
"""

FINANCIALS_CSV = b"""ticker,fy,revenue,opex,net_income,net_margin,ocf,capex,fcf,ebit,assets_current,liabilities_current,nwc,ppe_net,cash,lt_debt,st_debt,equity,shares
NVDA,2024,60922000000,,29760000000,0.49,28090000000,,,32972000000,,,44309000000,3914000000,7280000000,8459000000,1250000000,,24660000000
NVDA,2026,130497000000,,72880000000,0.56,64089000000,,,81453000000,,,62079000000,6283000000,8589000000,8463000000,,,24400000000
KO,2025,47061000000,,10714000000,0.23,6805000000,,,11373000000,,,2245000000,9236000000,10828000000,36960000000,1050000000,,4302000000
"""


def test_merge_takes_latest_fiscal_year() -> None:
    merged = csi.merge_fundamentals(STOCKS_CSV, FINANCIALS_CSV).decode()
    header, *rows = merged.strip().splitlines()
    assert "ebit" in header and "nwc" in header and "market_cap" in header
    nvda = next(row for row in rows if row.startswith("NVDA"))
    assert "81453000000" in nvda  # FY2026 ebit, not FY2024
    assert "3200000000000" in nvda  # market cap kept from snapshot


def test_merge_sums_debt_components() -> None:
    merged = csi.merge_fundamentals(STOCKS_CSV, FINANCIALS_CSV).decode()
    ko = next(row for row in merged.splitlines() if row.startswith("KO"))
    assert "38010000000" in ko  # 36960000000 + 1050000000


def test_missing_financials_keeps_snapshot_row() -> None:
    merged = csi.merge_fundamentals(
        b"ticker,name,market_cap\nZZZT,No Financials Inc,5\n", FINANCIALS_CSV
    ).decode()
    assert any(row.startswith("ZZZT") for row in merged.splitlines())


def test_financials_only_ticker_gets_a_row() -> None:
    # AMD is in financials_10y but has no valuation snapshot row — it must still
    # get a fundamentals row (from its balance sheet) so the screener covers it.
    financials = (
        FINANCIALS_CSV
        + b"AMD,2025,,,,,,,,5000000000,,,1000000000,2000000000,3000000000,4000000000,500000000,,1600000000\n"
    )
    merged = csi.merge_fundamentals(STOCKS_CSV, financials).decode()
    amd = next((row for row in merged.splitlines() if row.startswith("AMD")), None)
    assert amd is not None
    assert "5000000000" in amd  # ebit carried from financials
    assert "4500000000" in amd  # total_debt = lt (4e9) + st (5e8)


def test_financials_only_ticker_carries_available_comparison_fields() -> None:
    financials = (
        FINANCIALS_CSV + b"AMD,2025,10000000000,,500000000,0.05,900000000,200000000,700000000,"
        b"800000000,,,1000000000,2000000000,3000000000,4000000000,500000000,"
        b"5000000000,1600000000\n"
    )

    merged = csi.merge_fundamentals(STOCKS_CSV, financials).decode()
    rows = list(csv.DictReader(io.StringIO(merged)))
    amd = next(row for row in rows if row["ticker"] == "AMD")

    assert amd["revenue"] == "10000000000"
    assert amd["net_profit"] == "500000000"
    assert amd["profit_margin"] == "0.05"
    assert amd["free_cashflow"] == "700000000"
