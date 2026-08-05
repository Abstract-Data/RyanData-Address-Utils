# Bundled Notion Playbook Excerpts (fallback only)

Every subagent should prefer a live Notion pull over this file — it's a snapshot, not a subscription. Use this only when Notion is unreachable, and say so explicitly in the phase output when you do. Excerpts below were pulled directly from the source pages; verify against live Notion at implementation time since these playbooks are actively maintained.

## From "Spec-Driven Development — Constitution, Phases & Role Taxonomy" (Stable, last reviewed 2026-05-16)

**The constitution pattern (GitHub Spec Kit):** A constitution is a high-level, immutable set of project principles applied across every session. It answers what kind of project this is, what the non-negotiable constraints are, and what done looks like. It lives in the repo, is referenced from AGENTS.md, and is NOT a TASK.md — it defines permanent principles, not per-session tasks.

**The EARS pattern (AWS Kiro):**
```
WHEN [trigger condition]
THE [system component]
SHALL [required behavior]
SO THAT [business reason]
```
EARS criteria are directly executable as test cases — the criterion IS the test specification.

**BMAD role taxonomy:** PM (requirements, Phase 1), Architect (system design/ADRs, Phase 2), Engineer (implementation, Phase 4), QA (test cases, Phase 3+4), DevOps (deployment/CI-CD, Phase 4 infra tasks). Solo developers play PM and Architect; agents play Engineer, QA, and DevOps.

## From "AGENTS.md (Base)" (Stable v1.3.0, last reviewed 2026-06-08)

**Universal Python stack:** Python 3.11+ with uv for package management; pytest + Hypothesis for testing; ruff for linting and formatting; pre-commit hooks. Async-first design where I/O is involved; strong typing throughout; explicit over implicit; fail fast, fail loud.

**Agent Scope Declaration** (required immediately after the header of every generated AGENTS.md):
```
## Agent Scope
Reads:    {list directories/resources the agent may read}
Writes:   {list directories/resources the agent may write}
Executes: {list commands/tools the agent may run}
Off-limits: {list what is explicitly forbidden — prod DBs, secrets, other repos, etc.}
```

**Documentation Priority (required for all library code):** (1) Context7 MCP — resolve-library-id then get-library-docs, required, not optional, no exceptions for "well-known" libraries; (2) official docs via web search, only if Context7 doesn't index the library; (3) training-data knowledge, last resort, must be flagged inline with `# NOTE: based on training data — verify against current docs`. Priority libraries: pydantic-ai, tanstack-router/query/start, fastmcp, sqlmodel, supabase-py, polars.

**Conflict Resolution Hierarchy** (highest wins when concerns compete): Security > Correctness > Data integrity > Performance (only when backed by measurement) > Maintainability > Style.

**Definition of Done — Code Quality gate:** all tests pass, no linting errors, no formatting violations, type hints on all new public functions. **Safety & Security gate:** no secrets/tokens/credentials in committed code, no bare `print()`, no `eval()`/`exec()` with user input.

**Anti-pattern #1 — don't-only lists:** a list of ten-plus prohibitions with no paired alternatives degrades agent behavior — the agent becomes over-cautious and exploratory rather than decisive. Every 🚫 NEVER DO item must have a paired ✅ alternative in the same line.

**Anti-pattern #2 — LLM-generated AGENTS.md files:** running `/init` or asking an LLM to generate AGENTS.md produces files that reduce agent task success while increasing token cost. If a rule could be inferred from the codebase without being stated, it shouldn't be in AGENTS.md.

**Anti-pattern #3 — instruction bloat:** as instructions accumulate, compliance degrades uniformly across all instructions, not just the new ones. Keep always-loaded content under 5K tokens; audit anything over ~150 lines.

## From "DEV-ENV-INDEX — Agent-Queryable Reference" (last updated 2026-07-03)

**Canonical subagent deploy location:** `.claude/agents/` for Claude Code. `context7-mcp` is listed as "REQUIRED before writing any library-dependent code (not optional, not advisory)." `task-critic` is the completion auditor subagent — checks every requirement in TASK.md was actually implemented and wired, not just that tests pass; invoke before declaring any multi-step task complete.

**Design Principles Gates already exist as separate, mandatory blocking skills** — Python, TypeScript, Swift, and PostgreSQL, each checking a diff against P1–P17 principles with per-principle PASS/FAIL and line citations. This skill's Phase 3 does not reimplement them; it names which gate applies at implementation time.

## From "AGENTS.md (JS/TS Base)" (Stable v1.1.0, last reviewed 2026-07-02)

**Runtime & toolchain:** Node.js >= 22 (production / deploy target); Bun >= 1.3 (local dev runner —
native TS, no `tsc` step; pin exact, e.g. `1.3.11` — Bun has no LTS policy); TypeScript >= 5.4
(strict mode required). Use Bun for local dev (`bun run`, `bun install`); deploy targets the
Node 22 runtime — never use Bun-specific APIs (`Bun.file()`, `Bun.serve()`, `bun:sqlite`) in
source files that also need to run under Node.

**Package manager detection (required before any install command), in order:** (1) `"packageManager"`
field in `package.json`, (2) `bun.lock` present → bun, (3) `package-lock.json` → npm, (4) `yarn.lock`
→ yarn, (5) `pnpm-lock.yaml` → pnpm. Never run `bun install` in a project with a non-Bun lockfile
without explicit human approval, or vice versa.

**`bun test` vs `bun run test`:** different commands — `bun test` always invokes Bun's own test
runner; `bun run test` runs the `package.json` `"test"` script (which may be Vitest). Projects using
Vitest must always use `bun run test`; mixing the two causes silent test failures.

**Module system:** ESM required everywhere (`"type": "module"` in package.json). `tsconfig.json`:
`target: ES2022`, `module`/`moduleResolution: NodeNext`, `strict: true`,
`noUncheckedIndexedAccess: true`, `exactOptionalPropertyTypes: true`. Import paths must use `.js`
extensions even when importing `.ts` files (NodeNext requirement) — TanStack Router projects use
`moduleResolution: "bundler"` instead, via the `tsconfig.json (TanStack Router)` companion template.

**Type safety rules:** no `any` (use `unknown` then narrow); no non-null assertions (`!`) on API
responses; all async functions need explicit return types; prefer `type` over `interface` for data
shapes, `interface` for contracts; minimize `as` assertions (prefer narrowing; when unavoidable, a
`// SAFETY: reason` comment is required; never `as unknown as T` — fix the type at the source).

**Ecosystem overlays** (apply in addition to this base, required when detected): `AGENTS.md (TanStack
Router + Query)`, `AGENTS.md (TanStack Start)`, `AGENTS.md (Bun-Native)` for Bun-native production
deploys, `AGENTS.md (Astro)` for Astro projects (detected via `astro.config.*`/`astro` dep/`.astro`
files) — Astro's file-based routing and islands model differ fundamentally from Next.js/TanStack
Router, so those patterns don't apply under `src/pages/`.

**Reference Documentation to consult before implementing** (canonical "which pattern when" list):
TypeScript Design Principles Playbook (Next.js + TanStack + React) — mandatory, read first for any
TS/Next.js diff; React Composition Patterns — prevents god components/excessive useState/prop
drilling; Next.js App Router Architecture Anti-Patterns Playbook — nine highest-signal failure modes;
TanStack Ecosystem Architecture Guide — which TanStack package, version compatibility, Form v1 rules;
TanStack/Next.js Security Hardening playbooks — server-fn input validation, RSC/Server Actions
advisories.

This excerpt covers the tooling-decision-relevant sections (runtime, package manager, type safety,
overlays, reference docs to consult) needed for this skill's Phase 2/3 tooling decisions — it
deliberately omits the page's Notion-SDK-specific implementation patterns (client init, pagination,
error handling), which aren't relevant to a stack-selection brainstorm and would go stale fastest.

## What's deliberately NOT bundled here (live-pull only in this version)

These are referenced by name in the phase files but not excerpted, because getting them wrong from a stale copy is worse than a clean "Notion unreachable" flag:

- **Python / TypeScript / Swift / PostgreSQL Design Principles Playbooks** (the actual P1–P17 lists) — Phase 3 defers to the existing Design Principles Gate skills rather than needing these inline.
- **ARCHITECTURE.md template, GUARDRAILS.md template, SKILL.md Amendment Template** — pull live when Phase 3/4 needs the exact current structure.

If you hit one of these gaps with Notion unreachable, don't guess at the missing content — note the gap in the phase output and let the human decide whether to proceed or wait for connectivity.
