#!/bin/bash
# python-design-gate.sh
# Stop hook — hard-blocks session completion when Python files were changed
# without a fresh python-design-gate-reviewer receipt.
#
# Mirrors tanstack-review-gate.sh / terraform-review-gate.sh: same
# stop_hook_active guard, same diff_sha + TTL + verdict receipt pattern.
#
# Vendored from Notion into project_tools/hooks/ (abstract-data#281): FR-1 forbids a Notion page
# body from becoming an executable on disk, so every hook now ships from this committed,
# code-reviewed source. Scoped in manifest.toml to language = ["python"], and it self-exits when
# the diff touches no .py files, so it is inert in projects it does not apply to.
INPUT=$(cat)

# CRITICAL: never loop. stop_hook_active=true = Claude is already forced-continuing.
if [ "$(echo "$INPUT" | jq -r '.stop_hook_active')" = "true" ]; then
  exit 0
fi

# 1. Does this diff touch Python files at all?
CHANGED_PY=$(git diff --name-only HEAD 2>/dev/null | grep '\.py$' || true)
[ -z "$CHANGED_PY" ] && exit 0   # nothing to gate

# 2. SHA of the Python-relevant diff
DIFF_SHA=$(git diff HEAD -- $CHANGED_PY 2>/dev/null | shasum -a 256 | cut -d' ' -f1)
RECEIPT=".claude/python-design-gate-receipt.json"
NOW=$(date +%s); TTL=7200   # 2-hour receipt window, matches tanstack/terraform gates

if [ -f "$RECEIPT" ]; then
  R_SHA=$(jq -r '.diff_sha // empty' "$RECEIPT" 2>/dev/null)
  R_TIME=$(jq -r '.completed_at_unix // 0' "$RECEIPT" 2>/dev/null)
  R_VERDICT=$(jq -r '.verdict // empty' "$RECEIPT" 2>/dev/null)
  AGE=$((NOW - R_TIME))

  if [ "$R_SHA" = "$DIFF_SHA" ] && [ "$AGE" -lt "$TTL" ] && [ -n "$R_VERDICT" ]; then
    if [ "$R_VERDICT" = "BLOCK" ]; then
      echo "❌ Unresolved P1-P17 violations (receipt: $RECEIPT). Fix, then re-review." >&2
      exit 2
    fi
    exit 0   # WARN or CLEAN → proceed
  fi
fi

echo "❌ Python files changed with no fresh python-design-gate-reviewer receipt." >&2
echo "   Changed files: $CHANGED_PY" >&2
echo "   Invoke python-design-gate-reviewer on git diff HEAD; it must write $RECEIPT before this task can be marked done." >&2
exit 2
