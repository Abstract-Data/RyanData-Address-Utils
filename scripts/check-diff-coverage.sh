#!/bin/bash
# check-diff-coverage.sh — local pre-commit gate on patch-level test coverage.
#
# Runs after the `pytest` pre-commit hook, which generates coverage.xml with
# --cov. Compares that against the merge-base with the trunk branch and fails
# the commit if newly-added/changed lines aren't covered by tests — the same
# thing codecov.yml's "patch" check does on GitHub, but local and blocking,
# so it's caught before the code ever leaves this machine.
#
# Threshold matches TESTING.md's stated 80%+ project coverage target (the
# project's actual overall coverage is ~80% as of this writing, so this
# isn't an arbitrary number — it's the existing documented bar, applied to
# new code instead of just the aggregate).
set -euo pipefail

FAIL_UNDER=80

# Trunk detection — same chain as .claude/hooks/verify-submit.sh, so both
# tools agree on what "the diff" means.
detect_trunk() {
  local ref b
  if ref=$(git symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null); then
    printf '%s' "${ref##*/}"
    return
  fi
  for b in main master; do
    if git show-ref --verify --quiet "refs/heads/$b" 2>/dev/null; then
      printf '%s' "$b"
      return
    fi
  done
  printf 'main'
}

TRUNK_BRANCH=$(detect_trunk)
COMPARE_REF="origin/$TRUNK_BRANCH"
git rev-parse --verify --quiet "$COMPARE_REF" >/dev/null 2>&1 || COMPARE_REF="$TRUNK_BRANCH"

if [ ! -f coverage.xml ]; then
  echo "check-diff-coverage: coverage.xml not found — the pytest hook should have generated it." >&2
  echo "Run 'uv run pytest --cov=src/ryandata_address_utils --cov-report=xml:coverage.xml' first." >&2
  exit 1
fi

exec uv run diff-cover coverage.xml --compare-branch="$COMPARE_REF" --fail-under="$FAIL_UNDER"
