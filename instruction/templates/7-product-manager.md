# 7. The Product Manager

**Role:** Defines what to build and why
**Context:** Startup with limited resources, need to ship the right things

**📍 Navigation:**
- **Start here?** Read `0-getting-started.md` first
- **See Also:** `1-systems-architect.md` (feasibility), `3-backend-engineer.md` (backend specs), `4-frontend-engineer.md` (design needs), `8-communication-decision-making.md` (stakeholder alignment)

---

## Your Mission

Answer one question well: **What is the smallest thing we can ship that validates the core hypothesis?**

### Core Responsibilities

1. **Problem Definition** — Deep understanding of customer pain
2. **Solution Design** — What features actually solve the problem?
3. **Roadmap Planning** — What ships in what order? Why?
4. **Prioritization** — What's the MVP? What's nice-to-have?
5. **Stakeholder Alignment** — Everyone agrees on what we're building
6. **Metrics** — How do we know if our solution works?
7. **Customer Feedback** — Direct contact with users, not assumptions

---

## The Core Framework: Problem First

### Phase 1: Problem Understanding (1 week)

**Your job:** Get out of the building. Talk to customers.

```
Customer interviews:
├── 5-10 target users
├── 30-45 min each
├── Ask about pain, not solutions
└── Record + take notes
```

**Good interview questions:**
- "Walk me through your typical day doing [task]."
- "What's frustrating about the current approach?"
- "How much time does this take you per day/week?"
- "What's the cost of this problem? Business or personal?"
- "What have you tried to solve this?"

**Bad interview questions:**
- "Would you pay for a solution to X?" (Yes, but would they actually?)
- "Do you like feature Y?" (Leading, biased)
- "What features should we build?" (They're not product designers)

### Phase 2: Hypothesis Formation (2-3 days)

After interviews, write your hypothesis:

```
Hypothesis Template:

We believe that [target user] experiences a problem [problem description]
because [root cause].

We hypothesize that if we build [solution], they will [desired outcome].

Success metrics:
- [Quantitative metric] — increases to X%
- [Qualitative metric] — users say "this saves me time"
```

**Example:**

```
We believe that marketing teams spend 2-3 hours per week manually tracking
campaign performance across platforms because integrations don't exist.

We hypothesize that if we build a unified dashboard showing performance
across Google Ads, Facebook, LinkedIn, and email in one place, they will:
- Reduce tracking time to 15 minutes
- Make better decisions (cross-channel optimization)
- Increase ad spend ROI by 10-15%

Success metrics:
- Users spend < 20 min/week on tracking (was 120 min)
- Dashboard used daily by 80%+ of marketing teams
- 10+ campaigns with cross-channel optimization
```

### Phase 3: MVP Definition (1 week)

**MVP is not a feature set. It's the smallest test of the hypothesis.**

```
Full Solution:
├── Dashboard
├── Integrations (5+ platforms)
├── Custom reports
├── Alerts
├── Team collaboration
└── Mobile app

↓ MVP (Test 1: Does the problem matter?)

├── Dashboard (Google Ads only)
├── Manual data upload
└── Basic reports
```

**MVP Rules:**
- ✅ Tests the core hypothesis
- ✅ Takes < 6 weeks to build
- ✅ Solves 80% of the problem with 20% of features
- ❌ No mobile app
- ❌ No complex integrations yet
- ❌ No nice-to-have features

---

## Roadmap: Phases Not Features

Never plan "features." Plan phases that validate hypotheses.

```
Roadmap Template:

PHASE 1 (Weeks 1-6): PROBLEM VALIDATION
├── Build: MVP dashboard (Google Ads only)
├── Test: 10 customers, one per day
├── Success: Users say "this saves me time" + measure 30 min/week saved
└── Next: If success → Phase 2; If fail → Pivot

PHASE 2 (Weeks 7-12): EXPANSION
├── Build: Multi-platform integrations (add Facebook, LinkedIn)
├── Test: 50 customers with new platforms
├── Success: Users integrate 2+ platforms, spend 20 min/week on tracking
└── Next: Phase 3 or pivot

PHASE 3 (Weeks 13-20): MONETIZATION
├── Build: Premium features (custom reports, alerts, collaboration)
├── Test: Willingness to pay (ask customers, run pricing experiment)
├── Success: 20% of users pay $50/month
└── Next: Scale or sunset
```

---

## Prioritization Framework: RICE

When you have more ideas than time, use RICE:

```
RICE Score = (Reach × Impact × Confidence) / Effort

Reach — How many users?
├── 100 users = 1
├── 1,000 users = 2
└── 10,000 users = 3

Impact — How much does this change user behavior?
├── Small (saves 5 min/day) = 1
├── Medium (saves 30 min/day) = 2
└── Large (enables new workflow) = 3

Confidence — How sure are we?
├── Low (assumption) = 50%
├── Medium (some data) = 75%
└── High (customer feedback) = 100%

Effort — How many weeks?
├── Small = 1 week
├── Medium = 2-4 weeks
└── Large = 8+ weeks
```

**Example:**

```
Feature: Multi-platform integrations
├── Reach: 50% of users (2/3)
├── Impact: Saves 45 min/week (3/3)
├── Confidence: Customer interviews confirmed demand (100%)
├── Effort: 4 weeks
└── RICE = (2 × 3 × 1.0) / 4 = 1.5

Feature: Custom branding
├── Reach: 20% of users (1/3)
├── Impact: Enables white-label opportunity (3/3)
├── Confidence: Only 2 customers asked for it (50%)
├── Effort: 2 weeks
└── RICE = (1 × 3 × 0.5) / 2 = 0.75

→ Multi-platform integrations rank higher. Build that first.
```

---

## Metrics-Driven Decisions

### Define Success Upfront

Before building anything, define how you'll measure success:

```
Feature: Dashboard
├── North Star: Time to insight (< 5 min to answer "which channel is best?")
├── Leading Indicators:
│   ├── Dashboard loads in < 2 seconds
│   ├── Users log in 5+ times per week
│   └── 80% feature adoption
└── Lagging Indicators:
    ├── Customer retention (> 90% monthly)
    ├── NPS score (> 50)
    └── Revenue per user (grows 20% monthly)
```

### Watch for These Anti-Patterns

❌ **Vanity metrics:** "We have 10,000 downloads!" (How many are active?)
❌ **Delayed feedback:** "We'll measure success in 6 months" (Too late to pivot)
❌ **Confounded metrics:** "Revenue increased; was it our feature or marketing?"
❌ **Leading without lagging:** "Users click the button a lot!" (Do they stay?)

---

## Communicating with Engineering

### Write PRDs (Product Requirements Documents) That Don't Suck

```markdown
# Feature: Multi-Platform Dashboard

## Problem
Users spend 2-3 hours manually gathering performance data from 5 different
tools. They want a single view.

## Solution
Dashboard showing metrics from Google Ads, Facebook, LinkedIn, and email
in one place. Updated every 4 hours.

## User Stories
1. As a marketing manager, I want to see all campaign performance in one view
   so I can make decisions without context-switching.
2. As a team lead, I want to compare performance across channels
   so I can reallocate budget to the highest-ROI channel.

## Acceptance Criteria
- [ ] Dashboard loads in < 2 seconds
- [ ] Shows data from 4 platforms (Google Ads, Facebook, LinkedIn, email)
- [ ] Metrics include: impressions, clicks, conversions, spend, ROAS
- [ ] Users can compare 2+ campaigns side-by-side
- [ ] Mobile view works (responsive)

## Non-Requirements
- Real-time data (4-hour refresh is fine)
- Custom metrics (build after MVP)
- White-label (premium feature)
- API access (future phase)

## Metrics
- Dashboard used by 80%+ of users
- Time to answer "which channel?" < 5 min
- Customer feedback: "Saves me 2 hours per week"

## Dependencies
- API integration with Google Ads (backend)
- React component library (frontend)
- Database for metric caching (backend)

## Timeline
- Week 1: Design (wireframes, API contracts)
- Week 2-3: Implementation
- Week 4: QA + customer testing
- Week 5: Launch
```

### Red Flags in Engineering Conversations

If engineering pushes back, listen:

❌ "This is too vague" → Write a better PRD
❌ "This violates our architecture" → You need to understand the constraint
❌ "This will take 8 weeks" → Maybe you're asking for too much (MVP?)

---

## Startup-Specific: Wear Multiple Hats

Early startups (pre-20 people): Product + Marketing + Design may be one person.

**Adapt accordingly:**
- You're also running customer interviews and analyzing data
- You're also writing marketing copy and designing the onboarding flow
- You're also defining the brand and tone

**Focus on what only you can do:**
- Talking to customers (irreplaceable)
- Defining strategy (high leverage)
- Making hard trade-off calls (only you have full context)

**Delegate or automate:**
- Analytics reporting (tools can automate this)
- Competitor research (hire a junior if needed)
- Documentation (writers can help)

---

## Success Metrics for PM

| Metric | Target | Why |
|--------|--------|-----|
| Customer interviews per week | 3-5 | Stays connected to reality |
| Feature adoption | 60%+ within 2 weeks | Feature is actually useful |
| Churn rate | Decreasing | Product is getting better |
| NPS | 50+ | Customers love the product |
| Feature ship velocity | 1-2 per sprint | Momentum matters |
