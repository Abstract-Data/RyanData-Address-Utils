# Templates

These are the literal skeletons each phase writes into. Copy the structure; fill in the brackets. Don't add sections that aren't here without a reason worth naming in the orchestrator's handoff.

## brainstorm-intake.md (Phase 0, orchestrator writes, then append-only)

```markdown
# Brainstorm Intake — [Project Name]
**Spec name:** [kebab-case slug]
**Output path:** docs/spec/[spec-name]/ — or docs/spec/[spec-name]/v.[n].[n]/ once versioned (see orchestrator Phase 0 for how this is resolved and, if needed, migrated)
**Date:** YYYY-MM-DD
**Intent:** [free-form paragraph]
**Fixed constraints:** [bullets]
**Timeline:** spike | MVP | production
**Greenfield:** yes / no
**If no — retrofit or evergreen:** retrofit → stop here, hand off to project-alignment | evergreen → confirmed via `abstract-data status`, Phases 1–2 skipped, resuming at Phase 3
**BMAD roles:** [who plays PM, Architect, Engineer, QA, DevOps]

---

## Decision Log
<!-- Each phase appends its locked decision here after APPROVE. Never edit a prior entry. -->
<!-- On an evergreen run this starts at Phase 3 — there's no Phase 1/2 entry to append. -->

### Phase 1 — Language (locked YYYY-MM-DD)
[Phase 1's approved output, verbatim — omit this section entirely on an evergreen run]

### Phase 2 — Tooling (locked YYYY-MM-DD)
[Phase 2's approved output, verbatim — omit this section entirely on an evergreen run]

### Phase 3 — Patterns (locked YYYY-MM-DD)
[Phase 3's approved output, verbatim]
```

## project-constitution.md (Phase 4 output)

On an evergreen run, don't write a fresh copy of this template — the project already has one. Instead write `project-constitution.md` (in this run's resolved, module-scoped output folder — the folder name already carries the scoping, so no `-addendum-[module-name]` suffix is needed) with just the "Non-negotiable constraints" and "Context7 receipt log" sections, and a one-line pointer back to the existing root-level `project-constitution.md` for the immutable stack section. Full template below is for greenfield and post-retrofit runs, where there's no existing constitution to extend.

```markdown
# project-constitution.md
## Project: [name]
## Created: YYYY-MM-DD

## Stack (immutable)
- Language: [locked language + version]
- Runtime / Package manager: [locked]
- Framework: [locked]
- Deploy target: [locked]

## Non-negotiable constraints
- [Each human-stated fixed constraint from intake]
- [Each constraint implied by the AGENTS.md base template, e.g. "1Password Environments for all secrets"]
- [Each constraint from the Phase 3 architecture decision, e.g. "Supabase RLS enabled on every table before first write"]

<!-- Every prohibition below needs a paired alternative — see spec-constitution-writer.md -->

## Definition of done
- Python: `uv run pytest` + `uv run ruff check .` clean — if Python project
- TypeScript: `bun run tsc` passes with zero errors — if TS project
- All TASK.md items checked off
- task-critic subagent returns PASS before declaring the task complete

## AGENTS.md base
- Primary: [named template from Phase 1]
- Overlays: [alpha/staging/prod, if applicable]

## Context7 receipt log
- See context7-receipts.md (this run's output path)
```

## spec.md skeleton — see `agents/spec-draft-writer.md` for the full structure and the EARS format rules. Don't duplicate it here; that file is the source of truth for Phase 5.

## context7-receipts.md (append-only, written by Phases 2 and 3)

```markdown
## Context7 Receipt — [Library Name] [version]
- resolve-library-id result: [id]
- get-library-docs: [confirmation + key version-specific notes]
- Version-sensitive APIs noted: [any breaking changes observed, or "none"]
```

One entry per library. Phase 2 writes per-feature library receipts; Phase 3 writes architecture-level library receipts (e.g. pydantic-ai, FastMCP) if they weren't already covered in Phase 2.

## ADR draft (Phase 3 output, written as adr-draft-[slug].md under this run's resolved output path — NOT the project's ADR log)

This is a proposal, not a project record yet. It only becomes an accepted ADR at promotion time — see "ADR lifecycle: draft → promoted" in SKILL.md. Don't write `Status: Accepted` here, and don't number it as `ADR-001` or otherwise — that number doesn't exist until promotion assigns it from the project's actual `docs/adr/` sequence.

```markdown
# ADR (Draft): Stack and Architecture Selection

**Status:** Proposed
**Date:** YYYY-MM-DD

## Context
[Why this decision was needed — pull from the intake's project intent]

## Decision
[The locked language, tooling, and primary architectural pattern]

## Consequences
[What this commits the project to, and what it forecloses]

---
> **Promotion status:** Not yet promoted. This draft becomes part of the project's ADR log only if this spec proceeds — see SKILL.md § "ADR lifecycle: draft → promoted."
```

Once promoted, the copy in `docs/adr/` is the project's permanent record and is append-only from there — a later decision gets a new ADR, not an edit to this one. The draft copy inside `docs/spec/` is left as-is (still `Status: Proposed`) as a record of what this brainstorm pass recommended, even after promotion happens elsewhere.
