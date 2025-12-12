"""Abstract base validator class.

Provides a generic base class for creating validators for any model type.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ryandata_address_utils.core.results import ValidationResult

T = TypeVar("T")


class BaseValidator(ABC, Generic[T]):
    """Abstract base class for validators.

    Generic over T, the type of object being validated.
    Subclass this to create validators for specific model types.

    Example:
        class MyModelValidator(BaseValidator[MyModel]):
            @property
            def name(self) -> str:
                return "my_model"

            def validate(self, item: MyModel) -> ValidationResult:
                result = ValidationResult(is_valid=True)
                if not item.required_field:
                    result.add_error("required_field", "Field is required")
                return result
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of this validator for error reporting."""
        ...

    @abstractmethod
    def validate(self, item: T) -> ValidationResult:
        """Validate an item.

        Args:
            item: Object to validate.

        Returns:
            ValidationResult containing validation status and any errors.
        """
        ...
