# Python Code Style Rules

> **Enforced rules live in root [`CLAUDE.md`](../../CLAUDE.md). This document is the authoritative detail reference.**

---

## Naming conventions

```python
snake_case          # Functions, variables, methods
_private_method     # Internal methods (prefix with _)
CONSTANT_CASE       # Module constants, enum values
PascalCase          # Classes, protocols, exceptions
_PrivateClass       # Internal implementation classes
snake_case.py       # Module names
```

## Import rules: relative within same directory, absolute across modules

Files in the **same directory** must use relative imports (`from .`).
Files importing from a **different directory** (parent or sibling module) must use absolute imports.
Never use parent-relative imports (`from ..`).

```python
# Same directory: use relative imports
from .example import router          # CORRECT
from package.api.example import router  # WRONG — same directory, use relative

# Different directory: use absolute imports
from package.domain.models import MyModel  # CORRECT
from ..domain.models import MyModel        # WRONG — never use parent-relative (..)
```

## No lazy imports

All imports must be at the top of the file. Never import inside functions, methods, `if` blocks, `if TYPE_CHECKING` blocks, or any other conditional/deferred context.

## No wildcard imports

`from foo import *` is banned. Every import must name its symbols explicitly. Wildcard imports hide the source of names, break `grep`-based navigation, and cause spurious shadowing when the upstream module adds new exports.

## No `from __future__ import annotations` in Python 3.14+

Python 3.14 is the project baseline. Annotations already work for modern syntax (`list[str] | None`, `X | None`) without the future import. Remove `from __future__ import annotations` when you see it. For the rare self-referential TypedDict / dataclass case, use an inline string forward ref (`content: "list[ADFNode] | None"`) instead of re-enabling PEP 563 globally.

## No `if TYPE_CHECKING:` blocks

`from typing import TYPE_CHECKING` plus an `if TYPE_CHECKING:` guarded import block is banned. Every import is a real, unconditional, top-level import. The two reasons people reach for `TYPE_CHECKING` both have better fixes:

- **"It breaks a circular import."** Then the module graph is wrong. Move the shared type into a leaf module (a `_types.py`, a domain `models.py`, a `config.py`) that both sides depend on. A `TYPE_CHECKING` block hides the cycle from the interpreter without fixing the architectural mistake — and it forces every reader to mentally evaluate "is this name actually defined at runtime?" forever after.
- **"The import is heavy and only needed for annotations."** Pay the import cost or restructure. Module-load-time micro-optimisations are not worth a forked import graph that behaves differently at type-check time vs. runtime.

`TYPE_CHECKING` also pairs badly with the no-`from __future__ import annotations` rule: under PEP 563 the strings get resolved lazily, but without it every annotation is evaluated at class-body / function-def time and a `TYPE_CHECKING`-only import becomes a `NameError` waiting to happen. Just import the symbol normally.

```python
# WRONG
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .jira_client import JiraClient   # hides a cycle, fails at runtime if used

def handle(client: "JiraClient") -> None: ...

# CORRECT — extract shared types to a leaf module both sides import
from .jira_types import JiraClient        # always real, always at top

def handle(client: JiraClient) -> None: ...
```

## Always type-annotate class `__init__` attributes

Every `__init__` parameter and every instance attribute assignment must have explicit type annotations. The return type must be `-> None`. Use modern union syntax: `list[str] | None` (Python 3.10+). Avoid `Any` unless truly necessary.

```python
# CORRECT
class Foo:
    def __init__(self, num: int, name: str) -> None:
        self.num: int = num
        self.name: str = name

# WRONG — missing attribute annotations and return type
class Foo:
    def __init__(self, num, name):
        self.num = num
        self.name = name
```

## No module-level mutable service instances

Never instantiate mutable service objects (database clients, API clients, connection pools, stateful caches) at module level. Instantiate inside other classes, functions, or inject via dependency injection.

**Permitted at module level:**
- Module constants: `ROOT = pathlib.Path(__file__).resolve().parents[1]`
- Module loggers: `logger = logging.getLogger(__name__)`
- FastAPI app: `app = create_app()` — required by ASGI servers

**Also permitted (not module-level, but often confused):**
- Pydantic model config: `model_config = SettingsConfigDict(...)` inside a class body — this is a class variable, not module-level

**Banned at module level:**
```python
db_client = PostgresClient(url=settings.db_url)  # WRONG — service instance, not a constant
api_client = MyAPIClient(api_key="...")           # WRONG — stateful, should be injected

class Boo:
    def __init__(self) -> None:
        self.db: PostgresClient = PostgresClient(url=settings.db_url)  # CORRECT — injected

def main() -> None:
    client = MyAPIClient(api_key=settings.api_key)  # CORRECT — scoped to function
```

## Dataclass-first design

Prefer `@dataclasses.dataclass` for data structures. Use frozen dataclasses when immutable. Validate in `__post_init__`. Group related constants in a dataclass instead of scattering magic numbers.

```python
import dataclasses as dc

@dc.dataclass(frozen=True)
class AppConfig:
    host: str = "127.0.0.1"
    port: int = 8000
    max_retries: int = 3
    retry_delay: float = 1.0

@dc.dataclass
class ProcessResult:
    value: float
    status: str

    def __post_init__(self) -> None:
        assert self.value >= 0
```

## TypedDict rules — JSON shape discipline

For JSON-shaped data that must remain a `dict` (API responses, request payloads, config files, cross-process messages), use a named `TypedDict` — never `dict[str, object]`, `dict[str, Any]`, or `Mapping[str, object]`. A named TypedDict gives pyright a real shape to check; `dict[str, object]` gives it nothing.

**Every TypedDict field is key-required.** Fields that may be null use `X | None` as the value type — the KEY is always present, the VALUE may be null. Callers read them via `.get()` or `isinstance`-narrow.

```python
# CORRECT — named shape, all fields key-required, nullable via X | None
from typing import TypedDict

class JiraIssueFields(TypedDict):
    summary: str | None
    assignee: JiraUser | None
    priority: JiraPriority | None

class JiraIssueResponse(TypedDict):
    key: str
    id: str
    fields: JiraIssueFields
```

```python
# WRONG — untyped dict in a signature
def get_issue(key: str) -> dict[str, object]: ...

# WRONG — NotRequired used to make a field optional at key level
from typing import NotRequired
class Foo(TypedDict):
    always: str
    maybe: NotRequired[str]   # BANNED — use `maybe: str | None`

# WRONG — total=False makes every field NotRequired
class Foo(TypedDict, total=False):  # BANNED
    always: str
```

**Construct TypedDicts via the constructor, not cast-from-dict-literal.** The constructor form forces pyright to verify every required field is provided; `cast` is a type lie that can silently omit fields.

```python
# CORRECT — constructor; every required field spelled out
node = ADFNode(type="text", version=None, content=None, text="hi", marks=None)

# WRONG — cast hides missing required fields
from typing import cast
node = cast(ADFNode, {"type": "text", "text": "hi"})   # BANNED
```

**Cast only at JSON seams, using the bare type (no string forward refs).** Cast the result of `response.json()` immediately, on the same line it returns. Never let untyped JSON propagate past the seam — callers cannot narrow `Any`.

```python
# CORRECT — cast immediately after response.json(), bare type
body = cast(JiraIssueResponse, response.json())

# WRONG — string forward ref (Python 3.14 resolves the type at runtime)
body = cast("JiraIssueResponse", response.json())

# WRONG — let Any propagate; callers can't narrow
def fetch() -> Any:
    return response.json()
```

**No `from __future__ import annotations` in Python 3.14+.** Remove it when you see it. For self-referential TypedDicts, use an inline string forward ref: `content: "list[ADFNode] | None"` inside the class body.

**No `if TYPE_CHECKING:` import blocks.** A `TYPE_CHECKING` guard is a smell that the module graph has a cycle the architecture isn't admitting. Move the shared TypedDict / dataclass into a leaf module both sides import, and keep all imports unconditional at the top of the file. See the import rules section above for the full rationale.

**For recursive tree walkers of unknown-depth JSON** (ADF nodes, arbitrary YAML, discriminated unions Python can't statically express), keep the parameter typed as `object` and narrow with `isinstance` inside the walker. Don't force a TypedDict on a shape you can't statically know — you'll end up casting-and-praying, which is worse than owning the narrowing.

**Design check before committing to a TypedDict:** draft the three most common constructor calls. If more than half the fields are `None` in that draft, either the schema is too wide or it should be split into per-variant TypedDicts joined by a union.

## Protocol-based polymorphism

Use `typing.Protocol` for interfaces instead of abstract base classes. This provides type safety without tight coupling.

```python
import typing as tp

class StorageBackend(tp.Protocol):
    async def read(self, key: str) -> bytes: ...
    async def write(self, key: str, data: bytes) -> None: ...

def process_data(storage: StorageBackend) -> None:
    # Any class implementing read/write will satisfy this
    ...
```

## Async-first for I/O

Use `async`/`await` for all I/O operations (network, file, database). Use `asyncio.sleep()` for delays, never blocking `time.sleep()`. Use context managers for resource cleanup.

```python
async def fetch_data(url: str) -> dict[str, str]:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

## Retry pattern for unreliable operations

Wrap network calls and external API interactions with retry logic using exponential backoff.

```python
import asyncio
import logging

logger = logging.getLogger(__name__)

async def fetch_with_retry(
    url: str,
    max_attempts: int = 3,
    base_delay: float = 1.0,
) -> dict[str, str]:
    for attempt in range(1, max_attempts + 1):
        try:
            return await fetch_data(url)
        except (TimeoutError, ConnectionError) as exc:
            if attempt == max_attempts:
                raise
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning("Attempt %d/%d failed: %s, retrying in %.1fs", attempt, max_attempts, exc, delay)
            await asyncio.sleep(delay)
    raise RuntimeError("Unreachable")
```

## Logging over print

Never use `print()` in production code. Use the `logging` module. Log with `exc_info=True` when catching exceptions.

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Processing request %s", request_id)
logger.warning("Slow response: %.2fs", elapsed)
logger.error("Failed to connect", exc_info=True)
```

## Exception handling: no blind except, log before swallowing

Never catch `Exception` or `BaseException` silently. Allowed patterns:

```python
# CORRECT — re-raise after logging
try:
    result = await fetch()
except Exception:
    logger.error("Unexpected error", exc_info=True)
    raise

# CORRECT — log with exc_info=True (only when you truly need to swallow)
try:
    result = await fetch()
except Exception:
    logger.exception("Failed to fetch, continuing")

# PREFERRED — catch specific exceptions
try:
    result = await fetch()
except TimeoutError as exc:
    logger.warning("Timeout: %s", exc, exc_info=True)
    raise
```

Enforced by ruff rules `BLE001` (blind-except) and `TRY` (exception handling patterns).

## Ruff rules enforced

```
select = ["E", "W", "F", "I", "B", "C4", "UP", "ARG", "SIM", "TID", "N", "RUF",
          "ASYNC", "TRY", "BLE", "RET", "LOG", "DTZ"]
ignore = ["E501", "TRY003"]
```

Parent-relative imports (`from ..`) are banned via `ban-relative-imports = "parents"` in `[tool.ruff.lint.flake8-tidy-imports]`.

## See also

- [`SOLID_PRINCIPLES.md`](SOLID_PRINCIPLES.md) — design principles for classes and modules
- [`CODING_PRINCIPLES.md`](CODING_PRINCIPLES.md) — Karpathy-inspired behavioral guidelines
- [`FASTAPI_PATTERNS.md`](FASTAPI_PATTERNS.md) — FastAPI-specific architecture patterns
- Root [`CLAUDE.md`](../../CLAUDE.md) — enforced rules summary
