from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ryandata_address_utils.models import Address, ParseResult, ValidationResult, ZipInfo


@runtime_checkable
class AddressParserProtocol(Protocol):
    """Protocol for address parsing implementations.

    Implementations should parse raw address strings into structured
    Address objects, handling errors gracefully.
    """

    def parse(self, address_string: str) -> ParseResult:
        """Parse a single address string.

        Args:
            address_string: Raw address string to parse.

        Returns:
            ParseResult containing the parsed address or error information.
        """
        ...

    def parse_batch(self, addresses: Sequence[str]) -> list[ParseResult]:
        """Parse multiple address strings.

        Args:
            addresses: Sequence of raw address strings to parse.

        Returns:
            List of ParseResult objects, one for each input address.
        """
        ...


@runtime_checkable
class DataSourceProtocol(Protocol):
    """Protocol for ZIP code and state data sources.

    Implementations provide access to geographic validation data,
    supporting different backends (CSV, database, API, etc.).
    """

    def get_zip_info(self, zip_code: str) -> ZipInfo | None:
        """Get information about a ZIP code.

        Args:
            zip_code: US ZIP code (5 digits or ZIP+4 format).

        Returns:
            ZipInfo if found, None otherwise.
        """
        ...

    def is_valid_zip(self, zip_code: str) -> bool:
        """Check if a ZIP code is valid.

        Args:
            zip_code: US ZIP code to validate.

        Returns:
            True if valid, False otherwise.
        """
        ...

    def is_valid_state(self, state: str) -> bool:
        """Check if a state name or abbreviation is valid.

        Args:
            state: State name or abbreviation.

        Returns:
            True if valid, False otherwise.
        """
        ...

    def normalize_state(self, state: str) -> str | None:
        """Normalize a state name to its abbreviation.

        Args:
            state: State name or abbreviation.

        Returns:
            Two-letter state abbreviation if valid, None otherwise.
        """
        ...

    def get_valid_state_abbrevs(self) -> set[str]:
        """Get set of valid US state abbreviations.

        Returns:
            Set of two-letter state abbreviations.
        """
        ...


@runtime_checkable
class ValidatorProtocol(Protocol):
    """Protocol for address validation implementations.

    Implementations validate specific aspects of an address
    (ZIP codes, states, etc.) and return validation results.
    """

    def validate(self, address: Address) -> ValidationResult:
        """Validate an address.

        Args:
            address: Address object to validate.

        Returns:
            ValidationResult containing validation status and any errors.
        """
        ...

    @property
    def name(self) -> str:
        """Name of this validator for error reporting."""
        ...
