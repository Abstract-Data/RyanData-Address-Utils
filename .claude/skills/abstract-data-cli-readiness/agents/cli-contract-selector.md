---
name: cli-contract-selector
description: Phase 2 of abstract-data-cli-readiness. Locks the agent/human output contract — the --json/--plain envelope, exit codes, TTY detection strategy, and streaming needs — mapped directly onto the 15-point Agentic CLI Design Scorecard. Runs after Phase 1's surface decision is locked.
---

# Agent/Human Output Contract — Phase 2

This is the highest-leverage phase in the whole cycle. Every scorecard point in "Output &
Parsing" (4 points) and most of "Interactivity" (3 points) and "Reliability" (3 points) get
decided here. Work through the scorecard directly — don't invent a separate framing for the same
decisions.

## Work through each scorecard category

**Output & Parsing (4 points) — decide all four:**
- **JSON flag on every command.** Confirm `--json` (not a synonym) will exist on every command
  that produces data, not just the "important" ones.
- **stdout/stderr separation.** State the rule plainly: stdout = data only, stderr = everything
  else (logs, progress, warnings, errors-as-messages). Name the Rich console setup —
  `Console()` for stdout, `Console(stderr=True)` for messages.
- **Structured errors.** Lock the error envelope shape now:
  `{"ok": false, "error": {"code": ..., "message": ..., "fix": ..., "retryable": ...}}`. The
  `code` values don't all need to be enumerated in this phase, but the shape does.
- **Schema versioning.** Decide the `schema_version` field's starting value (`"1"` or `"1.0.0"`,
  pick one and note it) and state the rule for bumping it — additive fields don't bump it,
  removing or renaming a field does.

**Interactivity (3 points) — decide all three:**
- **Non-interactive flag.** Name it — `--no-input`, `--yes`, or both if they mean different
  things (`--yes` skips confirmations, `--no-input` also refuses to prompt for missing values).
- **No hidden prompts.** State the rule: if every required flag/arg is supplied, nothing prompts,
  ever, TTY or not.
- **TTY detection.** Confirm `sys.stdin.isatty()` gates every prompt, and that failing the check
  produces the actionable error from the playbook's Questionary pattern (name the missing
  flag/env var), not a hang or a bare traceback.

**Reliability (3 points) — decide all three:**
- **Semantic exit codes.** Pick the scheme now — either the scorecard's minimal
  `0/1/2/3/4/5` (success/error/usage/auth/retry/conflict) or the fuller `sysexits.h` vocabulary
  from the playbook, and note that whichever is chosen, it gets documented in `--help` and the
  design doc, not left implicit.
- **Idempotent writes.** For each write operation the intake/spec surfaced, decide: is it safe
  to retry as-is, or does it need an idempotency key / conflict exit code? Don't leave this as
  "we'll figure it out during implementation" — that's exactly the kind of decision this phase
  exists to lock.
- **Paginated lists.** For each list-producing command, confirm `--limit`/`--cursor` (or an
  equivalent) rather than an unbounded dump.

**Discoverability (4 points) — decide all four, though these lean more into Phase 4/5:**
- **Labeled flags** — required vs. optional distinguished in `--help`.
- **Usage examples in `--help`** — confirm this is a requirement, not a nice-to-have.
- **Machine-readable catalog** — decide whether `commands --json` (or equivalent) ships in this
  version or is deferred, and say which.
- **A `SKILL.md`/`AGENTS.md`** documenting the contract — confirm this ships alongside the CLI,
  not as a someday-item.

**Safety (1 point):**
- **Dry-run support.** For every destructive operation the intake/spec surfaced, decide whether
  `--dry-run` with a structured JSON diff ships now or is explicitly deferred with a reason.

## Streaming

If the intake/spec surfaced long-running or large-result operations, decide now whether NDJSON
streaming is needed (one JSON object per line) or whether a single JSON object per invocation is
sufficient. The playbook's threshold: below "large/streamed result sets," a single object is
simpler and preferred — don't add streaming complexity a project doesn't need yet.

## Output format

```markdown
## Agent/Human Output Contract

### Scorecard mapping (all 15 points addressed)
| Scorecard criterion | Decision |
|---|---|
| JSON flag on every command | [...] |
| stdout/stderr separation | [...] |
| Structured errors | [envelope shape, verbatim] |
| Schema versioning | [starting value + bump rule] |
| Non-interactive flag | [...] |
| No hidden prompts | [...] |
| TTY detection | [...] |
| Semantic exit codes | [scheme + where documented] |
| Idempotent writes | [per-operation, or "N/A — no writes"] |
| Paginated lists | [per-command, or "N/A — no list commands"] |
| Labeled flags | [...] |
| Usage examples in --help | [...] |
| Machine-readable catalog | [ships now / deferred + reason] |
| SKILL.md / AGENTS.md | [confirmed] |
| Dry-run support | [per-operation, or "N/A — no destructive ops"] |

**Streaming:** NDJSON | single object — [reason]
**Open questions for the human:** [anything a scorecard row depends on that isn't yet known —
e.g. an idempotency scheme that needs a real key the intake didn't surface] | none
**Critique pass result:** PASS | REVISE — [specific objection, or omit if PASS]
```

An open question doesn't mean `REVISE` — only mark `REVISE` if a scorecard row genuinely can't be
filled in without the answer (an empty envelope shape, an undecided exit-code scheme). If every
row has a concrete decision and the question is about something adjacent, it's a `PASS` with the
question named.

## Critique pass

Before returning this, check: (1) all 15 scorecard rows are filled, with N/A used only where
genuinely inapplicable, not as a placeholder for "didn't think about it"; (2) the error envelope
and exit code scheme are concrete enough that Phase 5 can drop them into a design doc verbatim,
not left as "we'll design this later"; (3) idempotency and dry-run decisions were made per
operation the intake actually surfaced, not answered in the abstract; (4) on a Path B run where
Phase 0 marked a scorecard row ALIGNED, this table confirms the spec doc's stated approach rather
than silently redesigning it; (5) every row has an actual decision, not one that quietly depends
on something unconfirmed — if it does, that dependency belongs in Open Questions, not buried
inside the row's text. If any of these fail, mark `REVISE` and fix it yourself before it reaches
the human.
