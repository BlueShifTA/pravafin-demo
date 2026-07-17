# WORK_CYCLE.md — Formal Development Process

> The complete development cycle for any significant feature, refactor, or new project.
> Integrates with all playbooks as the **PROCESS** framework.

**Related Documents:**
- `playbook-build-working-software.md` — General technical guidelines
- `playbook-dashboard-project.md` — Dashboard-specific patterns
- `AUDIT_TEMPLATE.md` — Testing & validation framework
- `CODING_PROFILE.md` — coding conventions

---

## 🔄 The Seven-Phase Cycle

```
PHASE 0: PLAN (Opus)
    ↓
PHASE 1: STRUCTURAL PLAN (Loop until solid)
    ↓
PHASE 2: CLEAR CONTEXT (Save plan + reset)
    ↓
PHASE 3: EXECUTE (Right model for task)
    ↓
PHASE 4: TEST & AUDIT (Verify against plan)
    ↓
PHASE 5: IMPROVEMENT LIST (What's missing?)
    ↓
PHASE 6: LOOP (Until satisfied)
    ↓
PHASE 7: CLEANUP & COMMIT
```

---

## Phase 0: PLAN MODE (30-60 min)

**Model:** Opus 4.6 (complex planning)
**Goal:** Strategic thinking before execution

### 0.1 Define the One Problem
- Write 1 sentence. Not 3. Not 10.
- Example: "Users waste 40% of tokens on context loading. Detect and optimize it."
- If you can't write 1 sentence, you're solving too many problems. Split the work.

### 0.2 Identify Single Source of Truth (SSoT)
- Database table? API response? Config file? Memory structure?
- Everything else derives from it.
- **Anti-pattern:** 3 DBs with overlapping schemas → 3 versions of truth, 0 correct answers.

### 0.3 Architecture Sketch (5 min)
```
User/Request → API/CLI → Core Logic → Storage → Presentation
     ↑                                            ↓
     ←────────── Monitoring/Metrics ──────────←
```
Draw it. Own it. Change it if needed, but do it now, not halfway through.

### 0.4 Choose the Right Pattern
Consult relevant playbooks:
- **General software?** → `playbook-build-working-software.md`
- **Dashboard/monitoring?** → `playbook-dashboard-project.md`
- **Similar past work?** → Search `memory/2026-*.md` for lessons

### 0.5 Anti-Pattern Review
Before coding, scan the anti-pattern tables:
- Hardcoded paths?
- Multiple DBs?
- Silent errors?
- No empty states?
- Slow health checks?

**Output:** Strategic plan document (save to `memory/plan-YYYY-MM-DD-<task>.md`)

---

## Phase 1: STRUCTURAL PLAN (30-60 min)

**Model:** Opus or Sonnet (architecture work)
**Goal:** Concrete structure ready to execute

### 1.1 File Structure
```
project/
├── project/
│   ├── config.py          # ALL paths + env vars
│   ├── settings.py        # ALL constants
│   ├── core/              # Business logic (pure functions)
│   ├── storage/           # DB queries only
│   ├── api/               # HTTP/CLI layer
│   └── integrations/      # Platform glue
├── tests/                 # Unit + integration
├── scripts/               # Deployment/cron
└── start.sh               # ONE way to run it
```

### 1.2 Module Boundaries
Define what goes where:
- **Core logic:** Testable, no side effects, pure functions or dataclasses
- **Storage:** All DB access in one place
- **API:** Thin layer mapping HTTP → core → storage
- **Integrations:** Platform-specific glue (OpenClaw, external APIs)

### 1.3 Data Model (If DB involved)
```python
# Single canonical table
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    timestamp REAL,
    event_type TEXT,
    data JSON
);

# Derived views (not separate tables)
CREATE VIEW hourly_summary AS
    SELECT date(timestamp, 'unixepoch') as day,
           COUNT(*) as count
    FROM events
    GROUP BY day;
```

### 1.4 Coding Patterns (From CODING_PROFILE.md)
**Dataclass-first design:**
```python
@dataclasses.dataclass
class MyConfig:
    """Prefer immutable dataclasses with descriptive names."""
    setting: float
    _private_state: int = 0

    def __post_init__(self) -> None:
        # Validation in __post_init__
        assert self.setting > 0
```

**Protocol-based polymorphism:**
```python
class ProcessorProtocol(typing.Protocol):
    async def process(self, data: Any) -> Result: ...

# Use protocols for type hints (not ABCs)
def handle(processor: ProcessorProtocol) -> None: ...
```

**Import rules (non-negotiable):**
```python
# Same directory → relative imports
from .example import router          # ✅ CORRECT
from package.api.example import router  # ❌ WRONG (same dir, use relative)

# Different directory → absolute imports
from package.domain.models import MyModel  # ✅ CORRECT
from ..domain.models import MyModel        # ❌ WRONG (never parent-relative)
```

**No lazy imports:**
```python
# All imports at the top of the file — never inside functions or conditions
from ._helpers import compute  # ✅ top-level

def run() -> None:
    from ._helpers import compute  # ❌ lazy import — not allowed
```

**Always type-annotate class `__init__` attributes:**
```python
class Foo:
    def __init__(self, num: int, name: str) -> None:
        self.num: int = num       # ✅ annotated
        self.name: str = name     # ✅ annotated
```

**Exception handling (non-negotiable):**
```python
# No blind except — log with exc_info=True or re-raise
try:
    result = await fetch()
except Exception:
    logger.error("Unexpected error", exc_info=True)
    raise  # or swallow only if justified with logging

# Prefer specific exceptions
except TimeoutError as exc:
    logger.warning("Timeout: %s", exc, exc_info=True)
    raise
```
Enforced by ruff rules `BLE001` + `TRY`.

**No module-level global instances:**
```python
foo = Foo()  # ❌ WRONG — module-level global

class Boo:
    def __init__(self) -> None:
        self.foo: Foo = Foo()  # ✅ CORRECT — inside a class
```

**Async-first concurrency:**
```python
async def step_iter(self, scratch: ScratchProxy) -> list[Any] | None:
    """Async by default for I/O-bound operations."""
    await asyncio.sleep(self.delay)
    return None
```

**Retry & error recovery:**
```python
@with_retry(max_attempts=3, backoff=2.0)
async def capture_image(self) -> CameraImage:
    """Decorator-based retry with exponential backoff."""
    # Auto-reset on failure
```

### 1.5 Loop Until Solid
- Review with fresh eyes
- Check: does this solve the one problem?
- Check: are module boundaries clean?
- Check: is there one obvious way to run it?
- **When satisfied:** Proceed to Phase 2

**Output:** Structural plan with file names, module boundaries, data models

---

## Phase 2: CLEAR CONTEXT (5 min)

**Goal:** Clean slate for execution

### 2.1 Save Your Plan
```bash
# Write plan to workspace
cat > memory/plan-YYYY-MM-DD-<task>.md << EOF
# Plan: <Task Name>
...
EOF
```

### 2.2 Clear Session Context
```bash
# If in main session:
/clear-session

# Or spawn fresh sub-agent:
sessions_spawn --task "Execute <task> per plan-YYYY-MM-DD-<task>.md"
```

### 2.3 Why This Matters
- Large planning discussions consume context window
- Fresh execution = more tokens for implementation
- Clean separation: Plan vs Execute vs Test

---

## Phase 3: EXECUTE (Hours to Days)

**Model:** Sonnet (general), Haiku (quick fixes), Opus (complex refactors)
**Goal:** Build according to the structural plan

### 3.1 Foundation First (Day 1)
```python
# config.py — centralize ALL paths
BASE_DIR = Path(os.environ.get("PROJECT_DIR", "~/.projectname")).expanduser()
DB_PATH = BASE_DIR / "project.db"
LOG_DIR = BASE_DIR / "logs"

# settings.py — centralize ALL constants
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30
MODEL_PRICING = {...}
```

**No hardcoded paths anywhere else.**

### 3.2 Core Logic (Maintainable & Scalable)
**CRITICAL from coding profile:** Prefer modular design with classes/dataclasses over scattered functions.

```python
# ✅ Modular class-based design
@dataclasses.dataclass
class ImageProcessor(LoggingHelper):
    """Process images with configurable settings."""
    exposure: float
    retry_count: int = 3

    async def process(self, image: np.ndarray) -> ProcessedImage:
        """Main processing logic."""
        self.logger.info("Processing with exposure %.2f", self.exposure)
        ...

# ❌ Scattered functions
def process_image_1(img, exp): ...
def process_image_2(img, exp, retry): ...
def process_image_helper(img): ...
```

**Type safety first (95%+ annotations):**
```python
def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """Always annotate function signatures."""
    ...
```

**Structured logging (not print):**
```python
class LoggingHelper:
    """Mixin providing self.logger to all classes."""
    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)

# Usage:
self.logger.warning("Retry %d/%d", attempt, max_retries, exc_info=True)
```

### 3.3 Storage Layer
```python
# storage/db.py — ALL database access here
def get_events(since: datetime) -> list[Event]:
    """Query events since timestamp."""
    ...

def record_event(event: Event) -> int:
    """Insert event, return ID."""
    ...
```

**Single database, single schema.** Derive views via SQL, not separate tables.

### 3.4 API/CLI Layer
```python
# api/server.py — thin layer
@app.get("/api/events")
async def get_events(since: str = None):
    events = storage.get_events(parse_date(since))
    return [event.to_dict() for event in events]

# cli.py — typer/click
@app.command()
def list_events(since: str = None):
    """List events since timestamp."""
    events = storage.get_events(parse_date(since))
    for event in events:
        print(event)
```

### 3.5 Errors Never Silent
```python
# ✅ Specific exceptions
try:
    result = await camera.capture()
except CameraTimeoutError as exc:
    self.logger.warning("Camera timeout, retrying...", exc_info=True)
    raise

# ❌ Bare except
try:
    do_something()
except:
    pass  # SILENT FAILURE
```

### 3.6 Frontend (If Applicable)
**Three states per component:**
```jsx
{loading && <Spinner />}
{!loading && data.length === 0 && <EmptyState />}   // ← CRITICAL
{!loading && data.length > 0 && <Charts data={data} />}
```

**Consistent data contract:**
```json
// Backend always returns same field names
{
  "total_cost_usd": 1.23,
  "total_tokens": 100000,
  "timestamp": "2026-02-19T10:00:00Z"
}
```

### 3.7 One Way to Run It
```bash
# start.sh — ONE entry point
export PROJECT_DIR=~/.projectname
mkdir -p $PROJECT_DIR/logs
python3 -m projectname migrate
uvicorn projectname.api:app --host 0.0.0.0 --port 8001
```

---

## Phase 4: TEST & AUDIT (Hours)

**Model:** Sonnet or Haiku (verification work)
**Goal:** Verify implementation against plan + quality standards

### 4.1 Use AUDIT_TEMPLATE.md
Open `AUDIT_TEMPLATE.md` and check EVERY section:
- ✅ Foundation (config, constants, DB schema)
- ✅ Code Quality (exceptions, imports, type annotations)
- ✅ Functionality (unit, integration, E2E tests)
- ✅ Monitoring (health checks, metrics)
- ✅ Safety (data deletion, secrets handling)
- ✅ Documentation (README, docstrings, changelog)

### 4.2 End-to-End Testing
For **every feature** (not just unit tests):
```bash
1. API endpoint returns non-empty data
2. Field names match what frontend expects
3. Empty-data behavior works (fresh install)
4. With real data: does the feature work?
5. Error case: what happens when it fails?
```

### 4.3 Metrics Collection
Track quality:
- **Build time:** Fresh install → working (target: <5 min)
- **Test coverage:** Lines covered (target: >80%)
- **Token cost:** This phase cost (log for future comparison)
- **Issue count:** P0/P1/P2 bugs found during audit

### 4.4 Regression Tests
For every bug fix:
```python
def test_regression_issue_123():
    """Ensure bug #123 doesn't return."""
    # Reproduce the bug condition
    # Verify the fix works
```

### 4.5 Performance Check
- Health endpoint: <100ms response time
- Cron collectors: <2s total execution (especially on ARM)
- Database queries: <50ms for dashboards

**Output:** Completed audit checklist + metrics log

---

## Phase 5: IMPROVEMENT LIST (30 min)

**Model:** Sonnet (analysis)
**Goal:** Identify gaps and prioritize next iteration

### 5.1 What's Missing?
Review audit results:
- ❌ P0 issues (critical bugs, security holes) → **Must fix**
- ❌ P1 issues (broken features, wrong data) → **Should fix**
- ❌ P2 issues (polish, optimization) → **Could fix**

### 5.2 Compare to Plan
- Did you solve the one problem?
- Are there edge cases not handled?
- Is the implementation maintainable?
- Would this pass a senior code review?

### 5.3 Create Improvement List
```markdown
## Iteration 2 — Improvements

**P0 (Must Fix):**
- [ ] Health check times out on ARM (use HTTP probe)
- [ ] Dashboard shows infinite spinner (add empty state)

**P1 (Should Fix):**
- [ ] Missing type annotations on 3 functions
- [ ] No retry logic for camera capture

**P2 (Could Fix):**
- [ ] Add dark mode support
- [ ] Optimize DB query for large datasets
```

**Output:** Prioritized improvement list saved to workspace

---

## Phase 6: LOOP (Until Satisfied)

**Model:** Context-appropriate (Sonnet for fixes, Opus for complex changes)
**Goal:** Iterate until quality threshold met

### 6.1 Satisfaction Check
Ask these questions:
- ✅ Does it solve the original one problem?
- ✅ Does it pass the audit checklist?
- ✅ Is build time acceptable (<5 min fresh install)?
- ✅ Is test coverage >80%?
- ✅ Are all P0 issues resolved?
- ✅ Would you deploy this to production?

### 6.2 If NO → Iterate
```
1. Clear context (optional if small changes)
2. Execute improvements from Phase 5 list
3. Re-audit (Phase 4)
4. Update improvement list (Phase 5)
5. Check satisfaction again (Phase 6)
```

### 6.3 If YES → Proceed to Phase 7

**Maximum iterations:** 3-5 loops typical. If >5, re-evaluate the plan (may need structural changes).

---

## Phase 7: CLEANUP & COMMIT (30 min)

**Model:** Haiku or Sonnet (cleanup work)
**Goal:** Production-ready state

### 7.0 CRITICAL: Safe Database Cleanup

⚠️ **GOLDEN RULE:** Never use `rm` for database files. Always use recycle bin.

**Safe deletion procedure:**
```bash
# Step 1: List what exists
ls -lah ~/.myapp/*.db

# Step 2: Identify CURRENT (canonical database)
# Example: tokenwise.db ✅ (keep)
#          metrics.db ❌ (old, delete)
#          unified_ledger.db ❌ (old, delete)

# Step 3: Safe deletion (use trash-cli or safe-delete.sh)
trash ~/.myapp/metrics.db
trash ~/.myapp/unified_ledger.db

# OR if trash-cli not installed:
./scripts/safe-delete.sh ~/.myapp/metrics.db
./scripts/safe-delete.sh ~/.myapp/unified_ledger.db

# Step 4: Verify correct file remains
ls -lh ~/.myapp/*.db
# Output: tokenwise.db (only one left) ✅

# Step 5: Verify in recycle bin
ls -la ~/.recycle-bin/$(date +%Y-%m-%d)/
# Files recoverable for 30 days
```

**Recovery (if you deleted wrong file):**
```bash
# List deleted files
ls -la ~/.recycle-bin/

# Restore from recycle bin
cp ~/.recycle-bin/2026-02-19/tokenwise.db.1771495876 ~/.myapp/tokenwise.db
```

**This applies to ANY database:**
- SQLite files (*.db)
- Postgres/MySQL backups (*.sql, *.dump)
- Configuration files (*.json, *.yaml, *.toml)
- State files (*.state, *.lock)
- Any file containing: transactions, records, metrics

### 7.1 Remove Dead Code
```bash
# Find old/backup files and move to trash
find . -name "*_old.py" -o -name "*_backup.py" | while read f; do
  trash "$f"
done
```

### 7.2 Update Documentation
```bash
# README.md — installation + usage
# CHANGELOG.md — what changed
# Inline docstrings — updated for new APIs
```

### 7.3 Pre-Commit Checks (Team Standard)
```bash
# Auto-format
uv run ruff format .
uv run ruff check --fix .

# Type check
uv run pyright
uv run mypy .

# Run tests
uv run pytest tests

# Pre-commit hooks
uv run pre-commit run --all-files
```

### 7.4 Commit
**Follow team commit style:**
```
<action> <what> [<detail>]

- problem: <root cause>
- <bullet points explaining changes>
- <impact/testing notes>
```

**Example:**
```
Fix dashboard empty state and add ARM-safe health checks

- problem: MetricsSection showed infinite spinner when API returned
  0 records (fresh install)
- Add empty state UI component for all dashboard tabs
- Replace `openclaw gateway status` with HTTP probe (100ms vs 10s)
- Add regression test for empty data behavior

Tested on fresh install + with real data.
```

### 7.5 Final Verification
```bash
# Fresh install test
rm -rf ~/.projectname  # or trash if contains data
./start.sh
# Verify: app starts, health check passes, UI shows empty state

# With data test
python3 scripts/generate-test-data.py
# Verify: dashboard shows charts, metrics correct, no errors
```

**Output:** Clean, production-ready codebase

---

## 📊 Metrics to Track

Track these across iterations to measure improvement:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Build Time** | <5 min | Fresh install → working app |
| **Test Coverage** | >80% | `pytest --cov` |
| **Token Cost** | Decrease over time | Session cost per phase |
| **Quality Score** | >90% | Audit checklist completion |
| **Iteration Count** | <5 loops | Loops to satisfaction |
| **P0 Issues** | 0 | Critical bugs at Phase 7 |

---

## 🎯 When to Use This Cycle

**Always use for:**
- ✅ New projects
- ✅ Major refactors
- ✅ Complex features (>1 day work)
- ✅ Multi-file changes
- ✅ Architecture decisions

**Optional for:**
- Quick bug fixes (<30 min)
- Documentation updates
- Minor tweaks to existing code

**Never skip Phase 4 (Audit) for:**
- Anything touching databases
- Anything affecting production
- Security-related changes
- Data deletion/cleanup

---

## 🔗 Integration with Playbooks

**This document (WORK_CYCLE.md) = PROCESS**
**Playbooks = TECHNICAL GUIDELINES**

**Use them together:**
1. **Phase 0 (Plan):** Read relevant playbook for patterns/anti-patterns
2. **Phase 1 (Structure):** Reference playbook file structures, module boundaries
3. **Phase 3 (Execute):** Follow playbook conventions (DB design, error handling, coding style)
4. **Phase 4 (Audit):** Use AUDIT_TEMPLATE.md + playbook checklists

**Example flow:**
```
Building a new dashboard?
→ WORK_CYCLE.md (process)
  + playbook-dashboard-project.md (technical patterns)
  + CODING_PROFILE.md (code quality standards)
  + AUDIT_TEMPLATE.md (validation framework)

Refactoring existing code?
→ WORK_CYCLE.md (process)
  + playbook-build-working-software.md (general patterns)
  + CODING_PROFILE.md (maintainable design)
  + memory/2026-*-lessons.md (past mistakes to avoid)
```

---

## 💡 Key Principles (Quick Reference)

1. **One Problem** — If you can't write it in 1 sentence, split the work
2. **Single Source of Truth** — One DB, one config, one entry point
3. **Plan Before Execute** — Opus for strategy, Sonnet for implementation
4. **Clear Context Between Phases** — Fresh slate = more tokens
5. **Maintainable & Scalable** — Classes/dataclasses over scattered functions
6. **Type Safety First** — 95%+ annotations, protocols over ABCs
7. **Test End-to-End** — Not just unit tests, verify full flow
8. **Audit Before Satisfaction** — Use AUDIT_TEMPLATE.md every time
9. **Loop Until Quality** — 3-5 iterations typical, <5 target
10. **Safe Cleanup** — Trash > rm, 30-day retention for databases

---

**Last Updated:** 2026-02-20
**Owner:** Surapat Ek-In (Arm)
**Next Review:** After using this cycle on 3 different projects
