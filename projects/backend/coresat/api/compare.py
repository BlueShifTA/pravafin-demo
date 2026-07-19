"""Comparison endpoint: fixed-shape question → one grounded LLM call."""

import logging

from fastapi import APIRouter, HTTPException, Request

import coresat.domain as csd
import coresat.services as css

log = logging.getLogger(__name__)

router = APIRouter(prefix="/compare", tags=["compare"])


@router.post("")
async def compare(spec: csd.CompareRequest, request: Request) -> csd.ComparisonResult:
    service: css.ComparisonService = request.app.state.comparison_service
    try:
        return await service.compare(spec.tickers, spec.portfolio_id)
    except css.UnknownTickerError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except css.FabricatedNumberError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except ConnectionError as error:
        log.exception("LLM unavailable")
        raise HTTPException(status_code=503, detail="LLM backend unavailable") from error
