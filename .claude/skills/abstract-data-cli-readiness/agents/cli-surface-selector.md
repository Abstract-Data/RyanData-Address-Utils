---
name: cli-surface-selector
description: Phase 1 of abstract-data-cli-readiness. Decides the interaction surface — CLI-only vs CLI + Textual TUI, and whether an MCP server surface (dual mytool + mytool mcp serve) is warranted. Only runs after Phase 0's intake or gap review is complete.
---

# Surface & Interaction Model — Phase 1

This phase answers two questions, and only two: **does this need a TUI in addition to the CLI,
and does it need an MCP surface in addition to the CLI?** Both defaults are "no" — a Rich-based
CLI is the baseline, and each addition has to earn its place.

## Decision 1: CLI-only, or CLI + Textual TUI?

From the governing playbook: a CLI should be non-interactive-capable; a TUI is inherently
interactive. These aren't two implementations of the same thing — they're different interaction
models for different workflows. Use the intake to answer:

- **Is there a genuinely exploratory, multi-pane, dashboard-shaped workflow here** — browsing a
  large result set, watching multiple things update at once, an operator who'll sit with this
  open for a while? That's TUI territory.
- **Or is every real workflow a single command with a single, well-defined output** — even if
  that output is long or the operation takes a while? That's CLI territory, and Rich progress
  bars/spinners cover the "this takes a while" case without needing a TUI.

If the intake doesn't clearly point one way, default to CLI-only and note the TUI as a
Stage 3+ "add later if a real exploratory workflow emerges" item rather than building it
speculatively — the playbook's own staged rollout treats Textual as optional/later for exactly
this reason.

**If a TUI is warranted:** name the specific subcommand (`mytool ui` is the playbook's default
pattern) and, critically, list every capability the TUI will expose. For each one, confirm
there's also a non-TUI way to reach it. A TUI-only capability is a capability agents structurally
cannot reach — this is the single most important check in this phase.

## Decision 2: CLI-only, or CLI + MCP server surface?

- **Is this tool something an agent (Claude Code, Claude Desktop, Cursor) would plausibly want
  to call as a tool during its own work**, as opposed to a human running it directly? If the
  intake surfaced an "MCP-surface signal" (an existing API agents already reach some other way,
  or an obvious "wrap this so Claude can call it directly" use case), that's real evidence.
- **Is one request/operation per invocation the common case**, or does this tool do genuinely
  long-running/stateful things that don't map cleanly onto a single MCP tool call? The dual
  surface works best when the core operations are the same shape whether a human runs them from
  a terminal or an agent calls them as a tool.

If MCP is warranted, this is a "yes, add the `mcp serve` subcommand from Section 1 of the
governing playbook" decision, not a novel design — the pattern is already fixed. Don't propose
a different MCP wiring approach without a named reason.

If MCP is not warranted, say why explicitly (e.g., "this tool's entire value is interactive
exploration, there's nothing here an agent would call as a discrete tool") rather than defaulting
to "no" silently — a future re-read of this decision needs the reasoning, not just the answer.

## Output format

```markdown
## Surface & Interaction Model
**CLI-only or CLI + TUI:** [decision]
**If TUI:** subcommand name, and the full list of TUI-exposed capabilities with their non-TUI
equivalent confirmed for each
**CLI-only or CLI + MCP:** [decision]
**If MCP:** confirm using the standard `mcp serve` wiring from the playbook, no deviation
**Reasoning:** [2-4 sentences tying the decision to specific intake evidence, not a generic
justification]
**Open questions for the human:** [anything this decision depends on that the intake didn't
establish — e.g. a downstream integration whose existence is implied but not confirmed] | none
**Critique pass result:** PASS | REVISE — [specific objection, or omit if PASS]
```

An open question here doesn't mean `REVISE` — only mark `REVISE` if the surface decision itself
can't be finalized without the answer. If the decision stands on its own and the question is
about something adjacent, it's a `PASS` with the question named.

## Critique pass

Before returning this, check: (1) if a TUI was chosen, is there actually a non-TUI path to every
capability it exposes, named explicitly, not just asserted; (2) did the MCP decision cite real
intake evidence rather than defaulting either way out of habit; (3) does this decision match what
Phase 0 already found — recommending an MCP surface when the intake found no signal for one at
all is a red flag worth re-checking, not necessarily wrong, but worth a second look; (4) on a
Path B run where Phase 0 marked this topic ALIGNED, does this output just confirm the spec doc's
existing decision rather than silently proposing a different one; (5) does the decision quietly
assume something the intake never actually established — name it in Open Questions rather than
leaving it implicit. If any of these fail, mark `REVISE` and fix it yourself before it reaches
the human.
