"""Single-stock analysis: one grounded LangChain call + deterministic MF match.

The magic-formula match tier is computed from the screener rank in code — the
LLM narrates strengths and weaknesses but never grades or computes.
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy.ext.asyncio import AsyncEngine

from coresat.domain.analysis import AnalysisNarrative, AnalysisResult
from coresat.services.analytics import AnalyticsService
from coresat.services.grounding import (
    FabricatedNumberError,
    fetch_facts,
    invoke_grounded,
    model_name_of,
    render_facts,
    write_audit,
)

_SCREENER_UNIVERSE = 500

_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an equity analyst. Analyze the company using ONLY the facts "
            "table provided. Quote numbers exactly as they appear in the table — never "
            "compute, extrapolate or invent figures, and write every figure in full "
            "digits (no abbreviations like 5M or 200k, no scientific notation). "
            "Write 2-4 concise strengths and 2-4 concise weaknesses as full sentences "
            "based only on metrics that have values; never mention or enumerate "
            "metrics marked n/a. Always include the caveats field (an empty list is "
            "fine). Answer in the requested JSON format.\n{format_instructions}",
        ),
        (
            "human",
            "Facts table:\n{facts}\n\nMagic-formula screener rank: {rank}\n\nAnalyze: {ticker}",
        ),
    ]
)


def _match_for_rank(rank: int | None) -> str:
    if rank is None:
        return "Unrated"
    if rank <= 10:
        return "Excellent"
    if rank <= 20:
        return "Good"
    if rank <= 40:
        return "Fair"
    return "Poor"


def _prose(narrative: AnalysisNarrative) -> str:
    return " ".join(
        [narrative.summary, *narrative.strengths, *narrative.weaknesses, *narrative.caveats]
    )


class AnalysisService:
    def __init__(
        self, engine: AsyncEngine, llm: BaseChatModel, analytics: AnalyticsService
    ) -> None:
        self._engine = engine
        self._llm = llm
        self._analytics = analytics
        self._parser: PydanticOutputParser[AnalysisNarrative] = PydanticOutputParser(
            pydantic_object=AnalysisNarrative
        )

    async def analyze(self, ticker: str, portfolio_id: int) -> AnalysisResult:
        facts_rows = await fetch_facts(self._engine, [ticker])
        facts_table, fact_numbers = render_facts(facts_rows)
        rank = await self._rank(ticker)
        prompt = _PROMPT.format_messages(
            format_instructions=self._parser.get_format_instructions(),
            facts=facts_table,
            rank="not ranked" if rank is None else str(rank),
            ticker=ticker,
        )
        narrative, tokens_in, tokens_out = await invoke_grounded(
            self._llm, self._parser, prompt, fact_numbers, _prose
        )
        await write_audit(
            self._engine, portfolio_id, "analysis", model_name_of(self._llm), tokens_in, tokens_out
        )
        if narrative is None:
            raise FabricatedNumberError(
                "analysis rejected: output contained fabricated numbers not present "
                "in the facts table"
            )
        return AnalysisResult(
            ticker=ticker,
            model=model_name_of(self._llm),
            magic_formula_match=_match_for_rank(rank),
            rank=rank,
            **narrative.model_dump(),
        )

    async def _rank(self, ticker: str) -> int | None:
        rows = await self._analytics.screener(_SCREENER_UNIVERSE)
        for row in rows:
            if row.ticker == ticker:
                return row.magic_rank
        return None
