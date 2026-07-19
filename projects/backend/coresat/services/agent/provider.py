"""Provider factory: build the LangChain chat model an agent runs on.

Local (Ollama) vs cloud (OpenAI) is configuration, not code — every agent
depends on the AgentLLM protocol, so switching a provider never touches the
graph, tools, or services.
"""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

import coresat.core as csc

# reasoning off + capped output mirrors the copilot's Ollama tuning: qwen's
# think mode spirals on strict-format prompts, and the grounded features need
# plain JSON, not chains of thought.
_OLLAMA_NUM_PREDICT = 3000


def model_name_for(provider: str, settings: csc.Settings) -> str:
    """The concrete model id a provider will run — for the audit and UI."""
    return settings.openai_model if provider == "openai" else settings.ollama_model


def build_chat_model(provider: str, settings: csc.Settings) -> BaseChatModel:
    if provider == "ollama":
        return ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=0,
            reasoning=False,
            num_predict=_OLLAMA_NUM_PREDICT,
        )
    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when an agent provider is 'openai'")
        # gpt-5 is a reasoning model; at its default effort it spends 15-30s of
        # reasoning tokens on EVERY node (scope, planner, synthesiser), which is
        # what makes routing feel slow. openai_reasoning_effort (default "low")
        # trades a little of that latency back for the SQL-planning care a small
        # model needs (scale/typing, core-is-a-fund) — tune via env. temperature
        # is left at the model default — the gpt-5 family rejects a non-default.
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=SecretStr(settings.openai_api_key),
            reasoning_effort=settings.openai_reasoning_effort,  # type: ignore[arg-type]
        )
    raise ValueError(f"unknown LLM provider: {provider!r} (use 'ollama' or 'openai')")
