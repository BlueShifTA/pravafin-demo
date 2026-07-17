from coresat.domain.models import ExampleEchoRequest, ExampleEchoResponse


def echo_message(payload: ExampleEchoRequest) -> ExampleEchoResponse:
    return ExampleEchoResponse(message=payload.message, length=len(payload.message))
