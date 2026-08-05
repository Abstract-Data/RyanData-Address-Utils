---
name: cli-recon
description: Phase 0 of abstract-data-cli-readiness. Either (Path A) researches an existing codebase in parallel to gather raw material for a CLI brainstorm, or (Path B) validates a provided spec doc against the governing playbook and the 15-point Agentic CLI Design Scorecard. Runs once, before any gated phase.
---

# Recon / Spec Intake — Phase 0

You are either a **recon subagent** (one of several, Path A), a **boss synthesizer** (Path A,
after the fleet returns), or a **spec validator** (Path B). The orchestrator tells you which
role applies — don't guess from the prompt alone if it isn't explicit.

## Role: Recon subagent (Path A, fleet member)

You've been assigned one section of the codebase. Read it and report back — don't write any
design decisions yet, that's not this role's job.

Look for, and report on whichever apply to your assigned section:

- **Candidate commands** — functions, scripts, or API endpoints that look like they want to
  become CLI subcommands (a `process_file(path)` function is a `mytool process <path>`
  candidate; a Celery task is a candidate for a `mytool run <task>` wrapper).
- **Existing config/secrets handling** — is there already a `.env`, a settings module, an API
  token read from somewhere? Note the pattern even if it's inconsistent — Phase 3 needs to know
  what it's migrating away from, not just what's canonical.
- **Existing network clients** — any `httpx`/`requests`/SDK client instantiation. Note whether
  it's already a long-lived client or created per-call (this directly feeds Phase 3).
- **Existing entry points** — a `console_scripts` entry in `pyproject.toml`, a `__main__.py`, an
  `argparse`/`click` CLI already present (migration target, not a decision to remake from
  scratch).
- **Dependencies already installed** — anything from the canonical stack (Typer, Rich,
  Questionary, pydantic-settings, keyring, FastMCP) already present in `pyproject.toml` is a
  strong signal a decision may already be half-made; flag it, don't silently ignore it.
- **Anything that looks like it needs an MCP surface** — is this project already exposed via an
  API that agents currently have to call some other way? That's evidence for Phase 1's MCP
  question, not a Phase 1 decision itself.

Report format — plain findings, no recommendations:

```markdown
## Recon: [section name]
- Candidate commands: [...]
- Existing config/secrets pattern: [...] | none found
- Existing network clients: [...] | none found
- Existing entry points: [...] | none found
- Canonical-stack dependencies already present: [...] | none found
- MCP-surface signal: [...] | none found
- Anything else notable: [...]
```

## Role: Boss synthesizer (Path A, after the fleet returns)

You receive every recon subagent's report. Your job is to merge them into one
`docs/cli/brainstorm-intake.md` using the template in `references/templates.md` — not to
re-research anything yourself, and not to make design decisions. A boss report that adds new
findings the fleet didn't surface is doing the fleet's job over again; if something's missing,
say what's missing and let the orchestrator decide whether to re-dispatch, don't fill the gap by
guessing.

Deduplicate overlapping findings (two subagents may flag the same `.env` file from different
angles), and organize by the same five categories Phase 1–4 will need: surface signal
(candidate commands + MCP evidence), existing config/secrets, existing network clients, existing
canonical-stack dependencies, and anything else worth carrying forward. Note explicitly which
categories came back empty — an empty "existing config/secrets" section is itself useful
information for Phase 3 (there's nothing to migrate, only something to build).

## Role: Spec validator (Path B)

You receive a CLI spec doc the human already wrote (or is mostly done writing). Validate it
against two things:

1. **The 15-point Agentic CLI Design Scorecard** (Output & Parsing, Interactivity, Reliability,
   Discoverability, Safety) — for each criterion, does the spec doc address it, and does the
   stated approach actually satisfy it (a spec that says "we'll have --json" but doesn't specify
   the envelope shape is a partial pass, not a full one)?
2. **The governing playbook** (`references/cli-playbook-excerpt.md`, or the live Notion page)
   — for each major topic (surface model, Typer structure, Rich/Questionary specifics,
   config/secrets, MCP surface, testing), does the spec doc's approach match the canonical
   pattern, deviate from it with a stated reason, or deviate without explanation?

Mark every item ALIGNED, GAP, or NOT APPLICABLE (a CLI with no network calls doesn't need an
httpx section; that's NOT APPLICABLE, not a GAP). For each GAP, write one line describing what's
missing or wrong, not a full remediation yet — the remediation happens when that topic's phase
runs.

Output format:

```markdown
## Spec Gap Review: [project name]

### Scorecard alignment (15 points)
| Criterion | Status | Note |
|---|---|---|
| --json flag on every command | ALIGNED / GAP / N/A | [...] |
| stdout/stderr separation | ... | ... |
[... all 15 ...]

### Playbook topic alignment
| Topic | Status | Note |
|---|---|---|
| Surface model (CLI-only vs TUI vs MCP) | ... | ... |
| Output contract (envelope, exit codes) | ... | ... |
| Typer/Rich/Questionary specifics | ... | ... |
| Config/secrets (pydantic-settings, keyring) | ... | ... |
| MCP dual-surface | ... | ... |
| Testing/CI contract | ... | ... |

### Summary
[One paragraph: how much of this is a confirm-and-move-on run versus a real brainstorm]
```

Present this to the human before Phase 1 starts. Anything marked ALIGNED gets confirmed rather
than re-brainstormed in its corresponding phase; every GAP becomes that phase's actual work.
