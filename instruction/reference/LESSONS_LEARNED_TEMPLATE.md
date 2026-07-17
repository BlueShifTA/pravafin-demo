# Lessons Learned Template

Reusable project retrospective template. Fill in each section after a project milestone, sprint, or completion. Remove guidance text (in italics) once filled.

---

## 1. Project Summary

| Field | Value |
|-------|-------|
| Project name | |
| Timeline | _Start date — End date_ |
| Team size | _Number of contributors (human + AI agents)_ |
| Outcome | _Shipped / Cancelled / Pivoted / On hold_ |
| Key metric 1 | _e.g., lines of code, endpoints, pages_ |
| Key metric 2 | _e.g., test count, coverage %_ |
| Key metric 3 | _e.g., build time, deploy frequency_ |

**One-sentence summary:** _What was built, for whom, and what was the result?_

---

## 2. Architecture Decisions

### What Worked (Keep Doing)

| Decision | Why It Worked | Evidence |
|----------|--------------|----------|
| _e.g., Protocol-based interfaces_ | _Decoupled components, easy to test_ | _Zero breaking changes during refactor_ |
| _e.g., Monorepo with shared types_ | _Single source of truth for API contracts_ | _Type errors caught at compile time_ |
| | | |

### What We'd Change (Stop or Adjust)

| Decision | Why It Failed | Better Alternative |
|----------|--------------|-------------------|
| _e.g., SQLite for multi-user app_ | _Write contention under concurrent load_ | _PostgreSQL from day 1_ |
| _e.g., God-class orchestrator_ | _800+ lines, untestable_ | _Extract into focused service classes_ |
| | | |

---

## 3. Security Patterns Applied

Check each pattern that was implemented. Add notes on gaps or issues found.

- [ ] **Input validation** — All user inputs validated at API boundary (type, length, format)
- [ ] **Network security** — Loopback bind by default, CORS restricted to explicit origins, no wildcard
- [ ] **Thread safety** — No shared mutable state, bounded thread pools, context managers for resources
- [ ] **Streaming safety** — Chunked responses have size limits, timeouts on long-running streams
- [ ] **Data safety** — No secrets in logs, no PII in error responses, env files excluded from VCS
- [ ] **Error handling** — No blind except, specific exceptions caught, errors logged with context
- [ ] **LLM/AI safety** _(if applicable)_ — Prompt injection mitigation, output sanitization, rate limiting
- [ ] **Authentication** — Token validation, session management, privilege escalation prevention
- [ ] **Request limits** — Body size caps, rate limiting, timeout enforcement

**Security gaps found:** _List any vulnerabilities discovered and how they were resolved._

---

## 4. Frontend Patterns

### Component Architecture

_Describe the component hierarchy, shared vs. page-specific components, and any patterns used (compound components, render props, HOCs)._

### Theming & Styling

_Theme system used, dark mode support, design tokens, CSS approach (CSS-in-JS, Tailwind, modules)._

### State Management

_Client state approach (React Query, Zustand, Context), server state caching strategy, optimistic updates._

### Performance

- [ ] Code splitting / lazy loading
- [ ] Image optimization
- [ ] Bundle size monitoring
- [ ] Virtualization for long lists
- [ ] Memoization of expensive computations

### Accessibility

- [ ] Keyboard navigation
- [ ] Screen reader support
- [ ] Color contrast compliance
- [ ] Focus management
- [ ] ARIA labels on interactive elements

---

## 5. Backend Patterns

### API Design

_REST vs. GraphQL, versioning strategy, pagination approach, error response format._

### Database

_Database choice and why, migration strategy, query patterns (ORM vs. raw), connection pooling._

### Middleware

_Middleware stack order, custom middleware written, request tracing approach._

### Error Handling

_Error classification (client vs. server), logging strategy, retry patterns for external services._

### Testing

| Layer | Strategy | Coverage |
|-------|----------|----------|
| Unit tests | _What was unit tested_ | _% or count_ |
| Integration tests | _API endpoint tests, DB tests_ | _% or count_ |
| End-to-end tests | _Full workflow tests_ | _% or count_ |

---

## 6. Code Quality Metrics

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Total lines of code | | | |
| Lines removed (dead code) | — | — | _e.g., -265 lines_ |
| Test count | | | |
| Test coverage % | | | |
| Lint warnings | | | |
| Type errors | | | |
| Build time (seconds) | | | |

**Dead code eliminated:** _List specific functions, classes, or files removed and why._

**Refactoring highlights:** _Major restructuring done and the impact on readability/maintainability._

---

## 7. Environment & Tooling Notes

### What Worked

| Tool / Config | Why It Worked |
|--------------|---------------|
| _e.g., uv for Python deps_ | _10x faster than pip, lockfile reproducibility_ |
| _e.g., just for task automation_ | _Single entry point for all commands_ |
| | |

### What Caused Friction

| Tool / Config | Problem | Workaround or Fix |
|--------------|---------|-------------------|
| _e.g., Node 22 + ESM_ | _Module resolution issues with some packages_ | _Added --experimental-vm-modules flag_ |
| _e.g., Pre-commit on large repos_ | _Slow hook execution_ | _Filtered to staged files only_ |
| | | |

### Runtime Versions

| Component | Version |
|-----------|---------|
| Python | |
| Node.js | |
| Database | |
| Package manager(s) | |
| CI/CD platform | |

---

## 8. Knowledge Propagation

Checklist of patterns and fixes to carry forward to other projects.

### Must Propagate (High Priority)

- [ ] _e.g., Security middleware defaults (request size, CORS, request ID)_
- [ ] _e.g., Error handling pattern (no blind except, log with exc_info)_
- [ ] _e.g., SQLite context manager pattern for thread safety_
- [ ]
- [ ]

### Should Propagate (Medium Priority)

- [ ] _e.g., Test fixture patterns that reduced boilerplate_
- [ ] _e.g., CI pipeline improvements (parallel jobs, caching)_
- [ ] _e.g., Documentation structure that worked well_
- [ ]
- [ ]

### Nice to Have (Low Priority)

- [ ] _e.g., Custom linting rules that caught real bugs_
- [ ] _e.g., Developer experience improvements (hot reload config, debug setup)_
- [ ]
- [ ]

---

## Retrospective Sign-off

| Role | Name | Date |
|------|------|------|
| Author | | |
| Reviewer | | |

**Next review date:** _When should this document be revisited?_
