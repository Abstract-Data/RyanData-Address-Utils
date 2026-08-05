# RUNBOOK.md — RyanData-Address-Utils
<!-- Version: 1.0.0 | Maintainer: John Eakin -->

## Setup

```bash
git clone <repo>
cd RyanData-Address-Utils
uv sync
uv run pytest          # verify install
```

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
