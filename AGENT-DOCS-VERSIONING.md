# Agent & Docs Versioning

Version: 1.0.0

The convention `agent-config-versioning-gate.sh` (Stop hook) and `agent-config-conformance-auditor`
(subagent) enforce.

## Rule

Whenever any of the following change in a session, a fresh audit receipt
(`.claude/agent-config-audit-receipt.json`) must exist before the session can close:

- `.claude/agents/*.md`
- `.claude/skills/*/SKILL.md`
- `.cursor/rules/*.mdc`
- `AGENTS.md`, `GUARDRAILS.md`, `TESTING.md`, `ARCHITECTURE.md`
- `plans/`

## Requirements checked by the auditor

- Every `.claude/skills/*/SKILL.md` has a version header in its first 20 lines.
- Every `.claude/agents/*.md` has `description:`, `model:`, `tools:`, and `version:` in its
  frontmatter.
- `AGENTS.md`, `GUARDRAILS.md`, `TESTING.md`, `ARCHITECTURE.md` each have a version header.
- `plans/` has no loose `.md` files directly in its root — every plan lives in
  `plans/{NNNN}-{slug}/`.

## Getting unblocked

If `agent-config-versioning-gate.sh` blocks session close: dispatch
`agent-config-conformance-auditor` via the Task tool. It re-checks the current state of the repo
(not just the diff) and writes the receipt only if everything passes. If something fails, fix the
specific gap it names, then re-dispatch.

## Why a receipt instead of just checking file existence

A file existing with a plausible-looking version number isn't the same as someone having actually
verified it's accurate. The receipt records that the auditor subagent re-read the current state
this session and confirmed it — not that the files merely exist.
