---
name: generate-types
description: Generate frontend API client types from the backend OpenAPI schema. Use after modifying backend API routes, adding/changing endpoints, or updating request/response models.
disable-model-invocation: true
allowed-tools: Bash, Read
---

Generate the frontend TypeScript API client from the backend's OpenAPI schema.

## Prerequisites

The backend server must be running for Orval to fetch the schema. If it's not running, start it first.

## Steps

1. **Check if backend is running:**
   ```bash
   curl -s http://localhost:8000/health || echo "NOT_RUNNING"
   ```

2. **If not running**, inform the user:
   > Backend is not running. Start it with `just run-backend` in another terminal, then re-run `/generate-types`.

3. **If running**, generate types:
   ```bash
   just generate-frontend-types
   ```

4. **Verify** the generated files exist and report what was generated:
   ```bash
   ls -la $(just --evaluate FRONTEND)/src/lib/generated/
   ```

5. Report which files were generated/updated.
