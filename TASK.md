# TASK: Drop-direction uniqueness + ADDRFEAT range matcher

GitHub issue: Abstract-Data/RyanData-Address-Utils#22
Branch: `feat/drop-direction-uniqueness` from `origin/main` (3d14fba)

Extract Derek Ryan's uniqueness rule and TIGER ADDRFEAT house-range matching into `ryandata_address_utils.match` so the public parser package can do what the private voterfile-audit-pipeline compare script proved.

## Files in scope

- Create: `src/ryandata_address_utils/match/__init__.py`
- Create: `src/ryandata_address_utils/match/keys.py`
- Create: `src/ryandata_address_utils/match/uniqueness.py`
- Create: `src/ryandata_address_utils/match/ranges.py`
- Create: `tests/test_match_keys.py`
- Create: `tests/test_match_uniqueness.py`
- Create: `tests/test_match_ranges.py`
- Create: `docs/plans/2026-08-28-drop-direction-uniqueness.md`
- Modify: `README.md`, `docs/ARCHITECTURE.md`, `AGENTS.md`

## Behavior to preserve / ship

- Directionless key: number + name + type + county + pct (unit optional)
- Problem-key refusal: 2+ distinct canonical directionals on that key, **blank is a state**, `EAST`/`E` collapse
- Callers supply `pct` — v1 does **not** attach precincts (no geopandas, no `[geo]` extra)
- ADDRFEAT: inclusive house containment, even/odd side parity, TIGER 2024 `LFROMADD` and 2025 `LFROMHN` (2024 names win if both present)
- Outcomes: `match` | `excluded_problem` | `unmatched`
- Pandas extra for DataFrame helpers; scalar helpers import without pandas
- Do **not** fold into `AddressService`
- Do **not** submodule voterfile-audit-pipeline
- Do **not** add pandas/geopandas/polars as a hard dependency

## Checks

- `uv run pytest tests/test_match_keys.py tests/test_match_uniqueness.py tests/test_match_ranges.py tests/test_pandas_utils.py -q`
- `uv run ruff check src/ryandata_address_utils/match tests/test_match_keys.py tests/test_match_uniqueness.py tests/test_match_ranges.py`
- `uv run ruff format --check src/ryandata_address_utils/match tests/test_match_keys.py tests/test_match_uniqueness.py tests/test_match_ranges.py`
- `uv run ty check src/ryandata_address_utils/match`

## Evidence before done

- E+W same key is a problem; EAST+E is not; blank vs E is a problem
- Even house does not match an odd-only ADDRFEAT side
- 2024 vs 2025 range field names resolve correctly
- Unique covering range → `match`; two dirs covering the same house → `excluded_problem`
- PR open against `Abstract-Data/RyanData-Address-Utils` `main`, closes #22
