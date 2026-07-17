"""Market data endpoints: candles, screener, funds, TER drag — all fact-table reads."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Request
from fastapi.params import Query

from coresat.domain.portfolio import (
    CandleBar,
    FundRow,
    IndicatorPoint,
    ScreenerRow,
    TerDrag,
    YearlyFinancials,
)
from coresat.services.analytics import AnalyticsService
from coresat.services.indicators import indicator_points

router = APIRouter(prefix="/market", tags=["market"])


def _analytics(request: Request) -> AnalyticsService:
    service: AnalyticsService = request.app.state.analytics_service
    return service


@router.get("/candles/{ticker}")
async def candles(
    ticker: str,
    request: Request,
    days: Annotated[int | None, Query(ge=1)] = None,
) -> list[CandleBar]:
    bars = await _analytics(request).candles(ticker, days)
    if not bars:
        raise HTTPException(status_code=404, detail=f"no prices for {ticker}")
    return bars


@router.get("/indicators/{ticker}")
async def indicators(
    ticker: str,
    request: Request,
    days: Annotated[int | None, Query(ge=1)] = None,
) -> list[IndicatorPoint]:
    # full history feeds the warm-up windows; `days` only slices the tail
    bars = await _analytics(request).candles(ticker, None)
    if not bars:
        raise HTTPException(status_code=404, detail=f"no prices for {ticker}")
    points = indicator_points(bars)
    if days is not None:
        points = points[-days:]
    return points


@router.get("/financials/{ticker}")
async def financials(ticker: str, request: Request) -> list[YearlyFinancials]:
    series = await _analytics(request).yearly_financials(ticker)
    if not series:
        raise HTTPException(status_code=404, detail=f"no yearly financials for {ticker}")
    return series


@router.get("/screener")
async def screener(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> list[ScreenerRow]:
    return await _analytics(request).screener(limit)


@router.get("/funds")
async def funds(request: Request) -> list[FundRow]:
    return await _analytics(request).funds()


@router.get("/ter-drag")
async def ter_drag(
    request: Request,
    fund: str,
    capital: Annotated[float, Query(gt=0)] = 10_000,
    years: Annotated[int, Query(ge=1, le=50)] = 20,
) -> TerDrag:
    result = await _analytics(request).ter_drag(fund, capital, years)
    if result is None:
        raise HTTPException(status_code=404, detail=f"fund {fund} not found or lacks CAGR")
    return result
