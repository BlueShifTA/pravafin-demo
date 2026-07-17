# Refactor Discipline & Test Design Rules

Full reference for the refactor and testing rules summarized in `CLAUDE.md`.

## Refactor Discipline — Mandatory

A refactor is a change that preserves behavior while improving a measurable property (LOC, complexity, type safety, test coverage, performance). These rules exist because **"simpler" is a claim that must be backed by evidence**, not a vibe.

### Pin the contract before refactoring

Before any refactor that touches a consumed surface — public API, CLI, exit codes, return shapes, stderr text, external message formats, anything a caller branches on — write functional tests that capture the **current observed behavior**, not the intended behavior. Land them as a separate commit BEFORE touching the code under refactor.

```bash
# Step 0 of every refactor: pin the contract
git checkout -b refactor/foo
# Write contract tests that pin observed behavior
just test   # all green
git commit -m "test: pin <surface> contract"
# Only NOW start the actual refactor
```

Every iteration's verification gate runs the contract tests. A refactor that breaks a contract test is rejected on the spot, not justified with a prose explanation.

### Measure the metric you're selling

If a refactor is sold as "simpler", "smaller", "faster", or "more maintainable", measure that metric at **every iteration**, not just at the end.

```bash
wc -l src/**/*.py            # before any iteration
wc -l src/**/*.py            # after each iteration — compare to baseline
```

If the metric moves the wrong direction, **name the trade-off upfront** and get explicit sign-off before continuing. A refactor that silently grows LOC by 30 % while the author talks about "cleaner structure" is a process failure, even if every individual change is defensible. When growing LOC is the correct call (e.g. trading brevity for type safety), say so in the commit message: `+N lines, traded brevity for X`.

### Extract only when the helper is smaller than the duplication

Before extracting a shared helper, compute the ROI:

```
helper_size_lines  <  per_site_duplication_lines  ×  number_of_sites
```

Example: three call sites each duplicate 5 lines = 15 lines of duplication. A 40-line shared helper is a **25-line loss** even though it "removes duplication". Keep the duplication unless the helper pays for itself at today's call-site count — not at hypothetical future call sites.

### Preserve defensive fallbacks

When the old code has a defensive branch (`if isinstance(x, int) else fallback`, `.get(key) or default`, `try/except SpecificError: return sentinel`), preserve **every branch** in the refactor — not just the happy path.

```python
# WRONG — "equivalent" refactor collapses the fallback
def _extract_total(body: Response) -> int:
    return body["meta"]["page"]["total_count"]   # KeyErrors on real wire data

# CORRECT — every old branch survives
def _extract_total(body: Response, fallback: int) -> int:
    meta = body.get("meta")
    if meta is None:
        return fallback
    page = meta.get("page")
    if page is None:
        return fallback
    total = page.get("total_count")
    if total is None:
        return fallback
    return total
```

The old fallbacks exist for reasons you cannot see from inside the refactor. Adversarial review (next rule) is the backup when you're wrong about which branches are unreachable.

### Adversarial review per iteration, not once at the end

After every iteration's verification gate passes, run an adversarial review from an agent that did NOT write the code — Codex, a second Claude session, or a human reviewer. Findings are to-fix items, not suggestions. Ignore only with a written reason in the commit message.

Reviewing once at the end misses regressions that stacked across iterations. Per-iteration review catches them while the change is still small enough to revert cheaply.

### Never skip the verification gate

`just lint && just typecheck && just test` must all pass on the current working tree before every commit. **Never** use `--no-verify`, `git commit --no-verify`, `SKIP=<hook>`, or any other bypass. If a pre-commit hook fails, fix the root cause — don't route around it.

### Present alternatives at the plan stage

When a refactor has two reasonable directions (e.g. "shared helper vs. inline at each site", "TypedDict vs. Protocol", "per-kind union vs. single shape"), present BOTH at the plan stage and let the user pick. Don't commit to a direction unilaterally. Guessing costs 30 minutes of rework when the user disagrees; asking costs 10 seconds.

## Test design rules — what a test must prove

Every test must exercise a real code path whose failure would cause a real bug. Before writing a test, answer: **what line of production code would have to break for this test to fail?** If the answer is "none, just a type rename", the test is tautological and must be deleted or rewritten.

**Functional tests only.** Every test must exercise a real code path through its public interface and assert on observable behavior (return value, HTTP response, rendered DOM text, exit code, side effect). Tests of structure — "component is a function", "class has method X", "the signature accepts parameter Y" — are banned. If a test fails, production code must have broken; if renaming a type can break the test, the test is structural, not functional.

- **Backend** — call the endpoint/function and assert on the response body, status code, or observable side effect (e.g. row in DB, log line, event emitted). Prefer `TestClient` / `CliRunner` / real function invocation over poking internals.
- **Frontend** — render the component with its real providers (React Query, theme) and assert on the user-facing DOM (text, roles, aria labels). Never assert on state hooks, prop types, or implementation details.

### Banned test shapes

```python
# WRONG — isinstance check right after construction is trivially true
def test_foo_is_foo() -> None:
    f = Foo(x=1)
    assert isinstance(f, Foo)   # BANNED — constructor already proves this

# WRONG — callable check on a def-declared function
def test_fn_is_callable() -> None:
    assert callable(my_function)   # BANNED — def makes it callable

# WRONG — parametrize over a set and assert membership in the same set
@pytest.mark.parametrize("status", ["ok", "error"])
def test_status_in_enum(status: str) -> None:
    assert status in {"ok", "error"}   # BANNED — tautology

# WRONG — inspect.signature to check a parameter exists
def test_has_param() -> None:
    sig = inspect.signature(fn)
    assert "key" in sig.parameters   # BANNED — call fn(key=...) instead

# WRONG — assert issubclass on a dataclass hierarchy you just defined
def test_error_is_value_error() -> None:
    assert issubclass(MyError, ValueError)   # BANNED — class shape, not behavior
```

### Required test shapes

- **CLI tests go through the test runner.** `CliRunner.invoke` (click) or `subprocess.run`. Never bypass to internal helpers. The exit code, stdout, and stderr are the contract — only end-to-end invocation proves it.
- **Fixtures must match the real wire format** of whatever external API they simulate. Include every field the TypedDict declares (with `None` where null). A fixture that omits a required field is lying about what the cast accepts.
- **Mock objects used as context managers must configure `__enter__` / `__exit__` explicitly.** `mock.__enter__.return_value = mock` — otherwise `with fake as inner:` yields a different mock than the one the test configured.
- **Before monkeypatching, trace the execution order inside the target function.** A guard injected at call position 2 doesn't catch things that happen at position 3+. Read the source of the function under test before writing the patch.
- **Contract tests BEFORE refactor.** Before touching any code that produces exit codes, JSON shapes, stderr phrases, or error messages an external caller branches on, write functional tests that pin the CURRENT observed behavior under its own commit (see Refactor Discipline above).

### Coverage targets

- Core business logic: 95%+ (CRUD, auth, domain models)
- API routes: 90%+ (all status codes, validation errors, edge cases)
- Services: 85%+ (including failure modes)
- Frontend components: cover each rendered state (loading, error, success, empty) via DOM assertions
- **Minimum floor: 80%** — no PR merges below this (enforced by `just run-ci`)

### Test priority order

1. Error paths and edge cases FIRST (these break in production)
2. Happy path second
3. Regression test required for every bug fix
