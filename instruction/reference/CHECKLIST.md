# ✅ Team Playbook Checklist

Use this checklist to audit whether your team is following the instructional scaffolding system.

**How to use:**
1. Run quarterly (every 3 months)
2. Score each section 1-5 (1 = not at all, 5 = fully implemented)
3. Identify lowest-scoring areas
4. Pick ONE area to improve next quarter
5. Celebrate wins

---

## 📝 Product Definition

**Goal:** Everyone knows what you're building and why.

- [ ] **Product Brief Exists** — Team has written document answering:
  - [ ] What problem are we solving?
  - [ ] Who has this problem?
  - [ ] How do we know we succeeded? (metrics)
  - [ ] What's our timeline?

- [ ] **Metrics Are Clear** — Team references 3-5 metrics when making decisions

- [ ] **Roadmap Alignment** — Next 3 features are documented + prioritized

- [ ] **Success Visible** — Team can point to: "We shipped X, it helped Z metric"

**Score: __/5**

**If <3:** Read `7-product-manager.md`
**Action:** Write your product brief (2 hours) and share with team

---

## 🏗️ Technical Architecture

**Goal:** Team can explain the system design. No surprises.

- [ ] **System Diagram Exists** — Can sketch boxes + connections in 5 min

- [ ] **Data Model Documented** — Database schema + major tables are clear

- [ ] **API Contracts Clear** — Endpoints documented (what goes in, what comes out)

- [ ] **Error Handling Defined** — Team knows: "If X breaks, Y happens"

- [ ] **Scaling Plan Known** — Team discusses: "What breaks if we 10x users?"

**Score: __/5**

**If <3:** Read `1-systems-architect.md`
**Action:** Spend 1 hour sketching your system (diagram + schema)

---

## 💻 Code Quality

**Goal:** Code reviews catch bugs. Tests prevent regressions.

- [ ] **Linting Automated** — Pre-commit hooks or CI catches style issues

- [ ] **Tests Running** — CI fails if tests don't pass (80%+ coverage)

- [ ] **Reviews Happen** — All code goes through review before merging

- [ ] **Review Feedback is Quick** — Average review time <15 min response

- [ ] **Standard Enforced** — Team uses same patterns (no wild inconsistency)

**Score: __/5**

**If <3:** Read `5-code-review-standards.md`
**Action:** Set up pre-commit hooks or tighten review standards (3 hours)

---

## 🔒 Security Baseline

**Goal:** No basic security gaps before any external demo or deployment.

**Reference:** `reference/SECURITY_PATTERNS.md` for patterns and code examples.

### Network Security
- [ ] **Bind address** — Server defaults to `127.0.0.1`, not `0.0.0.0`
- [ ] **CORS wildcard blocked** — `RuntimeError` at startup if `"*"` in origins
- [ ] **Request size limit** — `RequestSizeLimitMiddleware` rejects bodies >1 MB
- [ ] **Request ID middleware** — UUID on every request for log correlation

### Input Validation
- [ ] **Pydantic constraints** — `max_length`, `ge`, `le` on all free-text and numeric fields
- [ ] **Prompt injection guard** — regex on any field interpolated into LLM prompts
- [ ] **SQL identifier validation** — regex on identifiers before SQL interpolation
- [ ] **Array/list length caps** — `model_validator` limits on history and list fields

### Data Safety
- [ ] **SQL read-only guard** — DDL/DML keywords rejected before execution
- [ ] **JSON over pickle** — no `pickle` for cached data that crosses process boundary
- [ ] **DB context managers** — `with sqlite3.connect(...)` everywhere, no resource leaks

### Thread Safety
- [ ] **Bounded thread pool** — `max_workers` set, one executor created at startup
- [ ] **RLock on shared connections** — all shared DB/hardware connections wrapped
- [ ] **Fresh state per request** — singleton orchestrators hold no per-request mutable state

### Error Handling
- [ ] **No internal details in responses** — generic client messages, full detail in server logs
- [ ] **Global exception handler** — catches unhandled exceptions, returns `{"detail": "..."}`
- [ ] **No PII in logs** — names, diagnoses, credentials never appear in log messages

### Agent Safety (if using AI agents)
- [ ] **Agents never read `.env`** — agent prompts explicitly prohibit reading `.env` files
- [ ] **"Do NOT plan" directive** — file-creation prompts include explicit write instruction
- [ ] **LLM timeout cap** — max 120s HTTP timeout on all LLM backend calls

**Score: __/5**

**If <3:** Read `reference/SECURITY_PATTERNS.md`
**Action:** Address network + error handling sections first (highest blast radius). See `reference/SECURITY_PATTERNS.md` for code examples.

---

## 🚀 Deployment Confidence

**Goal:** Shipping doesn't cause fear or chaos.

- [ ] **CI/CD Pipeline Works** — Green deploy = feature in production

- [ ] **Monitoring Exists** — Team gets alerted if something breaks

- [ ] **Rollback Possible** — Can undo bad deploy in <5 min

- [ ] **Logs Available** — Can debug production issues quickly

- [ ] **Deploy Frequency Known** — Team ships at least 1x per week

**Score: __/5**

**If <3:** Read `6-devops-deployment.md`
**Action:** Set up basic monitoring (Sentry + logs) + rollback plan (2 hours)

---

## 🎯 Decision-Making

**Goal:** Decisions are made fast, not revisited every sprint.

- [ ] **RACI Matrix Exists** — Team knows who decides what

- [ ] **Decision Timeline Clear** — "Product decision takes 1 day, not 1 week"

- [ ] **Same Decision Not Revisited** — Once decided, team trusts the call

- [ ] **Escalation Path Known** — "If we disagree, here's who breaks tie"

- [ ] **Data-Driven** — Decisions reference metrics/data, not opinions

**Score: __/5**

**If <3:** Read `8-communication-decision-making.md`
**Action:** Create RACI matrix + post it (1 hour)

---

## 👥 Workflow & Sync

**Goal:** Team knows how to work together. Meetings are efficient.

- [ ] **Meeting Schedule Set** — Team knows: daily standup? Weekly planning?

- [ ] **Async Communication Works** — Not everything requires live meeting

- [ ] **Handoffs Clear** — When one person hands off to another, no confusion

- [ ] **Priorities Visible** — Everyone knows what's next (shared board)

- [ ] **Blockers Surface Fast** — Stuck person gets unblocked within 24h

**Score: __/5**

**If <3:** Read `2-workflow-orchestration.md`
**Action:** Write team meeting schedule + async norms (1 hour)

---

## 📚 Knowledge Sharing

**Goal:** New hires onboard in 1 week, not 1 month.

- [ ] **Onboarding Doc Exists** — New hire has checklist for week 1

- [ ] **Codebase Documented** — "How do I run this locally?" is answerable

- [ ] **Decision History Captured** — "Why did we build it this way?" is documented

- [ ] **Patterns Taught** — Senior engineers show juniors the "right way"

- [ ] **Role Clarity** — Each person knows their job, success metrics, who to ask

**Score: __/5**

**If <3:** Create onboarding doc + role clarification (4 hours)

---

## 🔧 Tool Consistency

**Goal:** Everyone uses the same tools, same way.

- [ ] **Version Control** — Team uses same branching strategy (main/develop/feature)

- [ ] **Issue Tracking** — All work captured in same system (GitHub/Linear/Jira)

- [ ] **Communication** — All async comms in same place (Slack/Discord)

- [ ] **Code Review Tool** — All code reviews in GitHub/GitLab (not email)

- [ ] **Deployment Tool** — All deploys go through same CI/CD (not SSH to server)

**Score: __/5**

**If <3:** Standardize tools + post norms (2 hours)

---

## 🎓 Learning & Growth

**Goal:** Team is getting better. No one stays the same for 6 months.

- [ ] **Feedback Happens** — People get 1-on-1 feedback at least monthly

- [ ] **Growth Plans Exist** — Person + manager have agreed goals for quarter

- [ ] **Learning Time Allocated** — Team spends 5-10% of time learning (not 0%)

- [ ] **Mistakes Blameless** — Failed experiment = learning, not punishment

- [ ] **Junior Mentorship** — Experienced people actively teach newer people

**Score: __/5**

**If <3:** Schedule 1-on-1s + create growth plan template

---

## 📊 Overall Score

| Section | Score | Status |
|---------|-------|--------|
| Product Definition | __/5 | 🟢 🟡 🔴 |
| Technical Architecture | __/5 | 🟢 🟡 🔴 |
| Code Quality | __/5 | 🟢 🟡 🔴 |
| Security Baseline | __/5 | 🟢 🟡 🔴 |
| Deployment Confidence | __/5 | 🟢 🟡 🔴 |
| Decision-Making | __/5 | 🟢 🟡 🔴 |
| Workflow & Sync | __/5 | 🟢 🟡 🔴 |
| Knowledge Sharing | __/5 | 🟢 🟡 🔴 |
| Tool Consistency | __/5 | 🟢 🟡 🔴 |
| Learning & Growth | __/5 | 🟢 🟡 🔴 |

**Average Score: __/5**

---

## 🎯 Interpretation

**4.5-5.0:** 🟢 Excellent — You're following the system well. Maintain.

**3.5-4.4:** 🟢 Good — Team is solid. Pick 1-2 areas to improve next quarter.

**2.5-3.4:** 🟡 Fair — Multiple gaps. Address top 3 scoring sections.

**1.5-2.4:** 🟡 Risky — Chaos is likely. Implement governance from `../README.md` + core role templates immediately.

**<1.5:** 🔴 Critical — Team needs foundation work. Start with Scenario 1 or 5 in `0-getting-started.md`.

---

## 🔄 Quarterly Improvement Cycle

1. **Run this checklist** (30 min)
2. **Identify lowest scores** (5 min)
3. **Pick #1 priority** for next quarter (5 min)
4. **Read related template** (2-4 hours)
5. **Implement 1 change** from that template (3-5 hours)
6. **Re-score next quarter** and celebrate the improvement

---

## 📋 Sample Improvement Plan

**Example: Code Quality is 2/5**

1. Read: `5-code-review-standards.md` (1.5 hours)
2. Identify issue: "Reviews take 2-3 days, too slow"
3. Action: Set up pre-commit hooks, auto-linter
4. Measure: Track review time next sprint
5. Goal: Reduce to <15 min average by end of quarter
6. Re-score: Should be 3.5-4/5 next checklist

---

## ✏️ Blank Template for Copying

Use this format to run your own audit:

```markdown
# Team Audit — Q2 2024

Date: March 19, 2024
Facilitator: [Name]

| Category | Score | Notes |
|----------|-------|-------|
| Product Definition | 4/5 | Brief exists, metrics clear |
| Technical Architecture | 3/5 | Diagram exists, needs more docs |
| Code Quality | 2/5 | Reviews too slow, no CI |
| Deployment Confidence | 3/5 | Monitoring basic, rollback risky |
| Decision-Making | 4/5 | RACI clear, decisions stick |
| Workflow & Sync | 3/5 | Standup works, planning vague |
| Knowledge Sharing | 2/5 | No onboarding doc, new hire lost |
| Tool Consistency | 4/5 | All using GitHub, Slack |
| Learning & Growth | 2/5 | No 1-on-1s, no growth plans |

Average: 3.1/5

Next Priority: Code Quality (set up CI/linting) + Knowledge Sharing (create onboarding)
Deadline: End of Q2
Owner: [Name]
```

---

**Last Updated:** 2026-03-19
**Review Cycle:** Quarterly (every 3 months)
**Expected Impact:** Team score improves 0.5-1.0 points per quarter with focused work
