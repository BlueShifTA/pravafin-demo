"""Settings parsing — pins the documented .env contract.

.env.example documents CORS_ORIGINS as a comma-separated string; Settings must
accept that format (and the JSON-list format pydantic-settings supports natively).
"""

import pytest

import coresat.core as csc


def test_cors_origins_comma_separated(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    settings = csc.Settings()
    assert settings.cors_origins == ["http://localhost:3000", "http://127.0.0.1:3000"]


def test_cors_origins_comma_separated_strips_whitespace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CORS_ORIGINS", " http://localhost:3000 , http://a.example ")
    settings = csc.Settings()
    assert settings.cors_origins == ["http://localhost:3000", "http://a.example"]


def test_cors_origins_json_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", '["http://localhost:3000"]')
    settings = csc.Settings()
    assert settings.cors_origins == ["http://localhost:3000"]


def test_cors_origins_default_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    settings = csc.Settings()
    assert settings.cors_origins == ["http://localhost:3000", "http://127.0.0.1:3000"]


def test_worker_threads_parsed_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WORKER_THREADS", "8")
    settings = csc.Settings()
    assert settings.worker_threads == 8


def test_worker_threads_default_is_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WORKER_THREADS", raising=False)
    settings = csc.Settings()
    assert settings.worker_threads is None
