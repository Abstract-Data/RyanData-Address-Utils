#!/bin/bash
# Script to resolve conflicts in PR #2 (copilot/sub-pr-1)
# This applies the improvements from PR #2 to the split workflow structure

set -e

echo "Resolving conflicts in PR #2 (copilot/sub-pr-1)..."

# Checkout the PR branch
git checkout copilot/sub-pr-1

# Reset to the original state before any merge attempts
echo "Resetting branch to clean state..."
if git reset --hard origin/copilot/sub-pr-1 2>/dev/null; then
    echo "Reset to origin/copilot/sub-pr-1"
else
    echo "Warning: Could not reset to origin, using current HEAD"
    git reset --hard HEAD
fi

# Merge the base branch
echo "Merging ci/add-github-workflows..."
if ! git merge ci/add-github-workflows --no-commit --no-ff; then
    echo "Merge conflicts detected (expected). Proceeding with resolution..."
    
    # Verify conflicts exist
    CONFLICTS=$(git diff --name-only --diff-filter=U)
    if [ -z "$CONFLICTS" ]; then
        echo "Error: Expected conflicts but none found. Aborting."
        git merge --abort 2>/dev/null || true
        exit 1
    fi
    echo "Conflicted files: $CONFLICTS"
else
    echo "Error: Merge completed without conflicts. This is unexpected. Aborting."
    git reset --hard HEAD~1
    exit 1
fi

# Remove the conflicted ci.yml file if it exists
echo "Removing conflicted ci.yml..."
if [ -f .github/workflows/ci.yml ]; then
    git rm .github/workflows/ci.yml
else
    # File might already be staged for deletion
    git rm --cached .github/workflows/ci.yml 2>/dev/null || echo "ci.yml already removed"
fi

# The new workflow files were added by the merge, now we need to enhance them
# Add permissions and caching to lint.yml
cat > .github/workflows/lint.yml << 'EOF'
name: Ruff

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"
          enable-cache: true

      - name: Set up Python
        run: uv python install 3.12

      - name: Install dependencies
        run: uv sync --group dev

      - name: Run Ruff check
        run: uv run ruff check src/ tests/

      - name: Run Ruff format check
        run: uv run ruff format --check src/ tests/
EOF

# Add permissions and caching to typecheck.yml
cat > .github/workflows/typecheck.yml << 'EOF'
name: Mypy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  typecheck:
    name: Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"
          enable-cache: true

      - name: Set up Python
        run: uv python install 3.12

      - name: Install dependencies
        run: uv sync --group dev

      - name: Run Mypy
        run: uv run mypy src/
EOF

# Add permissions, caching, and Python matrix to tests.yml
cat > .github/workflows/tests.yml << 'EOF'
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  test:
    name: Pytest - Python ${{ matrix.python-version }}
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"
          enable-cache: true

      - name: Set up Python
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --group dev --all-extras

      - name: Run tests
        run: uv run pytest tests/ -v --tb=short
EOF

# Stage all changes
git add .

# Commit the resolution
git commit -m "Resolve merge conflict: Apply PR #2 improvements to split workflow files

- Replaced single ci.yml with split workflows (lint.yml, typecheck.yml, tests.yml)
- Applied improvements from original PR #2:
  - Added enable-cache: true for uv setup in all workflows
  - Added permissions: contents: read to all workflows
  - Added Python version matrix (3.12, 3.13) to test workflow
  - Updated test job name to include Python version"

# Push the resolved branch
git push origin copilot/sub-pr-1

echo "PR #2 conflicts resolved and pushed successfully!"
