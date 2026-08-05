#!/usr/bin/env bash
# session-py-baseline.sh — SessionStart hook
# Records the set of Python files already dirty at session start (pre-existing
# uncommitted changes) so verify-completion.sh (Stop) can EXCLUDE them from its
# changed-file lint/pytest scope — a session that touched no .py of its own must not
# be blamed for pre-existing drift (#45). Session-keyed, best-effort, never blocks.
#
# Exit codes: always 0.
set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
cd "$PROJECT_DIR" 2>/dev/null || exit 0

# The same persistent store verify-completion.sh uses (survives GitButler worktree cleanup).
STORE_BASE="$HOME/.local/state/abstract-data-gate"
STORE_KEY="$(printf '%s' "$PROJECT_DIR" | shasum 2>/dev/null | cut -c1-12)"
STORE="$STORE_BASE/${STORE_KEY:-default}"
mkdir -p "$STORE" 2>/dev/null || true

SESSION_ID="$(
  cat 2>/dev/null | python3 -c 'import sys, json
try:
    print(json.load(sys.stdin).get("session_id", ""))
except Exception:
    print("")' 2>/dev/null || true
)"
[ -n "$SESSION_ID" ] || exit 0

# Sanitize the session id into a filename (mirrors gate.py ledger keying).
SAFE="$(printf '%s' "$SESSION_ID" | tr -c 'A-Za-z0-9._-' '_')"
BASELINE="$STORE/py-baseline-$SAFE.txt"

# Pre-existing dirty .py = tracked-modified vs HEAD + untracked, filtered to .py.
{ git diff --name-only HEAD 2>/dev/null; \
  git ls-files --others --exclude-standard 2>/dev/null; } \
  | grep -E '\.py$' | sort -u > "$BASELINE" 2>/dev/null || true

exit 0
