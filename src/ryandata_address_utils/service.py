from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

from ryandata_address_utils.data import DataSourceFactory
from ryandata_address_utils.models import (
    ADDRESS_FIELDS,
    PACKAGE_NAME,
    Address,
    InternationalAddress,
    ParseResult,
    RyanDataAddressError,
    ValidationResult,
    ZipInfo,
)
from ryandata_address_utils.parsers import ParserFactory
from ryandata_address_utils.validation.validators import create_default_validators

# Optional libpostal import for international parsing
try:
    from postal.parser import parse_address as lp_parse_address
except ImportError:
    lp_parse_address = None


def _is_probably_international(address_string: str) -> bool:
    """Lightweight heuristic to detect likely international addresses."""

    lower = address_string.lower()
    intl_keywords = [
        # Countries / regions
        "united kingdom",
        "uk",
        "england",
        "scotland",
        "wales",
        "ireland",
        "germany",
        "france",
        "japan",
        "россия",
        "russia",
        "india",
        "australia",
        "brazil",
        "canada",
        "mexico",
        "spain",
        "italy",
        "netherlands",
        "belgium",
        "switzerland",
        "sweden",
        "norway",
        "denmark",
        "finland",
        "united arab emirates",
        "uae",
        # Major non-us cities (helps steer ambiguous inputs)
        "london",
        "tokyo",
        "berlin",
        "paris",
        "dubai",
        "abu dhabi",
    ]

    if any(keyword in lower for keyword in intl_keywords) and (
        "united states" not in lower and "usa" not in lower
    ):
        return True

    # APO/FPO/DPO military or diplomatic addresses should bypass US parsing
    if any(token in lower for token in ("apo", "fpo", "dpo", "psc")):
        return True

    return bool(any(ord(ch) > 127 for ch in address_string))


def _international_to_address(intl: InternationalAddress) -> Address:
    """Convert an InternationalAddress into an Address schema for consumers expecting Address."""

    data: dict[str, Optional[str]] = {
        "AddressNumber": intl.HouseNumber,
        "StreetName": intl.Road,
        "PlaceName": intl.City,
        "StateName": intl.State,
        "RawInput": intl.RawInput,
        "IsInternational": True,
    }
    return Address.model_validate(data)


if TYPE_CHECKING:
    import pandas as pd

    from ryandata_address_utils.protocols import (
        AddressParserProtocol,
        DataSourceProtocol,
        ValidatorProtocol,
    )


class AddressService:
    """High-level facade for address parsing operations.

    Orchestrates parsers, validators, and data sources to provide
    a simple API for common address parsing tasks.

    Example:
        >>> service = AddressService()
        >>> result = service.parse("123 Main St, Austin TX 78749")
        >>> print(result.address.StreetName)  # "Main"

        # Without validation
        >>> result = service.parse("123 Main St", validate=False)

        # Custom components
        >>> from ryandata_address_utils.data import CSVDataSource
        >>> service = AddressService(data_source=CSVDataSource("/path/to/zips.csv"))
    """

    def __init__(
        self,
        parser: Optional[AddressParserProtocol] = None,
        data_source: Optional[DataSourceProtocol] = None,
        validator: Optional[ValidatorProtocol] = None,
        check_state_match: bool = False,
    ) -> None:
        """Initialize the address service.

        Args:
            parser: Parser implementation. Defaults to USAddressParser.
            data_source: Data source for validation. Defaults to CSVDataSource.
            validator: Validator implementation. Defaults to composite validator.
            check_state_match: If True, verify ZIP matches state during validation.
        """
        self._parser = parser or ParserFactory.create()
        self._data_source = data_source or DataSourceFactory.create()

        if validator is not None:
            self._validator = validator
        else:
            self._validator = create_default_validators(
                self._data_source,
                check_state_match=check_state_match,
            )

    @property
    def parser(self) -> AddressParserProtocol:
        """Get the parser instance."""
        return self._parser

    @property
    def data_source(self) -> DataSourceProtocol:
        """Get the data source instance."""
        return self._data_source

    @property
    def validator(self) -> ValidatorProtocol:
        """Get the validator instance."""
        return self._validator

    def parse(
        self,
        address_string: str,
        *,
        validate: bool = True,
    ) -> ParseResult:
        """Parse a single address string.

        Args:
            address_string: Raw address string to parse.
            validate: If True, validate the parsed address.

        Returns:
            ParseResult containing the parsed address, validation results,
            or error information.
        """
        result = self._parser.parse(address_string)
        result.source = "us"
        result.is_international = False

        if validate and result.is_parsed and result.address is not None:
            result.validation = self._validator.validate(result.address)
            # Check for ZIP/state validation errors and raise PydanticCustomError
            result.address.validate_external_results(result.validation)

        return result

    def parse_batch(
        self,
        addresses: Sequence[str],
        *,
        validate: bool = True,
    ) -> list[ParseResult]:
        """Parse multiple address strings.

        Args:
            addresses: Sequence of raw address strings to parse.
            validate: If True, validate the parsed addresses.

        Returns:
            List of ParseResult objects.
        """
        results = self._parser.parse_batch(addresses)

        for result in results:
            result.source = "us"

        if validate:
            for result in results:
                if result.is_parsed and result.address is not None:
                    result.validation = self._validator.validate(result.address)
                    # Check for ZIP/state validation errors and raise PydanticCustomError
                    result.address.validate_external_results(result.validation)

        return results

    def parse_to_dict(
        self,
        address_string: str,
        *,
        validate: bool = True,
        errors: str = "raise",
    ) -> dict[str, Optional[str]]:
        """Parse an address and return a dictionary.

        Args:
            address_string: Raw address string to parse.
            validate: If True, validate the parsed address.
            errors: How to handle errors:
                - "raise": Raise exception on failure
                - "coerce": Return dict with None values on failure

        Returns:
            Dictionary mapping field names to values.

        Raises:
            PydanticCustomError: If parsing fails and errors="raise".
        """
        result = self.parse(address_string, validate=validate)

        if not result.is_valid:
            if errors == "raise":
                if result.error:
                    raise result.error
                if result.validation and not result.validation.is_valid:
                    # Re-raise the first validation error if it's a PydanticCustomError
                    # This is already raised in parse() via validate_external_results()
                    error_msgs = [e.message for e in result.validation.errors]
                    raise RyanDataAddressError(
                        "validation_error",
                        f"Validation failed: {'; '.join(error_msgs)}",
                        {"package": PACKAGE_NAME},
                    )
            return {f: None for f in ADDRESS_FIELDS}

        return result.to_dict()

    def lookup_zip(self, zip_code: str) -> Optional[ZipInfo]:
        """Look up information about a ZIP code.

        Args:
            zip_code: US ZIP code (5 digits or ZIP+4).

        Returns:
            ZipInfo if found, None otherwise.
        """
        return self._data_source.get_zip_info(zip_code)

    def get_city_state_from_zip(self, zip_code: str) -> Optional[tuple[str, str]]:
        """Look up city and state from a ZIP code.

        Args:
            zip_code: US ZIP code (5 digits or ZIP+4).

        Returns:
            Tuple of (city, state_abbreviation) or None if not found.
        """
        info = self.lookup_zip(zip_code)
        if info:
            return (info.city, info.state_id)
        return None

    def is_valid_zip(self, zip_code: str) -> bool:
        """Check if a ZIP code is valid.

        Args:
            zip_code: US ZIP code to check.

        Returns:
            True if valid, False otherwise.
        """
        return self._data_source.is_valid_zip(zip_code)

    def is_valid_state(self, state: str) -> bool:
        """Check if a state name or abbreviation is valid.

        Args:
            state: State name or abbreviation.

        Returns:
            True if valid, False otherwise.
        """
        return self._data_source.is_valid_state(state)

    def normalize_state(self, state: str) -> Optional[str]:
        """Normalize a state name to its abbreviation.

        Args:
            state: State name or abbreviation.

        Returns:
            Two-letter state abbreviation if valid, None otherwise.
        """
        return self._data_source.normalize_state(state)

    # -------------------------------------------------------------------------
    # International / libpostal parsing
    # -------------------------------------------------------------------------

    def parse_international(self, address_string: str) -> ParseResult:
        """Parse an address using libpostal if available."""
        if lp_parse_address is None:
            return ParseResult(
                raw_input=address_string,
                error=RuntimeError("libpostal not available"),
                address=None,
                international_address=None,
                validation=ValidationResult(is_valid=False, errors=[]),
                source="international",
            is_international=True,
            )

        try:
            parsed_tokens = lp_parse_address(address_string)
            # Convert list of (value, label) tuples into a dict of lists to preserve duplicates
            components: dict[str, list[str]] = {}
            for value, label in parsed_tokens:
                components.setdefault(label, []).append(value)

            intl_address = InternationalAddress.from_libpostal(address_string, components)
            addr_from_intl = _international_to_address(intl_address)
            return ParseResult(
                raw_input=address_string,
                address=addr_from_intl,
                international_address=intl_address,
                error=None,
                validation=ValidationResult(is_valid=True),
                source="international",
            is_international=True,
            )
        except Exception as e:  # pragma: no cover
            return ParseResult(
                raw_input=address_string,
                error=e,
                address=None,
                international_address=None,
                validation=ValidationResult(is_valid=False, errors=[]),
                source="international",
            is_international=True,
            )

    def parse_auto_route(self, address_string: str, *, validate: bool = True) -> ParseResult:
        """Try US parse first; if invalid or fails and libpostal is available, fall back."""
        # If clearly international, skip US path
        if _is_probably_international(address_string) and lp_parse_address is not None:
            return self.parse_international(address_string)

        try:
            us_result = self.parse(address_string, validate=validate)
        except Exception as exc:
            if lp_parse_address is not None:
                intl_result = self.parse_international(address_string)
                if intl_result.is_valid or intl_result.international_address is not None:
                    intl_result.is_international = True
                    return intl_result
            # Return error as a ParseResult to avoid raising in auto route
            return ParseResult(
                raw_input=address_string,
                address=None,
                international_address=None,
                error=exc,
                validation=ValidationResult(is_valid=False, errors=[]),
                source="us",
                is_international=False,
            )

        if us_result.is_valid:
            return us_result

        if lp_parse_address is None:
            return us_result

        intl_result = self.parse_international(address_string)
        intl_result.is_international = True
        return intl_result

    # -------------------------------------------------------------------------
    # Pandas integration methods
    # -------------------------------------------------------------------------

    def to_series(
        self,
        address_string: str,
        *,
        validate: bool = True,
        errors: str = "coerce",
    ) -> pd.Series:
        """Parse an address and return a pandas Series.

        Args:
            address_string: Raw address string to parse.
            validate: If True, validate the parsed address.
            errors: How to handle errors ("raise" or "coerce").

        Returns:
            Series with address components as index.
        """
        import pandas as pd

        try:
            result = self.parse(address_string, validate=validate)

            if result.is_valid:
                return pd.Series(result.to_dict())
            elif errors == "raise":
                if result.error:
                    raise result.error
                raise RyanDataAddressError(
                    "validation_error",
                    "Validation failed",
                    {"package": PACKAGE_NAME},
                )
            else:
                return pd.Series({field: None for field in ADDRESS_FIELDS})
        except Exception:
            if errors == "raise":
                raise
            else:
                return pd.Series({field: None for field in ADDRESS_FIELDS})

    def parse_dataframe(
        self,
        df: pd.DataFrame,
        address_column: str,
        *,
        validate: bool = True,
        errors: str = "coerce",
        prefix: str = "",
        inplace: bool = False,
    ) -> pd.DataFrame:
        """Parse addresses in a DataFrame.

        Args:
            df: Input DataFrame.
            address_column: Name of column containing addresses.
            validate: If True, validate parsed addresses.
            errors: "coerce" (None for failures) or "raise".
            prefix: Prefix for new column names.
            inplace: If True, modify df in place.

        Returns:
            DataFrame with new address component columns.
        """
        import pandas as pd

        if not inplace:
            df = df.copy()

        # Parse all addresses
        parsed = df[address_column].apply(
            lambda x: self.to_series(x, validate=validate, errors=errors)
            if pd.notna(x) and x
            else pd.Series({field: None for field in ADDRESS_FIELDS})
        )

        # Add prefix to column names
        if prefix:
            parsed.columns = [f"{prefix}{col}" for col in parsed.columns]

        # Add columns to original DataFrame
        for col in parsed.columns:
            df[col] = parsed[col]

        return df


# Module-level convenience function
_default_service: Optional[AddressService] = None


def get_default_service() -> AddressService:
    """Get the default AddressService singleton.

    Returns:
        Shared AddressService instance with default configuration.
    """
    global _default_service
    if _default_service is None:
        _default_service = AddressService()
    return _default_service


def parse(address_string: str, *, validate: bool = True) -> ParseResult:
    """Parse an address using the default service.

    Convenience function for quick address parsing.

    Args:
        address_string: Raw address string to parse.
        validate: If True, validate the parsed address.

    Returns:
        ParseResult containing the parsed address.
    """
    return get_default_service().parse(address_string, validate=validate)
