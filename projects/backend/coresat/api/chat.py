"""Copilot chat endpoints: SSE stream, history, audit — all RLS-scoped."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from coresat.domain.chat import AuditEntry, ChatMessageOut, ChatRequest, CopilotInfo
from coresat.services.agent.service import CopilotService, PortfolioNotFoundError

router = APIRouter(prefix="/portfolios", tags=["copilot"])
info_router = APIRouter(prefix="/copilot", tags=["copilot"])


def _service(request: Request) -> CopilotService:
    service: CopilotService = request.app.state.copilot_service
    return service


@router.post("/{portfolio_id}/chat")
async def chat(portfolio_id: int, body: ChatRequest, request: Request) -> StreamingResponse:
    service = _service(request)
    try:
        await service.record_user_message(portfolio_id, body.message)
    except PortfolioNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return StreamingResponse(
        service.stream_chat(portfolio_id, body.message), media_type="text/event-stream"
    )


@router.get("/{portfolio_id}/chat")
async def chat_history(portfolio_id: int, request: Request) -> list[ChatMessageOut]:
    return await _service(request).history(portfolio_id)


@router.delete("/{portfolio_id}/chat", status_code=204)
async def clear_chat(portfolio_id: int, request: Request) -> None:
    await _service(request).clear_history(portfolio_id)


@router.get("/{portfolio_id}/audit")
async def audit_log(portfolio_id: int, request: Request) -> list[AuditEntry]:
    return await _service(request).audit(portfolio_id)


@info_router.get("/info")
async def copilot_info(request: Request) -> CopilotInfo:
    return CopilotInfo(model=_service(request).model_name)
