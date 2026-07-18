"""RAG retrieval domain models."""

from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    source_doc: str
    page: int | None
    text: str
    score: float
