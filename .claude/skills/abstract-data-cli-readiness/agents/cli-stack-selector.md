---
name: cli-stack-selector
description: Phase 3 of abstract-data-cli-readiness. Configures the canonical library stack for this specific project — Typer structure, Rich UI (including progress bars and NO_COLOR handling), Questionary gating, pydantic-settings config layering, keyring secrets, httpx/Jinja2 if applicable. Runs after Phase 2's output contract is locked.
---

# Stack Configuration & UX — Phase 3

Phase 1 decided the surface, Phase 2 decided the contract. This phase configures the canonical
libraries to deliver both. Nothing here is a "which library" decision — that's fixed by the
governing playbook — it's "how is this library configured for this project."

## Typer structure

- **Command groups.** Based on the intake's candidate commands, sketch the top-level command
  tree using `noun verb` ordering (`mytool users list`, not `mytool list-users`). Name the
  `app.add_typer()` groups explicitly.
- **`ctx.obj` / `AppState` shape.** List exactly what goes into shared state — at minimum
  `json_output`, `verbose`, and (if Phase 2 needs it) the config object; add an `httpx.Client`
  only if this project makes network calls.
- **`pretty_exceptions_show_locals=False`.** Confirm this is set — it's a security default, not
  a style preference.

## Rich UI

- **Console setup.** Confirm the module-level `console.py` pattern (stdout console +
  `Console(stderr=True)`) rather than ad hoc `Console()` calls scattered through the codebase.
- **Progress bars and spinners.** For every long-running operation the intake/spec surfaced,
  decide: spinner (`console.status(...)`, indeterminate) or progress bar (`Progress`, has a
  known total)? State which, per operation. Confirm the TTY + `--json` gate:
  `console.is_terminal and not state.json_output` — no animation reaches a pipe, CI log, or
  agent caller.
- **Color / `NO_COLOR` handling.** Confirm the CLI honors `NO_COLOR` (color stripped, other
  styles like bold remain) and doesn't need custom handling beyond what Rich already does —
  this is default Rich behavior, the decision here is just confirming nothing overrides it.
- **Error panels.** Confirm all errors route through one styled function, never a bare `print()`.

## Questionary (only if Phase 1/2 left any interactive prompts)

If Phase 2's "no hidden prompts" decision means there are no prompts at all when flags are
supplied, this section can be short — just confirm the TTY-gate + bypass pattern from the
playbook for whatever prompts remain. For each prompt:

- What's the flag/env/config fallback that lets it be skipped entirely?
- What's the `default=` value so it pre-fills from config/env when a human does hit it
  interactively?
- Does it need `questionary.password()` (secrets) or `questionary.confirm(default=False)`
  (destructive actions)?

## Config: pydantic-settings

- **Settings fields.** List the actual config fields this project needs (not a generic example)
  — API URLs, timeouts, feature flags, whatever the intake surfaced.
- **Precedence.** Confirm flags > env (`MYTOOL_` prefix, or the project's actual name) >
  project-local TOML > user TOML (XDG) > defaults, per the playbook. Note the actual env prefix
  and TOML filename for this project.
- **Where secrets live.** This overlaps with the keyring section below — settings should read a
  token from env/keyring, never accept it as a plain settings field with a default.

## Secrets: keyring (only if this project has secrets)

If there's nothing to authenticate against, say so and skip the rest of this section — don't
force a keyring section onto a project with no secrets.

- **Service name.** What string does `keyring.set_password(service, ...)` use — usually the
  project name.
- **Fallback ladder.** Confirm env-var-first → keyring → insecure-file-with-warning, per the
  playbook. Name the actual env var (e.g. `MYTOOL_TOKEN`).

## httpx (only if this project makes network calls)

- One long-lived client, built in the callback — confirm, don't re-derive.
- Explicit timeouts — state the actual values for this project's use case (a fast internal API
  and a slow scraping target don't get the same timeout).
- Retry policy — which operations are safe to retry (idempotent, e.g. GET) and which aren't.

## Jinja2 (only if this project scaffolds files)

- Template location — `PackageLoader` (ships in-package) vs `FileSystemLoader`
  (project-local templates).
- Autoescape — off for code/config generation, with the one-line rationale comment the playbook
  specifies, on for any HTML/XML output.

## Output format

```markdown
## Stack Configuration & UX

**Typer command tree:** [sketch]
**AppState / ctx.obj fields:** [list]
**Rich progress strategy:** [per long-running operation: spinner | progress bar]
**Color handling:** confirmed default Rich NO_COLOR behavior, no overrides needed | [exception, if any]
**Questionary prompts remaining:** [list with fallback + default for each] | none — all flags required
**pydantic-settings fields + precedence:** [list + confirm precedence order]
**Secrets:** [service name + fallback ladder] | N/A — no secrets
**httpx:** [timeouts + retry policy] | N/A — no network calls
**Jinja2:** [template location + autoescape setting] | N/A — no scaffolding
**Open questions for the human:** [anything the intake left ambiguous that this phase declined
to guess at — e.g. whether an existing write/integration the recon spotted actually belongs
inside this CLI or lives elsewhere] | none
**Critique pass result:** PASS | REVISE — [specific objection, or omit if PASS]
```

Don't resolve an open question by guessing just to keep the field empty. If the intake genuinely
doesn't say where something belongs, name it here and let every other decision in this phase
stand on what *is* known — that's a `PASS` with a question attached, not a reason to leave the
whole phase unfinished.

## Critique pass

Before returning this, check: (1) every N/A is actually justified by the intake/spec, not a
shortcut; (2) progress-bar decisions were made per operation, not as one blanket answer; (3) the
config field list and env prefix are this project's actual names, not the playbook's generic
`mytool`/`MYTOOL_` placeholders left unedited; (4) if Phase 1 chose an MCP surface, does this
phase's `AppState` shape actually support being called from both `cli.py` and `mcp_server.py`
without duplication; (5) any decision that leans on something the recon flagged but couldn't
confirm (an existing client, an existing write, an existing secret) is either grounded in
something the intake actually established, or named explicitly in Open Questions instead of
assumed either way. If any of these fail, mark `REVISE` and fix it yourself before it reaches the
human.
