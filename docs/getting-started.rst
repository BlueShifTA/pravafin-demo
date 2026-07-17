Getting Started
===============

This guide helps you run the template locally and understand the initial workflow.

Prerequisites
-------------

Before you begin, install:

* **Python 3.14+**
* **uv** (Python package manager)
* **Node.js 20+**
* **just** (recommended command runner)
* **Docker** (optional)

Initial Setup
-------------

1. Clone the repository::

      git clone <repository-url>
      cd coresat

2. Install backend + frontend dependencies and pre-commit hooks::

      just install

3. Validate the template state::

      just test
      just lint
      just typecheck

Run the Apps
------------

Run the backend in one terminal::

   just run-backend

Run the frontend in another terminal::

   just run-frontend

Open ``http://localhost:3000``.

The template homepage includes example/demo sections that verify:

* frontend layout/components load
* Next.js rewrites are active
* generated React Query hooks can call the backend health endpoint

Generate Frontend API Client
----------------------------

When backend API models or routes change, regenerate frontend types/hooks.

1. Ensure backend is running (OpenAPI served at ``http://127.0.0.1:8000/openapi.json``)
2. Run::

      just generate-frontend-types

This downloads the OpenAPI schema into ``projects/frontend/openapi.json`` and regenerates the Orval client in ``projects/frontend/src/lib/generated/``.

Template Bootstrap Flow
-----------------------

One-shot scaffold (rename + install + de-templating checklist)::

   just setup

For automation/non-interactive use, pass explicit args (forwarded to bootstrap)::

   just setup --project-name "My App" --project-slug my-app --python-package my_app --non-interactive

``just bootstrap`` runs the rename step alone.

Post-First-Build Cleanup (Required)
-----------------------------------

After your first successful build and smoke test:

1. Remove/replace template examples (routes, components, tests, docs)
2. Run ``just template-check`` until it reports no remnants (it lists every
   leftover brand string and demo file with file:line)
3. Update ``CLAUDE.md`` and ``README.md`` to describe your real project

Project Structure (High Level)
------------------------------

::

   coresat/
   ├── docs/                      # Sphinx docs
   ├── projects/
   │   ├── backend/
   │   │   ├── package/           # FastAPI app package (renamed by bootstrap)
   │   │   └── tests/
   │   └── frontend/
   │       ├── src/app/           # Next.js App Router pages/layout
   │       ├── src/components/
   │       ├── src/lib/generated/ # Orval-generated client/models
   │       └── src/theme/
   ├── devops/                    # Pre-commit config, bootstrap/check scripts
   ├── instruction/               # Role templates, profiles, guides, reference
   ├── justfile
   └── CLAUDE.md

Next Steps
----------

* Read :doc:`development` for workflows and quality checks
* Read :doc:`tech-stack` for tool inventory and CI docs
* Read :doc:`api/modules` for the template API endpoints and contract flow
