# To install just use `uv tool install rust-just`

set dotenv-load

_default:
  @just --list

[group('install')]
install:
  uv sync --all-packages --all-groups
  uv run pre-commit install --config devops/.pre-commit-config.yaml
  cd projects/frontend && pnpm install --frozen-lockfile

[doc("Delete local dev artifacts (deps, build outputs, tool caches). Restore with just install")]
[group('install')]
clean:
  rm -rf .venv .mypy_cache .ruff_cache .pytest_cache .coverage htmlcov .pnpm-store
  rm -rf projects/frontend/node_modules projects/frontend/.next projects/frontend/coverage projects/frontend/tsconfig.tsbuildinfo

[doc("Start infra containers (Postgres)")]
[group('run')]
stack-up:
  docker compose up -d --wait

[group('run')]
stack-down:
  docker compose down

[doc("Apply database schema (idempotent)")]
[group('run')]
db-apply:
  PYTHONPATH=projects/backend uv run python -m coresat.db.apply

[group('run')]
run-backend:
  PYTHONPATH=projects/backend uv run uvicorn coresat.main:app --reload --host 127.0.0.1 --port 8000

[group('run')]
run-frontend:
  cd projects/frontend && pnpm run dev

[doc("Make sure the backend is running before generating")]
[group('generate')]
generate-frontend-types:
  cd projects/frontend && pnpm run api

[group('test')]
test: test-backend test-frontend

[group('test')]
test-backend *args:
  PYTHONPATH=projects/backend uv run pytest projects/backend/tests {{args}}

[group('test')]
test-frontend:
  cd projects/frontend && pnpm run test

[doc("Whole-repo pre-commit run: format, lint, typecheck, custom checks")]
[group('lint')]
lint:
  uv run pre-commit run --config devops/.pre-commit-config.yaml --all-files

[group('lint')]
format:
  uv run ruff check --fix projects/backend
  uv run ruff format projects/backend
  cd projects/frontend && pnpm run prettify && pnpm run lint:fix

[group('lint')]
typecheck:
  PYTHONPATH=projects/backend uv run mypy projects/backend/coresat
  uv run pyright projects/backend/coresat
  cd projects/frontend && pnpm run typecheck

[doc("The CI pipeline (GitHub Actions runs exactly this): pre-commit gate + tests + frontend build")]
[group('test')]
run-ci:
  uv sync --locked --all-packages --all-groups
  cd projects/frontend && pnpm install --frozen-lockfile
  just lint
  just test
  cd projects/frontend && NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 pnpm run build

[doc("One-shot project scaffold: bootstrap rename + install + de-templating checklist")]
[group('template')]
setup *args:
  uv run python devops/bootstrap.py {{args}}
  just install
  @uv run python devops/template_check.py || true
  @echo ""
  @echo "Scaffold ready. Next: just run-backend + just run-frontend, then work through the checklist above."

[doc("Rename template placeholders. Explicit args: --project-name ... --project-slug ... --python-package ... --non-interactive")]
[group('template')]
bootstrap *args:
  uv run python devops/bootstrap.py {{args}}

[doc("List remaining template remnants (brand strings + demo surface). Exit 0 when fully de-templated")]
[group('template')]
template-check:
  uv run python devops/template_check.py

[doc("FINAL de-templating step: wipe template git history into one clean initial commit. DESTRUCTIVE")]
[group('template')]
template-reset-history:
  #!/usr/bin/env bash
  set -euo pipefail
  BRANCH=$(git branch --show-current)
  echo "This permanently deletes ALL git history and tags on this clone."
  echo "The current working tree becomes a single 'Initial commit' on '$BRANCH'."
  read -p "Type 'reset' to continue: " CONFIRM
  if [ "$CONFIRM" != "reset" ]; then
    echo "Aborted."
    exit 1
  fi
  git checkout --orphan template-reset-tmp
  git add -A
  git commit -m "Initial commit"
  git branch -D "$BRANCH"
  git branch -m "$BRANCH"
  for t in $(git tag); do git tag -d "$t"; done
  echo
  echo "History reset: single initial commit on '$BRANCH'."
  echo "Point origin at the new project repo before pushing:"
  echo "  git remote set-url origin <new-repo-url>"
  echo "  git push --force --set-upstream origin $BRANCH"

[doc("Create and push a release tag. Leave version empty to auto-increment patch")]
[group('release')]
create-version $VERSION="":
  #!/usr/bin/env bash
  set -euo pipefail
  TAG_REGEX='^[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9]+)?$'
  if [ -z "$VERSION" ]; then
    LAST_TAG=$(git tag --sort=-version:refname | grep -E -m1 '^v[0-9]+\.[0-9]+\.[0-9]+$' || echo "v0.0.0")
    IFS='.' read -r MAJOR MINOR PATCH <<< "${LAST_TAG#v}"
    PATCH=$((PATCH + 1))
    VERSION="$MAJOR.$MINOR.$PATCH"
  fi

  if [[ ! "$VERSION" =~ $TAG_REGEX ]]; then
    echo "Invalid release version: '$VERSION'"
    echo "Expected format: X.Y.Z or X.Y.Z-SUFFIX"
    exit 1
  fi

  TAG="v$VERSION"
  echo
  git --no-pager log -1
  echo
  read -p "Do you want to create and push release '$TAG' for the commit above? (y/n): " CONFIRM

  if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
    git tag -a "$TAG" -m "Release $TAG"
    git push origin "$TAG"
    echo "Tag '$TAG' pushed to origin."
  fi
