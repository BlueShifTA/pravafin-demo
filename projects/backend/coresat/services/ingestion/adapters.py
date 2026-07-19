"""Source adapters: one class per feed, ~30 lines each. New source = new class + registry entry."""

import csv
import io
import re
from collections.abc import Iterator, Sequence
from typing import Protocol

from pydantic import BaseModel, ValidationError
from pypdf import PdfReader
from pypdf.errors import PyPdfError

import coresat.domain as csd

# chunk target in characters; word-packed so a chunk never splits a token
_CHUNK_CHARS = 800

ParseResult = tuple[Sequence[BaseModel], list[csd.RejectedRow]]


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
        rejects: list[csd.RejectedRow] = []
        for raw in csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))):
            row = _clean(raw)
            try:
                valid.append(
                    csd.InstrumentRecord(
                        ticker=row.get("ticker") or "",
                        type=row.get("type") or "",  # type: ignore[arg-type]
                        name=row.get("name") or row.get("ticker"),
                        sector=row.get("sector"),
                        industry=row.get("industry"),
                    )
                )
            except ValidationError as error:
                rejects.append(csd.RejectedRow(row=row, reason=_reason(error)))
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
        rejects: list[csd.RejectedRow] = []
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
                    csd.PriceRecord(
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
                rejects.append(csd.RejectedRow(row=row, reason=reason))
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
        rejects: list[csd.RejectedRow] = []
        for raw in csv.DictReader(io.StringIO("\n".join(lines[header_index:]))):
            row = _clean(raw)
            try:
                valid.append(
                    csd.HoldingRecord(
                        fund_ticker=source_ref,
                        fund_name=fund_name,
                        ticker=row.get("Ticker") or "",
                        name=row.get("Name"),
                        sector=row.get("Sector"),
                        weight=_number(row.get("Weight (%)")),  # type: ignore[arg-type]
                    )
                )
            except ValidationError as error:
                rejects.append(csd.RejectedRow(row=row, reason=_reason(error)))
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
    # v4: sparse expanded-universe rows preserve previously populated values
    name = "fundamentals_csv"
    version = "4"

    def parse(self, payload: bytes, _source_ref: str | None, /) -> ParseResult:
        valid: list[BaseModel] = []
        rejects: list[csd.RejectedRow] = []
        for raw in csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))):
            row = _clean(raw)
            numbers = {field: _number(row.get(field)) for field in _FUNDAMENTALS_FIELDS}
            try:
                valid.append(
                    csd.FundamentalsRecord(
                        ticker=row.get("ticker") or "",
                        name=row.get("name"),
                        **numbers,  # type: ignore[arg-type]
                    )
                )
            except ValidationError as error:
                rejects.append(csd.RejectedRow(row=row, reason=_reason(error)))
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
        rejects: list[csd.RejectedRow] = []
        for raw in csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))):
            row = _clean(raw)
            numbers = {field: _number(row.get(field)) for field in _YEARLY_FINANCIALS_FIELDS}
            try:
                valid.append(
                    csd.YearlyFinancialsRecord(
                        ticker=row.get("ticker") or "",
                        fy=row.get("fy"),  # type: ignore[arg-type]
                        **numbers,  # type: ignore[arg-type]
                    )
                )
            except ValidationError as error:
                rejects.append(csd.RejectedRow(row=row, reason=_reason(error)))
        return valid, rejects


# The KIID/factsheet risk-reward ruler ("Potentially Lower Rewards 1 2 3 4 5 6 7
# Potentially Higher Rewards") is a graphic scale pypdf flattens into flat text.
# It carries no fund fact, crowds the real KEY BENEFITS/RISKS out of the top
# retrieved chunk, and the small synthesiser model parrots the labels back as if
# they were listed benefits. Drop the two fixed labels and the 1-7 scale before
# chunking. ponytail: the exact KIID label + the spaced 1-7 run only — never the
# bare words "higher risk", which appear in genuine risk prose.
_SRRI_RULER_RE = re.compile(r"Potentially (?:Lower|Higher) Rewards|(?<!\d)1 2 3 4 5 6 7(?!\d)")


def _strip_srri_ruler(text: str) -> str:
    return _SRRI_RULER_RE.sub(" ", text)


def _chunk_text(body: str) -> Iterator[str]:
    """Word-pack `body` into ~_CHUNK_CHARS pieces; whitespace-only yields nothing."""
    buffer: list[str] = []
    length = 0
    for word in body.split():
        if buffer and length + len(word) + 1 > _CHUNK_CHARS:
            yield " ".join(buffer)
            buffer, length = [], 0
        buffer.append(word)
        length += len(word) + 1
    if buffer:
        yield " ".join(buffer)


class PdfAdapter:
    """Per-page text extraction (pypdf) → word-packed chunks with page provenance."""

    name = "pdf"
    # v2: strip the KIID/factsheet SRRI risk-reward ruler before chunking. The
    # bump changes the ingest checksum so existing PDFs re-process on next ingest.
    version = "2"

    def parse(self, payload: bytes, source_ref: str | None, /) -> ParseResult:
        if not source_ref:
            raise ValueError("pdf requires source_ref = document name")
        # A corrupt upload must fail with a clear message like the CSV adapters,
        # not surface a raw pypdf error. Text extraction is eager here so the
        # failure is caught at the boundary, before any records are built.
        try:
            reader = PdfReader(io.BytesIO(payload))
            pages = [
                # pypdf can emit NUL bytes; Postgres text columns reject 0x00
                # (invalid in every encoding), so strip them, then drop the SRRI
                # risk-reward ruler, before chunking.
                (number, _strip_srri_ruler((page.extract_text() or "").replace("\x00", "")))
                for number, page in enumerate(reader.pages, start=1)
            ]
        except PyPdfError as error:
            raise ValueError(f"could not read PDF '{source_ref}': {error}") from error
        valid: list[BaseModel] = []
        rejects: list[csd.RejectedRow] = []
        index = 0
        for page_number, page_text in pages:
            for piece in _chunk_text(page_text):
                try:
                    valid.append(
                        csd.DocChunkRecord(
                            source_doc=source_ref,
                            doc_type="pdf",  # ponytail: one doc_type; split by kind if RAG grows
                            page=page_number,
                            chunk_index=index,
                            text=piece,
                        )
                    )
                    index += 1
                except ValidationError as error:
                    rejects.append(
                        csd.RejectedRow(row={"page": str(page_number)}, reason=_reason(error))
                    )
        return valid, rejects


class FundsCsvAdapter:
    name = "funds_csv"
    version = "2"

    def parse(self, payload: bytes, _source_ref: str | None, /) -> ParseResult:
        valid: list[BaseModel] = []
        rejects: list[csd.RejectedRow] = []
        for raw in csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))):
            row = _clean(raw)
            try:
                valid.append(
                    csd.FundRecord(
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
                rejects.append(csd.RejectedRow(row=row, reason=_reason(error)))
        return valid, rejects
