"""Facts rendering: float-noise decimals must be rounded before prompting.

Raw DOUBLE PRECISION values arrive as 28-digit Decimals
(24.08432200000000023010215955); rendered verbatim they bloat the prompt and
the model misquotes digits, tripping the fabrication guard. Render rounds to
6 significant figures and the grounding set must contain exactly the rendered
values.
"""

from decimal import Decimal

from coresat.services.grounding import render_facts


def _row(**values: object) -> dict[str, object]:
    return {"ticker": "TST", "name": "Test Corp", **values}


def test_float_noise_is_rounded_to_six_significant_figures() -> None:
    table, numbers = render_facts([_row(pe_trailing=Decimal("24.08432200000000023010215955"))])
    assert "24.0843" in table
    assert "24.08432200000000023010215955" not in table
    assert Decimal("24.0843") in numbers


def test_large_integers_round_to_six_significant_figures() -> None:
    table, numbers = render_facts([_row(market_cap=Decimal("141647790080"))])
    assert "141648000000" in table
    assert Decimal("141648000000") in numbers


def test_grounding_set_matches_rendered_values_only() -> None:
    _, numbers = render_facts(
        [_row(revenue=Decimal("27687000064"), profit_margin=Decimal("0.222269999999999995"))]
    )
    assert numbers == {Decimal("27687000000"), Decimal("0.22227")}


def test_zero_and_none_survive() -> None:
    table, numbers = render_facts([_row(revenue=Decimal("0"), market_cap=None)])
    assert "n/a" in table
    assert Decimal("0") in numbers
