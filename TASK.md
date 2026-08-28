# TASK: Phase B — suffix-pair uniqueness (PR #23)

GitHub issue: Abstract-Data/RyanData-Address-Utils#22
PR: Abstract-Data/RyanData-Address-Utils#23
Branch: `feat/drop-direction-uniqueness`

Port the Phase A uniqueness model: directional is `PRE|POST`, not prefix-only. Pandas, not Polars. Do not submodule voterfile-audit-pipeline. Do not fold into AddressService. ADDRFEAT range math stays; uniqueness dir becomes the pair. House-number suffix as a matcher is out of scope. No PII in samples.

## Files in scope

- EDIT `src/ryandata_address_utils/match/{keys,uniqueness,geo,voters,ranges,run,__init__}.py`
- EDIT `tests/test_match_{keys,uniqueness,geo,voters,ranges,run}.py`
- EDIT `README.md`, `docs/ARCHITECTURE.md`

## Behavior to ship

- `dir_pair_canon`: `E|` ≠ `|E`; EAST/E collapse; None/None → `|`
- Suffix-only N/S twins are problem keys; prefix-E vs suffix-E is a problem
- `match_drop_direction` → `EXCLUDED_PROBLEM` for suffix twins
- `fullname_dir_and_nodir_key("MAIN ST W")` → `("|W", …)`
- TxGIO: `pre_dir`=`St_PreDir`, `post_dir`=`St_PosDir`, `zip5`=`Post_Code` (5-char)
- Voters: `pre_dir`=`RSTPRE`, `post_dir`=`RSTSFX`
- `uniqueness_at_geography` / `cross_precinct_twin_counts` / `problem_pattern_counts` on `summary.json` (CD grain skipped unless PLANC2333 already exists)
- README: suffix pair, precinct-as-join-key circularity, cross-precinct twins, 2026 vs 2024 vintage, vendor-missing-dir

## Checks

```bash
uv run pytest tests/test_match_*.py -q
uv run pytest tests/test_match_keys.py tests/test_match_uniqueness.py tests/test_match_ranges.py tests/test_match_geo.py tests/test_match_fetch.py tests/test_match_run.py tests/test_match_cli.py tests/test_match_voters.py --cov=src/ryandata_address_utils/match --cov-report=term-missing --cov-fail-under=80
uv run pytest --cov=src --cov-fail-under=80
uv run ruff check src/ryandata_address_utils/match tests/test_match_*.py
uv run ruff format --check src/ryandata_address_utils/match tests/test_match_*.py
uv run ty check src/ryandata_address_utils/match
```

## Evidence before done

- Suffix twins excluded; `E|` ≠ `|E`
- TxGIO/TIGER/voter frames carry `post_dir`
- `summary.json` has geography / twins / patterns
- README contains `PRE|POST` and `cross-precinct`
- PR #23 body updated
