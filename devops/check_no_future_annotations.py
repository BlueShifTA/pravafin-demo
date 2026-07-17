"""Ban 'from __future__ import annotations' in Python 3.14+ code.

Python 3.14 is the project baseline. Modern union syntax (list[str] | None,
X | None) works natively. The future import is unnecessary and banned.

AST-based: catches the import regardless of formatting or aliasing.
"""

import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

SEARCH_DIRS = [
    ROOT / "projects",
    ROOT / "devops",
]

EXCLUDE_DIRS = {".venv", "__pycache__", "node_modules", ".git"}


def _iter_python_files() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for search_dir in SEARCH_DIRS:
        for path in search_dir.rglob("*.py"):
            if any(part in EXCLUDE_DIRS for part in path.parts):
                continue
            files.append(path)
    return sorted(files)


def _find_violations(path: pathlib.Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "__future__"
            and any(alias.name == "annotations" for alias in node.names)
        ):
            violations.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    return violations


def main() -> int:
    violations: list[str] = []
    for path in _iter_python_files():
        violations.extend(_find_violations(path))

    if violations:
        print("ERROR: 'from __future__ import annotations' is banned (Python 3.14+ baseline).")
        print("Remove it and use native syntax: list[str] | None, X | None.")
        print("Violations:")
        for v in violations:
            print(f"  {v}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
