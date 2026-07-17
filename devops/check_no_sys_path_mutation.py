"""Ban in-source sys.path mutation hacks.

This check intentionally detects common direct call patterns only:
- sys.path.insert/append/extend(...)
- import sys as s; s.path.insert/append/extend(...)
- from sys import path as p; p.insert/append/extend(...)

Non-goals (may be added later if needed):
- Deep alias/data-flow tracking (e.g. x = sys.path; x.insert(...))
- sys.path[...] = ... assignments

Allowed exception (current repo default):
- docs/conf.py (Sphinx config currently adjusts sys.path)
"""

import ast
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = ("projects", "devops", "docs")
ALLOWLIST = {Path("docs/conf.py")}
DISALLOWED_METHODS = {"insert", "append", "extend"}
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".next",
}


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    col: int
    method: str

    def format(self) -> str:
        return (
            f"{self.path}:{self.line}:{self.col}: "
            f"banned sys.path.{self.method}(...) mutation. "
            "Use proper package installs/editable installs, or set PYTHONPATH in tooling "
            "(not in source files)."
        )


def iter_python_files() -> list[Path]:
    files: list[Path] = []
    for root_name in SCAN_ROOTS:
        root = ROOT / root_name
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            rel = path.relative_to(ROOT)
            if rel in ALLOWLIST:
                continue
            files.append(path)
    return sorted(files)


def collect_aliases(tree: ast.AST) -> tuple[set[str], set[str]]:
    sys_aliases: set[str] = set()
    path_aliases: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "sys":
                    sys_aliases.add(alias.asname or "sys")
        elif isinstance(node, ast.ImportFrom) and node.module == "sys":
            for alias in node.names:
                if alias.name == "path":
                    path_aliases.add(alias.asname or "path")

    return sys_aliases, path_aliases


def _attr_chain_matches_sys_path_call(
    call: ast.Call,
    sys_aliases: set[str],
    path_aliases: set[str],
) -> str | None:
    func = call.func
    if not isinstance(func, ast.Attribute):
        return None
    if func.attr not in DISALLOWED_METHODS:
        return None

    target = func.value
    if isinstance(target, ast.Name) and target.id in path_aliases:
        return func.attr

    if not isinstance(target, ast.Attribute) or target.attr != "path":
        return None
    if not isinstance(target.value, ast.Name):
        return None
    if target.value.id not in sys_aliases:
        return None
    return func.attr


def check_file(path: Path) -> tuple[list[Violation], str | None]:
    rel = path.relative_to(ROOT)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return [], f"{rel}:1:1: failed to decode file as UTF-8: {exc}"

    try:
        tree = ast.parse(text, filename=str(rel))
    except SyntaxError as exc:
        line = exc.lineno or 1
        col = (exc.offset or 1) - 1
        return [], f"{rel}:{line}:{max(col, 0)}: failed to parse Python file: {exc.msg}"

    sys_aliases, path_aliases = collect_aliases(tree)

    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        method = _attr_chain_matches_sys_path_call(node, sys_aliases, path_aliases)
        if method is None:
            continue
        violations.append(
            Violation(
                path=rel,
                line=getattr(node, "lineno", 1),
                col=getattr(node, "col_offset", 0),
                method=method,
            )
        )
    return violations, None


def main() -> int:
    files = iter_python_files()
    errors: list[str] = []
    violations: list[Violation] = []

    for path in files:
        file_violations, parse_error = check_file(path)
        if parse_error is not None:
            errors.append(parse_error)
            continue
        violations.extend(file_violations)

    if errors:
        print("check_no_sys_path_mutation: parse/decode errors")
        for error in errors:
            print(error)
        return 2

    if violations:
        print("check_no_sys_path_mutation: found banned sys.path mutations")
        for violation in sorted(violations, key=lambda v: (str(v.path), v.line, v.col)):
            print(violation.format())
        print(f"\n{len(violations)} violation(s) found.")
        return 1

    print(
        "check_no_sys_path_mutation: OK "
        f"({len(files)} files scanned, allowlisted: {', '.join(str(p) for p in sorted(ALLOWLIST))})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
