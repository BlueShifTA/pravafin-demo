"""Deterministic de-templating check.

Scans the repo for everything still template-related and prints a checklist
with file:line locations. Exit 1 while remnants remain, 0 when the project is
fully de-templated — so it can be used as a gate.

Two kinds of remnants:
1. Brand strings bootstrap should have replaced ("Project Template",
   "project-template", backend package still named "package").
2. Demo surface that must be replaced or deleted by hand (example route,
   demo components, example profile).
"""

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

# These contain the template markers as data, not as remnants — and generated
# client output is rewritten by Orval after the backend is renamed.
SELF_FILES = (
    "devops/template_check.py",
    "devops/bootstrap.py",
    "projects/frontend/src/lib/generated/",
)

BRAND_STRINGS = (
    "Project Template",
    "project-template",
    "Minimal Startup Template",
)

# (path, what to do with it)
DEMO_SURFACE = (
    ("projects/backend/package", "backend package still named 'package' — run `just bootstrap`"),
    ("projects/backend/*/api/example.py", "demo route POST /api/example/echo — replace or delete"),
    ("projects/backend/tests/test_example.py", "demo route test — replace or delete"),
    ("projects/frontend/src/components/demo", "demo homepage components — replace or delete"),
    ("instruction/profiles/surapat", "example personal profile — replace with your own or delete"),
)


def _grep_brand_strings() -> list[str]:
    hits: list[str] = []
    for needle in BRAND_STRINGS:
        result = subprocess.run(
            ["git", "grep", "-n", "--fixed-strings", needle],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        for line in result.stdout.splitlines():
            if line.startswith(SELF_FILES):
                continue
            hits.append(f"{line.split(':', 2)[0]}:{line.split(':', 2)[1]}  contains '{needle}'")
    return hits


def _find_demo_surface() -> list[str]:
    found: list[str] = []
    for pattern, action in DEMO_SURFACE:
        if any(ROOT.glob(pattern)):
            found.append(f"{pattern}  — {action}")
    return found


def main() -> int:
    brand_hits = _grep_brand_strings()
    demo_hits = _find_demo_surface()

    if not brand_hits and not demo_hits:
        print("template-check: OK — no template remnants found.")
        return 0

    if brand_hits:
        print("Template brand strings still present (run `just bootstrap`, then fix leftovers):")
        for hit in brand_hits:
            print(f"  {hit}")
        print()
    if demo_hits:
        print("Template demo surface still present (replace or delete by hand):")
        for hit in demo_hits:
            print(f"  {hit}")
        print()
    print("Also update CLAUDE.md and README.md to describe the real project.")
    print(f"{len(brand_hits) + len(demo_hits)} remnant(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
