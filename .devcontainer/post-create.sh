#!/bin/bash
# Post-create hook for VS Code Dev Container

set -e

echo "📦 Installing Python dependencies..."
curl -sSL https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"
pip install --upgrade pip uv
uv sync --all-packages --all-groups

echo "🔗 Installing pre-commit hooks..."
uv run pre-commit install --config devops/.pre-commit-config.yaml

echo "📚 Installing frontend dependencies..."
corepack enable && corepack prepare pnpm@10.33.0 --activate
cd projects/frontend
pnpm install --frozen-lockfile
cd ../..

echo "✅ Dev container ready!"
echo ""
echo "Quick commands:"
echo "  just install      # Full install (if needed)"
echo "  just run-backend  # Start FastAPI on port 8000"
echo "  just run-frontend # Start Next.js on port 3000"
echo "  just test         # Run pytest"
echo "  just lint         # Run all linters"
