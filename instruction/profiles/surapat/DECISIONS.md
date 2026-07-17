# Tech Decision Tree

Choose your tech stack for MVP. **For MVP: Always pick the left (simpler) option.**

---

## 1️⃣ Language

| Choice | MVP (Pick This) | Scale Later |
|--------|-----------------|-------------|
| **Python** | ✅ Yes (fast, many frameworks) | Scales well |
| **Go** | ❌ No (steeper learning) | Scales great (performance) |
| **TypeScript** | ❌ No (Node overhead) | Scales (popular) |
| **Rust** | ❌ No (complex) | Scales (fast) |

**Decision:** Python
- Why: Simplest, largest ecosystem, FastAPI is great
- Cost: $0 (open source)
- Learning: 1 day if new to Python

---

## 2️⃣ Framework (if Python)

| Choice | MVP (Pick This) | Scale Later |
|--------|-----------------|-------------|
| **FastAPI** | ✅ Yes (modern, fast) | Scales well |
| **Flask** | ❌ No (too minimal) | Scales (manual) |
| **Django** | ❌ No (too much) | Scales (batteries included) |

**Decision:** FastAPI
- Why: Built-in API docs, fast, modern
- Cost: $0 (open source)
- Setup: 5 minutes

**If TypeScript:** Next.js or Express (choose Next.js for full-stack, Express for API-only)

---

## 3️⃣ Database

| Choice | MVP (Pick This) | Scale Later |
|--------|-----------------|-------------|
| **SQLite** | ✅ Yes (zero ops) | Migrate to PostgreSQL |
| **PostgreSQL** | ❌ No (needs hosting) | Great choice (reliable) |
| **MongoDB** | ❌ No (schema headaches) | Avoid (unless needed) |
| **Redis** | ❌ No (in-memory, data loss) | Add for caching later |

**Decision:** SQLite
- Why: File-based, zero setup, zero hosting cost
- Cost: $0
- Setup: 2 minutes (included with Python)
- Migration: Easy to PostgreSQL later

**For web dashboards:** Add PostgreSQL if multiple users writing simultaneously (SQLite has lock issues)

---

## 4️⃣ Frontend (if Building Web)

| Choice | MVP (Pick This) | Scale Later |
|--------|-----------------|-------------|
| **Next.js** | ✅ Yes (full-stack) | Scales great |
| **React** | ✅ Yes (if API-first) | Scales well |
| **Vue** | ❌ No (smaller ecosystem) | Scales (less common) |
| **Svelte** | ❌ No (niche) | Scales (experimental) |

**Decision:** Next.js (if full-stack) OR React (if API-only)
- Next.js: All-in-one (backend + frontend)
- React: Frontend-only (use separate API)
- Cost: $0 (open source)
- Setup: 5 minutes (create-next-app)

---

## 5️⃣ Deployment

| Choice | MVP (Pick This) | Scale Later |
|--------|-----------------|-------------|
| **Managed (Railway/Render)** | ✅ Yes (no ops) | Stays managed or switch to containers |
| **Serverless (Vercel/Lambda)** | ❌ No (cold starts) | Good for web (Vercel) |
| **Docker VPS (DigitalOcean)** | ❌ No (needs ops) | Great for scale |
| **Kubernetes** | ❌ No (over-complex) | Use only at scale |

**Decision:** Railway or Render
- Why: Git push → auto-deploy, includes database, no DevOps
- Cost: $5-20/month (or free tier)
- Setup: 10 minutes (connect GitHub)

**For front-end only:** Vercel (instant, free)

**For API + database:** Railway (database included)

---

## 6️⃣ Testing

| Strategy | MVP (Pick This) | Scale Later |
|----------|-----------------|-------------|
| **Unit tests (critical paths)** | ✅ Yes (fast, catch bugs) | Keep this |
| **Integration tests** | ❌ No (slow, not critical) | Add after MVP |
| **E2E tests** | ❌ No (slow, brittle) | Add after MVP |
| **No tests** | ❌ No (chaos) | N/A |

**Decision:** Unit tests only
- Why: Fast feedback, prevent regressions
- Coverage: 80% for critical paths, skip edge cases
- Cost: $0 (pytest is free)
- Setup: 5 minutes

**Critical paths to test:**
- User authentication (if you have it)
- Payment/money flows (if applicable)
- Core business logic
- API endpoints (happy path + error cases)

**Skip for MVP:**
- UI tests (do after MVP)
- Load tests (do after MVP)
- Security tests (do after MVP)

---

## 7️⃣ Hosting Database

| Choice | MVP (Pick This) | Scale Later |
|--------|-----------------|-------------|
| **SQLite (file)** | ✅ Yes (free, simple) | Migrate away at scale |
| **Managed PostgreSQL (Render, Railway)** | ✅ Yes (simple) | Keep or self-manage |
| **Self-hosted PostgreSQL** | ❌ No (ops overhead) | Only if specific need |
| **Cloud DBaaS (AWS RDS)** | ❌ No (expensive) | Consider at scale |

**Decision:** Let Railway/Render handle it
- Why: Included, managed, no extra ops
- Cost: Included in Railway/Render plan
- Setup: Automatic (part of deployment)

---

## 8️⃣ Authentication

| Choice | MVP (Pick This) | Scale Later |
|--------|-----------------|-------------|
| **Built-in (FastAPI + JWT)** | ✅ Yes (simple, free) | Works fine |
| **Third-party (Auth0, Firebase)** | ❌ No (extra complexity, cost) | Use if > 1000 users |
| **OAuth (Google, GitHub)** | ❌ No (for MVP, skip) | Add after MVP |
| **No auth** | ❌ No (security risk) | N/A |

**Decision:** Built-in JWT
- Why: Control, no cost, simple
- Cost: $0
- Setup: 30 minutes (FastAPI-JWT-Extended package)
- When to migrate: > 1000 users or compliance needs

---

## 9️⃣ Logging

| Choice | MVP (Pick This) | Scale Later |
|--------|-----------------|-------------|
| **Stdout + logs (file)** | ✅ Yes (simple) | Upgrade to SaaS |
| **Sentry (error tracking)** | ❌ No (overkill) | Add after MVP |
| **DataDog/New Relic** | ❌ No (expensive) | Use at scale |
| **ELK Stack** | ❌ No (self-host hell) | Only if required |

**Decision:** Just log to stdout
- Why: Railway/Render capture logs automatically
- Cost: $0
- Setup: 2 lines of code

---

## 🔟 API Documentation

| Choice | MVP (Pick This) | Scale Later |
|--------|-----------------|-------------|
| **Auto-generated (FastAPI /docs)** | ✅ Yes (free, great) | Keep this |
| **Swagger UI** | ✅ Yes (included with FastAPI) | Keep this |
| **Postman** | ❌ No (extra tool) | Use for testing only |
| **Custom docs** | ❌ No (time waster) | Do after MVP |

**Decision:** FastAPI's built-in OpenAPI docs
- Why: Automatic, beautiful, interactive
- Cost: $0 (included)
- Setup: 0 minutes (auto-generated)

---

## 📋 Quick Decision Card

Print this:

```
MVP TECH STACK (Copy This):
- Language: Python
- Framework: FastAPI
- Database: SQLite
- Frontend: Next.js (or skip if API-only)
- Deployment: Railway
- Testing: Unit tests only (critical paths)
- Auth: JWT (built-in)
- Logging: Stdout
- Docs: FastAPI /docs

WHEN TO MIGRATE:
- 100+ users → Consider managed PostgreSQL
- 1000+ users → Consider Auth0
- Performance issues → Add caching (Redis)
- Complex frontend → Add Next.js
- Multiple servers → Add Docker
```

---

## 🎯 Common Paths

### REST API Only
```
Python + FastAPI + SQLite + Railway + Pytest
Cost: $0-20/month
Setup: 30 min
```

### Web Dashboard (Full-Stack)
```
Python + FastAPI + Next.js + PostgreSQL (on Railway) + Pytest
Cost: $0-20/month
Setup: 1 hour
```

### CLI Tool
```
Python + Click + SQLite (optional) + PyPI
Cost: $0
Setup: 30 min
```

### Data Pipeline
```
Python + FastAPI + PostgreSQL + Railway + APScheduler
Cost: $5-20/month
Setup: 1 hour
```

---

## ⚠️ Mistakes to Avoid

❌ **Picking Kubernetes for MVP**
- Use: Managed host (Railway)
- Save: 20+ hours of DevOps

❌ **Picking MongoDB for structured data**
- Use: PostgreSQL (or SQLite for MVP)
- Save: Schema confusion

❌ **Building custom auth**
- Use: JWT (or Auth0 at scale)
- Save: 10+ hours of security work

❌ **Picking NoSQL without reason**
- Use: PostgreSQL/SQLite (relational)
- Save: Data consistency headaches

❌ **Writing E2E tests before shipping**
- Use: Unit tests only
- Save: 20+ hours of test maintenance

---

## 🚀 Next Steps

1. **Pick your stack** from this guide (use defaults for MVP)
2. **Read SOLO_WORKFLOW.md** (Phase 2: Decide is done)
3. **Move to Phase 3: Design** in SOLO_WORKFLOW.md

---

**Time to decide:** 15 minutes (use defaults)
**Time to change later:** 4-8 hours (migration is possible)
**Status:** Ready to build
