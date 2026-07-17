Development Guide
=================

This guide covers local development workflows for the template.

Core Workflow
-------------

Preferred root commands (via ``just``):

* Install everything: ``just install``
* Run backend: ``just run-backend``
* Run frontend: ``just run-frontend``
* Tests: ``just test``
* Lint: ``just lint``
* Format: ``just format``
* Typecheck: ``just typecheck``
* CI-equivalent local checks: ``just run-ci``

Backend Development
-------------------

Run the backend::

   just run-backend

Direct equivalent::

   PYTHONPATH=projects/backend uv run uvicorn coresat.main:app --reload --host 127.0.0.1 --port 8000

Tests
^^^^^

Run tests::

   just test

Coverage (80 percent threshold, enforced in CI)::

   just run-ci

Direct coverage command (current package path)::

   PYTHONPATH=projects/backend uv run pytest projects/backend/tests --cov=projects/backend/coresat --cov-report=term-missing

Linting / Formatting / Type Checking
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Backend quality commands are also available directly:

* ``uv run ruff check projects/backend``
* ``uv run ruff format projects/backend``
* ``PYTHONPATH=projects/backend uv run mypy projects/backend/coresat``
* ``uv run pyright projects/backend/coresat``

Frontend Development
--------------------

Run the frontend::

   just run-frontend

Direct equivalent::

   cd projects/frontend && pnpm run dev

Frontend checks:

* ``cd projects/frontend && pnpm run lint``
* ``cd projects/frontend && pnpm run typecheck``
* ``cd projects/frontend && pnpm run build``
* ``cd projects/frontend && pnpm run prettier:check``

Frontend lint config lives in ``projects/frontend/eslint.config.mjs``.

API Contract and Code Generation
--------------------------------

The template uses FastAPI -> OpenAPI -> Orval -> React Query hooks.

Backend contract:

* OpenAPI schema endpoint: ``http://127.0.0.1:8000/openapi.json``
* Health endpoints: ``/health`` and ``/ready``
* Example API route: ``/api/example/echo``

Frontend integration:

* Next.js rewrites in ``projects/frontend/next.config.ts`` proxy ``/api/*``, ``/health``, and ``/ready`` to the backend
* Orval config lives in ``projects/frontend/orval.config.ts``
* Generated client output lives in ``projects/frontend/src/lib/generated/``

Generate frontend API types/hooks::

   just generate-frontend-types

This runs the frontend ``pnpm run api`` script, which:

1. Downloads ``/openapi.json`` into ``projects/frontend/openapi.json``
2. Runs Orval to generate models + React Query hooks

Pre-commit Hooks
----------------

Pre-commit config: ``devops/.pre-commit-config.yaml``

Current local hooks include checks for:

* Ruff lint/format (backend)
* Mypy + Pyright (backend)
* Prettier + ESLint (frontend)
* sys.path mutation guard script

Install hooks::

   uv run pre-commit install --config devops/.pre-commit-config.yaml

Run all hooks manually::

   uv run pre-commit run --config devops/.pre-commit-config.yaml --all-files

Agent Docs
----------

Template users should update ``CLAUDE.md`` and ``README.md`` after replacing template examples.

Documentation
-------------

Build Sphinx docs locally::

   cd docs
   sphinx-build -b html . _build/html

Docs deploy workflow is defined in ``.github/workflows/docs.yml``.
