"""Source adapters: one class per feed, ~30 lines each. New source = new class + registry entry."""

import csv
import io
from collections.abc import Sequence
from typing import Protocol

from pydantic import BaseModel, ValidationError

from coresat.domain.ingestion import (
    FundamentalsRecord,
    FundRecord,
    HoldingRecord,
    InstrumentRecord,
    PriceRecord,
    RejectedRow,
    YearlyFinancialsRecord,
)

ParseResult = tuple[Sequence[BaseModel], list[RejectedRow]]


class SourceAdapter(Protocol):
    """Parses a raw payload into validated records plus rejects."""

    name: str
    version: str

    def parse(self, payload: bytes, source_ref: str | None, /) -> ParseResult: ...


def _reason(error: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in err['loc'])}: {err['msg']}" for err in error.errors()
    )


def _clean(row: dict[str, str | None]) -> dict[str, str | None]:
    return {
        (key or "").strip(): (value.strip() if value is not None and value.strip() else None)
        for key, value in row.items()
    }


def _number(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.replace(",", "").replace('"', "")
    # yfinance exports write literal nan/inf — treat as missing, they would
    # otherwise become NaN::numeric and break JSON serialization downstream
    if cleaned.lower().lstrip("+-") in ("", "nan", "inf", "infinity"):
        return None
    return cleaned


class UniverseCsvAdapter:
    name = "universe_csv"
    version = "1"

    def parse(self, payload: bytes, _source_ref: str | None, /) -> ParseResult:
        valid: list[BaseModel] = []
        rejects: list[RejectedRow] = []
        for raw in csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))):
            row = _clean(raw)
            try:
                valid.append(
                    InstrumentRecord(
                        ticker=row.get("ticker") or "",
                        type=row.get("type") or "",  # type: ignore[arg-type]
                        name=row.get("name") or row.get("ticker"),
                        sector=row.get("sector"),
                        industry=row.get("industry"),
                    )
                )
            except ValidationError as error:
                rejects.append(RejectedRow(row=row, reason=_reason(error)))
        return valid, rejects


class DailyPricesCsvAdapter:
    """yfinance `to_csv` layout: 3 header lines (Price…, Ticker…, Date…), then rows."""

    name = "daily_prices_csv"
    version = "1"

    def parse(self, payload: bytes, source_ref: str | None, /) -> ParseResult:
        lines = payload.decode("utf-8-sig").splitlines()
        if lines and lines[0].startswith("Date,"):
            # flat Ticker().history() export — ticker not in file, must come from caller
            if not source_ref:
                raise ValueError("flat daily CSV requires source_ref = ticker")
            columns = [column.strip().lower() for column in lines[0].split(",")]
            ticker = source_ref
            data_lines = lines[1:]
        elif len(lines) >= 4 and lines[0].startswith("Price"):
            columns = [column.strip().lower() for column in lines[0].split(",")]
            ticker = lines[1].split(",")[1].strip()
            data_lines = lines[3:]
        else:
            raise ValueError("unrecognised daily prices CSV layout")
        valid: list[BaseModel] = []
        rejects: list[RejectedRow] = []
        for cells in csv.reader(data_lines):
            if not cells or not any(cells):
                continue
            # flat exports carry tz-aware timestamps ("2024-01-02 00:00:00-05:00") — keep the date
            row: dict[str, str | None] = {"ticker": ticker, "date": cells[0].split(" ")[0] or None}
            for index, field in enumerate(columns[1:], start=1):
                row[field] = _number(cells[index]) if index < len(cells) else None
            volume = row.get("volume")
            try:
                valid.append(
                    PriceRecord(
                        ticker=ticker,
                        date=row.get("date") or "",  # type: ignore[arg-type]
                        close=row.get("close") or "",  # type: ignore[arg-type]
                        open=row.get("open"),  # type: ignore[arg-type]
                        high=row.get("high"),  # type: ignore[arg-type]
                        low=row.get("low"),  # type: ignore[arg-type]
                        volume=int(float(volume)) if volume else None,
                    )
                )
            except (ValidationError, ValueError) as error:
                reason = _reason(error) if isinstance(error, ValidationError) else str(error)
                rejects.append(RejectedRow(row=row, reason=reason))
        return valid, rejects


class ISharesHoldingsCsvAdapter:
    """iShares export: BOM + quoted preamble lines, real header starts at 'Ticker,'."""

    name = "ishares_holdings_csv"
    version = "1"

    def parse(self, payload: bytes, source_ref: str | None, /) -> ParseResult:
        if not source_ref:
            raise ValueError("ishares_holdings_csv requires source_ref = fund ticker")
        lines = payload.decode("utf-8-sig").lstrip("﻿").splitlines()
        fund_name = next(line for line in lines if line.strip()).strip().strip('"')
        header_index = next(index for index, line in enumerate(lines) if line.startswith("Ticker,"))
        valid: list[BaseModel] = []
        rejects: list[RejectedRow] = []
        for raw in csv.DictReader(io.StringIO("\n".join(lines[header_index:]))):
            row = _clean(raw)
            try:
                valid.append(
                    HoldingRecord(
                        fund_ticker=source_ref,
                        fund_name=fund_name,
                        ticker=row.get("Ticker") or "",
                        name=row.get("Name"),
                        sector=row.get("Sector"),
                        weight=_number(row.get("Weight (%)")),  # type: ignore[arg-type]
                    )
                )
            except ValidationError as error:
                rejects.append(RejectedRow(row=row, reason=_reason(error)))
        return valid, rejects


_FUNDAMENTALS_FIELDS = (
    "market_cap",
    "pe_trailing",
    "pe_forward",
    "revenue",
    "net_profit",
    "profit_margin",
    "roe",
    "dividend_yield",
    "beta",
    "price_to_book",
    "debt_to_equity",
    "free_cashflow",
    "cagr_5y",
    "cagr_10y",
    "ebit",
    "nwc",
    "ppe_net",
    "cash",
    "total_debt",
    "shares",
)


class FundamentalsCsvAdapter:
    # v3: loader backfills instrument names from the name column
    name = "fundamentals_csv"
    version = "3"

    def parse(self, payload: bytes, _source_ref: str | None, /) -> ParseResult:
        valid: list[BaseModel] = []
        rejects: list[RejectedRow] = []
        for raw in csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))):
            row = _clean(raw)
            numbers = {field: _number(row.get(field)) for field in _FUNDAMENTALS_FIELDS}
            try:
                valid.append(
                    FundamentalsRecord(
                        ticker=row.get("ticker") or "",
                        name=row.get("name"),
                        **numbers,  # type: ignore[arg-type]
                    )
                )
            except ValidationError as error:
                rejects.append(RejectedRow(row=row, reason=_reason(error)))
        return valid, rejects


_YEARLY_FINANCIALS_FIELDS = (
    "revenue",
    "net_income",
    "net_margin",
    "ocf",
    "capex",
    "fcf",
    "shares",
)


class FinancialsYearlyCsvAdapter:
    name = "financials_yearly_csv"
    version = "1"

    def parse(self, payload: bytes, _source_ref: str | None, /) -> ParseResult:
        valid: list[BaseModel] = []
        rejects: list[RejectedRow] = []
        for raw in csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))):
            row = _clean(raw)
            numbers = {field: _number(row.get(field)) for field in _YEARLY_FINANCIALS_FIELDS}
            try:
                valid.append(
                    YearlyFinancialsRecord(
                        ticker=row.get("ticker") or "",
                        fy=row.get("fy"),  # type: ignore[arg-type]
                        **numbers,  # type: ignore[arg-type]
                    )
                )
            except ValidationError as error:
                rejects.append(RejectedRow(row=row, reason=_reason(error)))
        return valid, rejects


class FundsCsvAdapter:
    name = "funds_csv"
    version = "2"

    def parse(self, payload: bytes, _source_ref: str | None, /) -> ParseResult:
        valid: list[BaseModel] = []
        rejects: list[RejectedRow] = []
        for raw in csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))):
            row = _clean(raw)
            try:
                valid.append(
                    FundRecord(
                        ticker=row.get("ticker") or "",
                        name=row.get("name") or "",
                        provider=row.get("provider"),
                        category=row.get("category"),
                        currency=row.get("currency"),
                        fund_size=_number(row.get("fund_size")),  # type: ignore[arg-type]
                        ter=_number(row.get("ter") or row.get("ter_alt")),  # type: ignore[arg-type]
                        dist_yield=_number(row.get("dist_yield")),  # type: ignore[arg-type]
                        cagr_5y=_number(row.get("cagr_5y")),  # type: ignore[arg-type]
                        cagr_10y=_number(row.get("cagr_10y")),  # type: ignore[arg-type]
                    )
                )
            except ValidationError as error:
                rejects.append(RejectedRow(row=row, reason=_reason(error)))
        return valid, rejects
