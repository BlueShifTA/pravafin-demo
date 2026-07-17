# FastAPI Architecture Patterns

> **Enforced rules live in root [`CLAUDE.md`](../../CLAUDE.md). This document is the authoritative detail reference.**

---

## Middleware ordering

`app.add_middleware()` **prepends** — the middleware registered LAST is the OUTERMOST at request time. To get the request flow `RequestIDMiddleware → RequestSizeLimitMiddleware → CORSMiddleware → routes`, register in this order:

1. `CORSMiddleware` — handle cross-origin requests
2. `RequestSizeLimitMiddleware` — reject oversized payloads before parsing
3. `RequestIDMiddleware` — registered last = outermost, so every response (including 413s short-circuited by the size limiter) carries `X-Request-ID`

Regression test: `test_oversized_request_response_carries_request_id` in `projects/backend/tests/test_security.py`. See `projects/backend/coresat/main.py` for the reference implementation.

## Lifespan resource management

Use FastAPI's `lifespan` context manager for startup/shutdown resources (database pools, thread executors, caches). Resources created in `yield` are cleaned up on shutdown.

## Thread pool sizing

Install a bounded `ThreadPoolExecutor` via lifespan to prevent unbounded OS thread spawning under concurrent `run_in_executor` calls. Default: `min(32, cpu_count + 4)`.

## Adding new backend modules

Follow the existing layer pattern:
- `api/` — route handlers (thin, delegate to services)
- `services/` — business logic
- `domain/` — Pydantic models and domain types
- `core/` — configuration, middleware, shared utilities

## CLI shared error boundary

Every CLI entry point funnels through one shared `run_cli(fn, handlers)` helper that maps exceptions to exit codes and stderr messages. Each CLI defines a handler list; its `main` is `sys.exit(run_cli(_work, _HANDLERS))`. No hand-written `try/except` ladder per CLI.

```python
# src/_cli_errors.py — shared, imported by every CLI
from collections.abc import Callable
from dataclasses import dataclass
import click

@dataclass(frozen=True)
class CliErrorHandler:
    exc_type: type[BaseException]
    exit_code: int
    hint: str | None
    message_fn: Callable[[BaseException], str] | None = None

def run_cli(fn: Callable[[], int], handlers: list[CliErrorHandler]) -> int:
    try:
        return fn()
    except BaseException as exc:
        for handler in handlers:
            if isinstance(exc, handler.exc_type):
                body = handler.message_fn(exc) if handler.message_fn else str(exc)
                click.echo(f"error: {body}", err=True)
                if handler.hint:
                    click.echo(f"hint: {handler.hint}", err=True)
                return handler.exit_code
        raise   # unhandled — let the framework print a traceback
```

```python
# src/fetch_ticket.py — a CLI that uses the shared helper
import sys
import click
import httpx
from _cli_errors import CliErrorHandler, run_cli

_HANDLERS: list[CliErrorHandler] = [
    CliErrorHandler(exc_type=LookupError, exit_code=2, hint=None),
    CliErrorHandler(exc_type=FileNotFoundError, exit_code=1, hint=None),
    CliErrorHandler(exc_type=httpx.HTTPError, exit_code=1, hint=None),
]

@click.command()
@click.argument("ticket_key", type=str)
def main(ticket_key: str) -> None:
    def _work() -> int:
        # business logic here — return the exit code
        ...
        return 0
    sys.exit(run_cli(_work, _HANDLERS))
```

**Exit codes are part of the public contract** the moment any external caller (skill, script, CI, documentation) branches on them. Pin them in contract tests before refactoring any CLI that produces them. Same for stderr substrings that external tooling matches on.

**Handlers are scanned top-down; the first `isinstance` match wins.** List specific classes before their parents — `ReportFormatError(ValueError)` must come before generic `ValueError`.

**Unhandled exceptions re-raise.** This is intentional: an exception class not in any handler list means someone added a new failure mode without updating the handlers. Failing loudly is better than silently returning exit 1.

## See also

- [`PYTHON_STYLE.md`](PYTHON_STYLE.md) — Python naming, imports, typing rules
- [`SECURITY_PATTERNS.md`](SECURITY_PATTERNS.md) — network, input, data, LLM safety
- [`SOLID_PRINCIPLES.md`](SOLID_PRINCIPLES.md) — design principles for classes and modules
- Root [`CLAUDE.md`](../../CLAUDE.md) — enforced rules summary
