#!/bin/bash
# PostToolUse hook: warn if `requests` is imported under src/ (async-first stack)
# Project: abstract-data
# Trigger: Edit/Write to *.py under src/
# Severity: WARN (Hooks Reference #8, simplified — any src file)

set -euo pipefail

read -r INPUT
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // .file_path // empty')

if [[ "$FILE" != *.py ]]; then
  exit 0
fi

case "$FILE" in
  */src/*) ;;
  *) exit 0 ;;
esac

if [[ ! -f "$FILE" ]]; then
  exit 0
fi

if grep -qE '^[[:space:]]*(import requests|from requests)' "$FILE" 2>/dev/null; then
  echo "WARNING: $FILE imports requests — use httpx (async) per AGENTS.md / GUARDRAILS." >&2
fi

exit 0
