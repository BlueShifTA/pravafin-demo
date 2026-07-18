"""Portfolio draft-chat API models (stateless — history held by the client)."""

from pydantic import BaseModel, Field

from coresat.domain.agent import PortfolioDraft


class ChatTurn(BaseModel):
    role: str
    content: str


class DraftChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[ChatTurn] = Field(default_factory=list)
    # The last proposal the client was shown; creation is honored only when
    # this is present — the agent cannot create out of nowhere.
    proposed_draft: PortfolioDraft | None = None
    # Set by the client's explicit "build it" action. When true (and a
    # proposed_draft is present) the portfolio is created deterministically,
    # without an LLM turn — the user's click is the confirmation, so creation
    # never depends on the model choosing to emit a create action.
    confirm: bool = False
