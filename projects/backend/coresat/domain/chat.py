"""Copilot chat API models."""

import datetime

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class Citation(BaseModel):
    id: str
    content: str


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    citations: list[Citation]
    tokens_in: int
    tokens_out: int
    created_at: datetime.datetime


class CopilotInfo(BaseModel):
    model: str


class AuditEntry(BaseModel):
    id: int
    feature: str
    model: str
    node: str | None
    graph_run_id: str | None
    tokens_in: int
    tokens_out: int
    created_at: datetime.datetime
