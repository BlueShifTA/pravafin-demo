"""Shared grounded-LLM infrastructure: facts injection, fabrication guard, audit.

All numeric facts are fetched by SQL and injected into the prompt; the LLM
writes prose and verdicts but never computes a figure. A post-hoc guard rejects
any large number in the output that does not appear in the injected facts.
"""

import re
from collections.abc import Callable
from decimal import Decimal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from coresat.db.session import portfolio_scope
from coresat.services.portfolios import UnknownTickerError

# numbers below this are allowed unmatched: ordinals, ratios, percentages the
# model may legitimately phrase ("3 times", "top 2") without fabricating facts.
# B/M-suffixed figures are exempt from the ceiling — a fabricated "93.5B" is
# small as a mantissa but must still match the injected facts.
_SMALL_NUMBER_CEILING = 100.0
_NUMBER_PATTERN = re.compile(r"(-?\d[\d,]*\.?\d*)\s?([BM%](?![A-Za-z]))?")

FACT_COLUMNS = (
    "pe_trailing",
    "pe_forward",
    "market_cap",
    "revenue",
    "net_profit",
    "profit_margin",
    "roe",
    "dividend_yield",
    "beta",
    "price_to_book",
    "debt_to_equity",
    "free_cashflow",
    "cagr_5y",
    "cagr_10y",
    "ebit",
)

# money renders compact (B/M) and fractions as percents so the model quotes
# human-readable figures verbatim instead of raw 11-digit values
_MONEY_COLUMNS = frozenset({"market_cap", "revenue", "net_profit", "free_cashflow", "ebit"})
_FRACTION_COLUMNS = frozenset({"profit_margin", "roe", "cagr_5y", "cagr_10y"})


class FabricatedNumberError(ValueError):
    """LLM output contained a figure that is not in the injected facts."""


async def fetch_facts(engine: AsyncEngine, tickers: list[str]) -> list[dict[str, object]]:
    async with engine.connect() as conn:
        rows = (
            (
                await conn.execute(
                    text(
                        "SELECT i.ticker, i.name, i.sector, f.* FROM fundamentals f "
                        "JOIN instruments i ON i.id = f.instrument_id "
                        "WHERE i.ticker = ANY(:tickers)"
                    ),
                    {"tickers": tickers},
                )
            )
            .mappings()
            .all()
        )
    found = {str(row["ticker"]) for row in rows}
    missing = set(tickers) - found
    if missing:
        raise UnknownTickerError(f"no fundamentals for: {sorted(missing)}")
    return [dict(row) for row in rows]


def six_significant_figures(value: Decimal) -> Decimal:
    # raw DOUBLE PRECISION values arrive as 28-digit Decimals that bloat the
    # prompt and get misquoted by the model, tripping the fabrication guard
    if value == 0:
        return value
    return value.quantize(Decimal(1).scaleb(value.adjusted() - 5)).normalize()


def _render_value(column: str, value: object) -> tuple[str, Decimal]:
    decimal_value = Decimal(str(value)).normalize()
    if column in _FRACTION_COLUMNS:
        percent = (decimal_value * 100).quantize(Decimal("0.01")).normalize()
        return f"{format(percent, 'f')}%", percent
    if column in _MONEY_COLUMNS and abs(decimal_value) >= 1_000_000:
        scale, suffix = (9, "B") if abs(decimal_value) >= 1_000_000_000 else (6, "M")
        mantissa = (decimal_value.scaleb(-scale)).quantize(Decimal("0.001")).normalize()
        return f"{format(mantissa, 'f')}{suffix}", mantissa
    rounded = six_significant_figures(decimal_value)
    return format(rounded, "f"), rounded


def render_facts(rows: list[dict[str, object]]) -> tuple[str, set[Decimal]]:
    # One "column: value" line per fact — a wide pipe table makes small models
    # misattribute columns (e.g. read debt_to_equity as free cash flow), which
    # the fabrication guard then rejects.
    blocks: list[str] = []
    numbers: set[Decimal] = set()
    for row in rows:
        lines = [f"{row['ticker']} ({row['name']})"]
        for column in FACT_COLUMNS:
            value = row.get(column)
            if value is None:
                lines.append(f"  {column}: n/a")
            else:
                rendered, grounded_number = _render_value(column, value)
                numbers.add(grounded_number)
                lines.append(f"  {column}: {rendered}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks), numbers


def extract_numbers(source_text: str) -> set[Decimal]:
    """All numbers in a text, normalised the way numbers_grounded compares them."""
    numbers: set[Decimal] = set()
    for number_text, _suffix in _NUMBER_PATTERN.findall(source_text):
        numbers.add(Decimal(number_text.replace(",", "")).normalize())
    return numbers


def numbers_grounded(prose: str, fact_numbers: set[Decimal]) -> bool:
    for number_text, suffix in _NUMBER_PATTERN.findall(prose):
        candidate = Decimal(number_text.replace(",", "")).normalize()
        if suffix in ("B", "M"):
            if candidate not in fact_numbers:
                return False
        elif abs(candidate) <= Decimal(str(_SMALL_NUMBER_CEILING)):
            continue
        elif candidate not in fact_numbers:
            return False
    return True


async def invoke_grounded[VerdictT: BaseModel](
    llm: BaseChatModel,
    parser: PydanticOutputParser[VerdictT],
    prompt: list[BaseMessage],
    fact_numbers: set[Decimal],
    prose_of: Callable[[VerdictT], str],
) -> tuple[VerdictT | None, int, int]:
    """Run the LLM with one retry on fabrication; return (verdict, tokens_in, tokens_out)."""
    verdict: VerdictT | None = None
    tokens_in = tokens_out = 0
    for _ in range(2):  # one retry on fabrication
        message = await llm.ainvoke(prompt)
        usage = getattr(message, "usage_metadata", None) or {}
        tokens_in += int(usage.get("input_tokens", 0))
        tokens_out += int(usage.get("output_tokens", 0))
        candidate = parser.parse(str(message.content))
        if numbers_grounded(prose_of(candidate), fact_numbers):
            verdict = candidate
            break
    return verdict, tokens_in, tokens_out


async def write_audit(
    engine: AsyncEngine,
    portfolio_id: int,
    feature: str,
    model_name: str,
    tokens_in: int,
    tokens_out: int,
) -> None:
    async with portfolio_scope(engine, portfolio_id) as conn:
        await conn.execute(
            text(
                "INSERT INTO llm_audit_log (portfolio_id, feature, model, tokens_in, "
                "tokens_out) VALUES (:pid, :feature, :model, :tokens_in, :tokens_out)"
            ),
            {
                "pid": portfolio_id,
                "feature": feature,
                "model": model_name,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
            },
        )


def model_name_of(llm: BaseChatModel) -> str:
    return str(getattr(llm, "model", llm.__class__.__name__))
