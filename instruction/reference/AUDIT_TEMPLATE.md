# AUDIT_TEMPLATE.md — Testing & Validation Framework

> Comprehensive audit checklist for Phase 4 of the work cycle.
> Use this BEFORE declaring anything "complete" or "production ready."

**Related Documents:**
- `WORK_CYCLE.md` — Formal development process (use this in Phase 4)
- `memory/VALIDATION_PROTOCOL.md` — Haiku hallucination prevention
- `SURAPAT_CODING_PROFILE.md` — Code quality standards

---

## 🎯 Audit Goals

**Before marking work as complete:**
- ✅ Data is real (not hallucinated/hardcoded)
- ✅ Services actually work (not just "code exists")
- ✅ Tests prove functionality (not just pass)
- ✅ Metrics are measured (not estimated)
- ✅ Quality meets standards (team conventions)

**Remember:** "Code exists" ≠ "It works" — run it and prove it.

---

## 📋 Section 1: Foundation (30 min)

### 1.1 Configuration & Paths ✅

**Check:**
- [ ] All paths centralized in `config.py` (or equivalent)
- [ ] No hardcoded paths in any other files
- [ ] Environment variables documented
- [ ] Defaults work on fresh install
- [ ] Path validation on startup (create dirs if missing)

**Test:**
```bash
# Fresh install test
rm -rf ~/.projectname  # or trash if contains data
python3 -m projectname  # should create dirs, not crash
ls ~/.projectname       # verify structure created
```

**Expected output:**
```
~/.projectname/
├── project.db
├── logs/
└── config.json
```

### 1.2 Constants & Settings ✅

**Check:**
- [ ] All pricing/costs in `pricing.py` or `settings.py`
- [ ] All magic numbers replaced with named constants
- [ ] Constants grouped logically (dataclasses preferred)
- [ ] No scattered constants in business logic

**Test:**
```python
# Should find ALL pricing in one file
grep -r "15.0.*input" src/  # model pricing
grep -r "0.015" src/        # any hardcoded costs
# Only hits: pricing.py ✅
```

**Example structure:**
```python
@dataclasses.dataclass
class CameraConstants:
    MAX_ATTEMPTS: int = 3
    ATTEMPT_RETRY_DELAY: float = 2.0
    DEFAULT_EXPOSURE: float = 0.1
```

### 1.3 Database Schema ✅

**Check:**
- [ ] Single canonical database file
- [ ] Schema documented (CREATE TABLE statements or ORM models)
- [ ] Migrations handle existing databases gracefully
- [ ] No duplicate tables with overlapping schemas
- [ ] Indexes on frequently queried columns

**Test:**
```bash
# Fresh DB creation
rm ~/.projectname/project.db
python3 -c "from projectname.db import init_db; init_db()"
sqlite3 ~/.projectname/project.db ".schema"
# Verify: expected tables exist, no duplicates
```

**Anti-pattern check:**
```sql
-- ❌ Multiple tables with same data
CREATE TABLE api_calls (...);
CREATE TABLE cost_metrics (...);  -- overlaps with api_calls
CREATE TABLE token_usage (...);   -- overlaps with api_calls

-- ✅ Single source of truth + derived views
CREATE TABLE api_calls (...);
CREATE VIEW cost_metrics AS SELECT ... FROM api_calls;
```

### 1.4 Logging Setup ✅

**Check:**
- [ ] No `print()` statements in production code
- [ ] Centralized logging configuration
- [ ] Log levels appropriate (DEBUG/INFO/WARNING/ERROR)
- [ ] Structured logging (key-value pairs preferred)
- [ ] Log files rotate (don't fill disk)

**Test:**
```bash
# Search for print statements
grep -r "print(" src/ --exclude-dir=tests
# Should be empty or only in __main__ blocks

# Run app, check logs
python3 -m projectname
cat ~/.projectname/logs/app.log
# Verify: structured logs, appropriate levels
```

**Example (recommended pattern):**
```python
class LoggingHelper:
    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)

# Usage:
self.logger.info("Processing image", extra={"exposure": 0.1})
self.logger.warning("Retry %d/%d", attempt, max_retries, exc_info=True)
```

---

## 📋 Section 2: Code Quality (60 min)

### 2.1 Type Annotations ✅

**Check:**
- [ ] All function signatures annotated (95%+ coverage)
- [ ] Return types specified
- [ ] Class `__init__` methods: all params annotated, all `self.x` attributes annotated, return `-> None`
- [ ] Avoid `Any` unless truly necessary
- [ ] Use modern syntax (`list[str]` not `List[str]`)
- [ ] Protocols for interfaces (not ABCs)

**Test:**
```bash
# Type check with mypy/pyright
uv run mypy src/
uv run pyright src/

# Count unannotated functions
grep -r "^def " src/ | grep -v " -> " | wc -l
# Target: <5% of total functions
```

**Example:**
```python
# ✅ Full annotations
def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """Calculate cost for API call."""
    ...

# ❌ No annotations
def calculate_cost(model, input_tokens, output_tokens):
    ...
```

### 2.2 Error Handling ✅

**Check:**
- [ ] No bare `except:` clauses
- [ ] Specific exceptions caught
- [ ] Errors logged with context (`exc_info=True`)
- [ ] User-facing errors have helpful messages
- [ ] Critical errors re-raised after logging

**Test:**
```bash
# Find bare except
grep -r "except:" src/ --include="*.py"
# Should be empty or have justification comments

# Find generic Exception catches
grep -r "except Exception" src/ --include="*.py"
# Review each: is it justified?
```

**Example:**
```python
# ✅ Specific exceptions
try:
    result = await camera.capture()
except CameraTimeoutError as exc:
    self.logger.warning("Camera timeout, retrying...", exc_info=True)
    raise
except CameraDisconnectedError:
    self.logger.error("Camera disconnected, resetting...")
    await self._reset_camera()

# ❌ Silent failures
try:
    do_something()
except:
    pass  # WHO KNOWS WHAT BROKE?
```

### 2.3 Import Organization ✅

**Check:**
- [ ] Imports at module level (not inside functions) — **no lazy imports**
- [ ] Same-directory imports use relative paths (`from .x`), cross-module use absolute — never parent-relative (`from ..`)
- [ ] No unused imports
- [ ] Grouped: stdlib, third-party, local
- [ ] Absolute imports for cross-package, relative imports within same package
- [ ] No circular dependencies
- [ ] No module-level global instances (`foo = Foo()` at top level) — use singleton or instantiate in classes/functions

**Test:**
```bash
# Linting
uv run ruff check src/ --select I,F401
# F401 = unused imports
# I = import sorting

# Circular dependency check
python3 -c "import projectname"  # should not fail
```

**Example (recommended pattern):**
```python
# Standard library
import asyncio
import dataclasses as dc
import logging
from pathlib import Path

# Third-party
import numpy as np
import aiohttp

# Local imports (absolute)
from projectname.core import processor
from projectname.storage import db

# Relative imports (same package only)
from ._protocols import ProcessorProtocol
```

### 2.4 Code Structure (Maintainable & Scalable) ✅

**CRITICAL from coding profile:** Prefer modular design with classes/dataclasses over scattered functions.

**Check:**
- [ ] Related logic grouped in classes
- [ ] Dataclasses for data structures
- [ ] Pure functions where appropriate
- [ ] Clear separation of concerns
- [ ] No "god classes" (>500 lines = split)

**Test:**
```bash
# Find large files that might need splitting
find src/ -name "*.py" -exec wc -l {} + | sort -rn | head
# >500 lines? Consider splitting

# Check for scattered functions vs classes
grep -r "^def " src/ | wc -l     # function count
grep -r "^class " src/ | wc -l   # class count
# Ratio should favor classes for complex logic
```

**Example:**
```python
# ✅ Modular class-based design
@dataclasses.dataclass
class ImageProcessor(LoggingHelper):
    """Process images with configurable settings."""
    exposure: float
    retry_count: int = 3
    _state: dict = dataclasses.field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate settings."""
        assert self.exposure > 0

    async def process(self, image: np.ndarray) -> ProcessedImage:
        """Main processing logic."""
        self.logger.info("Processing with exposure %.2f", self.exposure)
        ...

# ❌ Scattered functions
def process_image_1(img, exp): ...
def process_image_2(img, exp, retry): ...
def process_image_helper(img): ...
def process_image_variant_a(img, exp): ...
```

### 2.5 Documentation ✅

**Check:**
- [ ] All public classes have docstrings
- [ ] All public functions have docstrings
- [ ] Docstrings explain "why" not just "what"
- [ ] Complex logic has inline comments
- [ ] No TODO comments in committed code

**Test:**
```bash
# Find undocumented public classes/functions
grep -A1 "^class [A-Z]" src/ | grep -v '"""'
grep -A1 "^def [a-z]" src/ | grep -v '"""'

# Find TODOs
grep -r "TODO" src/
# Move to issues/backlog before commit
```

---

## 📋 Section 3: Functionality Testing (90 min)

### 3.1 Unit Tests ✅

**Check:**
- [ ] Core logic has unit tests (>80% coverage)
- [ ] Tests are fast (<1s each)
- [ ] Tests are isolated (no shared state)
- [ ] Test names describe behavior
- [ ] Edge cases covered

**Test:**
```bash
# Run unit tests
uv run pytest tests/unit/ -v

# Coverage report
uv run pytest tests/ --cov=projectname --cov-report=term
# Target: >80% coverage
```

**Example:**
```python
def test_cost_calculation_opus():
    """Calculate cost for Claude Opus 4.6."""
    cost = calculate_cost("claude-opus-4-6", input_tokens=1000, output_tokens=500)
    assert cost == 0.0525  # (1000 * 0.015) + (500 * 0.075)

def test_cost_calculation_zero_tokens():
    """Handle zero tokens gracefully."""
    cost = calculate_cost("claude-opus-4-6", input_tokens=0, output_tokens=0)
    assert cost == 0.0
```

### 3.2 Integration Tests ✅

**Check:**
- [ ] Database operations tested with real DB
- [ ] API endpoints return expected data
- [ ] External integrations mocked appropriately
- [ ] Error conditions tested (not just happy path)

**Test:**
```bash
# Run integration tests (may be slower)
uv run pytest tests/integration/ -v

# Test with fresh database
rm /tmp/test_project.db
uv run pytest tests/integration/test_db.py
```

**Example:**
```python
def test_record_and_query_events(tmp_path):
    """Test full DB lifecycle."""
    db_path = tmp_path / "test.db"
    db = Database(db_path)

    # Record event
    event_id = db.record_event(Event(type="test", data={"key": "value"}))

    # Query back
    events = db.get_events(limit=10)
    assert len(events) == 1
    assert events[0].id == event_id
    assert events[0].data["key"] == "value"
```

### 3.3 End-to-End Tests ✅

**For EVERY user-facing feature:**
- [ ] Fresh install → feature works
- [ ] Empty data → UI shows empty state
- [ ] Real data → feature renders correctly
- [ ] Error case → graceful degradation

**Test (Example: Dashboard):**
```bash
# 1. Fresh install
rm -rf ~/.projectname
./start.sh &
sleep 5

# 2. Empty state test
curl http://localhost:8001/api/dashboard/metrics
# Expected: {"metrics": []}  (not error)
curl http://localhost:8001/
# Expected: UI shows "No data yet" message

# 3. With data test
python3 scripts/generate-test-data.py  # populate DB
curl http://localhost:8001/api/dashboard/metrics
# Expected: {"metrics": [{...}, ...]}
# Visit UI: charts render, no infinite spinner

# 4. Error case test
chmod 000 ~/.projectname/project.db  # simulate permission error
curl http://localhost:8001/api/dashboard/metrics
# Expected: 500 error with helpful message (not crash)
chmod 644 ~/.projectname/project.db  # restore
```

### 3.4 Regression Tests ✅

**For every bug fix:**
- [ ] Reproduce the bug
- [ ] Write test that fails on old code
- [ ] Verify test passes on fixed code
- [ ] Document the bug in test docstring

**Example:**
```python
def test_regression_infinite_spinner_empty_data():
    """
    Regression test for issue #42: infinite spinner on fresh install.

    Bug: MetricsSection showed loading spinner forever when API
    returned empty array (fresh install, no data yet).

    Fix: Add explicit empty state check.
    """
    response = client.get("/api/dashboard/metrics")
    assert response.status_code == 200
    data = response.json()

    # Even with empty data, API should return valid structure
    assert "metrics" in data
    assert isinstance(data["metrics"], list)
    assert len(data["metrics"]) == 0  # fresh install = no data
```

---

## 📋 Section 4: Monitoring & Performance (60 min)

### 4.1 Health Checks ✅

**Check:**
- [ ] Health endpoint exists (`/health` or equivalent)
- [ ] Response time <100ms (fast probe, not diagnostics)
- [ ] Returns 200 when healthy, 503 when degraded
- [ ] No shell commands (subprocess overhead)
- [ ] Tests core dependencies (DB accessible, etc.)

**Test:**
```bash
# Start service
./start.sh &
PID=$!
sleep 5

# Health check
time curl -s http://localhost:8001/health
# Expected: <0.1s, 200 OK

# Verify it's a probe, not full diagnostics
timeout 1 curl -s http://localhost:8001/health
# Should not timeout

# Cleanup
kill $PID
```

**Example:**
```python
@app.get("/health")
async def health():
    """Fast health probe (not diagnostics)."""
    try:
        # Quick DB check
        db.execute("SELECT 1")
        return {"status": "healthy"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded"}
        )
```

**Anti-pattern:**
```python
# ❌ SLOW (10s on ARM)
subprocess.run(["openclaw", "gateway", "status"], timeout=5)

# ❌ Unreliable from cron
subprocess.run(["systemctl", "--user", "is-active", "service"])

# ✅ Direct probe (100ms)
requests.get("http://127.0.0.1:8000/", timeout=2).status_code == 200
```

### 4.2 Metrics Collection ✅

**Check:**
- [ ] Metrics derived from canonical data source
- [ ] No duplicate recording pipelines
- [ ] Cron-friendly (exit codes, stdout/stderr logging)
- [ ] Fast execution (<2s total, especially on ARM)
- [ ] Errors logged, not silenced

**Test:**
```bash
# Run collector manually
time python3 scripts/collect-metrics.py
# Expected: <2s, exit 0

# Check logs
cat ~/.projectname/logs/metrics.log
# Should show: what was collected, any warnings

# Verify data written
sqlite3 ~/.projectname/project.db "SELECT COUNT(*) FROM metrics;"
# Should increment after each run
```

**Example cron entry:**
```cron
*/5 * * * * /usr/bin/python3 /path/to/collect-metrics.py >> /var/log/metrics.log 2>&1
```

### 4.3 Performance Benchmarks ✅

**Check:**
- [ ] Key operations measured (not guessed)
- [ ] Database queries <50ms (dashboard views)
- [ ] API endpoints <200ms (P95)
- [ ] Frontend loads <2s (initial render)
- [ ] No N+1 queries

**Test:**
```bash
# API benchmarks
time curl http://localhost:8001/api/dashboard/metrics
# Target: <200ms

# DB query benchmarks
sqlite3 ~/.projectname/project.db <<EOF
.timer ON
SELECT * FROM api_calls WHERE timestamp > (unixepoch() - 3600);
EOF
# Target: <50ms

# Frontend load time
curl -o /dev/null -s -w "Time: %{time_total}s\n" http://localhost:8001/
# Target: <2s
```

### 4.4 Resource Usage ✅

**Check:**
- [ ] Memory usage reasonable (<500MB for small projects)
- [ ] CPU usage low when idle (<5%)
- [ ] Disk usage grows linearly (no runaway logs)
- [ ] File descriptors closed properly (no leaks)

**Test:**
```bash
# Start service
./start.sh &
PID=$!
sleep 10

# Check resource usage
ps aux | grep $PID
# Note: RSS memory, CPU%

# Idle CPU usage
sleep 30
ps aux | grep $PID
# Should be <5% CPU when idle

# Check file descriptors
lsof -p $PID | wc -l
# Should be stable (not growing)

# Cleanup
kill $PID
```

---

## 📋 Section 5: Safety & Security (45 min)

### 5.1 Data Deletion Safety ✅

**CRITICAL:** Never permanently delete database files.

**Check:**
- [ ] Use `trash` or `safe-delete.sh` (not `rm`) for DBs
- [ ] 30-day retention in recycle bin
- [ ] Recovery procedure documented
- [ ] User confirmations for destructive actions
- [ ] Audit log of deletions

**Test:**
```bash
# Verify safe-delete.sh exists
ls scripts/safe-delete.sh

# Test safe deletion
touch /tmp/test.db
./scripts/safe-delete.sh /tmp/test.db
ls ~/.recycle-bin/$(date +%Y-%m-%d)/
# Should contain: test.db.TIMESTAMP

# Test recovery
ls ~/.recycle-bin/$(date +%Y-%m-%d)/ | head -1
# Restore: cp ~/.recycle-bin/YYYY-MM-DD/file.TIMESTAMP /original/path
```

**Anti-pattern:**
```bash
# ❌ NEVER do this
rm ~/.projectname/database.db  # NO UNDO

# ✅ Always use
trash ~/.projectname/old_database.db
# OR
./scripts/safe-delete.sh ~/.projectname/old_database.db
```

### 5.2 Secrets Handling ✅

**Check:**
- [ ] No API keys in code
- [ ] No passwords in config files
- [ ] Environment variables for secrets
- [ ] `.env` files gitignored
- [ ] Secrets rotation documented

**Test:**
```bash
# Search for potential secrets
grep -r "api_key\|password\|secret\|token" src/ --include="*.py"
# Should only find env var references, not values

# Check gitignore
cat .gitignore | grep -E "\.env|secret|key"
# Should include: .env, *.key, secrets.json, etc.

# Verify secrets not in git
git log -p | grep -i "api_key.*=.*sk-" || echo "Clean"
# Should print: Clean
```

### 5.3 Input Validation ✅

**Check:**
- [ ] User inputs sanitized (SQL injection, path traversal)
- [ ] File uploads validated (size, type, content)
- [ ] API parameters type-checked
- [ ] Timestamps validated (reasonable range)

**Test:**
```bash
# SQL injection test
curl "http://localhost:8001/api/events?query='; DROP TABLE events; --"
# Should: sanitize or reject, not execute

# Path traversal test
curl "http://localhost:8001/api/files/../../etc/passwd"
# Should: reject, not leak system files

# Type validation test
curl "http://localhost:8001/api/events?limit=not_a_number"
# Should: 400 error with helpful message
```

---

## 📋 Section 6: Documentation (30 min)

### 6.1 README.md ✅

**Check:**
- [ ] One-sentence project description
- [ ] Installation instructions
- [ ] Usage examples
- [ ] Configuration options documented
- [ ] Troubleshooting section

**Test:**
```bash
# Follow README from scratch
cd /tmp
git clone <repo>
# Follow installation steps EXACTLY
# Verify: app runs without modifications
```

### 6.2 Inline Documentation ✅

**Check:**
- [ ] All public APIs documented
- [ ] Complex logic explained
- [ ] Architecture decisions noted
- [ ] No stale comments (outdated code references)

**Test:**
```bash
# Find undocumented public functions
grep -r "^def [a-z]" src/ -A1 | grep -v '"""' | wc -l
# Target: 0

# Find potential stale comments
grep -r "TODO\|FIXME\|HACK" src/
# Move to issues before commit
```

### 6.3 CHANGELOG.md ✅

**Check:**
- [ ] Version history maintained
- [ ] Breaking changes highlighted
- [ ] Migration guides for major versions
- [ ] Follows semantic versioning

**Example:**
```markdown
## [1.2.0] - 2026-02-20

### Added
- Monitoring framework with metrics collection
- Health check endpoint (fast HTTP probe)

### Changed
- Replaced `openclaw gateway status` with HTTP probe (100ms vs 10s)

### Fixed
- Dashboard infinite spinner on empty data (#42)

### Breaking Changes
- Database schema: added `context_tokens` column
  Migration: `python3 -m projectname migrate`
```

---

## 📋 Section 7: Deployment Readiness (30 min)

### 7.1 One-Command Deployment ✅

**Check:**
- [ ] Single script to start (`start.sh` or equivalent)
- [ ] Environment detection (dev/staging/prod)
- [ ] Migrations run automatically
- [ ] Log directory creation handled
- [ ] Port configuration via env vars

**Test:**
```bash
# Fresh deployment test
cd /tmp
git clone <repo>
export PROJECT_DIR=/tmp/test-deploy
./start.sh
# Should: create dirs, run migrations, start service
curl http://localhost:8001/health
# Expected: 200 OK
```

### 7.2 Graceful Shutdown ✅

**Check:**
- [ ] SIGTERM handled (clean shutdown)
- [ ] Active requests complete (not dropped)
- [ ] Resources released (DB connections, files)
- [ ] Exit code indicates success/failure

**Test:**
```bash
# Start service
./start.sh &
PID=$!
sleep 5

# Graceful shutdown
kill -TERM $PID
sleep 5

# Verify clean exit
wait $PID
echo "Exit code: $?"
# Expected: 0

# Check logs for cleanup messages
tail ~/.projectname/logs/app.log
# Should show: "Shutting down gracefully..."
```

### 7.3 Monitoring Integration ✅

**Check:**
- [ ] Cron jobs configured (if applicable)
- [ ] Health checks integrated (systemd, supervisor, etc.)
- [ ] Log aggregation configured
- [ ] Alert thresholds defined

**Test:**
```bash
# Verify cron entry (if applicable)
crontab -l | grep collect-metrics
# Should show: */5 * * * * /path/to/collect-metrics.py

# Simulate failure
pkill -9 -f "projectname"
sleep 10
# Health check should detect failure and alert/restart
```

---

## 📊 Quality Scorecard

Fill this out at the end of Phase 4:

| Category | Score (0-100%) | Notes |
|----------|----------------|-------|
| **Foundation** | __% | Config, constants, DB schema, logging |
| **Code Quality** | __% | Types, errors, imports, structure, docs |
| **Functionality** | __% | Unit, integration, E2E, regression tests |
| **Monitoring** | __% | Health checks, metrics, performance |
| **Safety** | __% | Data deletion, secrets, input validation |
| **Documentation** | __% | README, inline docs, changelog |
| **Deployment** | __% | One-command start, shutdown, monitoring |
| **OVERALL** | __% | Average of above |

**Target:** >90% overall before declaring "production ready"

**P0 Issues:** Any category <50% = must fix before merge
**P1 Issues:** Any category <80% = should fix before production
**P2 Issues:** Any category <90% = could improve in next iteration

---

## 🚨 Red Flags (Stop and Fix)

If you see ANY of these during audit, STOP and fix immediately:

- ❌ Database deletions use `rm` (no recycle bin)
- ❌ Bare `except:` clauses (silent failures)
- ❌ Hardcoded paths (breaks on deployment)
- ❌ No empty state UI (infinite spinners)
- ❌ Health checks take >1s (timeout issues)
- ❌ API keys in code (security leak)
- ❌ No type annotations (<80% coverage)
- ❌ Test coverage <60% (insufficient testing)
- ❌ Multiple DBs with same schema (truth conflicts)
- ❌ Shell commands in health checks (slow/unreliable)

---

## 💡 Quick Reference

**Before declaring work "complete":**
1. Run full test suite: `pytest tests/ --cov`
2. Type check: `mypy src/` and `pyright src/`
3. Lint: `ruff check src/ --fix`
4. End-to-end test: Fresh install → feature works
5. Fill out quality scorecard (target: >90%)
6. Check for red flags (fix any immediately)

**"Code exists" ≠ "It works"** — Always verify with real data, real services, real measurements.

---

**Last Updated:** 2026-02-20
**Owner:** Surapat Ek-In (Arm)
**Next Review:** After completing 5 audits using this template
