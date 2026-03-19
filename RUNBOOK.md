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
uv run mypy src                # type check
```

## Dependency Updates

```bash
uv lock --upgrade              # update lock file
uv sync                        # reinstall
uv run pytest                  # verify nothing broke
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `uv sync` |
| Parser returns `None` | Check address format; try `usaddress` backend |
| Shapefile import fails | Ensure `geopandas` extras installed: `uv sync --extra geo` |
