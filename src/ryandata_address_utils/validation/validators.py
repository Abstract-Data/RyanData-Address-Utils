from __future__ import annotations

from ryandata_address_utils.models import Address, ValidationResult
from ryandata_address_utils.protocols import DataSourceProtocol
from ryandata_address_utils.validation.base import BaseValidator


class ZipCodeValidator(BaseValidator):
    """Validator for ZIP codes.

    Validates that ZIP codes exist in the data source and
    optionally match the expected state.
    """

    def __init__(
        self,
        data_source: DataSourceProtocol,
        check_state_match: bool = False,
    ) -> None:
        """Initialize ZIP code validator.

        Args:
            data_source: Data source for ZIP code lookups.
            check_state_match: If True, verify ZIP matches state.
        """
        self._data_source = data_source
        self._check_state_match = check_state_match

    @property
    def name(self) -> str:
        """Name of this validator."""
        return "zip_code"

    def validate(self, address: Address) -> ValidationResult:
        """Validate the ZIP code in an address.

        Args:
            address: Address to validate.

        Returns:
            ValidationResult with any ZIP code errors.
        """
        result = ValidationResult(is_valid=True)

        if address.ZipCodeFull is None and address.ZipCode5 is None:
            # No ZIP code to validate
            return result

        # Prefer ZipCode5 for lookup
        zip_clean = (address.ZipCode5 or "").strip()
        if not zip_clean and address.ZipCodeFull:
            zip_clean = address.ZipCodeFull.split("-")[0].strip()

        # Check if ZIP exists
        zip_info = self._data_source.get_zip_info(zip_clean)
        if zip_info is None:
            result.add_error(
                field="ZipCode",
                message=f"Invalid US ZIP code: {address.ZipCodeFull or address.ZipCode}",
                value=address.ZipCodeFull or address.ZipCode,
            )
            return result

        # Optionally check state match
        if self._check_state_match and address.StateName is not None:
            normalized_state = self._data_source.normalize_state(address.StateName)
            if normalized_state and normalized_state != zip_info.state_id:
                result.add_error(
                    field="ZipCode",
                    message=(
                        "ZIP code "
                        f"{address.ZipCodeFull or address.ZipCode} "
                        f"is in {zip_info.state_id}, not {normalized_state}"
                    ),
                    value=address.ZipCodeFull or address.ZipCode,
                )

        return result


class StateValidator(BaseValidator):
    """Validator for state names and abbreviations.

    Validates that state values are valid US states.
    """

    def __init__(self, data_source: DataSourceProtocol) -> None:
        """Initialize state validator.

        Args:
            data_source: Data source for state validation.
        """
        self._data_source = data_source

    @property
    def name(self) -> str:
        """Name of this validator."""
        return "state"

    def validate(self, address: Address) -> ValidationResult:
        """Validate the state in an address.

        Args:
            address: Address to validate.

        Returns:
            ValidationResult with any state errors.
        """
        result = ValidationResult(is_valid=True)

        if address.StateName is None:
            # No state to validate
            return result

        if not self._data_source.is_valid_state(address.StateName):
            result.add_error(
                field="StateName",
                message=f"Invalid US state: {address.StateName}",
                value=address.StateName,
            )

        return result


class CompositeValidator(BaseValidator):
    """Validator that combines multiple validators.

    Runs all validators and aggregates their results.
    """

    def __init__(self, validators: list[BaseValidator]) -> None:
        """Initialize composite validator.

        Args:
            validators: List of validators to run.
        """
        self._validators = validators

    @property
    def name(self) -> str:
        """Name of this validator."""
        return "composite"

    def validate(self, address: Address) -> ValidationResult:
        """Run all validators and combine results.

        Args:
            address: Address to validate.

        Returns:
            Combined ValidationResult from all validators.
        """
        result = ValidationResult(is_valid=True)

        for validator in self._validators:
            validator_result = validator.validate(address)
            result.merge(validator_result)

        return result

    def add_validator(self, validator: BaseValidator) -> None:
        """Add a validator to the composite.

        Args:
            validator: Validator to add.
        """
        self._validators.append(validator)

    def remove_validator(self, name: str) -> bool:
        """Remove a validator by name.

        Args:
            name: Name of the validator to remove.

        Returns:
            True if a validator was removed, False otherwise.
        """
        for i, v in enumerate(self._validators):
            if v.name == name:
                self._validators.pop(i)
                return True
        return False

    @property
    def validators(self) -> list[BaseValidator]:
        """Get list of validators."""
        return self._validators.copy()


def create_default_validators(
    data_source: DataSourceProtocol,
    check_state_match: bool = False,
) -> CompositeValidator:
    """Create default set of validators.

    Args:
        data_source: Data source for validation lookups.
        check_state_match: If True, verify ZIP matches state.

    Returns:
        CompositeValidator with default validators configured.
    """
    return CompositeValidator(
        [
            ZipCodeValidator(data_source, check_state_match=check_state_match),
            StateValidator(data_source),
        ]
    )


# -----------------------------------------------------------------------------
# Component-level validation functions for partial validation
# -----------------------------------------------------------------------------


def validate_zip5(zip_code: str | None) -> tuple[str | None, str | None]:
    """Validate a 5-digit ZIP code.

    Args:
        zip_code: The ZIP code string to validate.

    Returns:
        Tuple of (cleaned_value, error_message).
        cleaned_value is None if invalid.
        error_message is None if valid.
    """
    if not zip_code or not isinstance(zip_code, str):
        return None, "Missing or invalid zip code"

    cleaned = zip_code.strip()
    if len(cleaned) == 5 and cleaned.isdigit():
        return cleaned, None
    else:
        return None, f"Invalid zip5 format: {zip_code}"


def validate_zip4(zip4: str | None) -> tuple[str | None, str | None]:
    """Validate a 4-digit ZIP+4 extension.

    Args:
        zip4: The ZIP+4 extension string to validate.

    Returns:
        Tuple of (cleaned_value, error_message).
        cleaned_value is None if invalid or empty.
        error_message is None if valid or if zip4 is empty (zip4 is optional).
    """
    if not zip4:  # Zip4 is optional - empty is valid
        return None, None

    if isinstance(zip4, str):
        cleaned = zip4.strip()
        if len(cleaned) == 4 and cleaned.isdigit():
            return cleaned, None

    return None, f"Invalid zip4 format: {zip4}"
