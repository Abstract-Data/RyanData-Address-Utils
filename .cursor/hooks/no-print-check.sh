#!/bin/bash
# PostToolUse hook: No print() in production code
# Project: abstract-data
# Trigger: Edit/Write to *.py under src/abstract_data/
# Severity: WARN
#
# The CLI uses `rich.console.Console` for user-facing output and
# `logging.getLogger(__name__)` for diagnostics. `print()` in src/ is a smell
# because it bypasses both surfaces and can leak into MCP `serve` stdio.
#
# Skips: tests/, scripts/, conftest.py, __main__.py, cli.py (the typer.echo entry).

read -r INPUT
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // .file_path // empty')

if [[ "$FILE" != *.py ]]; then
  exit 0
fi

case "$FILE" in
  */tests/*|*/test_*|*_test.py|*/scripts/*|*/conftest.py|*__main__.py|*/cli.py)
    exit 0
    ;;
esac

case "$FILE" in
  */src/abstract_data/*|*/src/*|*/app/*|*/domain/*|*/services/*|*/adapters/*)
    ;;
  *)
    exit 0
    ;;
esac

if [[ ! -f "$FILE" ]]; then
  exit 0
fi

PRINT_CALLS=$(grep -nE '^\s*print\(' "$FILE" 2>/dev/null | grep -vE '^\s*#' 2>/dev/null)

if [[ -n "$PRINT_CALLS" ]]; then
  COUNT=$(echo "$PRINT_CALLS" | wc -l | tr -d ' ')
  WARNINGS="NO PRINT: $FILE has $COUNT print() call(s) in production code.\n"
  while IFS= read -r line; do
    WARNINGS="${WARNINGS}  $line\n"
  done <<< "$PRINT_CALLS"
  WARNINGS="${WARNINGS}  Use rich.console.Console for user output, logging.getLogger(__name__) for diagnostics.\n"
  echo -e "$WARNINGS"
fi
