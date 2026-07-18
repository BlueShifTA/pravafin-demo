"""RAG retrieval (integration): hybrid vec + fts pool → rerank → top-k.

Exercises RagRetriever against a seeded doc_chunks table with scripted
Embedder/Reranker (no model download, deterministic scores). Auto-skips when
Postgres is down (`just stack-up` to run).
"""

from collections.abc import AsyncIterator, Sequence

import asyncpg
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from coresat.db.schema import apply_schema
from coresat.db.session import create_engine
from coresat.services.agent.retrieval import RagRetriever

ADMIN_DSN = "postgresql://postgres:postgres@localhost:5434/coresat_test"
ADMIN_SQLA_URL = "postgresql+asyncpg://postgres:postgres@localhost:5434/coresat_test"

# 768-d to match the doc_chunks.embedding column. QVEC is what the fake embedder
# returns for every query; VEC_CHUNK shares it (cosine distance 0), ORTHO_CHUNK
# is orthogonal (distance 1).
QVEC = [1.0] + [0.0] * 767
ORTHO = [0.0, 1.0] + [0.0] * 766


def _literal(vector: list[float]) -> str:
    return "[" + ",".join(repr(v) for v in vector) + "]"


class FakeEmbedder:
    async def embed(self, query: str) -> list[float]:
        return QVEC


class FakeReranker:
    """Deterministic scores by keyword so rerank ordering is assertable."""

    def rank(self, query: str, documents: Sequence[str]) -> list[float]:
        scores = []
        for document in documents:
            if "dividend" in document:
                scores.append(3.0)
            elif "earnings" in document:
                scores.append(2.0)
            else:
                scores.append(1.0)
        return scores


async def _connect_or_skip() -> asyncpg.Connection:
    try:
        return await asyncpg.connect(ADMIN_DSN, timeout=3)
    except OSError, asyncpg.PostgresError, TimeoutError:
        pytest.skip("postgres not running — just stack-up")


async def _insert_chunk(
    conn: asyncpg.Connection,
    source_doc: str,
    chunk_index: int,
    text: str,
    embedding: list[float] | None,
    page: int | None,
) -> None:
    await conn.execute(
        "INSERT INTO doc_chunks "
        "(source_doc, doc_type, chunk_index, text, embedding, checksum, page) "
        "VALUES ($1, 'report', $2, $3, CAST($4 AS vector), $5, $6)",
        source_doc,
        chunk_index,
        text,
        None if embedding is None else _literal(embedding),
        f"{source_doc}:{chunk_index}",
        page,
    )


@pytest.fixture
async def retriever() -> AsyncIterator[RagRetriever]:
    admin = await _connect_or_skip()
    await apply_schema(ADMIN_DSN)
    await admin.execute("TRUNCATE doc_chunks RESTART IDENTITY CASCADE")
    engine: AsyncEngine = create_engine(ADMIN_SQLA_URL)
    yield RagRetriever(engine=engine, embedder=FakeEmbedder(), reranker=FakeReranker())
    await engine.dispose()
    await admin.close()


async def test_hybrid_pool_reranks_and_trims_to_k(retriever: RagRetriever) -> None:
    admin = await _connect_or_skip()
    # F: fts-only (NULL embedding, matches "dividend"); V: vec-only (embedding ==
    # query, no query term); N: neither strong (orthogonal embedding, no term).
    await _insert_chunk(admin, "dividends.pdf", 0, "dividend policy update", None, 7)
    await _insert_chunk(admin, "earnings.pdf", 0, "quarterly earnings summary", QVEC, 3)
    await _insert_chunk(admin, "noise.pdf", 0, "unrelated boilerplate", ORTHO, 1)
    await admin.close()

    results = await retriever.retrieve("dividend", k=2)

    assert [r.source_doc for r in results] == ["dividends.pdf", "earnings.pdf"]
    assert [r.score for r in results] == [3.0, 2.0]
    assert results[0].page == 7
    assert "noise.pdf" not in {r.source_doc for r in results}


async def test_empty_store_returns_empty(retriever: RagRetriever) -> None:
    assert await retriever.retrieve("anything", k=5) == []


async def test_chunk_matching_both_signals_appears_once(retriever: RagRetriever) -> None:
    # A chunk that both scores in the vector pool AND matches full-text must
    # come back once — the pool UNION dedups ids (UNION ALL would double it).
    admin = await _connect_or_skip()
    await _insert_chunk(admin, "both.pdf", 0, "dividend growth summary", QVEC, 1)
    await _insert_chunk(admin, "earnings.pdf", 0, "earnings review", ORTHO, 1)
    await admin.close()

    results = await retriever.retrieve("dividend", k=10)

    assert [r.source_doc for r in results].count("both.pdf") == 1
    assert {r.source_doc for r in results} == {"both.pdf", "earnings.pdf"}


async def test_k_larger_than_pool_returns_all_available(retriever: RagRetriever) -> None:
    admin = await _connect_or_skip()
    await _insert_chunk(admin, "a.pdf", 0, "dividend note", QVEC, 1)
    await _insert_chunk(admin, "b.pdf", 0, "earnings note", ORTHO, 1)
    await admin.close()

    results = await retriever.retrieve("dividend", k=50)

    assert len(results) == 2
