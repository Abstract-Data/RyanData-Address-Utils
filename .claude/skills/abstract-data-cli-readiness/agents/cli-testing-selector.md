---
name: cli-testing-selector
description: Phase 4 of abstract-data-cli-readiness. Locks the testing and CI contract — CliRunner coverage of the Phase 2 output contract, snapshot testing approach, non-TTY CI simulation, and Textual pilot tests if a TUI was chosen. Runs after Phase 3's stack configuration is locked.
---

# Testing & Quality Gates — Phase 4

The point of this phase is narrow: make sure every decision from Phases 2 and 3 has a
corresponding test that would catch a regression, before implementation starts rather than
after something breaks in an agent's pipeline.

## CliRunner coverage of the output contract

For each Phase 2 decision, name the specific test that proves it:

- **`--json` validity** — every command with a `--json` mode gets a test that invokes it and
  asserts `json.loads(result.stdout)` succeeds.
- **Exit codes** — one test per failure mode named in Phase 2's exit code scheme, asserting the
  specific code, not just "non-zero."
- **stdout/stderr separation** — use `CliRunner(mix_stderr=False)` (or the Typer/Click
  equivalent) to assert stdout carries only data and stderr carries only messages, at least for
  the commands most likely to be piped.
- **Non-interactive mode** — a test that supplies all required flags with `NO_COLOR=1` and
  confirms no prompt fires and no color escapes appear in output.
- **`NO_COLOR` respected** — confirm human-mode output has no ANSI codes when `NO_COLOR=1` is
  set, even when not otherwise in `--json`/`--plain` mode.

## Snapshot testing

- **Human output** — decide whether `syrupy` snapshots are worth it for this project's tables/
  panels, or whether the CliRunner assertions above are sufficient given the project's size.
  Don't add snapshot testing as a default if the CLI is small enough that it adds more
  maintenance than value — but say that's the reasoning if you skip it.
- **JSON envelope** — if snapshotting human output, snapshot the JSON envelope shape alongside
  it so an accidental field rename or dropped key surfaces in review.
- **TUI (only if Phase 1 chose one)** — `pytest-textual-snapshot`'s `snap_compare` for the
  Textual app; note that the first run has no baseline and needs `--snapshot-update`, and that
  this works in CI across OSes.

## Non-TTY / CI simulation

- Confirm CI runs the test suite with `NO_COLOR=1` set to assert agent-mode behavior actually
  holds, not just that it's implemented.
- Add (or confirm the project already has) a CI job that pipes a real invocation through `jq`
  (`mytool ... --json | jq .`) — this catches stdout/stderr leakage that unit tests sometimes
  miss, since it exercises the actual process boundary.
- If Phase 1 chose an MCP surface: confirm a test using the FastMCP in-memory client that asserts
  the tool list and structured return shape, separate from the CLI's own tests — the same core
  function gets exercised through two different harnesses.

## Housekeeping this phase should also lock

- Shell completion (`--install-completion`) — confirmed as shipping, or explicitly deferred.
- `--version` — confirmed as an eager option callback.
- A changelog — confirmed as starting now, not "later."

## Output format

```markdown
## Testing & Quality Gates

### CliRunner coverage
| Phase 2 decision | Test |
|---|---|
| --json validity | [per-command or "all commands with --json"] |
| Exit codes | [per failure mode] |
| stdout/stderr separation | [...] |
| Non-interactive mode | [...] |
| NO_COLOR respected | [...] |

**Snapshot testing:** syrupy for human output + JSON envelope | skipped — [reason]
**TUI snapshot testing (if applicable):** pytest-textual-snapshot, baseline TBD on first run | N/A
**CI non-TTY job:** [confirm NO_COLOR=1 test run + pipe-to-jq job]
**MCP in-memory client test (if applicable):** [confirm] | N/A — no MCP surface
**Shell completion / --version / changelog:** [confirmed shipping, or deferred with reason]

### Repository quality gates (mandatory)
- [ ] Ruff formatting check (`ruff format --check`)
- [ ] Ruff linting clean (`ruff check`)
- [ ] Type checking (`uv run ty check src`)
- [ ] pytest coverage >= 80%
- [ ] Hypothesis tests for parsers and validators (if applicable to this project's domain)

**Open questions for the human:** [anything this phase couldn't fully test-plan because an
earlier phase carried its own open question forward — e.g. can't finalize the idempotency test
until Phase 3's open question about where a write happens is resolved] | none
**Critique pass result:** PASS | REVISE — [specific objection, or omit if PASS]
```

## Critique pass

Before returning this, check: (1) every Phase 2 decision has a named corresponding test, not a
generic "we'll write tests" statement; (2) the snapshot-testing decision has an actual reason,
whether that reason is "yes" or "not worth it yet"; (3) the pipe-to-jq CI job is concrete enough
to actually add to a CI config, not left vague; (4) if no MCP surface was chosen in Phase 1, this
phase doesn't invent MCP testing anyway; (5) check every prior phase's Open Questions field
before finalizing — if one of them blocks a specific test from being fully specified, say so here
rather than writing a test plan that quietly assumes the question's already answered. If any of
these fail, mark `REVISE` and fix it yourself before it reaches the human.
