#!/bin/bash
# PostToolUse hook: catch naive datetime usage (datetime.now() without tz)
# Project: abstract-data
# Tool: Edit|Write
# Severity: WARN (exit 0, message to stderr)
#
# Naive datetimes (datetime.now(), datetime.utcnow()) break timestamp comparisons
# when the Notion API returns timezone-aware ISO 8601 strings. All datetimes must
# be timezone-aware. Use datetime.now(UTC) or datetime.fromisoformat() which
# preserves the tzinfo from the Notion response.
#
# Reference: GUARDRAILS.md — always use timezone-aware datetimes.

read -r INPUT
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // .file_path // empty')

if [[ "$FILE" != *.py ]]; then
  exit 0
fi

# Skip test files — mocked/fixed datetimes in tests are expected
case "$FILE" in
  */tests/*|*/test_*|*_test.py|*/conftest.py)
    exit 0
    ;;
esac

if [[ ! -f "$FILE" ]]; then
  exit 0
fi

WARNINGS=""

# datetime.now() without a tz argument (datetime.now(UTC) is fine)
naive_now=$(grep -nE 'datetime\.now\(\s*\)' "$FILE" 2>/dev/null | grep -vE '^\s*#' || true)
if [[ -n "$naive_now" ]]; then
  WARNINGS="${WARNINGS}NAIVE DATETIME: $FILE uses datetime.now() without a timezone:\n"
  while IFS= read -r line; do
    WARNINGS="${WARNINGS}  $line\n"
  done <<< "$naive_now"
  WARNINGS="${WARNINGS}  Use datetime.now(UTC) or datetime.now(timezone.utc) instead.\n"
fi

# datetime.utcnow() — deprecated in 3.12, always naive
utcnow=$(grep -nE 'datetime\.utcnow\(\)' "$FILE" 2>/dev/null | grep -vE '^\s*#' || true)
if [[ -n "$utcnow" ]]; then
  WARNINGS="${WARNINGS}NAIVE DATETIME: $FILE uses deprecated datetime.utcnow():\n"
  while IFS= read -r line; do
    WARNINGS="${WARNINGS}  $line\n"
  done <<< "$utcnow"
  WARNINGS="${WARNINGS}  Use datetime.now(UTC) — utcnow() is deprecated in Python 3.12.\n"
fi

if [[ -n "$WARNINGS" ]]; then
  echo -e "$WARNINGS" >&2
fi

exit 0
