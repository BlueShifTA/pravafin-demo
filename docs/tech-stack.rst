Technology Stack
================

This page documents the current template stack and supporting tooling.

Backend Stack
-------------

Runtime and App Framework
^^^^^^^^^^^^^^^^^^^^^^^^^

* **Python 3.14+**
* **FastAPI** for the backend API
* **pydantic-settings** for application settings/config
* **uvicorn** for local ASGI serving

Project Layout
^^^^^^^^^^^^^^

* App package: ``projects/backend/coresat/`` (renamed by bootstrap)
* Routers: ``projects/backend/coresat/api/``
* Settings: ``projects/backend/coresat/core/config.py``
* Tests: ``projects/backend/tests/``

Backend Quality Tooling
^^^^^^^^^^^^^^^^^^^^^^^

* **Ruff** (lint + format)
* **Mypy** (type checking)
* **Pyright** (type checking)
* **pytest** + **pytest-cov**
* **pre-commit**

Frontend Stack
--------------

Core Framework
^^^^^^^^^^^^^^

* **Next.js 15** (App Router)
* **React 18**
* **TypeScript 5**

UI, Styling, and State
^^^^^^^^^^^^^^^^^^^^^^

* **MUI** (theme + components)
* **Tailwind CSS 3**
* **@tanstack/react-query**
* **axios** (dependency available for custom API calls)

API Contract / Codegen
^^^^^^^^^^^^^^^^^^^^^^

* **FastAPI OpenAPI** schema served by backend
* **Orval** for generated TypeScript models and React Query hooks
* Generated output:
  - ``projects/frontend/src/lib/generated/endpoints.ts``
  - ``projects/frontend/src/lib/generated/models/*``

Frontend Quality Tooling
^^^^^^^^^^^^^^^^^^^^^^^^

* **ESLint 9** (config: ``projects/frontend/eslint.config.mjs``)
* **Prettier 3**
* **TypeScript compiler** (``tsc --noEmit``)

Repository Tooling
------------------

Automation
^^^^^^^^^^

* **just** command runner (root ``justfile``)
* Root commands cover install, run, lint, typecheck, tests, and CI-equivalent checks

Documentation
^^^^^^^^^^^^^

* **Sphinx**
* **sphinx-rtd-theme**
* **sphinx-autodoc-typehints**

CI/CD (GitHub Actions)
----------------------

CI workflow: ``.github/workflows/ci.yml``

* Frontend job:
  - ``pnpm install --frozen-lockfile``
  - Prettier check
  - ESLint
  - Typecheck
  - Next.js build
* Backend job:
  - ``uv sync --all-groups --all-packages``
  - Ruff lint + format check
  - sys.path mutation guard check
  - pytest
  - pytest with coverage + Codecov upload

Docs deploy workflow: ``.github/workflows/docs.yml``

* Builds Sphinx docs from ``docs/``
* Uploads Pages artifact
* Deploys to GitHub Pages
