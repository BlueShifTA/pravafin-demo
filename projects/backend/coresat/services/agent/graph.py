"""Copilot graph: scope_guard → planner → execute → synthesise → validate.

LLM calls happen in exactly three nodes (scope_guard, planner, synthesiser);
execution and grounding validation are plain code. On any validation problem —
a fabricated figure, a failed run_sql, or a synthesiser-flagged miss — the
planner re-plans with the error fed back, up to MAX_ATTEMPTS times. If the data
still won't come, one rag_fallback tries the document corpus before an honest
refusal — never an ungrounded answer.
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

import coresat.domain as csd
from coresat.services.agent.executor import Executor
from coresat.services.agent.llm import AgentLLM
from coresat.services.grounding import extract_numbers, numbers_grounded

# Planner attempts before falling back to RAG. Each attempt re-plans with the
# prior error, so retries self-correct instead of repeating identical SQL. Kept
# low (3) because each attempt is a full LLM round-trip — more just stalls the
# user on a slow model without materially improving convergence.
MAX_ATTEMPTS = 3
# LangGraph super-step ceiling: MAX_ATTEMPTS loops of 4 nodes + scope + the
# rag_fallback tail. Set well above the worst path so a legitimate 5th retry is
# never cut off as a recursion error.
RECURSION_LIMIT = 60

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
    scope: csd.ScopeVerdict | None
    plan: csd.Plan | None
    evidence: list[csd.Evidence]
    answer: csd.Answer | None
    grounded: bool
    attempts: int
    rag_tried: bool
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
        attempts=0,
        rag_tried=False,
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
        return {"answer": csd.Answer(text=OFF_TOPIC_TEXT), "grounded": True}

    async def planner(state: AgentState) -> dict[str, object]:
        plan, usage = await llm.plan(state["query"], state["context"], state["validation_error"])
        return {
            "plan": plan,
            "attempts": state["attempts"] + 1,
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
        # grounded set = evidence numbers plus user-stated figures: capital,
        # weights and similar numbers come from the user's own words, not SQL
        # evidence, and must not trip the fabrication guard
        grounded_numbers = extract_numbers(state["query"]) | extract_numbers(state["context"])
        grounded_numbers |= {
            number
            for item in state["evidence"]
            if item.error is None
            for number in extract_numbers(item.content)
        }
        # A portfolio proposal (action propose/create) is a design, not a report:
        # its numbers — chosen weights, default capital/contribution, and blended
        # figures the model computes from the picks (weighted TER, weighted CAGR)
        # — are legitimately absent from the raw SQL evidence. The fabrication
        # guard, which requires every figure to appear verbatim in evidence, is
        # for factual Q&A (action chat) and must not gate a design. Tickers stay
        # evidence-bound through the synthesiser prompt, not this guard.
        is_design = answer.action in ("propose", "create")
        # A plan that ran retrieval steps but came back with only empty results,
        # "(no rows)", or errors gathered no facts. A refusal built on that carries
        # no figure, so the fabrication guard alone would wave it through — treat
        # empty retrieval as ungrounded so the graph re-plans, then tries the
        # document corpus, instead of shipping a first-pass "I cannot find it".
        # An empty plan (greeting, "where did that number come from") ran no
        # retrieval and is exempt: it legitimately answers from the conversation.
        plan = state["plan"]
        ran_retrieval = plan is not None and len(plan.steps) > 0
        gathered_facts = any(
            item.error is None and item.content.strip() not in ("", "(no rows)")
            for item in state["evidence"]
        )
        retrieval_empty = ran_retrieval and not gathered_facts and not is_design
        # An empty answer (e.g. the synthesiser's parse-failure fallback) is never
        # a valid grounded answer — treat it as ungrounded so it routes to the
        # rag fallback / honest refusal instead of streaming a blank bubble.
        grounded = (
            bool(answer.text.strip())
            and not retrieval_empty
            and (is_design or numbers_grounded(answer.text, grounded_numbers))
        )
        problems: list[str] = []
        if not answer.text.strip():
            problems.append("the synthesiser produced no answer text")
        elif retrieval_empty:
            problems.append(
                "every retrieval step returned no rows or errored — no facts were "
                "gathered to answer from"
            )
        elif not grounded:
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

    async def rag_fallback(state: AgentState) -> dict[str, object]:
        # SQL retries are exhausted and the answer still isn't grounded. Before
        # refusing, try the shared document corpus: one rag_search on the user's
        # question, then synthesise from whatever it returns. Both agents wire a
        # rag_search tool, so this always has somewhere to look.
        fallback_plan = csd.Plan(
            steps=[csd.Step(id=1, question=state["query"], tool=csd.ToolName.RAG_SEARCH)]
        )
        evidence = await executor.execute(fallback_plan)
        answer, usage = await llm.synthesise(state["query"], state["context"], evidence)
        return {
            "plan": fallback_plan,
            "evidence": evidence,
            "answer": answer,
            "rag_tried": True,
            "usage": _spent(state, "rag_fallback", usage.tokens_in, usage.tokens_out),
        }

    async def give_up(state: AgentState) -> dict[str, object]:  # noqa: ARG001
        return {"answer": csd.Answer(text=CANNOT_ANSWER_TEXT)}

    def route_after_scope(state: AgentState) -> str:
        scope = state["scope"]
        return "plan" if scope is not None and scope.in_scope else "refuse"

    def route_after_validate(state: AgentState) -> str:
        # Any validation problem (fabricated figure, failed run_sql, or a
        # synthesiser-flagged miss) is a retry trigger — retrying with the error
        # fed back is how the planner gets the data it missed.
        if state["validation_error"] is not None and state["attempts"] < MAX_ATTEMPTS:
            return "replan"
        if not state["grounded"] and not state["rag_tried"]:
            return "rag_fallback"
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
    builder.add_node("rag_fallback", rag_fallback)
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
        {"replan": "planner", "rag_fallback": "rag_fallback", "give_up": "give_up", "end": END},
    )
    builder.add_edge("rag_fallback", "validate")
    builder.add_edge("give_up", END)
    return builder.compile()
