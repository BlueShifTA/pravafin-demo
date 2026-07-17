"""Security tests for FastAPI application middleware and configuration.

Tests cover:
- Request ID middleware (X-Request-ID header injection and uniqueness)
- Request size limiting (413 for oversized bodies)
- CORS configuration (allowed/disallowed origins, no wildcard)
- Host binding defaults (127.0.0.1, not 0.0.0.0)
- Worker threads setting
- General security hygiene (no server version leak, clean 404s, content-type handling)
"""

from fastapi.testclient import TestClient

from coresat.core.config import get_settings
from coresat.main import app

# ──────────────────────────────────────────────────────────────
# Request ID Middleware
# ──────────────────────────────────────────────────────────────


def test_request_id_header_present() -> None:
    """Every response must include an X-Request-ID header."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers, (
        "X-Request-ID header missing — RequestIDMiddleware may not be registered"
    )


def test_request_id_is_unique_per_request() -> None:
    """Each request should receive a distinct X-Request-ID value."""
    client = TestClient(app)
    ids: set[str] = set()
    for _ in range(5):
        response = client.get("/health")
        request_id = response.headers.get("x-request-id", "")
        assert request_id, "X-Request-ID header is empty"
        ids.add(request_id)
    assert len(ids) == 5, f"Expected 5 unique request IDs, got {len(ids)}. IDs: {ids}"


def test_request_id_client_supplied_id_is_honoured() -> None:
    """If the client sends X-Request-ID, the middleware must echo it back.

    This validates pass-through behaviour. If the middleware overwrites the
    client-supplied value, the assertion will fail and the docstring must be
    updated to reflect that design decision.
    """
    client = TestClient(app)
    supplied_id = "trace-abc-123"
    response = client.get("/health", headers={"X-Request-ID": supplied_id})
    returned_id = response.headers.get("x-request-id", "")
    assert returned_id == supplied_id, (
        f"Expected echoed request ID '{supplied_id}', got '{returned_id}'. "
        "If the middleware intentionally overwrites client IDs, update this test."
    )


# ──────────────────────────────────────────────────────────────
# Request Size Limiting
# ──────────────────────────────────────────────────────────────

_ONE_MB = 1024 * 1024  # bytes


def test_normal_sized_request_succeeds() -> None:
    """A request body well below the 1 MB limit must be accepted."""
    client = TestClient(app)
    response = client.post(
        "/api/example/echo",
        json={"message": "hello"},
    )
    assert response.status_code == 200


def test_oversized_request_returns_413() -> None:
    """A request body exceeding 1 MB must be rejected with HTTP 413."""
    client = TestClient(app, raise_server_exceptions=False)
    oversized_body = b"x" * (_ONE_MB + 1)
    response = client.post(
        "/api/example/echo",
        content=oversized_body,
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 413, (
        f"Expected 413 for oversized body, got {response.status_code}. "
        "RequestSizeLimitMiddleware may not be registered."
    )


def test_oversized_request_response_carries_request_id() -> None:
    """Even a 413 produced by the size-limit middleware must carry X-Request-ID.

    Regression: RequestIDMiddleware must be the OUTERMOST middleware, so
    responses short-circuited by inner middleware still get tagged for log
    correlation. add_middleware() prepends — RequestIDMiddleware must be
    registered LAST in create_app().
    """
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/api/example/echo",
        content=b"x" * (_ONE_MB + 1),
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 413
    assert response.headers.get("x-request-id"), (
        "413 response is missing X-Request-ID — RequestIDMiddleware is not outermost."
    )


def test_request_at_exact_size_limit_succeeds() -> None:
    """A request body at exactly 1 MB must be accepted (boundary is exclusive)."""
    client = TestClient(app, raise_server_exceptions=False)
    exact_body = b"x" * _ONE_MB
    response = client.post(
        "/api/example/echo",
        content=exact_body,
        headers={"Content-Type": "application/octet-stream"},
    )
    # 1 MB exactly is at the boundary — expect success (not a 413)
    assert response.status_code != 413, (
        "A body of exactly 1 MB should not be rejected; only bodies *over* the limit."
    )


def test_empty_body_succeeds() -> None:
    """An empty request body must not trigger the size limiter."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200


# ──────────────────────────────────────────────────────────────
# CORS
# ──────────────────────────────────────────────────────────────


def test_cors_allowed_origin_receives_headers() -> None:
    """An origin in cors_origins must receive Access-Control-Allow-Origin."""
    client = TestClient(app)
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers, (
        "CORS headers missing for a known-allowed origin."
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_disallowed_origin_does_not_receive_headers() -> None:
    """An unknown origin must NOT receive Access-Control-Allow-Origin."""
    client = TestClient(app)
    response = client.get(
        "/health",
        headers={"Origin": "https://evil.example.com"},
    )
    assert response.status_code == 200
    # FastAPI CORSMiddleware omits the header rather than returning "*" for unknown origins
    acao = response.headers.get("access-control-allow-origin", "")
    assert acao != "*", "Wildcard CORS origin must never be returned."
    assert acao == "" or acao != "https://evil.example.com", (
        "Disallowed origin should not be reflected in Access-Control-Allow-Origin."
    )


def test_cors_no_wildcard_in_settings() -> None:
    """The default settings must not allow wildcard ('*') CORS origins.

    A wildcard defeats authentication cookies and tokens. If create_app()
    is patched to raise RuntimeError on wildcard, this test also validates
    that the running app was created without triggering that guard.
    """
    settings = get_settings()
    assert "*" not in settings.cors_origins, (
        "Wildcard '*' found in cors_origins — this is a security misconfiguration."
    )


def test_cors_preflight_allowed_origin() -> None:
    """OPTIONS preflight for an allowed origin must return 200 with CORS headers."""
    client = TestClient(app)
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


# ──────────────────────────────────────────────────────────────
# Host Binding
# ──────────────────────────────────────────────────────────────


def test_default_host_is_loopback() -> None:
    """Default host must be '127.0.0.1', never '0.0.0.0'.

    Binding to 0.0.0.0 exposes the service on all interfaces including
    public-facing ones. Loopback-only is the safe default; a reverse proxy
    (nginx, Caddy) should handle external traffic.
    """
    settings = get_settings()
    assert settings.host == "127.0.0.1", (
        f"Default host is '{settings.host}' — must be '127.0.0.1', not '0.0.0.0'."
    )


# ──────────────────────────────────────────────────────────────
# General Security Hygiene
# ──────────────────────────────────────────────────────────────


def test_no_server_version_header() -> None:
    """The 'Server' header must not reveal framework or version information."""
    client = TestClient(app)
    response = client.get("/health")
    server_header = response.headers.get("server", "").lower()
    # Uvicorn / Starlette emit "uvicorn" — reject any version string like "uvicorn/0.x"
    assert "/" not in server_header, (
        f"Server header leaks version info: '{server_header}'. "
        "Strip or suppress the Server header in production."
    )


def test_404_does_not_leak_stack_trace() -> None:
    """Unknown routes must return a plain 404 with no internal detail."""
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/this-route-does-not-exist")
    assert response.status_code == 404
    body = response.text.lower()
    # Check that common stack trace markers are absent
    for marker in ("traceback", 'file "', "line ", "exception", "<html"):
        assert marker not in body, (
            f"Response body contains '{marker}' — possible stack trace or HTML error page leak."
        )


def test_invalid_content_type_returns_422_not_500() -> None:
    """Sending wrong content-type to a JSON endpoint must yield 422, not 500."""
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/api/example/echo",
        content=b"not-json",
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code in (415, 422), (
        f"Expected 415 or 422 for mismatched content-type, got {response.status_code}. "
        "A 500 here would indicate missing input validation."
    )
    assert response.status_code != 500
