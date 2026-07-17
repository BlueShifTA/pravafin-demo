# GitHub Copilot Instructions

This repository uses Python 3.13+ and TypeScript/React. For complete coding rules, see `CLAUDE.md` in the repo root.

## Python Standards

- Python 3.13 with modern syntax: `list[T]`, `dict[K, V]`, `X | None`
- `@dataclass` for data structures, `Protocol` for interfaces
- Ruff for linting/formatting (4-space indent, double quotes, 100 char line length)
- Strict type annotations (pyright/mypy compatible)
- Async-first for all I/O operations
- Same-dir relative imports, cross-module absolute imports, no parent-relative (`..`)
- No lazy imports, no module-level global instances
- Logging over print, no blind except

## TypeScript/React Standards

- TypeScript 5+ strict mode
- Functional components with hooks only
- Tailwind CSS for utilities, MUI components for complex UI
- `@tanstack/react-query` for server state
- Orval-generated API clients for type-safe backend calls
- ESLint + Prettier
- Keep components < 200 lines

## FastAPI Patterns

- Dependency injection: `Annotated[T, Depends(get_dep)]`
- Return appropriate HTTP status codes
- Handle errors with `HTTPException`
- See `projects/backend/coresat/main.py` for middleware patterns

## Testing

- pytest with `httpx.AsyncClient` via `ASGITransport` for endpoint tests
- Prefer integration tests over unit tests
- 80% minimum coverage
- Descriptive names: `test_<function>_<scenario>_<expected_outcome>`
