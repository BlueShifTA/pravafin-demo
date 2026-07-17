# Surapat Ek-In (Arm) — Coding Profile

**Generated:** 2026-02-20 12:27 CET
**Author commits analyzed:** 100+ commits

> **Note:** General coding rules (imports, type annotations, naming, exception handling, dataclasses, protocols, async, retry, logging, commit format) are enforced in the root [CLAUDE.md](../../../CLAUDE.md). This profile documents personal domain knowledge, hardware-specific patterns, and preferences beyond the shared rules.

---

## Who is Arm?

**Full Stack Scientist-Engineer** specializing in scientific instrumentation, embedded systems, and real-time control software. Primary focus: optical biosensor systems with nanometer-precision control.

**Technical Stack:**
- **Languages:** Python 3.13 (primary), TypeScript (frontend), Bash (automation)
- **Frameworks:** FastAPI, Next.js, Ansible, Playwright
- **Hardware:** NVIDIA Jetson Orin, embedded cameras (Spinnaker SDK), lasers, optical systems
- **DevOps:** Docker, GitLab CI, Ansible deployment, just task runner
- **Domain:** Real-time image acquisition, PID control, optical alignment, biosensor measurement

---

## Hardware-Specific Patterns

### Retry & Error Recovery for Hardware

```python
@with_camera_retry
async def capture_image(self) -> CameraImage:
    """Decorator-based retry with exponential backoff."""
    # Auto-reset camera on failure
    # Max retries from CameraConstants.MAX_ATTEMPTS
```

**Strategy:**
- Hardware operations wrapped in retry decorators
- Exponential backoff between retries
- Automatic device reset on specific error codes
- Log warnings on retry, raise on final failure

### LoggingHelper Mixin

```python
class LoggingHelper:
    """Mixin providing self.logger to all classes."""
    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)

# Usage:
self.logger.warning("Camera retry %d/%d", attempt, max_retries, exc_info=True)
```

### Hardware Constants Pattern

```python
@dc.dataclass
class CameraConstants:
    """Centralized constants for camera operations."""
    MAX_ATTEMPTS: int = 3
    ATTEMPT_RETRY_DELAY: float = 2.0
    DEFAULT_EXPOSURE: float = 0.1
```

---

## Development Workflow

### 1. Research Phase
Identify affected files, understand dependencies:
```bash
fd -e py <pattern>
rg "class ProcessBase" -t py
git log --oneline -- path/to/file.py
```

### 2. Plan Phase
Outline approach in comments or scratch file:
```python
# TODO:
# 1. Add retry logic to camera.capture()
# 2. Extract MAX_ATTEMPTS to CameraConstants
# 3. Add regression test for [-1008] error code
```

### 3. Execute Phase
Write code following conventions:
```bash
uv run ruff format .
uv run ruff check --fix .
```

### 4. QA Phase
```bash
uv run pyright
uv run mypy -- .
uv run pytest tests -k test_camera_retry
uv run pre-commit run --all-files
git commit -m "Add retry logic to camera capture with regression test"
```

---

## Tool Usage (Arm's Projects)

### Just (Task Runner)
```bash
just install           # Install deps (uv + pnpm)
just run-hub           # Start hub server (port 5001)
just run-reader        # Start reader server (port 5003)
just run-frontend      # Start Next.js dev (port 3000)
just test <CORE_PROJECT>         # Run tests for projects/<CORE_PACKAGE>
just lint              # Run pre-commit on all files
```

**Port prefix support:** Set `PORT_PREFIX=6` -> hub runs on 6001, frontend on 6000.

### Ruff (Arm's Extended Rule Set)

**Enabled rules:** F, W, E, N, RET, SLF, G, I, PLR, UP, SIM, B, RUF, TRY, ARG, LOG, ASYNC, BLE, DTZ

**Ignored:** E501 (line length), PLR2004 (magic values), TRY003 (verbose exception)

---

## Repository Structure (Arm's Projects)

```
<REPO>/
├── AGENTS.md                    # AI assistant instructions
├── .claude/                     # Claude Code config
│   ├── hooks/format_code.py     # Post-edit auto-format hook
│   ├── settings.json            # Hook configuration
│   └── skills/                  # Custom skills (jira, remote-logs)
├── .devcontainer/               # VS Code Dev Container setup
├── devops/                      # CI, docs build, firmware scripts
├── projects/                    # Workspace structure
│   ├── api/                     # FastAPI services (hub, reader, auth)
│   ├── <CORE_PACKAGE>/          # Core business logic (processline, acquisition)
│   ├── devices/                 # Hardware drivers (camera, sensors)
│   ├── experiments/             # Experiment configuration
│   ├── postprocess/             # Data analysis & plotting
│   ├── deploy/                  # Ansible playbooks
│   └── frontend/                # Next.js UI (static export)
├── docs/                        # Docusaurus documentation
├── justfile                     # Task runner commands
├── pyproject.toml               # Workspace config (uv + ruff)
└── uv.lock                      # Dependency lockfile
```

---

## Deployment & Infrastructure

### Ansible Deployment
```bash
cd projects/deploy/<DEPLOY_PROJECT>
./deploy.yml -i inventory/machine.cfg -e version="1.2.3"
```

### Docker
```bash
docker build -f devops/backend.dockerfile -t <REPO>:local .
```

### Dev Container Setup
- **Base image:** Custom Dockerfile with Python 3.13, system deps
- **Privileged mode:** Hardware access (cameras, GPIO)
- **Network:** Host networking for inter-service communication
- **Mounts:** `/dev`, config files, data directory

---

## AI Assistant Instructions

**When helping Arm with code:**

1. **Hardware awareness:**
   - Camera operations need retry logic
   - Optical systems = nanometer precision
   - Real-time control = timing critical
   - Embedded systems = resource constraints

2. **Domain knowledge:**
   - Processline = async pipeline framework
   - Reader = optical measurement instrument
   - Coupling = laser beam alignment
   - Aperture = optical element for beam shaping

3. **Respect workflow:** Research -> Plan -> Execute -> QA

---

## Code Review Checklist

- Check unused functions: remove any functions no longer called
- Check typing: proper type annotations, avoid `Any`, no `TYPE_CHECKING` guards
- Check private methods: prefix internal methods with `_`
- Check logging/print: remove debug `print()`, use proper logging
- Check import sanity: imports at module level, no unused imports
- Docstrings for public API
- Regression tests for bug fixes
- Pre-commit hooks pass
- No TODOs in committed code

---

## Gaps to Close

1. **Test Coverage Metrics:** Add `coverage` to CI pipeline, set minimum thresholds
2. **API Documentation:** Add API versioning strategy (URL path or headers)
3. **Performance Profiling:** Add `py-spy` or `scalene` for production profiling
4. **Error Telemetry:** Consider Sentry integration for production errors
5. **Dependency Security:** Add `safety` or `pip-audit` to pre-commit

---

## Usage Examples

### Example 1: Hardware Retry Pattern
```python
from <DEVICES_PACKAGE>.camera import with_camera_retry

class MyCamera(CameraBase):
    @with_camera_retry
    async def custom_capture(self, exposure: float) -> CameraImage:
        """Capture with automatic retry on failure."""
        return await self._hardware_capture(exposure)
```

### Example 2: Error Message Mapping
```python
@dc.dataclass
class ErrorInstruction:
    def _get_instructions(self) -> dict[str, str]:
        return {
            MyException.MESSAGE: "User-friendly instruction here.",
            "[-1008]": "Camera reset required, check connections.",
        }
```

---

**Last Updated:** 2026-02-20
**Owner:** Surapat Ek-In (Arm)
**Next Review:** When Arm onboards new team member or AI assistant
