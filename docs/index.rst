CoreSat
================

Welcome to the CoreSat documentation.

This template provides a working full-stack baseline with a FastAPI backend, a Next.js App Router frontend, MUI + React Query provider wiring, and Orval-based OpenAPI client generation.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting-started
   development
   tech-stack
   api/modules

Overview
--------

The template includes:

* FastAPI backend in ``projects/backend/coresat``
* Next.js frontend in ``projects/frontend`` (App Router)
* MUI theme/provider setup and shared UI components
* TanStack React Query and generated API hooks via Orval
* Root ``just`` commands for install/test/lint/typecheck/CI checks
* Sphinx docs plus agent-focused docs (``CLAUDE.md``)

Quick Start
-----------

Install everything::

   just install

Run backend and frontend in separate terminals::

   just run-backend
   just run-frontend

Generate frontend API client/types after backend API changes::

   just generate-frontend-types

See :doc:`getting-started` and :doc:`development` for details.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
