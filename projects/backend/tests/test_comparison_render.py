"""Facts rendering: values must reach the LLM in human units.

Money columns render compact (89.263B, 5M) and fraction columns as percents
(28.69%) so the model quotes readable figures verbatim. The grounding set holds
exactly the rendered mantissas; numbers_grounded() requires any B/M-suffixed
figure in the output to match the set regardless of the small-number ceiling.
"""

from decimal import Decimal

import coresat.services as css


def _row(**values: object) -> dict[str, object]:
    return {"ticker": "TST", "name": "Test Corp", **values}


def test_plain_columns_round_to_six_significant_figures() -> None:
    table, numbers = css.render_facts([_row(pe_trailing=Decimal("24.08432200000000023010215955"))])
    assert "24.0843" in table
    assert "24.08432200000000023010215955" not in table
    assert Decimal("24.0843") in numbers


def test_money_columns_render_compact_billions() -> None:
    table, numbers = css.render_facts([_row(market_cap=Decimal("141647790080"))])
    assert "141.648B" in table
    assert Decimal("141.648") in numbers


def test_money_columns_render_compact_millions() -> None:
    table, numbers = css.render_facts([_row(revenue=Decimal("5000000"))])
    assert "5M" in table
    assert Decimal("5") in numbers


def test_small_money_stays_plain() -> None:
    table, numbers = css.render_facts([_row(net_profit=Decimal("500000"))])
    assert "500000" in table
    assert Decimal("500000") in numbers


def test_fraction_columns_render_as_percent() -> None:
    table, numbers = css.render_facts([_row(profit_margin=Decimal("0.222269999999999995"))])
    assert "22.23%" in table
    assert Decimal("22.23") in numbers


def test_none_renders_na() -> None:
    table, _ = css.render_facts([_row(market_cap=None)])
    assert "n/a" in table


def test_guard_rejects_unmatched_suffixed_number_even_below_ceiling() -> None:
    assert not css.numbers_grounded("market cap of 93.5B", {Decimal("89.263")})
    assert css.numbers_grounded("market cap of 89.263B", {Decimal("89.263")})


def test_guard_still_allows_small_plain_numbers() -> None:
    assert css.numbers_grounded("ranked in the top 10 of 65 stocks", set())


def test_guard_rejects_large_raw_numbers_not_in_facts() -> None:
    assert not css.numbers_grounded("revenue of 987654321000 dominates", {Decimal("89.263")})


def test_guard_does_not_treat_word_initials_as_suffix() -> None:
    # "5 Million" — the M of Million must not bind as a unit suffix
    assert css.numbers_grounded("worth 5 Million according to filings", set())
