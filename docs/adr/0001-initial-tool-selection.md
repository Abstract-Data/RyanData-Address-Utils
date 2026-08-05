# ADR 0001: Initial Tool Selection

**Date:** 2026-08-04
**Status:** accepted

## Context

`ryandata-address-utils` is a US address parsing library distributed as a standalone Python
package. It needed: a validation/serialization layer for a 26+ field `Address` model, a
pluggable parser backend (multiple US address parsing strategies exist with different
tradeoffs), pandas interop for bulk processing, and a CLI for interactive use.

## Decision

- **Pydantic 2.x** for the `Address` model — field validation, aliasing (`AliasChoices`), and
  serialization in one layer, with `Protocol`-based interfaces used elsewhere for extensibility
  without inheriting from Pydantic base classes.
- **`usaddress`** as the default parser backend, behind a `ParserFactory` so a second backend
  (e.g., libpostal) can be registered without touching call sites.
- **`typer` + `trogon`** for the CLI, giving both a scriptable interface and an interactive TUI.
- **uv** as the package manager (lockfile-based, fast installs) over pip/poetry.
- **ruff** for lint + format, **ty** (Astral's Rust-based type checker) for type checking,
  **pytest** + **pytest-cov** for testing. See ADR 0002 for why ty over mypy.
- **AI agent governance**: a local, self-contained enforcement layer (`.claude/hooks/gate.py` +
  companion hooks) rather than a cloud-tooling-coupled one — this package is distributed to
  collaborators who won't have access to any particular vendor's private tooling account, so the
  governance layer had to work standalone with zero external service dependency.

## Consequences

- Swapping the parser backend is a registration call, not a rewrite, at the cost of an extra
  `Protocol` indirection layer.
- ty catches type errors early but requires discipline on every new public function.
- The enforcement-hook layer only checks what's actually installed locally (ruff/ty/pytest via
  uv) — it does not depend on any account-gated service being reachable, so it works identically
  for every contributor who clones the repo.
