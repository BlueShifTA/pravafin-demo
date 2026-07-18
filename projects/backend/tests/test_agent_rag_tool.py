"""RagSearchTool: retriever chunks → cited Evidence for the synthesiser.

Pure unit tests with a scripted retriever — no DB, no models.
"""

from coresat.domain.agent import Step, ToolName
from coresat.domain.rag import RetrievedChunk
from coresat.services.agent.tools import RagSearchTool


class _FakeRetriever:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self._chunks: list[RetrievedChunk] = chunks
        self.seen_query: str | None = None
        self.seen_k: int | None = None

    async def retrieve(self, query: str, k: int) -> list[RetrievedChunk]:
        self.seen_query = query
        self.seen_k = k
        return self._chunks


async def test_rag_search_formats_chunks_with_provenance() -> None:
    retriever = _FakeRetriever(
        [
            RetrievedChunk(source_doc="iwda.pdf", page=3, text="tracks the MSCI World", score=0.9),
            RetrievedChunk(source_doc="notes.pdf", page=None, text="undated note", score=0.4),
        ]
    )
    tool = RagSearchTool(retriever, k=4)

    evidence = await tool.run(Step(id=1, question="what does IWDA track", tool=ToolName.RAG_SEARCH))

    assert retriever.seen_query == "what does IWDA track"  # step.question is the query
    assert retriever.seen_k == 4
    assert evidence.source == "rag_search"
    assert evidence.error is None
    assert "iwda.pdf p.3" in evidence.content
    assert "tracks the MSCI World" in evidence.content
    assert "notes.pdf" in evidence.content


async def test_rag_search_empty_reports_no_documents() -> None:
    retriever = _FakeRetriever([])
    tool = RagSearchTool(retriever, k=4)

    evidence = await tool.run(Step(id=2, question="anything", tool=ToolName.RAG_SEARCH))

    assert evidence.error is None
    assert "no" in evidence.content.lower()
