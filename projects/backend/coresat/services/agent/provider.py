"""Provider factory: build the LangChain chat model an agent runs on.

Local (Ollama) vs cloud (OpenAI) is configuration, not code — every agent
depends on the AgentLLM protocol, so switching a provider never touches the
graph, tools, or services.
"""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from coresat.core.config import Settings

# reasoning off + capped output mirrors the copilot's Ollama tuning: qwen's
# think mode spirals on strict-format prompts, and the grounded features need
# plain JSON, not chains of thought.
_OLLAMA_NUM_PREDICT = 3000


def model_name_for(provider: str, settings: Settings) -> str:
    """The concrete model id a provider will run — for the audit and UI."""
    return settings.openai_model if provider == "openai" else settings.ollama_model


def build_chat_model(provider: str, settings: Settings) -> BaseChatModel:
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
        # gpt-5 is a reasoning model that, at its default effort, spends 15-30s
        # of reasoning tokens on EVERY node (scope guard, planner, synthesiser),
        # which is what makes "routing" feel slow. These are structured,
        # template-guided tasks, not deep reasoning, so minimal effort keeps them
        # a few seconds each with no quality loss (the retry loop + SQL sanitizer
        # are the backstops). temperature is left at the model default — the
        # gpt-5 family rejects a non-default one.
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=SecretStr(settings.openai_api_key),
            reasoning_effort="minimal",
        )
    raise ValueError(f"unknown LLM provider: {provider!r} (use 'ollama' or 'openai')")
