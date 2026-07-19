"""PDF ingestion (integration): pypdf → per-page chunks → embed → doc_chunks.

Uses a scripted embedder (fixed 768-d vector) so no Ollama is needed; the PDF
itself is hand-built so page provenance and chunk splitting are assertable.
Auto-skips when Postgres is down (`just stack-up` to run).
"""

from collections.abc import AsyncIterator

import asyncpg
import pytest
from _pdfgen import make_text_pdf
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from coresat.db.schema import apply_schema
from coresat.db.session import create_engine
from coresat.services.ingestion.pipeline import IngestionPipeline, build_registry

ADMIN_DSN = "postgresql://postgres:postgres@localhost:5434/coresat_test"
ADMIN_SQLA_URL = "postgresql+asyncpg://postgres:postgres@localhost:5434/coresat_test"

_DIM = 768


class FakeEmbedder:
    async def embed(self, query: str) -> list[float]:
        return [0.1] * _DIM


async def _connect_or_skip() -> asyncpg.Connection:
    try:
        return await asyncpg.connect(ADMIN_DSN, timeout=3)
    except OSError, asyncpg.PostgresError, TimeoutError:
        pytest.skip("postgres not running — just stack-up")


@pytest.fixture
async def pipeline() -> AsyncIterator[IngestionPipeline]:
    admin = await _connect_or_skip()
    await apply_schema(ADMIN_DSN)
    # ingest_runs carries the checksum idempotency: reset it too, else a prior
    # run's checksum makes these payloads 'skipped' when the file runs alone.
    await admin.execute(
        "TRUNCATE doc_chunks, ingest_runs, ingest_quarantine RESTART IDENTITY CASCADE"
    )
    await admin.close()
    engine: AsyncEngine = create_engine(ADMIN_SQLA_URL)
    yield IngestionPipeline(engine=engine, registry=build_registry(FakeEmbedder()))
    await engine.dispose()


async def test_pdf_ingests_chunks_with_page_provenance(pipeline: IngestionPipeline) -> None:
    pdf = make_text_pdf(["revenue growth dividend policy", "magic formula screener notes"])

    report = await pipeline.run("pdf", pdf, "report.pdf")

    assert report.status == "succeeded"
    assert report.rows_ok == 2
    async with pipeline.engine.connect() as conn:
        rows = (
            (
                await conn.execute(
                    text(
                        "SELECT page, text, embedding IS NOT NULL AS has_vec "
                        "FROM doc_chunks WHERE source_doc = 'report.pdf' ORDER BY chunk_index"
                    )
                )
            )
            .mappings()
            .all()
        )
    assert [row["page"] for row in rows] == [1, 2]
    assert "dividend" in rows[0]["text"]
    assert all(row["has_vec"] for row in rows)


async def test_long_page_splits_into_ordered_chunks(pipeline: IngestionPipeline) -> None:
    long_page = " ".join(["alpha beta gamma delta epsilon"] * 60)  # ~1800 chars → multiple chunks

    await pipeline.run("pdf", make_text_pdf([long_page]), "long.pdf")

    async with pipeline.engine.connect() as conn:
        rows = (
            (
                await conn.execute(
                    text(
                        "SELECT page, chunk_index FROM doc_chunks "
                        "WHERE source_doc = 'long.pdf' ORDER BY chunk_index"
                    )
                )
            )
            .mappings()
            .all()
        )
    assert len(rows) >= 2
    assert all(row["page"] == 1 for row in rows)
    assert [row["chunk_index"] for row in rows] == list(range(len(rows)))


async def test_reingest_same_pdf_skips_no_duplicates(pipeline: IngestionPipeline) -> None:
    pdf = make_text_pdf(["one page only"])

    first = await pipeline.run("pdf", pdf, "dup.pdf")
    second = await pipeline.run("pdf", pdf, "dup.pdf")

    assert first.status == "succeeded"
    assert second.status == "skipped"
    async with pipeline.engine.connect() as conn:
        count = (
            await conn.execute(text("SELECT count(*) FROM doc_chunks WHERE source_doc = 'dup.pdf'"))
        ).scalar_one()
    assert count == 1


async def test_reingest_after_interrupted_run_resumes(pipeline: IngestionPipeline) -> None:
    # A crash mid-load commits the run row but leaves it non-succeeded. Re-running
    # the same payload must reset+finish that row, not trip the checksum UNIQUE key.
    pdf = make_text_pdf(["interrupted run resume test"])
    first = await pipeline.run("pdf", pdf, "resume.pdf")
    assert first.status == "succeeded"
    async with pipeline.engine.begin() as conn:
        await conn.execute(text("UPDATE ingest_runs SET status = 'running', finished_at = NULL"))

    second = await pipeline.run("pdf", pdf, "resume.pdf")

    assert second.status == "succeeded"  # resumed via ON CONFLICT, no unique violation
    async with pipeline.engine.connect() as conn:
        count = (
            await conn.execute(
                text("SELECT count(*) FROM doc_chunks WHERE source_doc = 'resume.pdf'")
            )
        ).scalar_one()
    assert count == 1


async def test_pdf_without_source_ref_is_rejected(pipeline: IngestionPipeline) -> None:
    with pytest.raises(ValueError, match="source_ref"):
        await pipeline.run("pdf", make_text_pdf(["x"]), None)


async def test_modified_pdf_updates_chunk_in_place(pipeline: IngestionPipeline) -> None:
    # Same source_doc, changed content → new checksum → the run is NOT skipped,
    # and chunk_index 0 is upserted (ON CONFLICT DO UPDATE), not duplicated.
    first = await pipeline.run("pdf", make_text_pdf(["original alpha content"]), "same.pdf")
    second = await pipeline.run("pdf", make_text_pdf(["revised beta content"]), "same.pdf")

    assert first.status == "succeeded"
    assert second.status == "succeeded"  # different payload → re-ingested, not skipped
    async with pipeline.engine.connect() as conn:
        rows = (
            (
                await conn.execute(
                    text(
                        "SELECT text FROM doc_chunks WHERE source_doc = 'same.pdf' "
                        "ORDER BY chunk_index"
                    )
                )
            )
            .mappings()
            .all()
        )
    assert len(rows) == 1
    assert "revised beta" in rows[0]["text"]
    assert "original" not in rows[0]["text"]
