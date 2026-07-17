"""Stock comparison: one LangChain call, grounded by construction.

All facts are fetched by SQL and injected into the prompt; the LLM writes prose
and verdicts but never computes a figure. A post-hoc guard rejects any large
number that does not appear in the injected facts (fabrication check).
"""

import re
from decimal import Decimal

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from coresat.db.session import portfolio_scope
from coresat.domain.comparison import ComparisonResult, ComparisonVerdicts
from coresat.services.portfolios import UnknownTickerError

# numbers below this are allowed unmatched: ordinals, ratios, percentages the
# model may legitimately phrase ("3 times", "top 2") without fabricating facts
_SMALL_NUMBER_CEILING = 100.0
_NUMBER_PATTERN = re.compile(r"-?\d[\d,]*\.?\d*")

_FACT_COLUMNS = (
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

_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an equity analyst. Compare the companies using ONLY the facts "
            "table provided. Quote numbers exactly as they appear in the table — never "
            "compute, extrapolate or invent figures. Answer in the requested JSON "
            "format.\n{format_instructions}",
        ),
        ("human", "Facts table:\n{facts}\n\nCompare: {tickers}"),
    ]
)


class FabricatedNumberError(ValueError):
    """LLM output contained a figure that is not in the injected facts."""


class ComparisonService:
    def __init__(self, engine: AsyncEngine, llm: BaseChatModel) -> None:
        self._engine = engine
        self._llm = llm
        self._parser: PydanticOutputParser[ComparisonVerdicts] = PydanticOutputParser(
            pydantic_object=ComparisonVerdicts
        )

    async def compare(self, tickers: list[str], portfolio_id: int) -> ComparisonResult:
        facts_rows = await self._fetch_facts(tickers)
        facts_table, fact_numbers = _render_facts(facts_rows)
        prompt = _PROMPT.format_messages(
            format_instructions=self._parser.get_format_instructions(),
            facts=facts_table,
            tickers=", ".join(tickers),
        )
        verdicts: ComparisonVerdicts | None = None
        tokens_in = tokens_out = 0
        for _ in range(2):  # one retry on fabrication
            message = await self._llm.ainvoke(prompt)
            usage = getattr(message, "usage_metadata", None) or {}
            tokens_in += int(usage.get("input_tokens", 0))
            tokens_out += int(usage.get("output_tokens", 0))
            candidate = self._parser.parse(str(message.content))
            if _numbers_grounded(candidate, fact_numbers):
                verdicts = candidate
                break
        await self._audit(portfolio_id, tokens_in, tokens_out)
        if verdicts is None:
            raise FabricatedNumberError(
                "comparison rejected: output contained fabricated numbers not present "
                "in the facts table"
            )
        model_name = getattr(self._llm, "model", self._llm.__class__.__name__)
        return ComparisonResult(tickers=tickers, model=str(model_name), **verdicts.model_dump())

    async def _fetch_facts(self, tickers: list[str]) -> list[dict[str, object]]:
        async with self._engine.connect() as conn:
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

    async def _audit(self, portfolio_id: int, tokens_in: int, tokens_out: int) -> None:
        model_name = getattr(self._llm, "model", self._llm.__class__.__name__)
        async with portfolio_scope(self._engine, portfolio_id) as conn:
            await conn.execute(
                text(
                    "INSERT INTO llm_audit_log (portfolio_id, feature, model, tokens_in, "
                    "tokens_out) VALUES (:pid, 'comparison', :model, :tokens_in, :tokens_out)"
                ),
                {
                    "pid": portfolio_id,
                    "model": str(model_name),
                    "tokens_in": tokens_in,
                    "tokens_out": tokens_out,
                },
            )


def _render_facts(rows: list[dict[str, object]]) -> tuple[str, set[Decimal]]:
    lines = ["ticker | " + " | ".join(_FACT_COLUMNS)]
    numbers: set[Decimal] = set()
    for row in rows:
        cells: list[str] = []
        for column in _FACT_COLUMNS:
            value = row.get(column)
            if value is None:
                cells.append("n/a")
            else:
                decimal_value = Decimal(str(value)).normalize()
                numbers.add(decimal_value)
                cells.append(str(decimal_value))
        lines.append(f"{row['ticker']} ({row['name']}) | " + " | ".join(cells))
    return "\n".join(lines), numbers


def _numbers_grounded(verdicts: ComparisonVerdicts, fact_numbers: set[Decimal]) -> bool:
    prose = " ".join(
        [verdict.reasoning for verdict in verdicts.per_criterion]
        + [verdicts.summary]
        + verdicts.caveats
    )
    for match in _NUMBER_PATTERN.findall(prose):
        candidate = Decimal(match.replace(",", "")).normalize()
        if abs(candidate) <= Decimal(str(_SMALL_NUMBER_CEILING)):
            continue
        if candidate not in fact_numbers:
            return False
    return True
