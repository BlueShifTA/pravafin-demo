---
name: format-code
description: Auto-format and fix code style issues. Use after writing code, when lint checks fail, or when the user asks to format or fix style.
allowed-tools: Bash, Read
argument-hint: [backend|frontend|all]
---

Auto-format code using project formatters (ruff for Python, prettier + eslint for TypeScript).

Scope defaults to `all` unless specified: `$ARGUMENTS`

## Steps

1. Run the formatter:
   ```bash
   just format
   ```

2. If scoped to `backend` only:
   ```bash
   cd $(just --evaluate ROOT) && uv run ruff check --fix $(just --evaluate BACKEND)
   cd $(just --evaluate ROOT) && uv run ruff format $(just --evaluate BACKEND)
   ```

3. If scoped to `frontend` only:
   ```bash
   cd $(just --evaluate FRONTEND) && pnpm run prettier:write && pnpm run lint:fix
   ```

4. Report what changed — list files modified by the formatter.
