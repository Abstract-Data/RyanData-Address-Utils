# TESTING.md — RyanData-Address-Utils
<!-- Version: 1.0.0 | Maintainer: John Eakin -->

## Framework

- **Runner:** pytest
- **Property-based:** Hypothesis
- **Coverage target:** 80%+ (src/)

## Commands

```bash
uv run pytest                        # all tests
uv run pytest --cov=src              # with coverage
uv run pytest -x                     # stop on first failure
uv run pytest -k "test_parse"        # filter by name
uv run pytest tests/unit/            # unit tests only
uv run pytest tests/property/        # Hypothesis tests only
```

## Test Layout

```
tests/
├── unit/           # Pure unit tests — no I/O, no network
├── integration/    # Tests that hit the filesystem or pandas
├── property/       # Hypothesis property-based tests
└── conftest.py     # Shared fixtures
```

## Test Standards

- Every public function has at least one unit test
- Parsers and validators get Hypothesis `@given` tests
- Fixtures live in `conftest.py`, not in test files
- No `print()` — use `caplog` or `capsys`
- Mock external I/O at the boundary (file reads, HTTP)

## CI

Tests run automatically on every PR via GitHub Actions.
All checks must pass before merge.
