#!/bin/bash
# PostToolUse hook: catch real HTTP calls in unit tests
# Project: abstract-data
# Tool: Edit|Write
# Severity: WARN (exit 0, message to stderr)
#
# Unit tests must be hermetic — real network calls make tests flaky, slow,
# and environment-dependent. This project uses respx for mocking httpx calls
# and pytest-recording for Notion API cassettes. Any httpx.get/post/AsyncClient
# in tests/ that isn't inside a respx mock or a cassette fixture is suspect.
#
# Skips: tests/e2e/ (e2e tests are allowed to make real calls) and
#        tests/integration/ (integration tests may also use real calls under markers).

read -r INPUT
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // .file_path // empty')

if [[ "$FILE" != *.py ]]; then
  exit 0
fi

case "$FILE" in
  */tests/unit/*|*/tests/test_*|*/test_*.py)
    ;;
  *)
    exit 0
    ;;
esac

if [[ ! -f "$FILE" ]]; then
  exit 0
fi

WARNINGS=""

# Direct httpx client instantiation without respx context in unit tests
direct_calls=$(grep -nE '(httpx\.(get|post|put|patch|delete|AsyncClient|Client)\()' "$FILE" 2>/dev/null | grep -vE '^\s*#' || true)
if [[ -n "$direct_calls" ]]; then
  # Check if respx is imported/used in this file
  if ! grep -qE 'import respx|respx\.mock|@respx\.mock' "$FILE" 2>/dev/null; then
    WARNINGS="${WARNINGS}REAL HTTP: $FILE makes httpx calls without respx mock:\n"
    while IFS= read -r line; do
      WARNINGS="${WARNINGS}  $line\n"
    done <<< "$direct_calls"
    WARNINGS="${WARNINGS}  Unit tests must be hermetic. Use respx.mock or @pytest.mark.vcr for Notion cassettes.\n"
  fi
fi

if [[ -n "$WARNINGS" ]]; then
  echo -e "$WARNINGS" >&2
fi

exit 0
