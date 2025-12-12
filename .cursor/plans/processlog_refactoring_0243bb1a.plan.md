---
name: ProcessLog Refactoring
overview: Create a unified ProcessLog system with consistent APIs across all models. ValidationBase provides logging for Pydantic models, ParseResult aggregates logs from all child models plus its own process-level operations.
todos:
  - id: create-process-log
    content: Create ProcessLog and ProcessEntry models in core/process_log.py
    status: completed
  - id: create-validation-base
    content: Create ValidationBase class with add_error(), add_cleaning_process(), audit_log() methods
    status: completed
  - id: update-address-model
    content: Update Address to inherit from ValidationBase
    status: completed
  - id: update-intl-address
    content: Update InternationalAddress to inherit from ValidationBase
    status: completed
  - id: update-parseresult
    content: Update ParseResult with ProcessLog and aggregate_logs() method
    status: completed
  - id: deprecate-legacy-cleaning
    content: Deprecate CleaningMixin usage in ParseResult (keep available for non-Pydantic classes)
    status: completed
  - id: update-core-exports
    content: Update core/__init__.py exports to add ProcessLog, ProcessEntry
    status: completed
  - id: fix-imports
    content: Update imports throughout codebase
    status: completed
---

# ProcessLog Refactoring Plan

## Overview

Create a unified `ProcessLog` system with **consistent, composable APIs** across all models:

```
┌─────────────────────────────────────────────────────────────────┐
│  ParseResult (aggregates all logs)                              │
│  ┌─────────────────────┐    ┌──────────────────────────────┐   │
│  │ Address             │    │ InternationalAddress         │   │
│  │ - process_log       │    │ - process_log                │   │
│  │ - add_error()       │    │ - add_error()                │   │
│  │ - add_cleaning()    │    │ - add_cleaning()             │   │
│  │ - audit_log()       │    │ - audit_log()                │   │
│  └─────────────────────┘    └──────────────────────────────┘   │
│                                                                 │
│  + ParseResult.process_log (for process-level operations)       │
│  + ParseResult.aggregate_logs() → combines everything           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Create ProcessLog Models

**File:** `src/ryandata_address_utils/core/process_log.py` (new file)

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Any

class ProcessEntry(BaseModel):
    """Base entry for any process log record."""
    entry_type: Literal["cleaning", "error"]
    field: str
    message: str
    original_value: str | None = None
    new_value: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    context: dict[str, Any] = Field(default_factory=dict)

class ProcessLog(BaseModel):
    """Tracks cleaning operations and errors during model processing."""
    cleaning: list[ProcessEntry] = Field(default_factory=list)
    errors: list[ProcessEntry] = Field(default_factory=list)
```

---

## 2. Create ValidationBase Class

**File:** `src/ryandata_address_utils/validation/base.py` (modify existing)

```python
from pydantic import BaseModel, Field
from typing import Any
from ryandata_address_utils.core.process_log import ProcessLog, ProcessEntry

class ValidationBase(BaseModel):
    """Base model with built-in process logging for cleaning and errors."""

    process_log: ProcessLog = Field(default_factory=ProcessLog, exclude=True)

    def add_error(
        self,
        field: str,
        message: str,
        value: Any = None,
        context: dict | None = None,
        raise_exception: bool = False,
    ) -> None:
        """Log an error and optionally raise ValidationError."""
        entry = ProcessEntry(
            entry_type="error",
            field=field,
            message=message,
            original_value=str(value) if value is not None else None,
            context=context or {},
        )
        self.process_log.errors.append(entry)

        if raise_exception:
            from ryandata_address_utils.core.errors import RyanDataValidationError
            raise RyanDataValidationError(...)

    def add_cleaning_process(
        self,
        field: str,
        original_value: Any,
        new_value: Any,
        reason: str,
        operation_type: str = "cleaning",
    ) -> None:
        """Log a cleaning/transformation operation."""
        entry = ProcessEntry(
            entry_type="cleaning",
            field=field,
            message=reason,
            original_value=str(original_value) if original_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            context={"operation_type": operation_type},
        )
        self.process_log.cleaning.append(entry)

    def audit_log(self, source: str | None = None) -> list[dict[str, Any]]:
        """Export combined cleaning and error entries for DataFrame analysis.

        Args:
            source: Optional source identifier to add to each entry.
        """
        entries = []
        for entry in self.process_log.cleaning:
            d = entry.model_dump()
            if source:
                d["source"] = source
            entries.append(d)
        for entry in self.process_log.errors:
            d = entry.model_dump()
            if source:
                d["source"] = source
            entries.append(d)
        return sorted(entries, key=lambda x: x.get("timestamp", ""))
```

---

## 3. Update Address Model

**File:** `src/ryandata_address_utils/models.py`

- Change `class Address(BaseModel)` to `class Address(ValidationBase)`
- Import `ValidationBase` from the validation module
- Address automatically gets `process_log`, `add_error()`, `add_cleaning_process()`, `audit_log()`

---

## 4. Update InternationalAddress Model

**File:** `src/ryandata_address_utils/models.py`

- Change `class InternationalAddress(BaseModel)` to `class InternationalAddress(ValidationBase)`

---

## 5. Update ParseResult

**File:** `src/ryandata_address_utils/models.py`

ParseResult gets its **own ProcessLog** for process-level operations (things that happen before/during model creation):

```python
from ryandata_address_utils.core.process_log import ProcessLog, ProcessEntry

@dataclass
class ParseResult:
    """Result of address parsing with log aggregation."""

    raw_input: str
    address: Address | None = None
    international_address: InternationalAddress | None = None
    error: Exception | None = None
    validation: ValidationResult | None = None
    source: str | None = None
    is_international: bool | None = None

    # Process-level log (for operations before model exists)
    process_log: ProcessLog = field(default_factory=ProcessLog)

    # Keep for partial validation tracking
    cleaned_components: dict[str, Any] = field(default_factory=dict)
    invalid_components: dict[str, dict[str, Any]] = field(default_factory=dict)

    # REMOVE: cleaning_operations: list[CleaningOperation] (replaced by process_log)

    def add_process_error(
        self,
        field: str,
        message: str,
        value: Any = None,
        context: dict | None = None,
    ) -> None:
        """Track process-level errors (before model exists)."""
        entry = ProcessEntry(
            entry_type="error",
            field=field,
            message=message,
            original_value=str(value) if value is not None else None,
            context=context or {},
        )
        self.process_log.errors.append(entry)

    def add_process_cleaning(
        self,
        field: str,
        original_value: Any,
        new_value: Any,
        reason: str,
        operation_type: str = "cleaning",
    ) -> None:
        """Track process-level cleaning (before model exists)."""
        entry = ProcessEntry(
            entry_type="cleaning",
            field=field,
            message=reason,
            original_value=str(original_value) if original_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            context={"operation_type": operation_type},
        )
        self.process_log.cleaning.append(entry)

    def aggregate_logs(self) -> list[dict[str, Any]]:
        """Combine logs from self + all child models."""
        all_entries = []

        # Add process-level operations
        for entry in self.process_log.cleaning:
            all_entries.append({**entry.model_dump(), "source": "parse_result"})
        for entry in self.process_log.errors:
            all_entries.append({**entry.model_dump(), "source": "parse_result"})

        # Add model-level operations
        if self.address:
            all_entries.extend(self.address.audit_log(source="address"))
        if self.international_address:
            all_entries.extend(self.international_address.audit_log(source="international_address"))

        return sorted(all_entries, key=lambda x: x.get("timestamp", ""))
```

---

## 6. Deprecate (Don't Remove) Legacy Cleaning Infrastructure

**File:** `src/ryandata_address_utils/core/cleaning.py`

- Keep `CleaningMixin`, `CleaningTracker`, `CleaningOperation` available for non-Pydantic classes
- Add deprecation warning to CleaningMixin docstring
- ParseResult stops using CleaningMixin but it remains available

**File:** `src/ryandata_address_utils/core/__init__.py`

- Keep existing exports: `CleaningMixin`, `CleaningTracker`, `CleaningOperation`
- Add new exports: `ProcessLog`, `ProcessEntry`

---

## 7. Update Imports Throughout Codebase

- `models.py` - remove `CleaningMixin` from ParseResult, add `ProcessLog`, `ProcessEntry` imports
- Update any services/validators that call cleaning methods on ParseResult

---

## Key Design Decisions

| Decision | Choice |

|----------|--------|

| ProcessLog storage | `Field(exclude=True)` - accessible via constructor, excluded from serialization |

| Error behavior | Log first, then optionally raise based on `raise_exception` param |

| ParseResult | Has its OWN ProcessLog for process-level operations + aggregates child logs |

| Model tracking | Each model tracks its own operations via inherited ValidationBase |

| CleaningMixin | Deprecated but kept for non-Pydantic compatibility |

| Audit export | Combined list with `entry_type` AND `source` fields for DataFrame grouping |

---

## audit_log() Output Format

Each entry includes a `source` field identifying where it originated:

```python
[
    {
        "entry_type": "cleaning",
        "field": "raw_input",
        "message": "Trimmed whitespace from input",
        "original_value": "  123 Main St  ",
        "new_value": "123 Main St",
        "timestamp": "2025-12-11T10:29:59",
        "context": {"operation_type": "formatting"},
        "source": "parse_result"  # ← Process-level operation
    },
    {
        "entry_type": "cleaning",
        "field": "ZipCode",
        "message": "Normalized ZIP format",
        "original_value": "787491234",
        "new_value": "78749-1234",
        "timestamp": "2025-12-11T10:30:00",
        "context": {"operation_type": "formatting"},
        "source": "address"  # ← Model-level operation
    },
    {
        "entry_type": "error",
        "field": "StateName",
        "message": "Invalid state abbreviation",
        "original_value": "XX",
        "new_value": null,
        "timestamp": "2025-12-11T10:30:01",
        "context": {},
        "source": "address"
    }
]
```

**DataFrame analysis:**

```python
import pandas as pd
df = pd.DataFrame(result.aggregate_logs())
df.groupby(['source', 'entry_type']).size()
# source              entry_type
# address             cleaning      1
#                     error         1
# parse_result        cleaning      1
```
