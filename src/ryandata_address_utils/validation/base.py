from __future__ import annotations

from abc import ABC, abstractmethod

from ryandata_address_utils.models import Address, ValidationResult


class BaseValidator(ABC):
    """Abstract base class for address validators.

    Validators check specific aspects of an address (ZIP codes,
    states, etc.) and return validation results.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of this validator for error reporting."""
        ...

    @abstractmethod
    def validate(self, address: Address) -> ValidationResult:
        """Validate an address.

        Args:
            address: Address object to validate.

        Returns:
            ValidationResult containing validation status and any errors.
        """
        ...

