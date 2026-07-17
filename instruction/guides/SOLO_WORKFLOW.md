# Solo Consultant Workflow

**Goal:** Rough requirements → Live MVP in 6-8 hours
**Prerequisites:** Claude Code + Codex + TECH_DECISIONS.md + PROJECT_QUICKSTART.md

---

## 🎯 Six Phases (Time-Boxed)

### PHASE 1: Clarify Requirements (1 hour)

**Goal:** Turn "rough requirements" into 1-page clarity

**Tools:** Claude Code + notepad

**Process:**
1. Write down rough requirements (2-3 paragraphs)
2. Use Claude Code:
   ```
   "Here are rough requirements:
    [paste requirements]

    Help me clarify:
    1. Scope: What's MVP? What's later?
    2. Constraints: Performance? Scale? Budget?
    3. Users: Who uses this? How?
    4. Success: How do we know it works?"
   ```
3. Document answers (1-2 pages)

**Output:** 1-page requirements clarity
- MVP scope (specific)
- Constraints (documented)
- Success metrics (3-4 metrics)

**Success Criteria:**
- You can explain MVP in 1 sentence
- You know 3 constraints
- You know 2-3 success metrics

**What to Skip:**
- Detailed user research (do later)
- Full feature list (do later)
- Market analysis (do later)

---

### PHASE 2: Decide Tech Stack (1 hour)

**Goal:** Pick language, framework, database, deployment

**Tools:** TECH_DECISIONS.md (reference, don't overthink)

**Process:**
1. Answer 5 questions using TECH_DECISIONS.md:
   - Language: Python / Go / TypeScript?
   - Framework: FastAPI / Flask / Django (if Python)?
   - Database: SQLite / PostgreSQL / Redis?
   - Deployment: Managed / Serverless / VPS?
   - Testing: Unit only / Unit + Integration / Full pyramid?

2. For MVP, ALWAYS choose:
   - **Language:** Python (if unsure)
   - **Framework:** FastAPI (if Python)
   - **Database:** SQLite (easiest)
   - **Deployment:** Managed service (Vercel, Railway, Render)
   - **Testing:** Unit tests only (critical paths)

3. Document decisions (3 lines):
   ```
   Tech Stack:
   - Python + FastAPI + SQLite
   - Deploy: Railway
   - Test: Unit only
   ```

**Output:** Tech stack decided (3 lines)

**Success Criteria:**
- You have 5 decisions
- All decisions are documented
- You're ready to code (no second-guessing)

**What to Skip:**
- Performance analysis (do later)
- Cost comparison (do later)
- Detailed benchmarks (do later)

---

### PHASE 3: Design MVP (1 hour)

**Goal:** 1-page architecture + clear MVP scope

**Tools:** Claude Code + whiteboard/pencil

**Process:**
1. Use Claude Code:
   ```
   "Design a [domain] system:

    Requirements: [from Phase 1]
    Tech Stack: Python + FastAPI + SQLite
    Constraints: [from Phase 1]

    Provide:
    1. MVP scope (what ships first, what's later)
    2. Data model (3-5 main entities)
    3. API endpoints (5-10 core endpoints)
    4. Architecture diagram (text description)"
   ```

2. Ask for:
   - Clear MVP scope (what's in, what's out)
   - Data model sketch (entities + relationships)
   - Endpoint list (method + path + purpose)
   - Risks (what could go wrong?)

3. Draw on whiteboard/paper (box diagram):
   - Boxes: Frontend (if any), Backend, Database
   - Arrows: API calls, DB queries
   - Labels: Keep simple

**Output:** 1-page architecture sketch
- MVP scope (clear boundaries)
- Data model (5-10 lines)
- Endpoint list (10-15 lines)
- Diagram (text or photo)

**Success Criteria:**
- You know exactly what to build (MVP)
- You know what NOT to build yet
- You can sketch the flow in 5 minutes
- You identified 2-3 risks

**What to Skip:**
- Complex diagrams (text is fine)
- Detailed error handling (add later)
- Performance optimization (do after MVP works)
- Advanced features (do later)

---

### PHASE 4: Scaffold Boilerplate (1-2 hours)

**Goal:** Working project structure + test setup

**Tools:** Codex + PROJECT_QUICKSTART.md + AGENT_ADAPTATION_PROMPTS.md

**Process:**
1. Choose project type from PROJECT_QUICKSTART.md:
   - REST API?
   - Web Dashboard?
   - CLI Tool?
   - Data Pipeline?

2. Use Codex:
   ```
   "Generate [PROJECT_TYPE] for [domain]:

    Requirements: [from Phase 1]
    Models: [from Phase 3]
    Endpoints: [from Phase 3]
    Database: SQLite + SQLAlchemy

    Include:
    - Project structure (folders + files)
    - main.py (FastAPI app)
    - models.py (SQLAlchemy models)
    - tests/test_api.py (starter tests)
    - requirements.txt
    - .env.example
    - README.md (one page)"
   ```

3. Run locally:
   ```bash
   python -m pip install -r requirements.txt
   python -m uvicorn main:app --reload
   ```

4. Test:
   ```bash
   pytest tests/
   ```

**Output:** Working boilerplate
- Project cloned locally
- Dependencies installed
- API running (FastAPI docs at /docs)
- Tests passing

**Success Criteria:**
- `python -m uvicorn main:app` works
- API docs visible at http://localhost:8000/docs
- `pytest` passes
- You can add a new endpoint without refactoring

**What to Skip:**
- Docker (add later)
- CI/CD (add later)
- Logging (add later)
- Monitoring (add later)

---

### PHASE 5: Build Features + Auto-Quality (4-5 hours)

**Goal:** MVP working, core features shipped, production-ready

**Tools:** Codex + Claude Code + Context7 + Autoresearch + IDE

**Process (For Each Feature):**

**Step 5.0:** Load context (`.consultant-context.md`)
- Tech stack, models, endpoints, critical paths

**Step 5.1:** Implement with Codex (30-60 min)
- Write code using existing patterns

**Step 5.2:** Code review with Context7 + Claude (15 min)
- Fetch accurate docs: `context7 fetch fastapi 0.104.0`
- Review: security, simplicity, performance

**Step 5.3:** Auto-improve with Autoresearch (20 min)
```bash
/autoresearch
Goal: Simplify code while tests pass
Metric: Lines of code (lower better)
Iterations: 10
```

**Step 5.4:** Hunt bugs with Autoresearch:debug (15 min)
```bash
/autoresearch:debug
Symptom: [describe any issues]
Iterations: 15
```

**Step 5.5:** Auto-fix errors with Autoresearch:fix (15 min)
```bash
/autoresearch:fix --target "pytest && ruff && mypy"
Iterations: unlimited (stops at 0 errors)
```

**Step 5.6:** Security audit with Autoresearch:security (15 min)
```bash
/autoresearch:security --fix
Iterations: 10
```

**Step 5.7:** Expert review with Autoresearch:predict (5 min)
```bash
/autoresearch:predict --chain debug,fix,security
```

**Repeat 5.1-5.7 for each feature**

**Output:** Production-ready MVP
- All features working
- Code simplified + reviewed
- Bugs found + fixed
- Security audited
- Zero errors
- Expert consensus

**Success Criteria:**
- All Phase 3 endpoints work
- Tests passing (80%+ critical)
- Code simplified (verified)
- Security audit passed
- Expert consensus reached
- Zero errors
- Production-ready

**See:** PHASE_5_AUTO_QUALITY.md for detailed guide

---

### PHASE 6: Ship (1 hour)

**Goal:** Live MVP accessible from internet

**Tools:** Codex + Railway/Vercel/Render

**Process:**
1. Create account on managed host (Railway, Vercel, or Render)

2. Use Codex:
   ```
   "Generate deployment files for FastAPI + SQLite:

    - Dockerfile
    - docker-compose.yml
    - GitHub Actions workflow (deploy on push)
    - .env.example

    Target: [Railway/Render/Heroku]"
   ```

3. Push to GitHub:
   ```bash
   git add .
   git commit -m "MVP: core features working"
   git push origin main
   ```

4. Connect repo to Railway/Render:
   - Link GitHub repo
   - Set environment variables
   - Deploy (auto-deploys on push)

5. Test live:
   ```bash
   curl https://[your-app].railway.app/docs
   ```

**Output:** Live MVP
- Accessible from internet
- Database persisted (SQLite uploaded or use managed DB)
- Auto-deploys on git push

**Success Criteria:**
- You have a public URL
- API responds (GET /docs works)
- You can share with someone
- Deployment takes <30 min

**What to Skip:**
- Custom domain (add later)
- SSL (managed host handles it)
- CDN (add later)
- Analytics (add later)

---

## 📊 Time Breakdown

| Phase | Time | What | Output |
|-------|------|------|--------|
| 1. Clarify | 1h | Understand problem | 1-page clarity |
| 2. Decide | 1h | Pick tech | Tech stack (3 lines) |
| 3. Design | 1h | Plan MVP | Architecture sketch |
| 4. Scaffold | 1-2h | Generate boilerplate | Working project |
| 5. Build | 3-4h | Code features | Live MVP |
| 6. Ship | 1h | Deploy | Public URL |
| **TOTAL** | **6-8h** | **Requirements → MVP** | **Live product** |

---

## 🔄 Iterative Refinement (After MVP Ships)

Once MVP is live:

1. **Week 1:** Gather feedback (users, stakeholders)
2. **Week 2:** Bug fixes + critical improvements
3. **Week 3:** Add Phase 2 features (from Phase 1 "later" list)
4. **Week 4:** Performance optimization (if needed)

---

## 🚫 Common Mistakes to Avoid

**MISTAKE:** Spending 2 hours on architecture before coding
- ❌ Over-design
- ✅ Spend 1 hour, then iterate

**MISTAKE:** Writing tests for everything in Phase 5
- ❌ 50% time on tests
- ✅ Unit tests for critical paths only

**MISTAKE:** Deploying to custom VPS instead of managed
- ❌ 2+ hours on DevOps
- ✅ Use Railway/Render (30 min total)

**MISTAKE:** Refactoring code before MVP ships
- ❌ Never ships
- ✅ Build, ship, then refactor

**MISTAKE:** Adding Phase 2 features in Phase 5
- ❌ MVP never ships
- ✅ Strict MVP scope

---

## 🤖 Agent Usage by Phase

| Phase | Agent | Purpose | Tool |
|-------|-------|---------|------|
| 1. Clarify | Claude Code | Understand problem | AGENT_ADAPTATION_PROMPTS |
| 2. Decide | None | Pick tech | TECH_DECISIONS.md |
| 3. Design | Claude Code | Architecture | AGENT_ADAPTATION_PROMPTS |
| 4. Scaffold | Codex | Boilerplate | AGENT_ADAPTATION_PROMPTS |
| 5. Build | Codex + Claude | Features | AGENT_ADAPTATION_PROMPTS |
| 6. Ship | Codex | Deployment | AGENT_ADAPTATION_PROMPTS |

---

## ✅ Phase Checklist

**Phase 1: Clarify**
- [ ] Requirements documented (2-3 pages)
- [ ] MVP scope clear (1 sentence)
- [ ] Constraints documented (3+)
- [ ] Success metrics defined (3+)

**Phase 2: Decide**
- [ ] Language chosen
- [ ] Framework chosen
- [ ] Database chosen
- [ ] Deployment platform chosen
- [ ] Testing strategy chosen

**Phase 3: Design**
- [ ] MVP scope finalized
- [ ] Data model defined (5+ entities)
- [ ] Endpoints listed (10+)
- [ ] Architecture sketched
- [ ] Risks identified (2+)

**Phase 4: Scaffold**
- [ ] Project created locally
- [ ] Dependencies installed
- [ ] App runs (`uvicorn main:app`)
- [ ] Tests pass (`pytest`)
- [ ] Endpoints visible in /docs

**Phase 5: Build**
- [ ] All MVP features implemented
- [ ] Tests passing
- [ ] No major bugs
- [ ] Can demo

**Phase 6: Ship**
- [ ] Deployed to public URL
- [ ] API responds
- [ ] Database persists
- [ ] Auto-deploy configured (git push)

---

**Total Time:** 6-8 hours from requirements to live MVP
**Status:** Ready to use
**Next:** Phase 1 with AGENT_ADAPTATION_PROMPTS.md
