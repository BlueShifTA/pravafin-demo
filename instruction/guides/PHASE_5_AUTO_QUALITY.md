# Phase 5: Build (With Auto-Quality)

**Previous:** Phase 5 was "just code"
**Now:** Phase 5 is "code + auto-improve + secure + tested"

---

## 🚀 Enhanced Phase 5 (3-4 hours → 4-5 hours)

### Step 5.0: Load Project Context

**File:** `.consultant-context.md` (create at project root)

```markdown
# Project Context

## Tech Stack
- Language: Python
- Framework: FastAPI
- Database: SQLite
- Deployment: Railway

## Key Models
- User (id, email, name, created_at)
- Project (id, name, owner_id, created_at)
- Task (id, project_id, title, status)

## Endpoints (from Phase 3)
- GET /users
- POST /users
- GET /projects
- POST /projects/{id}/tasks

## Dependencies
- FastAPI 0.104.0
- SQLAlchemy 2.0.23
- Pydantic 2.4.2

## Critical Paths (test these)
- User authentication
- Project creation
- Task assignment

## Known Issues
- None yet

## Next Tasks
- [x] Phase 4: Scaffold
- [ ] Phase 5.1: Build feature 1
- [ ] Phase 5.2: Code review
- [ ] Phase 5.3: Auto-improve
- [ ] Phase 5.4: Security audit
```

---

### Step 5.1: Implement Feature (Codex)

**Your code (30-60 min per feature):**

```bash
# Use AGENT_ADAPTATION_PROMPTS.md Phase 5 prompt
# Build one endpoint/feature at a time
```

---

### Step 5.2: Code Review (Context7 + Claude)

**After implementing each feature:**

```bash
# Load context
context7 fetch fastapi 0.104.0
context7 fetch sqlalchemy 2.0.23

# Review prompt (Claude Code):
"Review this code for issues:
[PASTE YOUR CODE]

Use this ACCURATE documentation:
[PASTE CONTEXT7 OUTPUT]

Check:
1. SECURITY: Auth? Input validation? SQL injection risk?
2. SIMPLICITY: Unnecessary complexity? Over-engineered?
3. PERFORMANCE: N+1 queries? Async needed?
4. PATTERNS: Following FastAPI best practices?
5. TESTS: Critical path testable?

Flag issues (don't fix yet, just identify with line numbers)."
```

**Expected output:** 3-5 issues per feature

---

### Step 5.3: Auto-Improve Code (Autoresearch Loop)

**After fixing issues from Step 5.2:**

```bash
# Fix identified issues
# Then run autoresearch to keep improving

/autoresearch
Goal: Simplify code while keeping tests passing
Scope: src/api/**/*.py, src/models.py
Metric: Lines of code (lower is better)
Verify: pytest tests/ -v
Guard: pytest tests/ --cov=src (80%+ coverage)
Iterations: 10

# What it does:
# - Makes ONE change per iteration
# - Runs pytest after each change
# - If LOC decreased: KEEP
# - If LOC increased or tests fail: REVERT
# - Logs all iterations in TSV format
```

**Expected result:** 10-20% simpler code, tests still passing

---

### Step 5.4: Hunt Bugs (Autoresearch Debug)

**If bugs found during manual testing:**

```bash
/autoresearch:debug
Scope: src/api/**/*.ts, src/models.py
Symptom: "API returns 500 on POST /users"
Iterations: 15

# What it does:
# - Gathers symptoms
# - Makes hypothesis (specific, testable)
# - Runs ONE experiment per iteration
# - Confirms/disproves hypothesis
# - Logs all findings with code evidence
# - Never stops until iteration limit OR no more bugs
```

**Expected result:** All bugs found + documented

---

### Step 5.5: Fix All Errors (Autoresearch Fix)

**Before shipping:**

```bash
/autoresearch:fix
Target: pytest tests/ && ruff check src/ && mypy src/
Iterations: unlimited (stops when 0 errors)

# What it does:
# - Auto-detects what's broken (tests, lint, types)
# - Fixes ONE thing per iteration
# - Commits, verifies, keeps/reverts
# - Stops automatically when error count = 0
```

**Expected result:** Zero errors (tests, types, linting)

---

### Step 5.6: Security Audit (Autoresearch Security)

**After Phase 5.5:**

```bash
/autoresearch:security
Iterations: 10
--fix (auto-fix confirmed Critical/High findings)

# What it does:
# - STRIDE threat modeling
# - OWASP Top 10 audit
# - Red-team adversarial analysis
# - Produces structured security report
# - Auto-fixes critical issues (optional)
```

**Expected result:** Security audit report + fixes applied

---

### Step 5.7: Get Expert Review (Autoresearch Predict)

**Optional but recommended:**

```bash
/autoresearch:predict
--chain debug,fix,security

# What it does:
# - Simulates 5 experts (Architect, Security, Performance, Reliability, Devil's Advocate)
# - Each analyzes code independently
# - Debate findings
# - Reach consensus on risks/improvements
# - Takes 2 minutes
```

**Expected result:** Multi-perspective analysis + consensus recommendations

---

## 📊 Phase 5 Timeline

| Step | Time | Tool | Output |
|------|------|------|--------|
| 5.0 | 5 min | Manual | `.consultant-context.md` |
| 5.1 | 30-60 min | Codex | Working feature code |
| 5.2 | 15 min | Context7 + Claude | Issues identified |
| 5.3 | 20 min | Autoresearch | Simplified code |
| 5.4 | 15 min | Autoresearch:debug | Bugs documented |
| 5.5 | 15 min | Autoresearch:fix | Zero errors |
| 5.6 | 15 min | Autoresearch:security | Security audit |
| 5.7 | 5 min | Autoresearch:predict | Expert consensus |
| **Repeat 5.1-5.7 for each feature** | | | |

---

## ✅ Quality Checklist (After Each Feature)

- [ ] Code reviewed (Step 5.2)
- [ ] Simplified with autoresearch (Step 5.3)
- [ ] Bugs hunted & fixed (Steps 5.4-5.5)
- [ ] Security audited (Step 5.6)
- [ ] No errors (tests, types, lint)
- [ ] Tests passing (80%+ critical path)
- [ ] Expert review passed (Step 5.7)
- [ ] Committed to git

---

## 🚫 What NOT to Do in Phase 5

- ❌ Don't refactor after you write code (autoresearch does it)
- ❌ Don't write all features then test (test as you go)
- ❌ Don't skip security audit (do it every time)
- ❌ Don't ignore autoresearch findings (it's mechanical, trust it)
- ❌ Don't ship without expert review (5 min Autoresearch:predict)

---

## 🎯 Success Metrics

**Phase 5 is complete when:**
- ✅ All MVP features implemented
- ✅ Tests passing (80%+ critical paths)
- ✅ Code simplified (autoresearch confirmed)
- ✅ Zero errors (tests, types, linting)
- ✅ Security audit passed
- ✅ Expert review consensus
- ✅ Ready to ship

---

## 🔗 Related

- **SOLO_WORKFLOW.md** — Full 6-phase workflow
- **AGENT_ADAPTATION_PROMPTS.md** — Copy-paste prompts
- **TECH_DECISIONS.md** — Tech stack (needed for Context7 fetch)

---

**Result:** Feature is production-ready (clean, tested, secure, reviewed)

**Time:** 5-7 minutes per feature (after initial implementation)
