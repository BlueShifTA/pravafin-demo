# Project Instruction

Single source of truth for starting new projects with selected agents and project architectures. Combines a runnable full-stack template with instructional documentation for teams.

## What's Included

- **Runnable template:** FastAPI backend + Next.js frontend with CI, pre-commit, and dev tooling
- **Instructional docs:** Role-based templates, coding profiles, workflow guides, and reference materials (`instruction/`)
- **Unified coding rules:** `CLAUDE.md` as the enforced-rules entrypoint, with detailed references in `instruction/reference/`

## Project Structure

```text
project-instruction/
├── CLAUDE.md          # Enforced coding rules entrypoint (links to instruction/reference/)
├── README.md
├── justfile           # Root automation commands
├── pyproject.toml     # Python workspace config
├── uv.lock
├── projects/
│   ├── backend/       # FastAPI app (example endpoints, tests)
│   └── frontend/      # Next.js app (MUI, React Query, Orval)
├── devops/            # Pre-commit config, bootstrap/check scripts, CI Docker
├── docs/              # Sphinx documentation
└── instruction/       # Role templates, coding profiles, guides, reference
```

## Prerequisites

- Python 3.14+
- [uv](https://github.com/astral-sh/uv)
- [just](https://github.com/casey/just)
- Node.js 20+

## Quick Start

```bash
just install        # Install all dependencies + pre-commit hooks
just run-backend    # Start FastAPI on :8000
just run-frontend   # Start Next.js on :3000 (new terminal)
```

Open `http://localhost:3000`

## Commands

All automation via `just` — run `just --list` for the full set.

| Command | Description |
|---------|-------------|
| `just install` | Install Python + Node + pre-commit |
| `just run-backend` / `just run-frontend` | Dev servers |
| `just test` | Backend (pytest) + frontend (vitest) tests |
| `just lint` | Whole-repo pre-commit run (format, lint, typecheck, custom checks) |
| `just format` | Auto-fix formatting (ruff + prettier + eslint) |
| `just typecheck` | mypy + pyright + tsc |
| `just run-ci` | Mirror GitHub Actions CI locally (coverage gate 80%) |
| `just generate-frontend-types` | Regenerate Orval API client |
| `just setup` | One-shot scaffold: bootstrap + install + checklist |
| `just bootstrap` | Rename template placeholders only |
| `just template-check` | List remaining template remnants (exit 0 = clean) |
| `just template-reset-history` | Final de-templating step: wipe template git history into one initial commit |
| `just create-version [X.Y.Z]` | Tag + push a release (empty = auto patch bump) |
| `just clean` | Delete deps, build outputs, tool caches (restore: `just install`) |

Before every commit: `just lint && just typecheck && just test` — never `--no-verify`.

## API Contract (FastAPI → OpenAPI → Orval → Frontend)

1. FastAPI serves OpenAPI at `http://127.0.0.1:8000/openapi.json`
2. Frontend downloads it into `projects/frontend/openapi.json`
3. Orval generates typed models + React Query hooks into `projects/frontend/src/lib/generated/`

Regenerate after backend API changes: `just run-backend`, then `just generate-frontend-types`.

## Template Demo Surface (Replace After Bootstrap)

- Backend: `GET /health`, `GET /ready`, `POST /api/example/echo`
- Frontend: health widget, setup form on home page

After first successful build:
1. Replace template endpoints/components
2. Run `just template-check` until it reports no remnants
3. Update `CLAUDE.md` and `README.md` for your project

## Documentation

- Coding rules and workflow: `CLAUDE.md` (read before opening a PR)
- Instructional docs: `instruction/README.md` — role templates, coding profiles, workflow guides, reference materials
- Sphinx docs: `docs/` (build with `cd docs && sphinx-build -b html . _build/html`)

## License

Template scaffold provided as-is for reuse and modification.
