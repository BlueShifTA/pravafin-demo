"""Projection math (unit, golden values pin the formula)."""

import pytest
from coresat.services.projection import project

# FV = C·(1+r)^n + A·((1+r)^n - 1)/r, A = annual contribution


def test_lump_sum_only_compounds() -> None:
    result = project(capital=10_000, monthly_contribution=0, annual_rate=0.07, years=10)
    assert result.expected == pytest.approx(10_000 * 1.07**10, rel=1e-9)


def test_contributions_accumulate() -> None:
    result = project(capital=0, monthly_contribution=100, annual_rate=0.05, years=10)
    annual = 1200
    expected = annual * ((1.05**10 - 1) / 0.05)
    assert result.expected == pytest.approx(expected, rel=1e-9)


def test_zero_rate_is_linear() -> None:
    result = project(capital=1_000, monthly_contribution=100, annual_rate=0.0, years=5)
    assert result.expected == pytest.approx(1_000 + 100 * 12 * 5, rel=1e-9)


def test_band_is_plus_minus_one_percent() -> None:
    result = project(capital=10_000, monthly_contribution=0, annual_rate=0.07, years=20)
    assert result.low == pytest.approx(10_000 * 1.06**20, rel=1e-9)
    assert result.high == pytest.approx(10_000 * 1.08**20, rel=1e-9)


def test_negative_years_rejected() -> None:
    with pytest.raises(ValueError):
        project(capital=1, monthly_contribution=0, annual_rate=0.05, years=-1)
