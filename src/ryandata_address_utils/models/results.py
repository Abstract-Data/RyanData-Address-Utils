"""Result classes for address parsing operations.

This module contains dataclasses for representing parsing results
and ZIP code information.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from abstract_validation_base import ProcessEntry, ProcessLog, ValidationResult

if TYPE_CHECKING:
    from ryandata_address_utils.models.address import Address, InternationalAddress


@dataclass
class ZipInfo:
    """Information about a US ZIP code."""

    zip_code: str
    city: str
    state_id: str
    state_name: str
    county_name: str


@dataclass
class ParseResult:
    """Result of address parsing with log aggregation.

    Extended to support partial validation with component-level cleaning tracking.
    ParseResult has its own ProcessLog for process-level operations (things that
    happen before/during model creation), and can aggregate logs from child models.
    """

    raw_input: str
    address: Address | None = None
    international_address: InternationalAddress | None = None
    error: Exception | None = None
    validation: ValidationResult | None = None
    source: str | None = None  # "us" or "international"
    is_international: bool | None = None
    # Process-level log (for operations before model exists)
    process_log: ProcessLog = field(default_factory=ProcessLog)
    # Partial validation tracking fields
    cleaned_components: dict[str, Any] = field(default_factory=dict)
    invalid_components: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        """Check if parsing was successful and validation passed."""
        if self.error is not None:
            return False
        if self.address is None and self.international_address is None:
            return False
        if self.validation is not None:
            return self.validation.is_valid
        return True

    @property
    def is_parsed(self) -> bool:
        """Check if parsing was successful (regardless of validation)."""
        return self.error is None and (
            self.address is not None or self.international_address is not None
        )

    def to_dict(self) -> dict[str, str | None]:
        """Convert to dictionary of address fields."""
        from ryandata_address_utils.models.enums import ADDRESS_FIELDS

        # Prefer international address data when available to preserve postal codes
        if self.international_address:
            return self.international_address.to_dict()
        if self.address:
            return self.address.to_dict()
        return {f: None for f in ADDRESS_FIELDS}

    def add_process_error(
        self,
        field: str,
        message: str,
        value: Any = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Track process-level errors (before model exists).

        Args:
            field: Name of the field with the error.
            message: Error message describing the issue.
            value: The problematic value (optional).
            context: Additional context dict (optional).
        """
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
        """Track process-level cleaning (before model exists).

        Args:
            field: Name of the field that was cleaned.
            original_value: The original value before transformation.
            new_value: The value after transformation.
            reason: Explanation of why the cleaning was performed.
            operation_type: Category of operation (cleaning, normalization, etc.).
        """
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
        """Combine logs from self + all child models.

        Returns:
            List of dicts suitable for pd.DataFrame(), sorted by timestamp.
            Each entry includes a 'source' field identifying where it originated:
            - "parse_result": Process-level operations
            - "address": Operations from the Address model
            - "international_address": Operations from the InternationalAddress model
        """
        all_entries: list[dict[str, Any]] = []

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

    # Backward-compatible methods (delegate to ProcessLog-based implementation)
    # These methods are deprecated but kept for compatibility with existing code.

    @property
    def cleaning_operations(self) -> list[ProcessEntry]:
        """Get all cleaning operations from the process log.

        .. deprecated::
            Access `process_log.cleaning` directly instead.

        Returns:
            List of ProcessEntry objects representing cleaning operations.
        """
        return self.process_log.cleaning

    def add_cleaning_operation(
        self,
        component: str,
        original_value: Any,
        reason: str,
        new_value: Any = None,
        operation_type: str = "cleaning",
    ) -> None:
        """Track a cleaning operation (backward-compatible method).

        .. deprecated::
            Use `add_process_cleaning()` instead.

        Args:
            component: Name of the component that was cleaned.
            original_value: The original value before transformation.
            reason: Explanation of why the cleaning was performed.
            new_value: The value after transformation (optional).
            operation_type: Category of operation (default: "cleaning").
        """
        self.add_process_cleaning(
            field=component,
            original_value=original_value,
            new_value=new_value,
            reason=reason,
            operation_type=operation_type,
        )

    def has_cleaning_operations(self) -> bool:
        """Check if any cleaning operations were performed.

        .. deprecated::
            Check `len(process_log.cleaning) > 0` directly instead.

        Returns:
            True if any cleaning operations exist.
        """
        return len(self.process_log.cleaning) > 0

    def get_cleaning_report(self) -> list[dict[str, Any]]:
        """Get cleaning operations as a list of dictionaries for export.

        .. deprecated::
            Use `aggregate_logs()` instead for a more comprehensive report.

        Returns:
            List of dicts with component, original_value, new_value, reason,
            operation_type, and timestamp fields.
        """
        return [
            {
                "component": op.field,
                "original_value": op.original_value,
                "new_value": op.new_value,
                "reason": op.message,
                "operation_type": op.context.get("operation_type", "cleaning"),
                "timestamp": op.timestamp,
            }
            for op in self.process_log.cleaning
        ]

    def get_cleaning_summary(self) -> dict[str, int]:
        """Get summary counts of cleaning operations by component.

        .. deprecated::
            Use `aggregate_logs()` with DataFrame groupby instead.

        Returns:
            Dict mapping component names to operation counts.
        """
        return dict(Counter(op.field for op in self.process_log.cleaning))

    def get_cleaning_summary_by_type(self) -> dict[str, int]:
        """Get summary counts of cleaning operations by operation type.

        .. deprecated::
            Use `aggregate_logs()` with DataFrame groupby instead.

        Returns:
            Dict mapping operation types to counts.
        """
        return dict(
            Counter(
                op.context.get("operation_type", "cleaning") for op in self.process_log.cleaning
            )
        )
