"""Typed models shared by the copilot LangGraph agent and the API layer.

Ported from the LocalAI plan-mode agent (docs/ARCHITECTURE.md §7 reuse map) and
adapted to CoreSat's tool surface: SQL facts and deterministic projections.
"""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ToolName(StrEnum):
    RUN_SQL = "run_sql"
    GET_PROJECTION = "get_projection"
    RAG_SEARCH = "rag_search"
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

    @model_validator(mode="before")
    @classmethod
    def _accept_bare_step_list(cls, data: object) -> object:
        # Small models routinely emit the steps array directly instead of the
        # wrapped {"steps": [...]} object. Accept both so a valid plan is not
        # discarded and the agent degraded to an empty plan.
        if isinstance(data, list):
            return {"steps": data}
        return data


class Evidence(BaseModel):
    step_id: int
    source: str
    content: str
    error: str | None


class DraftPosition(BaseModel):
    ticker: str
    weight: float


class PortfolioDraft(BaseModel):
    name: str
    initial_capital: float
    monthly_contribution: float
    # One or more passive core ETFs (ticker + weight); the user may ask for a
    # multi-ETF core (e.g. SCHG + SCHD). Satellites are the stock picks.
    cores: list[DraftPosition]
    satellites: list[DraftPosition]


class Answer(BaseModel):
    text: str
    # Defaults tolerated: small local models occasionally emit partial JSON
    # (e.g. only "text"); missing list/bool fields must not crash the graph.
    citations: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    needs_replan: bool = False
    # Draft-agent fields; the copilot leaves them at the defaults. "propose"
    # attaches a complete draft for the user to confirm; "create" is emitted
    # only after the user confirms a shown proposal.
    action: Literal["chat", "propose", "create"] = "chat"
    draft: PortfolioDraft | None = None


class ScopeVerdict(BaseModel):
    in_scope: bool
