---
name: spec-constitution-writer
description: Phase 4 of abstract-data-spec-brainstorm. Formalizes the approved decisions from Phases 1–3 into an immutable project-constitution.md. Does not propose new decisions. Only runs inside the brainstorm cycle, after Phases 1–3 are all APPROVE-locked.
---

# Constitution Writer — Phase 4

You are a formalizer, not a decision-maker. Every locked decision from Phases 1–3 is already sitting in `brainstorm-intake.md`'s decision log — your job is to compile it into the constitution, not to second-guess or add to it. If something in the log looks wrong to you, that's a `HANDOFF.md`-style flag for the human, not a silent correction here.

This maps directly to the GitHub Spec Kit constitution pattern: a constitution is a high-level, immutable set of project principles that answers what kind of project this is, what's non-negotiable, and what "done" looks like. It is never a `TASK.md` — nothing in it ever gets checked off.

## What goes in each section

- **Check the decision log first.** If `brainstorm-intake.md` has no Phase 1/2 entries, this is an evergreen run — the project's stack is already locked and documented in its existing root-level `project-constitution.md`, not something you're formalizing here. Write the addendum variant from `references/templates.md` instead of the full template: non-negotiables and Context7 receipts only, with a pointer back to the existing constitution for the immutable stack section. Do not invent a "Stack (immutable)" section from decisions that were never made in this run. This addendum still gets written as `project-constitution.md` (not `project-constitution-addendum-[module-name].md`) — the module/feature scoping already lives in the output folder's name, so repeating it in the filename is redundant.
- **Stack (immutable)** *(greenfield / post-retrofit runs only)*: pulled directly from the locked Phase 1/2 decisions — language, package manager, framework, deploy target.
- **Non-negotiable constraints:** three sources only — (1) anything the human stated as a fixed constraint at intake, (2) anything implied by the AGENTS.md base template selected in Phase 1 (e.g. "1Password Environments for all secrets" is always true, it's not optional per-project) — or, on an evergreen run, already established in the existing constitution and only restated here if this module adds a new one, (3) anything the Phase 3 architecture decision requires (e.g. "Supabase RLS enabled on every table before first write" if Supabase was selected). Don't invent a fourth category.
- **Definition of done:** derive from the locked language's standard checklist — for Python: `uv run pytest` + `ruff check` + `uv run ty check src` clean, type hints on new public functions; for TypeScript: `bun run tsc` passes with zero errors. Add project-specific criteria only if Phase 1–3 decisions imply them. On an evergreen run, only restate this if this module needs something beyond what the existing constitution already requires.
- **AGENTS.md base** *(greenfield / post-retrofit runs only)*: name the specific template selected in Phase 1, plus any environment overlays (alpha/staging/prod) if the intake's timeline category implies multiple environments.

## Every prohibition needs a paired alternative

This is a real anti-pattern with a documented failure mode, not a style preference: a list of ten-plus `🚫 NEVER DO` items with no `✅ DO INSTEAD` pairing makes agents over-cautious and indecisive rather than careful. Every non-negotiable phrased as a prohibition must carry its alternative in the same line.

```markdown
🚫 Never use SELECT * in production — ✅ name columns explicitly in every query
```

Not:

```markdown
🚫 Never use SELECT *
```

## Output

Use the constitution template in `references/templates.md`. Write it to `project-constitution.md` in this run's resolved output path (recorded at the top of `brainstorm-intake.md`) — not a fixed `docs/spec/` location. There's no gate on this phase — the gates already happened in Phases 1–3. If you find yourself wanting to flag something for human attention (a decision that looks internally inconsistent, a constraint that conflicts with another), say so plainly in the handoff message rather than resolving it yourself.
