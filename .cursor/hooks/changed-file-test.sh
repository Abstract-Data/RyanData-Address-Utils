#!/bin/bash
# PostToolUse hook: run a changed source file's OWN tests, resolved by find
# Project: abstract-data
# Tool: Edit|Write
# Severity: WARN (exit 0, message to stderr)
#
# FR-5.1 (enforcement-integrity v1.0.0). When a .py file under src/ is written,
# locate every tests/**/test_<stem>.py and run it, so the file's own tests fail in
# the same turn rather than at the end of the session.
#
# Three deliberate choices, each of which has a silently-wrong alternative:
#   * `find tests -type f -name "test_<stem>.py"` — NOT a shell glob. Bash `globstar`
#     is off by default, so `tests/**/` degrades to depth 2 and misses most matches.
#   * whole test FILE paths — never a pytest name filter (that is a substring match,
#     which for a stem like `apply` selects 150+ unrelated functions).
#   * `cd` to the project root before `uv run`, because `uv run` resolves its project
#     from the current working directory (precedent: ruff-and-ty-check.sh).
#
# Zero matches runs nothing at all. One match runs it. More than one runs all of them.

read -r INPUT

FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // .file_path // empty' 2>/dev/null)

if [ -z "$FILE" ]; then
  exit 0
fi

if [[ "$FILE" != *.py ]]; then
  exit 0
fi

# --- project root: gate.py's chain (CLAUDE → CURSOR → workspace_roots[0] → cwd → pwd) ---
ROOT="${CLAUDE_PROJECT_DIR:-}"
if [ -z "$ROOT" ]; then
  ROOT="${CURSOR_PROJECT_DIR:-}"
fi
if [ -z "$ROOT" ]; then
  ROOT=$(echo "$INPUT" | jq -r '.workspace_roots[0] // empty' 2>/dev/null)
fi
if [ -z "$ROOT" ]; then
  ROOT=$(echo "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)
fi
if [ -z "$ROOT" ]; then
  ROOT=$(pwd)
fi

if [ ! -d "$ROOT" ]; then
  exit 0
fi

# --- scope: .py files under the project's src/ tree only (FR-5.1) ---
case "$FILE" in
  /*) ABS="$FILE" ;;
  *) ABS="$ROOT/$FILE" ;;
esac

case "$ABS" in
  "$ROOT"/src/*) ;;
  *) exit 0 ;;
esac

if ! command -v uv >/dev/null 2>&1; then
  exit 0
fi

cd "$ROOT" || exit 0

if [ ! -d tests ]; then
  exit 0
fi

STEM=$(basename "$FILE" .py)
if [ -z "$STEM" ]; then
  exit 0
fi

MATCHES=()
while IFS= read -r match; do
  if [ -n "$match" ]; then
    MATCHES+=("$match")
  fi
done < <(find tests -type f -name "test_${STEM}.py" 2>/dev/null | sort)

if [ ${#MATCHES[@]} -eq 0 ]; then
  exit 0
fi

if ! OUT=$(uv run pytest "${MATCHES[@]}" -q 2>&1); then
  {
    echo "── changed-file tests: $FILE ──"
    echo "$OUT" | tail -30
    echo "(ran: ${MATCHES[*]})"
  } >&2
fi

exit 0
