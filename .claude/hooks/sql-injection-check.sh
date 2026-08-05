#!/bin/bash
# PostToolUse hook: SQL Injection Prevention
# Enforces: SQLModel + FastAPI Playbook — SQL Injection Prevention section
# Trigger: Edit/Write to *.py
# Severity: WARN (this project has no SQL; guard against future additions)

read -r INPUT
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // .file_path // empty')

if [[ "$FILE" != *.py ]]; then
  exit 0
fi

if [[ ! -f "$FILE" ]]; then
  exit 0
fi

WARNINGS=""

FSTRING_IN_TEXT=$(grep -nE 'text\(\s*f["'"'"']' "$FILE" 2>/dev/null)
if [[ -n "$FSTRING_IN_TEXT" ]]; then
  WARNINGS="${WARNINGS}SQL INJECTION RISK: $FILE uses f-string inside text() — critical vulnerability.\n"
  while IFS= read -r line; do
    WARNINGS="${WARNINGS}  $line\n"
  done <<< "$FSTRING_IN_TEXT"
  WARNINGS="${WARNINGS}  Fix: Use named parameter binding: text(\"SELECT ... WHERE id = :id\"), {\"id\": value}\n"
fi

CONCAT_IN_TEXT=$(grep -nE 'text\([^)]*\+[^)]*\)' "$FILE" 2>/dev/null)
if [[ -n "$CONCAT_IN_TEXT" ]]; then
  WARNINGS="${WARNINGS}SQL INJECTION RISK: $FILE uses string concatenation inside text().\n"
  while IFS= read -r line; do
    WARNINGS="${WARNINGS}  $line\n"
  done <<< "$CONCAT_IN_TEXT"
fi

FORMAT_IN_TEXT=$(grep -nE 'text\([^)]*\.format\(' "$FILE" 2>/dev/null)
if [[ -n "$FORMAT_IN_TEXT" ]]; then
  WARNINGS="${WARNINGS}SQL INJECTION RISK: $FILE uses .format() inside text().\n"
  while IFS= read -r line; do
    WARNINGS="${WARNINGS}  $line\n"
  done <<< "$FORMAT_IN_TEXT"
fi

PERCENT_IN_TEXT=$(grep -nE 'text\([^)]*%\s' "$FILE" 2>/dev/null)
if [[ -n "$PERCENT_IN_TEXT" ]]; then
  WARNINGS="${WARNINGS}SQL INJECTION RISK: $FILE uses % formatting inside text().\n"
  while IFS= read -r line; do
    WARNINGS="${WARNINGS}  $line\n"
  done <<< "$PERCENT_IN_TEXT"
fi

if [[ -n "$WARNINGS" ]]; then
  echo -e "$WARNINGS"
fi
