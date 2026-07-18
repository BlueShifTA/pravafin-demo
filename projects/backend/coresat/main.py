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

from coresat.api.analysis import router as analysis_router
from coresat.api.chat import info_router as copilot_info_router
from coresat.api.chat import router as chat_router
from coresat.api.compare import router as compare_router
from coresat.api.draft import router as draft_router
from coresat.api.example import router as example_router
from coresat.api.health import router as health_router
from coresat.api.ingest import router as ingest_router
from coresat.api.market import router as market_router
from coresat.api.portfolios import router as portfolios_router
from coresat.core.config import get_settings
from coresat.core.observability import setup_logging
from coresat.db.session import create_engine, to_async_url
from coresat.services.agent.agent import GroundedAgent
from coresat.services.agent.draft_service import DraftService
from coresat.services.agent.llm import COPILOT_PROMPTS, DRAFT_PROMPTS, ChatModelAgentLLM
from coresat.services.agent.provider import build_chat_model, model_name_for
from coresat.services.agent.retrieval import CrossEncoderReranker, OllamaEmbedder, RagRetriever
from coresat.services.agent.service import CopilotService
from coresat.services.agent.tools import RagSearchTool
from coresat.services.analysis import AnalysisService
from coresat.services.analytics import AnalyticsService
from coresat.services.comparison import ComparisonService
from coresat.services.ingestion.pipeline import IngestionPipeline, build_registry
from coresat.services.portfolios import PortfolioService

log = logging.getLogger(__name__)

# Maximum accepted request body size: 1 MB.  Larger bodies are rejected with
# 413 before any parsing occurs, preventing memory exhaustion from malicious
# clients sending arbitrarily large JSON payloads.
_MAX_REQUEST_BYTES = 1 * 1024 * 1024  # 1 MB

# chunks returned by rag_search before the synthesiser reads them
_RAG_K = 4


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
    # Document embeddings for RAG ingestion and retrieval share one embedder so
    # chunks and queries land in the same vector space.
    embedder = OllamaEmbedder(settings.ollama_base_url, settings.ollama_embed_model)
    app.state.ingest_pipeline = IngestionPipeline(
        engine=admin_engine, registry=build_registry(embedder)
    )
    # RAG retrieval reads the shared doc_chunks fact table on the app engine (no
    # RLS scope needed); both agents share one grounded rag_search tool.
    rag_tool = RagSearchTool(
        RagRetriever(app.state.app_engine, embedder, CrossEncoderReranker(settings.rerank_model)),
        _RAG_K,
    )
    app.state.rag_tool = rag_tool
    app.state.portfolio_service = PortfolioService(app.state.app_engine)
    app.state.analytics_service = AnalyticsService(app.state.app_engine)
    # Comparison and single-stock analysis stay on local Ollama — they are
    # grounded-by-construction (facts injected, output guarded), not agentic.
    local_llm = build_chat_model("ollama", settings)
    app.state.comparison_service = ComparisonService(engine=app.state.app_engine, llm=local_llm)
    app.state.analysis_service = AnalysisService(
        engine=app.state.app_engine, llm=local_llm, analytics=app.state.analytics_service
    )
    # Copilot's provider is chosen by config; fails loud here at startup if it
    # is 'openai' without a key, never mid-chat.
    copilot_model = build_chat_model(settings.copilot_provider, settings)
    app.state.copilot_service = CopilotService(
        engine=app.state.app_engine,
        agent=GroundedAgent(ChatModelAgentLLM(copilot_model, COPILOT_PROMPTS)),
        summaries=app.state.analytics_service,
        rag_tool=rag_tool,
        model_name=model_name_for(settings.copilot_provider, settings),
    )
    # Draft agent: same GroundedAgent class, its own provider, prompts, and
    # fact-only tools; creates through the existing PortfolioService path.
    draft_model = build_chat_model(settings.draft_agent_provider, settings)
    app.state.draft_service = DraftService(
        engine=app.state.app_engine,
        agent=GroundedAgent(ChatModelAgentLLM(draft_model, DRAFT_PROMPTS)),
        portfolios=app.state.portfolio_service,
        rag_tool=rag_tool,
    )

    log.info("%s started", settings.app_name)
    yield
    log.info("%s shutting down", settings.app_name)
    await app.state.app_engine.dispose()
    await admin_engine.dispose()
    executor.shutdown(wait=False)


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.runtime_log_dir, logging.INFO)

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
    app.include_router(portfolios_router, prefix=settings.api_prefix)
    app.include_router(market_router, prefix=settings.api_prefix)
    app.include_router(compare_router, prefix=settings.api_prefix)
    app.include_router(analysis_router, prefix=settings.api_prefix)
    app.include_router(chat_router, prefix=settings.api_prefix)
    app.include_router(copilot_info_router, prefix=settings.api_prefix)
    app.include_router(draft_router, prefix=settings.api_prefix)
    return app


app = create_app()
