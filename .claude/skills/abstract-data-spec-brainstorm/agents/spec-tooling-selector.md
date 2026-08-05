---
name: spec-tooling-selector
description: Phase 2 of abstract-data-spec-brainstorm. Recommends package manager, framework, data layer, test stack, deploy target, and observability against the locked language and the DEV-ENV-INDEX canonical tool list, with a mandatory Context7 receipt for every library selected. Only runs inside the brainstorm cycle, after Phase 1 is locked.
---

# Tooling & Framework Selection — Phase 2

This is the most consequential phase — a wrong tooling call here compounds through the entire implementation. You're not inventing a stack; you're selecting from the canonical one, per the rule in the orchestrator's non-negotiables. If nothing canonical fits the intake, say that explicitly rather than reaching for something unlisted.

## Decision tree

**If Python was selected:**
```
Package manager: uv (always)
Framework:       FastAPI (API/service) | None (pipeline, script, CLI)
Data layer:       SQLModel + Supabase (relational, app state) | Polars (data pipeline / ETL) | None (an external system is the actual source of truth — e.g. a config-orchestration CLI wrapping someone else's API)
Test stack:       pytest + Hypothesis
Linting:          ruff (target py312, line-length 100)
Deploy:           Railway | Vercel (serverless) | bare Docker | N/A — packaged for `uv tool install` / PyPI-style distribution (CLI/local tool, nothing running to deploy)
Observability:    Logfire + Axiom + Checkly | structured logging to stdout only (on-demand CLI/local tool — there's no uptime to monitor between invocations)
Secrets:          1Password Environments (always)
```

A CLI or local tool is a legitimate project shape, not a stripped-down service — don't force service assumptions onto it. If the intent is "wrap someone else's API so I stop clicking through their UI" rather than "run continuously and hold state," the `None` / `N/A` options above are the correct canonical answer, not a gap to paper over with a Railway deploy or a Supabase table it doesn't need.

**If TypeScript was selected:**
```
Runtime:          Bun (preferred) | Node.js
Framework:        Next.js (full-stack) | TanStack Start | Astro (content/SSG or full-stack SSR) | None (CLI/local tool)
Query layer:      TanStack Query | Supabase client | None (CLI/local tool, no persisted app state)
Routing:          TanStack Router | Next.js App Router | N/A (CLI/local tool)
Test stack:        Vitest + Playwright
Linting:          ESLint + Prettier
Deploy:           Vercel (Next.js/Astro) | Cloudflare (Astro + Workers — the default target absent an existing adapter) | N/A — published as an npm package / distributed binary (CLI/local tool)
Infra:            Terraform, if the project needs provisioned cloud resources beyond a simple deploy
```

*The TypeScript CLI branch above is added by direct analogy to the Python one and hasn't been exercised by a real brainstorm run yet — treat it as lower-confidence than the rest of this tree until a real TS CLI intake tests it.*

If the intake describes something these trees don't cover cleanly (a Swift client, a data-science-heavy Python project, a monorepo spanning both), don't force-fit — name the gap and propose the closest canonical match with the deviation flagged.

## Context7 requirement (mandatory)

For every library in your recommendation, before finalizing: call `resolve-library-id` then `get-library-docs`, and append a receipt to `context7-receipts.md` in this run's resolved output path (the path recorded at the top of `brainstorm-intake.md` — e.g. `docs/spec/user-auth-service/context7-receipts.md` on a first pass, or `docs/spec/user-auth-service/v.1.1/context7-receipts.md` on a later one):

```markdown
## Context7 Receipt — [Library Name] [version]
- resolve-library-id result: [id]
- get-library-docs: [confirmation + key version-specific notes]
- Version-sensitive APIs noted: [any breaking changes observed, or "none"]
```

This is required for every library, not just the exotic ones — pydantic-ai, tanstack-router/query/start, fastmcp, sqlmodel, supabase-py, and polars all have version-sensitive APIs that break silently on training-data assumptions. If Context7 doesn't index a library, fall back to official docs via web search, and if you end up writing anything from training-data memory anyway, flag it inline: `# NOTE: based on training data — verify against current docs`. A tooling recommendation without a receipt for every selected library is not done.

## Output format

```markdown
## Tooling Stack Recommendation
**Package manager:** [tool + version]
**Framework:** [tool + version] | None
**Data layer:** [tool + version]
**Test stack:** [tools]
**Deploy:** [target]
**Observability:** [tools, if applicable to timeline category]
**Infra-as-code:** Terraform — YES | NO
**Context7 receipts:** [confirm one exists per library above, link to context7-receipts.md in this run's output path]
**Critique pass result:** PASS | REVISE — [specific objection, or omit if PASS]
```

## Critique pass

Check your own output against four things before returning it: (1) did every library actually get a receipt, not just the notable ones; (2) does anything here fall outside the decision tree without an explicit, named reason; (3) does the deploy/observability depth actually match the intake's timeline category (a days-scale spike doesn't need the full Logfire/Axiom/Checkly stack); (4) if this is a CLI or local tool, did the recommendation actually reach for the `None`/`N/A` data-layer, deploy, and observability options above, or did it default to service assumptions out of habit. If any of these fail, mark `REVISE` and fix it yourself before it reaches the human — don't surface a known gap as if it were finished.
