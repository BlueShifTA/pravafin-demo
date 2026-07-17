# Master Playbook: Building a Small Startup Team (3-15 People)

**Purpose:** Template system for structuring roles, workflows, and decision-making in fast-moving startups

**Author:** Beluga (concept) + Surapat (validation)

**Status:** Framework, ready to customize for your team

---

## What This Is

8 interconnected templates that define:
1. **Roles** — What each person does and how they think (Templates 1, 3-7)
2. **Processes** — How the team collaborates (Templates 2, 5, 8)
3. **Workflows** — Day-to-day execution (all templates)

## What This Isn't

- A rigid organizational chart (your structure may differ)
- A blueprint that works for every startup (adapt liberally)
- A substitute for hiring great people (these templates help great people be more effective)

---

## The 8 Templates at a Glance

| # | Template | Focus | Team Size | When to Use |
|---|----------|-------|-----------|------------|
| 1 | Systems Architect | Technical design spec | 1-3 engineers | Building a new product/feature |
| 2 | Workflow Orchestration | How we work | All | Day 1 onboarding |
| 3 | Backend Engineer | API/database design | 1+ | Building the backend |
| 4 | Frontend Engineer | UI/UX implementation | 1+ | Building the frontend |
| 5 | Code Review Standards | Quality gates | 2+ | Preventing bugs |
| 6 | DevOps/Deployment | Infrastructure & ops | 1+ | Shipping to production |
| 7 | Product Manager | Problem definition | 1+ | Deciding what to build |
| 8 | Communication & Decisions | Team dynamics | All | Making choices fast |

---

## Startup Growth Stages & Templates

### Stage 0: Pre-Product (You're Solo)

**Team:** 1 founder (you're doing everything)

**Use templates:**
- #1 (Systems Architect) — Design your product
- #7 (Product Manager) — Talk to customers
- #2 (Workflow Orchestration) — How you'll work with future team

**Skip:** Code review, DevOps (premature)

**Timeline:** 1-8 weeks

---

### Stage 1: MVP Phase (2-5 People)

**Team composition:**
- Founder (product + strategy)
- 1 Full-stack engineer (or 1 backend + 1 frontend if lucky)
- 1 Designer (could be founder initially)

**Use templates:**
- #1 (Systems Architect) — Design the MVP
- #2 (Workflow Orchestration) — Shared working style
- #3 (Backend Engineer) — How backend engineer works
- #4 (Frontend Engineer) — How frontend engineer works
- #7 (Product Manager) — Customer discovery
- #8 (Communication) — Lightweight decision-making

**Skip:** Code review (team is small), DevOps (premature)

**Customization:**
- Founder wears PM hat (use #7)
- Skip formal code review, do pair programming instead
- Deploy manually (no CI/CD needed yet)

**Key metrics:**
- Build velocity (features per week)
- Customer feedback (not metrics yet)
- Code quality (prevent technical debt)

**Timeline:** 8 weeks to 6 months

---

### Stage 2: Post-MVP (5-10 People)

**Team composition:**
- Founder (CEO/strategy)
- Tech Lead (architecture, mentoring)
- 2-3 Backend engineers
- 1-2 Frontend engineers
- 1 Designer
- 1 Product Manager (could still be founder)
- 1 DevOps/Infrastructure person (part-time initially)

**Use templates:**
- All 8 (implement full system)

**Customization:**
- Code review becomes formal (Template 5)
- Introduce basic CI/CD (Template 6)
- Separate PM from founder (Template 7)
- Lightweight org structure (Template 8)

**Key metrics:**
- Deployment frequency (1-2x daily)
- Code review quality (catching bugs)
- Incident response time (< 30 min)
- Team velocity (consistent sprints)

**Timeline:** 6 months to 2 years

---

### Stage 3: Scaling (10-15+ People)

**Team composition:**
- Founder (CEO)
- CTO (engineering leadership)
- Tech Leads (per domain: backend, frontend, infrastructure)
- 3-5 Backend engineers
- 2-3 Frontend engineers
- 1-2 Designers
- 1 Product Manager
- 1-2 DevOps engineers
- Sales/Marketing (not in these templates)

**Use templates:**
- All 8 (formalize everything)
- Add career progression (senior/staff engineer roles)
- Add hiring criteria (use templates to define what you're looking for)

**Customization:**
- Introduce disciplines (testing lead, security lead, etc.)
- Formalize standards (#5 becomes strict)
- Architecture review board (#1 becomes governance)
- Advanced monitoring and SLOs (#6 adds alerts)

**Key metrics:**
- Test coverage (90%+)
- Deployment success rate (99%+)
- Incident severity (0 critical per quarter)
- Time to hire & onboard (< 2 weeks fully productive)

**Timeline:** 2+ years

---

## How to Use This System

### Phase 1: Customize (Week 1)

1. **Read all 8 templates** (4-6 hours total)
   - Mark sections that fit your culture
   - Mark sections that don't (delete or modify)

2. **Create a team playbook document:**
   ```
   OUR_PLAYBOOK.md
   ├── How we work (from #2)
   ├── Code standards (from #3, #4, #5)
   ├── Deployment process (from #6)
   ├── How we make decisions (from #8)
   └── [Your customizations]
   ```

3. **Create role documents for each position:**
   ```
   roles/
   ├── backend-engineer.md (customize #3)
   ├── frontend-engineer.md (customize #4)
   ├── devops-engineer.md (customize #6)
   ├── product-manager.md (customize #7)
   └── [your roles]
   ```

### Phase 2: Onboard (Week 1-2)

When you hire your first engineer:

1. **Day 1:** Show them this system
   - "Here's how we work as a team"
   - "Here's your role's template"
   - "Here's how we make decisions"

2. **Week 1:** Pair them with a founder/tech lead
   - Do your first code review together (review #5)
   - Make a decision together (use #8 framework)
   - Discuss architecture (use #1 concepts)

3. **Week 2:** They start owning tasks
   - Use templates as reference, not micromanagement
   - They'll find parts that work, parts that don't

### Phase 3: Iterate (Ongoing)

Every month:
- [ ] Ask the team: "What's working? What isn't?"
- [ ] Update OUR_PLAYBOOK.md with learnings
- [ ] Delete templates sections that don't fit
- [ ] Add new sections for your culture

**Example evolution:**
```
Month 1: "Let's follow the code review template exactly"
Month 3: "We're doing pair programming instead, reviews are post-merge"
Month 6: "We added a design review template because we ship UI bugs"
Month 12: "We deleted the meetings section - we're all async now"
```

---

## Red Flags: When to Pivot

### Your Templates Aren't Working If...

❌ **Code review takes 3+ days per PR** (Template 5 failing)
- Fix: Async reviews, smaller PRs, clearer standards

❌ **Deployments happen once a month** (Template 6 failing)
- Fix: Add CI/CD, automate testing, build confidence

❌ **Team doesn't know how decisions get made** (Template 8 failing)
- Fix: Write down decision protocols, explain accountability

❌ **Engineers shipping features without understanding why** (Template 7 failing)
- Fix: Product manager talks to customers weekly, shares in Slack

❌ **Senior engineers disagree on code style constantly** (Template 3-5 failing)
- Fix: Automate linting, formalize conventions, resolve conflicts upfront

---

## Template Interaction Map

How the templates work together:

```
Product Manager (#7)
    ↓ defines what to build
    ↓
Systems Architect (#1)
    ↓ designs how to build it
    ↓
Backend Engineer (#3) + Frontend Engineer (#4)
    ↓ implement it
    ↓
Code Review (#5)
    ↓ ensures quality
    ↓
DevOps (#6)
    ↓ ships it
    ↓
Communication (#8)
    ↓ team aligns on decisions
    ↓
Workflow Orchestration (#2)
    ↓ enables all of the above
```

---

## Building for Scale (Avoiding Tech Debt)

These templates are designed to prevent the most common startup mistakes:

### Mistake 1: No Architecture (Template #1 prevents this)
**Problem:** Engineers build without a plan, chaos ensues
**Solution:** Systems Architect reviews every new feature before coding

### Mistake 2: Code Quality Declines (Template #5 prevents this)
**Problem:** Early hires write good code, but culture doesn't scale
**Solution:** Code review standards force consistent quality

### Mistake 3: Deployments Become Scary (Template #6 prevents this)
**Problem:** Shipping becomes a manually-step-filled process, engineers fear it
**Solution:** Automate everything, deploy daily

### Mistake 4: Wrong Features Ship (Template #7 prevents this)
**Problem:** Engineers build what seems cool, not what customers need
**Solution:** Product manager validates every feature with customers first

### Mistake 5: Team Friction (Template #8 prevents this)
**Problem:** No clear decision process, lots of arguing
**Solution:** Clear frameworks for who decides what

### Mistake 6: Unclear Expectations (Template #2 prevents this)
**Problem:** Engineer thinks "quality means 99% test coverage", you disagree
**Solution:** Shared working styles prevent surprises

---

## Metrics Dashboard

Track these to know if your system is working:

```
Weekly Metrics:
├── Code review turnaround (target: < 4 hours)
├── Deployment frequency (target: 1-2x daily)
├── Bug escape rate (target: < 1 per 100 PRs)
├── Team satisfaction (target: 7+/10)
└── Deployment failure rate (target: < 15%)

Monthly Metrics:
├── Feature ship rate (target: 8-12 features)
├── Customer churn (target: decreasing)
├── Technical debt (target: decreasing)
├── Team velocity (target: stable or increasing)
└── Incident severity (target: no critical incidents)

Quarterly Metrics:
├── Product satisfaction (NPS, target: 50+)
├── Employee retention (target: > 90%)
├── Revenue impact of features (target: measurable)
├── System uptime (target: > 99.5%)
└── Team growth (hiring velocity)
```

---

## When to Hire for Each Role

### Hire Your First Backend Engineer When:
- You have product-market fit signals (customers want it)
- You can't ship features fast enough (bottleneck is clear)
- You can articulate the technical architecture (use Template #1)

### Hire Your First Frontend Engineer When:
- You have customers (they complain about UI)
- Backend engineer is overloaded (can't maintain both)
- You have a product direction (won't pivot in 2 weeks)

### Hire Your First DevOps Engineer When:
- Deployments happen frequently (> 1x daily)
- Infrastructure is becoming complex (more than 5 services)
- Engineers are spending > 5% time on ops work

### Hire Your Product Manager When:
- You (founder) are bottleneck on decisions
- Customer feedback is hard to track (no one owns it)
- Team disagrees on priorities (no clear framework)

### Hire a Designer When:
- Users complain about UI (not engineer's job)
- Design decisions are slowing engineering (UI debates)
- You want brand consistency (colors, spacing, typography)

---

## Template Customization Examples

### Example 1: AI/ML Startup

Add template: **Machine Learning Engineer**
- Model training and evaluation
- Data pipeline design
- Experiment tracking and versioning
- Adapt #3 (Backend) for this context

### Example 2: B2B SaaS (Enterprise Focus)

Add template: **Sales Engineer**
- Pre-sales technical consultation
- Customer success technical support
- Integration work
- Adapt #7 (Product Manager) for enterprise-specific needs

### Example 3: Open Source Project

Skip templates:
- #6 (DevOps) — community deployment
- #7 (Product Manager) — community decides
- #8 (Communication) — adapt for distributed volunteers

Keep:
- #1 (Architecture) — needed more due to distributed contributors
- #2 (Workflow) — essential for coordination
- #5 (Code Review) — strict for quality

### Example 4: Game Studio

Add template: **Game Designer**
- Gameplay mechanics and balance
- Narrative and world-building
- Adapt #7 (Product Manager) for game-specific metrics

---

## Success Stories

### Hypothetical Example: Linear (Code Collaboration)

**Stage 1 (2 people):**
- Used #1 (Architecture) to design issuing system
- Used #7 (Product) for customer interviews
- Used #2 (Workflow) to stay aligned

**Stage 2 (5 people):**
- Added #3 (Backend), #4 (Frontend), #6 (DevOps) roles
- Used #5 (Code Review) to maintain quality
- Used #8 (Communication) for fast decisions

**Stage 3 (15 people):**
- Formalized all roles
- Added sub-disciplines (security, performance)
- Used templates as hiring criteria

**Result:** Linear ships reliably, high team retention, customers love it

---

## Anti-Patterns

❌ **Treat templates as law**
- "The system says we need X, so we need X"
- ✅ Use as guidance, adapt to your team

❌ **Never revisit them**
- "We chose these templates in month 1; they're set"
- ✅ Revisit quarterly, evolve with team

❌ **Hire for templates, not talent**
- "We need a DevOps engineer for template #6"
- ✅ Hire great people, assign roles based on needs

❌ **Template before team**
- "Let's perfect the system before hiring"
- ✅ Ship with 80% of the system, iterate with team

---

## Final Thoughts

These 8 templates are a starting point. They encode lessons from:
- Production engineering (reliability, scaling)
- Clean code principles (readability, maintainability)
- Startup best practices (speed, iteration)
- Psychology research (communication, decision-making)

**Your job:** Take what works, discard what doesn't, add what's unique to you.

The best team isn't the one with perfect processes. It's the one where everyone understands:
- What we're building (clarity)
- Why we're building it (purpose)
- How we work together (trust)
- How we decide (speed)

These templates help with all four.

---

## Quick Reference: Template Selection

```
Starting a feature?
├── Use Template #1 (Systems Architect)
├── Use Template #7 (Product Manager)
└── Then #3 or #4 (Backend/Frontend Engineer)

Shipping code?
├── Use Template #5 (Code Review)
└── Use Template #6 (DevOps)

Making a decision?
├── Use Template #8 (Communication & Decisions)

Onboarding someone new?
├── Show them Template #2 (Workflow)
├── Show them their role template (#3-7)
└── Reference Template #8 (how we decide)

Team feels broken?
├── Use Template #8 first (usually a communication issue)
├── Then #2 (how we work)
└── Then specific role template if targeted issue
```

---

**Version:** 1.0
**Last Updated:** 2026-02-25
**Next Review:** 2026-05-25 (quarterly)
