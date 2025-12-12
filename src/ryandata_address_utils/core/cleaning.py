"""Cleaning operation tracking for data transformation pipelines.

Provides infrastructure for tracking when data components are cleaned,
normalized, or transformed during processing.

.. deprecated::
    This module is deprecated. For Pydantic models, use ValidationBase from
    ryandata_address_utils.validation.base which provides ProcessLog-based
    tracking with add_error(), add_cleaning_process(), and audit_log() methods.

    For non-Pydantic classes, these utilities remain available but consider
    migrating to ProcessLog/ProcessEntry from ryandata_address_utils.core.process_log.
"""

from __future__ import annotations

import warnings
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CleaningOperation:
    """Record of a component cleaning operation.

    .. deprecated::
        Use ProcessEntry from ryandata_address_utils.core.process_log instead.

    Tracks when a data component was cleaned, normalized, or transformed.

    Attributes:
        component: Name of the component that was cleaned (e.g., "zip5", "state").
        original_value: The original value before cleaning/transformation.
        reason: Explanation of why the component was cleaned.
        timestamp: ISO format timestamp of when the operation occurred.
        new_value: The value after cleaning/transformation (None if removed).
        operation_type: Category of operation performed:
            - "normalization": Format standardization
            - "expansion": Abbreviation expansion
            - "cleaning": Removal of invalid data
            - "formatting": Whitespace, punctuation changes
    """

    component: str
    original_value: str | None
    reason: str
    timestamp: str  # ISO format
    new_value: str | None = None
    operation_type: str = "cleaning"


@dataclass
class CleaningTracker:
    """Standalone tracker for cleaning operations.

    .. deprecated::
        Use ProcessLog from ryandata_address_utils.core.process_log instead.

    Use this when you need cleaning tracking without inheritance.
    """

    cleaning_operations: list[CleaningOperation] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Emit deprecation warning on instantiation."""
        warnings.warn(
            "CleaningTracker is deprecated. Use ProcessLog from "
            "ryandata_address_utils.core.process_log instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    def add_cleaning_operation(
        self,
        component: str,
        original_value: Any,
        reason: str,
        new_value: Any = None,
        operation_type: str = "cleaning",
    ) -> None:
        """Track a cleaning operation."""
        self.cleaning_operations.append(
            CleaningOperation(
                component=component,
                original_value=str(original_value) if original_value is not None else None,
                reason=reason,
                timestamp=datetime.now().isoformat(),
                new_value=str(new_value) if new_value is not None else None,
                operation_type=operation_type,
            )
        )

    def has_cleaning_operations(self) -> bool:
        """Check if any cleaning operations were performed."""
        return len(self.cleaning_operations) > 0

    def get_cleaning_report(self) -> list[dict[str, Any]]:
        """Get cleaning operations as a list of dictionaries for export."""
        return [
            {
                "component": op.component,
                "original_value": op.original_value,
                "new_value": op.new_value,
                "reason": op.reason,
                "operation_type": op.operation_type,
                "timestamp": op.timestamp,
            }
            for op in self.cleaning_operations
        ]

    def get_cleaning_summary(self) -> dict[str, int]:
        """Get summary counts of cleaning operations by component."""
        return dict(Counter(op.component for op in self.cleaning_operations))

    def get_cleaning_summary_by_type(self) -> dict[str, int]:
        """Get summary counts of cleaning operations by operation type."""
        return dict(Counter(op.operation_type for op in self.cleaning_operations))


class CleaningMixin:
    """Mixin that adds cleaning operation tracking to any class.

    .. deprecated::
        For Pydantic models, inherit from ValidationBase instead, which provides
        ProcessLog-based tracking with add_error(), add_cleaning_process(),
        and audit_log() methods.

        For non-Pydantic dataclasses, consider using ProcessLog directly from
        ryandata_address_utils.core.process_log.

    Classes using this mixin must define:
        cleaning_operations: list[CleaningOperation] = field(default_factory=list)

    Example:
        @dataclass
        class MyResult(CleaningMixin):
            data: str
            cleaning_operations: list[CleaningOperation] = field(default_factory=list)
    """

    cleaning_operations: list[CleaningOperation]

    def add_cleaning_operation(
        self,
        component: str,
        original_value: Any,
        reason: str,
        new_value: Any = None,
        operation_type: str = "cleaning",
    ) -> None:
        """Track a cleaning operation performed during processing."""
        self.cleaning_operations.append(
            CleaningOperation(
                component=component,
                original_value=str(original_value) if original_value is not None else None,
                reason=reason,
                timestamp=datetime.now().isoformat(),
                new_value=str(new_value) if new_value is not None else None,
                operation_type=operation_type,
            )
        )

    def has_cleaning_operations(self) -> bool:
        """Check if any components were cleaned."""
        return len(self.cleaning_operations) > 0

    def get_cleaning_report(self) -> list[dict[str, Any]]:
        """Get cleaning operations as a list of dictionaries for export."""
        return [
            {
                "component": op.component,
                "original_value": op.original_value,
                "new_value": op.new_value,
                "reason": op.reason,
                "operation_type": op.operation_type,
                "timestamp": op.timestamp,
            }
            for op in self.cleaning_operations
        ]

    def get_cleaning_summary(self) -> dict[str, int]:
        """Get summary counts of cleaning operations by component."""
        return dict(Counter(op.component for op in self.cleaning_operations))

    def get_cleaning_summary_by_type(self) -> dict[str, int]:
        """Get summary counts of cleaning operations by operation type."""
        return dict(Counter(op.operation_type for op in self.cleaning_operations))
