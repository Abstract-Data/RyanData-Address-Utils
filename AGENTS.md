# AGENTS.md - AI Coding Assistant Guide

This document provides context for AI coding assistants (Claude, GPT, Copilot, Cursor, etc.) working with the `ryandata-address-utils` codebase.

---

## Codebase Overview

**Package:** `ryandata-address-utils`
**Purpose:** US address parsing library with Pydantic models, validation, and pandas integration
**Python Version:** 3.12+ required (<=3.13)
**License:** MIT

### Architecture Patterns

- **Facade Pattern:** `AddressService` provides a unified interface to parsers, validators, and data sources
- **Protocol-based Interfaces:** Uses Python `Protocol` classes instead of ABCs for loose coupling
- **Factory Pattern:** `ParserFactory`, `DataSourceFactory` for extensible component creation
- **Composite Pattern:** `CompositeValidator` chains multiple validators
- **Builder Pattern:** `AddressBuilder` for fluent address construction

### Key Dependencies

- `pydantic>=2.0.0` - Data validation and serialization
- `usaddress>=0.5.16` - Default US address parser backend
- `abstract-validation-base` - ProcessLog system for transformation tracking
- `typer` + `trogon` - CLI with interactive TUI

---

## Key Files

| File | Purpose |
|------|---------|
| `src/ryandata_address_utils/__init__.py` | Public API exports - check here for available symbols |
| `src/ryandata_address_utils/service.py` | `AddressService` facade - main entry point |
| `src/ryandata_address_utils/models/address.py` | `Address` Pydantic model with 26+ fields |
| `src/ryandata_address_utils/models/results.py` | `ParseResult`, `ZipInfo` dataclasses |
| `src/ryandata_address_utils/protocols.py` | Protocol definitions for extensibility |
| `src/ryandata_address_utils/parsers/` | Parser implementations (usaddress, libpostal) |
| `src/ryandata_address_utils/validation/` | Validators (ZIP, state, composite) |
| `src/ryandata_address_utils/data/` | Data sources (CSV-backed ZIP database) |
| `src/ryandata_address_utils/core/` | Shared utilities (formatters, tracking, errors) |

---

## Coding Conventions

### Style & Linting

- **Formatter:** Ruff (`ruff format`)
- **Linter:** Ruff with `E, F, I, UP, B, SIM` rule sets
- **Type Checker:** MyPy in strict mode (`disallow_untyped_defs = true`)
- **Line Length:** 100 characters

### Pydantic Models

```python
# Use Field() with descriptions for all model fields
field_name: str | None = Field(
    default=None,
    description="Clear description of the field",
    validation_alias=AliasChoices("FieldName", "alias"),
)
```

### Protocol-based Design

```python
# Define protocols in protocols.py
class ValidatorProtocol(Protocol):
    def validate(self, address: Address) -> ValidationResult: ...

# Implementations satisfy protocols implicitly
class ZipCodeValidator:
    def validate(self, address: Address) -> ValidationResult:
        # Implementation
```

### ProcessLog for Transformations

```python
# Models inherit from RyanDataValidationBase which provides process_log
address.add_cleaning_process(
    field="StateName",
    original_value="Texas",
    new_value="TX",
    reason="Normalized state name to abbreviation",
)
```

### Error Handling

- Use `RyanDataAddressError` for address-specific errors
- Use `RyanDataValidationError` for validation failures
- All errors include package context via `PACKAGE_NAME`

---

## Common Tasks

### Adding a New Validator

1. Create class in `validation/validators.py`
2. Implement `ValidatorProtocol` (must have `validate(address) -> ValidationResult`)
3. Register with `CompositeValidator` if needed

```python
class MyValidator:
    def validate(self, address: Address) -> ValidationResult:
        errors = []
        # validation logic
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
```

### Adding a New Parser Backend

1. Create class in `parsers/` implementing `AddressParserProtocol`
2. Register with `ParserFactory.register("name", MyParser)`
3. Use via `AddressService(parser=ParserFactory.create("name"))`

### Extending the Address Model

1. Add field to `models/address.py` with proper `Field()` definition
2. Add to `ADDRESS_FIELDS` enum if needed for iteration
3. Update `AddressFormatter` if field affects full address computation

### Working with Pandas

```python
service = AddressService()
df = service.parse_dataframe(df, "address_column", prefix="addr_")
# Returns DataFrame with addr_StreetName, addr_ZipCode, etc.
```

---

## Testing

- **Framework:** pytest with pytest-cov
- **Test Location:** `tests/` directory
- **Run Tests:** `uv run pytest`
- **Coverage:** Target 80%+ coverage

```bash
uv run pytest                    # Run all tests
uv run pytest -v                 # Verbose output
uv run pytest --cov=src          # With coverage
uv run pytest -k "test_parse"    # Run specific tests
```

---

## Development Commands

```bash
uv sync                          # Install dependencies
uv run pytest                    # Run tests
uv run ruff check src/           # Lint
uv run ruff format src/          # Format
uv run mypy src/                 # Type check
uv run ryandata-address-utils-setup  # Setup libpostal (optional)
```

---

## Architecture Reference

See `docs/ARCHITECTURE.md` for:
- Detailed data flow diagrams
- SOLID principles applied
- DRY improvements made
- Full package structure

---

## Important Notes for AI Assistants

1. **Do not redesign architecture** without explicit approval - stick to incremental changes
2. **Use existing patterns** - follow the protocol/factory patterns already in place
3. **ProcessLog is preferred** over legacy `CleaningTracker` for new code
4. **Check `__init__.py`** for the public API before suggesting imports
5. **Run `uv run pytest`** to verify changes don't break existing tests
6. **Cursor-specific workflows** are documented in `.cursor/agents.md`

---

## Reporting Issues to This Package

If you're an AI agent assisting with a project that uses `ryandata-address-utils` and you discover a bug, missing feature, or documentation issue, you can file an issue against this package.

**Repository:** `Abstract-Data/RyanData-Address-Utils`

### Using MCP GitHub Server (Recommended for AI Agents)

If your AI client (Cursor, Claude Desktop, etc.) has the GitHub MCP server configured, use the `mcp_github_create_issue` tool targeting `Abstract-Data/RyanData-Address-Utils`.

**Cursor** (`~/.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "<your-token>"
      }
    }
  }
}
```

### Issue Templates (Structured Forms)

This repository uses GitHub's YAML-based issue forms. When creating issues via MCP, format the body to match the template fields:

**Bug Report** — Use title prefix `[Bug]: `
```markdown
### Prerequisites
- [x] I have searched existing issues
- [x] I am using the latest version

### Bug Description
[Clear description of the bug]

### Steps to Reproduce
```python
from ryandata_address_utils import AddressService, parse

# Minimal code that reproduces the issue
```

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happens]

### Affected Component
[AddressService / Parsers / Models / Validators / Pandas / CLI]

### Error Output
```
[Stack trace if applicable]
```

### Environment
- Package Version: [e.g., 0.7.1]
- Python Version: [3.12 / 3.13]
- OS: [macOS / Linux / Windows]
```

**Feature Request** — Use title prefix `[Feature]: `
```markdown
### Prerequisites
- [x] I have searched existing issues
- [x] I have read the documentation

### Problem Statement
[What limitation or pain point does this address?]

### Proposed Solution
[What would you like to see?]

### Alternatives Considered
[Other approaches you've thought about]

### Affected Component
[AddressService / Parsers / Models / Validators / Pandas / CLI / New Component]

### Use Case Example
```python
# Example code showing how this feature would be used
```

### Priority
[Nice to have / Would significantly improve workflow / Blocking use case]
```

**Documentation Issue** — Use title prefix `[Docs]: `
```markdown
### Issue Type
[Missing / Incorrect / Unclear / Needs example / Typo / Outdated]

### Location
[README.md / AGENTS.md / docs/ARCHITECTURE.md / Docstrings / API reference]

### Problem Description
[What's wrong or missing?]

### Suggested Improvement
[How should the documentation be improved?]
```

### Auto-Labeling

Issues are automatically labeled based on content:

| Keywords in Issue | Label Applied |
|-------------------|---------------|
| AddressService, parse, facade | `component:service` |
| Address, Pydantic, model, Field | `component:models` |
| usaddress, libpostal, parser | `component:parsers` |
| validator, ZIP, state, validation | `component:validators` |
| pandas, DataFrame, series | `component:pandas` |
| CLI, setup, TUI, typer | `component:cli` |
| ProcessLog, cleaning, tracking | `component:tracking` |

Bug reports automatically receive a helpful comment with relevant documentation links.

---

## Contributing Pull Requests

When submitting PRs to this repository, ensure the following checks pass locally:

### Pre-submission Checklist

```bash
# Linting
uv run ruff check src tests
uv run ruff format src tests

# Type checking
uv run mypy src

# Tests
uv run pytest
```

### PR Requirements

1. **Link to related issue** — Reference with `Closes #123`
2. **Type of change** — Bug fix, feature, docs, refactor, tests
3. **Tests** — Add tests for new functionality
4. **Documentation** — Update docs/docstrings for user-facing changes

### CI Checks (Automated)

These run automatically on PRs:
- `ruff check` and `ruff format --check`
- `mypy src`
- `pytest --cov`

PRs cannot be merged until all CI checks pass.
