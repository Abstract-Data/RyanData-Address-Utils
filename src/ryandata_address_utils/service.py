from __future__ import annotations

import hashlib
import os
import warnings
from collections.abc import Sequence
from typing import TYPE_CHECKING

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
from ryandata_address_utils.validation.validators import (
    create_default_validators,
    validate_zip4,
    validate_zip5,
)

# Optional libpostal import for international parsing
try:
    from postal.expand import expand_address as lp_expand_address
    from postal.parser import parse_address as lp_parse_address
except ImportError:
    lp_parse_address = None
    lp_expand_address = None

_LIBPOSTAL_WARN_ENV = "RYANDATA_LIBPOSTAL_WARN"
_libpostal_warned = False


def _maybe_warn_libpostal_missing() -> None:
    """Emit a one-time warning when libpostal is unavailable."""

    global _libpostal_warned
    if _libpostal_warned or lp_parse_address is not None:
        return

    flag = os.getenv(_LIBPOSTAL_WARN_ENV, "1").lower()
    if flag in {"0", "false", "no"}:
        _libpostal_warned = True
        return

    warnings.warn(
        (
            "libpostal not available. Run 'ryandata-address-utils-setup' to install "
            "libpostal and its data (set RYANDATA_LIBPOSTAL_WARN=0 to suppress)."
        ),
        RuntimeWarning,
        stacklevel=2,
    )
    _libpostal_warned = True


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
        "pakistan",
        "pak",
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

    normalized_full = (
        intl.NormalizedAddresses[0]
        if intl.NormalizedAddresses
        else (intl.FullAddress or intl.RawInput)
    )

    # Use components dict for direct alias mapping (Address model supports libpostal keys)
    # Join list values into strings
    data: dict[str, object] = {k: " ".join(v) for k, v in intl.Components.items()}

    # Add explicit overrides/extras
    data.update(
        {
            "RawInput": intl.RawInput,
            "IsInternational": True,
            "Country": intl.Country,
        }
    )

    addr = Address.model_validate(data)

    # Overwrite FullAddress with normalized version if available (validator overwrites it initially)
    if normalized_full:
        addr.FullAddress = normalized_full

    return addr


def _looks_like_us(address_string: str, data_source: DataSourceProtocol) -> bool:
    """Lightweight check to keep US-looking inputs on the US path."""

    lower = address_string.lower()
    if "united states" in lower or "usa" in lower:
        return True

    tokens = ["".join(ch for ch in part if ch.isalnum()).upper() for part in lower.split()]
    tokens = [t for t in tokens if t]
    for t in tokens:
        if len(t) == 5 and t.isdigit():
            return True
        if len(t) == 2 and data_source.is_valid_state(t):
            return True
        if data_source.is_valid_state(t):
            return True
    return False


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
        parser: AddressParserProtocol | None = None,
        data_source: DataSourceProtocol | None = None,
        validator: ValidatorProtocol | None = None,
        check_state_match: bool = False,
    ) -> None:
        """Initialize the address service.

        Args:
            parser: Parser implementation. Defaults to USAddressParser.
            data_source: Data source for validation. Defaults to CSVDataSource.
            validator: Validator implementation. Defaults to composite validator.
            check_state_match: If True, verify ZIP matches state during validation.
        """
        _maybe_warn_libpostal_missing()
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
        expand: bool = True,
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

        # Apply expansion and hashing if requested (and available)
        if expand and result.is_parsed and result.address is not None:
            expanded_str, addr_hash = self._expand_and_hash(address_string)
            if addr_hash:
                result.address.AddressHash = addr_hash
            if expanded_str:
                # User prefers expanded format (e.g. "Street" vs "St")
                # We update FullAddress with the libpostal expansion if available
                result.address.FullAddress = expanded_str

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

    def parse_us_only(
        self,
        address_string: str,
        *,
        validate: bool = True,
    ) -> ParseResult:
        """Explicit US-only parse (alias of parse)."""

        return self.parse(address_string, validate=validate)

    def parse_to_dict(
        self,
        address_string: str,
        *,
        validate: bool = True,
        errors: str = "raise",
    ) -> dict[str, str | None]:
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
                    from ryandata_address_utils.models import RyanDataAddressError

                    # Ensure it is a RyanDataAddressError, even if it was just passed through
                    if not isinstance(result.error, RyanDataAddressError):
                        raise RyanDataAddressError.from_validation_error(result.error)
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

    def lookup_zip(self, zip_code: str) -> ZipInfo | None:
        """Look up information about a ZIP code.

        Args:
            zip_code: US ZIP code (5 digits or ZIP+4).

        Returns:
            ZipInfo if found, None otherwise.
        """
        return self._data_source.get_zip_info(zip_code)

    def get_city_state_from_zip(self, zip_code: str) -> tuple[str, str] | None:
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

    def normalize_state(self, state: str) -> str | None:
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

    def _expand_and_hash(self, address_string: str) -> tuple[str | None, str | None]:
        """Expand address using libpostal and return expanded string + hash.

        Returns:
            Tuple of (expanded_address_string, sha256_hash).
            Values are None if libpostal is not available or fails.
        """
        if lp_expand_address is None:
            return None, None

        try:
            # expand_address returns a list of normalized variants
            expansions = lp_expand_address(address_string)
            if not expansions:
                return None, None

            # Use the first variant as canonical
            expanded_str = expansions[0]

            # Compute SHA-256 hash of the expanded string
            addr_hash = hashlib.sha256(expanded_str.encode("utf-8")).hexdigest()

            return expanded_str, addr_hash
        except Exception:
            return None, None

    def _apply_partial_validation(self, result: ParseResult) -> ParseResult:
        """Apply partial validation logic to clean optional components.

        This method validates individual address components and cleans/removes
        invalid optional components (like Zip4) while keeping the address valid.
        Required components (street, city, state, zip5) will still cause errors
        if invalid.

        Args:
            result: The ParseResult to validate and potentially clean.

        Returns:
            The same ParseResult with cleaned components and tracking info.
        """
        if not result.is_parsed or result.address is None:
            return result

        address = result.address

        # Track valid/invalid components - preserve any existing invalid_components
        valid_components: dict[str, object] = {}
        invalid_components: dict[str, dict[str, object]] = dict(result.invalid_components)

        # Validate Zip5 (required for a valid US address)
        if address.ZipCode5:
            cleaned_zip5, zip5_error = validate_zip5(address.ZipCode5)
            if zip5_error:
                invalid_components["zip5"] = {
                    "original_value": address.ZipCode5,
                    "error": zip5_error,
                }
                result.add_cleaning_operation("zip5", address.ZipCode5, zip5_error)
            else:
                valid_components["zip5"] = cleaned_zip5

        # Validate Zip4 (optional - clean if invalid, don't fail address)
        if address.ZipCode4:
            cleaned_zip4, zip4_error = validate_zip4(address.ZipCode4)
            if zip4_error:
                # Clean the invalid Zip4 - set to None
                original_zip4 = address.ZipCode4
                invalid_components["zip4"] = {
                    "original_value": original_zip4,
                    "error": zip4_error,
                }
                result.add_cleaning_operation("zip4", original_zip4, zip4_error)

                # Update the address to remove the invalid Zip4
                address.ZipCode4 = None
                # Update ZipCodeFull to only have 5-digit ZIP
                if address.ZipCode5:
                    address.ZipCodeFull = address.ZipCode5
                    address.ZipCode = address.ZipCode5
                    # Recompute FullAddress with cleaned ZIP
                    self._recompute_full_address(address)
            else:
                valid_components["zip4"] = cleaned_zip4

        # Track other components as valid (we're not cleaning them in this phase)
        if address.AddressNumber or address.StreetName:
            valid_components["street"] = address.Address1
        if address.PlaceName:
            valid_components["city"] = address.PlaceName
        if address.StateName:
            valid_components["state"] = address.StateName

        result.cleaned_components = valid_components
        result.invalid_components = invalid_components

        return result

    def _recompute_full_address(self, address: Address) -> None:
        """Recompute FullAddress after modifying ZIP components.

        Args:
            address: The Address object to update.
        """
        full_parts: list[str] = []

        if address.Address1:
            full_parts.append(address.Address1)
        if address.Address2:
            full_parts.append(address.Address2)

        city_state_zip_parts: list[str] = []
        if address.PlaceName:
            city_state_zip_parts.append(address.PlaceName)

        if address.StateName and address.ZipCodeFull:
            city_state_zip_parts.append(f"{address.StateName} {address.ZipCodeFull}")
        elif address.StateName:
            city_state_zip_parts.append(address.StateName)
        elif address.ZipCodeFull:
            city_state_zip_parts.append(address.ZipCodeFull)

        if city_state_zip_parts:
            full_parts.append(", ".join(city_state_zip_parts))

        address.FullAddress = ", ".join(full_parts)

    def parse_international(self, address_string: str, expand: bool = True) -> ParseResult:
        """Parse an address using libpostal if available."""
        if lp_parse_address is None:
            return ParseResult(
                raw_input=address_string,
                error=RuntimeError(
                    "libpostal not available. Run 'ryandata-address-utils-setup' "
                    "to install libpostal and its data."
                ),
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

            normalized_addresses: list[str] = []
            # Reuse helper or just call expand directly to keep the list?
            # parse_international needs the list for InternationalAddress.NormalizedAddresses
            # But helper only returns the first one.
            # Let's call expand manually here to preserve the list convention
            # for InternationalAddress, but calculate hash too.
            if expand and lp_expand_address is not None:
                try:
                    normalized_addresses = lp_expand_address(address_string)
                except Exception:
                    normalized_addresses = []

            intl_address = InternationalAddress.from_libpostal(
                address_string,
                components,
                normalized_addresses=normalized_addresses,
            )
            addr_from_intl = _international_to_address(intl_address)

            if expand and normalized_addresses:
                # Compute hash using the first expansion (same as _expand_and_hash)
                expanded_str = normalized_addresses[0]
                addr_hash = hashlib.sha256(expanded_str.encode("utf-8")).hexdigest()
                addr_from_intl.AddressHash = addr_hash
                # _international_to_address likely set FullAddress to normalized_full already

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

    def parse_auto(
        self,
        address_string: str,
        *,
        validate: bool = True,
        expand: bool = True,
        allow_partial: bool = False,
    ) -> ParseResult:
        """Try US parse first; if invalid or fails and libpostal is available, fall back.

        Args:
            address_string: Raw address string to parse.
            validate: If True, validate the parsed address.
            expand: If True, expand address using libpostal (if available).
            allow_partial: If True, allow partial validation where optional components
                          (like Zip4) can be cleaned/removed while keeping the address
                          valid. Invalid required components will still raise errors.

        Returns:
            ParseResult containing the parsed address, validation results,
            cleaning operations (if allow_partial=True), or error information.
        """
        # If clearly international, skip US path
        if _is_probably_international(address_string) and lp_parse_address is not None:
            return self.parse_international(address_string, expand=expand)

        # When allow_partial is True, we need to handle parsing differently
        # to catch validation errors for optional components without failing
        if allow_partial:
            return self._parse_auto_partial(
                address_string, validate=validate, expand=expand
            )

        try:
            us_result = self.parse(address_string, validate=validate, expand=expand)
        except Exception as exc:
            if _looks_like_us(address_string, self._data_source) or lp_parse_address is None:
                return ParseResult(
                    raw_input=address_string,
                    address=None,
                    international_address=None,
                    error=exc,
                    validation=ValidationResult(is_valid=False, errors=[]),
                    source="us",
                    is_international=False,
                )
            intl_result = self.parse_international(address_string, expand=expand)
            if intl_result.is_valid or intl_result.international_address is not None:
                intl_result.is_international = True
                if intl_result.address:
                    intl_result.address.IsInternational = True
                return intl_result
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

        # If the input still looks like US, return the US result even if not valid
        if _looks_like_us(address_string, self._data_source):
            us_result.is_international = False
            if us_result.address:
                us_result.address.IsInternational = False
            return us_result

        intl_result = self.parse_international(address_string, expand=expand)
        intl_result.is_international = True
        if intl_result.address:
            intl_result.address.IsInternational = True
        return intl_result

    def _parse_auto_partial(
        self,
        address_string: str,
        *,
        validate: bool = True,
        expand: bool = True,
    ) -> ParseResult:
        """Parse with partial validation - cleans optional components instead of failing.

        This internal method handles partial validation where invalid optional
        components (like Zip4) are cleaned/removed while keeping the address valid.
        Only required component failures (street, city, state, zip5) raise errors.

        Args:
            address_string: Raw address string to parse.
            validate: If True, validate the parsed address.
            expand: If True, expand address using libpostal (if available).

        Returns:
            ParseResult with cleaned components and tracking information.
        """
        import re

        # First, try normal parsing
        result = self._parser.parse(address_string)
        result.source = "us"
        result.is_international = False

        # If parsing failed due to ZIP4 validation error, try to clean and re-parse
        if result.error is not None and result.address is None:
            error_str = str(result.error)
            if "ZipCode4" in error_str or "zip4" in error_str.lower():
                # Extract the invalid ZIP4 from the address and try again
                # Pattern matches: 5-digit ZIP followed by dash and any non-space chars
                zip_plus4_pattern = r"(\d{5})-([^\s,]+)"
                match = re.search(zip_plus4_pattern, address_string)

                if match:
                    zip5 = match.group(1)
                    invalid_zip4 = match.group(2)

                    # Create a cleaned address string with just the ZIP5
                    cleaned_address = re.sub(
                        zip_plus4_pattern,
                        zip5,
                        address_string,
                        count=1,
                    )

                    # Try parsing the cleaned address
                    result = self._parser.parse(cleaned_address)
                    result.source = "us"
                    result.is_international = False

                    # If successful, track the cleaning operation
                    if result.is_parsed and result.address is not None:
                        result.add_cleaning_operation(
                            "zip4",
                            invalid_zip4,
                            f"Invalid zip4 format: {invalid_zip4}",
                        )
                        result.invalid_components["zip4"] = {
                            "original_value": invalid_zip4,
                            "error": f"Invalid zip4 format: {invalid_zip4}",
                        }

        # If still not parsed, return the error result
        if not result.is_parsed or result.address is None:
            return result

        # Apply partial validation - clean optional components (for already parsed)
        result = self._apply_partial_validation(result)

        # Now run regular validation for required components
        if validate and result.address is not None:
            result.validation = self._validator.validate(result.address)
            # Only raise for required component errors (ZipCode lookup, StateName)
            # These are considered "required" in the sense that if provided,
            # they should be valid
            result.address.validate_external_results(result.validation)

        # Apply expansion and hashing if requested
        if expand and result.is_parsed and result.address is not None:
            expanded_str, addr_hash = self._expand_and_hash(address_string)
            if addr_hash:
                result.address.AddressHash = addr_hash
            if expanded_str:
                result.address.FullAddress = expanded_str

        return result

    def parse_auto_route(self, address_string: str, *, validate: bool = True) -> ParseResult:
        """Deprecated alias for parse_auto."""

        warnings.warn(
            "parse_auto_route is deprecated; use parse_auto instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.parse_auto(address_string, validate=validate)

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
_default_service: AddressService | None = None


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


def parse_us_only(address_string: str, *, validate: bool = True) -> ParseResult:
    """Explicit US-only parse using the default service."""

    return get_default_service().parse_us_only(address_string, validate=validate)


def parse_auto(
    address_string: str,
    *,
    validate: bool = True,
    allow_partial: bool = False,
) -> ParseResult:
    """Auto route: try US, then libpostal.

    Args:
        address_string: Raw address string to parse.
        validate: If True, validate the parsed address.
        allow_partial: If True, allow partial validation where optional components
                      (like Zip4) can be cleaned/removed while keeping the address
                      valid. Invalid required components will still raise errors.

    Returns:
        ParseResult containing the parsed address, validation results,
        cleaning operations (if allow_partial=True), or error information.
    """
    return get_default_service().parse_auto(
        address_string, validate=validate, allow_partial=allow_partial
    )


def parse_auto_route(address_string: str, *, validate: bool = True) -> ParseResult:
    """Deprecated alias for parse_auto."""

    warnings.warn(
        "parse_auto_route is deprecated; use parse_auto instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return parse_auto(address_string, validate=validate)
