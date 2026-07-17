from pydantic import BaseModel, Field


class ExampleEchoRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)


class ExampleEchoResponse(BaseModel):
    message: str
    length: int
