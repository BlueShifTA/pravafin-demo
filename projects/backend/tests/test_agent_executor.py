"""Executor: dependency-ordered plan execution with typed error evidence."""

import asyncio

import coresat.domain as csd
import coresat.services.agent as csa


class RecordingTool:
    """Fake tool that records call order and answers with its own name."""

    def __init__(self, name: str, calls: list[int]) -> None:
        self.name: str = name
        self.calls: list[int] = calls

    async def run(self, step: csd.Step) -> csd.Evidence:
        self.calls.append(step.id)
        await asyncio.sleep(0)
        return csd.Evidence(
            step_id=step.id, source=self.name, content=f"answer {step.id}", error=None
        )


class ExplodingTool:
    async def run(self, step: csd.Step) -> csd.Evidence:
        raise ValueError("boom")


def _plan(*steps: csd.Step) -> csd.Plan:
    return csd.Plan(steps=list(steps))


async def test_independent_steps_all_execute_and_keep_plan_order() -> None:
    calls: list[int] = []
    executor = csa.Executor({csd.ToolName.RUN_SQL: RecordingTool("run_sql", calls)})
    plan = _plan(
        csd.Step(id=1, question="q1", tool=csd.ToolName.RUN_SQL),
        csd.Step(id=2, question="q2", tool=csd.ToolName.RUN_SQL),
    )
    evidence = await executor.execute(plan)
    assert [e.step_id for e in evidence] == [1, 2]
    assert all(e.error is None for e in evidence)
    assert sorted(calls) == [1, 2]


async def test_dependent_step_runs_after_its_prerequisite() -> None:
    calls: list[int] = []
    executor = csa.Executor({csd.ToolName.RUN_SQL: RecordingTool("run_sql", calls)})
    plan = _plan(
        csd.Step(id=1, question="first", tool=csd.ToolName.RUN_SQL),
        csd.Step(id=2, question="second", tool=csd.ToolName.RUN_SQL, depends_on=[1]),
    )
    await executor.execute(plan)
    assert calls == [1, 2]


async def test_cyclic_dependencies_yield_error_evidence_not_hang() -> None:
    executor = csa.Executor({csd.ToolName.RUN_SQL: RecordingTool("run_sql", [])})
    plan = _plan(
        csd.Step(id=1, question="a", tool=csd.ToolName.RUN_SQL, depends_on=[2]),
        csd.Step(id=2, question="b", tool=csd.ToolName.RUN_SQL, depends_on=[1]),
    )
    evidence = await executor.execute(plan)
    assert [e.error for e in evidence] == ["unresolvable dependencies"] * 2


async def test_unregistered_tool_becomes_error_evidence() -> None:
    executor = csa.Executor({})
    plan = _plan(csd.Step(id=1, question="q", tool=csd.ToolName.GAP))
    evidence = await executor.execute(plan)
    assert evidence[0].error is not None
    assert "gap" in evidence[0].error


async def test_tool_exception_becomes_error_evidence() -> None:
    executor = csa.Executor({csd.ToolName.RUN_SQL: ExplodingTool()})
    plan = _plan(csd.Step(id=1, question="q", tool=csd.ToolName.RUN_SQL))
    evidence = await executor.execute(plan)
    assert evidence[0].error == "ValueError: boom"
    assert evidence[0].content == ""
