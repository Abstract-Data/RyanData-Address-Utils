# ADR 0002: Switch type checker from mypy to ty

**Date:** 2026-08-05
**Status:** accepted

## Context

The project's enforcement hooks (`ruff-and-ty-check.sh`, `verify-completion.sh`) already invoked
`ty check` on every edited Python file, while `pyproject.toml` still declared and configured
`mypy` as the project's type checker. Neither tool was actually the single source of truth, and
running `ty check` for real surfaced 44 diagnostics mypy had never caught, including a genuine
runtime bug (see below) — meaning the inconsistency wasn't cosmetic, it was hiding real gaps.

## Decision

Standardize on **ty** (Astral's Rust-based type checker) as the project's sole type checker.
`mypy` and its `[tool.mypy]` config are removed; `ty` is a normal `uv` dev dependency
(`pyproject.toml`'s `[dependency-groups.dev]`), not a global tool install, so `uv sync` gives
every contributor an identical, working type checker with no separate setup step.

Config lives under `[tool.ty.environment]` (`python-version = "3.12"`). ty's suppression
comment is `# ty: ignore[rule-name]`, placed on the exact flagged line — not mypy's
`# type: ignore[code]`, which ty does not recognize (an unrecognized-but-present ignore comment
is worse than none, since it looks like the diagnostic was handled when it wasn't).

## What the switch actually found

Doing this properly — fixing root causes rather than blanket-suppressing — surfaced:

- **A real `UnboundLocalError` bug** in `AddressService.parse_to_dict`: a local
  `from ryandata_address_utils.models import RyanDataAddressError` inside one `if` branch made
  Python treat the name as function-scoped everywhere in that method, shadowing the already-valid
  module-level import. A sibling branch that referenced the name without having executed the
  first branch would have crashed at runtime. Fixed by removing the redundant local import.
- **A dead, fully-shadowed file**: `src/ryandata_address_utils/models.py` (1026 lines) was
  unreachable — `ryandata_address_utils.models` always resolved to the `models/` package
  directory of the same name, left behind by an earlier refactor. Deleted.
- **Four Liskov substitution violations**: every validator's `validate(self, address: Address)`
  used a different parameter name than the external `abstract_validation_base.BaseValidator`'s
  `validate(self, item: T)` — harmless today since nothing calls `.validate(item=...)` by
  keyword, but a real substitutability gap. Renamed to match.
- **Two more of the same**, self-inflicted this time: `PluginFactory.create`'s subclasses use
  more descriptive parameter names (`source_type`, `parser_type`) than the base's generic `name`.
  Fixed by making the base parameter positional-only (`name: str | None = None, /`) — the
  subclass's more readable name is no longer part of the interface contract, so this is no longer
  a violation, and it required touching zero call sites since nobody was calling it by keyword.
- **A real pandas edge case**: `Series.apply()` returns a bare `Series`, not a `DataFrame`, when
  given an empty input (pandas can't infer columns from zero rows) — both public entry points
  that promised a `DataFrame` return type would have silently returned the wrong type on empty
  input. Fixed with an explicit empty-input guard; added regression tests for both.
- **A previously-untested feature area**: `pandas` wasn't installed anywhere in dev/CI, so
  `tests/test_pandas_utils.py` (23 tests) was entirely skipped and the pandas integration code
  had zero type-checking coverage. Added `pandas` as a dev dependency (kept optional for end
  users via `[project.optional-dependencies]`) — those 23 tests now run.

The remaining diagnostics (7 for `pandas`-guarded-optional paths pre-fix, `postal`/libpostal
imports, and GIS deps in the unrelated `src/pisd_shape/` script) are genuine environment
limitations — libpostal is a system C library with downloaded data files, not a pip package, and
`src/pisd_shape/`'s GIS stack is unrelated to this library and excluded from the built wheel —
suppressed with `# ty: ignore[...]` and an explanatory comment at each site, not blanket-ignored.

## Consequences

- `uv run mypy` no longer works — anyone with muscle memory for it needs `uv run ty check src`.
- ty's diagnostics are more thorough than mypy's were for this codebase; expect new diagnostics
  when touching code ty hasn't previously had a reason to analyze deeply (e.g. adding a new
  optional integration).
- Suppression comments are a signal, not a shortcut: each one here documents *why* the diagnostic
  can't be resolved at the source (an overly-strict third-party stub, or a dependency that can't
  reasonably be a dev dependency) — a future `# ty: ignore` without that reasoning should be
  treated as a code-review flag, not precedent.
