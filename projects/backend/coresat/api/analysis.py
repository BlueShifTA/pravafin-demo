"""Single-stock analysis endpoint: fixed-shape question → one grounded LLM call."""

import logging

from fastapi import APIRouter, HTTPException, Request

from coresat.domain.analysis import AnalysisResult, AnalyzeRequest
from coresat.services.analysis import AnalysisService
from coresat.services.grounding import FabricatedNumberError
from coresat.services.portfolios import UnknownTickerError

log = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/stock")
async def analyze_stock(spec: AnalyzeRequest, request: Request) -> AnalysisResult:
    service: AnalysisService = request.app.state.analysis_service
    try:
        return await service.analyze(spec.ticker, spec.portfolio_id)
    except UnknownTickerError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except FabricatedNumberError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except ConnectionError as error:
        log.exception("LLM unavailable")
        raise HTTPException(status_code=503, detail="LLM backend unavailable") from error
