---
name: spec-draft-writer
description: Phase 5 of abstract-data-spec-brainstorm. Writes the initial spec.md using EARS-format acceptance criteria, drawing on the locked constitution and the original intake. This is SDD Phase 1 (SPECIFY) output — the last thing this skill produces before handoff. Only runs after Phase 4's constitution is written.
---

# Spec Draft Writer — Phase 5

This is an evaluator-optimizer phase, same as 1–3, except there's no human gate at the end of it — the draft gets reviewed properly once it enters SDD Phase 2, by the existing `spec-reviewer` subagent. Your job is to make sure it's a genuinely usable first draft, not a placeholder.

## EARS format (non-negotiable for every functional requirement)

```
WHEN [trigger condition]
THE [system component]
SHALL [required behavior]
SO THAT [business reason]
```

This isn't formatting preference — EARS criteria are directly executable as test specifications; the criterion *is* the test spec. "The system should be fast" is not a criterion in this format and must be rejected, not softened into one. If a requirement resists being written as trigger → component → behavior → reason, that's usually a sign the requirement itself is still too vague — push back to the human rather than forcing a bad EARS statement.

## Structure

```markdown
# spec.md — [Project Name]
## Version: 0.1.0 (Draft)
## Date: [YYYY-MM-DD]
## Constitution: ./project-constitution.md

## Problem Statement
[1–2 paragraphs — what the system does and why]

## Scope
### In scope
- [bullets]
### Out of scope
- [bullets — this section exists specifically to keep implementation agents from scope-creeping later; don't skip it]

## Functional Requirements
### [Feature / Module 1]
WHEN [trigger]
THE [component]
SHALL [behavior]
SO THAT [reason]

### [Feature / Module 2]
...

## Non-functional Requirements
- Performance: [specific and measurable, e.g. "P95 latency < 500ms on Railway free tier" — not "should be fast"]
- Security: [e.g. "All credentials via 1Password Environments — never in env vars"]
- Data integrity: [e.g. "Supabase RLS enabled on every table before first write"]

## Open questions (for human to resolve before Phase 2 PLAN)
- [unresolved decision list — it's fine for this to be non-empty]
```

Every non-functional requirement must cite the constitution file for its source — if you're writing a security or data-integrity requirement that isn't traceable to something the constitution already locked, that's either a new decision that should have surfaced in Phases 1–3, or it's genuinely out of scope for this draft. Flag it in Open Questions rather than inventing it here.

## Critique pass (EARS compliance check)

Before returning the draft, walk every functional requirement and confirm it's genuinely in WHEN/THE/SHALL/SO-THAT form, not prose wearing EARS-shaped headers. Reject and rewrite anything that fails this — a spec with three good EARS criteria and one paragraph of vague prose is not a passing draft, it's a draft with a flagged gap. Note any rejected/rewritten items in the handoff so the human knows where the draft was weakest.
