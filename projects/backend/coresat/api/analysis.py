"""Single-stock analysis endpoint: fixed-shape question → one grounded LLM call."""

import logging

from fastapi import APIRouter, HTTPException, Request

import coresat.domain as csd
import coresat.services as css

log = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/stock")
async def analyze_stock(spec: csd.AnalyzeRequest, request: Request) -> csd.AnalysisResult:
    service: css.AnalysisService = request.app.state.analysis_service
    try:
        return await service.analyze(spec.ticker, spec.portfolio_id)
    except css.UnknownTickerError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except css.FabricatedNumberError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except ConnectionError as error:
        log.exception("LLM unavailable")
        raise HTTPException(status_code=503, detail="LLM backend unavailable") from error
