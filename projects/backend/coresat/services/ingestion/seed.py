"""Seed the database from the etops-demo-data directory. Used by `just ingest-all`.

Thin walker over the tested pipeline — idempotent via run checksums, so
re-running only ingests what changed.
"""

import argparse
import asyncio
import csv
import io
import logging
import pathlib

from coresat.core.config import get_settings
from coresat.db.schema import apply_schema
from coresat.db.session import create_engine, to_async_url
from coresat.services.agent.retrieval import OllamaEmbedder
from coresat.services.ingestion.pipeline import IngestionPipeline, build_registry

log = logging.getLogger(__name__)

_HOLDINGS_FUNDS = {"iwda_holdings.csv": "IWDA.AS", "cspx_holdings.csv": "CSPX.L"}

_MAGIC_INPUT_COLUMNS = ("ebit", "nwc", "ppe_net", "cash", "shares")


def merge_fundamentals(stocks_csv: bytes, financials_csv: bytes) -> bytes:
    """Join valuation snapshot with latest-FY magic-formula inputs (per ticker).

    fundamentals_stocks.csv has valuation ratios but no balance-sheet items;
    financials_10y.csv (SEC XBRL) has them per fiscal year. total_debt = lt + st.
    """
    latest: dict[str, dict[str, str]] = {}
    for row in csv.DictReader(io.StringIO(financials_csv.decode("utf-8-sig"))):
        ticker = row["ticker"]
        if ticker not in latest or float(row["fy"]) > float(latest[ticker]["fy"]):
            latest[ticker] = row

    reader = csv.DictReader(io.StringIO(stocks_csv.decode("utf-8-sig")))
    base_fields = list(reader.fieldnames or [])
    extra_fields = [
        column for column in (*_MAGIC_INPUT_COLUMNS, "total_debt") if column not in base_fields
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=base_fields + extra_fields)
    writer.writeheader()
    for row in reader:
        financials = latest.get(row["ticker"], {})
        for column in _MAGIC_INPUT_COLUMNS:
            row.setdefault(column, financials.get(column, ""))
        lt_debt = financials.get("lt_debt") or "0"
        st_debt = financials.get("st_debt") or "0"
        total = float(lt_debt) + float(st_debt)
        row.setdefault("total_debt", str(int(total)) if total else "")
        writer.writerow(row)
    return output.getvalue().encode()


async def seed(data_dir: pathlib.Path) -> None:
    settings = get_settings()
    await apply_schema(settings.admin_database_url)
    engine = create_engine(to_async_url(settings.admin_database_url))
    embedder = OllamaEmbedder(settings.ollama_base_url, settings.ollama_embed_model)
    pipeline = IngestionPipeline(engine=engine, registry=build_registry(embedder))
    try:
        stocks_path = data_dir / "fundamentals_stocks.csv"
        financials_path = data_dir / "financials_10y.csv"
        fundamentals_payload = b""
        if stocks_path.exists():
            fundamentals_payload = (
                merge_fundamentals(stocks_path.read_bytes(), financials_path.read_bytes())
                if financials_path.exists()
                else stocks_path.read_bytes()
            )
        for name, adapter, payload in (
            ("universe_v2.csv", "universe_csv", None),
            ("fundamentals_stocks.csv", "fundamentals_csv", fundamentals_payload or None),
            ("financials_10y.csv", "financials_yearly_csv", None),
            ("fundamentals_etfs.csv", "funds_csv", None),
        ):
            path = data_dir / name
            if path.exists():
                report = await pipeline.run(adapter, payload or path.read_bytes(), None)
                log.info(
                    "%s: %s ok=%d q=%d",
                    name,
                    report.status,
                    report.rows_ok,
                    report.rows_quarantined,
                )
        for filename, fund_ticker in _HOLDINGS_FUNDS.items():
            path = data_dir / "funds" / filename
            if path.exists():
                report = await pipeline.run("ishares_holdings_csv", path.read_bytes(), fund_ticker)
                log.info(
                    "%s: %s ok=%d q=%d",
                    filename,
                    report.status,
                    report.rows_ok,
                    report.rows_quarantined,
                )
        price_files = sorted((data_dir / "prices" / "daily").glob("*/*.csv"))
        for index, path in enumerate(price_files, start=1):
            # stem is the ticker for flat-format files; multi-header files ignore it
            report = await pipeline.run("daily_prices_csv", path.read_bytes(), path.stem)
            if index % 50 == 0 or index == len(price_files):
                log.info(
                    "prices: %d/%d files (last: %s %s)",
                    index,
                    len(price_files),
                    path.stem,
                    report.status,
                )
        for path in sorted((data_dir / "docs").glob("*.pdf")):
            try:
                report = await pipeline.run("pdf", path.read_bytes(), path.name)
            except Exception as error:  # noqa: BLE001
                # Error boundary: one unreadable/quirky PDF (encryption, corruption,
                # embed hiccup) must not abort the whole batch — log it and move on.
                log.warning("%s: FAILED, skipped — %s", path.name, error)
                continue
            log.info("%s: %s chunks=%d", path.name, report.status, report.rows_ok)
    finally:
        await engine.dispose()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", type=pathlib.Path)
    asyncio.run(seed(parser.parse_args().data_dir))


if __name__ == "__main__":
    main()
