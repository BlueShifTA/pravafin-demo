import coresat.domain as csd


def echo_message(payload: csd.ExampleEchoRequest) -> csd.ExampleEchoResponse:
    return csd.ExampleEchoResponse(message=payload.message, length=len(payload.message))
