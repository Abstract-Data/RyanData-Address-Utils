#!/bin/bash
# PostToolUse hook: enforce GUARDRAILS Sign #3 — no tomli/toml package imports
# Project: abstract-data
# Tool: Edit|Write
# Severity: WARN (exit 0, message to stderr)
#
# GUARDRAILS.md Sign #3: stdlib `tomllib` (Python 3.11+) handles TOML reads.
# `tomli_w` handles TOML writes. The `tomli` backport package and the `toml`
# package are not dependencies and must not be imported. Importing them indicates
# a misread of the dependency list and will cause an ImportError at runtime.

read -r INPUT
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // .file_path // empty')

if [[ "$FILE" != *.py ]]; then
  exit 0
fi

if [[ ! -f "$FILE" ]]; then
  exit 0
fi

WARNINGS=""

# Catch: import tomli, from tomli import ..., import toml, from toml import ...
bad_imports=$(grep -nE '^\s*(import tomli\b|from tomli\b|import toml\b|from toml\b)' "$FILE" 2>/dev/null | grep -vE '^\s*#|tomli_w' || true)
if [[ -n "$bad_imports" ]]; then
  WARNINGS="${WARNINGS}TOMLI GUARD [GUARDRAILS Sign #3]: $FILE imports banned package:\n"
  while IFS= read -r line; do
    WARNINGS="${WARNINGS}  $line\n"
  done <<< "$bad_imports"
  WARNINGS="${WARNINGS}  For reads: import tomllib (stdlib, Python 3.11+).\n"
  WARNINGS="${WARNINGS}  For writes: import tomli_w (the only allowed TOML write dep).\n"
fi

if [[ -n "$WARNINGS" ]]; then
  echo -e "$WARNINGS" >&2
fi

exit 0
