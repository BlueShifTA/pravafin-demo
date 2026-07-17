"""Ban 'if TYPE_CHECKING:' import blocks.

TYPE_CHECKING guards hide circular import cycles rather than fixing them.
Move shared types to a leaf module that both sides import unconditionally.

AST-based: catches `if TYPE_CHECKING:`, `if typing.TYPE_CHECKING:`, and any
aliased form (`import typing as tp; if tp.TYPE_CHECKING:`).

See instruction/reference/PYTHON_STYLE.md for the full rationale.
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


def _is_type_checking_test(test: ast.expr) -> bool:
    # `if TYPE_CHECKING:` (however TYPE_CHECKING was imported or renamed)
    if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
        return True
    # `if typing.TYPE_CHECKING:` / `if tp.TYPE_CHECKING:` (any module alias)
    return isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"


def _find_violations(path: pathlib.Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and _is_type_checking_test(node.test):
            violations.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    return violations


def main() -> int:
    violations: list[str] = []
    for path in _iter_python_files():
        violations.extend(_find_violations(path))

    if violations:
        print(
            "ERROR: 'if TYPE_CHECKING:' blocks are banned (any alias, e.g. typing.TYPE_CHECKING)."
        )
        print("Move shared types to a leaf module both sides import unconditionally.")
        print("See instruction/reference/PYTHON_STYLE.md for rationale.")
        print("Violations:")
        for v in violations:
            print(f"  {v}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
