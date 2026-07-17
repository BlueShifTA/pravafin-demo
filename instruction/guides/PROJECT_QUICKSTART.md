# Project Quickstart: Minimal Structures

**Choose your project type below. Use these as starting points.**

Each template includes:
- Minimal folder structure (no bloat)
- Essential files only
- Ready to scaffold with Codex
- Easy to extend with features

---

## 🔌 REST API (FastAPI + SQLite)

**Use for:** Backend API, microservice, data service

**Setup time:** 30 minutes

**Structure:**
```
my-api/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── models.py            # SQLAlchemy models
│   ├── database.py          # DB connection
│   └── api/
│       ├── __init__.py
│       ├── users.py         # User endpoints
│       └── items.py         # Item endpoints (example)
├── tests/
│   ├── __init__.py
│   ├── test_users.py        # User tests
│   └── conftest.py          # Shared fixtures
├── .env.example
├── requirements.txt
├── README.md
└── .gitignore
```

**Files count:** 15 files
**Complexity:** Low
**Default database:** SQLite (in src/app.db)

**How to scaffold:**
```
Use Codex:
"Generate a REST API for [domain]:
 - Models: User, Item
 - Endpoints: CRUD for User and Item
 - Database: SQLite + SQLAlchemy
 - Include: tests, requirements.txt, .env.example"
```

**Run it:**
```bash
pip install -r requirements.txt
python -m uvicorn src.main:app --reload
# Visit http://localhost:8000/docs
```

**Key files to understand:**
- `src/main.py` — FastAPI app setup, routes
- `src/models.py` — Database models (User, Item)
- `src/database.py` — DB connection + session
- `tests/test_users.py` — Unit tests for endpoints

---

## 🖥️ Web Dashboard (Next.js + FastAPI)

**Use for:** Admin dashboard, data visualization, user-facing app

**Setup time:** 1 hour

**Structure:**
```
my-dashboard/
├── backend/                 # FastAPI (from REST API above)
│   ├── src/
│   │   ├── main.py
│   │   ├── models.py
│   │   └── api/
│   ├── requirements.txt
│   └── .env.example
├── frontend/                # Next.js
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx         # Home page
│   │   ├── dashboard/
│   │   │   └── page.tsx
│   │   └── api/
│   │       └── route.ts     # Optional: API proxy
│   ├── components/
│   │   ├── Header.tsx
│   │   └── UserCard.tsx
│   ├── lib/
│   │   └── api.ts           # API client functions
│   ├── package.json
│   ├── .env.example
│   └── tsconfig.json
├── docker-compose.yml       # Run both services
└── README.md
```

**Files count:** 25 files
**Complexity:** Medium
**Default database:** SQLite (backend)

**How to scaffold:**
```
Backend (Codex):
"Generate FastAPI backend for user management:
 - Models: User, Dashboard
 - Endpoints: GET/POST /users, GET /dashboard
 - Include tests"

Frontend (Codex):
"Generate Next.js dashboard:
 - Page: /dashboard (shows user data)
 - Component: UserCard (display user)
 - API client: fetch data from /api/users
 - Use SWR for data fetching"
```

**Run it:**
```bash
# Terminal 1: Backend
cd backend
pip install -r requirements.txt
python -m uvicorn src.main:app

# Terminal 2: Frontend
cd frontend
pnpm install
pnpm run dev
# Visit http://localhost:3000
```

**Key files to understand:**
- `frontend/lib/api.ts` — API client functions
- `frontend/app/dashboard/page.tsx` — Dashboard component
- `backend/src/api/users.py` — User endpoints

---

## 🛠️ CLI Tool (Click/Typer)

**Use for:** Command-line tool, automation, scripts

**Setup time:** 20 minutes

**Structure:**
```
my-cli-tool/
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI entry point (Click or Typer)
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── list.py          # list command
│   │   ├── add.py           # add command
│   │   └── delete.py        # delete command
│   └── utils.py             # Helper functions
├── tests/
│   ├── __init__.py
│   └── test_commands.py
├── requirements.txt
├── setup.py
├── README.md
└── .gitignore
```

**Files count:** 12 files
**Complexity:** Low
**Default database:** None (or SQLite if needed)

**How to scaffold:**
```
Use Codex:
"Generate CLI tool using Typer:
 - Commands: list, add, delete
 - Help text for each command
 - Error handling
 - Include tests"
```

**Run it:**
```bash
pip install -r requirements.txt
python -m src.main --help
python -m src.main list
python -m src.main add "item name"
```

**Key files to understand:**
- `src/main.py` — CLI app (Typer)
- `src/commands/list.py` — List command implementation
- `src/commands/add.py` — Add command implementation

---

## 📊 Data Pipeline (Batch Job)

**Use for:** Scheduled data processing, ETL, reporting

**Setup time:** 1 hour

**Structure:**
```
my-pipeline/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI app (optional, for monitoring)
│   ├── jobs/
│   │   ├── __init__.py
│   │   ├── import_data.py   # Job 1: import
│   │   ├── process_data.py  # Job 2: process
│   │   └── export_data.py   # Job 3: export
│   ├── database.py
│   ├── models.py
│   └── config.py            # Schedule config
├── tests/
│   ├── __init__.py
│   └── test_jobs.py
├── requirements.txt
├── .env.example
├── README.md
└── .gitignore
```

**Files count:** 16 files
**Complexity:** Medium
**Default database:** SQLite (transform data)

**How to scaffold:**
```
Use Codex:
"Generate data pipeline:
 - Job 1: import data from CSV
 - Job 2: validate and transform
 - Job 3: export to database
 - Schedule: daily at 8 AM
 - Include: logging, error handling"
```

**Run it:**
```bash
pip install -r requirements.txt
python -m src.jobs.import_data        # Run manually
# Or schedule with APScheduler (runs automatically)
```

**Key files to understand:**
- `src/jobs/import_data.py` — Data import logic
- `src/jobs/process_data.py` — Transformation logic
- `src/jobs/export_data.py` — Data export logic

---

## 🎮 Microservice

**Use for:** Single-responsibility service, part of larger system

**Setup time:** 45 minutes

**Structure:**
```
my-microservice/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── models.py
│   ├── health.py            # Health check endpoint
│   └── api/
│       └── v1/
│           ├── __init__.py
│           └── items.py     # Main feature
├── tests/
│   ├── __init__.py
│   └── test_api.py
├── Dockerfile               # Container image
├── .dockerignore
├── requirements.txt
├── .env.example
├── README.md
└── .gitignore
```

**Files count:** 16 files
**Complexity:** Low (code) + Medium (Docker)
**Default database:** PostgreSQL (or SQLite for MVP)

**How to scaffold:**
```
Use Codex:
"Generate FastAPI microservice:
 - Endpoints: GET /health, POST /items, GET /items
 - Database: SQLite
 - Include: Dockerfile, tests
 - Error handling: HTTP status codes"
```

**Run it:**
```bash
# Locally
pip install -r requirements.txt
python -m uvicorn src.main:app

# Docker
docker build -t my-service .
docker run -p 8000:8000 my-service
```

**Key files to understand:**
- `src/health.py` — Health check (liveness probe)
- `Dockerfile` — Container definition

---

## 📋 Comparison Table

| Project Type | Setup Time | Complexity | Database | Best For |
|--------------|-----------|-----------|----------|----------|
| REST API | 30 min | Low | SQLite | Microservice, backend |
| Dashboard | 1 hour | Medium | SQLite | Admin UI, visualization |
| CLI Tool | 20 min | Low | Optional | Automation, scripts |
| Data Pipeline | 1 hour | Medium | SQLite | ETL, reporting |
| Microservice | 45 min | Low (code) | SQLite | Service mesh |

---

## 🚀 Scaffold Workflow

For any project type:

1. **Create empty folder:**
   ```bash
   mkdir my-project
   cd my-project
   git init
   ```

2. **Create folder structure** (from above)

3. **Use Codex to scaffold:**
   Copy the prompt from your project type above into Codex

4. **Run locally:**
   ```bash
   pip install -r requirements.txt
   [Run command from your project type]
   ```

5. **Test it:**
   ```bash
   pytest tests/
   ```

6. **Build features** from SOLO_WORKFLOW.md Phase 5

---

## 📌 Tips

**Folder names matter:**
- `src/` — Source code (keeps things clean)
- `tests/` — Test files (keeps them separate)
- `backend/` and `frontend/` — For full-stack (clear separation)

**Files matter:**
- `.env.example` — Template for environment variables (share with team)
- `requirements.txt` — All dependencies (reproducible installs)
- `README.md` — One page: what it is, how to run it

**Don't include:**
- `docs/` folder (add later)
- `scripts/` folder (add later)
- `.devcontainer/` (add later if team)
- `docker-compose.yml` (add later unless microservice)

---

## 🔗 Next Steps

1. **Pick your project type** (above)
2. **Read AGENT_ADAPTATION_PROMPTS.md** (exact prompts for scaffolding)
3. **Use Codex** to scaffold (Phase 4 of SOLO_WORKFLOW.md)
4. **Run locally** and test
5. **Build features** (Phase 5)

---

**Time to choose:** 5 minutes
**Time to scaffold:** 30-60 minutes
**Status:** Ready to generate boilerplate
