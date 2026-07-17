"""Single-stock analysis API models."""

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    ticker: str
    portfolio_id: int


class AnalysisNarrative(BaseModel):
    """Shape the LLM must produce (enforced by the output parser)."""

    summary: str
    strengths: list[str]
    weaknesses: list[str]
    caveats: list[str]


class AnalysisResult(AnalysisNarrative):
    ticker: str
    model: str
    magic_formula_match: str
    rank: int | None
