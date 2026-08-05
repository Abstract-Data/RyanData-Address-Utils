#!/usr/bin/env bash
# agent-config-versioning-gate.sh -- Stop hook
# Blocks completion if .claude/, .cursor/, skills, subagents, agent docs, or plans/
# changed this session without a fresh agent-config-audit-receipt.json.
#
# Universal Stop-hook backstop for the versioning requirement — mirrors tanstack-review-gate.sh /
# terraform-review-gate.sh / python-design-gate.sh, scoped to config/doc paths instead of code.
# Self-exits when none of the watched paths changed, so it is inert on unrelated turns.
#
# The watch-check is a fixed-string loop (grep -qF) rather than one alternation regex, and
# redirects use the 1-prefixed form, because Notion's rich-text storage backslash-escaped pipe,
# caret and dollar characters outside fenced blocks. That constraint no longer applies now the
# script is committed here (abstract-data#281: FR-1 forbids a Notion body becoming an executable),
# but the form is kept as-is so the vendored copy stays byte-faithful to what was reviewed.

set -euo pipefail

RECEIPT=".claude/agent-config-audit-receipt.json"
TTL_SECONDS=14400

changed=$(git diff --name-only HEAD 2>/dev/null; git diff --cached --name-only 2>/dev/null)

touched=""
for pattern in ".claude/skills/" ".claude/agents/" ".cursor/rules/" "AGENTS.md" "GUARDRAILS.md" "TESTING.md" "ARCHITECTURE.md" "plans/"; do
  if echo "$changed" | grep -qF "$pattern"; then
    touched="yes"
    break
  fi
done

if [ -z "$touched" ]; then
  exit 0
fi

if [ ! -f "$RECEIPT" ]; then
  echo "BLOCK: agent-config-versioning-gate -- config/doc files changed but no audit receipt found." 1>&2
  echo "Dispatch agent-config-conformance-auditor via Task tool, then retry." 1>&2
  exit 2
fi

now_ts=$(date +%s)
receipt_ts=$(python3 -c "import json; print(json.load(open('$RECEIPT'))['passed_at_unix'])" 2>/dev/null || echo 0)
age=$(( now_ts - receipt_ts ))

if [ "$age" -gt "$TTL_SECONDS" ]; then
  echo "BLOCK: agent-config-versioning-gate -- receipt is stale." 1>&2
  exit 2
fi

exit 0
