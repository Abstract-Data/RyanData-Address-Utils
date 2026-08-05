---
name: abstract-data-spec-brainstorm
description: >-
  Runs a structured pre-specification brainstorm cycle before SDD Phase 1
  (SPECIFY), for new projects, features, or refactors whose stack isn't
  locked yet. Walks through six phases — intake, language, tooling/framework,
  design patterns, constitution, spec draft — with evaluator-optimizer
  critique and human APPROVE/REVISE gates after each. Requires a Context7
  receipt for every library; never free-forms tooling outside the AGENTS.md
  bases and DEV-ENV-INDEX stack. Produces project-constitution.md, an
  EARS-format spec.md, a draft ADR, and a Context7 receipt log into a
  versioned docs/spec/[spec-name]/ output folder, then hands off to SDD
  Phase 2 (PLAN). Trigger phrases include "start a
  project spec brainstorm for X," "brainstorm the spec for X," and "I want
  to build X but don't know what to use yet." Works in Claude Code, Cursor,
  and Antigravity via native subagents, falling back to sequential
  single-agent execution otherwise. Do NOT use for single-session bug fixes
  or projects with a stack already locked.
license: MIT
metadata:
  author: abstract-data
  version: 1.2.0
  status: draft
  scope: global
  category: methodology
  languages: [Python, TypeScript, Markdown]
  last_reviewed: null
  amendment_of: null
  amendment_reason: >-
    1.1.0 restructured output into a spec-name-scoped, versioned folder
    (docs/spec/[spec-name]/ -> v.[n].[n]/ on a modification or additional
    pass). 1.2.0 fixes Phase 3's ADR to be an unpromoted draft (Status:
    Proposed, unnumbered) instead of writing Status: Accepted straight into
    the brainstorm output, and adds the promotion procedure that moves it
    into the project's real docs/adr/ log only once the spec proceeds. See
    "ADR lifecycle: draft -> promoted."
  related_playbooks:
    - "Spec-Driven Development — Constitution, Phases & Role Taxonomy"
    - "Agentic Engineering — Workflow Survey & Foundational Patterns"
    - "Multi-Agent Agentic Coding Workflows: Implementation-Ready Guide"
  related_skills:
    - subagent-driven-development
    - doc-coauthoring
    - project-alignment
  evaluation_criteria: |
    After the brainstorm cycle completes, spec.md must:
    - Have a filled project-constitution.md with >= 3 non-negotiables
    - Map to at least one existing AGENTS.md base template
    - Have a Context7 doc-pull receipt for every selected library
    - Pass the Python or TypeScript Design Principles Gate without P1-P3 violations
---

# Project Spec Brainstorm

Most real projects start as a vague intent, not a spec. Spec-Driven Development assumes you already know the language, stack, and architecture when Phase 1 (SPECIFY) begins — in practice that decision-making has to happen first, or the implementation phase produces technically correct code against the wrong stack. This skill is that pre-flight: a five-decision brainstorm cycle (plus intake) that ends with a locked `project-constitution.md` and a draft `spec.md`, ready to hand to SDD Phase 2.

## Non-negotiables (read before starting)

- **Never auto-advance past a gate.** Phases 1–3 each end with a human `APPROVE` / `REVISE` decision. "Should I continue?" is not a valid stop — that's a real gate, wait for it. A `REVISE` re-runs that phase's dispatch with the human's added context; it does not silently patch the prior output.
- **No free-form tooling.** Every language, framework, and library recommendation must trace to an AGENTS.md base template, the DEV-ENV-INDEX canonical list, or an explicit human override. If nothing canonical fits, say so and ask — don't invent a plausible-sounding library.
- **Context7 receipts are mandatory, not advisory**, for every library selected in Phase 2. A tooling recommendation without a receipt is incomplete, not merely unpolished.
- **Phases run serially.** Each phase depends on the prior one's locked decision. Don't parallelize Phases 1–5, even though the subagents dispatching them could technically run concurrently.
- **Never overwrite a prior pass silently.** If `docs/spec/[spec-name]/` already has content when Phase 0 starts, migrate it into `v.1.0/` before writing anything new there — a second pass commingling with or clobbering the first is a data-loss bug, not a formatting detail.

## The six phases

```
Phase 0  INTAKE        — orchestrator collects intent, constraints, timeline inline (no subagent)
Phase 1  LANGUAGE       — agents/spec-language-selector.md    → gate  [skipped on an evergreen existing-project run]
Phase 2  TOOLING         — agents/spec-tooling-selector.md     → gate  [skipped on an evergreen existing-project run]
Phase 3  PATTERNS        — agents/spec-patterns-selector.md    → gate
Phase 4  CONSTITUTION    — agents/spec-constitution-writer.md  (no gate — formalizes approved decisions)
Phase 5  SPEC DRAFT      — agents/spec-draft-writer.md         (no gate — draft, reviewed in SDD Phase 2)
```

Phases 1–2 only apply when there's a language/tooling decision left to make — greenfield or a retrofit that's resumed here after `project-alignment`. An evergreen existing project already has both locked, so this run starts at Phase 3. See "Phase 0: Intake" below for how that gets decided.

Each phase's role definition, evaluation criteria, and output format live in its own file under `agents/`. Read the relevant file when you reach that phase — don't try to hold all five in context at once.

### Model selection (optional)

Phases 1 and 4 are a bounded decision and a formalization pass — they don't need your most capable model. Phases 2, 3, and 5 are where real judgment gets exercised (multi-library tooling tradeoffs, architecture pattern selection, EARS-quality spec writing) and benefit from your strongest available model. If your environment lets you pin a subagent's model, use that split. In Claude Code's `.claude/agents/*.md` frontmatter this is a `model:` key (`haiku` | `sonnet` | `opus` | `inherit`); Cursor and Antigravity configure subagent models differently as of this writing (per-invocation or UI-level, not a shared frontmatter key) — verify the current mechanism in each tool rather than assuming this key carries over.

## Environment detection and subagent dispatch

Before Phase 1, determine which subagent mechanism the current session actually has, in this order, and use the first one that's real:

1. **Claude Code** — dispatch via the Task tool to `.claude/agents/spec-*.md`.
2. **Cursor 2.4+** — dispatch via native Subagents to the same files copied into `.cursor/skills/abstract-data-spec-brainstorm/agents/`.
3. **Antigravity 2.0+** — dispatch via native subagents to the same files under `.agents/skills/abstract-data-spec-brainstorm/agents/`.
4. **None of the above** (a plain chat session, an older tool build, or a dispatch failure) — run the phase **inline**. Read the matching `agents/spec-*.md` file yourself, adopt the role it describes, produce its output format, then step back into the orchestrator role to present the gate.

The role, inputs, evaluation criteria, and output format for a phase are identical regardless of which path fires — only the dispatch mechanism changes. **Running inline is not a reason to skip the critique pass.** Phases 1–3 are evaluator-optimizer loops: generate the recommendation, then explicitly critique it against that phase's evaluation criteria as a second pass, before it ever reaches the human. If you're one agent doing both passes, say so out loud in the output ("critique pass, self-run") rather than silently merging them.

If you can't tell which environment you're in, ask once rather than guessing — dispatching a `.claude/agents/` reference in a tool that doesn't resolve it silently produces an inline execution that looks like a failed subagent call.

## Phase 0: Intake (orchestrator, inline)

Before dispatching anything, resolve where this run's output will live, then collect and write `brainstorm-intake.md` into that location. This is the scene-setting artifact every subsequent phase receives — they never interrogate the human directly, they read this file.

### Resolve the spec's output path (do this first)

Every brainstorm cycle is scoped to a **spec name** — a short kebab-case slug (`user-auth-service`, `billing-webhooks`). Propose one from the project intent (or, on an evergreen run, the module/feature name) and confirm it with the human rather than asking cold.

Check what's already on disk for that name:

```bash
ls -la docs/spec/[spec-name]/ 2>/dev/null
```

- **Nothing there** → first pass for this spec. This run's output path is `docs/spec/[spec-name]/` — flat, no version subfolder. Skip to "Collect in one pass" below.
- **A flat folder exists** (files sit directly in it, no `v.*` subfolder yet) → this is the spec's second pass. Before writing anything new:
  1. Create `docs/spec/[spec-name]/v.1.0/` and move every existing file/folder out of `docs/spec/[spec-name]/` into it, unchanged — the prior flat pass becomes the first recorded version, not a fresh v.1.0 write.
  2. Ask the human: is this pass a **modification** of what's already there (revising or refining existing decisions) or **additional** (new scope under the same spec name — e.g. a further module layered onto an evergreen project)? Modification → this run's output path is `v.1.1`. Additional → `v.2.0`.
- **Versioned subfolders already exist** → find the highest `v.<major>.<minor>` present. Ask the same modification-or-additional question, then bump from that highest version: modification increments the minor (`v.1.3` → `v.1.4`), additional increments the major and resets the minor to zero (`v.1.4` → `v.2.0`). This run's output path is that new version folder.

Whatever this resolves to, every artifact any phase produces this run — `brainstorm-intake.md`, `project-constitution.md`, `spec.md`, `adr/`, `context7-receipts.md` — writes into that one path, fully self-contained. Never reference a file in a sibling version folder by relative path; each version stands alone so a later `v.2.0` remains readable even if `v.1.0` is archived or deleted. Record the resolved path as the first line of `brainstorm-intake.md` (see the template in `references/templates.md`) so every downstream phase knows where to write without re-deriving this logic itself.

State the resolved path back to the human before moving on — e.g. "This run writes to `docs/spec/user-auth-service/v.2.0/`" — so there's no ambiguity about where output is landing.

### Collect in one pass (ask the human, don't guess)
1. **Project intent** — one paragraph, free-form
2. **Fixed constraints** — anything already locked (must use Postgres, must deploy on Railway, must use 1Password, etc.)
3. **Timeline category** — spike/prototype (days), MVP (weeks), production (months) — this materially changes Phase 2's tooling depth
4. **Greenfield or existing codebase?** — if existing, don't jump straight to `project-alignment`. Ask one more question first: **retrofit or evergreen?**
   - **Evergreen** means the project already runs the abstract-data pipeline and stays current on its own (a `.abstract-data/` directory exists — same detection `project-alignment` itself uses). Confirm rather than assume:
     ```bash
     test -d .abstract-data && abstract-data status --json
     ```
     If it reports stale items, offer `abstract-data pull && abstract-data apply`; proceed either way once the human's responded — don't block the brainstorm on a sync they didn't ask for. An evergreen project's language and tooling are locked by definition, so **Phases 1–2 are skipped** for this run. Jump straight to Phase 3, scoped to whatever new module or feature prompted this brainstorm, not the whole project.
   - **Retrofit** means the project isn't on the abstract-data pipeline yet, or its alignment has drifted past what a sync fixes. Stop the brainstorm cycle here and hand off to `project-alignment` instead — this skill doesn't re-derive stack decisions that skill already exists to audit properly.
   - If it's not obvious which one applies, ask the human directly. This is exactly the judgment call Phase 0 exists for, not something to infer silently from a directory's presence.
5. **Team context** — solo or team; if team, who plays which BMAD role (PM / Architect / Engineer / QA / DevOps — solo devs play PM + Architect, agents play the rest)

Use the intake template in `references/templates.md`. This file is append-only from here — each phase's locked decision gets appended after its `APPROVE`, so by Phase 4 it's the full decision log.

## Phases 1–3: dispatch, critique, gate

For each applicable phase — Language, Tooling, and Patterns on a greenfield or retrofit-then-resumed run; Patterns only on an evergreen run, since 1–2 are already locked:

1. Dispatch (or run inline) per the environment logic above, passing the subagent the full current `brainstorm-intake.md`.
2. The subagent produces its recommendation, then its own critique pass, and returns a result marked `PASS` or `REVISE` against that phase's evaluation criteria (defined in the phase's own file).
3. If the subagent's self-critique is `REVISE`, loop it once more with the specific objection before presenting anything to the human — don't surface an unresolved internal objection as if it were the final answer.
4. Present the phase's output to the human exactly as formatted by the subagent. Wait for `APPROVE` or `REVISE`.
   - `APPROVE` → append the locked decision to `brainstorm-intake.md`, mark the phase complete, move to the next phase.
   - `REVISE` → re-dispatch the same phase with the human's additional context folded into the prompt. This is a fresh generation, not a patch.

## Phases 4–5: synthesis, no gate

Constitution and Spec Draft don't propose new decisions — they formalize what Phases 1–3 already locked (or, on an evergreen run, what Phase 3 locked plus the project's existing constitution). No `APPROVE`/`REVISE` gate here; the gate already happened. On an evergreen run, Phase 4 writes a scoped addendum referencing the existing `project-constitution.md` rather than a duplicate one — the project already has an immutable stack section, this run only adds the new module's non-negotiables to it. The spec draft's quality gets checked properly in SDD Phase 2 by the existing `spec-reviewer` subagent, not re-litigated here.



## Delivering the result

When Phase 5 completes, the brainstorm cycle is done. Everything lands in the output path resolved back in Phase 0 — call it `[out]` below:
- `[out]/project-constitution.md` — on an evergreen run, non-negotiables and Context7 receipts only, plus a pointer back to the project's existing root constitution. No `-addendum-[module-name]` suffix on the filename anymore; the containing folder already carries that scoping.
- `[out]/spec.md` (draft, EARS format)
- `[out]/adr/adr-draft-stack-selection.md` (draft ADR, `Status: Proposed`, from Phase 3's architecture decision — see "ADR lifecycle" below; this is not yet part of the project's ADR log)
- `[out]/context7-receipts.md`
- `[out]/brainstorm-intake.md` (the full decision log, for reference)

Two worked examples:
- **First-ever brainstorm** for a spec named `user-auth-service` → `docs/spec/user-auth-service/project-constitution.md`, `.../spec.md`, `.../adr/adr-draft-stack-selection.md`, `.../context7-receipts.md`, `.../brainstorm-intake.md`, all flat.
- **Third pass** on that same spec — `v.1.0` (the migrated original) and `v.1.1` (a prior modification) already exist, and this pass is another modification — → `docs/spec/user-auth-service/v.1.2/project-constitution.md`, `.../spec.md`, and so on, nested entirely inside `v.1.2/`.

Then say plainly: "Phases 0–5 complete. Output written to `[out]`. Hand off to SDD Phase 2 (PLAN)." Don't ask if they want to continue into PLAN yourself — that's a different skill's job, and conflating them blurs the human review boundary that made the gates worth having.

## ADR lifecycle: draft → promoted

A brainstorm's architecture decision isn't project history yet — it's a recommendation the human just approved at a gate, sitting ahead of an EARS spec that's *still marked draft* and hasn't been through SDD Phase 2 review. Writing `Status: Accepted` into a project's real ADR log at this point would be recording a decision as final before it's actually been committed to. So the lifecycle has two distinct stages, and this skill only ever performs the first:

1. **Draft (this skill, Phase 3).** Written as `[out]/adr/adr-draft-[slug].md`, `Status: Proposed`, no ADR number — nested inside this brainstorm's own spec-scoped, versioned output folder, same as everything else. It records what Phase 3 recommended and the human approved *at the brainstorm gate*, nothing more.
2. **Promoted (later, gated on the spec proceeding — not this skill's job).** Only once the spec actually moves forward — accepted in SDD Phase 2, or the human otherwise commits to building it — does the draft get promoted into the project's real, project-root `docs/adr/` log:
   - Find the highest existing `docs/adr/ADR-*.md` at the project root; the new number is one past that (or `001` if `docs/adr/` doesn't exist yet — this may be the project's first-ever ADR even if it isn't the spec's first brainstorm pass).
   - Copy the draft's Context/Decision/Consequences into `docs/adr/ADR-<NNN>-[slug].md`, set `Status: Accepted`, and record the promotion date.
   - Leave the original draft in `docs/spec/[spec-name]/.../adr/` untouched (`Status: Proposed` stays as the historical record of the brainstorm), and add a one-line pointer in it: "Promoted to `docs/adr/ADR-<NNN>-[slug].md` on YYYY-MM-DD."
   - From that point on, `docs/adr/ADR-<NNN>-...md` is the append-only, canonical record — a later decision gets a new ADR, not an edit to this one.

This skill never performs step 2 itself — it hands off at Phase 5, before SDD Phase 2 has run, so it has no way to know whether the spec actually proceeds. If a spec is revised, shelved, or never built, its draft ADR just stays a draft inside its versioned spec folder indefinitely — that's the correct, unremarkable outcome, not a dangling task. Whoever runs SDD Phase 2 (or the human directly, if they're committing to build without it) owns triggering promotion.



## Anti-patterns this skill guards against

- **Tooling free-for-all** — a subagent recommending something outside AGENTS.md/DEV-ENV-INDEX without flagging it as an explicit override request. If nothing canonical fits, say so; don't quietly reach for whatever's fashionable.
- **Skipping Context7** — a Phase 2 output without a receipt for every library is incomplete, not just unpolished. Self-check before presenting.
- **Vague acceptance criteria** — Phase 5 rejects any requirement not in EARS form (`WHEN … THE … SHALL … SO THAT …`). "The system should be fast" isn't a criterion.
- **Constitution drift** — Phase 4 marks every non-negotiable as sourced from either the intake or a template constraint. It doesn't invent new ones; it's a formalizer, not a decision-maker.
- **Don't-only lists** — per AGENTS.md Base's own anti-pattern rule: every 🚫 in the constitution needs a paired ✅. A list of prohibitions with no alternatives makes agents overcautious rather than decisive.
- **Parallel phase execution** — Phases 1–5 are a dependency chain. Tempting to fan them out for speed; don't.
- **Treating every existing codebase the same** — assuming an existing project always needs the full `project-alignment` retrofit (wastes a cycle on an already-current project) or always just needs a quick `abstract-data` sync (skips a real audit a drifted project needs). Ask; don't default either way.
- **Flattening version history** — writing a second or later pass directly into `docs/spec/[spec-name]/` without first migrating the existing flat content into `v.1.0/`. This either overwrites the prior decision set or commingles two passes' artifacts in one un-versioned folder — always resolve the output path (including the migration) before any phase writes anything.
- **Treating the brainstorm's ADR as already accepted** — writing `Status: Accepted` or a real `ADR-NNN` number onto Phase 3's draft. Nothing here is project history until the spec actually proceeds and someone runs the promotion step in "ADR lifecycle" — the brainstorm only ever produces a proposal.

## Notion access

Phase 2, 3, and 4 subagents reference specific Abstract Data playbooks (the AGENTS.md bases, DEV-ENV-INDEX, Design Principles Gates, this skill's own templates). Prefer pulling these live via the Notion MCP each run — they change, and a stale bundled copy is worse than a live miss. If Notion is unreachable, fall back to `references/notion-playbook-excerpts.md` and say so explicitly in the phase output (e.g. "Notion unreachable — used bundled excerpt, verify against live docs before implementation"). Never present a fallback-sourced recommendation as if it came from a live pull.

## Promoting this skill from draft to stable

- [ ] Run >= 3 times across different project types
- [ ] All three gated phases (Language, Tooling, Patterns) completed with `APPROVE` on each run
- [ ] Constitution file produced with >= 3 non-negotiables per run
- [ ] Context7 receipt log has a receipt for every selected library, every run
- [ ] A resulting `spec.md`'s EARS criteria pass review on its first SDD Phase 2 cycle
- [ ] Output-path resolution verified on a real second pass: prior flat output correctly migrated into `v.1.0/`, the new pass isolated in its own version folder, nothing overwritten
- [ ] Phase 3's ADR output confirmed as `Status: Proposed` with no ADR number, never auto-promoted to `docs/adr/` during the brainstorm cycle itself
- [ ] `metadata.status` flipped to `stable`, `metadata.last_reviewed` set, and DEV-ENV-INDEX updated in the same session this skill is promoted

## Reference files

- `agents/spec-language-selector.md` — Phase 1 role definition
- `agents/spec-tooling-selector.md` — Phase 2 role definition
- `agents/spec-patterns-selector.md` — Phase 3 role definition
- `agents/spec-constitution-writer.md` — Phase 4 role definition
- `agents/spec-draft-writer.md` — Phase 5 role definition
- `references/templates.md` — intake / constitution / spec.md / Context7 receipt templates
- `references/notion-playbook-excerpts.md` — bundled fallback content for when Notion is unreachable
