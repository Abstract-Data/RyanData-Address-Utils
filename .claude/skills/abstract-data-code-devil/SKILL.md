---
name: abstract-data-code-devil
description: >-
  Runs a ruthless, evidence-driven adversarial code review using a nested council of subagents
  (LeadCritic, RedTeamAttacker, SecurityAuditor, MaintainabilityEnforcer, FailureModeAnalyst,
  Synthesizer) that override the default agreeable/sycophantic LLM behavior and surface real
  security, correctness, reliability, maintainability, and performance risks with concrete evidence
  and failure modes. Use WHENEVER the user wants a hard, honest, no-flattery review of code, a diff,
  a PR, or a module — including "tear this apart", "brutal code review", "what will break", "red team
  this code", "find the failure modes", "adversarial review", "stress test this design", "is this
  production-ready", "review this PR harshly", or when a normal review would be too soft. Grounds
  library claims in Context7 docs when available and writes a review receipt confirming which critics
  ran and what was checked. Do NOT use for writing new features, generic style linting, or when the
  user wants encouraging feedback.
metadata:
  version: 0.9.1
---

# abstract-data-code-devil

A council of nested subagents that reviews code the way a burned-out principal engineer would after
one too many 3am incidents: no flattery, no "looks good overall," just force-ranked, evidence-backed
problems and the failure modes they lead to. The whole point is to defeat the model's default
instinct to be agreeable, because that instinct is exactly what lets real flaws ship.

Everything the critics need lives inside this skill (`prompts/`, `scripts/`, `references/`), so the
review is self-contained and portable across environments.

---

## Core principles (why this skill exists)

LLMs are trained to be helpful and agreeable, which quietly biases code review toward reassurance.
That bias is the enemy here. Every subagent prompt in `prompts/` opens with hard anti-sycophancy
rules, and the orchestration below exists to keep that stance intact end to end:

- **Anti-sycophancy is non-negotiable.** No praise, no "overall this looks solid," no softening
  ("minor", "consider", "nice to have"). Lead with problems or state plainly there are none. Value
  is measured by legitimate high-impact issues found, not by how the author feels.
- **Adversarial default.** Assume the code is mediocre until the evidence proves otherwise. The job
  is to protect the system and the humans who will suffer its failures, not the author's ego.
- **Evidence mandate.** Every finding quotes or precisely references the code. Anything that can't be
  pinned to specific lines or a concrete data flow is labeled "potential — requires manual
  verification." This is what keeps the critics from hallucinating severity.
- **Stakes framing.** Treat the code as if it runs in production with real users, data, and money. A
  missed flaw becomes an outage, breach, or corruption. Err toward surfacing, and be specific about
  the failure mode.
- **Negative constraints.** Don't flag theoretical risks needing unlikely preconditions, don't
  recommend a library unless it fixes a concrete flaw here, don't review unchanged code or style
  preferences.

If the user explicitly wants supportive or encouraging feedback, this is the wrong skill — say so
rather than dialing the critics down, because a half-adversarial critic is worse than an honest
normal review.

---

## The council (nested subagents)

Each critic is a bundled prompt at `prompts/{Name}/current.md`. Dispatch them with the Task tool,
passing the prompt file contents as the agent instructions along with the code/diff and profile. The
prompts are the authoritative source of each critic's rules — read them, don't paraphrase from
memory.

| Subagent | Prompt file | Role |
|---|---|---|
| **Cartographer** | `prompts/Cartographer/current.md` | Runs first. Neutral map of what the project *claims* to do (docs) vs. what the code *actually* does, plus claimed-vs-observed divergences. Establishes the shared intended-behavior baseline the critics attack. |
| **LeadCritic** | `prompts/LeadCritic/current.md` | Initial full structured adversarial review. |
| **RedTeamAttacker** | `prompts/RedTeamAttacker/current.md` | Attacks the other critics' output — finds leniency, weak evidence, missed issues; forces upgrades. |
| **SecurityAuditor** | `prompts/SecurityAuditor/current.md` | Deep security: auth bypass, injection, secrets, supply chain, OWASP, real exploit narratives. |
| **MaintainabilityEnforcer** | `prompts/MaintainabilityEnforcer/current.md` | Long-term debt: coupling, hidden assumptions, god objects, testability, future-maintainer pain. |
| **FailureModeAnalyst** | `prompts/FailureModeAnalyst/current.md` | Pre-mortems: realistic production failure stories tied to specific constructs and missing controls. |
| **Synthesizer** | `prompts/Synthesizer/current.md` | Consolidates, dedupes, re-prioritizes, upgrades, verifies evidence; produces one hardened report. |

`prompts/README.md` is the registry of critics and versions. When you change a prompt, snapshot the
old one to `prompts/{Name}/vX.Y.Z.md` and bump the version header in `current.md`.

---

## Modes

Pick based on scope and stakes; confirm with the user at Checkpoint A.

All modes except `quick` open with a **Cartographer** recon pass so the critics share one grounded
picture of intended vs. actual behavior.

| Mode | Cartographer | First Critic | Participating Specialists | Notes |
|------|--------------|--------------|---------------------------|-------|
| `audit-only` (default) | Yes | LeadCritic | SecurityAuditor, MaintainabilityEnforcer, FailureModeAnalyst, RedTeamAttacker | Read-only; hardened report only |
| `full` | Yes | LeadCritic | All specialists | Debate rounds + optional second RedTeamAttacker pass |
| `security-deep` | Yes | SecurityAuditor | LeadCritic, FailureModeAnalyst, RedTeamAttacker | SecurityAuditor leads and expands |
| `maintainability-deep` | Yes | MaintainabilityEnforcer | LeadCritic, RedTeamAttacker | MaintainabilityEnforcer leads |
| `quick` | No | LeadCritic | None (Synthesizer only) | Cartographer skipped for speed |

- **`audit-only`** *(default, read-only)* — Cartographer → LeadCritic + parallel specialists →
  Synthesizer. No code changes, just the hardened report.
- **`full`** — audit-only plus debate rounds and an optional second RedTeamAttacker pass on the final
  report. Use for high-stakes or pre-release code.
- **`security-deep`** — SecurityAuditor leads and expands; others support. For auth, payments, data
  handling, anything internet-facing.
- **`maintainability-deep`** — MaintainabilityEnforcer leads. For refactors and legacy rescue.
- **`quick`** — LeadCritic + Synthesizer only (Cartographer skipped). For small diffs where intent is
  obvious and the full council is overkill.

---

## Execution

### Step 0 — Profile & scope — then **Checkpoint A**

Establish, from the request and a quick look at the target:

- What's under review: whole repo, a module, or a diff/PR. Prefer a diff when one exists — reviewing
  unchanged code wastes the council's attention.
- Language/stack and framework (Python/FastAPI, TS/Next.js, etc.).
- Purpose, threat model, and any constraints the user gives.
- **Context7 pre-fetch** (see `references/context7.md`): if the code leans on identifiable libraries
  and the Context7 tools are available, resolve the library IDs and pull the relevant docs *now* so
  every critic validates version-specific claims against real documentation instead of stale training
  data. If Context7 isn't available, note that in the profile so findings that hinge on library
  behavior get flagged "requires manual verification."
- Optional tool augmentation: feed in linter/SAST output (ruff, mypy, bandit, semgrep, eslint) so the
  critics validate and prioritize those findings and hunt for what the tools missed.

**Checkpoint A — stop and confirm with the user:** the scope, the mode, and whether Context7 docs
were pulled. Don't launch the council until scope is agreed; a mis-scoped review burns the most
tokens for the least signal.

### Step 1 — Cartographer (recon; skipped in `quick`)

Dispatch Cartographer (`prompts/Cartographer/current.md`) with the repo/diff, available docs, and any
Context7 excerpts. It returns a neutral map: what the project *claims* to do (attributed to docs),
what the code *actually* does (with file references), and — most valuable — the claimed-vs-observed
divergences.

**Show the user Cartographer's map before the critics run.** This is what lets them confirm the
council actually understands the project, and it's cheap insurance against reviewing the wrong thing.
If the user says the map misreads intent, correct the profile now — that correction propagates to
every critic. Then pass the full map into every downstream critic as shared context; the divergence
list is a seeded source of findings (each critic decides severity). Because Cartographer is strictly
descriptive, it does not soften the critics — it arms them.

### Step 2 — LeadCritic

Dispatch LeadCritic (`prompts/LeadCritic/current.md`) with the code/diff, the profile, Cartographer's
map, and any Context7 excerpts and tool output. It produces the initial structured report in the
mandatory format (see below).

### Step 3 — Parallel specialists

In a single turn, dispatch the specialists that fit the mode — RedTeamAttacker, SecurityAuditor,
MaintainabilityEnforcer, FailureModeAnalyst — each with the code, profile, Cartographer's map,
Context7 excerpts, and the LeadCritic report. Running them together keeps the review fast and lets
each attack independently before anyone reconciles.

### Step 4 — Synthesizer (+ optional debate)

Dispatch Synthesizer (`prompts/Synthesizer/current.md`) with every prior report. It dedupes,
re-ranks by severity × blast radius, upgrades under-stated findings, verifies each finding still has
evidence, and emits the single hardened report. In `full` mode, run one more RedTeamAttacker pass on
the Synthesizer output and fold in whatever it hardens.

### Step 5 — Validate, write receipt, deliver — then **Checkpoint B**

- **Validate evidence.** Spot-check that top findings actually reference real lines/flows. Anything
  unverifiable gets demoted to "potential — requires manual verification." A confident-but-wrong
  finding destroys the council's credibility faster than a missed one.
- **Write the review receipt.** Run `scripts/write_receipt.py` (see below) to record which critics
  ran, the mode, Context7 usage, finding counts by severity, and the reviewed-surface checklist. This
  is the artifact that confirms the review actually happened and what it covered — deliver it
  alongside the report.
- **Deliver** the Synthesizer report plus the receipt.
- **Checkpoint B (high-stakes runs):** for security-deep, full, or anything the user flags as
  pre-release, pause and confirm the user has seen the Critical/High findings before considering the
  engagement closed.

---

## Mandatory output format (all critics)

This format is one of the highest-leverage controls — it's what forces specificity and blocks vague
reassurance. Each critic prompt restates it; keep them consistent with this canonical version.

**Top Highest-Impact Issues** — force-ranked 1–N by severity × blast radius.

Then only the categorized sections that have findings:
Security & Attack Surface · Correctness, Logic Errors & Edge Cases · Reliability, Error Handling &
Resilience · Maintainability & Technical Debt · Performance & Scalability · Testing & Verification
Gaps · Architecture & Design Flaws · Dependency / Supply Chain / Environment Risks.

Every finding uses exactly these six fields:

- **Severity** — Critical / High / Medium / Low
- **Location** — `file.py:123` or module/function + short context
- **Evidence** — exact code quote or precise data-flow/assumption
- **Why it is a problem** — the specific failure mode
- **Impact if unaddressed**
- **Concrete remediation** — diff-style fix or clear steps; if there's no simple fix, explain the
  trade-off

Always-included closing sections:

- **Easiest breakage paths** — how a malicious actor or careless future dev most easily causes harm.
- **Pre-mortem scenarios** — 2–4 realistic ways this causes a major incident in the next 6–12 months,
  tied to specific code.

Forbidden everywhere: overall positive/"balancing" summaries, generic best-practice advice untied to
a concrete flaw here, style nits that aren't real bugs, and softening words ("minor", "consider",
"nice effort").

---

## Receipts (confirming the review happened)

The skill's `scripts/write_receipt.py` writes a JSON + Markdown receipt so the user can confirm — and
later audit — exactly what was reviewed. Run it in Step 5 once the Synthesizer report is final, using
the full path from this skill's directory (e.g., `.claude/skills/abstract-data-code-devil/scripts/write_receipt.py`):

```bash
python .claude/skills/abstract-data-code-devil/scripts/write_receipt.py \
  --target "<repo/module/diff description>" \
  --mode audit-only \
  --critics Cartographer,LeadCritic,RedTeamAttacker,SecurityAuditor,MaintainabilityEnforcer,FailureModeAnalyst,Synthesizer \
  --context7 used \
  --critical 2 --high 5 --medium 8 --low 3 \
  --checked "auth,input validation,error handling,concurrency,dependencies,tests" \
  --out ./review-receipt
```

The receipt records the mode, every critic that ran, whether Context7 grounding was used, the
severity tally, and the surface-area checklist — the evidence that everything was reviewed rather
than a subset quietly skipped. Treat a run without a receipt as incomplete.

---

## Context7 grounding

Version-specific claims ("this FastAPI dependency runs per-request", "this Next.js route is
statically cached") are exactly where stale training data produces confident-but-wrong findings. When
the Context7 tools are available, resolve library IDs and pull docs during Step 0 and pass the
excerpts to every critic. See `references/context7.md` for the resolve→fetch flow and how critics
should cite the docs. When Context7 is unavailable, library-behavior findings must be labeled
"requires manual verification" rather than asserted.

---

## Integration

- **`project-alignment` first.** Run it (audit-only/critical-only) to fix structure, docs, AGENTS.md,
  and hooks, then point this skill at the implementation logic, security, and maintainability. The two
  are complementary: one aligns the scaffolding, this one attacks the substance.
- **Domain-specific critics.** For specialized code (election data integrity, redistricting/geospatial,
  txelections tooling), extend the council with a subagent focused on reproducibility, auditability,
  and domain edge-case failure modes — same anti-sycophancy and evidence rules, added to `prompts/`.
- **Notion logging (optional).** If the user works out of the Abstract Data Notion workspace, offer to
  log the receipt and top findings there after delivery.
