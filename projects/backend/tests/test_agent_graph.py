"""Copilot graph: scope guard, plan-execute-synthesise, grounding validator,
self-correcting retry loop (max 5) and rag fallback."""

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableConfig

import coresat.domain as csd
import coresat.services.agent as csa

_USAGE = csa.Usage(tokens_in=10, tokens_out=5)
# Loops past the default LangGraph recursion ceiling (25) reach it at 5 attempts.
_CONFIG: RunnableConfig = {"recursion_limit": csa.RECURSION_LIMIT}


class ScriptedLLM:
    """AgentLLM fake: fixed scope verdict, scripted plans and answers."""

    def __init__(self, in_scope: bool, plans: list[csd.Plan], answers: list[csd.Answer]) -> None:
        self.in_scope: bool = in_scope
        self.plans: list[csd.Plan] = plans
        self.answers: list[csd.Answer] = answers
        self.plan_calls: int = 0
        self.replan_errors_seen: list[str | None] = []
        self.scope_contexts_seen: list[str] = []

    async def classify_scope(self, query: str, context: str) -> tuple[csd.ScopeVerdict, csa.Usage]:
        self.scope_contexts_seen.append(context)
        return csd.ScopeVerdict(in_scope=self.in_scope), _USAGE

    async def plan(
        self, query: str, context: str, replan_error: str | None
    ) -> tuple[csd.Plan, csa.Usage]:
        self.replan_errors_seen.append(replan_error)
        plan = self.plans[min(self.plan_calls, len(self.plans) - 1)]
        self.plan_calls += 1
        return plan, _USAGE

    async def synthesise(
        self, query: str, context: str, evidence: list[csd.Evidence]
    ) -> tuple[csd.Answer, csa.Usage]:
        index = min(self.plan_calls - 1, len(self.answers) - 1)
        return self.answers[index], _USAGE


class StaticTool:
    def __init__(self, content: str) -> None:
        self._content: str = content

    async def run(self, step: csd.Step) -> csd.Evidence:
        return csd.Evidence(step_id=step.id, source="run_sql", content=self._content, error=None)


def _graph(llm: ScriptedLLM, evidence_content: str = "invested_amount=5000"):
    executor = csa.Executor({csd.ToolName.RUN_SQL: StaticTool(evidence_content)})
    return csa.build_graph(llm, executor)


def _sql_plan() -> csd.Plan:
    return csd.Plan(steps=[csd.Step(id=1, question="q", tool=csd.ToolName.RUN_SQL, sql="SELECT 1")])


async def test_user_stated_numbers_count_as_grounded() -> None:
    # capital figures come from the user, not SQL evidence — they must not
    # trip the fabrication guard
    answer = csd.Answer(text="With 100000 as capital you invested 5000 so far.")
    llm = ScriptedLLM(in_scope=True, plans=[_sql_plan()], answers=[answer])
    state = await _graph(llm).ainvoke(
        csa.initial_state("I have 100000 to invest, how much placed already?", "")
    )
    assert llm.plan_calls == 1
    assert state["grounded"] is True
    assert state["answer"] is not None
    assert state["answer"].text == answer.text


async def test_scope_guard_receives_conversation_context() -> None:
    answer = csd.Answer(text="It came from the projection tool over your portfolio data.")
    llm = ScriptedLLM(in_scope=True, plans=[csd.Plan(steps=[])], answers=[answer])
    context = "user: prospect in 10 years?\nassistant: expected 1747701.27"
    state = await _graph(llm).ainvoke(
        csa.initial_state("where did you get the number from?", context)
    )
    assert llm.scope_contexts_seen == [context]
    assert state["answer"] is not None
    assert state["answer"].text == answer.text


async def test_greeting_with_empty_plan_answers_from_conversation() -> None:
    answer = csd.Answer(text="Hello! Ask me about your portfolio, funds, or stocks.")
    llm = ScriptedLLM(in_scope=True, plans=[csd.Plan(steps=[])], answers=[answer])
    state = await _graph(llm).ainvoke(csa.initial_state("Hi", "(new conversation)"))
    assert state["answer"] is not None
    assert state["answer"].text == answer.text
    assert state["grounded"] is True
    assert state["evidence"] == []


async def test_off_topic_refused_without_planning() -> None:
    llm = ScriptedLLM(in_scope=False, plans=[_sql_plan()], answers=[])
    state = await _graph(llm).ainvoke(csa.initial_state("weather tomorrow?", ""))
    assert state["answer"] is not None
    assert state["answer"].text == csa.OFF_TOPIC_TEXT
    assert llm.plan_calls == 0


async def test_grounded_answer_passes_first_try() -> None:
    answer = csd.Answer(text="You invested 5000 in total.", citations=["run_sql#1"])
    llm = ScriptedLLM(in_scope=True, plans=[_sql_plan()], answers=[answer])
    state = await _graph(llm).ainvoke(csa.initial_state("how much invested?", ""))
    assert state["answer"] is not None
    assert state["answer"].text == answer.text
    assert state["grounded"] is True
    assert llm.plan_calls == 1
    nodes = [entry["node"] for entry in state["usage"]]
    assert nodes == ["scope_guard", "planner", "synthesiser"]


async def test_fabricated_number_triggers_one_replan_then_success() -> None:
    fabricated = csd.Answer(text="You invested 123456 in total.")
    honest = csd.Answer(text="You invested 5000 in total.")
    llm = ScriptedLLM(in_scope=True, plans=[_sql_plan()], answers=[fabricated, honest])
    state = await _graph(llm).ainvoke(csa.initial_state("how much invested?", ""))
    assert llm.plan_calls == 2
    assert llm.replan_errors_seen[0] is None
    assert llm.replan_errors_seen[1] is not None
    assert state["answer"] is not None
    assert state["answer"].text == honest.text
    assert state["grounded"] is True


async def test_retries_until_a_grounded_answer_arrives() -> None:
    # Two fabricated attempts, then an honest one on the third (== the cap): the
    # loop keeps re-planning and returns the first grounded answer.
    fabricated = csd.Answer(text="You invested 123456 in total.")
    honest = csd.Answer(text="You invested 5000 in total.")
    llm = ScriptedLLM(in_scope=True, plans=[_sql_plan()], answers=[fabricated, fabricated, honest])
    state = await _graph(llm).ainvoke(csa.initial_state("how much invested?", ""), _CONFIG)
    assert llm.plan_calls == 3
    assert state["answer"] is not None
    assert state["answer"].text == honest.text
    assert state["grounded"] is True
    # every retry after the first carries the prior error back to the planner
    assert llm.replan_errors_seen[0] is None
    assert all(err is not None for err in llm.replan_errors_seen[1:3])


async def test_persistent_fabrication_exhausts_retries_then_refuses() -> None:
    # Nothing ever grounds the figure and the only tool is run_sql, so the rag
    # fallback finds no corpus either — after MAX_ATTEMPTS self-correcting tries
    # the agent refuses rather than emit a fabricated number.
    fabricated = csd.Answer(text="You invested 123456 in total.")
    llm = ScriptedLLM(in_scope=True, plans=[_sql_plan()], answers=[fabricated])
    state = await _graph(llm).ainvoke(csa.initial_state("how much invested?", ""), _CONFIG)
    assert llm.plan_calls == csa.MAX_ATTEMPTS
    assert state["answer"] is not None
    assert state["answer"].text == csa.CANNOT_ANSWER_TEXT
    assert state["grounded"] is False


async def test_empty_synthesis_refuses_cleanly_never_blank() -> None:
    # The synthesiser parse-failure fallback returns an empty needs_replan
    # answer. An empty answer is vacuously "number-grounded", so it must be
    # forced ungrounded and routed to an honest refusal — never streamed blank.
    blank = csd.Answer(text="", needs_replan=True)
    llm = ScriptedLLM(in_scope=True, plans=[_sql_plan()], answers=[blank])
    state = await _graph(llm).ainvoke(csa.initial_state("how much invested?", ""), _CONFIG)
    assert state["answer"] is not None
    assert state["answer"].text == csa.CANNOT_ANSWER_TEXT
    assert state["grounded"] is False
    assert llm.plan_calls == csa.MAX_ATTEMPTS


class _FailingSqlTool:
    async def run(self, step: csd.Step) -> csd.Evidence:
        return csd.Evidence(
            step_id=step.id,
            source="run_sql",
            content="",
            error="SQL failed: syntax error near 'SELET'",
        )


class _EvidenceAwareLLM:
    """Fabricates a figure while only failing SQL evidence is present, but
    answers honestly the moment rag_search evidence appears — models a planner
    whose SQL keeps erroring while the document fallback succeeds."""

    def __init__(self) -> None:
        self.plan_calls: int = 0
        self.replan_errors_seen: list[str | None] = []

    async def classify_scope(self, query: str, context: str) -> tuple[csd.ScopeVerdict, csa.Usage]:
        return csd.ScopeVerdict(in_scope=True), _USAGE

    async def plan(
        self, query: str, context: str, replan_error: str | None
    ) -> tuple[csd.Plan, csa.Usage]:
        self.replan_errors_seen.append(replan_error)
        self.plan_calls += 1
        return _sql_plan(), _USAGE

    async def synthesise(
        self, query: str, context: str, evidence: list[csd.Evidence]
    ) -> tuple[csd.Answer, csa.Usage]:
        rag = [item for item in evidence if item.source == "rag_search" and item.error is None]
        if rag:
            return (
                csd.Answer(
                    text="From the documents: IWDA is a global equity fund.",
                    citations=["rag_search#1"],
                ),
                _USAGE,
            )
        return csd.Answer(text="You invested 123456 in total."), _USAGE


async def test_sql_failures_fall_back_to_rag_after_exhausting_retries() -> None:
    # The run_sql tool errors on every attempt; after the retry cap the graph
    # runs one rag_search fallback and answers from the retrieved document.
    chunk = csd.RetrievedChunk(
        source_doc="iwda.pdf", page=1, text="IWDA is a global equity fund.", score=0.9
    )
    executor = csa.Executor(
        {
            csd.ToolName.RUN_SQL: _FailingSqlTool(),
            csd.ToolName.RAG_SEARCH: csa.RagSearchTool(_FakeRetriever([chunk]), k=4),
        }
    )
    llm = _EvidenceAwareLLM()
    state = await csa.build_graph(llm, executor).ainvoke(
        csa.initial_state("how much invested?", ""), _CONFIG
    )
    assert llm.plan_calls == csa.MAX_ATTEMPTS  # SQL retried to the cap, then stopped
    assert all(err is not None for err in llm.replan_errors_seen[1:])  # errors fed back
    assert state["answer"] is not None
    assert state["answer"].text.startswith("From the documents")
    assert state["grounded"] is True
    assert any(item.source == "rag_search" for item in state["evidence"])


async def test_synthesiser_requested_replan_honoured_once() -> None:
    incomplete = csd.Answer(text="Partial answer with 5000.", needs_replan=True)
    complete = csd.Answer(text="Full answer with 5000.")
    llm = ScriptedLLM(in_scope=True, plans=[_sql_plan()], answers=[incomplete, complete])
    state = await _graph(llm).ainvoke(csa.initial_state("how much invested?", ""))
    assert llm.plan_calls == 2
    assert state["answer"] is not None
    assert state["answer"].text == complete.text


async def test_portfolio_proposal_is_not_grounding_gated() -> None:
    # A design proposal invents allocation numbers (weights, default capital)
    # the user never stated and no SQL returned — those are choices, not facts,
    # so the fabrication guard must not reject a propose answer. Otherwise the
    # draft agent re-plans, exhausts retries, and refuses instead of surfacing
    # the portfolio the user asked it to build.
    draft = csd.PortfolioDraft(
        name="Growth 10%",
        initial_capital=10000,
        monthly_contribution=0,
        cores=[csd.DraftPosition(ticker="SMH", weight=0.6)],
        satellites=[csd.DraftPosition(ticker="NVDA", weight=0.4)],
    )
    proposal = csd.Answer(
        text="Proposed: 60% SMH core, 40% NVDA, 10000 initial capital.",
        action="propose",
        draft=draft,
    )
    llm = ScriptedLLM(in_scope=True, plans=[_sql_plan()], answers=[proposal])
    state = await _graph(llm, "ticker=SMH, cagr_10y=0.3579").ainvoke(
        csa.initial_state("build me a growth portfolio", "")
    )
    assert llm.plan_calls == 1  # proposed on the first try, no re-plan loop
    assert state["grounded"] is True
    assert state["answer"] is not None
    assert state["answer"].action == "propose"
    assert state["answer"].draft is not None


async def test_draft_agent_chat_answer_still_grounded() -> None:
    # A factual (action=chat) answer from the same draft agent stays fully
    # grounded — the proposal exemption must not leak into Q&A.
    fabricated = csd.Answer(text="SMH returned 999 percent.", action="chat")
    llm = ScriptedLLM(in_scope=True, plans=[_sql_plan()], answers=[fabricated])
    state = await _graph(llm, "ticker=SMH, cagr_10y=0.3579").ainvoke(
        csa.initial_state("what is SMH's return?", ""), _CONFIG
    )
    assert state["grounded"] is False
    assert state["answer"] is not None
    assert state["answer"].text == csa.CANNOT_ANSWER_TEXT


class _NoRowsSqlTool:
    # A syntactically fine SELECT that simply matches nothing: content is the
    # "(no rows)" sentinel, error is None. This is the CSPX-ticker-mismatch shape
    # — the query ran, gathered no facts, yet did not error.
    async def run(self, step: csd.Step) -> csd.Evidence:
        return csd.Evidence(step_id=step.id, source="run_sql", content="(no rows)", error=None)


class _RefuseUntilRagLLM:
    """Refuses while only empty SQL evidence is present, then answers from the
    document once the rag fallback supplies a chunk. A refusal carries no figure,
    so the number guard alone would wave it through — the empty-evidence gate is
    what must force the retry."""

    def __init__(self) -> None:
        self.plan_calls: int = 0
        self.replan_errors_seen: list[str | None] = []

    async def classify_scope(self, query: str, context: str) -> tuple[csd.ScopeVerdict, csa.Usage]:
        return csd.ScopeVerdict(in_scope=True), _USAGE

    async def plan(
        self, query: str, context: str, replan_error: str | None
    ) -> tuple[csd.Plan, csa.Usage]:
        self.replan_errors_seen.append(replan_error)
        self.plan_calls += 1
        return _sql_plan(), _USAGE

    async def synthesise(
        self, query: str, context: str, evidence: list[csd.Evidence]
    ) -> tuple[csd.Answer, csa.Usage]:
        rag = [item for item in evidence if item.source == "rag_search" and item.error is None]
        if rag:
            return (
                csd.Answer(
                    text="From the factsheet: the TER is 0.07%.", citations=["rag_search#1"]
                ),
                _USAGE,
            )
        return csd.Answer(text="I could not find that figure in the data you have."), _USAGE


async def test_no_rows_sql_is_not_grounded_and_falls_back_to_rag() -> None:
    # A run_sql that returns zero rows gathered no facts. A refusal built on it
    # must NOT ship as grounded on the first pass — the graph must exhaust its
    # retries and then consult the document corpus before finalising.
    chunk = csd.RetrievedChunk(
        source_doc="cspx.pdf", page=1, text="Total Expense Ratio 0.07%.", score=0.9
    )
    executor = csa.Executor(
        {
            csd.ToolName.RUN_SQL: _NoRowsSqlTool(),
            csd.ToolName.RAG_SEARCH: csa.RagSearchTool(_FakeRetriever([chunk]), k=4),
        }
    )
    llm = _RefuseUntilRagLLM()
    state = await csa.build_graph(llm, executor).ainvoke(
        csa.initial_state("what is CSPX's TER?", ""), _CONFIG
    )
    assert llm.plan_calls == csa.MAX_ATTEMPTS  # retried, not shipped on the first refusal
    assert state["answer"] is not None
    assert state["answer"].text.startswith("From the factsheet")
    assert state["grounded"] is True
    assert any(item.source == "rag_search" for item in state["evidence"])


async def test_no_rows_without_corpus_refuses_after_retries_never_first_pass() -> None:
    # Same empty-evidence shape but no rag tool: the graph must retry to the cap
    # and give an honest refusal — never treat the first-pass "cannot find"
    # refusal as a grounded answer and stop.
    executor = csa.Executor({csd.ToolName.RUN_SQL: _NoRowsSqlTool()})
    llm = _RefuseUntilRagLLM()
    state = await csa.build_graph(llm, executor).ainvoke(
        csa.initial_state("what is CSPX's TER?", ""), _CONFIG
    )
    assert llm.plan_calls == csa.MAX_ATTEMPTS
    assert state["answer"] is not None
    assert state["answer"].text == csa.CANNOT_ANSWER_TEXT
    assert state["grounded"] is False


def test_plan_parser_accepts_bare_step_list() -> None:
    # qwen frequently returns the steps array directly instead of {"steps": [...]}.
    # The Plan before-validator must recover it, or the planner degrades to empty.
    parser: PydanticOutputParser[csd.Plan] = PydanticOutputParser(pydantic_object=csd.Plan)
    plan = parser.parse('[{"id": 1, "question": "q", "tool": "run_sql", "sql": "SELECT 1"}]')
    assert len(plan.steps) == 1
    assert plan.steps[0].tool == csd.ToolName.RUN_SQL


def test_plan_parser_still_accepts_wrapped_object() -> None:
    parser: PydanticOutputParser[csd.Plan] = PydanticOutputParser(pydantic_object=csd.Plan)
    plan = parser.parse('{"steps": [{"id": 1, "question": "q", "tool": "gap"}]}')
    assert plan.steps[0].tool == csd.ToolName.GAP


class _FakeRetriever:
    def __init__(self, chunks: list[csd.RetrievedChunk]) -> None:
        self._chunks: list[csd.RetrievedChunk] = chunks

    async def retrieve(self, query: str, k: int) -> list[csd.RetrievedChunk]:
        return self._chunks


async def test_rag_search_step_routes_to_rag_tool_and_grounds_document_number() -> None:
    # A planner-chosen rag_search step must reach RagSearchTool, and a figure
    # quoted from the retrieved chunk must count as grounded (evidence numbers
    # feed the fabrication guard) — otherwise the answer would be refused.
    chunk = csd.RetrievedChunk(
        source_doc="iwda.pdf",
        page=2,
        text="The fund holds about 1500 companies across developed markets.",
        score=0.9,
    )
    executor = csa.Executor(
        {csd.ToolName.RAG_SEARCH: csa.RagSearchTool(_FakeRetriever([chunk]), k=4)}
    )
    plan = csd.Plan(
        steps=[
            csd.Step(
                id=1, question="how many holdings does IWDA have", tool=csd.ToolName.RAG_SEARCH
            )
        ]
    )
    answer = csd.Answer(text="IWDA holds about 1500 companies.", citations=["rag_search#1"])
    llm = ScriptedLLM(in_scope=True, plans=[plan], answers=[answer])

    state = await csa.build_graph(llm, executor).ainvoke(
        csa.initial_state("how many holdings does IWDA have?", "")
    )

    assert llm.plan_calls == 1  # grounded on the first try, no re-plan
    assert state["grounded"] is True
    assert state["answer"] is not None
    assert state["answer"].text == answer.text
    rag_evidence = [item for item in state["evidence"] if item.source == "rag_search"]
    assert len(rag_evidence) == 1
    assert "iwda.pdf p.2" in rag_evidence[0].content


async def test_ungrounded_document_number_is_refused() -> None:
    # A number that appears in NO chunk must not survive — the rag path is held
    # to the same grounding bar as run_sql.
    chunk = csd.RetrievedChunk(
        source_doc="iwda.pdf", page=1, text="A global equity fund.", score=0.5
    )
    executor = csa.Executor(
        {csd.ToolName.RAG_SEARCH: csa.RagSearchTool(_FakeRetriever([chunk]), k=4)}
    )
    plan = csd.Plan(
        steps=[csd.Step(id=1, question="how many holdings", tool=csd.ToolName.RAG_SEARCH)]
    )
    fabricated = csd.Answer(text="IWDA holds 4321 companies.", citations=["rag_search#1"])
    llm = ScriptedLLM(in_scope=True, plans=[plan], answers=[fabricated, fabricated])

    state = await csa.build_graph(llm, executor).ainvoke(
        csa.initial_state("how many holdings?", ""), _CONFIG
    )

    assert state["answer"] is not None
    assert state["answer"].text == csa.CANNOT_ANSWER_TEXT
    assert state["grounded"] is False
