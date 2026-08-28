# RyanData Address Utils

[![Tests](https://github.com/Abstract-Data/RyanData-Address-Utils/actions/workflows/tests.yml/badge.svg)](https://github.com/Abstract-Data/RyanData-Address-Utils/actions/workflows/tests.yml)
[![Ruff](https://github.com/Abstract-Data/RyanData-Address-Utils/actions/workflows/lint.yml/badge.svg)](https://github.com/Abstract-Data/RyanData-Address-Utils/actions/workflows/lint.yml)
[![Type Check (ty)](https://github.com/Abstract-Data/RyanData-Address-Utils/actions/workflows/typecheck.yml/badge.svg)](https://github.com/Abstract-Data/RyanData-Address-Utils/actions/workflows/typecheck.yml)
[![codecov](https://codecov.io/gh/Abstract-Data/RyanData-Address-Utils/graph/badge.svg?token=75LQK4KJTZ)](https://codecov.io/gh/Abstract-Data/RyanData-Address-Utils)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/packaging-uv-9055ff.svg)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Parse and validate US addresses with Pydantic models, ZIP/state validation, pandas integration, and release-please powered CI.

## Highlights

- Structured parsing of US addresses into 26+ components with Pydantic models
- ZIP and state validation backed by authoritative datasets
- Pandas-friendly parsing for batch workloads
- Custom errors (`RyanDataAddressError`, `RyanDataValidationError`) with package context
- Builder API for programmatic address construction
- ProcessLog system for transformation auditing (via `abstract-validation-base`)
- Semantic-release CI for automated tagging and releases

## Install

### uv (recommended)

```bash
uv add git+https://github.com/Abstract-Data/RyanData-Address-Utils.git
# with pandas extras
uv add "ryandata-address-utils[pandas] @ git+https://github.com/Abstract-Data/RyanData-Address-Utils.git"
```

### pip

```bash
pip install git+https://github.com/Abstract-Data/RyanData-Address-Utils.git
pip install "ryandata-address-utils[pandas] @ git+https://github.com/Abstract-Data/RyanData-Address-Utils.git"
```

### Setup cheat sheet (pick what you need)

- Local parsing only: install base package (no extras) and call `parse(...)` or `AddressService`.
- Pandas workflows: add the `[pandas]` extra so `parse_dataframe` works without optional import errors.
- Libpostal setup (local, no Docker): run `uv run ryandata-address-utils-setup` and follow the prompts. The default data directory is system-wide (e.g., `/usr/local/share/libpostal` or `C:\\libpostal`); override it if you prefer and set `LIBPOSTAL_DATA_DIR` accordingly.
- The setup command detects your OS, attempts installation via Homebrew/apt/dnf/yum where available, and downloads the official libpostal data archives into the chosen directory.

### International parsing (libpostal)

- `parse_auto` (service) tries US first, then libpostal if US validation fails.
- Strict rules: international results must include a road plus at least one location element (city/state/postal/country) or parsing fails.
- Returned structure includes `InternationalAddress` fields (`HouseNumber`, `Road`, `City`, `State`, `PostalCode`, `Country`, `CountryCode`) and raw libpostal `Components`.
- Requires libpostal installed; use the setup helper (`uv run ryandata-address-utils-setup`) to install locally and download data.
- Heuristics: if the input clearly names a non-US country or contains non-ASCII, it skips US parsing and goes straight to libpostal; otherwise, US is attempted first and any US validation failure triggers libpostal fallback.

## Quick start

```python
from ryandata_address_utils import AddressService, parse

result = parse("123 Main St, Austin TX 78749")
if result.is_valid:
    print(result.address.ZipCode)   # "78749"
    print(result.to_dict())         # full address dict
else:
    print(result.validation.errors) # custom errors with context

service = AddressService()
service.parse("456 Oak Ave, Dallas TX 75201")
```

## Pandas integration

```python
import pandas as pd
from ryandata_address_utils import AddressService

df = pd.DataFrame({"address": ["123 Main St, Austin TX 78749", "456 Oak Ave, Dallas TX 75201"]})
service = AddressService()

parsed = service.parse_dataframe(df, "address", prefix="addr_")
print(parsed[["addr_AddressNumber", "addr_StreetName", "addr_ZipCode"]])
```

## Drop-direction uniqueness

Match rows after dropping street direction, keyed on number + name + type + county + precinct. Pass `include_unit=True` to add unit to that key so unit-bearing rows do not collapse. Keys with two or more distinct directionals (blank counts as a state; `EAST` and `E` collapse) are refused.

Derek Ryan's one-liner: a Texas SOS voter extract and which universes to run. The CLI fetches TxGIO address points, TIGER ADDRFEAT, and TLC precinct polygons into `~/.cache/ryandata-address-utils` when they are missing.

```bash
uv sync --extra pandas
# shapefile readers / point-in-polygon:
uv add geopandas
uv run ryandata-address-utils-setup uniqueness \
  --voterfile ~/path/to/texas.csv \
  --sources txgio,tiger \
  --out uniqueness_out
```

`--sources` is `txgio`, `tiger`, or both. Counties default to every `COUNTY` on the voter file. Writes `outcomes.csv` and `summary.json`.

Library use when you already have `pct`:

```python
from ryandata_address_utils.match import (
    addrfeat_range_field_names,
    match_addrfeat_ranges,
    match_drop_direction,
)

voters["outcome"] = match_drop_direction(voters, points)
voters["outcome_unit"] = match_drop_direction(voters, points, include_unit=True)

lfrom, lto, rfrom, rto = addrfeat_range_field_names(addrfeat.columns)
ranges = addrfeat.rename(columns={lfrom: "lfrom", lto: "lto", rfrom: "rfrom", rto: "rto"})
voters["tiger_outcome"] = match_addrfeat_ranges(voters, ranges)
```

`match_addrfeat_ranges` expects canonical `lfrom`/`lto`/`rfrom`/`rto` columns. Raw TIGER 2024 `LFROMADD` / 2025 `LFROMHN` names must be resolved first. Import from `ryandata_address_utils.match`, not the top-level package.

## Programmatic build

```python
from ryandata_address_utils import AddressBuilder

address = (
    AddressBuilder()
    .with_street_number("123")
    .with_street_name("Main")
    .with_street_type("St")
    .with_city("Austin")
    .with_state("TX")
    .with_zip("78749")
    .build()
)
```

## Transformation tracking

Track what normalizations and cleanings were applied during parsing:

```python
from ryandata_address_utils import AddressService

service = AddressService()
result = service.parse("123 main st, austin texas 78749")

# Aggregate logs from parsing and model transformations
for entry in result.aggregate_logs():
    print(f"{entry['field']}: {entry['message']}")
# Example output:
# StateName: Normalized state name from full name to abbreviation
# ZipCode: ZIP code parsed and validated
```

## Workflow at a glance

```mermaid
flowchart LR
    parseStep[Parse] --> validateStep[Validate ZIP/State]
    validateStep --> testsStep[Tests & Lint]
    testsStep --> releaseStep[release-please PR merged]
    releaseStep --> githubRelease[Tag + GitHub Release]
```

## APIs you get

- `AddressService`: parse single, batch, DataFrame; look up ZIP/state; validate
- `parse(...)`: convenience wrapper returning `ParseResult`
- ZIP utilities: `get_city_state_from_zip`, `get_zip_info`, `is_valid_zip`, `is_valid_state`, `normalize_state`
- Builder: `AddressBuilder` for programmatic address construction
- Audit trail: `ProcessLog`, `ProcessEntry` for tracking transformations
- Validation base: `ValidationBase`, `RyanDataValidationBase` for model mixins
- Drop-direction match: `ryandata_address_utils.match` plus `uniqueness --voterfile --sources txgio,tiger` (fetches TxGIO, TIGER ADDRFEAT, TLC precincts)

## Documentation

- **[Architecture Overview](docs/ARCHITECTURE.md)** - Package structure, data flow diagrams, design patterns, and SOLID/DRY principles applied
- **[Diagrams](docs/diagrams.md)** - Visual references for the codebase
- **[Changelog](CHANGELOG.md)** - Version history and release notes
- **[AI Agent Guide](AGENTS.md)** - Guidance for AI coding assistants

## Development (uv)

```bash
git clone https://github.com/Abstract-Data/RyanData-Address-Utils.git
cd RyanData-Address-Utils
uv sync
uv run pytest
uv run ruff check src/
uv run ty check src/
uv run ruff format src/
```

## Agent Workflow (Cursor)

This project uses a structured parallel agent workflow for AI-assisted development. See [`.cursor/agents.md`](.cursor/agents.md) for:

- **STEP/AGENT naming convention** for organizing parallel tasks
- **Specialized agents**: CodeAgent, TestAgent, DocsAgent, RefactorAgent, ConfigAgent
- **Execution rules** for coordinating multi-agent work
- **Task templates** for features, bug fixes, and refactoring

Example todo format:
```
STEP1 - CodeAgent: Implement core data models
STEP1 - TestAgent: Create test scaffolding
STEP2 - CodeAgent: Wire up service layer (runs after STEP1)
```

## Contributing and support

- Issues: <https://github.com/Abstract-Data/RyanData-Address-Utils/issues>
- Releases/notes: <https://github.com/Abstract-Data/RyanData-Address-Utils/releases>
- Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- License: MIT
