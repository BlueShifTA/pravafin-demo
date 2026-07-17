"""Comparison endpoint: fixed-shape question → one grounded LLM call."""

import logging

from fastapi import APIRouter, HTTPException, Request

from coresat.domain.comparison import CompareRequest, ComparisonResult
from coresat.services.comparison import ComparisonService, FabricatedNumberError
from coresat.services.portfolios import UnknownTickerError

log = logging.getLogger(__name__)

router = APIRouter(prefix="/compare", tags=["compare"])


@router.post("")
async def compare(spec: CompareRequest, request: Request) -> ComparisonResult:
    service: ComparisonService = request.app.state.comparison_service
    try:
        return await service.compare(spec.tickers, spec.portfolio_id)
    except UnknownTickerError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except FabricatedNumberError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except ConnectionError as error:
        log.exception("LLM unavailable")
        raise HTTPException(status_code=503, detail="LLM backend unavailable") from error
