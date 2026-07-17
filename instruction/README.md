# Instructional Documentation

Reusable workflow templates, role-based guidance, and decision frameworks for building software teams.

For coding rules enforced in this repo, see the root [CLAUDE.md](../CLAUDE.md).

---

## Quick Start

| Goal | File | Time |
|------|------|------|
| Role clarity | `templates/[role].md` | 15 min |
| Code examples | `profiles/coding-profiles/[role].md` | 20 min |
| Team workflow | `guides/SOLO_WORKFLOW.md` | 30 min |
| Quick audit | `reference/CHECKLIST.md` | 10 min |
| Example profile *(replace with yours)* | `profiles/surapat/PROFILE.md` | 20 min |
| Decision rules example *(replace with yours)* | `profiles/surapat/DECISIONS.md` | 15 min |
| Team scenarios | `guides/0-getting-started.md` | 45 min |

---

## By Role

### Individual Contributors

| Role | Template | Coding Profile |
|------|----------|----------------|
| Backend Engineer | `templates/3-backend-engineer.md` | `profiles/coding-profiles/data-engineer.md` |
| Frontend Engineer | `templates/4-frontend-engineer.md` | `profiles/coding-profiles/frontend-engineer.md` |
| Frontend (Next.js) | `templates/4-frontend-engineer.md` | `profiles/coding-profiles/frontend-nextjs.md` |
| Systems Engineer | `templates/2-workflow-orchestration.md` | `profiles/coding-profiles/systems-engineer.md` |
| DevOps / Reliability | `templates/6-devops-deployment.md` | `profiles/coding-profiles/reliability-engineer.md` |

### Leadership

| Role | Primary File | Secondary |
|------|-------------|-----------|
| Systems Architect | `templates/1-systems-architect.md` | `profiles/surapat/DECISIONS.md` *(example — replace)* |
| Engineering Manager | `templates/8-communication-decision-making.md` | `guides/0-getting-started.md` |
| Product Manager | `templates/7-product-manager.md` | `guides/WORK_CYCLE.md` |
| Tech Lead | `templates/5-code-review-standards.md` | `profiles/surapat/PROFILE.md` *(example — replace)* |

---

## By Goal

### Starting a Project

- **Solo (1-2 people):** `guides/0-getting-started.md` (Scenario 1) + `guides/SOLO_WORKFLOW.md`
- **Small team (3-5):** `guides/0-getting-started.md` (Scenario 2) + pick 3-4 role `templates/`
- **Scaling (5-10):** `guides/0-getting-started.md` (Scenario 3) + all `templates/` + `reference/CHECKLIST.md`

### Fixing a Problem

| Problem | File | Time |
|---------|------|------|
| Slow code reviews | `templates/5-code-review-standards.md` | 2 hours |
| Team not aligned | `templates/8-communication-decision-making.md` | 1 week |
| Code quality issues | `guides/PHASE_5_AUTO_QUALITY.md` | 2 days |
| Security gaps | `reference/SECURITY_PATTERNS.md` | 4 hours |
| Bad architecture decisions | `profiles/[your-name]/DECISIONS.md` + `reference/AGENTIC_AI_ARCHITECTURES.md` | 3 days |

---

## By Topic

- **Architecture & Design:** `templates/1-systems-architect.md`, `profiles/[your-name]/DECISIONS.md`, `reference/AGENTIC_AI_ARCHITECTURES.md`
- **Security:** `reference/SECURITY_PATTERNS.md`, `profiles/coding-profiles/systems-engineer.md`, `profiles/coding-profiles/reliability-engineer.md`
- **Code Quality:** `templates/5-code-review-standards.md`, `guides/PHASE_5_AUTO_QUALITY.md`, `reference/PYTHON_STYLE.md`
- **Team Management:** `templates/8-communication-decision-making.md`, `guides/WORK_CYCLE.md`, `reference/CHECKLIST.md`
- **Deployment & Operations:** `templates/6-devops-deployment.md`, `profiles/coding-profiles/reliability-engineer.md`
- **AI Agent Operations:** `reference/AGENT_OPERATING_RULES.md`, `reference/AGENTIC_AI_ARCHITECTURES.md`
- **Retrospectives:** `reference/LESSONS_LEARNED_TEMPLATE.md`

---

## By Audience

- **Solo founders (2 hours):** `guides/0-getting-started.md` (Scenario 1) -> `guides/SOLO_WORKFLOW.md` -> `guides/PROJECT_QUICKSTART.md`
- **Engineering managers (4 hours):** `guides/0-getting-started.md` (Scenario 3) -> all `templates/` -> `reference/CHECKLIST.md` monthly
- **New team members (1 week):** `guides/0-getting-started.md` (Scenario 2) -> your role template -> your coding profile
- **Architects (8 hours):** `templates/1-systems-architect.md` -> `profiles/[your-name]/DECISIONS.md` -> `reference/AGENTIC_AI_ARCHITECTURES.md`
- **Code reviewers (3 hours):** `templates/5-code-review-standards.md` -> all `profiles/coding-profiles/` -> `reference/PYTHON_STYLE.md`

---

## Search by Keyword

| Keyword | Files |
|---------|-------|
| Agentic AI / Frameworks | `reference/AGENTIC_AI_ARCHITECTURES.md` |
| API design | `templates/3-backend-engineer.md`, `profiles/coding-profiles/data-engineer.md` |
| Code review | `templates/5-code-review-standards.md`, `reference/PYTHON_STYLE.md` |
| Security | `reference/SECURITY_PATTERNS.md`, `profiles/coding-profiles/systems-engineer.md` |
| CI/CD | `templates/6-devops-deployment.md`, `guides/PHASE_5_AUTO_QUALITY.md` |
| Database | `profiles/coding-profiles/data-engineer.md`, `profiles/[your-name]/DECISIONS.md` |
| Frontend | `templates/4-frontend-engineer.md`, `profiles/coding-profiles/frontend-engineer.md` |
| Scaling | `guides/0-getting-started.md`, `templates/1-systems-architect.md` |
| Testing | `templates/4-frontend-engineer.md`, `guides/PHASE_5_AUTO_QUALITY.md` |
| Agent operations | `reference/AGENT_OPERATING_RULES.md` |
| Lessons learned | `reference/LESSONS_LEARNED_TEMPLATE.md` |
| Dev cycle | `.claude/skills/dev-cycle/SKILL.md` |
| Code review (automated) | `.claude/skills/brutal-critic/SKILL.md` |
| Research | `.claude/skills/research/SKILL.md`, `.claude/skills/autoresearch/SKILL.md` |
| Screenshots | `.claude/skills/screenshot/SKILL.md` |

---

## Claude Code Skills

Skills are invocable automation commands available via `/skill-name` in Claude Code.

| Skill | Purpose | Trigger |
|-------|---------|---------|
| `/verify` | Run tests + lint + typecheck | After code changes |
| `/format-code` | Auto-format Python + TypeScript | When style issues found |
| `/dev-cycle` | Full audit → fix → test → critic workflow | "run a dev cycle" |
| `/brutal-critic` | Brutally honest code/UX/arch review | "critique this", "review" |
| `/autoresearch` | Autonomous goal-directed iteration (bounded) | Explicit request only |
| `/research` | Deep knowledge base research | "research [topic]" |
| `/simplify` | Code reuse/quality/efficiency review + fix | "simplify", "clean up" |
| `/screenshot` | Playwright desktop + mobile captures | "take screenshots" |
| `/seed-data` | Populate database with realistic test data | "seed data" |
| `/ci` | Run full CI pipeline locally | Before PR, after feature |
| `/install-deps` | Install project dependencies | Setup, after pull |
| `/run-dev` | Start dev servers | Starting development |
| `/generate-types` | Generate frontend API types from backend | After API changes |

Skill definitions: `.claude/skills/[name]/SKILL.md`

---

## Directory Structure

```
instruction/
├── profiles/
│   ├── surapat/                   # Example personal profile — replace/delete after bootstrap
│   │   ├── PROFILE.md             # Coding style, tools, patterns
│   │   ├── DECISIONS.md           # Tech decision rules
│   │   └── WORKFLOWS.md           # Workflow + process
│   └── coding-profiles/           # Generic engineer profiles
│       ├── data-engineer.md
│       ├── frontend-engineer.md
│       ├── frontend-nextjs.md
│       ├── fullstack-architect.md
│       ├── reliability-engineer.md
│       └── systems-engineer.md
├── templates/                     # Role-based guidance
│   ├── 1-systems-architect.md
│   ├── 2-workflow-orchestration.md
│   ├── 3-backend-engineer.md
│   ├── 4-frontend-engineer.md
│   ├── 5-code-review-standards.md
│   ├── 6-devops-deployment.md
│   ├── 7-product-manager.md
│   └── 8-communication-decision-making.md
├── guides/                        # Workflow playbooks
│   ├── 0-getting-started.md       # 5 entry scenarios
│   ├── SOLO_WORKFLOW.md
│   ├── WORK_CYCLE.md
│   ├── PHASE_5_AUTO_QUALITY.md
│   └── PROJECT_QUICKSTART.md
└── reference/                     # Checklists & standards
    ├── CODING_PRINCIPLES.md
    ├── PYTHON_STYLE.md
    ├── SOLID_PRINCIPLES.md
    ├── FASTAPI_PATTERNS.md
    ├── REFACTOR_AND_TESTING.md
    ├── SECURITY_PATTERNS.md
    ├── AGENT_ROUTING.md
    ├── AGENT_OPERATING_RULES.md
    ├── AGENTIC_AI_ARCHITECTURES.md
    ├── PATTERNS.md
    ├── CHECKLIST.md
    ├── AUDIT_TEMPLATE.md
    └── LESSONS_LEARNED_TEMPLATE.md
```

---

## Contributing

To add your personal profile:
1. Create `profiles/[your-name]/` directory
2. Add `PROFILE.md` (coding style), `DECISIONS.md` (tech decisions), `WORKFLOWS.md` (process)
3. Keep `templates/` generic for team-wide use
