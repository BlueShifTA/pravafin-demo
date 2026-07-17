## Backend

Minimal FastAPI backend scaffold for `coresat`.

### Entrypoint

- `package/main.py` exports `app`
- FastAPI serves OpenAPI at `GET /openapi.json`

### Local Run

```bash
PYTHONPATH=projects/backend uv run uvicorn coresat.main:app --reload
```

Settings are defined in `package/core/config.py` (default API prefix: `/api`).

### Endpoints

- `GET /health`
- `GET /ready`
- `POST /api/example/echo`

These routes are template examples and are expected to be replaced or extended.
