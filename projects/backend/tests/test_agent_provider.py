"""Provider factory: local vs cloud chat model chosen by configuration."""

import pytest
from langchain_core.language_models.chat_models import BaseChatModel

from coresat.core.config import Settings
from coresat.services.agent.provider import build_chat_model


def _settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "openai_api_key": "",
        "openai_model": "gpt-5-mini",
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "gemma4:e4b",
    }
    base.update(overrides)
    return Settings(**base)


def test_ollama_provider_builds_chat_model() -> None:
    model = build_chat_model("ollama", _settings())
    assert isinstance(model, BaseChatModel)
    assert model.model == "gemma4:e4b"  # type: ignore[attr-defined]


def test_openai_provider_builds_chat_model_with_key() -> None:
    model = build_chat_model("openai", _settings(openai_api_key="sk-test-key"))
    assert isinstance(model, BaseChatModel)
    assert model.model_name == "gpt-5-mini"  # type: ignore[attr-defined]


def test_openai_provider_without_key_fails_loud() -> None:
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        build_chat_model("openai", _settings(openai_api_key=""))


def test_unknown_provider_fails_loud() -> None:
    with pytest.raises(ValueError, match="unknown LLM provider"):
        build_chat_model("gemini", _settings())
