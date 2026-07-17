"""Copilot graph: scope_guard → planner → execute → synthesise → validate.

LLM calls happen in exactly three nodes (scope_guard, planner, synthesiser);
execution and grounding validation are plain code. One re-plan allowed, then
an honest refusal — never an ungrounded answer.
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from coresat.domain.agent import Answer, Evidence, Plan, ScopeVerdict
from coresat.services.agent.executor import Executor
from coresat.services.agent.llm import AgentLLM
from coresat.services.grounding import extract_numbers, numbers_grounded

OFF_TOPIC_TEXT = (
    "I can only help with your portfolio, funds, stocks, and market data. "
    "Please ask an investing question."
)
CANNOT_ANSWER_TEXT = (
    "I cannot answer that from the data I have — the figures I gathered do not "
    "support a grounded answer."
)


class NodeUsage(TypedDict):
    node: str
    tokens_in: int
    tokens_out: int


class AgentState(TypedDict):
    query: str
    context: str
    scope: ScopeVerdict | None
    plan: Plan | None
    evidence: list[Evidence]
    answer: Answer | None
    grounded: bool
    replanned: bool
    validation_error: str | None
    usage: list[NodeUsage]


def initial_state(query: str, context: str) -> AgentState:
    return AgentState(
        query=query,
        context=context,
        scope=None,
        plan=None,
        evidence=[],
        answer=None,
        grounded=False,
        replanned=False,
        validation_error=None,
        usage=[],
    )


def _spent(state: AgentState, node: str, tokens_in: int, tokens_out: int) -> list[NodeUsage]:
    return [*state["usage"], NodeUsage(node=node, tokens_in=tokens_in, tokens_out=tokens_out)]


def build_graph(
    llm: AgentLLM, executor: Executor
) -> CompiledStateGraph[AgentState, None, AgentState, AgentState]:
    async def scope_guard(state: AgentState) -> dict[str, object]:
        verdict, usage = await llm.classify_scope(state["query"], state["context"])
        return {
            "scope": verdict,
            "usage": _spent(state, "scope_guard", usage.tokens_in, usage.tokens_out),
        }

    async def refuse(state: AgentState) -> dict[str, object]:  # noqa: ARG001
        # LangGraph node signatures require the parameter named `state`,
        # even though this node only writes a constant update.
        return {"answer": Answer(text=OFF_TOPIC_TEXT), "grounded": True}

    async def planner(state: AgentState) -> dict[str, object]:
        plan, usage = await llm.plan(state["query"], state["context"], state["validation_error"])
        return {
            "plan": plan,
            "usage": _spent(state, "planner", usage.tokens_in, usage.tokens_out),
        }

    async def execute(state: AgentState) -> dict[str, object]:
        plan = state["plan"]
        if plan is None:
            raise RuntimeError("executor reached without a plan")
        return {"evidence": await executor.execute(plan)}

    async def synthesise(state: AgentState) -> dict[str, object]:
        answer, usage = await llm.synthesise(state["query"], state["context"], state["evidence"])
        return {
            "answer": answer,
            "usage": _spent(state, "synthesiser", usage.tokens_in, usage.tokens_out),
        }

    async def validate(state: AgentState) -> dict[str, object]:
        answer = state["answer"]
        if answer is None:
            raise RuntimeError("validator reached without an answer")
        evidence_numbers = {
            number
            for item in state["evidence"]
            if item.error is None
            for number in extract_numbers(item.content)
        }
        grounded = numbers_grounded(answer.text, evidence_numbers)
        problems: list[str] = []
        if not grounded:
            problems.append("the answer quotes figures that appear in no gathered evidence")
        problems.extend(
            f"{item.source}#{item.step_id} failed: {item.error}"
            for item in state["evidence"]
            if item.error is not None
        )
        if answer.needs_replan:
            problems.append("the synthesiser judged the plan missed the question")
        return {
            "grounded": grounded,
            "validation_error": "; ".join(problems) if problems else None,
        }

    async def mark_replanned(state: AgentState) -> dict[str, object]:  # noqa: ARG001
        return {"replanned": True}

    async def give_up(state: AgentState) -> dict[str, object]:  # noqa: ARG001
        return {"answer": Answer(text=CANNOT_ANSWER_TEXT)}

    def route_after_scope(state: AgentState) -> str:
        scope = state["scope"]
        return "plan" if scope is not None and scope.in_scope else "refuse"

    def route_after_validate(state: AgentState) -> str:
        answer = state["answer"]
        wants_retry = not state["grounded"] or (answer is not None and answer.needs_replan)
        if wants_retry and not state["replanned"]:
            return "replan"
        if not state["grounded"]:
            return "give_up"
        return "end"

    builder: StateGraph[AgentState, None, AgentState, AgentState] = StateGraph(AgentState)
    builder.add_node("scope_guard", scope_guard)
    builder.add_node("refuse", refuse)
    builder.add_node("planner", planner)
    builder.add_node("execute", execute)
    builder.add_node("synthesise", synthesise)
    builder.add_node("validate", validate)
    builder.add_node("mark_replanned", mark_replanned)
    builder.add_node("give_up", give_up)
    builder.add_edge(START, "scope_guard")
    builder.add_conditional_edges(
        "scope_guard", route_after_scope, {"plan": "planner", "refuse": "refuse"}
    )
    builder.add_edge("refuse", END)
    builder.add_edge("planner", "execute")
    builder.add_edge("execute", "synthesise")
    builder.add_edge("synthesise", "validate")
    builder.add_conditional_edges(
        "validate",
        route_after_validate,
        {"replan": "mark_replanned", "give_up": "give_up", "end": END},
    )
    builder.add_edge("mark_replanned", "planner")
    builder.add_edge("give_up", END)
    return builder.compile()
