from __future__ import annotations

from typing import TYPE_CHECKING

from abstract_validation_base import (
    BaseValidator,
    CompositeValidator,
    ValidationResult,
    ValidatorPipelineBuilder,
)

from ryandata_address_utils.core.zip_normalizer import ZipCodeNormalizer
from ryandata_address_utils.protocols import DataSourceProtocol

if TYPE_CHECKING:
    from ryandata_address_utils.models import Address


class Zip5FormatValidator(BaseValidator["Address"]):
    """Validates ZIP5 format (5 digits).

    This is a fast format validator that doesn't require
    external lookups - it only checks the format is correct.
    """

    @property
    def name(self) -> str:
        """Name of this validator."""
        return "zip5_format"

    def validate(self, address: Address) -> ValidationResult:
        """Validate the ZIP5 format.

        Args:
            address: Address to validate.

        Returns:
            ValidationResult with any format errors.
        """
        result = ValidationResult(is_valid=True)
        if address.ZipCode5:
            cleaned, error = validate_zip5(address.ZipCode5)
            if error:
                result.add_error("ZipCode5", error, address.ZipCode5)
        return result


class Zip4FormatValidator(BaseValidator["Address"]):
    """Validates ZIP4 extension format (4 digits).

    This is a fast format validator that doesn't require
    external lookups - it only checks the format is correct.
    """

    @property
    def name(self) -> str:
        """Name of this validator."""
        return "zip4_format"

    def validate(self, address: Address) -> ValidationResult:
        """Validate the ZIP4 format.

        Args:
            address: Address to validate.

        Returns:
            ValidationResult with any format errors.
        """
        result = ValidationResult(is_valid=True)
        if address.ZipCode4:
            cleaned, error = validate_zip4(address.ZipCode4)
            if error:
                result.add_error("ZipCode4", error, address.ZipCode4)
        return result


class ZipCodeValidator(BaseValidator["Address"]):
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


class StateValidator(BaseValidator["Address"]):
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


def create_default_validators(
    data_source: DataSourceProtocol,
    check_state_match: bool = False,
    include_format_validators: bool = True,
) -> CompositeValidator[Address]:
    """Create default address validation pipeline.

    Uses ValidatorPipelineBuilder to construct a composable
    validation pipeline with format and lookup validators.

    Args:
        data_source: Data source for validation lookups.
        check_state_match: If True, verify ZIP matches state.
        include_format_validators: If True, include Zip5/Zip4 format validators.

    Returns:
        CompositeValidator with default validators configured.
    """
    builder: ValidatorPipelineBuilder[Address] = ValidatorPipelineBuilder("address_validation")

    # Format validators (fast, no external lookups)
    if include_format_validators:
        builder.add(Zip5FormatValidator())
        builder.add(Zip4FormatValidator())

    # Lookup validators (require data source)
    builder.add(ZipCodeValidator(data_source, check_state_match=check_state_match))
    builder.add(StateValidator(data_source))

    return builder.build()


# -----------------------------------------------------------------------------
# Component-level validation functions for partial validation
# -----------------------------------------------------------------------------

# Module-level normalizer instance for validation functions
_zip_normalizer = ZipCodeNormalizer()


def validate_zip5(zip_code: str | None) -> tuple[str | None, str | None]:
    """Validate a 5-digit ZIP code.

    Delegates to ZipCodeNormalizer.validate_zip5() for consistent validation.

    Args:
        zip_code: The ZIP code string to validate.

    Returns:
        Tuple of (cleaned_value, error_message).
        cleaned_value is None if invalid.
        error_message is None if valid.
    """
    return _zip_normalizer.validate_zip5(zip_code)


def validate_zip4(zip4: str | None) -> tuple[str | None, str | None]:
    """Validate a 4-digit ZIP+4 extension.

    Delegates to ZipCodeNormalizer.validate_zip4() for consistent validation.

    Args:
        zip4: The ZIP+4 extension string to validate.

    Returns:
        Tuple of (cleaned_value, error_message).
        cleaned_value is None if invalid or empty.
        error_message is None if valid or if zip4 is empty (zip4 is optional).
    """
    return _zip_normalizer.validate_zip4(zip4)
