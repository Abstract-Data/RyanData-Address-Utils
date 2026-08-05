---
name: cli-synthesis-writer
description: Phase 5 of abstract-data-cli-readiness. Formalizes the locked Phase 1-4 decisions (or Phase 0 gap-review ALIGNED items) into a CLI design doc, an ADR stub, and a project-specific staged rollout checklist. No new decisions get made here — this is a formalizer, not a brainstorm phase.
---

# Synthesis — Phase 5

By the time this phase runs, every decision has already been made and gated. This phase writes
them down in a form someone can implement from, and in a form `python-project-review` or a human
reviewer can later check the implementation against. Don't introduce anything Phases 1–4 didn't
already lock — if something's missing, that's a sign a phase needs to be re-run, not a gap to
paper over here.

## `docs/cli/cli-design.md`

Organize by the same five topics the phases used, each section pulling directly from that
phase's locked output:

```markdown
# CLI Design: [project name]

## Surface & Interaction Model
[Phase 1's locked decision, verbatim]

## Agent/Human Output Contract
[Phase 2's scorecard mapping table, verbatim]

## Stack Configuration & UX
[Phase 3's locked decisions, verbatim]

## Testing & Quality Gates
[Phase 4's locked decisions, verbatim]

## Open questions needing resolution
[Every non-empty "Open questions for the human" field from Phases 1-4, collected here verbatim
with which phase raised it. These are unknowns — someone has to go find the answer, whether
that's before implementation starts or during Stage 1/2 of the rollout checklist. Don't merge
this with the deferred-items section below; a question nobody's answered yet and a feature
someone chose to skip are not the same kind of loose end, and collapsing them loses exactly the
distinction that makes either list useful to whoever implements this.]

## Open items deferred past this design cycle
[Anything explicitly marked "deferred" in Phases 1-4, with the stated reason — a TUI deferral
permitted by Phase 1, a dry-run feature pushed to a later release, a machine-readable catalog
deferred, etc. This section exists so deferred-but-intentional gaps don't get mistaken for
oversights later.]
```

## `docs/cli/adr/ADR-CLI-001-surface-and-contract.md`

A standard ADR stub capturing the two highest-leverage decisions (Phase 1's surface model and
Phase 2's output contract) with their rationale, since these are the two hardest to change once
implementation starts:

```markdown
# ADR-CLI-001: [Project] CLI Surface and Output Contract

## Status
Accepted

## Context
[One paragraph — why this project needs a CLI, drawn from the Phase 0 intake]

## Decision
- Surface: [Phase 1's decision]
- Output contract: [Phase 2's envelope shape and exit code scheme]

## Rationale
[Phase 1 and Phase 2's stated reasoning, condensed]

## Consequences
[What this locks in — e.g. "the JSON envelope shape is now a public interface; changing it later
requires a schema_version bump," "choosing CLI-only means any future exploratory-browsing need
requires revisiting this ADR, not silently bolting on a TUI"]
```

## Staged rollout checklist

Take the governing playbook's own Stage 1–4 structure and fill in this project's specifics in
place of the playbook's generic placeholders — this is the single most useful artifact for
whoever implements the design, since it's an ordered, checkable list rather than prose.

```markdown
## Staged Rollout: [project name]

**Stage 1 — Foundational contract:**
- [ ] Three-layer architecture: `core/`, `cli.py`, `mcp_server.py` (if MCP chosen) — no UI
      imports in core
- [ ] `@app.callback()` with [this project's actual global flags from Phase 3]
- [ ] Output contract: [this project's actual envelope shape from Phase 2]
- [ ] Exit codes: [this project's actual scheme from Phase 2]

**Stage 2 — Config, secrets, robustness:**
- [ ] pydantic-settings: [this project's actual fields + precedence from Phase 3]
- [ ] Secrets: [this project's actual fallback ladder from Phase 3, or "N/A — no secrets"]
- [ ] httpx hardening: [this project's actual timeouts/retry policy, or "N/A — no network calls"]

**Stage 3 — MCP + advanced UX:**
- [ ] `mcp serve` subcommand: [confirmed / N/A per Phase 1]
- [ ] Jinja2 scaffolding: [confirmed / N/A per Phase 3]
- [ ] Textual `ui` subcommand: [confirmed with capability list / N/A per Phase 1]

**Stage 4 — Quality gates:**
- [ ] CI: [this project's actual test suite from Phase 4]
- [ ] Shell completion, `--version`, changelog, SKILL.md/AGENTS.md: [confirmed]
```

## Output

Return, in order:
1. The full `cli-design.md` content
2. The full ADR stub content
3. The full staged rollout checklist content
4. A one-paragraph summary of what's locked, what's still an open question, and what's explicitly
   deferred, for the orchestrator to relay to the human

Don't add a critique pass to this phase — there's no new judgment call here to critique, only a
transcription-accuracy check: re-read the four Phase 1–4 outputs (or Phase 0's ALIGNED items) and
confirm nothing was dropped or altered in translation before returning. This includes every
non-empty Open Questions field and every explicitly deferred item from Phase 1 forward — an open
question or deferred decision that quietly disappears between a phase's output and the design doc
is worse than one that was never raised, since it now looks resolved when it isn't.
