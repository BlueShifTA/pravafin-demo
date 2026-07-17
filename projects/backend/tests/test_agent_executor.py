"""Executor: dependency-ordered plan execution with typed error evidence."""

import asyncio

from coresat.domain.agent import Evidence, Plan, Step, ToolName
from coresat.services.agent.executor import Executor


class RecordingTool:
    """Fake tool that records call order and answers with its own name."""

    def __init__(self, name: str, calls: list[int]) -> None:
        self.name: str = name
        self.calls: list[int] = calls

    async def run(self, step: Step) -> Evidence:
        self.calls.append(step.id)
        await asyncio.sleep(0)
        return Evidence(step_id=step.id, source=self.name, content=f"answer {step.id}", error=None)


class ExplodingTool:
    async def run(self, step: Step) -> Evidence:
        raise ValueError("boom")


def _plan(*steps: Step) -> Plan:
    return Plan(steps=list(steps))


async def test_independent_steps_all_execute_and_keep_plan_order() -> None:
    calls: list[int] = []
    executor = Executor({ToolName.RUN_SQL: RecordingTool("run_sql", calls)})
    plan = _plan(
        Step(id=1, question="q1", tool=ToolName.RUN_SQL),
        Step(id=2, question="q2", tool=ToolName.RUN_SQL),
    )
    evidence = await executor.execute(plan)
    assert [e.step_id for e in evidence] == [1, 2]
    assert all(e.error is None for e in evidence)
    assert sorted(calls) == [1, 2]


async def test_dependent_step_runs_after_its_prerequisite() -> None:
    calls: list[int] = []
    executor = Executor({ToolName.RUN_SQL: RecordingTool("run_sql", calls)})
    plan = _plan(
        Step(id=1, question="first", tool=ToolName.RUN_SQL),
        Step(id=2, question="second", tool=ToolName.RUN_SQL, depends_on=[1]),
    )
    await executor.execute(plan)
    assert calls == [1, 2]


async def test_cyclic_dependencies_yield_error_evidence_not_hang() -> None:
    executor = Executor({ToolName.RUN_SQL: RecordingTool("run_sql", [])})
    plan = _plan(
        Step(id=1, question="a", tool=ToolName.RUN_SQL, depends_on=[2]),
        Step(id=2, question="b", tool=ToolName.RUN_SQL, depends_on=[1]),
    )
    evidence = await executor.execute(plan)
    assert [e.error for e in evidence] == ["unresolvable dependencies"] * 2


async def test_unregistered_tool_becomes_error_evidence() -> None:
    executor = Executor({})
    plan = _plan(Step(id=1, question="q", tool=ToolName.GAP))
    evidence = await executor.execute(plan)
    assert evidence[0].error is not None
    assert "gap" in evidence[0].error


async def test_tool_exception_becomes_error_evidence() -> None:
    executor = Executor({ToolName.RUN_SQL: ExplodingTool()})
    plan = _plan(Step(id=1, question="q", tool=ToolName.RUN_SQL))
    evidence = await executor.execute(plan)
    assert evidence[0].error == "ValueError: boom"
    assert evidence[0].content == ""
