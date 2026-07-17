"""Typed models shared by the copilot LangGraph agent and the API layer.

Ported from the LocalAI plan-mode agent (ARCHITECTURE.md §7 reuse map) and
adapted to CoreSat's tool surface: SQL facts and deterministic projections.
"""

from enum import StrEnum

from pydantic import BaseModel, Field


class ToolName(StrEnum):
    RUN_SQL = "run_sql"
    GET_PROJECTION = "get_projection"
    GAP = "gap"


class Step(BaseModel):
    id: int
    question: str
    tool: ToolName
    # Defaults tolerated: the planner LLM omits depends_on for independent
    # steps and sql for non-SQL tools.
    depends_on: list[int] = Field(default_factory=list)
    sql: str | None = None


class Plan(BaseModel):
    steps: list[Step]


class Evidence(BaseModel):
    step_id: int
    source: str
    content: str
    error: str | None


class Answer(BaseModel):
    text: str
    # Defaults tolerated: small local models occasionally emit partial JSON
    # (e.g. only "text"); missing list/bool fields must not crash the graph.
    citations: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    needs_replan: bool = False


class ScopeVerdict(BaseModel):
    in_scope: bool
