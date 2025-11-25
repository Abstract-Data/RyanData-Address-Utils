#!/bin/bash
# Script to resolve conflicts in PR #4 (copilot/sub-pr-1-another-one)
# This applies the composite action approach to the split workflow structure

set -e

echo "Resolving conflicts in PR #4 (copilot/sub-pr-1-another-one)..."

# Checkout the PR branch
git checkout copilot/sub-pr-1-another-one

# Merge the base branch
git merge ci/add-github-workflows || true

# Remove the conflicted ci.yml file
git rm .github/workflows/ci.yml

# Create the composite action directory
mkdir -p .github/actions/setup-python-uv

# Create the composite action with enhancements (caching + python-version parameter)
cat > .github/actions/setup-python-uv/action.yml << 'EOF'
name: Setup Python with uv
description: Set up Python environment using uv package manager

inputs:
  install-extras:
    description: 'Whether to install all extras with dependencies'
    required: false
    default: 'false'
  python-version:
    description: 'Python version to install'
    required: false
    default: '3.12'

runs:
  using: composite
  steps:
    - uses: actions/checkout@v4

    - name: Install uv
      uses: astral-sh/setup-uv@v4
      with:
        version: "latest"
        enable-cache: true

    - name: Set up Python
      shell: bash
      run: uv python install ${{ inputs.python-version }}

    - name: Install dependencies
      shell: bash
      run: |
        if [ "${{ inputs.install-extras }}" = "true" ]; then
          uv sync --group dev --all-extras
        else
          uv sync --group dev
        fi
EOF

# Update lint.yml to use composite action
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
      - name: Setup Python with uv
        uses: ./.github/actions/setup-python-uv

      - name: Run Ruff check
        run: uv run ruff check src/ tests/

      - name: Run Ruff format check
        run: uv run ruff format --check src/ tests/
EOF

# Update typecheck.yml to use composite action
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
      - name: Setup Python with uv
        uses: ./.github/actions/setup-python-uv

      - name: Run Mypy
        run: uv run mypy src/
EOF

# Update tests.yml to use composite action with extras and Python matrix
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
      - name: Setup Python with uv
        uses: ./.github/actions/setup-python-uv
        with:
          install-extras: 'true'
          python-version: ${{ matrix.python-version }}

      - name: Run tests
        run: uv run pytest tests/ -v --tb=short
EOF

# Stage all changes
git add .

# Commit the resolution
git commit -m "Resolve merge conflict: Apply composite action to split workflow files

- Replaced single ci.yml with split workflows (lint.yml, typecheck.yml, tests.yml)
- Created composite action .github/actions/setup-python-uv/action.yml
- Applied improvements:
  - Composite action reduces duplication across workflows
  - Added enable-cache: true to composite action
  - Added permissions: contents: read to all workflows
  - Added python-version parameter to composite action
  - Added Python version matrix (3.12, 3.13) to test workflow
  - Test workflow passes install-extras and python-version to composite action"

# Push the resolved branch
git push origin copilot/sub-pr-1-another-one

echo "PR #4 conflicts resolved and pushed successfully!"
