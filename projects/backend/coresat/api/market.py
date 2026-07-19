"""Market data endpoints: candles, screener, funds, TER drag — all fact-table reads."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Request
from fastapi.params import Query

import coresat.domain as csd
import coresat.services as css

router = APIRouter(prefix="/market", tags=["market"])


def _analytics(request: Request) -> css.AnalyticsService:
    service: css.AnalyticsService = request.app.state.analytics_service
    return service


@router.get("/candles/{ticker}")
async def candles(
    ticker: str,
    request: Request,
    days: Annotated[int | None, Query(ge=1)] = None,
    interval: Annotated[str | None, Query()] = None,
) -> list[csd.CandleBar]:
    bars = await _analytics(request).candles(ticker, days, interval)
    if not bars:
        raise HTTPException(status_code=404, detail=f"no prices for {ticker}")
    return bars


@router.get("/indicators/{ticker}")
async def indicators(
    ticker: str,
    request: Request,
    days: Annotated[int | None, Query(ge=1)] = None,
) -> list[csd.IndicatorPoint]:
    # full history feeds the warm-up windows; `days` only slices the tail
    bars = await _analytics(request).candles(ticker, None, None)
    if not bars:
        raise HTTPException(status_code=404, detail=f"no prices for {ticker}")
    points = css.indicator_points(bars)
    if days is not None:
        points = points[-days:]
    return points


@router.get("/financials/{ticker}")
async def financials(ticker: str, request: Request) -> list[csd.YearlyFinancials]:
    series = await _analytics(request).yearly_financials(ticker)
    if not series:
        raise HTTPException(status_code=404, detail=f"no yearly financials for {ticker}")
    return series


@router.get("/screener")
async def screener(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> list[csd.ScreenerRow]:
    return await _analytics(request).screener(limit)


@router.get("/funds")
async def funds(
    request: Request,
    compare: Annotated[str | None, Query()] = None,
) -> list[csd.FundRow]:
    analytics = _analytics(request)
    if compare:
        tickers = [ticker.strip() for ticker in compare.split(",") if ticker.strip()]
        return await analytics.compare_funds(tickers)
    return await analytics.funds()


@router.get("/ter-drag")
async def ter_drag(
    request: Request,
    fund: str,
    capital: Annotated[float, Query(gt=0)] = 10_000,
    years: Annotated[int, Query(ge=1, le=50)] = 20,
) -> csd.TerDrag:
    result = await _analytics(request).ter_drag(fund, capital, years)
    if result is None:
        raise HTTPException(status_code=404, detail=f"fund {fund} not found or lacks CAGR")
    return result
