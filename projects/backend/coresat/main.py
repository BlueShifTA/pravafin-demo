import asyncio
import logging
import uuid
from collections.abc import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from coresat.api.example import router as example_router
from coresat.api.health import router as health_router
from coresat.api.ingest import router as ingest_router
from coresat.core.config import get_settings
from coresat.db.session import create_engine, to_async_url
from coresat.services.ingestion.pipeline import IngestionPipeline, build_registry

log = logging.getLogger(__name__)

# Maximum accepted request body size: 1 MB.  Larger bodies are rejected with
# 413 before any parsing occurs, preventing memory exhaustion from malicious
# clients sending arbitrarily large JSON payloads.
_MAX_REQUEST_BYTES = 1 * 1024 * 1024  # 1 MB


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique X-Request-ID to every request and response.

    If the client supplies an X-Request-ID header we echo it back; otherwise we
    generate a new UUID4.  The ID is stored in ``request.state.request_id`` so
    that route handlers and downstream code can include it in log records,
    making concurrent request logs traceable.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose Content-Length exceeds the configured limit.

    Checked before any route handler runs, so oversized payloads are dropped
    without parsing the body.  Guards against memory exhaustion from clients
    sending multi-MB JSON blobs.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                size = int(content_length)
            except ValueError:
                return JSONResponse(
                    status_code=400, content={"detail": "Invalid Content-Length header"}
                )
            if size > _MAX_REQUEST_BYTES:
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"Request body too large (max {_MAX_REQUEST_BYTES} bytes)"},
                )
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application startup and shutdown lifecycle.

    Installs a bounded thread pool for all run_in_executor calls.  Replace the
    placeholder startup/shutdown logic here with your own resource initialisation
    (database connections, caches, LLM clients, etc.).
    """
    settings = get_settings()

    # Scaling: install a bounded thread pool so run_in_executor calls cannot
    # spawn an unbounded number of OS threads under concurrent load.
    # worker_threads=None falls back to Python's default (min(32, cpu+4)).
    executor = ThreadPoolExecutor(max_workers=settings.worker_threads)
    loop = asyncio.get_running_loop()
    loop.set_default_executor(executor)
    app.state.executor = executor

    # Two engines by privilege: the app engine is RLS-enforced for portfolio
    # requests; the admin engine writes fact tables (ingestion only).
    app.state.app_engine = create_engine(settings.database_url)
    admin_engine = create_engine(to_async_url(settings.admin_database_url))
    app.state.ingest_pipeline = IngestionPipeline(engine=admin_engine, registry=build_registry())

    log.info("%s started", settings.app_name)
    yield
    log.info("%s shutting down", settings.app_name)
    await app.state.app_engine.dispose()
    await admin_engine.dispose()
    executor.shutdown(wait=False)


def create_app() -> FastAPI:
    settings = get_settings()

    # Reject wildcard CORS to prevent credential leakage.  In any deployment
    # a wildcard would accept cross-origin requests from any domain.  Explicit
    # origins must be listed in the CORS_ORIGINS environment variable.
    cors_origins = settings.cors_origins
    if "*" in cors_origins:
        log.error(
            "CORS origin wildcard ('*') is not permitted. "
            "Set CORS_ORIGINS to a list of explicit allowed origins."
        )
        raise RuntimeError(
            "CORS misconfiguration: wildcard origin ('*') is not allowed. "
            "Provide explicit origins via the CORS_ORIGINS environment variable."
        )

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    # add_middleware() PREPENDS: the last one added is the outermost at request
    # time.  Desired request flow: RequestID → SizeLimit → CORS → routes, so
    # every response — including 413s short-circuited by the size limiter —
    # carries an X-Request-ID.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Enforce request body size limit before any route handler runs.
    app.add_middleware(RequestSizeLimitMiddleware)
    # Attach a unique request ID for log tracing — registered last = outermost.
    app.add_middleware(RequestIDMiddleware)
    app.include_router(health_router)
    app.include_router(example_router, prefix=settings.api_prefix)
    app.include_router(ingest_router, prefix=settings.api_prefix)
    return app


app = create_app()
