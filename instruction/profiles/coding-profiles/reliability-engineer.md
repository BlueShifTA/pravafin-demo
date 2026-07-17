# RELIABILITY_ENGINEER — Coding Profile

**Role:** Reliability Engineer (Hardware/Devices Focus)
**Reference:** Analyzed from 97 commits (6-month analysis)
**Primary Focus:** Devices + Core + API
**Strength:** Hardware reliability, graceful failure handling, retry logic
**Analysis Date:** 2026-03-19

---

## 🎯 Coding Philosophy

A reliability engineer is **resilience-focused**. This profile shows:
- Hardware reliability as a feature (retry logic, failure recovery)
- Graceful degradation (don't fail hard, fail smart)
- Performance optimization (startup speed, startup processes)
- Systematic testing (especially failure modes)
- Maintenance-first approach (monitoring, logging, alerts)

**Principle:** "Hardware is unreliable; write code to handle failures gracefully"

---

## 📊 Activity Profile

| Metric | Value |
|--------|-------|
| **Typical Commit Volume** | 95+ commits/6 months |
| **Systems** | Devices (primary) + Core + API |
| **Avg Commit Size** | Medium-Large |
| **Code Focus** | Reliability, recovery, monitoring |

### Commit Categories

- **Hardware Features:** 35-40% (pump modes, sensors, autosampler)
- **Reliability/Retry Logic:** 20-25% (timeout handling, reconnection)
- **Performance:** 15-20% (startup speed, caching, image processing)
- **Bug Fixes:** 15-20% (flaky tests, configuration, telemetry)
- **Maintenance:** 5-10% (release notes, firmware updates)

---

## 💻 Code Style & Patterns

### 1. Hardware Configuration Pattern

**Pattern:** Device-specific setup in dedicated modules

```
New device feature:
├── projects/devices/hardware_module.py  (abstraction)
├── projects/<PROJECT>/config/device.yaml (configuration)
├── projects/api/endpoints/device.py     (API exposure)
└── projects/devices/tests/test_hardware.py (tests)
```

**Each new device:**
- Hardware abstraction class
- Configuration file (YAML)
- API endpoint (if user-facing)
- Tests (including failure modes)

### 2. Retry Logic Pattern

**Pattern:** Exponential backoff + explicit reconnection

```python
def operation_with_retry():
    retry_count = 0
    max_retries = 3

    while retry_count < max_retries:
        try:
            hardware.command(operation)
            return
        except HardwareTimeout:
            retry_count += 1
            backoff_time = exponential_backoff(retry_count)  # 2s, 4s, 8s
            wait(backoff_time)
            reconnect()  # CRITICAL: Reconnect BEFORE retrying
        except FatalHardwareError:
            raise  # Don't retry fatal errors
```

**Key insight:** Reconnect BEFORE retry, not after

### 3. Failure Classification

**Pattern:** Different handling for different errors

```python
try:
    pump.send(command)
except PumpDisconnected:
    # Transient: retry with reconnection
    reconnect()
    retry(command)
except PumpTimeout:
    # Transient: retry with backoff
    wait_exponential_backoff()
    retry(command)
except PumpFatalError:
    # Fatal: don't retry, alert user
    alert_user("Hardware failed")
    shutdown()
```

### 4. Performance Optimization Pattern

**Pattern:** Measure → Profile → Optimize → Verify

```
"Speed up startup by pre-migrating database template"

Before: 5000ms (copy template, initialize, validate)
Analysis: DB initialization is slowest step
Solution: Pre-migrate template offline, copy on startup
After: 2000ms (just file copy + validation)
Improvement: 60% faster, measured and documented
```

---

## 🧪 Testing Strategy

**Approach:** Test normal AND failure modes

**Test categories:**
```
projects/devices/tests/
├── test_device_normal.py
│   ├── Test initialization
│   ├── Test normal commands
│   └── Test data collection
├── test_device_failures.py
│   ├── Test timeout recovery
│   ├── Test disconnect recovery
│   ├── Test reconnection logic
│   └── Test fatal error handling
└── fixtures/
    ├── mock_hardware.py (with injectable failures)
    └── failure_scenarios.py
```

**Key:** Mock hardware to trigger failure modes intentionally

### Failure Mode Testing

```python
def test_pump_timeout_recovery():
    """Test that pump timeout triggers retry with backoff"""
    mock_pump = MockPump()
    mock_pump.inject_failure(
        failure_type="timeout",
        fail_count=2,  # Fail twice, then succeed
        response_delay=100  # Slow response
    )

    result = operation_with_retry(mock_pump)

    assert mock_pump.retry_count == 2
    assert mock_pump.reconnect_called
    assert result == expected_value
```

---

## 🏗️ Architectural Decisions

### Decision 1: Hardware Abstraction Protocol

**Problem:** Multiple hardware types (pumps, sensors, samplers), each with different failure modes

**Solution:**
```python
class HardwareInterface:
    """Abstract interface all hardware must implement"""

    def send_command(cmd: str) -> Result:
        """Send command, handle timeouts/disconnects"""
        pass

    def reconnect() -> bool:
        """Restore connection"""
        pass

    def status() -> HardwareStatus:
        """Current state (connected, busy, error)"""
        pass

class PumpController(HardwareInterface):
    """Specific implementation for pump"""
    pass

class SensorController(HardwareInterface):
    """Specific implementation for sensor"""
    pass
```

**Benefits:**
- Consistent error handling across all hardware
- Easy to add new hardware types
- Tests use same interface

### Decision 2: Configuration-Driven Features

**Pattern:** Features in YAML, code reads it

```yaml
# projects/<PROJECT>/config/device01.yaml
hardware:
  pump:
    type: "peristaltic"
    address: 0x10
    can_interface: "primary"
    modes: ["standard", "boot", "pressure"]
    timeout_ms: 5000
    retry_attempts: 3

  pressure_sensor:
    enabled: true
    address: 0x20
    calibration: [0.0, 100.0]
```

**Code reads config and instantiates accordingly:**
- New device modes → just YAML change
- Feature disabled by default
- Enable after testing
- Easy rollback (edit YAML, no code deploy)

### Decision 3: Monitoring is Built-In

**Pattern:** Every hardware operation logs and metrics

```python
def pump_command(operation):
    start_time = now()
    try:
        result = pump.send(operation)
        duration_ms = now() - start_time
        log.info(f"Pump command success: {operation}, {duration_ms}ms")
        metrics.record("pump.command.success", duration_ms)
        return result
    except PumpError as e:
        duration_ms = now() - start_time
        log.error(f"Pump command failed: {operation}, {e}")
        metrics.record("pump.command.failed", duration_ms, {"error": str(e)})
        raise
```

---

## 📝 Commit Message Style

**Approach:** Action + what it affects + outcome

```
[Action] [Component] — [Outcome]

"Fix CAN multiplexer warnings for pump boot mode"
"Speed up measurement startup by pre-migrating database"
"Add Pressure Sensor Support"
"Improve image registration for spike reduction"
```

---

## 🚀 Key Techniques

### Technique 1: Hardware Abstraction

One class per hardware type:

```python
class PumpController:
    """Abstracts pump communication (CAN/serial)"""
    def __init__(config):
        self.can = CANInterface(config.address)

    def send_command(cmd):
        try:
            self.can.send(cmd)
        except CANTimeout:
            self.reconnect()
            retry()

class PressureSensor:
    """Abstracts pressure sensor (ADC/I2C)"""
    def read():
        value = adc.read()
        if not in_valid_range(value):
            alert_user()
        return value
```

### Technique 2: Explicit Failure Recovery

**Pattern:**
- Categorize failures (transient vs. fatal)
- Transient → retry with backoff + reconnect
- Fatal → alert and shutdown
- Never silent failures

### Technique 3: Performance Profiling

**Workflow:**
1. Identify slow operation (startup, I/O, processing)
2. Profile to find bottleneck
3. Optimize (caching, pre-migration, batching)
4. Measure improvement
5. Document result

### Technique 4: Test Failure Modes

**Approach:**
- Mock hardware with injectable failures
- Test timeout recovery
- Test disconnect recovery
- Test fatal error handling
- Run all failure tests in CI

---

## 🔒 Security & Reliability Patterns

**Reference:** `reference/SECURITY_PATTERNS.md` (full patterns with code examples)

Reliability and security are intertwined: thread exhaustion, resource leaks, and unbounded growth are both correctness failures and attack surfaces. A reliability engineer addresses both.

### Thread Safety

**Bounded thread pools** — Create one `ThreadPoolExecutor(max_workers=N)` at startup. Never create per-request executors; they exhaust OS thread limits under load.

```python
from concurrent.futures import ThreadPoolExecutor

# At app startup — one shared pool
executor = ThreadPoolExecutor(max_workers=settings.worker_threads)

# In async handlers
result = await loop.run_in_executor(executor, blocking_hardware_call, args)
```

**Shared resource locking** — Any resource accessed from multiple threads (DB connection, hardware channel, counter) needs a lock:

```python
import threading

class HardwareBackend:
    def __init__(self) -> None:
        self._conn = open_hardware_channel()
        self._lock: threading.RLock = threading.RLock()

    def send_command(self, cmd: str) -> str:
        with self._lock:
            return self._conn.send(cmd)
```

**Fresh state per request** — Service objects that are singletons must hold no per-request mutable state. Create a fresh state dataclass for each operation.

### Resource Leak Prevention

- Use context managers for all file handles, DB connections, and network sockets: `with sqlite3.connect(path) as conn:`
- Set explicit timeouts on all external calls (HTTP, hardware I/O, LLM). Without timeouts, one slow client blocks a thread indefinitely.
- Use `asyncio.Queue(maxsize=512)` for SSE/streaming queues. Unbounded queues exhaust memory when producers outpace consumers.
- On SSE connections, enforce a wall-clock deadline (e.g. 300s). Kill connections that exceed it.

### Error Disclosure

Never return internal implementation details in client-facing error messages. Full context goes to server logs only:

```python
try:
    result = hardware.read()
except HardwareError:
    logger.error("Hardware read failed", exc_info=True)  # full detail in logs
    return {"error": "Sensor read failed."}              # generic to client
```

### Monitoring and Observability

Attach a request ID to every operation log so failures can be traced:

```python
logger.info(
    "Hardware command sent",
    extra={"request_id": request_id, "command": cmd, "duration_ms": elapsed},
)
# NEVER log: patient names, credentials, API keys, raw PII
```

---

## 📋 Checklist: Code Like a Reliability Engineer

- [ ] Hardware abstraction layer (one class per device type)
- [ ] Configuration in YAML (features disabled by default)
- [ ] Retry logic with exponential backoff
- [ ] Reconnect BEFORE retry (not after)
- [ ] Classify failures (transient vs. fatal)
- [ ] Different handling for each failure type
- [ ] Test failure modes (not just happy path)
- [ ] Mock hardware to trigger failures intentionally
- [ ] Measure performance improvements
- [ ] Monitor all operations (logging + metrics)
- [ ] Never silent failures (always alert or log)
- [ ] Thread pool bounded (`max_workers` set, created once at startup)
- [ ] Shared resources protected with `RLock`
- [ ] Fresh state per request (no per-request mutation on singletons)
- [ ] All connections use context managers (no resource leaks)
- [ ] All external calls have explicit timeouts
- [ ] SSE/streaming queues have `maxsize` set
- [ ] Error responses return generic messages (full detail in logs only)
- [ ] Request IDs attached to all log lines

---

## 🔗 Real Examples from Codebase

See mono repo for working examples:
- Hardware abstraction for pumps, sensors, samplers
- Retry logic with exponential backoff
- Configuration-driven feature management
- Comprehensive failure mode testing
- Performance optimization with measurement

---

**Profile Created:** 2026-03-19
**Based On:** 97+ commits over 6 months
**Confidence:** High (very consistent reliability-first pattern)
**Use This For:** Engineers building hardware integrations, distributed systems, or any critical-path code
