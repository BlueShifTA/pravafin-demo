---
name: run-dev
description: Start development servers (backend and/or frontend).
disable-model-invocation: true
allowed-tools: Bash
argument-hint: [backend|frontend]
---

Start development servers.

Target: `$ARGUMENTS`

## Steps

1. **Determine what to start:**
   - `backend` → `just run-backend`
   - `frontend` → `just run-frontend`
   - empty → Show instructions for running both

2. **Start the server.** Note: this is a long-running process.

3. **If no argument given**, tell the user:
   > Run in separate terminals:
   > - `just run-backend` (http://localhost:8000)
   > - `just run-frontend` (http://localhost:3000)
