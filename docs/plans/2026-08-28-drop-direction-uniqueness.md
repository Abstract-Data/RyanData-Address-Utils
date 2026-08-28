# Drop-Direction Uniqueness + ADDRFEAT Matcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `ryandata_address_utils.match` so Derek Ryan can run drop-direction uniqueness and TIGER ADDRFEAT range matching from this public package without depending on voterfile-audit-pipeline.

**Architecture:** New `match/` subpackage next to `pandas_ext.py`, not folded into `AddressService`. Scalar key/range helpers are pandas-free. DataFrame matchers require the existing `[pandas]` extra, import pandas lazily, and stay vectorized (groupby / merge — no row loops). Callers supply `pct`; v1 does not attach precincts.

**Tech Stack:** Python 3.12–3.13, pandas (optional extra), pytest, ruff 100, ty. No polars, no geopandas.

**Issue:** #22

---

## File map

| Path | Responsibility |
|------|----------------|
| `src/ryandata_address_utils/match/keys.py` | `DIRECTIONALS`, `canon_dir`, `normalize_precinct_code`, `drop_direction_key`, `fullname_dir_and_nodir_key` |
| `src/ryandata_address_utils/match/uniqueness.py` | `classify_problem_keys`, `match_drop_direction` |
| `src/ryandata_address_utils/match/ranges.py` | `addrfeat_range_field_names`, `house_in_addrfeat_range`, `match_addrfeat_ranges` |
| `src/ryandata_address_utils/match/__init__.py` | Public exports + outcome constants |
| `tests/test_match_*.py` | Ported uniqueness/range cases from the audit-pipeline compare script |
| `README.md`, `docs/ARCHITECTURE.md`, `AGENTS.md` | Document the submodule; do not add to top-level `__init__.py` |

Column contract for DataFrame helpers:

- voters: `num`, `street_key_nodir`, `county`, `pct`
- points: those plus `dir` (optional `unit`)
- ranges: `street_key_nodir`, `county`, `pct`, `dir`, `lfrom`, `lto`, `rfrom`, `rto`

Outcomes: `MATCH = "match"`, `EXCLUDED_PROBLEM = "excluded_problem"`, `UNMATCHED = "unmatched"`.

Provenance (do not copy Polars): `voterfile-audit-pipeline` `scripts/compare_direction_match.py` (`canon_dir`, `classify_problem_keys`, `house_in_addrfeat_range`, `tiger_derek_outcome`, `fullname_dir_and_nodir_key`) and `normalize_precinct_code` in `src/stages/geography/precinct_vintages.py`.

### Task 1: Failing tests for keys

**Files:**
- Create: `tests/test_match_keys.py`

- [x] Write tests for `canon_dir`, `normalize_precinct_code`, `drop_direction_key`, `fullname_dir_and_nodir_key`
- [x] Run `uv run pytest tests/test_match_keys.py -q` — expected FAIL (module missing)
- [x] Implement `keys.py` + export from `__init__.py`
- [x] Re-run — PASS

### Task 2: Failing tests for uniqueness

**Files:**
- Create: `tests/test_match_uniqueness.py`
- Create: `src/ryandata_address_utils/match/uniqueness.py`

- [x] Port E+W problem, EAST+E not, blank vs E, N vs S, NE vs N, unit split, match/exclude/unmatch
- [x] Run — FAIL
- [x] Implement pandas groupby `nunique` + left-join
- [x] Re-run — PASS

### Task 3: Failing tests for ADDRFEAT ranges

**Files:**
- Create: `tests/test_match_ranges.py`
- Create: `src/ryandata_address_utils/match/ranges.py`

- [x] Port 2024/2025 field names, even-in-even, even-vs-odd miss, hyphenated house, unique range match, E+W covering same number, even-E/odd-W unique
- [x] Run — FAIL
- [x] Implement scalar + vectorized range match
- [x] Re-run — PASS

### Task 4: Docs

- [x] README usage section
- [x] ARCHITECTURE package tree
- [x] AGENTS.md Key Files row

### Task 5: Lint, types, full match tests

```bash
uv run ruff check src/ryandata_address_utils/match tests/test_match_*.py
uv run ruff format src/ryandata_address_utils/match tests/test_match_*.py
uv run ty check src/ryandata_address_utils/match
uv run pytest tests/test_match_keys.py tests/test_match_uniqueness.py tests/test_match_ranges.py tests/test_pandas_utils.py -q
```

### Out of scope

- `[geo]` extra / geopandas PIP attach
- Submodule of voterfile-audit-pipeline
- TxGIO address-point index (issue #21)
- Folding into `AddressService`
- Texas sentinel precinct codes (`99999`) — caller pre-filters
