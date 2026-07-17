"""Deterministic growth projection — the LLM never computes these numbers."""

from dataclasses import dataclass

_BAND = 0.01  # sensitivity band: rate ± 1 percentage point


@dataclass(frozen=True)
class Projection:
    years: int
    annual_rate: float
    expected: float
    low: float
    high: float


def _future_value(capital: float, annual_contribution: float, rate: float, years: int) -> float:
    growth = (1 + rate) ** years
    if rate == 0:
        return capital + annual_contribution * years
    return capital * growth + annual_contribution * ((growth - 1) / rate)


def project(
    capital: float, monthly_contribution: float, annual_rate: float, years: int
) -> Projection:
    """FV = C·(1+r)^n + A·((1+r)^n - 1)/r with A = 12·monthly (annual approximation)."""
    if years < 0:
        raise ValueError("years must be >= 0")
    annual = monthly_contribution * 12
    return Projection(
        years=years,
        annual_rate=annual_rate,
        expected=_future_value(capital, annual, annual_rate, years),
        low=_future_value(capital, annual, annual_rate - _BAND, years),
        high=_future_value(capital, annual, annual_rate + _BAND, years),
    )
