"""Shared pytest fixtures for backend tests."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from coresat.main import app

# ──────────────────────────────────────────────────────────────
# HTTP Client Fixtures
# ──────────────────────────────────────────────────────────────


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    """Provide an AsyncClient for testing the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def client_with_auth(client: AsyncClient) -> AsyncClient:
    """Provide a client with mock authentication headers."""
    client.headers.update(
        {
            "Authorization": "Bearer test-token",
        }
    )
    return client


# ──────────────────────────────────────────────────────────────
# Markers for Test Organization
# ──────────────────────────────────────────────────────────────


def pytest_configure(config: pytest.Config) -> None:
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests",
    )
    config.addinivalue_line(
        "markers",
        "unit: marks tests as unit tests",
    )


# ──────────────────────────────────────────────────────────────
# Pytest Collection Hooks
# ──────────────────────────────────────────────────────────────


def pytest_collection_modifyitems(
    config: pytest.Config,  # noqa: ARG001
    items: list[pytest.Item],
) -> None:
    """Auto-mark tests based on their module."""
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "unit" in item.nodeid or "test_" in item.nodeid:
            item.add_marker(pytest.mark.unit)
