---
name: abstract-data-cli-readiness
description: >-
  Runs a phase-gated pre-build design cycle for a Python CLI that needs to work for both human
  operators and AI agents — surface model (CLI-only vs +TUI vs +MCP), the --json/--plain agent
  output contract, Typer/Rich/Questionary/pydantic-settings/keyring decisions, and the
  testing/CI contract. Two entry paths: no spec doc (a subagent fleet recons the codebase, or
  Phase 0 interviews inline if greenfield, then brainstorms); or a spec doc exists/is coming
  (validates it against the governing playbook and the Agentic CLI Design Scorecard, flags
  gaps, goes to synthesis). Produces a CLI design doc, an ADR, and a staged rollout checklist,
  then hands off to CLI Agent-Readiness Audit for post-build verification. Trigger on "let's
  design a CLI for X," "brainstorm the CLI/TUI for X," "does this need a CLI or a TUI," or
  "here's my CLI spec, sanity check it." Do NOT use to audit a CLI that already exists — use
  CLI Agent-Readiness Audit instead.
license: MIT
metadata:
  author: abstract-data
  version: 1.0.0
  status: draft
  scope: global
  category: methodology
  languages: [Python, Markdown]
  last_reviewed: null
  amendment_of: null
  amendment_reason: null
  related_playbooks:
    - "Agent-Friendly Dual-Mode CLI Design — Typer + Rich + FastMCP"
    - "CLI Tool Best Practices — Typer + Rich + yt-dlp"
  related_skills:
    - abstract-data-spec-brainstorm
    - python-project-review
    - "CLI Agent-Readiness Audit"
  evaluation_criteria: |
    After the cycle completes, the CLI design doc must:
    - Map every Phase 2 (Output & Agent Contract) decision to a specific one of the 15 Agentic
      CLI Design Scorecard criteria (Output & Parsing, Interactivity, Reliability,
      Discoverability, Safety) — not a separately invented rubric
    - Have a filled staged rollout checklist (Stage 1-4) with no placeholders
    - Cite the CLI design playbook (or its bundled fallback) for every library-level decision
    - If a TUI was chosen in Phase 1, explicitly confirm the CLI-only path still covers every
      capability — a TUI-only capability is a capability agents can't reach
---

# Abstract Data CLI Readiness

Most CLIs get their architecture decided by accident — whatever the first `typer.Typer()`
happened to look like sticks, and the agent-facing contract (`--json`, exit codes, TTY
detection) gets bolted on later once something breaks in a pipeline. This skill is the
pre-build decision cycle that prevents that: five decisions (plus recon) that end with a locked
CLI design doc, an ADR, and a staged rollout checklist, before the first `@app.command()` gets
written.

This is the **construction-time counterpart** to `CLI Agent-Readiness Audit`, which already
exists and scores a *finished* CLI against a 15-point Agentic CLI Design Scorecard. This skill
exists so that score is closer to 15/15 the first time the audit runs, not something discovered
and retrofitted afterward. Everything in Phase 2 is written to map directly onto that scorecard.

**This is not a "which CLI framework" brainstorm.** Between the governing playbook and the
existing yt-dlp playbook, Typer + Rich + Questionary + pydantic-settings + keyring + FastMCP +
(optionally) Textual is the canonical Abstract Data CLI stack already. The decisions this skill
walks through are which of those pieces this specific project needs and how they're configured
— not whether Typer beats Click.

## Non-negotiables (read before starting)

- **Two entry paths, decided once, in Phase 0.** No blending — a project either has no spec doc
  (recon + brainstorm) or has one / has one coming (validate + gap-review). Don't start
  brainstorming decisions a spec doc already made.
- **No framework free-for-all.** The canonical stack comes from the governing playbook. A phase
  recommending something outside it (a different CLI framework, a different config library)
  needs an explicit, named reason — not a preference.
- **Never auto-advance past a gate.** Phases 1–4 each end with a human `APPROVE` / `REVISE`.
  "Should I continue?" is not a valid stop for the human — that's the actual gate; wait for it.
- **An open question isn't automatically a `REVISE`.** If a phase's core recommendation is sound
  and actionable but surfaces something only the human (or a later phase) can resolve, that's a
  `PASS` with an entry in that phase's **Open Questions** field — it travels forward into Phase
  5, it doesn't block this gate. Reserve `REVISE` for when the open question actually undermines
  the recommendation itself and the phase can't be finalized without an answer first.
- **The TUI must never be the sole path to a capability.** If Phase 1 lands on "CLI + Textual
  TUI," Phase 1's critique pass must confirm every capability is still reachable without the
  TUI. Agents cannot drive a TUI.
- **Design toward the existing scorecard, not a new one.** Phase 2's output contract decisions
  map 1:1 onto the 15 Agentic CLI Design Scorecard criteria. If a decision doesn't trace to one
  of those criteria, it belongs in Phase 3 (stack/UX), not Phase 2.

## The six stages

```
Phase 0  RECON / INTAKE     — agents/cli-recon.md               → no gate (fleet + boss, or spec-doc gap review)
Phase 1  SURFACE            — agents/cli-surface-selector.md    → gate
Phase 2  OUTPUT CONTRACT    — agents/cli-contract-selector.md   → gate
Phase 3  STACK & UX         — agents/cli-stack-selector.md      → gate
Phase 4  TESTING            — agents/cli-testing-selector.md    → gate
Phase 5  SYNTHESIS          — agents/cli-synthesis-writer.md    → no gate (formalizes what 1-4 locked)
```

Each phase's role definition, decision tree, and output format live in its own file under
`agents/`. Read the relevant file when you reach that phase — don't try to hold all five in
context at once.

### Model selection (optional)

Phase 0 (recon) benefits from your strongest available model when a fleet is dispatched — it's
independent research across a codebase, and a shallow read here propagates errors through every
later phase. Phases 1–3 are where the real judgment calls live (interaction model, the agent
contract, library configuration) and also warrant your strongest model. Phase 4 (testing) and
Phase 5 (synthesis) are closer to checklist application and formalization — a lighter model is
usually fine if your environment lets you pin one per subagent.

## Environment detection and subagent dispatch

Before Phase 0, determine which subagent mechanism the current session actually has, in this
order, and use the first one that's real:

1. **Claude Code** — dispatch via the Task tool to `.claude/agents/cli-*.md`.
2. **Cursor 2.4+** — dispatch via native Subagents to the same files copied into
   `.cursor/skills/abstract-data-cli-readiness/agents/`.
3. **Antigravity 2.0+** — dispatch via native subagents to the same files under
   `.agents/skills/abstract-data-cli-readiness/agents/`.
4. **None of the above** (plain chat, an older tool build, or a dispatch failure) — run the
   phase **inline**. Read the matching `agents/cli-*.md` file, adopt the role it describes,
   produce its output format, then step back into the orchestrator role to present the gate.

Running inline is not a reason to skip the critique pass. Phases 1–4 are evaluator-optimizer
loops — generate the recommendation, then explicitly critique it against that phase's own
criteria as a second pass, before it reaches the human. If one agent is doing both passes, say
so out loud in the output ("critique pass, self-run") rather than silently merging them.

If you can't tell which environment you're in, ask once rather than guessing.

## Phase 0: Recon or Spec Intake (orchestrator + fleet, no gate)

Before dispatching anything, determine which of two entry paths applies. Ask the human directly
if it isn't already obvious from context:

**"Do you have a CLI spec doc already, or is one coming — or should we brainstorm this from
scratch?"**

### Path A — No spec doc: Recon then brainstorm

1. Check whether the project has existing code at all. If it's genuinely greenfield (no
   repository, or an empty one), skip the fleet — interview the human directly for what
   operations/data the CLI needs to expose, and write that straight into
   `docs/cli/brainstorm-intake.md` using the template in `references/templates.md`.
2. If a codebase already exists (a FastAPI service or Polars pipeline that wants a companion
   CLI, an existing argparse/Click tool being redone, etc.), dispatch a **subagent fleet** to
   research it in parallel — one subagent per natural section (e.g. core business logic
   modules, existing config/secrets handling, existing network clients, existing
   scripts/entry-points, README/docs, `pyproject.toml` dependencies). Each subagent reports back
   candidate commands, existing patterns worth preserving, and anything that already half-solves
   a later phase's decision (e.g. an existing `httpx.Client` setup, an existing `.env` pattern).
3. A **boss agent** synthesizes every subagent's findings into a single
   `docs/cli/brainstorm-intake.md` — this is the shared context every later phase reads, not raw
   subagent output. Use the intake template in `references/templates.md`.
4. Proceed to Phase 1.

### Path B — Spec doc exists or is coming

- **Spec doc exists now:** read it in full, then validate it against the governing playbook
  (`references/cli-playbook-excerpt.md`, or the live Notion page if available — see "Notion
  access" below) and the 15-point Agentic CLI Design Scorecard. Produce
  `docs/cli/spec-gap-review.md`: for each of the 15 scorecard criteria and each major playbook
  topic (surface model, output contract, Typer/Rich/Questionary specifics, config/secrets,
  MCP surface, testing), mark the spec doc as ALIGNED, GAP, or NOT APPLICABLE, with a one-line
  reason. Present this to the human. Decisions the spec doc already made correctly are locked as-
  is — don't re-litigate them in Phases 1–4. Any GAP becomes the seed of that phase's discussion
  when you reach it.
- **Spec doc is coming, not here yet:** don't block waiting. Offer to co-draft it now (this
  overlaps with `doc-coauthoring`'s workflow) or offer to run Path A instead and let the spec
  doc get written from the resulting design doc. Either way, this is a real pause, not a silent
  fallback — ask which the human wants before doing anything else.

## Phases 1–4: dispatch, critique, gate

For each phase, in order:

1. Dispatch (or run inline) per the environment logic above, passing the subagent the current
   `docs/cli/brainstorm-intake.md` (Path A) or `docs/cli/spec-gap-review.md` (Path B), plus every
   prior phase's locked decision.
2. The subagent produces its recommendation, then its own critique pass, returning `PASS` or
   `REVISE` against that phase's own criteria (defined in the phase's file).
3. If the subagent's self-critique is `REVISE`, loop it once more with the specific objection
   before presenting anything to the human.
4. Present the phase's output to the human exactly as formatted by the subagent — and if its
   Open Questions field is non-empty, call those out explicitly as part of how you relay the
   gate, don't let them sit buried in the full text waiting to be noticed. Wait for `APPROVE` or
   `REVISE`.
   - `APPROVE` → append the locked decision (and any open questions, carried forward as-is) to
     the intake/gap-review file, mark the phase complete, move on. An open question doesn't
     require `REVISE` on its own — the human can approve the decision and carry the question
     forward for Phase 5 to collect.
   - `REVISE` → re-dispatch the same phase with the human's added context. This is a fresh
     generation, not a patch on the old one.

On a Path B run where Phase 0 marked a topic ALIGNED, that phase can move faster — confirm the
spec doc's existing decision rather than generating a new recommendation from nothing, but still
run the critique pass and still gate. "The spec doc already said so" is not itself a critique
pass.

## Phase 5: Synthesis (no gate)

Phase 5 doesn't propose new decisions — it formalizes what Phases 1–4 (or Phase 0's gap review,
for anything marked ALIGNED) already locked. No `APPROVE`/`REVISE` gate here; the gate already
happened per-decision. Read `agents/cli-synthesis-writer.md` for the exact output format. It
produces:

- `docs/cli/cli-design.md` — the design doc, organized by the same five topics as the phases
- `docs/cli/adr/ADR-CLI-001-surface-and-contract.md` — an ADR stub capturing the Phase 1/2
  decisions and their rationale
- A **customized staged rollout checklist** (Stage 1–4), lifted from the governing playbook's
  own checklist structure and filled in with this project's specific decisions rather than the
  playbook's generic placeholders

`cli-design.md` keeps two separate sections for two different kinds of loose end: **open
questions** (things nobody could answer from the intake/spec — someone has to go find out before
or during implementation) and **deferred items** (things the human already decided to skip for
now). Collapsing these into one list loses exactly the distinction that makes either one useful.

## Delivering the result

When Phase 5 completes:

- Save `cli-design.md` to Abstract Data Docs in Notion (Document Type: AI Codebase Assessment,
  or a more specific type if one exists for design docs — check before defaulting) if Notion MCP
  is available; otherwise leave it in `docs/cli/` and say so.
- Deliver all four files: `brainstorm-intake.md` (or `spec-gap-review.md`), `cli-design.md`, the
  ADR stub, and the rollout checklist.
- Say plainly: "Design cycle complete. Once this is built, run **CLI Agent-Readiness Audit**
  against it to verify the scorecard score matches what Phase 2 designed for." Don't run that
  audit yourself here — it needs a real CLI to point `--help` traversal at, which doesn't exist
  yet at the end of this skill.

## Anti-patterns this skill guards against

- **Framework free-for-all** — recommending a CLI/config/secrets library outside the canonical
  stack without flagging it as an explicit override. If nothing canonical fits, say so.
- **Re-litigating a Path B spec doc** — regenerating decisions from scratch that Phase 0 already
  marked ALIGNED. Confirm, don't reinvent.
- **TUI-only capability** — any capability reachable only through a Textual `ui` subcommand and
  not through a scriptable command. Phase 1's critique pass exists specifically to catch this.
- **Inventing a parallel scorecard** — Phase 2 criteria that don't map onto the existing 15-point
  Agentic CLI Design Scorecard. If a decision doesn't fit one of the five scorecard categories
  (Output & Parsing, Interactivity, Reliability, Discoverability, Safety), it's a Phase 3 concern.
- **Skipping the pause on "spec doc coming"** — treating a promised-but-absent spec doc as
  equivalent to "no spec doc" and silently running Path A instead of asking which the human
  actually wants.
- **Parallel phase execution** — Phases 1–4 are a dependency chain (surface model constrains the
  contract, which constrains stack config, which constrains what needs testing). Tempting to
  fan them out for speed; don't.

## Notion access

Phase 0 (Path B validation), Phase 2, and Phase 3 reference the governing playbook, "Agent-
Friendly Dual-Mode CLI Design — Typer + Rich + FastMCP," in Reference Documentation. Prefer
pulling it live via the Notion MCP each run — it's marked Draft and will get revised as real
runs surface gaps, so a stale bundled copy is worse than a live miss. If Notion is unreachable,
fall back to `references/cli-playbook-excerpt.md` and say so explicitly in the phase output
("Notion unreachable — used bundled excerpt, verify against the live page before implementation").
Never present a fallback-sourced recommendation as if it came from a live pull.

## Cross-Skill Relationships

| Skill | When to use |
|---|---|
| **CLI Agent-Readiness Audit** | Run after the CLI is built, against the design this skill produced. This skill's whole purpose is making that audit's score high on the first pass. |
| **abstract-data-spec-brainstorm** | If the *whole project* (not just its CLI surface) doesn't have a locked language/stack yet, run that skill's Phases 1–3 first. This skill assumes Python is already decided and picks up from there. |
| **doc-coauthoring** | If Phase 0 finds a spec doc is "coming but not here," offer this skill for co-drafting it before returning to Phase 0. |
| **python-project-review** | Once the CLI exists, its "CLI tool" detected-type path covers general Python code quality — this skill's design doc is a useful input to that review, not a replacement for it. |

`CLI Agent-Readiness Audit` should list this skill as its pre-build companion once this skill is
promoted — that's a two-way relationship worth adding to that skill's Notion registry entry when
this one goes Stable.

## Promoting this skill from draft to stable

- [ ] Run ≥ 3 times across different project shapes (at minimum: one Path A greenfield, one
      Path A existing-codebase, one Path B spec-doc-validation run)
- [ ] All four gated phases completed with `APPROVE` on each run
- [ ] Every Phase 5 design doc's Phase 2 section maps cleanly onto the 15-point scorecard with
      no unmapped decisions
- [ ] At least one resulting CLI has actually been built and scored against CLI Agent-Readiness
      Audit, and the score matches what Phase 2 designed for (or the gap is understood)
- [ ] Governing playbook flipped from Draft → Stable in Reference Documentation, based on what
      real runs surfaced
- [ ] `metadata.status` flipped to `stable`, `metadata.last_reviewed` set, this skill registered
      as a page in Dev: Agent Skills, and the governing playbook's `Related Skills` field updated
      to point back at it, all in the same session this skill is promoted

## Reference files

- `agents/cli-recon.md` — Phase 0 role definition (fleet dispatch + boss synthesis, or spec-doc
  gap review)
- `agents/cli-surface-selector.md` — Phase 1 role definition
- `agents/cli-contract-selector.md` — Phase 2 role definition
- `agents/cli-stack-selector.md` — Phase 3 role definition
- `agents/cli-testing-selector.md` — Phase 4 role definition
- `agents/cli-synthesis-writer.md` — Phase 5 role definition
- `references/templates.md` — intake / gap-review / design-doc / ADR / rollout-checklist templates
- `references/cli-playbook-excerpt.md` — bundled fallback content for when Notion is unreachable
