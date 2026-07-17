"""Stock comparison API models."""

from pydantic import BaseModel, Field


class CompareRequest(BaseModel):
    tickers: list[str] = Field(min_length=2, max_length=4)
    portfolio_id: int


class CriterionVerdict(BaseModel):
    criterion: str
    winner: str
    reasoning: str


class TickerAssessment(BaseModel):
    """Per-ticker pros and cons (pravafin comparison structure)."""

    ticker: str
    pros: list[str]
    cons: list[str]


class ComparisonVerdicts(BaseModel):
    """Shape the LLM must produce (enforced by the output parser)."""

    per_criterion: list[CriterionVerdict]
    per_ticker: list[TickerAssessment]
    recommendation: str
    summary: str
    caveats: list[str]


class ComparisonResult(ComparisonVerdicts):
    tickers: list[str]
    model: str
