"""Market data endpoints: candles, screener, funds, TER drag — all fact-table reads."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Request
from fastapi.params import Query

from coresat.domain.portfolio import CandleBar, FundRow, ScreenerRow, TerDrag
from coresat.services.analytics import AnalyticsService

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
