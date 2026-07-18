# Backend (FastAPI + uvicorn), built with uv from the workspace root.
# Build context = repo root (needs root pyproject.toml + uv.lock + projects/backend).
#   docker build -f devops/backend.Dockerfile -t coresat-backend .
# syntax=docker/dockerfile:1

FROM python:3.14-slim-bookworm AS build
COPY --from=ghcr.io/astral-sh/uv:0.9.9 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /app

# 1) Dependencies only — cached until the manifests change. --all-packages pulls
#    every workspace member's deps (coresat's live here, not on the empty root
#    project). READMEs are copied because both pyproject files reference them.
COPY pyproject.toml uv.lock README.md ./
COPY projects/backend/pyproject.toml projects/backend/README.md ./projects/backend/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --all-packages --frozen --no-default-groups --no-install-workspace

# 2) Source + build the coresat wheel into the same venv.
COPY projects/backend/coresat ./projects/backend/coresat
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --all-packages --frozen --no-default-groups

FROM python:3.14-slim-bookworm AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app/projects/backend \
    FASTEMBED_CACHE_PATH=/home/app/.cache/fastembed
WORKDIR /app
RUN useradd --create-home --uid 10001 app
COPY --from=build --chown=app:app /app/.venv /app/.venv
COPY --from=build --chown=app:app /app/projects/backend /app/projects/backend
USER app
# Bake the cross-encoder reranker (fastembed ONNX) into the image so the first
# rag_search never downloads it from HuggingFace at runtime (unauthenticated →
# rate-limited, adds seconds). Downloads into FASTEMBED_CACHE_PATH as `app`.
# Must match core/config.py rerank_model default.
RUN python -c "from fastembed.rerank.cross_encoder import TextCrossEncoder; TextCrossEncoder(model_name='Xenova/ms-marco-MiniLM-L-6-v2')"
EXPOSE 8000
# Bind 0.0.0.0 so the container is reachable; the reverse proxy / compose network
# is the trust boundary (the app default binds loopback only).
CMD ["uvicorn", "coresat.main:app", "--host", "0.0.0.0", "--port", "8000"]
