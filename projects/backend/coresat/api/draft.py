"""Portfolio draft-chat endpoint: stateless SSE, no portfolio scope yet."""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from coresat.domain.draft import DraftChatRequest
from coresat.services.agent.draft_service import DraftService

router = APIRouter(prefix="/portfolio-draft", tags=["draft"])


def _service(request: Request) -> DraftService:
    service: DraftService = request.app.state.draft_service
    return service


@router.post("/chat")
async def draft_chat(body: DraftChatRequest, request: Request) -> StreamingResponse:
    service = _service(request)
    return StreamingResponse(
        service.stream_chat(body.message, body.history, body.proposed_draft, body.confirm),
        media_type="text/event-stream",
    )
