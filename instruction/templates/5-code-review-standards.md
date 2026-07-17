# 5. Code Review & Quality Standards

**Role:** Maintains code quality across the team
**Context:** Startup growing from 2-15 engineers, preventing technical debt

---

## Philosophy

Code review is not punishment. It's the team's shared responsibility to maintain quality.

- **Fast feedback loops** (< 4 hours, preferably < 1 hour)
- **Psychological safety** (critique code, not people)
- **Learn-as-you-go** (junior engineers review senior code)
- **Automate what you can** (linters, formatters, tests)

---

## Review Process

### 1. Pre-Review Checklist (Author's Job)

Before requesting review, ensure:

- [ ] Code is formatted (linter passes, no style issues)
- [ ] Tests pass locally (including new tests)
- [ ] No obvious bugs (you tested manually)
- [ ] Commit history is clean (logical chunks, good messages)
- [ ] Documentation updated (docstrings, README, etc.)
- [ ] No debug code, console logs, or TODOs
- [ ] Performance considered (no obvious inefficiencies)

### 2. Code Review Process (Reviewer's Job)

**Read code in this order:**

1. **PR description:** What's the intent? Why this change?
2. **File changes:** Which files changed? Why? (Check diff stats)
3. **Critical logic:** Understand the main change
4. **Edge cases:** What could break? What if X is null?
5. **Tests:** Do tests cover the new code?
6. **Performance:** Any obvious inefficiencies?

**Review types:**

```
🟢 APPROVE — Code is good, can ship
🟡 COMMENT — Style/clarity issues, not blocking
🔴 REQUEST CHANGES — Logic issues, test gaps, security concerns
```

### 3. Feedback Guidelines

#### ✅ Good Feedback
```
"This query might N+1 on large datasets. Consider using SELECT * with a join
or adding a limit. Run with EXPLAIN to verify."

"Error message is unclear. Users won't know what 'Invalid token' means.
Suggest: 'Your session expired. Please log in again.'"
```

#### ❌ Bad Feedback
```
"This is inefficient"  — Doesn't tell them what's wrong
"Why did you do it this way?" — Sounds critical
"You should use async/await" — Without explaining why it matters here
```

### 4. Responding to Feedback

**Author's mindset:**
- Feedback is about the code, not you
- Ask questions if feedback is unclear
- Explain your reasoning if you disagree
- Don't over-engineer to appease reviewers

**When to push back:**
- "This doesn't match our conventions" → Show them the convention
- "This is premature optimization" → Agree, simplify, move on
- "This violates our architecture" → Refactor to fit the pattern

---

## Automated Checks (CI/CD)

Set these up to run automatically on every PR:

```yaml
# .github/workflows/ci.yml (example)

pre-checks:
  - Linter (Prettier, ESLint, Black, etc.)
  - Type checker (TypeScript, mypy)
  - Test suite (unit + integration)
  - Coverage check (80% minimum)
  - Security scan (pnpm audit, bandit)
  - Performance baseline (compare to main)
```

**Humans should only review things humans need to review.** Everything else should be automated.

---

## Code Quality Metrics

Track these per sprint:

| Metric | Target | Why |
|--------|--------|-----|
| Review turnaround | < 4 hours | Fast feedback |
| Comment ratio | 1-3 per PR | Balanced feedback |
| Rework cycles | < 2 per PR | Clear feedback |
| Test coverage | 80%+ | Confidence |
| Bug escape rate | < 1 per 100 PRs | Quality gates work |

---

## Conventions to Enforce

### Language-Specific

**Python:**
- PEP 8 (with Ruff + Black for auto-formatting)
- Type hints on all public functions
- Always type-annotate class `__init__` params, attributes (`self.x: int = x`), and `-> None`
- Same-directory imports use relative (`from .x`), cross-module use absolute — never parent-relative (`from ..`)
- No lazy imports — all imports at the top, never inside functions or conditions
- No blind `except Exception: pass` — must log with `exc_info=True` or re-raise (ruff `BLE001`/`TRY`)
- No module-level global instances (`foo = Foo()` at top level) — instantiate inside classes/functions
- Docstrings (Google or NumPy style)
- No wildcard imports

**TypeScript/JavaScript:**
- ESLint + Prettier (opinionated, consistent)
- No `any` types (except escape hatches with comments)
- Explicit error handling
- Async/await over promises

**General:**
- Single responsibility (functions do one thing)
- Clear naming (no `x`, `temp`, `data`)
- DRY (don't repeat yourself)
- KISS (keep it simple, stupid)

### Git Hygiene
- One logical change per commit
- Good commit messages: "Add X because Y" (not "fix stuff")
- Rebase and squash when needed
- No merge commits (rebase main into branch, then fast-forward)

---

## Decision Matrix: When to Merge vs. Request Changes

| Situation | Action | Why |
|-----------|--------|-----|
| Test coverage 100%, all checks pass, logic clear | APPROVE | Low risk, ship fast |
| One small issue (naming, comment) | COMMENT (not blocking) | Don't slow down good code |
| Performance concern, no data to support it | COMMENT (get metrics first) | Optimize what's slow, not guesses |
| Missing test for error case | REQUEST CHANGES | Untested code fails in production |
| Violates team convention | REQUEST CHANGES | Consistency matters at startup scale |
| Unclear business logic | REQUEST CHANGES | Future maintainers will struggle |

---

## Onboarding Code Reviews

### For New Team Members

**First 2 weeks:**
- Review senior code (learn patterns)
- Don't request changes, only ask questions
- Pair with senior engineer on 1-2 reviews

**Weeks 3-8:**
- Review peer code (give feedback, non-blocking)
- Pair on decisions, not all reviews
- Expect your code to be reviewed carefully

**After 2 months:**
- Full review responsibilities
- Can approve PRs
- Mentoring junior engineers

### Red Flags in Code Review

If you see these patterns, talk to the author:
- Repeated code (DRY violations)
- Growing functions (too much responsibility)
- Increasing test complexity (bad design)
- Cryptic variable names
- Missing error handling

These usually mean the design needs discussion, not just code fixes.

---

## Review SLA

| PR Priority | SLA | Who |
|-------------|-----|-----|
| Hot fix (production broken) | 15 min | On-call engineer |
| Bug fix | 1 hour | Any engineer |
| Feature | 4 hours | Code owner + 1 reviewer |
| Refactor | Next day | At least 1 reviewer |

---

## Anti-Patterns to Avoid

❌ **Rubber stamping:** "Looks good" without reading code
❌ **Perfectionism:** Requesting changes for personal style preferences
❌ **Slow feedback:** Reviewing after 5 days (context lost)
❌ **Anonymous feedback:** Always know who reviewed your code
❌ **Bike-shedding:** Debating tabs vs. spaces (use automation)
