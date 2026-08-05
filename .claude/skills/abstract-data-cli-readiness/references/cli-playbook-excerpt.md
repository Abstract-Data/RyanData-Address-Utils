# CLI Playbook Excerpt (bundled fallback)

**This is a fallback.** The canonical, maintained version of this content lives in Notion as
"Agent-Friendly Dual-Mode CLI Design — Typer + Rich + FastMCP"
(https://app.notion.com/p/3937d7f56298811a87edf4919605b3f8), Reference Documentation, currently
marked Draft. Prefer pulling it live via the Notion MCP every run. Use this file only when Notion
is unreachable, and say so explicitly in the phase output when you do — never present a
fallback-sourced recommendation as if it came from a live pull. If you edit this file, the Notion
page is still the source of truth; sync there too.

---

## Overview

Design one core logic layer with two thin adapters, not a CLI with logic tangled through it. All
real work lives in pure Python functions with no I/O/UI imports; a Typer CLI and a FastMCP server
both wrap the same core. The single highest-leverage agent-friendliness feature is a `--json`
structured-output mode combined with TTY detection that auto-plains output whenever stdout isn't
a terminal.

This playbook is the construction-time counterpart to **CLI Agent-Readiness Audit**, which scores
a finished CLI against a 15-point Agentic CLI Design Scorecard (Output & Parsing, Interactivity,
Reliability, Discoverability, Safety). Everything below is written to produce a CLI that scores
15/15 on that scorecard by construction, plus the library-level decisions the scorecard doesn't
cover.

## 1. Core architecture: one logic layer, two thin adapters

```
project/
├── core/          # pure logic — NO typer/rich/mcp imports
├── cli.py         # Typer: @app.command() wrappers around core (+ Rich UI)
└── mcp_server.py  # FastMCP: @mcp.tool wrappers around the SAME core
```

Core modules use logging only, never UI imports. Wire an `mcp serve` Typer subcommand that calls
`mcp.run()`:

```python
# mcp_server.py
from fastmcp import FastMCP
from .core import summarize
mcp = FastMCP("my-tool")

@mcp.tool
def summarize_file(path: str) -> dict:
    """Summarize a data file."""
    return summarize(path)

# cli.py
import typer
from .mcp_server import mcp
mcp_app = typer.Typer()
app.add_typer(mcp_app, name="mcp")

@mcp_app.command("serve")
def serve(transport: str = "stdio", host: str = "127.0.0.1", port: int = 8000):
    if transport == "stdio":
        mcp.run(transport="stdio")     # default; what Claude Desktop/Code/Cursor expect locally
    else:
        mcp.run(transport="http", host=host, port=port)
```

Claude Desktop config for a stdio server:
```json
{"mcpServers": {"my-tool": {"command": "my-tool", "args": ["mcp", "serve"]}}}
```

**Version note (2026):** the actively-developed standalone line is FastMCP 2.x → 3.x
(`from fastmcp import FastMCP`, PrefectHQ), separate from the official MCP Python SDK's own
FastMCP (`from mcp.server.fastmcp import FastMCP`). Pin deliberately and re-verify the
`mcp.run(transport=...)` signature against the installed version before shipping.

## 2. The agent/human output contract

The heuristic that drives everything: **is stdout/stderr a TTY?** Check `sys.stdout.isatty()`.
When it's not a TTY, emit machine-parseable output, disable color/animation, never prompt.

- **Default human mode** — Rich tables/panels/color, gated on `console.is_terminal`.
- **`--json`** — a single well-formed JSON object/array to stdout. Consistently the single most
  important feature for agent compatibility across surveyed agent-facing CLIs.
- **`--plain`** — one record per line, grep/awk-friendly, for scripts.
- **NDJSON streaming** for long/streamed operations — one JSON object per line.

**Field selection**, copying `gh`: `--json <fields>` + `-q/--jq <expr>` lets a caller request
exactly the fields it needs instead of a wall of text.

**stdout vs stderr discipline (non-negotiable):** machine-readable output → stdout; logs, errors,
progress → stderr. Rich supports this with `Console(stderr=True)`.

**Exit codes:** 0 = success, non-zero = failure, distinct codes per failure mode. BSD
`sysexits.h`: `EX_USAGE=64`, `EX_DATAERR=65`, `EX_NOINPUT=66`, `EX_UNAVAILABLE=69`,
`EX_SOFTWARE=70`, `EX_TEMPFAIL=75` (retryable), `EX_CONFIG=78`. The one hard rule: codes must be
*documented*. Codes >128 are reserved for signal termination (130 = SIGINT).

**Structured errors:**
```json
{"ok": false, "error": {"code": "CONFIG_MISSING", "message": "No API token configured.",
 "fix": "mytool auth login  # or set MYTOOL_TOKEN", "retryable": false}}
```

**Envelope:** `{"ok": bool, "data": ..., "error": ..., "schema_version": ...}` — treat this shape
as a contract you don't break casually.

**Interactivity gates:** only prompt if stdin is an interactive terminal. Never *require* a
prompt. Provide a global `--no-input`/`--yes`.

## 3. Typer patterns

```python
import typer, httpx, logging
from dataclasses import dataclass

app = typer.Typer(no_args_is_help=True)

@dataclass
class AppState:
    json_output: bool
    verbose: int
    client: httpx.Client

@app.callback()
def main(ctx: typer.Context,
         json_: bool = typer.Option(False, "--json", help="Machine-readable output"),
         verbose: int = typer.Option(0, "--verbose", "-v", count=True),
         config: str = typer.Option(None, "--config", envvar="MYTOOL_CONFIG")):
    logging.basicConfig(level=logging.WARNING - 10*min(verbose, 2))
    ctx.obj = AppState(json_output=json_, verbose=verbose,
                       client=httpx.Client(timeout=30.0))

@app.command()
def fetch(ctx: typer.Context, name: str):
    state: AppState = ctx.obj
    ...
```

Command groups: `app.add_typer(sub_app, name="...")`, group name set explicitly. `noun verb`
ordering. Disable pretty exceptions for agent/CI legibility:
`typer.Typer(pretty_exceptions_enable=False)`, or at minimum `pretty_exceptions_show_locals=False`.

Testing:
```python
from typer.testing import CliRunner
runner = CliRunner()

def test_json_mode():
    result = runner.invoke(app, ["fetch", "widget", "--json"])
    assert result.exit_code == 0
    import json; json.loads(result.stdout)
```
`CliRunner(mix_stderr=False)` asserts stdout/stderr separately.

## 4. Rich patterns

One Console, module level — a stdout console and a `Console(stderr=True)` for messages. Respect
`NO_COLOR` (color stripped, other styles remain), `FORCE_COLOR`, `TERM=dumb`, and
`TTY_COMPATIBLE`/`TTY_INTERACTIVE` for CI. Gate all decorative output behind
`console.is_terminal and not state.json_output`. Show progress for long operations, TTY only.
`rich.logging.RichHandler` for humans; plain `logging.StreamHandler` on stderr in non-TTY/agent
mode. Serialize a Pydantic model two ways: `model.model_dump()` into a `Table` for humans,
`model.model_dump_json()` for `--json`. Pin current Rich (14.x) — older versions had piped-output
bugs on Windows.

## 5. Questionary — interactivity gates

```python
import sys, questionary, typer

def get_value(cli_value, env_value, config_value, *, prompt, no_input):
    for candidate in (cli_value, env_value, config_value):
        if candidate is not None:
            return candidate
    if no_input or not sys.stdin.isatty():
        raise typer.BadParameter(
            "value required; pass --value, set MYTOOL_VALUE, or add it to config")
    return questionary.text(prompt).ask()
```
`.ask()` returns `None` on Ctrl-C — handle it, prefer over `.unsafe_ask()`. `default=` on every
prompt. `questionary.confirm(..., default=False)` for destructive confirmations, plus
`--yes`/`--force`. `questionary.password()` for secrets.

## 6. Pydantic v2 / pydantic-settings

```python
from pydantic_settings import (BaseSettings, SettingsConfigDict,
                               TomlConfigSettingsSource)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MYTOOL_", extra="ignore")
    api_url: str = "https://api.example.com"
    timeout: float = 30.0
    token: str | None = None

    @classmethod
    def settings_customise_sources(cls, settings_cls, init_settings, env_settings,
                                   dotenv_settings, file_secret_settings):
        return (init_settings, env_settings,
                TomlConfigSettingsSource(settings_cls, toml_file="mytool.toml"),
                file_secret_settings)
```
Precedence: flags > env > project config > user config > defaults. Validation errors: dump
`ValidationError.errors()` into the error envelope for `--json`, friendly summary for humans.
Validate CLI args into a Pydantic model early; pass the validated model into `core/`.

## 7. httpx (if networked)

One long-lived `Client` built in the callback. Explicit timeouts always
(`httpx.Timeout(connect=..., read=..., write=..., pool=...)`). Transport retries for connection
failures only; `tenacity` with jitter for status backoff, idempotent methods only. Sync by
default — async only for genuine concurrent fan-out. Translate `httpx.TimeoutException` /
`ConnectError` / `HTTPStatusError` into the error envelope with the matching exit code.

## 8. Jinja2 (if scaffolding)

Autoescape off for code/config generation (documented rationale comment), on for HTML/XML —
`select_autoescape()`. `PackageLoader` for in-package templates. `SandboxedEnvironment` only if
template *content* could come from users/agents. `trim_blocks`/`lstrip_blocks` for clean output.

## 9. Config files (TOML preferred)

`tomllib` to read (stdlib 3.11+), `tomli-w` to write (binary mode). YAML only if users expect it,
always `yaml.safe_load()`. Precedence: `--config` flag → env → project-local (walk up like git)
→ user (`typer.get_app_dir("mytool")`, XDG) → system.

## 10. keyring (secrets)

Fallback ladder: env var first (CI/agents) → keyring (interactive desktop) → encrypted/plain
file as explicit opt-in (XDG dir, `600` perms, warn loudly).

```python
import os, keyring
from keyring.errors import NoKeyringError

def get_token():
    if tok := os.getenv("MYTOOL_TOKEN"):
        return tok
    try:
        return keyring.get_password("mytool", "default")
    except NoKeyringError:
        return _read_token_file()
```
Never accept secrets via `--password`-style flags — they leak into `ps`/shell history.

## 11. FastMCP / MCP dual-surface

See Section 1. `stdio` is the default and what Claude Desktop/Code/Cursor expect locally. `http`
for network deployments (needs `mcp-remote` proxy for Claude Desktop). Prefer the shared-core
approach over auto-conversion tools like `click-mcp` for cleaner tool ergonomics.

## 12. packaging (versioning)

`packaging.version.Version`/`parse` (PEP 440-aware). `packaging.specifiers.SpecifierSet` for
requirement checks. Update checks: opt-in/cached, never a blocking phone-home on normal runs.

## 13. Textual (TUI) — when warranted

Don't conflate CLI and TUI — CLI is non-interactive-capable, TUI is inherently interactive.
Rich-based CLI as default/scriptable/agent-facing; Textual only for genuinely exploratory
human workflows (dashboards, multi-pane browsing). Pattern: `mytool list --json` plus optional
`mytool ui`. **The TUI must never be the only way to do something.** Blocking I/O in `@work`
workers, never event handlers. Testing: `async with app.run_test() as pilot:`,
`await pilot.pause()` to avoid race-condition flakes. Snapshot testing via
`pytest-textual-snapshot`.

## 14. General CLI UX

Anchor on clig.dev, 12-Factor CLI Apps, POSIX/GNU conventions. Prefer flags to positional args,
always long forms. Help: concise with no args, full on `-h/--help`, lead with examples. Errors:
actionable, human-rewritten. Robustness: respond fast or print something, show progress
TTY-only, keep Ctrl-C working. Future-proofing: flags/output/env/config are interfaces — additive
changes, SemVer, changelog.

## 15. Testing and CI

CliRunner for the contract — `exit_code`, `stdout`, `stderr` (separately). Snapshot testing:
`syrupy` (general) or `pytest-textual-snapshot` (TUI) for both the human table and the JSON
envelope. Non-TTY simulation: `NO_COLOR=1` in CI, plus a pipe-to-jq job
(`mytool ... --json | jq .`) to catch stdout/stderr leakage. MCP tools: unit-test core directly,
FastMCP in-memory client for the tool-list/structured-return check. Validate `--json` always
parses in CI.

## Staged rollout checklist

**Stage 1 — Foundational contract:** three-layer architecture; global callback with
`--json`/`--verbose`/`--config`/`--no-input`/`--yes`; output contract (envelope + `schema_version`
+ TTY-gated Rich + `NO_COLOR`); exit codes + actionable error envelope.

**Stage 2 — Config, secrets, robustness:** pydantic-settings with full precedence chain; keyring
fallback ladder; httpx hardening (timeouts, pooled client, idempotent-only retries).

**Stage 3 — MCP + advanced UX:** `mcp serve` subcommand; Jinja2 scaffolding if applicable;
optional Textual `ui` subcommand, never the sole path to a capability.

**Stage 4 — Quality gates:** CI covering JSON/human/non-TTY modes + pipe-to-jq; shell completion,
`--version`, changelog, `SKILL.md`/`AGENTS.md` documenting the contract.

## Caveats

Fast-moving area (2024–2026, largely vendor blogs and community skills, not formal standards).
FastMCP version churn is real — pin explicitly. clig.dev is opinionated, not law — TTY detection
+ explicit `--json`/`--plain` is the accepted reconciliation with agent-first needs. Library
specifics drift across versions — verify against exact pinned versions. TOML is the default
recommendation here but partly cultural; support YAML with `safe_load` only if users expect it.
