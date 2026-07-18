"""GroundedAgent: the one generic agent core — both agents are instances.

Wraps the LangGraph graph (scope_guard → planner → execute → synthesise →
grounding validator, one re-plan) behind a typed event stream. Feature glue
(persistence, SSE encoding, create rails) lives in the services that hold an
instance; a policy fix here fixes every agent.
"""

from collections.abc import AsyncIterator
from typing import NamedTuple

from coresat.domain.agent import Answer, Evidence, Plan, ToolName
from coresat.services.agent.executor import Executor
from coresat.services.agent.graph import NodeUsage, build_graph, initial_state
from coresat.services.agent.llm import AgentLLM
from coresat.services.agent.tools import Tool


class PlanEmitted(NamedTuple):
    plan: Plan


class EvidenceGathered(NamedTuple):
    evidence: list[Evidence]


class AnswerReady(NamedTuple):
    answer: Answer
    evidence: list[Evidence]
    usage: list[NodeUsage]


AgentEvent = PlanEmitted | EvidenceGathered | AnswerReady


class GroundedAgent:
    def __init__(self, llm: AgentLLM) -> None:
        self._llm: AgentLLM = llm

    async def run(
        self, query: str, context: str, tools: dict[ToolName, Tool]
    ) -> AsyncIterator[AgentEvent]:
        graph = build_graph(self._llm, Executor(tools))
        answer: Answer | None = None
        evidence: list[Evidence] = []
        usage: list[NodeUsage] = []
        async for update in graph.astream(initial_state(query, context), stream_mode="updates"):
            for node_state in update.values():
                if "usage" in node_state:
                    usage = list(node_state["usage"])
                plan = node_state.get("plan")
                if isinstance(plan, Plan):
                    yield PlanEmitted(plan=plan)
                if "evidence" in node_state:
                    evidence = list(node_state["evidence"])
                    yield EvidenceGathered(evidence=evidence)
                if isinstance(node_state.get("answer"), Answer):
                    answer = node_state["answer"]
        if answer is None:  # a graph bug, not a user error — surface loudly
            raise RuntimeError("agent graph produced no answer")
        yield AnswerReady(answer=answer, evidence=evidence, usage=usage)
