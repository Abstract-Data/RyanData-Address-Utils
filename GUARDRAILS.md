# GUARDRAILS.md — RyanData-Address-Utils
<!-- Version: 1.0.0 | Maintainer: John Eakin -->

## Always

- Add type hints to all function signatures
- Format with `ruff format` before committing
- Write or update tests for every code change
- Use structured logging (`logging` module) — never `print()`
- Raise domain errors (`RyanDataAddressError`, `RyanDataValidationError`)

## Ask First

- Adding a new package dependency
- Changing a Pydantic model field (may break downstream consumers)
- Changing the public API in `__init__.py`
- Altering shapefile schema or PISD boundary logic

## Never

- Store secrets, tokens, or credentials in source code
- Use bare `except:` without specifying the exception type
- Commit `.env` files or production data files
- Use `print()` as a substitute for logging
- Access `src/pisd_shape/data/` files outside the `pisd_shape` module

## Data Sensitivity

- Voter file data and shapefiles are **not** committed to git
- Test fixtures use synthetic or publicly available data only
- Production data paths are configured via environment variables
