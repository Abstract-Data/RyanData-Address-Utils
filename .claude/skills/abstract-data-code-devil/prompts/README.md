# abstract-data-code-devil — Subagent Registry

The council's critics live here as bundled prompts. Each `{Name}/current.md` is the authoritative,
in-force version of that critic. SKILL.md dispatches them via the Task tool by reading the prompt
file and passing it as the subagent's instructions along with the code/diff, profile, Context7
excerpts, and any prior critic reports.

## Critics

| Subagent | Version | Prompt | Runs in modes | Role |
|---|---|---|---|---|
| Cartographer | 0.9.1 | `Cartographer/current.md` | all except `quick` | Runs first. Neutral claimed-vs-observed map establishing the intended-behavior baseline. |
| LeadCritic | 0.9.1 | `LeadCritic/current.md` | all | Initial full structured adversarial review. |
| RedTeamAttacker | 0.9.1 | `RedTeamAttacker/current.md` | audit-only, full, security-deep, maintainability-deep | Attacks other critics' output; forces upgrades. |
| SecurityAuditor | 0.9.1 | `SecurityAuditor/current.md` | audit-only, full, security-deep | Deep security / exploit analysis. |
| MaintainabilityEnforcer | 0.9.1 | `MaintainabilityEnforcer/current.md` | audit-only, full, maintainability-deep | Long-term technical-debt analysis. |
| FailureModeAnalyst | 0.9.1 | `FailureModeAnalyst/current.md` | audit-only, full, security-deep | Pre-mortem / reliability failure modes. |
| Synthesizer | 0.9.1 | `Synthesizer/current.md` | all | Consolidates into one hardened final report. |

`quick` mode runs LeadCritic + Synthesizer only (Cartographer skipped).

**Cartographer is the one exception to the adversarial contract below:** it is strictly descriptive —
no praise, no criticism, no severity — because its output is the neutral baseline the critics measure
against. Its map (especially the claimed-vs-observed divergences) is fed into every critic as shared
context.

## Shared contract (every critic)

1. Opens with hard anti-sycophancy rules — no praise, no softening, adversarial default.
2. Evidence mandate — every finding quotes/points to real code; uncertain ones labeled
   "potential — requires manual verification".
3. Uses the mandatory six-field finding structure and the canonical section list from SKILL.md.
4. Grounds library-specific claims in Context7 excerpts when provided; otherwise flags them for
   manual verification.
5. Ends after the pre-mortem section — no positive summary, no closing pleasantries.

## Versioning

On any change to a critic, snapshot the current file to `{Name}/vX.Y.Z.md` before editing, then bump
the `# Version:` header in `current.md` and update the table above. This mirrors the Abstract Data
`current.md` + snapshot convention so a review's behavior is always traceable to a versioned prompt.
