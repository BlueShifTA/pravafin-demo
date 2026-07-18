"""Pipeline: checksum → run row → parse → load valid / quarantine rejects → finalize."""

import hashlib
import json
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from coresat.domain.ingestion import IngestReport
from coresat.services.agent.retrieval import Embedder
from coresat.services.ingestion.adapters import (
    DailyPricesCsvAdapter,
    FinancialsYearlyCsvAdapter,
    FundamentalsCsvAdapter,
    FundsCsvAdapter,
    ISharesHoldingsCsvAdapter,
    PdfAdapter,
    SourceAdapter,
    UniverseCsvAdapter,
)
from coresat.services.ingestion.loaders import (
    DocChunkLoader,
    Loader,
    load_financials_yearly,
    load_fundamentals,
    load_funds,
    load_holdings,
    load_instruments,
    load_prices,
)


@dataclass(frozen=True)
class AdapterEntry:
    adapter: SourceAdapter
    loader: Loader


def build_registry(embedder: Embedder) -> dict[str, AdapterEntry]:
    entries = (
        AdapterEntry(UniverseCsvAdapter(), load_instruments),
        AdapterEntry(DailyPricesCsvAdapter(), load_prices),
        AdapterEntry(ISharesHoldingsCsvAdapter(), load_holdings),
        AdapterEntry(FundamentalsCsvAdapter(), load_fundamentals),
        AdapterEntry(FinancialsYearlyCsvAdapter(), load_financials_yearly),
        AdapterEntry(FundsCsvAdapter(), load_funds),
        AdapterEntry(PdfAdapter(), DocChunkLoader(embedder)),
    )
    return {entry.adapter.name: entry for entry in entries}


class IngestionPipeline:
    def __init__(self, engine: AsyncEngine, registry: dict[str, AdapterEntry]) -> None:
        self.engine = engine
        self._registry = registry

    async def run(
        self, adapter_name: str, payload: bytes, source_ref: str | None = None
    ) -> IngestReport:
        """Ingest one payload. Same payload twice → 'skipped' (checksum idempotency)."""
        entry = self._registry[adapter_name]
        version = entry.adapter.version
        checksum = hashlib.sha256(
            f"{adapter_name}:{version}".encode() + b"\0" + payload
        ).hexdigest()

        async with self.engine.begin() as conn:
            done = (
                await conn.execute(
                    text(
                        "SELECT id FROM ingest_runs "
                        "WHERE checksum = :checksum AND status = 'succeeded'"
                    ),
                    {"checksum": checksum},
                )
            ).first()
            if done is not None:
                return IngestReport(
                    run_id=done.id,
                    source=adapter_name,
                    status="skipped",
                    rows_in=0,
                    rows_ok=0,
                    rows_quarantined=0,
                )
            run_id = (
                await conn.execute(
                    text(
                        "INSERT INTO ingest_runs (source, adapter_version, checksum) "
                        "VALUES (:source, :version, :checksum) RETURNING id"
                    ),
                    {"source": adapter_name, "version": version, "checksum": checksum},
                )
            ).scalar_one()

        valid, rejects = entry.adapter.parse(payload, source_ref)
        status = "succeeded" if valid or not rejects else "failed"

        async with self.engine.begin() as conn:
            if valid:
                await entry.loader(conn, valid)
            if rejects:
                await conn.execute(
                    text(
                        "INSERT INTO ingest_quarantine (run_id, source, payload, reason) "
                        "VALUES (:run_id, :source, cast(:payload AS jsonb), :reason)"
                    ),
                    [
                        {
                            "run_id": run_id,
                            "source": adapter_name,
                            "payload": json.dumps(reject.row),
                            "reason": reject.reason,
                        }
                        for reject in rejects
                    ],
                )
            await conn.execute(
                text(
                    "UPDATE ingest_runs SET status = :status, rows_in = :rows_in, "
                    "rows_ok = :rows_ok, rows_quarantined = :rows_quarantined, "
                    "finished_at = now() WHERE id = :run_id"
                ),
                {
                    "status": status,
                    "rows_in": len(valid) + len(rejects),
                    "rows_ok": len(valid),
                    "rows_quarantined": len(rejects),
                    "run_id": run_id,
                },
            )
        return IngestReport(
            run_id=run_id,
            source=adapter_name,
            status=status,  # type: ignore[arg-type]
            rows_in=len(valid) + len(rejects),
            rows_ok=len(valid),
            rows_quarantined=len(rejects),
        )
