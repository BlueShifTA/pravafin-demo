"""Portfolio draft-chat endpoint: stateless SSE, no portfolio scope yet."""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

import coresat.domain as csd
import coresat.services.agent as csa

router = APIRouter(prefix="/portfolio-draft", tags=["draft"])


def _service(request: Request) -> csa.DraftService:
    service: csa.DraftService = request.app.state.draft_service
    return service


@router.post("/chat")
async def draft_chat(body: csd.DraftChatRequest, request: Request) -> StreamingResponse:
    service = _service(request)
    return StreamingResponse(
        service.stream_chat(body.message, body.history, body.proposed_draft, body.confirm),
        media_type="text/event-stream",
    )
