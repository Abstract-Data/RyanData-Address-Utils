# Pull Request Conflict Resolution Guide

This document provides step-by-step instructions to resolve merge conflicts in PRs #2, #3, and #4.

## Root Cause

The base branch `ci/add-github-workflows` split the single `ci.yml` workflow into three separate workflow files:
- `.github/workflows/lint.yml` (Ruff linting)
- `.github/workflows/typecheck.yml` (Mypy type checking)  
- `.github/workflows/tests.yml` (Pytest tests)

PRs #2, #3, and #4 all modify the original `ci.yml` file, which no longer exists in the base branch, causing merge conflicts.

## PR #2: Improve CI workflow with dependency caching and Python version matrix

**Changes to Apply:**
- Add `permissions: contents: read` to all three workflow files
- Add `enable-cache: true` to uv setup in all three workflows
- Add Python version matrix (`["3.12", "3.13"]`) to tests.yml
- Update test job name to include Python version: `Pytest - Python ${{ matrix.python-version }}`
- Update Python installation in tests.yml to use matrix variable: `uv python install ${{ matrix.python-version }}`

### Resolution Steps:

1. Checkout the branch:
   ```bash
   git checkout copilot/sub-pr-1
   git merge ci/add-github-workflows
   ```

2. Remove the conflicted ci.yml:
   ```bash
   git rm .github/workflows/ci.yml
   ```

3. Apply the improvements to each new workflow file:

   **lint.yml:**
   - Add `permissions: contents: read` after the `on:` section
   - Add `enable-cache: true` to the uv setup step

   **typecheck.yml:**
   - Add `permissions: contents: read` after the `on:` section
   - Add `enable-cache: true` to the uv setup step

   **tests.yml:**
   - Add `permissions: contents: read` after the `on:` section
   - Add `enable-cache: true` to the uv setup step
   - Add matrix strategy with Python 3.12 and 3.13
   - Update job name to include version
   - Use matrix Python version in setup step

4. Commit and push:
   ```bash
   git add .
   git commit -m "Resolve merge conflict: Apply PR #2 improvements to split workflow files"
   git push origin copilot/sub-pr-1
   ```

## PR #3: Remove trailing blank line from CI workflow

**Status:** This PR only removed a trailing blank line from `ci.yml`. Since the file has been split and reformatted, this change is no longer applicable.

**Resolution:** Close this PR as the formatting issue has been resolved in the split workflow files.

### Resolution Steps:

1. Close PR #3 with a comment explaining that the formatting issue was resolved during the workflow split.

## PR #4: Extract duplicated CI setup steps into composite action

**Changes to Apply:**
- Create `.github/actions/setup-python-uv/action.yml` composite action
- Update all three workflow files to use the composite action
- Add `install-extras` parameter to the composite action (default: false)
- Test workflow should pass `install-extras: 'true'`

### Resolution Steps:

1. Checkout the branch:
   ```bash
   git checkout copilot/sub-pr-1-another-one
   git merge ci/add-github-workflows
   ```

2. Remove the conflicted ci.yml:
   ```bash
   git rm .github/workflows/ci.yml
   ```

3. Create the composite action `.github/actions/setup-python-uv/action.yml`:
   ```yaml
   name: Setup Python with uv
   description: Set up Python environment using uv package manager

   inputs:
     install-extras:
       description: 'Whether to install all extras with dependencies'
       required: false
       default: 'false'

   runs:
     using: composite
     steps:
       - uses: actions/checkout@v4

       - name: Install uv
         uses: astral-sh/setup-uv@v4
         with:
           version: "latest"

       - name: Set up Python
         shell: bash
         run: uv python install 3.12

       - name: Install dependencies
         shell: bash
         run: |
           if [ "${{ inputs.install-extras }}" = "true" ]; then
             uv sync --group dev --all-extras
           else
             uv sync --group dev
           fi
   ```

4. Update each workflow file to use the composite action:

   **lint.yml:**
   ```yaml
   steps:
     - name: Setup Python with uv
       uses: ./.github/actions/setup-python-uv

     - name: Run Ruff check
       run: uv run ruff check src/ tests/

     - name: Run Ruff format check
       run: uv run ruff format --check src/ tests/
   ```

   **typecheck.yml:**
   ```yaml
   steps:
     - name: Setup Python with uv
       uses: ./.github/actions/setup-python-uv

     - name: Run Mypy
       run: uv run mypy src/
   ```

   **tests.yml:**
   ```yaml
   steps:
     - name: Setup Python with uv
       uses: ./.github/actions/setup-python-uv
       with:
         install-extras: 'true'

     - name: Run tests
       run: uv run pytest tests/ -v --tb=short
   ```

5. Commit and push:
   ```bash
   git add .
   git commit -m "Resolve merge conflict: Apply composite action to split workflow files"
   git push origin copilot/sub-pr-1-another-one
   ```

## Recommended Merge Order

To avoid future conflicts, merge PRs in this order:

1. **PR #1** - Base CI workflows (already mergeable, no conflicts)
2. **PR #2** - Add caching and Python matrix (after resolving conflicts per above)
3. **Close PR #3** - No longer needed after split
4. **PR #4** - Add composite action (after resolving conflicts per above, can be merged after PR #2)

## Alternative: Combined Resolution

Instead of resolving each PR separately, consider combining the best features of all PRs into a single update to PR #1:

1. Start with the split workflows from PR #1
2. Add caching and permissions from PR #2
3. Add Python version matrix from PR #2
4. Add composite action from PR #4
5. Close PRs #2, #3, #4 as superseded

This would result in clean, optimized workflows with all improvements applied without conflicts.
