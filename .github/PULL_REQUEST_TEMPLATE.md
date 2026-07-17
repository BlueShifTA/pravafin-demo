## Summary

<!-- 1-3 bullets on what changed and why. Lead with the root cause if this is a bug fix. -->

## Changes

<!-- Bulleted list of concrete changes, grouped by file/module if long. -->

## Test plan

- [ ] `just lint` passes
- [ ] `just typecheck` passes
- [ ] `just test` passes (coverage ≥ 80%)
- [ ] Regression test added (if bug fix)
- [ ] Manual QA (describe briefly if UI/API change)

## Checklist

**Code quality**
- [ ] TDD followed (failing test committed before implementation)
- [ ] No unused functions, dead code, or unused imports
- [ ] No `print()` — use `logging`
- [ ] No `Any` unless justified with a comment
- [ ] Internal methods prefixed with `_`
- [ ] Type annotations on all new function signatures and `__init__` attributes

**Import/type hygiene**
- [ ] No `from __future__ import annotations`, `if TYPE_CHECKING:` blocks, wildcard imports
- [ ] No `dict[str, object]` / `dict[str, Any]` — use named TypedDicts
- [ ] No `NotRequired[X]` or `total=False` — use `X | None` for nullable fields
- [ ] JSON casts at the seam with bare type name (`cast(MyType, response.json())`)

**Design**
- [ ] SOLID principles satisfied (SRP/OCP/LSP/ISP/DIP) — see [`SOLID_PRINCIPLES.md`](../instruction/reference/SOLID_PRINCIPLES.md)
- [ ] No new module-level mutable service instances

**Tests**
- [ ] No tautological tests (isinstance-after-construction, callable-on-def, etc.)
- [ ] CLI tests use `CliRunner.invoke` or `subprocess.run`, not internal helpers
- [ ] Fixtures match real wire format (all TypedDict fields present)

**Refactor discipline (if this is a refactor)**
- [ ] Contract tests pinned before touching public-surface code
- [ ] LOC/complexity measured before and after
- [ ] Helper-extraction ROI verified (`helper_size < duplication × sites`)
- [ ] Defensive fallbacks preserved from old code

**Process**
- [ ] Pre-commit hooks passed — no `--no-verify`, no `SKIP=<hook>`
- [ ] Relevant docs updated (`CLAUDE.md`, `README.md`, or `instruction/`)

## Related

<!-- Issue numbers, related PRs, or design docs. -->
