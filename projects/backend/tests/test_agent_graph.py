"""Copilot graph: scope guard, plan-execute-synthesise, grounding validator, one re-plan."""

from coresat.domain.agent import Answer, Evidence, Plan, ScopeVerdict, Step, ToolName
from coresat.services.agent.executor import Executor
from coresat.services.agent.graph import (
    CANNOT_ANSWER_TEXT,
    OFF_TOPIC_TEXT,
    build_graph,
    initial_state,
)
from coresat.services.agent.llm import Usage

_USAGE = Usage(tokens_in=10, tokens_out=5)


class ScriptedLLM:
    """AgentLLM fake: fixed scope verdict, scripted plans and answers."""

    def __init__(self, in_scope: bool, plans: list[Plan], answers: list[Answer]) -> None:
        self.in_scope: bool = in_scope
        self.plans: list[Plan] = plans
        self.answers: list[Answer] = answers
        self.plan_calls: int = 0
        self.replan_errors_seen: list[str | None] = []
        self.scope_contexts_seen: list[str] = []

    async def classify_scope(self, query: str, context: str) -> tuple[ScopeVerdict, Usage]:
        self.scope_contexts_seen.append(context)
        return ScopeVerdict(in_scope=self.in_scope), _USAGE

    async def plan(self, query: str, context: str, replan_error: str | None) -> tuple[Plan, Usage]:
        self.replan_errors_seen.append(replan_error)
        plan = self.plans[min(self.plan_calls, len(self.plans) - 1)]
        self.plan_calls += 1
        return plan, _USAGE

    async def synthesise(
        self, query: str, context: str, evidence: list[Evidence]
    ) -> tuple[Answer, Usage]:
        index = min(self.plan_calls - 1, len(self.answers) - 1)
        return self.answers[index], _USAGE


class StaticTool:
    def __init__(self, content: str) -> None:
        self._content: str = content

    async def run(self, step: Step) -> Evidence:
        return Evidence(step_id=step.id, source="run_sql", content=self._content, error=None)


def _graph(llm: ScriptedLLM, evidence_content: str = "invested_amount=5000"):
    executor = Executor({ToolName.RUN_SQL: StaticTool(evidence_content)})
    return build_graph(llm, executor)


def _sql_plan() -> Plan:
    return Plan(steps=[Step(id=1, question="q", tool=ToolName.RUN_SQL, sql="SELECT 1")])


async def test_scope_guard_receives_conversation_context() -> None:
    answer = Answer(text="It came from the projection tool over your portfolio data.")
    llm = ScriptedLLM(in_scope=True, plans=[Plan(steps=[])], answers=[answer])
    context = "user: prospect in 10 years?\nassistant: expected 1747701.27"
    state = await _graph(llm).ainvoke(initial_state("where did you get the number from?", context))
    assert llm.scope_contexts_seen == [context]
    assert state["answer"] is not None
    assert state["answer"].text == answer.text


async def test_greeting_with_empty_plan_answers_from_conversation() -> None:
    answer = Answer(text="Hello! Ask me about your portfolio, funds, or stocks.")
    llm = ScriptedLLM(in_scope=True, plans=[Plan(steps=[])], answers=[answer])
    state = await _graph(llm).ainvoke(initial_state("Hi", "(new conversation)"))
    assert state["answer"] is not None
    assert state["answer"].text == answer.text
    assert state["grounded"] is True
    assert state["evidence"] == []


async def test_off_topic_refused_without_planning() -> None:
    llm = ScriptedLLM(in_scope=False, plans=[_sql_plan()], answers=[])
    state = await _graph(llm).ainvoke(initial_state("weather tomorrow?", ""))
    assert state["answer"] is not None
    assert state["answer"].text == OFF_TOPIC_TEXT
    assert llm.plan_calls == 0


async def test_grounded_answer_passes_first_try() -> None:
    answer = Answer(text="You invested 5000 in total.", citations=["run_sql#1"])
    llm = ScriptedLLM(in_scope=True, plans=[_sql_plan()], answers=[answer])
    state = await _graph(llm).ainvoke(initial_state("how much invested?", ""))
    assert state["answer"] is not None
    assert state["answer"].text == answer.text
    assert state["grounded"] is True
    assert llm.plan_calls == 1
    nodes = [entry["node"] for entry in state["usage"]]
    assert nodes == ["scope_guard", "planner", "synthesiser"]


async def test_fabricated_number_triggers_one_replan_then_success() -> None:
    fabricated = Answer(text="You invested 123456 in total.")
    honest = Answer(text="You invested 5000 in total.")
    llm = ScriptedLLM(in_scope=True, plans=[_sql_plan()], answers=[fabricated, honest])
    state = await _graph(llm).ainvoke(initial_state("how much invested?", ""))
    assert llm.plan_calls == 2
    assert llm.replan_errors_seen[0] is None
    assert llm.replan_errors_seen[1] is not None
    assert state["answer"] is not None
    assert state["answer"].text == honest.text
    assert state["grounded"] is True


async def test_still_fabricated_after_replan_gives_honest_refusal() -> None:
    fabricated = Answer(text="You invested 123456 in total.")
    llm = ScriptedLLM(in_scope=True, plans=[_sql_plan()], answers=[fabricated, fabricated])
    state = await _graph(llm).ainvoke(initial_state("how much invested?", ""))
    assert llm.plan_calls == 2
    assert state["answer"] is not None
    assert state["answer"].text == CANNOT_ANSWER_TEXT
    assert state["grounded"] is False


async def test_synthesiser_requested_replan_honoured_once() -> None:
    incomplete = Answer(text="Partial answer with 5000.", needs_replan=True)
    complete = Answer(text="Full answer with 5000.")
    llm = ScriptedLLM(in_scope=True, plans=[_sql_plan()], answers=[incomplete, complete])
    state = await _graph(llm).ainvoke(initial_state("how much invested?", ""))
    assert llm.plan_calls == 2
    assert state["answer"] is not None
    assert state["answer"].text == complete.text
