"""Address validation base class.

Re-exports the generic BaseValidator from core and provides
an address-specific type alias for convenience.

Also provides ValidationBase, a Pydantic base model with built-in
process logging for cleaning and errors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic_core import PydanticCustomError

from ryandata_address_utils.core.process_log import ProcessEntry, ProcessLog
from ryandata_address_utils.core.validation import BaseValidator

if TYPE_CHECKING:
    from ryandata_address_utils.models import Address  # noqa: F401 (used as forward reference)

# Re-export for backwards compatibility
__all__ = ["BaseValidator", "AddressValidator", "ValidationBase", "RyanDataValidationBase"]

# Address-specific type alias for convenience (uses forward reference to avoid circular import)
AddressValidator = BaseValidator["Address"]


class ValidationBase(BaseModel):
    """Base model with built-in process logging for cleaning and errors.

    All models inheriting from this class automatically get:
    - process_log: ProcessLog field (excluded from serialization)
    - add_error(): Log an error and optionally raise ValidationError
    - add_cleaning_process(): Log a cleaning/transformation operation
    - audit_log(): Export combined entries for DataFrame analysis

    Example:
        class MyModel(ValidationBase):
            name: str

        model = MyModel(name="test")
        model.add_cleaning_process("name", "  test  ", "test", "Trimmed whitespace")
        model.add_error("name", "Name too short", "test")
        print(model.audit_log())
    """

    model_config = ConfigDict(
        # Subclasses can override this
        extra="ignore",
    )

    process_log: ProcessLog = Field(default_factory=ProcessLog, exclude=True)

    def _create_error(
        self,
        error_type: str,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> Exception:
        """Create an error to raise. Override in subclasses for custom error types.

        Default implementation returns PydanticCustomError.

        Args:
            error_type: Type/category of the error.
            message: Error message describing the issue.
            context: Additional context dict (optional).

        Returns:
            Exception instance to be raised.
        """
        return PydanticCustomError(
            error_type,
            message,
            context or {},
        )

    def add_error(
        self,
        field: str,
        message: str,
        value: Any = None,
        context: dict[str, Any] | None = None,
        raise_exception: bool = False,
    ) -> None:
        """Log an error and optionally raise an exception.

        Args:
            field: Name of the field with the error.
            message: Error message describing the issue.
            value: The problematic value (optional).
            context: Additional context dict (optional).
            raise_exception: If True, raise an exception after logging.

        Raises:
            Exception: If raise_exception is True. The exception type is
                determined by _create_error() which can be overridden.
        """
        entry = ProcessEntry(
            entry_type="error",
            field=field,
            message=message,
            original_value=str(value) if value is not None else None,
            context=context or {},
        )
        self.process_log.errors.append(entry)

        if raise_exception:
            raise self._create_error(
                error_type="validation_error",
                message=f"{field}: {message}",
                context={"field": field, "value": value, **(context or {})},
            )

    def add_cleaning_process(
        self,
        field: str,
        original_value: Any,
        new_value: Any,
        reason: str,
        operation_type: str = "cleaning",
    ) -> None:
        """Log a cleaning/transformation operation.

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

    def audit_log(self, source: str | None = None) -> list[dict[str, Any]]:
        """Export combined cleaning and error entries for DataFrame analysis.

        Args:
            source: Optional source identifier to add to each entry.

        Returns:
            List of dicts suitable for pd.DataFrame(), sorted by timestamp.
            Each entry includes entry_type, field, message, timestamps, etc.
        """
        entries: list[dict[str, Any]] = []
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


class RyanDataValidationBase(ValidationBase):
    """ValidationBase with RyanData-specific error handling.

    Overrides _create_error() to raise RyanDataAddressError instead of
    generic PydanticCustomError. Use this as the base class for models
    in the ryandata_address_utils package.

    Example:
        class Address(RyanDataValidationBase):
            street: str

        addr = Address(street="123 Main")
        addr.add_error("street", "Invalid format", raise_exception=True)
        # Raises RyanDataAddressError instead of PydanticCustomError
    """

    def _create_error(
        self,
        error_type: str,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> Exception:
        """Create a RyanDataAddressError.

        Args:
            error_type: Type/category of the error.
            message: Error message describing the issue.
            context: Additional context dict (optional).

        Returns:
            RyanDataAddressError instance.
        """
        # Late import to avoid circular dependency with models.py
        from ryandata_address_utils.models import RyanDataAddressError

        return RyanDataAddressError(
            error_type,
            message,
            {"package": "ryandata_address_utils", **(context or {})},
        )
