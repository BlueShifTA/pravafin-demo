# 🚀 Getting Started with Instructional Scaffolding

**Start here.** This document shows you exactly how to use this template system based on your situation.

---

## 📍 Quick Navigation: Where Are You?

Answer these questions in order:

```
1. Do you have a working product or MVP?
   YES → Go to: "Post-MVP Teams" (below)
   NO  → Go to: Question 2

2. Do you have a full engineering team (3+ people)?
   YES → Go to: "Scaling Teams" (below)
   NO  → Go to: "Startup Founders" (below)
```

---

## 🎯 Five Scenario Playbooks

Pick the one that matches your situation. Each includes **exact next steps**.

---

### Scenario 1: Startup Founder (Solo or 2-Person Team)

**Your Situation:**
- Building MVP or initial product
- 1-2 people engineering
- Moving fast, trying to find product-market fit
- Don't know what "right process" looks like

**Action Plan (Next 2 Weeks):**

1. **Day 1-2: Understand the System (2 hours)**
   - Read: `../README.md` (navigation hub by role/goal)
   - Read: `2-workflow-orchestration.md` (how you should work)
   - Takeaway: You need clarity on "what done looks like"

2. **Day 3-5: Define Your North Star (4 hours)**
   - Read: `7-product-manager.md` (discovery → prioritization)
   - **Action:** Write your answer to these 3 questions:
     - What problem are we solving? (1 paragraph)
     - Who has this problem? (1-2 customer profiles)
     - How will we know we succeeded? (2-3 measurable metrics)
   - **Output:** Save to `OUR_PRODUCT_BRIEF.md`

3. **Day 6-7: Technical Architecture (3 hours)**
   - Read: `1-systems-architect.md`
   - **Action:** Sketch your system (boxes + arrows, hand-drawn is fine)
   - Answer: "What are the 3 hardest technical problems to solve?"
   - **Output:** Save to `TECHNICAL_RISKS.md`

4. **Day 8-10: Team Clarity (3 hours)**
   - Read: `8-communication-decision-making.md`
   - **Action:** Write decision rules for your team:
     - How do we make product decisions? (RACI matrix)
     - How often do we sync? (meeting schedule)
     - How do we escalate when stuck?
   - **Output:** Save to `OUR_DECISION_RULES.md`

5. **Day 11-14: Code Quality Baseline (2 hours)**
   - Read: `5-code-review-standards.md` (especially "Lightweight Process")
   - **Action:** Set up basic code review + linting
   - **Output:** Update your `.pre-commit-config.yaml` or CI pipeline

**Deliverables after 2 weeks:**
- ✅ OUR_PRODUCT_BRIEF.md (product clarity)
- ✅ TECHNICAL_RISKS.md (architecture sketch)
- ✅ OUR_DECISION_RULES.md (how we work)
- ✅ Code review process active

**Next Phase:**
Once MVP is shipping: Jump to **Scenario 2**

---

### Scenario 2: New Hire (Engineer Joining Small Team)

**Your Situation:**
- Just joined a startup (early stage, 3-8 people)
- Want to be productive in first week
- Don't know team's processes, standards, or tech stack
- Need to understand what good looks like

**Action Plan (Your First Week):**

1. **Day 1: Onboarding Overview (1 hour)**
   - Your manager shares: OUR_PRODUCT_BRIEF.md (what we're building)
   - Your manager shares: OUR_DECISION_RULES.md (how we work)
   - **Action:** Ask 5 clarifying questions:
     - What's our biggest technical debt right now?
     - Who decides what we build next?
     - What happens if I find a bug in production?
     - How do we handle disagreements on design?
     - What's our deployment frequency? (daily? weekly?)

2. **Day 2-3: Learn Your Role (4 hours)**
   - **If Backend Engineer:** Read `3-backend-engineer.md`
   - **If Frontend Engineer:** Read `4-frontend-engineer.md`
   - **If Systems/DevOps:** Read `6-devops-deployment.md`
   - **If Product/PM:** Read `7-product-manager.md`
   - **Action:** Pair program for 2 hours with a senior engineer
   - Take notes on: "What do they do differently than the template says?"

3. **Day 4: Code Quality & Tools (2 hours)**
   - Read: `5-code-review-standards.md`
   - **Action:** Set up your dev environment:
     - Clone the repo
     - Run the linter
     - Run tests
     - Make a trivial fix (1 line) and open a PR
   - **Goal:** Get your first code review feedback

4. **Day 5: Build Small Feature (Full Day)**
   - **Action:** Implement something small but real:
     - Fix a small bug, OR
     - Build a small feature from spec, OR
     - Improve one test suite
   - **Goal:** Submit a real PR with multiple reviewers

**By End of Week:**
- ✅ Onboarded to codebase
- ✅ First PR submitted + reviewed
- ✅ Understand role + standards
- ✅ Know who to ask for what

**Ongoing:**
- Every 2 weeks: Ask manager for 1-on-1 feedback
- Weekly: Attend team decision meeting (see `8-communication-decision-making.md`)

---

### Scenario 3: Scaling Teams (3-10 People)

**Your Situation:**
- MVP is shipping, now hiring your first "real" team
- Need clearer processes, roles, and standards
- Code quality starting to decline as team grows
- Meetings are becoming chaotic

**Action Plan (This Month):**

1. **Week 1: System Audit (4 hours)**
   - Read all 9 templates (20 hours total, spread over week)
   - **Action:** Score yourself on each dimension:
     - Product Definition: 1-10 (Is everyone aligned on what to build?)
     - Technical Architecture: 1-10 (Do we have a clear system design?)
     - Code Quality: 1-10 (Are reviews catching bugs?)
     - Deployment Confidence: 1-10 (Can we ship without fear?)
     - Decision Speed: 1-10 (Can we make decisions without long meetings?)
   - **Output:** Save scores to `TEAM_AUDIT_2024.md`

2. **Week 2: Customize Master Playbook (6 hours)**
   - Use: `../README.md` + `../templates/` as your starting point
   - **Action:** Create `OUR_PLAYBOOK.md` with your team:
     - Pick your "stage" (MVP Phase / Post-MVP / Growth)
     - Which templates matter most right now?
     - Customize decision-making process (your RACI matrix)
     - Define your meeting schedule
   - **Output:** `OUR_PLAYBOOK.md` (custom version)

3. **Week 3: Role Clarity (8 hours)**
   - For each person on your team:
     - Pick their template (Backend/Frontend/Product/Architect/DevOps)
     - Create a role document: `ROLE_<name>.md`
     - Answer: "What does success look like in 90 days?"
     - Clarify: "What decision authority do they have?"
   - **Output:** Role documents for each person

4. **Week 4: Process Upgrades (6 hours)**
   - Based on your audit, pick 2-3 processes to improve:
     - **If low on Code Quality:** Set up weekly code review standups (`5-code-review-standards.md`)
     - **If low on Decision Speed:** Run a decision framework workshop (`8-communication-decision-making.md`)
     - **If low on Deployment:** Improve CI/CD + runbook (`6-devops-deployment.md`)
   - **Action:** Implement ONE process this week
   - **Output:** Updated workflows, new runbooks

**By End of Month:**
- ✅ OUR_PLAYBOOK.md (team's version of the system)
- ✅ Role documents for each person
- ✅ Team audit + score
- ✅ 1-2 process improvements implemented
- ✅ Clarity on what needs to improve next quarter

**Quarterly Cadence:**
- Each quarter: Re-run the audit, celebrate wins, pick next priorities

---

### Scenario 4: Code Quality Crisis

**Your Situation:**
- Bugs are increasing, code reviews are slow
- Tech debt is mounting, refactors are stalled
- New features take longer than they should
- Team is frustrated ("Why is code review taking 3 days?")

**Action Plan (This Week):**

1. **Tuesday: Diagnose (2 hours)**
   - Read: `5-code-review-standards.md`
   - **Action:** Answer these questions:
     - How long does a typical PR take to review? (Track 5 PRs)
     - What % of PRs need >2 rounds of feedback?
     - Are we catching bugs in review or production?
     - Do we have a linter/formatter? Is it automated?
   - **Output:** Save findings to `CODE_QUALITY_BASELINE.md`

2. **Wednesday: Quick Wins (3 hours)**
   - **Action:** Implement at least 2 of these (30-60 min each):
     - Turn on pre-commit hooks (auto-format, auto-lint)
     - Add type hints to 5 high-risk functions
     - Write 3 more test cases for flaky code
     - Create a 1-page PR template ("What should I tell reviewers?")
   - **Output:** Updated CI, PR template

3. **Thursday: Retraining (2 hours)**
   - Read: `5-code-review-standards.md` → "What Makes a Good Review?"
   - **Action:** Run a 30-min team sync on code review norms:
     - "A review should take <15 min"
     - "Focus on logic, not style (linter handles style)"
     - "Approve after addressing critical issues, not perfection"
   - **Output:** Shared rubric, posted to Slack/Wiki

4. **Friday: Measure & Iterate (1 hour)**
   - **Action:** Track metrics for next 2 weeks:
     - Average review time
     - Number of review rounds per PR
     - % of bugs caught in review vs. production
   - **Goal:** See improvement by Week 2

**By End of Month:**
- ✅ Faster reviews (<15 min response time)
- ✅ Fewer review rounds (auto-format + linter)
- ✅ More bugs caught early (better test coverage)
- ✅ Happier team (less friction)

**If still struggling:** One person may need focus on code quality: assign them `5-code-review-standards.md` as their "specialization"

---

### Scenario 5: Team Alignment Crisis ("We Can't Decide Anything")

**Your Situation:**
- Meetings are long and inconclusive
- Same decisions get re-litigated every sprint
- People feel unheard, decisions feel arbitrary
- Some people bypass process, some over-consult

**Action Plan (This Week):**

1. **Monday: Diagnose (1 hour)**
   - Read: `8-communication-decision-making.md`
   - **Action:** Run a quick survey (5 minutes, Slack poll or survey):
     - "How clear are our decision-making rules?" (1-5 scale)
     - "Do you know who decides what?" (yes/no)
     - "What decision took longest in the last month?"
   - **Output:** Collect responses

2. **Tuesday: Decision Framework Workshop (2 hours)**
   - Get your 3-5 core decision-makers in a room (remote or in-person)
   - Read together: `8-communication-decision-making.md` → "Decision-Making Framework"
   - **Action:** Build your RACI matrix:
     - List 10 decision types (product features, hiring, design, deadlines, etc.)
     - For each: Who decides? Who advises? Who's informed?
   - **Output:** Save to `OUR_RACI_MATRIX.md` + post in shared wiki

3. **Wednesday: Process Rollout (1 hour)**
   - Share `OUR_RACI_MATRIX.md` with the team
   - **Action:** Run a 15-min sync:
     - "Here's how we make decisions from now on"
     - "This means if you're in the 'Decides' role, you decide within 24h"
     - "Questions?"
   - **Output:** Team acknowledges, matrix posted everywhere

4. **Thursday-Friday: First Real Decision (2 hours)**
   - **Action:** Use the new framework on the next decision that comes up
   - Example: "What do we ship in the next sprint?"
   - Use the RACI: Who's the Decider? What's their deadline?
   - **Output:** Decision made within the process (by Friday)

**By End of Week:**
- ✅ RACI matrix defined + posted
- ✅ First decision using new process
- ✅ Team knows the rules

**Ongoing:**
- Every month: Audit one decision → "Did we follow RACI?"
- Every quarter: Refine RACI based on what works/doesn't work

---

## 📚 Quick Reference: Which Template to Read?

| Situation | Read This | Time |
|-----------|-----------|------|
| "I'm new, help me onboard" | `3-backend-engineer.md` (or your role) + `5-code-review-standards.md` | 2 hours |
| "We need faster code reviews" | `5-code-review-standards.md` | 1.5 hours |
| "What should we build next?" | `7-product-manager.md` | 2 hours |
| "How should we organize?" | `2-workflow-orchestration.md` | 1 hour |
| "Our deploys are scary" | `6-devops-deployment.md` | 2 hours |
| "Our meetings are chaotic" | `8-communication-decision-making.md` | 1.5 hours |
| "Our system is a mess" | `1-systems-architect.md` | 2 hours |
| "We can't find good people" | `../README.md` + relevant role templates | 4 hours |
| "Everything is broken" | `../reference/CHECKLIST.md` (full audit) | 8 hours |

---

## 🎓 Template Map: How They Connect

```
START HERE
    ↓
../README.md (role/goal navigation hub)
    ↓
    ├─→ Building a product?  → 7-product-manager.md
    ├─→ Designing systems?   → 1-systems-architect.md
    ├─→ Want to code?        → 3-backend-engineer.md OR 4-frontend-engineer.md
    ├─→ Need to deploy?      → 6-devops-deployment.md
    ├─→ Reviewing code?      → 5-code-review-standards.md
    ├─→ Making decisions?    → 8-communication-decision-making.md
    └─→ How to sync?         → 2-workflow-orchestration.md
```

---

## ✅ Validation Checklist: Are You Using This Right?

After you've picked your scenario, use this checklist to track progress:

**Week 1:**
- [ ] You've read the relevant scenario section
- [ ] You've identified your specific situation
- [ ] You know your next 3 actions

**Week 2-4 (depending on scenario):**
- [ ] You've completed the first "Action Plan" step
- [ ] You've documented your findings (OUR_*.md files)
- [ ] You've shared with your team
- [ ] You've gotten feedback

**Month 2+:**
- [ ] You've implemented 1-2 changes from the templates
- [ ] You can point to a specific outcome: "We review code 2x faster now"
- [ ] Your team references these docs ("Remember, this is in the playbook")
- [ ] You're customizing (not just following templates blindly)

---

## 🚀 Next Steps

1. **Pick your scenario** above
2. **Follow the action plan** for your situation
3. **Read the recommended templates** (start with one)
4. **Share with your team** — these aren't solo resources
5. **Iterate** — update your customized versions every quarter

**Questions?** Check the template you're reading for more details, or reference the cross-links.

**Want to contribute?** You'll find notes in `memory/PLAYBOOKS_INDEX.md`.

---

**Last Updated:** 2026-03-19
**Status:** Ready for adoption
**Adoption Rate Target:** 60-70% team usage within 3 months

---

## 📊 APPENDIX: Growth Stages

Identify your company's stage. This determines which templates matter most right now.

| Stage | Team Size | Timeline | Focus | Use These Templates |
|-------|-----------|----------|-------|-------------------|
| **Pre-Product** | 1 | Months 0-3 | Building MVP, finding problem-market fit | #1 (architect), #7 (product), #2 (workflow) |
| **MVP Phase** | 2-5 | Months 3-9 | Shipping features, learning from users | #1-4 (architect through design), #7 (product), #8 (decisions) |
| **Post-MVP** | 5-10 | Months 9-18 | Scaling systems, hiring team | All 8 templates (focus on #5 code quality, #6 devops) |
| **Growth** | 10-15+ | 18+ months | Hiring, process maturity, product excellence | All 8 templates + quarterly CHECKLIST |

### Stage Interpretation

**Pre-Product (1 person):**
- You are the architect, product manager, engineer, ops
- Focus on: "Can we solve the problem?" (Scenario 1 in this guide)
- Use: Systems architect thinking + product discovery

**MVP Phase (2-5 people):**
- Adding first hires (engineers, maybe product)
- Focus on: "Can we ship fast?" (Scenario 2-3 in this guide)
- Use: Clear roles + decision frameworks + code standards

**Post-MVP (5-10 people):**
- Hiring engineering team, scaling infrastructure
- Focus on: "Can we scale?" (Scenario 3 in this guide)
- Use: All 8 templates, especially #5 & #6

**Growth (10-15+ people):**
- Multiple squads, process maturity required
- Focus on: "How do we stay aligned?" (Scenario 3 + quarterly audits)
- Use: All templates + CHECKLIST for team health

---

## 🔄 Moving Between Stages

When you level up, you don't abandon old templates. You ADD new ones.

```
Pre-Product (1 person)
  → Add template #3 (backend engineer role)
  → Add template #4 (frontend engineer role)

MVP Phase (2-5 people)
  → Add template #5 (code review standards)
  → Add template #6 (devops)
  → Add template #8 (decision frameworks)

Post-MVP (5-10 people)
  → Full adoption of all 8 templates
  → Start quarterly CHECKLIST audits

Growth (10-15+ people)
  → All templates active
  → Monthly/quarterly process reviews
```

---

## 💡 Stage Detection

Unsure which stage you're in?

- **"Can we build it?"** → Pre-Product (focus: feasibility)
- **"Can we ship it?"** → MVP (focus: speed)
- **"Can we scale it?"** → Post-MVP (focus: systems)
- **"Can we keep everyone aligned?"** → Growth (focus: process)
