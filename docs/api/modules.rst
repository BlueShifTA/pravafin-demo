API Reference
=============

This template ships with a small FastAPI example API to verify local integration and frontend code generation.

Template Endpoints
------------------

Health endpoints:

* ``GET /health`` -> returns ``{"status": "ok"}``
* ``GET /ready`` -> returns ``{"status": "ready"}``

Example endpoint (under default API prefix ``/api``):

* ``POST /api/example/echo`` -> echoes a typed request/response model

OpenAPI Contract
----------------

FastAPI serves the schema at:

* ``/openapi.json`` (local default: ``http://127.0.0.1:8000/openapi.json``)

The frontend downloads this schema and generates models/hooks using Orval.

Related files:

* Backend app entrypoint: ``projects/backend/coresat/main.py``
* Frontend Orval config: ``projects/frontend/orval.config.ts``
* Generated client output: ``projects/frontend/src/lib/generated/``

Template Note
-------------

This page is intentionally lightweight for the template.

After bootstrap and feature implementation, replace this page with project-specific API documentation and endpoint references.
