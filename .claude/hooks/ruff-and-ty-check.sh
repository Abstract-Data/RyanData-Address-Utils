#!/bin/bash
# PostToolUse hook: run ruff lint + ty type-check on every edited Python file
# Project: abstract-data
# Tool: Edit|Write
# Severity: WARN (exit 0, message to stderr)
#
# Surfaces lint errors and type violations immediately after a write, while the
# context is still hot. Claude sees the output and can fix issues in the same
# turn rather than discovering them at pytest time.
#
# Uses `uv run` so the project virtualenv is always used regardless of which
# Python is active in the shell. Both tools are dev dependencies (pyproject.toml).
#
# Ruff: fast linter + formatter check (E, W, F, I, UP, B, C4, SIM rule sets)
# ty:   Pyright-derived type checker (Anthropic's replacement for mypy)

read -r INPUT
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // .file_path // empty')

if [[ "$FILE" != *.py ]]; then
  exit 0
fi

if [[ ! -f "$FILE" ]]; then
  exit 0
fi

# Resolve project root (directory containing pyproject.toml)
PROJECT_ROOT=$(git -C "$(dirname "$FILE")" rev-parse --show-toplevel 2>/dev/null || dirname "$FILE")

WARNINGS=""

# --- ruff lint ---
if command -v ruff &>/dev/null || command -v uv &>/dev/null; then
  if command -v uv &>/dev/null; then
    RUFF_OUT=$(cd "$PROJECT_ROOT" && uv run ruff check "$FILE" --output-format=concise 2>&1 | head -30 || true)
  else
    RUFF_OUT=$(ruff check "$FILE" --output-format=concise 2>&1 | head -30 || true)
  fi
  if [[ -n "$RUFF_OUT" ]]; then
    WARNINGS="${WARNINGS}RUFF:\n$RUFF_OUT\n"
  fi
fi

# --- ty type check ---
if command -v uv &>/dev/null; then
  TY_OUT=$(cd "$PROJECT_ROOT" && uv run ty check "$FILE" 2>&1 | grep -vE '^(warning: |$|Using Python)' | head -30 || true)
  if [[ -n "$TY_OUT" ]]; then
    WARNINGS="${WARNINGS}TY:\n$TY_OUT\n"
  fi
fi

if [[ -n "$WARNINGS" ]]; then
  echo -e "── lint/type check: $FILE ──" >&2
  echo -e "$WARNINGS" >&2
fi

exit 0
