"""Address validation base class.

Re-exports the generic BaseValidator and ValidationBase from abstract_validation_base
and provides an address-specific type alias and RyanData-specific subclass.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from abstract_validation_base import (
    BaseValidator,
    ProcessEntry,
    ProcessLog,
    ValidationBase,
)

if TYPE_CHECKING:
    from ryandata_address_utils.models import Address  # noqa: F401 (used as forward reference)

# Re-export for backwards compatibility
__all__ = [
    "BaseValidator",
    "AddressValidator",
    "ValidationBase",
    "RyanDataValidationBase",
    "ProcessEntry",
    "ProcessLog",
]

# Address-specific type alias for convenience (uses forward reference to avoid circular import)
AddressValidator = BaseValidator["Address"]


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
