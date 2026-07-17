# SYSTEMS_ENGINEER — Coding Profile

**Role:** Systems Engineer (Systematic Decomposition)
**Reference:** Analyzed from 108 commits (6-month analysis)
**Primary Focus:** API + Frontend + Core + Postprocessing
**Strength:** Feature decomposition, incremental deployment, event loop safety
**Analysis Date:** 2026-03-19

---

## 🎯 Coding Philosophy

A systems engineer approaches complex, multi-system features with **methodical decomposition**. This profile shows:
- Numbered series approach ("[X/N]" pattern for large features)
- Breaking large features into testable, independently deployable components
- Deep systems work (hardware integration, acquisition, threading)
- Post-processing pipelines (data transformation chains)
- Event loop optimization (non-blocking, async patterns)

**Principle:** "Break large problems into numbered increments; test & deploy each independently"

---

## 📊 Activity Profile

| Metric | Value |
|--------|-------|
| **Typical Commit Volume** | 100+ commits/6 months (High activity) |
| **Systems Touched** | 4 (API, frontend, core, postprocess) |
| **Avg Commit Size** | Medium-Large (features) |
| **Commit Pattern** | Numbered series ([X/N]) for complex work |

### Commit Categories

- **System Features (Numbered Series):** 35-40% ([X/N] increments)
- **Performance Optimization:** 20-25% (async/await, event loop, blocking)
- **Postprocessing:** 15-20% (data transformation, exports)
- **Bug Fixes:** 10-15% (edge cases, configuration)
- **Maintenance:** 5-10% (release notes, logging)

---

## 💻 Code Style & Patterns

### 1. Numbered Series Pattern

**The Key Pattern:** Break large features into numbered increments

```
[Feature Name 1/N] Infrastructure foundation
[Feature Name 2/N] Add caching optimization
[Feature Name 3/N] Compute only when needed
[Feature Name 4/N] Non-blocking I/O
[Feature Name 5/N] Flexible configuration
...
[Feature Name N/N] Activate and ship
```

**Why This Works:**
- Each increment is reviewable in isolation
- Can deploy/revert individual steps
- Testing is incremental (not all-or-nothing)
- Clear dependency chain visible to reviewers
- Feature completion date = last increment done

### 2. Problem-First Commits

**Pattern:** Each commit solves ONE problem, titled clearly

```
"Fix error in straylight power computation"
"Don't block the event loop when exporting images"
"Add pressure sensor support"
"Remove reference channel from illumination"
```

**Structure:** Problem → Solution, not feature name

### 3. Infrastructure-First Approach

**Order matters:**
1. Build abstractions first (classes, utilities)
2. Add non-blocking infrastructure (async, queues)
3. Then build features on top
4. Optimize performance along the way
5. Finally activate when all ready

**Pattern:**
```
[System Feature 1/N] Add required classes/abstractions
[System Feature 2/N] Cache expensive operations
[System Feature 3/N] Optimize computations
[System Feature 4/N] Non-blocking patterns
[System Feature 5/N] Configuration management
[System Feature 6/N] Enable the feature
```

### 4. Event Loop Awareness

Explicitly think about blocking:
- "Don't block the event loop when exporting images"
- Non-blocking I/O is infrastructure, not an afterthought
- Test non-blocking patterns early

---

## 🧪 Testing Strategy

**Approach:**
- Each numbered increment is tested independently
- Infrastructure (utilities, abstractions) tested first
- Performance optimizations verified before features
- Each step should pass tests before moving to next

### Test Pattern for Increments

```
For "[System Feature 3/N] Optimize computations":
├── Test: Computation is correct
├── Test: Is it faster? (measure)
├── Test: Does it work with other features?
└── Test: Edge cases handled
```

---

## 🏗️ Architectural Decisions

### Decision 1: Break Large Features into Increments

**Problem:** Need to add complex system without one giant, risky commit

**Solution:** 9-step series

```
[System 1/N] Infrastructure (foundation)
[System 2/N] Properties (cache, state)
[System 3/N] Optimization (compute only needed)
[System 4/N] Non-blocking (safe for async)
[System 5/N] Configuration (flexible control)
[System 6/N] Abstractions (introduce classes)
[System 7/N] State management (independent parts)
[System 8/N] Coordination (bring together)
[System 9/N] Activation (turn it on)
```

**Benefits:**
- Step 1-3: Foundation is solid
- Step 4: Performance guaranteed (no blocking)
- Step 5-8: Structure before complexity
- Step 9: Only activate when all ready

### Decision 2: Incremental Hardware Integration

**Pattern:** Add hardware support in discrete, testable steps

Each hardware feature adds:
- New capability
- Abstraction layer
- Configuration management
- Integration tests
- Documentation

### Decision 3: Event Loop Safety First

**Pattern:** Optimization happens before feature completion

Do this EARLY, not later:
- If you add blocking code, it's hard to remove
- Fix it early, test it thoroughly
- All future features inherit non-blocking pattern

---

## 📝 Commit Message Style

**Approach:** Problem title + brief description

```
[System Feature X/N] Problem being solved

Brief description of what this increment adds.
Why it's necessary for the complete feature.
Any new patterns or abstractions introduced.
```

**Examples:**
```
[Camera acquisition 4/N] Don't block the event loop when exporting images

Refactored image export to use async/await instead of blocking I/O.
This allows camera operations to continue while exports happen in background.

[System Feature 6/N] Introduce acquisition classes

Created AcquisitionController abstraction to manage state and coordinate
multiple background tasks. Simplifies testing and makes logic reusable.
```

---

## 🚀 Key Techniques

### Technique 1: Feature Decomposition

**How to decompose like a systems engineer:**

Take: "Add background camera acquisition"

Decompose into:
1. Infrastructure (can we capture in background?)
2. State management (track ongoing acquisition)
3. Performance (can we do it without blocking?)
4. Configuration (what can user control?)
5. Coordination (how does it talk to other systems?)
6. Activation (turn it on)

### Technique 2: Numbered Series Execution

**Steps:**
1. Design the series (1/N through N/N)
2. Each increment solves one problem
3. Use same prefix ("[Feature X/N]")
4. Increment from 1 to N
5. Final increment says "Activate" or "Enable"

### Technique 3: Performance-First Infrastructure

**Order:**
- [1/N] Infrastructure
- [2/N] Cache expensive operations
- [3/N] Compute only when needed
- [4/N] Don't block event loop
- Then features can safely use these patterns

---

## 🔒 Security Patterns

**Reference:** `reference/SECURITY_PATTERNS.md` (full patterns with code examples)

A systems engineer owns the middleware stack, bind addresses, and concurrency model — these are the surfaces where security misconfigurations are introduced. Apply these at infrastructure layer, before any feature work.

### Security Defaults (set at project start, never revisit)

| Setting | Secure Default | Why |
|---------|---------------|-----|
| Bind address | `127.0.0.1` | Never expose to network unintentionally |
| CORS origins | Explicit list | `*` raises `RuntimeError` at startup |
| Thread pool | `max_workers=N` (bounded) | Unbounded → OS thread exhaustion |
| DB connections | RLock wrapper | Shared connections are not thread-safe |
| Request body | 1 MB limit middleware | Prevents memory exhaustion before parsing |

### Middleware Stack Order

Register middleware in this order in `create_app()`:

```python
def create_app(settings: Settings) -> FastAPI:
    if "*" in settings.cors_origins:
        raise RuntimeError("CORS wildcard not allowed.")

    app = FastAPI()
    app.add_middleware(RequestSizeLimitMiddleware, max_bytes=1_048_576)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, ...)
    return app
```

### Concurrency Safety Rules

- **Orchestrators are singletons** — hold no per-request mutable state. Create a fresh state dataclass per request.
- **Shared DB connections** — wrap with `threading.RLock()`. Never call `.execute()` outside the lock.
- **Thread pool** — one `ThreadPoolExecutor(max_workers=settings.worker_threads)` at app startup. Never create one per request.
- **Event loop** — use `loop.run_in_executor(executor, fn, arg)` for all blocking I/O. Never call blocking code directly in an async handler.

### Error Information

Never return internal details in HTTP responses:

```python
# WRONG — leaks stack trace and SQL to client
raise HTTPException(detail=str(exc))

# RIGHT — generic client message, full detail in server log
logger.error("Query failed", exc_info=True)
raise HTTPException(status_code=500, detail="Query execution failed.")
```

Register a global exception handler in `create_app()` that returns `{"detail": "An internal error occurred."}` for all unhandled exceptions.

### .env File Rule

Agents MUST NEVER read `.env` files. Only `.env.example` is safe for agents to read or reference. Include this rule in every agent prompt that involves configuration files.

---

## 📋 Checklist: Code Like a Systems Engineer

- [ ] Break large feature into numbered increments ([X/N])
- [ ] Each increment is independently deployable
- [ ] Infrastructure (utilities, abstractions) comes before features
- [ ] Performance optimizations happen early (non-blocking, caching)
- [ ] Each commit solves ONE problem
- [ ] Test after each increment
- [ ] Configuration management before feature activation
- [ ] Use series prefix consistently
- [ ] Final increment is "Activate" or "Enable"
- [ ] Document dependency chain in PR/MR
- [ ] Bind address defaults to `127.0.0.1`
- [ ] CORS wildcard block in `create_app()`
- [ ] Request size limit middleware registered
- [ ] Request ID middleware registered
- [ ] Thread pool is bounded (`max_workers` set)
- [ ] Shared DB connections protected with `RLock`
- [ ] No internal error details in HTTP responses
- [ ] Global exception handler returns generic message

---

## 🔗 Real Examples from Codebase

See mono repo for working examples:
- [Camera acquisition 1/N] through [9/N] series
- Infrastructure-first approach to hardware integration
- Non-blocking I/O patterns implemented early
- Numbered series for large system features

---

**Profile Created:** 2026-03-19
**Based On:** 108+ commits over 6 months
**Confidence:** Very High (very consistent numbered series pattern)
**Use This For:** Engineers building large, complex features that need incremental rollout
