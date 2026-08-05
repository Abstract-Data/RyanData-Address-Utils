# RUNBOOK.md — RyanData-Address-Utils
<!-- Version: 1.0.0 | Maintainer: John Eakin -->

## Setup

```bash
git clone <repo>
cd RyanData-Address-Utils
uv sync
uv run pre-commit install   # wire up local git hooks — see Pre-commit Hooks below
uv run pytest                # verify install
```

## Pre-commit Hooks

`.pre-commit-config.yaml` defines the hooks, but **`pre-commit install` must be run once per
clone** — the config file alone doesn't wire anything into git. `git commit` then runs, in order:

- `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-added-large-files`,
  `check-merge-conflict`, `debug-statements` (standard pre-commit-hooks)
- `ruff` (lint, `--fix`) and `ruff-format`
- `pytest` — full suite, with `--cov` (writes `coverage.xml`)
- `diff-coverage` (`scripts/check-diff-coverage.sh`) — fails the commit if the lines you
  actually added/changed fall below 80% coverage, using `diff-cover` against the merge-base
  with the trunk branch. This is a **local, blocking** version of what `codecov.yml`'s `patch`
  check does on GitHub — it catches uncovered new code before it ever leaves your machine,
  instead of just flagging it after the fact in a PR.

To run everything without committing: `uv run pre-commit run --all-files`.

## Common Operations

### Parse a batch of addresses

```python
from ryandata_address_utils import AddressService
service = AddressService()
result = service.parse("123 Main St, Plano TX 75023")
```

### Parse a DataFrame column

```python
df = service.parse_dataframe(df, address_col="RES_STREET", prefix="addr_")
```

### Run PISD shapefile extraction

```bash
cd src/pisd_shape
uv run python -m pisd_shape.main
```

## Linting & Formatting

```bash
uv run ruff check src tests    # lint
uv run ruff format src tests   # format
uv run ty check src             # type check
```

## Dependency Updates

```bash
uv lock --upgrade              # update lock file
uv sync                        # reinstall
uv run pytest                  # verify nothing broke
```

## Releasing

Releases are fully automated via [release-please](https://github.com/googleapis/release-please) —
`ryandata_address_utils` and `pisd_shape` are versioned **independently** (separate version
numbers, changelogs, and git tags), since they're unrelated components sharing one repo.

1. Merge Conventional Commits (`feat:`, `fix:`, `feat!:`/`BREAKING CHANGE:`, etc.) to `main`,
   scoped to `src/ryandata_address_utils/**` or `src/pisd_shape/**`.
2. release-please opens (or updates) a standing Release PR **per component** — title like
   `chore(main): release address-utils 0.8.0` or `chore(main): release pisd-shape 0.2.0` — with
   the version bump and changelog entry already computed. Nothing is released yet; review it like
   any other PR.
3. Merging that PR triggers the release: a `{component}-v{version}` git tag (e.g.
   `address-utils-v0.8.0`, `pisd-shape-v0.2.0`), a GitHub Release, and the changelog commit —
   `CHANGELOG.md` for address-utils, `src/pisd_shape/CHANGELOG.md` for pisd-shape.

No manual version bump, tagging, or GitHub Release creation — don't hand-edit `version` in
`pyproject.toml` or `.release-please-manifest.json`; let the Release PR do it.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `uv sync` |
| Parser returns `None` | Check address format; try `usaddress` backend |
| Shapefile import fails | Ensure `geopandas` extras installed: `uv sync --extra geo` |
