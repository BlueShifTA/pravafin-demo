"""RAG retrieval: embed → hybrid search (pgvector + full-text) → rerank.

Deterministic once triggered — no LLM call. The embedder and reranker sit
behind protocols so the store, the embedding model, and the reranker are each
swappable at the composition root.
"""

import asyncio
from collections.abc import Sequence
from typing import Protocol

from fastembed.rerank.cross_encoder import TextCrossEncoder
from langchain_ollama import OllamaEmbeddings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from coresat.domain.rag import RetrievedChunk

# recall pool gathered by each signal before the cross-encoder reranks it
_PROBE = 20


class Embedder(Protocol):
    async def embed(self, query: str) -> list[float]: ...


class Reranker(Protocol):
    def rank(self, query: str, documents: Sequence[str]) -> list[float]: ...


class Retriever(Protocol):
    async def retrieve(self, query: str, k: int) -> list[RetrievedChunk]: ...


class OllamaEmbedder:
    def __init__(self, base_url: str, model: str) -> None:
        self._embeddings: OllamaEmbeddings = OllamaEmbeddings(base_url=base_url, model=model)

    async def embed(self, query: str) -> list[float]:
        return await self._embeddings.aembed_query(query)


class CrossEncoderReranker:
    """ONNX cross-encoder (fastembed, no torch). Loaded lazily on first use."""

    def __init__(self, model_name: str) -> None:
        self._model_name: str = model_name
        self._encoder: TextCrossEncoder | None = None

    def rank(self, query: str, documents: Sequence[str]) -> list[float]:
        if not documents:
            return []
        encoder = self._encoder
        if encoder is None:
            encoder = self._encoder = TextCrossEncoder(model_name=self._model_name)
        return list(encoder.rerank(query, list(documents)))


def _vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(repr(value) for value in vector) + "]"


class RagRetriever:
    def __init__(self, engine: AsyncEngine, embedder: Embedder, reranker: Reranker) -> None:
        self._engine: AsyncEngine = engine
        self._embedder: Embedder = embedder
        self._reranker: Reranker = reranker

    async def retrieve(self, query: str, k: int) -> list[RetrievedChunk]:
        query_vector = await self._embedder.embed(query)
        async with self._engine.connect() as conn:
            rows = (
                (
                    await conn.execute(
                        text(
                            "WITH vec AS ("
                            "  SELECT id, embedding <=> CAST(:qvec AS vector) AS dist"
                            "  FROM doc_chunks WHERE embedding IS NOT NULL"
                            "  ORDER BY dist LIMIT :probe"
                            "), fts AS ("
                            "  SELECT id, ts_rank(tsv, plainto_tsquery('english', :q)) AS rank"
                            "  FROM doc_chunks WHERE tsv @@ plainto_tsquery('english', :q)"
                            "  ORDER BY rank DESC LIMIT :probe"
                            "), pool AS (SELECT id FROM vec UNION SELECT id FROM fts)"
                            " SELECT d.source_doc, d.page, d.text"
                            " FROM doc_chunks d JOIN pool p ON p.id = d.id"
                        ),
                        {"qvec": _vector_literal(query_vector), "q": query, "probe": _PROBE},
                    )
                )
                .mappings()
                .all()
            )
        if not rows:
            return []
        texts = [row["text"] for row in rows]
        scores = await asyncio.to_thread(self._reranker.rank, query, texts)
        ranked = sorted(zip(rows, scores, strict=True), key=lambda pair: pair[1], reverse=True)
        return [
            RetrievedChunk(
                source_doc=row["source_doc"], page=row["page"], text=row["text"], score=float(score)
            )
            for row, score in ranked[:k]
        ]
