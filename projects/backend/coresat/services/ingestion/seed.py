"""Seed the database from the etops-demo-data directory. Used by `just ingest-all`.

Thin walker over the tested pipeline — idempotent via run checksums, so
re-running only ingests what changed.
"""

import argparse
import asyncio
import logging
import pathlib

from coresat.core.config import get_settings
from coresat.db.schema import apply_schema
from coresat.db.session import create_engine, to_async_url
from coresat.services.ingestion.pipeline import IngestionPipeline, build_registry

log = logging.getLogger(__name__)

_HOLDINGS_FUNDS = {"iwda_holdings.csv": "IWDA.AS", "cspx_holdings.csv": "CSPX.L"}


async def seed(data_dir: pathlib.Path) -> None:
    settings = get_settings()
    await apply_schema(settings.admin_database_url)
    engine = create_engine(to_async_url(settings.admin_database_url))
    pipeline = IngestionPipeline(engine=engine, registry=build_registry())
    try:
        for name, adapter in (
            ("universe_v2.csv", "universe_csv"),
            ("fundamentals_stocks.csv", "fundamentals_csv"),
            ("fundamentals_etfs.csv", "funds_csv"),
        ):
            path = data_dir / name
            if path.exists():
                report = await pipeline.run(adapter, path.read_bytes(), None)
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
    finally:
        await engine.dispose()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", type=pathlib.Path)
    asyncio.run(seed(parser.parse_args().data_dir))


if __name__ == "__main__":
    main()
