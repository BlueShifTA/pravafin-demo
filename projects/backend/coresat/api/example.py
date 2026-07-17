from fastapi import APIRouter

from coresat.domain.models import ExampleEchoRequest, ExampleEchoResponse
from coresat.services.example import echo_message

router = APIRouter(prefix="/example", tags=["example"])


@router.post("/echo", response_model=ExampleEchoResponse)
def echo(payload: ExampleEchoRequest) -> ExampleEchoResponse:
    return echo_message(payload)
