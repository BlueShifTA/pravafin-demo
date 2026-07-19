"""Ingestion endpoints: upload payloads, inspect runs and quarantine."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Request, UploadFile
from fastapi.params import Query
from sqlalchemy import text

import coresat.domain as csd
import coresat.services.ingestion as csi

router = APIRouter(prefix="/ingest", tags=["ingest"])


def _pipeline(request: Request) -> csi.IngestionPipeline:
    pipeline: csi.IngestionPipeline = request.app.state.ingest_pipeline
    return pipeline


@router.post("/{adapter_name}")
async def ingest(
    adapter_name: str,
    file: UploadFile,
    request: Request,
    source_ref: Annotated[str | None, Query()] = None,
) -> csd.IngestReport:
    payload = await file.read()
    try:
        return await _pipeline(request).run(adapter_name, payload, source_ref)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=f"unknown adapter: {adapter_name}") from error


@router.get("/runs")
async def list_runs(request: Request) -> list[dict[str, object]]:
    async with _pipeline(request).engine.connect() as conn:
        rows = await conn.execute(
            text(
                "SELECT id, source, status, rows_in, rows_ok, rows_quarantined, "
                "started_at, finished_at FROM ingest_runs ORDER BY id DESC LIMIT 200"
            )
        )
        return [dict(row) for row in rows.mappings()]


@router.get("/quarantine")
async def list_quarantine(request: Request) -> list[dict[str, object]]:
    async with _pipeline(request).engine.connect() as conn:
        rows = await conn.execute(
            text(
                "SELECT id, run_id, source, payload, reason, created_at "
                "FROM ingest_quarantine ORDER BY id DESC LIMIT 200"
            )
        )
        return [dict(row) for row in rows.mappings()]
