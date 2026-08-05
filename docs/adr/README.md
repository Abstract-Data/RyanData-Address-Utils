# Architecture Decision Records

This directory documents why specific tools, models, or architectural patterns were chosen for
this project — the "why," not just the "what" (which is what the code and `AGENTS.md` already
show).

## Format

Each ADR is a single file: `{NNNN}-{slug}.md`, numbers sequential and never reused.

```markdown
# ADR {NNNN}: {Title}
**Date:** {YYYY-MM-DD}
**Status:** proposed | accepted | superseded by ADR-{NNNN}

## Context
{What situation prompted this decision?}

## Decision
{What was decided and why?}

## Consequences
{What are the trade-offs? What becomes easier or harder?}
```

## Policy

- **Append-only.** Never delete or rewrite a past ADR, even a superseded one — mark its status
  and point to the ADR that replaced it.
- A new significant tool/architecture choice gets a new ADR, not an edit to an existing one.
