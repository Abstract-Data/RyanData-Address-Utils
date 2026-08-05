#!/bin/bash
# PostToolUse hook: warn on test functions missing a pytest marker
# Project: abstract-data
# Tool: Edit|Write
# Severity: WARN (exit 0, message to stderr)
#
# pyproject.toml defines three strict markers: smoke, integration, unit.
# --strict-markers is set, so pytest will error on unknown markers, but it
# won't warn on *missing* markers — unmarked tests slip into the default
# run and are invisible to the test suite partitioning (unit / integration / e2e).
#
# Every test function in tests/ must have at least one of:
#   @pytest.mark.unit
#   @pytest.mark.integration
#   @pytest.mark.smoke

read -r INPUT
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // .file_path // empty')

if [[ "$FILE" != *.py ]]; then
  exit 0
fi

case "$FILE" in
  */tests/*|*/test_*.py|*_test.py)
    ;;
  *)
    exit 0
    ;;
esac

if [[ ! -f "$FILE" ]]; then
  exit 0
fi

WARNINGS=""

# Find test functions: lines starting with "def test_" or "async def test_"
# then check if the preceding lines include a marker
while IFS= read -r lineno_and_line; do
  lineno=$(echo "$lineno_and_line" | cut -d: -f1)
  fn_line=$(echo "$lineno_and_line" | cut -d: -f2-)

  # Look back up to 5 lines for a pytest.mark decorator
  start=$((lineno - 5))
  [[ $start -lt 1 ]] && start=1
  preceding=$(sed -n "${start},$((lineno - 1))p" "$FILE" 2>/dev/null || true)

  if ! echo "$preceding" | grep -qE '@pytest\.mark\.(unit|integration|smoke)'; then
    WARNINGS="${WARNINGS}MISSING MARKER: $FILE:$lineno — $fn_line\n"
  fi
done < <(grep -nE '^\s*(async\s+)?def\s+test_' "$FILE" 2>/dev/null | grep -vE '^\s*#' || true)

if [[ -n "$WARNINGS" ]]; then
  echo -e "MISSING PYTEST MARKER: test(s) in $FILE lack a required marker:" >&2
  echo -e "$WARNINGS" >&2
  echo -e "  Add one of: @pytest.mark.unit  @pytest.mark.integration  @pytest.mark.smoke" >&2
fi

exit 0
