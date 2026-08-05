# Templates

## `docs/cli/brainstorm-intake.md` (Path A — no spec doc)

Used by the Phase 0 boss synthesizer (or written directly by the orchestrator on a genuinely
greenfield run with no fleet dispatched). This is the shared context every gated phase reads —
keep it factual, not aspirational; decisions belong in the phases, not here.

```markdown
# CLI Brainstorm Intake: [project name]

**Date:** [date]
**Entry path:** Path A (no spec doc)
**Codebase status:** greenfield (no fleet dispatched) | existing codebase (fleet dispatched)

## Candidate commands
[From recon findings, or direct interview on a greenfield run — every operation/function/
endpoint that looks like a CLI subcommand]

## Existing config/secrets pattern
[What's already there, even if inconsistent] | None found — nothing to migrate

## Existing network clients
[Client library, instantiation pattern — per-call or long-lived] | None found

## Existing entry points
[argparse/Click CLI, console_scripts entry, __main__.py] | None found — first CLI for this project

## Canonical-stack dependencies already present
[Typer/Rich/Questionary/pydantic-settings/keyring/FastMCP already in pyproject.toml] | None found

## MCP-surface signal
[Existing API agents already call some other way; explicit "wrap this for Claude" use case] | None found

## Anything else notable
[Team context, timeline pressure, a specific pain point that motivated wanting a CLI at all]
```

## `docs/cli/spec-gap-review.md` (Path B — spec doc exists)

Produced by the Phase 0 spec validator. See `agents/cli-recon.md` for the full scoring
instructions — this is the blank structure:

```markdown
# CLI Spec Gap Review: [project name]

**Date:** [date]
**Entry path:** Path B (spec doc: [link or filename])

## Scorecard alignment (15 points)
| Criterion | Status | Note |
|---|---|---|
| JSON flag on every command | | |
| stdout/stderr separation | | |
| Structured errors | | |
| Schema versioning | | |
| Non-interactive flag | | |
| No hidden prompts | | |
| TTY detection | | |
| Semantic exit codes | | |
| Idempotent writes | | |
| Paginated lists | | |
| Labeled flags | | |
| Usage examples in --help | | |
| Machine-readable catalog | | |
| SKILL.md / AGENTS.md | | |
| Dry-run support | | |

## Playbook topic alignment
| Topic | Status | Note |
|---|---|---|
| Surface model | | |
| Output contract | | |
| Typer/Rich/Questionary specifics | | |
| Config/secrets | | |
| MCP dual-surface | | |
| Testing/CI contract | | |

## Summary
[...]
```

## Design-doc, ADR, and rollout-checklist templates

These live inline in `agents/cli-synthesis-writer.md` rather than duplicated here, since Phase 5
is the only place they're used and keeping them next to the role that fills them in avoids the
two copies drifting apart.
