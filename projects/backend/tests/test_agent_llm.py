"""ChatModelAgentLLM output cleaning at the real-LLM boundary.

The small local model copies the evidence-id brackets it sees in the prompt
(e.g. "[rag_search#1]") straight into the answer prose, even though citations
are surfaced separately as chips. These inline markers must be stripped from
the answer text; the structured `citations` field is left untouched.
"""

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

import coresat.services.agent as csa


def _llm(answer_json: str) -> csa.ChatModelAgentLLM:
    model = GenericFakeChatModel(messages=iter([AIMessage(content=answer_json)]))
    return csa.ChatModelAgentLLM(model, csa.COPILOT_PROMPTS)


async def test_inline_evidence_markers_stripped_from_answer_text() -> None:
    answer_json = (
        '{"text": "The CSPX factsheet lists key risks [rag_search#1] and '
        'the fund tracks 500 large-cap U.S. companies [rag_search#1].", '
        '"citations": ["rag_search#1"], "gaps": [], "needs_replan": false, '
        '"action": "chat", "draft": null}'
    )
    answer, _ = await _llm(answer_json).synthesise("what does CSPX cover?", "", [])
    assert "rag_search#1" not in answer.text
    assert "[]" not in answer.text
    assert "key risks and" in answer.text
    assert "500 large-cap U.S. companies." in answer.text
    # citations are still surfaced structurally for the chip renderer
    assert answer.citations == ["rag_search#1"]


async def test_parenthesised_markers_also_stripped() -> None:
    # The model wraps the id in parentheses as often as brackets — e.g. it ends
    # a sentence with "(rag_search#1)". Both delimiters must be stripped.
    answer_json = (
        '{"text": "The key benefits are growth and diversification (rag_search#1).", '
        '"citations": ["rag_search#1"], "gaps": [], "needs_replan": false, '
        '"action": "chat", "draft": null}'
    )
    answer, _ = await _llm(answer_json).synthesise("what are the benefits?", "", [])
    assert answer.text == "The key benefits are growth and diversification."
    assert answer.citations == ["rag_search#1"]


async def test_run_sql_markers_also_stripped() -> None:
    answer_json = (
        '{"text": "You invested 5000 [run_sql#1] so far.", '
        '"citations": ["run_sql#1"], "gaps": [], "needs_replan": false, '
        '"action": "chat", "draft": null}'
    )
    answer, _ = await _llm(answer_json).synthesise("how much invested?", "", [])
    assert answer.text == "You invested 5000 so far."
    assert answer.citations == ["run_sql#1"]
