"""Composite validator for combining multiple validators.

Provides a generic composite validator that runs multiple validators
and aggregates their results.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from ryandata_address_utils.core.results import ValidationResult
from ryandata_address_utils.core.validation.base import BaseValidator

T = TypeVar("T")


class CompositeValidator(BaseValidator[T], Generic[T]):
    """Validator that combines multiple validators.

    Runs all validators and aggregates their results.
    """

    def __init__(self, validators: list[BaseValidator[T]]) -> None:
        """Initialize composite validator.

        Args:
            validators: List of validators to run.
        """
        self._validators = validators

    @property
    def name(self) -> str:
        """Name of this validator."""
        return "composite"

    def validate(self, item: T) -> ValidationResult:
        """Run all validators and combine results."""
        result = ValidationResult(is_valid=True)

        for validator in self._validators:
            validator_result = validator.validate(item)
            result.merge(validator_result)

        return result

    def add_validator(self, validator: BaseValidator[T]) -> None:
        """Add a validator to the composite."""
        self._validators.append(validator)

    def remove_validator(self, name: str) -> bool:
        """Remove a validator by name. Returns True if removed."""
        for i, v in enumerate(self._validators):
            if v.name == name:
                self._validators.pop(i)
                return True
        return False

    @property
    def validators(self) -> list[BaseValidator[T]]:
        """Get copy of validators list."""
        return self._validators.copy()
