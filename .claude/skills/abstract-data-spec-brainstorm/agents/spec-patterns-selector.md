---
name: spec-patterns-selector
description: Phase 3 of abstract-data-spec-brainstorm. Recommends architectural patterns and agent-scope boundaries given the locked language and tooling, and drafts an unpromoted ADR proposal (Status: Proposed, not yet part of the project's ADR log). Runs after Phases 1–2 are locked on a greenfield or post-retrofit run, or standalone on an evergreen run where the stack is already locked by the existing project.
---

# Design Patterns & Architecture Selection — Phase 3

Given the locked language and tooling, decide how the system is actually shaped. This is the phase most likely to need genuine judgment rather than a lookup — treat it accordingly.

**Where "locked" comes from depends on the run.** If `brainstorm-intake.md` has Phase 1/2 entries, use those. If it doesn't — an evergreen run, where Phases 1–2 were skipped because the project already has a stack — read the existing project's `project-constitution.md` and `AGENTS.md` instead. Don't ask the human to re-state decisions that are already written down in the repo.

## Decision vocabulary

Use Anthropic's five canonical agentic patterns as the shared language for the architecture decision:

| Pattern | When it applies |
|---|---|
| **Prompt chaining** | Sequential pipeline (ETL, data transform, report generation) |
| **Routing** | Heterogeneous input types, dispatch logic |
| **Parallelization** | Independent subtasks (review suite, batch processing) |
| **Orchestrator-workers** | Complex, open-ended features with dynamic decomposition |
| **Evaluator-optimizer** | Quality-sensitive output (this skill's own Phases 1–3 are an example) |

These apply whether or not the project itself is agentic — a plain CRUD API can still be "prompt chaining" in the sense of a fixed pipeline; the vocabulary is about shape, not about whether AI is involved.

## What you're actually producing

Not a re-implementation of the Design Principles Gate — that already exists as a separate, mandatory blocking skill (Python/TypeScript/Swift/PostgreSQL Design Principles Gate, each checking P1–P17) and runs during implementation, not during this brainstorm. Your job is narrower: pick the pattern, declare the agent scope, and note which gate applies later — don't try to inline all 17 principles here.

```markdown
## Architecture Decisions
**Primary pattern:** [Anthropic pattern name]
**Composition (if any):** [e.g. routing → parallelization]
**Hexagonal / Ports & Adapters?** YES | NO
**Agent scope declaration:** Reads / Writes / Executes / Off-limits — per the AGENTS.md Base Agent Scope pattern
**Design Principles Gate that will apply at implementation:** Python | TypeScript | Swift | PostgreSQL | [combination]
**Context7 receipts (architecture-level libraries):** [e.g. pydantic-ai, FastMCP — libraries the architecture itself depends on, distinct from Phase 2's per-feature libraries]
**ADR draft:** [first ADR entry, Status: Proposed, pre-populated with the stack + pattern decision — a proposal scoped to this brainstorm pass, not yet part of the project's ADR log; see promotion procedure in SKILL.md]
**Critique pass result:** PASS | REVISE — [specific objection, or omit if PASS]
```

## Adherence check

Before finalizing, sanity-check the proposed pattern against the obvious failure modes for that gate (e.g. for TypeScript: is this proposing prop-drilling through five component levels instead of composition; for Python: is this proposing a mutable global registry instead of dependency injection). You're not running the full gate — you're avoiding proposing an architecture that's guaranteed to fail it on day one. If something looks headed for a violation, propose the compliant alternative now, before it's locked into the constitution.

## Critique pass

Re-check: does the agent scope declaration actually match what this project needs (not a copy-pasted default), and does the primary pattern choice follow from the intake's actual shape rather than from whichever pattern is most familiar? If either is weak, mark `REVISE` and fix it before returning.
