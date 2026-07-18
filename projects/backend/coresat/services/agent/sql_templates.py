"""Vetted SQL query patterns — the single source of truth for planner SQL.

Both agent planners render these into their prompts (via templates_block) so the
small model copies known-good SELECTs over the real fact-table columns instead
of inventing them; the graph's self-correcting retry loop repairs whatever still
drifts. Keeping the patterns here — not buried inside the prompt strings — means
they are edited, reviewed, and executed against the live schema in one place
(test_sql_templates runs every one), so a mistyped column fails a test rather
than a live agent turn.

Each value is a complete, runnable SELECT over the shared read-all fact tables
(instruments, fundamentals, funds, fund_holdings). Literals (tickers, LIMIT,
sector text) are placeholders the planner adapts per question.
"""

TOP_STOCKS_BY_MARKET_CAP = (
    "SELECT i.ticker, i.name, i.sector, f.market_cap "
    "FROM instruments i JOIN fundamentals f ON f.instrument_id = i.id "
    "WHERE i.type = 'stock' ORDER BY f.market_cap DESC NULLS LAST LIMIT 5"
)
STOCKS_BY_TICKER = "SELECT ticker, name, sector FROM instruments WHERE ticker IN ('NVDA', 'AAPL')"
FUND_BY_TICKER = (
    "SELECT ticker, name, ter, fund_size, cagr_5y, cagr_10y FROM funds WHERE ticker = 'IWDA.AS'"
)
LIST_FUNDS = "SELECT ticker, name, ter, fund_size FROM funds ORDER BY fund_size DESC NULLS LAST"
RANK_STOCKS_BY_FUNDAMENTAL = (
    "SELECT i.ticker, i.name, f.roe, f.pe_trailing "
    "FROM instruments i JOIN fundamentals f ON f.instrument_id = i.id "
    "WHERE i.type = 'stock' AND f.free_cashflow > 0 "
    "ORDER BY f.roe DESC NULLS LAST LIMIT 10"
)
STOCKS_IN_SECTOR = (
    "SELECT i.ticker, i.name, i.sector FROM instruments i "
    "WHERE i.type = 'stock' AND (i.sector ILIKE '%tech%' OR i.sector ILIKE '%semi%') "
    "LIMIT 10"
)
ETF_SECTOR_EXPOSURE = (
    "SELECT f.ticker, fh.sector, SUM(fh.weight) AS weight "
    "FROM fund_holdings fh JOIN funds f ON f.id = fh.fund_id "
    "WHERE f.ticker = 'IWDA.AS' GROUP BY f.ticker, fh.sector ORDER BY weight DESC"
)
DISTINCT_STOCK_SECTORS = "SELECT DISTINCT sector FROM instruments WHERE type = 'stock'"


# (intent label shown to the planner, template SQL) — order = prompt order.
SQL_TEMPLATES: tuple[tuple[str, str], ...] = (
    ("top N stocks by size", TOP_STOCKS_BY_MARKET_CAP),
    ("look up specific tickers the user named", STOCKS_BY_TICKER),
    ("look up a named ETF/fund", FUND_BY_TICKER),
    ("list the available ETFs/funds", LIST_FUNDS),
    ("rank stock picks by fundamentals (upside)", RANK_STOCKS_BY_FUNDAMENTAL),
    ("stocks in a sector", STOCKS_IN_SECTOR),
    ("an ETF's sector breakdown", ETF_SECTOR_EXPOSURE),
    ("discover the distinct sectors", DISTINCT_STOCK_SECTORS),
)


def templates_block() -> str:
    """Render the templates as a planner-prompt block."""
    lines = [
        "Known-good SQL patterns — copy the closest one and adapt only its"
        " literals (tickers, LIMIT, sector text); never invent column names:"
    ]
    for intent, sql in SQL_TEMPLATES:
        lines.append(f"- {intent}:\n    {sql}")
    return "\n".join(lines)
