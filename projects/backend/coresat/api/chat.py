"""Copilot chat endpoints: SSE stream, history, audit — all RLS-scoped."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

import coresat.domain as csd
import coresat.services.agent as csa

router = APIRouter(prefix="/portfolios", tags=["copilot"])
info_router = APIRouter(prefix="/copilot", tags=["copilot"])


def _service(request: Request) -> csa.CopilotService:
    service: csa.CopilotService = request.app.state.copilot_service
    return service


@router.post("/{portfolio_id}/chat")
async def chat(portfolio_id: int, body: csd.ChatRequest, request: Request) -> StreamingResponse:
    service = _service(request)
    try:
        await service.record_user_message(portfolio_id, body.message)
    except csa.PortfolioNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return StreamingResponse(
        service.stream_chat(portfolio_id, body.message), media_type="text/event-stream"
    )


@router.get("/{portfolio_id}/chat")
async def chat_history(portfolio_id: int, request: Request) -> list[csd.ChatMessageOut]:
    return await _service(request).history(portfolio_id)


@router.delete("/{portfolio_id}/chat", status_code=204)
async def clear_chat(portfolio_id: int, request: Request) -> None:
    await _service(request).clear_history(portfolio_id)


@router.get("/{portfolio_id}/audit")
async def audit_log(portfolio_id: int, request: Request) -> list[csd.AuditEntry]:
    return await _service(request).audit(portfolio_id)


@info_router.get("/info")
async def copilot_info(request: Request) -> csd.CopilotInfo:
    return csd.CopilotInfo(model=_service(request).model_name)
