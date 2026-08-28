# TASK: Drop-direction uniqueness + ADDRFEAT matcher + shapefile fetch/CLI

GitHub issue: Abstract-Data/RyanData-Address-Utils#22
PR: Abstract-Data/RyanData-Address-Utils#23
Branch: `feat/drop-direction-uniqueness`

Derek Ryan should only need a voter-file path and `--sources txgio`, `tiger`, or both. The package fetches TxGIO address points, TIGER ADDRFEAT, and TLC precinct polygons into a cache, attaches precincts, and writes uniqueness outcomes.

## Files in scope

- Keep: `src/ryandata_address_utils/match/{__init__,keys,uniqueness,ranges}.py`
- Create: `src/ryandata_address_utils/match/texas.py`
- Create: `src/ryandata_address_utils/match/fetch/{__init__,http,txgio,tiger,precincts}.py`
- Create: `src/ryandata_address_utils/match/{voters,geo,run,cli}.py`
- Create: `tests/test_match_{fetch,voters,run,cli}.py`
- Modify: `src/ryandata_address_utils/setup_cli.py`, `pyproject.toml`, `README.md`, `docs/ARCHITECTURE.md`, `AGENTS.md`

## Behavior to ship

- CLI: `ryandata-address-utils-setup uniqueness --voterfile PATH --sources txgio,tiger`
- Sources: `txgio`, `tiger`, or both. Unknown tokens fail loud.
- Counties default to those present on the voter file
- Fetch-if-missing into `~/.cache/ryandata-address-utils` (overridable)
- TxGIO: newest Address Points vintage from api.tnris.org; skip statewide ZIP; WAF UA starts with `Mozilla/5.0`
- TIGER ADDRFEAT only (not CD/SLDL/VTD); `tl_{year}_{fips}_addrfeat.zip`; try 2025 then 2024 on 404
- TLC precincts: newest Precincts##P/G via CKAN `package_show?id=precincts`
- PIP precinct onto TxGIO points and ADDRFEAT centroids (`[geo]` extra)
- Outcomes columns `txgio_outcome` / `tiger_outcome`
- No hard pandas/geopandas/httpx/polars dependency
- Do not submodule voterfile-audit-pipeline
- Do not fold into AddressService

## Checks

- `uv run pytest tests/test_match_*.py -q`
- `uv run pytest tests/test_match_keys.py tests/test_match_ranges.py tests/test_match_uniqueness.py tests/test_match_geo.py tests/test_match_fetch.py tests/test_match_run.py tests/test_match_cli.py tests/test_match_voters.py --cov=src/ryandata_address_utils/match --cov-report=term-missing --cov-fail-under=80`
- `uv run pytest --cov=src --cov-fail-under=80`
- `uv run ruff check src/ryandata_address_utils/match tests/test_match_*.py src/ryandata_address_utils/setup_cli.py`
- `uv run ruff format --check` on those files
- `uv run ty check src/ryandata_address_utils/match src/ryandata_address_utils/setup_cli.py`

## Evidence before done

- Newest TxGIO vintage wins; statewide ZIP excluded
- ADDRFEAT URL uses 5-digit FIPS; year fallback 2025→2024
- Precinct rank: 26P over 24G
- CLI uniqueness with mocked fetchers writes outcomes for `--sources txgio,tiger`
- PR #23 updated
