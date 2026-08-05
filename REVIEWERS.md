# REVIEWERS.md

Index mapping touched-file patterns to the review-capable subagent that covers them. Regenerate
this file when `.claude/agents/` changes — don't hand-edit it out of sync with the real roster.

**Roster arithmetic:** 10 subagents total in `.claude/agents/` this repo. Of those, 6 are
review/audit-capable (listed in Installed below); the remaining 4 (`doc-writer`, `researcher`,
`session-closer`, `test-writer`) are authoring/support roles, not reviewers, so they're
intentionally absent from the mapping table.
This project has no Notion-sourced canonical reviewer roster to diff against (no abstract-data
coupling by design — see `docs/adr/0001-initial-tool-selection.md`), so "Not installed" below
lists roles a *generic* Python-package project commonly has but this one doesn't need, not gaps
against an external source of truth.

## Installed

| Subagent | Covers | Enforcement mode |
|---|---|---|
| `code-reviewer` | Any diff before a PR — architecture/typing/test-coverage review | On-demand (dispatch via Task tool) |
| `security-auditor` | `src/**` — injection risk, unsafe deserialization, hardcoded secrets, dependency CVEs | On-demand |
| `python-design-principles-gate` | `*.py` — P1-P17 design-principle check (Pydantic v2 patterns) | Hard-blocked (`python-design-gate.sh`, PostToolUse on Edit\|Write) |
| `agent-config-conformance-auditor` | `.claude/`, `.cursor/rules/`, `AGENTS.md`, `GUARDRAILS.md`, `TESTING.md`, `ARCHITECTURE.md`, `plans/` | Hard-blocked (`agent-config-versioning-gate.sh`, Stop hook) |
| `task-critic` | Any multi-step task, before declaring it complete | On-demand, required before completion claims per `AGENTS.md`/global governance |
| `reviewer` | General read-only code review (overlaps `code-reviewer`; kept for continuity with pre-existing setup) | On-demand |

## Not installed

These are common review roles for other project types that don't apply here (this is a Python
`package` project, not an `api`/`pipeline`/web project):

- `db-migrator`, `supabase-auditor`, `api-contract-checker` — API/database projects only
- `pipeline-auditor`, `data-validator` — data-pipeline projects only
- `tanstack-change-reviewer`, `terraform-change-reviewer` — no TypeScript/TanStack or Terraform in this repo
- `spec-reviewer` — Subagent-Driven Development workflow, not in use here
- `notion-publisher` — Notion-integration role; this project has no Notion coupling by design

## Other agents (non-reviewer roles)

`doc-writer`, `researcher`, `session-closer`, `test-writer` — authoring/support roles, not part of
the review-coverage mapping above.
