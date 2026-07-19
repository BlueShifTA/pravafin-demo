from fastapi import APIRouter

import coresat.domain as csd
import coresat.services as css

router = APIRouter(prefix="/example", tags=["example"])


@router.post("/echo", response_model=csd.ExampleEchoResponse)
def echo(payload: csd.ExampleEchoRequest) -> csd.ExampleEchoResponse:
    return css.echo_message(payload)
