#!/bin/bash
# PostToolUse hook: catch mutable default arguments in function definitions
# Project: abstract-data
# Tool: Edit|Write
# Severity: WARN (exit 0, message to stderr)
#
# Python mutable default arguments (def foo(items=[]), def foo(config={}),
# def foo(tags=set())) are shared across all calls — mutations in one call
# persist to the next. This is one of the most common Python footguns and
# causes subtle bugs that only appear after repeated invocations.
#
# Fix: use None as the default and assign inside the function body.
#   def foo(items=None): items = items if items is not None else []

read -r INPUT
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // .file_path // empty')

if [[ "$FILE" != *.py ]]; then
  exit 0
fi

if [[ ! -f "$FILE" ]]; then
  exit 0
fi

WARNINGS=""

# Match: def funcname(... param=[] or param={} or param=set() or param=list() or param=dict()
mutable_defaults=$(grep -nE 'def\s+\w+\s*\(.*=\s*(\[\s*\]|\{\s*\}|set\s*\(\s*\)|list\s*\(\s*\)|dict\s*\(\s*\))' "$FILE" 2>/dev/null | grep -vE '^\s*#' || true)

if [[ -n "$mutable_defaults" ]]; then
  WARNINGS="${WARNINGS}MUTABLE DEFAULT: $FILE has mutable default argument(s):\n"
  while IFS= read -r line; do
    WARNINGS="${WARNINGS}  $line\n"
  done <<< "$mutable_defaults"
  WARNINGS="${WARNINGS}  Mutable defaults are shared across calls. Use None and assign inside the body:\n"
  WARNINGS="${WARNINGS}    def foo(items=None): items = items if items is not None else []\n"
fi

if [[ -n "$WARNINGS" ]]; then
  echo -e "$WARNINGS" >&2
fi

exit 0
