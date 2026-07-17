"""Portfolio endpoints: wizard create, selector list, summary."""

from fastapi import APIRouter, HTTPException, Request

from coresat.domain.portfolio import (
    PortfolioCreate,
    PortfolioCreated,
    PortfolioListItem,
    PortfolioSummary,
)
from coresat.services.analytics import AnalyticsService
from coresat.services.portfolios import PortfolioService, UnknownTickerError

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


def _service(request: Request) -> PortfolioService:
    service: PortfolioService = request.app.state.portfolio_service
    return service


def _analytics(request: Request) -> AnalyticsService:
    service: AnalyticsService = request.app.state.analytics_service
    return service


@router.post("", status_code=201)
async def create_portfolio(spec: PortfolioCreate, request: Request) -> PortfolioCreated:
    try:
        portfolio_id = await _service(request).create(spec)
    except UnknownTickerError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return PortfolioCreated(id=portfolio_id)


@router.get("")
async def list_portfolios(request: Request) -> list[PortfolioListItem]:
    return await _service(request).list()


@router.get("/{portfolio_id}/summary")
async def portfolio_summary(portfolio_id: int, request: Request) -> PortfolioSummary:
    summary = await _analytics(request).summary(portfolio_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="portfolio not found")
    return summary
