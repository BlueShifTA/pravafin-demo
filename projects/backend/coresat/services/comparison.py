"""Stock comparison: one LangChain call, grounded by construction.

Facts injection, the fabrication guard and audit logging live in
`coresat.services.grounding` (shared with the single-stock analysis feature).
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy.ext.asyncio import AsyncEngine

import coresat.domain as csd
from coresat.services.grounding import (
    FabricatedNumberError,
    fetch_facts,
    invoke_grounded,
    model_name_of,
    render_facts,
    write_audit,
)

_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an equity analyst. Compare the companies using ONLY the facts "
            "table provided. Quote each value verbatim with its unit exactly as shown "
            "(% stays %, B means billions, M means millions) — never convert units, "
            "expand abbreviations, or compute new figures. "
            "For per_ticker give 2-3 one-sentence pros and 2-3 one-sentence cons per "
            "company based only on metrics that have values; never mention metrics "
            "marked n/a. End with a one-sentence recommendation naming the strongest "
            "pick. Answer in the requested JSON format.\n{format_instructions}",
        ),
        ("human", "Facts table:\n{facts}\n\nCompare: {tickers}"),
    ]
)


def _prose(verdicts: csd.ComparisonVerdicts) -> str:
    per_ticker = [
        line for assessment in verdicts.per_ticker for line in assessment.pros + assessment.cons
    ]
    return " ".join(
        [verdict.reasoning for verdict in verdicts.per_criterion]
        + per_ticker
        + [verdicts.recommendation, verdicts.summary]
        + verdicts.caveats
    )


class ComparisonService:
    def __init__(self, engine: AsyncEngine, llm: BaseChatModel) -> None:
        self._engine = engine
        self._llm = llm
        self._parser: PydanticOutputParser[csd.ComparisonVerdicts] = PydanticOutputParser(
            pydantic_object=csd.ComparisonVerdicts
        )

    async def compare(self, tickers: list[str], portfolio_id: int) -> csd.ComparisonResult:
        facts_rows = await fetch_facts(self._engine, tickers)
        facts_table, fact_numbers = render_facts(facts_rows)
        prompt = _PROMPT.format_messages(
            format_instructions=self._parser.get_format_instructions(),
            facts=facts_table,
            tickers=", ".join(tickers),
        )
        verdicts, tokens_in, tokens_out = await invoke_grounded(
            self._llm, self._parser, prompt, fact_numbers, _prose
        )
        await write_audit(
            self._engine,
            portfolio_id,
            "comparison",
            model_name_of(self._llm),
            tokens_in,
            tokens_out,
        )
        if verdicts is None:
            raise FabricatedNumberError(
                "comparison rejected: output contained fabricated numbers not present "
                "in the facts table"
            )
        return csd.ComparisonResult(
            tickers=tickers, model=model_name_of(self._llm), **verdicts.model_dump()
        )
