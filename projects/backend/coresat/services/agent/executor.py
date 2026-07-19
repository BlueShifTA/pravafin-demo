"""Pure-code plan execution: dependency levels, parallel steps, typed errors."""

import asyncio
import logging

import coresat.domain as csd
from coresat.services.agent.tools import Tool

log = logging.getLogger(__name__)


class Executor:
    def __init__(self, tools: dict[csd.ToolName, Tool]) -> None:
        self._tools: dict[csd.ToolName, Tool] = tools

    async def execute(self, plan: csd.Plan) -> list[csd.Evidence]:
        done: dict[int, csd.Evidence] = {}
        remaining = list(plan.steps)
        while remaining:
            ready = [step for step in remaining if all(dep in done for dep in step.depends_on)]
            if not ready:
                # Cycle or dangling depends_on from the planner: fail the
                # stuck steps explicitly so the synthesiser can surface them.
                for step in remaining:
                    done[step.id] = csd.Evidence(
                        step_id=step.id,
                        source="error",
                        content="",
                        error="unresolvable dependencies",
                    )
                break
            results = await asyncio.gather(*(self._run_step(step) for step in ready))
            for evidence in results:
                done[evidence.step_id] = evidence
            remaining = [step for step in remaining if step.id not in done]
        return [done[step.id] for step in plan.steps]

    async def _run_step(self, step: csd.Step) -> csd.Evidence:
        tool = self._tools.get(step.tool)
        if tool is None:
            return csd.Evidence(
                step_id=step.id,
                source="error",
                content="",
                error=f"no tool registered for '{step.tool}'",
            )
        try:
            return await tool.run(step)
        except Exception as exc:
            # must become typed evidence, never a crashed request.
            log.exception("tool %s failed for step %d", step.tool, step.id)
            return csd.Evidence(
                step_id=step.id,
                source="error",
                content="",
                error=f"{type(exc).__name__}: {exc}",
            )
