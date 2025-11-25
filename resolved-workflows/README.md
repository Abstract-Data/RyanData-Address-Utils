# Pull Request Conflict Resolution

This directory contains everything needed to resolve merge conflicts in PRs #2, #3, and #4.

## Quick Summary

- **PR #1**: ✅ No conflicts (mergeable)
- **PR #2**: ❌ Has conflicts (resolved via `resolve-pr2.sh`)
- **PR #3**: ℹ️ Not needed (formatting fix superseded by workflow split)
- **PR #4**: ❌ Has conflicts (resolved via `resolve-pr4.sh`)

## Root Cause

The base branch `ci/add-github-workflows` split the single `.github/workflows/ci.yml` into three files:
- `lint.yml` - Ruff linting
- `typecheck.yml` - Mypy type checking
- `tests.yml` - Pytest testing

PRs #2, #3, and #4 all modify the old `ci.yml` which no longer exists, causing conflicts.

## Automated Resolution

### Option 1: Run Resolution Scripts

The repository contains automated scripts to resolve each PR:

```bash
# Resolve PR #2 (caching + Python matrix)
./resolve-pr2.sh

# Resolve PR #4 (composite action)
./resolve-pr4.sh
```

**Note:** These scripts require GitHub push permissions. If you don't have direct push access, you'll need to fork and create new PRs or ask a maintainer to run these scripts.

### Option 2: Use Resolved Workflow Files

The `resolved-workflows/` directory contains the fully resolved workflow files that incorporate ALL improvements from PRs #2 and #4:

1. **Resolved workflow files:**
   - `lint.yml` - With permissions, caching, and composite action
   - `typecheck.yml` - With permissions, caching, and composite action
   - `tests.yml` - With permissions, caching, Python matrix, and composite action
   - `setup-python-uv-action.yml` - Composite action for setup

2. **To apply these files:**
   - Copy them to the appropriate locations in the repository
   - The composite action should go to `.github/actions/setup-python-uv/action.yml`
   - The workflow files should go to `.github/workflows/`

## Manual Resolution

See `PR_CONFLICT_RESOLUTION.md` for detailed step-by-step manual resolution instructions.

## Improvements Included

The resolved workflows incorporate all improvements from the conflicting PRs:

### From PR #2:
✅ `enable-cache: true` for faster CI runs
✅ `permissions: contents: read` for security
✅ Python version matrix (3.12, 3.13) for broader testing
✅ Python version in test job name for clarity

### From PR #4:
✅ Composite action to eliminate code duplication
✅ Parameterized composite action (install-extras, python-version)
✅ Clean, maintainable workflow files

### Bonus Enhancement:
✅ Added `python-version` parameter to composite action for matrix support

## Recommended Action

**For Repository Maintainers:**

1. Review the resolved workflow files in `resolved-workflows/`
2. Either:
   - Run `./resolve-pr2.sh` and `./resolve-pr4.sh` to automatically resolve conflicts, OR
   - Manually apply the changes from `resolved-workflows/` to PR #1 or a new PR
3. Close PR #3 as it's no longer needed
4. Merge the resolved PRs or the enhanced PR #1

The end result will be a clean CI setup with:
- Separate workflows for each CI task (better status badges)
- Dependency caching (faster runs)  
- Python version matrix (better compatibility testing)
- Reusable composite action (DRY principle)
- Proper security permissions
