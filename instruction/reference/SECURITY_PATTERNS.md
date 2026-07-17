# SECURITY_PATTERNS.md — Web Application Security Reference

**Purpose:** Reusable security patterns for FastAPI + Next.js projects.
Apply before any external demo or deployment.

**Cross-reference:** `reference/CHECKLIST.md` (audit scorecard)

---

## Categories

1. [Network Security](#1-network-security)
2. [Input Validation](#2-input-validation)
3. [Data Safety](#3-data-safety)
4. [LLM Safety](#4-llm-safety)
5. [Agent Safety](#5-agent-safety)
6. [Thread Safety](#6-thread-safety)
7. [Error Handling](#7-error-handling)

---

## 1. Network Security

### 1.1 Request ID Middleware

**What:** Attach a UUID to every inbound HTTP request and return it in the response header.

**Why:** Without request IDs, correlating logs across distributed services or across a request's full lifecycle is impossible. A single UUID threads every log line together.

**How:**

```python
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

# Register in create_app():
app.add_middleware(RequestIDMiddleware)
```

**Usage in logs:**
```python
logger.info("Request started", extra={"request_id": request.state.request_id})
```

**When to use:** Every HTTP service. No exceptions.

---

### 1.2 Request Size Limits

**What:** Reject requests whose `Content-Length` exceeds a threshold (default 1 MB) before the body is parsed.

**Why:** Without a size limit, a malicious or buggy client can send arbitrarily large bodies that exhaust memory during JSON parsing — before any application code runs.

**How:**

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_bytes: int = 1_048_576) -> None:
        super().__init__(app)
        self.max_bytes: int = max_bytes

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_bytes:
            return Response("Request body too large", status_code=413)
        return await call_next(request)

# Register before other middleware:
app.add_middleware(RequestSizeLimitMiddleware, max_bytes=1_048_576)
```

**When to use:** All public or LAN-accessible HTTP services.

---

### 1.3 CORS Wildcard Block

**What:** Raise a `RuntimeError` at application startup if `"*"` appears in the configured `cors_origins`.

**Why:** A CORS wildcard allows any origin to make credentialed requests to your API. This is never intentional in production and is frequently introduced by copy-paste. Failing at startup makes the misconfiguration impossible to ship.

**How:**

```python
from fastapi.middleware.cors import CORSMiddleware

def create_app(settings: Settings) -> FastAPI:
    app = FastAPI()

    if "*" in settings.cors_origins:
        raise RuntimeError(
            "CORS wildcard ('*') is not allowed. "
            "Set CORS_ORIGINS to explicit origins."
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app
```

**When to use:** All services. The check goes in `create_app()`, not at request time.

---

### 1.4 Loopback Bind Default

**What:** Default the server bind address to `127.0.0.1`, not `0.0.0.0`.

**Why:** `0.0.0.0` binds to all network interfaces. If the server is run in a cloud VM, CI environment, or container with an exposed port, it is immediately internet-accessible. Loopback-by-default requires an explicit override to expose the service.

**How:**

```python
# core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    host: str = "127.0.0.1"   # NEVER default to 0.0.0.0
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]
```

**When to use:** Every FastAPI service. Override to `0.0.0.0` only in Docker containers behind a reverse proxy (nginx, Traefik, Caddy) with explicit documentation.

---

## 2. Input Validation

### 2.1 Pydantic Field Constraints

**What:** Enforce `min_length`, `max_length`, `ge`, `le` on all Pydantic model fields that accept user input.

**Why:** Without explicit bounds, users can send arbitrarily long strings (memory exhaustion), negative values, or impossible inputs. Pydantic validates before the data reaches any handler.

**How:**

```python
from pydantic import BaseModel, Field, model_validator

class CreateItemRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    quantity: int = Field(ge=0, le=10000)
    query: str = Field(min_length=1, max_length=4000)

class ChatRequest(BaseModel):
    history: list[dict] = Field(default_factory=list)

    @model_validator(mode="after")
    def cap_history(self) -> "ChatRequest":
        self.history = self.history[-50:]  # Never more than 50 turns
        return self
```

**When to use:** All request bodies. Free-text fields always get `max_length`. Lists always get a length cap via `model_validator`.

---

### 2.2 Prompt Injection Guards

**What:** Validate free-text fields with a regex that catches common prompt injection patterns before interpolating them into LLM prompts.

**Why:** If user-supplied text reaches an LLM system prompt or few-shot examples without sanitization, attackers can override system instructions, extract confidential prompt contents, or manipulate outputs. Regex is not a complete defense but adds a meaningful layer.

**How:**

```python
import re
from pydantic import field_validator

_INJECTION_PATTERNS = re.compile(
    r"(ignore previous instructions|system prompt|<system>|</system>"
    r"|jailbreak|forget your instructions|disregard all prior)",
    re.IGNORECASE,
)

def sanitize_text(value: str) -> str:
    value = value.strip()
    if _INJECTION_PATTERNS.search(value):
        raise ValueError("Input contains disallowed content.")
    return value

class UserQueryRequest(BaseModel):
    query: str

    @field_validator("query", mode="before")
    @classmethod
    def validate_query(cls, v: str) -> str:
        return sanitize_text(v)
```

**When to use:** Any field that is interpolated into an LLM prompt. Also apply to fields that influence SQL queries or file paths.

---

### 2.3 SQL Identifier Injection Prevention

**What:** Validate column names, table names, and record IDs with a strict regex before interpolating them into SQL strings.

**Why:** Column names and identifiers cannot be parameterized with `?` placeholders in most SQL drivers. If they come from user input, they must be validated against an allowlist or a strict character-class regex.

**How:**

```python
import re

_SAFE_IDENTIFIER_RE = re.compile(r"^[\w.\-]+$")

def validate_identifier(value: str, name: str = "identifier") -> str:
    if not _SAFE_IDENTIFIER_RE.match(value):
        raise ValueError(f"Invalid {name}: {value!r}")
    return value

# Usage:
record_id = validate_identifier(request.record_id, "record_id")
query = f"SELECT * FROM records WHERE id = ?"
cursor.execute(query, (record_id,))  # value still parameterized
```

**When to use:** Any identifier that comes from user input and must be embedded in a SQL string. Always combine with parameterized queries for values.

---

## 3. Data Safety

### 3.1 SQL Read-Only Guards

**What:** Reject SQL strings containing DDL or DML keywords before execution.

**Why:** If SQL queries are constructed from LLM output or user input, the query surface includes DROP, DELETE, INSERT, and ALTER. A read-only guard prevents any mutation, even if the query bypasses other validation.

**How:**

```python
import re

_MUTATION_RE = re.compile(
    r"\b(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE|GRANT|REVOKE|TRUNCATE|EXPORT)\b",
    re.IGNORECASE,
)

def execute_safe_sql(conn, query: str, params: tuple = ()) -> list:
    if _MUTATION_RE.search(query):
        raise ValueError("Mutation queries are not permitted.")
    with conn:
        cursor = conn.execute(query, params)
        return cursor.fetchall()
```

**When to use:** Any code path where SQL is constructed from LLM output, user input, or external configuration. Not a substitute for proper DB permissions — use both.

---

### 3.2 JSON Cache Over Pickle

**What:** Use JSON (or msgpack) for caching serialized data. Never use `pickle`.

**Why:** `pickle.loads()` on untrusted data executes arbitrary Python code. If a cache file is written by one process and read by another (or by a future version of the code), a corrupted or malicious cache can achieve remote code execution.

**How:**

```python
import json
import hashlib
from pathlib import Path

def cache_key(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

def read_cache(path: Path) -> dict | None:
    if path.exists():
        return json.loads(path.read_text())
    return None

def write_cache(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data))

# NEVER:
# import pickle
# pickle.loads(untrusted_bytes)  # arbitrary code execution
```

**When to use:** All caching, embedding storage, model artifact metadata. `pickle` is only acceptable for short-lived in-process caches where the data is generated and consumed in the same process run.

---

### 3.3 SQLite Context Managers

**What:** Always open SQLite connections with `with sqlite3.connect(...) as conn:` (or an explicit `conn.close()` in a `finally` block).

**Why:** Without context managers, exceptions leave connections open. Under load, this exhausts the file descriptor limit.

**How:**

```python
import sqlite3

def get_record(db_path: str, record_id: str) -> dict | None:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM records WHERE id = ?", (record_id,)
        )
        row = cursor.fetchone()
    return dict(row) if row else None

# WRONG — connection left open if exception occurs:
# conn = sqlite3.connect(db_path)
# cursor = conn.execute(...)
# conn.close()
```

**When to use:** All sqlite3 usage. For long-lived connections (DuckDB, psycopg2), use a connection pool or an RLock wrapper — see Thread Safety section.

---

## 4. LLM Safety

### 4.1 Timeout Cap on LLM HTTP Calls

**What:** Set explicit connect and read timeouts on all LLM API calls (Ollama, OpenAI, etc.).

**Why:** Without timeouts, a slow or unresponsive LLM backend blocks the thread indefinitely. This exhausts the thread pool and makes the application unresponsive to all other requests.

**How:**

```python
import httpx

# Ollama-style LLM client
client = httpx.Client(
    base_url=settings.ollama_url,
    timeout=httpx.Timeout(
        connect=10.0,   # 10s to establish connection
        read=120.0,     # 120s max wait for response (was 600s — too long)
        write=30.0,
        pool=5.0,
    ),
)
```

**When to use:** All external HTTP calls to LLM backends, embedding services, or any blocking API.

---

### 4.2 Singleton Prompt Loading

**What:** Load prompt templates once at startup using `@lru_cache`, not on every request.

**Why:** File I/O on every LLM call adds latency and creates race conditions if multiple threads read the same file simultaneously. `lru_cache` is thread-safe for the initialization path.

**How:**

```python
from functools import lru_cache
from pathlib import Path
import yaml

@lru_cache(maxsize=1)
def load_prompts(prompts_path: str) -> dict:
    with open(prompts_path) as f:
        return yaml.safe_load(f)

# Called once, cached forever:
prompts = load_prompts(str(settings.prompts_path))
```

**When to use:** Any configuration or template data loaded from disk that does not change at runtime.

---

## 5. Agent Safety

### 5.1 .env File Protection

**What:** Agents MUST NEVER read `.env` files. They may only read `.env.example`.

**Why:** `.env` files contain real credentials, API keys, and secrets. An agent that reads and logs or echoes `.env` contents creates a secret exfiltration risk. `.env.example` contains only placeholder values and is safe to read, inspect, and reference in documentation.

**Rules:**
- When writing agent prompts, explicitly state: "Do NOT read `.env` files. Read `.env.example` only."
- When an agent needs to understand required environment variables, point it to `.env.example`.
- Code generated by agents must never contain `open(".env")` or `Path(".env").read_text()`.
- CI pipelines inject secrets via environment variables — never via file reads.

**How (safe pattern):**

```python
# SAFE — reads placeholder values only
with open(".env.example") as f:
    example_vars = [line.split("=")[0] for line in f if "=" in line]

# NEVER — reads real secrets
# with open(".env") as f:
#     secrets = f.read()
```

**When to use:** All agent prompts for file-creation tasks. Include this rule explicitly when the task involves any configuration or settings files.

---

### 5.2 "Do NOT Plan" Agent Prompt Pattern

**What:** Include an explicit directive in every file-creation agent prompt: "Write the files now. Do NOT plan. Do NOT summarize. Do NOT ask for confirmation."

**Why:** Sub-agents default to entering planning/analysis mode when given a complex task. A planning agent produces a detailed outline but creates no files. This wastes token budget and clock time. The directive short-circuits this pattern.

**How (prompt template):**

```
You are a [role] implementing [task].

Write the files now. Do NOT plan. Do NOT summarize. Do NOT ask for confirmation.
Create the following files:
- [file 1]: [description]
- [file 2]: [description]

[Specific requirements...]
```

**When to use:** Every sub-agent prompt that requires file creation, code writing, or document authoring. Optional for research-only or analysis-only tasks.

---

### 5.3 Protocol Over ABC Pattern

**What:** Use `typing.Protocol` for dependency injection and mock boundaries instead of abstract base classes (`abc.ABC`).

**Why:** ABCs require inheriting from the base class — mocks must subclass and implement every abstract method. Protocols are structural: a mock only needs to implement the methods actually called in a test. This makes mocks smaller, tests faster to write, and the production implementation decoupled from any base class hierarchy.

**How:**

```python
from typing import Protocol

# PREFERRED — structural typing, no inheritance required
class LLMBackend(Protocol):
    def generate(self, prompt: str) -> str: ...
    def stream(self, prompt: str): ...

class MockLLMBackend:
    """Implements LLMBackend protocol without inheriting from it."""
    def generate(self, prompt: str) -> str:
        return "mock response"
    def stream(self, prompt: str):
        yield "mock"

# AVOID — forces mocks to inherit and implement all abstract methods
# from abc import ABC, abstractmethod
# class LLMBackend(ABC):
#     @abstractmethod
#     def generate(self, prompt: str) -> str: ...
```

**When to use:** All dependency injection boundaries where the concrete implementation is swappable (LLM backends, data backends, storage adapters, notification services).

---

## 6. Thread Safety

### 6.1 RLock on Shared Database Connections

**What:** Wrap shared database connections with `threading.RLock()`. All queries go through a single `_execute()` method that acquires the lock.

**Why:** DuckDB and similar analytical databases are not thread-safe for concurrent writes on a shared connection. Without a lock, concurrent requests race on the connection and produce corrupted results or crashes.

**How:**

```python
import threading
import duckdb

class DataBackend:
    def __init__(self, db_path: str) -> None:
        self._conn: duckdb.DuckDBPyConnection = duckdb.connect(db_path)
        self._lock: threading.RLock = threading.RLock()

    def _execute(self, query: str, params: tuple = ()) -> list:
        with self._lock:
            return self._conn.execute(query, params).fetchall()

    def query_records(self, filters: dict) -> list:
        sql = "SELECT * FROM records WHERE created_at > ?"
        return self._execute(sql, (filters["since"],))
```

**When to use:** Any shared mutable resource accessed from multiple threads: database connections, file handles, in-memory caches, counters. RLock (reentrant lock) is preferred over Lock when the same thread may acquire it recursively.

---

### 6.2 Bounded Thread Pools

**What:** Always create `ThreadPoolExecutor` with an explicit `max_workers` limit. Never use an unbounded executor.

**Why:** Python's default `ThreadPoolExecutor` (without `max_workers`) creates up to `min(32, os.cpu_count() + 4)` threads — but this can be overridden accidentally. If a web server spawns one executor per request, or if the global executor grows unbounded, OS thread limits are exhausted and the process crashes.

**How:**

```python
from concurrent.futures import ThreadPoolExecutor

# In settings:
class Settings(BaseSettings):
    worker_threads: int = 4

# In application startup (not per-request):
executor = ThreadPoolExecutor(max_workers=settings.worker_threads)

# Run blocking work in the executor:
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(executor, blocking_function, arg1, arg2)
```

**Never:**
```python
# WRONG — unbounded, grows with concurrency
executor = ThreadPoolExecutor()

# WRONG — new executor per request, unbounded thread creation
async def handler(request):
    with ThreadPoolExecutor() as ex:
        result = await loop.run_in_executor(ex, work)
```

**When to use:** All FastAPI services that run blocking I/O (LLM calls, file I/O, DB queries) in a thread pool. Create one executor at app startup, share it across all requests.

---

### 6.3 Fresh State Per Request

**What:** Orchestrators and service classes must create fresh state objects for each request. No mutable instance variables that persist across requests.

**Why:** Shared mutable state on a singleton orchestrator is a race condition. Two concurrent requests can interleave reads and writes on the same state object, producing corrupted results.

**How:**

```python
from dataclasses import dataclass, field

@dataclass
class RequestState:
    """Created fresh per request. Never reused across requests."""
    request_id: str
    history: list[dict] = field(default_factory=list)
    results: list[str] = field(default_factory=list)

class Orchestrator:
    """Singleton — stateless. Creates fresh RequestState per call."""
    def __init__(self, llm: LLMBackend, db: DataBackend) -> None:
        self.llm: LLMBackend = llm
        self.db: DataBackend = db

    async def process(self, request: ProcessRequest) -> RequestState:
        state = RequestState(request_id=request.request_id)  # fresh per call
        state = await self._validate(state, request)
        state = await self._execute(state)
        state = await self._finalize(state)
        return state
```

**When to use:** All request-handling orchestrators and service classes. The rule is: if a class is a singleton (one instance per application), it must hold no per-request mutable state.

---

## 7. Error Handling

### 7.1 No Internal Details in HTTP Responses

**What:** Return generic error messages to clients. Log full details (including tracebacks and request context) server-side only.

**Why:** Stack traces, file paths, SQL queries, and internal module names in HTTP responses are a reconnaissance tool for attackers. They reveal implementation details that make targeted attacks easier.

**How:**

```python
import logging
from fastapi import HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception",
        exc_info=True,
        extra={"request_id": getattr(request.state, "request_id", "unknown")},
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred."},
    )

# In route handlers — specific errors also sanitized:
try:
    result = db.query(sql)
except Exception:
    logger.error("Query failed", exc_info=True)
    raise HTTPException(status_code=500, detail="Query execution failed.")
    # NEVER: raise HTTPException(detail=str(exc))  — leaks internals
```

**When to use:** All FastAPI services. Register the global exception handler in `create_app()`. Never use `str(exc)` directly in HTTP response bodies.

---

### 7.2 PII-Safe Logging

**What:** Never log PII (names, emails, passwords, sensitive user data) in log messages. Log only transient identifiers (request ID, user ID hash).

**Why:** Log aggregation systems (CloudWatch, Datadog, Loki) retain logs for weeks or months, often without the same access controls as the application database. PII in logs creates a compliance and breach risk that is disproportionately hard to remediate.

**Rules:**
- Log `request_id` and hashed user identifiers only.
- Never log: names, emails, passwords, API keys, phone numbers, or any sensitive user data.
- If a user ID could identify someone, hash it: `hashlib.sha256(user_id.encode()).hexdigest()[:12]`.
- Audit log statements before any external demo.

**How:**

```python
import hashlib
import logging

logger = logging.getLogger(__name__)

def hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode()).hexdigest()[:12]

# SAFE:
logger.info("Request complete", extra={"uid_hash": hash_user_id(user_id)})

# NEVER:
# logger.info(f"Request from {user_name}, email={email}")
```

**When to use:** All applications handling personal data. Required before any GDPR/compliance-scoped deployment. Good practice for all production systems.

---

## Quick-Reference Summary

| Pattern | File/Location | Priority |
|---------|--------------|----------|
| RequestID middleware | `core/middleware.py` | Required |
| Request size limit | `core/middleware.py` | Required |
| CORS wildcard block | `create_app()` | Required |
| Loopback bind default | `core/config.py` | Required |
| Pydantic field constraints | `domain/schemas.py` | Required |
| Prompt injection regex | `domain/schemas.py` | Required if LLM |
| SQL identifier validation | `domain/queries.py` | Required if SQL |
| SQL read-only guard | `domain/queries.py` | Required if LLM→SQL |
| JSON cache (not pickle) | anywhere caching used | Required |
| SQLite context managers | `domain/db.py` | Required |
| LLM timeout cap | `infrastructure/llm.py` | Required if LLM |
| Singleton prompt loading | `infrastructure/llm.py` | Required if LLM |
| .env protection rule | agent prompts | Required |
| "Do NOT plan" directive | agent prompts | Required |
| Protocol over ABC | all DI boundaries | Recommended |
| RLock on shared DB | `infrastructure/db.py` | Required if shared conn |
| Bounded thread pool | app startup | Required |
| Fresh state per request | orchestrator | Required |
| No internals in responses | exception handler | Required |
| PII-safe logging | all loggers | Required if PII |

---

**Created:** 2026-03-22
**Review:** Apply to every new project before first external demo
