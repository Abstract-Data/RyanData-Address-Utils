"""jre-addr-parse: A Python address parser with validation and extensibility.

This package provides a production-ready address parsing system with:
- Extensible parser backends (default: usaddress)
- Pluggable data sources for ZIP/state validation
- Composable validators
- Pandas integration
- Builder pattern for programmatic address construction

Quick Start:
    >>> from ryandata_address_utils import AddressService
    >>> service = AddressService()
    >>> result = service.parse("123 Main St, Austin TX 78749")
    >>> print(result.address.StreetName)  # "Main"

    # Check validity
    >>> if result.is_valid:
    ...     print(result.address.ZipCode)
    ... else:
    ...     print(result.validation.errors)

    # Pandas integration
    >>> import pandas as pd
    >>> df = pd.DataFrame({"address": ["123 Main St, Austin TX 78749"]})
    >>> result_df = service.parse_dataframe(df, "address")

    # Build addresses programmatically
    >>> from ryandata_address_utils import AddressBuilder
    >>> address = (
    ...     AddressBuilder()
    ...     .with_street_number("123")
    ...     .with_street_name("Main")
    ...     .with_street_type("St")
    ...     .with_city("Austin")
    ...     .with_state("TX")
    ...     .with_zip("78749")
    ...     .build()
    ... )
"""

from __future__ import annotations

# Imports grouped by type and sorted
from ryandata_address_utils.data import (
    BaseDataSource,
    CSVDataSource,
    DataSourceFactory,
    get_zip_info,
    is_valid_state,
    is_valid_zip,
    normalize_state,
)
from ryandata_address_utils.models import (
    ADDRESS_FIELDS,
    Address,
    AddressBuilder,
    AddressField,
    ParseResult,
    ValidationError,
    ValidationResult,
    ZipInfo,
)
from ryandata_address_utils.pandas_ext import (
    parse_address_series,
    parse_address_to_dict,
    parse_addresses,
    register_accessor,
)
from ryandata_address_utils.parsers import BaseAddressParser, ParserFactory, USAddressParser
from ryandata_address_utils.protocols import (
    AddressParserProtocol,
    DataSourceProtocol,
    ValidatorProtocol,
)
from ryandata_address_utils.service import AddressService, get_default_service, parse
from ryandata_address_utils.validation import (
    BaseValidator,
    CompositeValidator,
    StateValidator,
    ZipCodeValidator,
)

__version__ = "0.2.0"
__package_name__ = "ryandata-address-utils"

__all__ = [
    # Version
    "__version__",
    # Primary interface
    "AddressService",
    "get_default_service",
    "parse",
    # Models
    "Address",
    "AddressBuilder",
    "AddressField",
    "ADDRESS_FIELDS",
    "ParseResult",
    "ValidationError",
    "ValidationResult",
    "ZipInfo",
    # Protocols
    "AddressParserProtocol",
    "DataSourceProtocol",
    "ValidatorProtocol",
    # Parsers
    "BaseAddressParser",
    "ParserFactory",
    "USAddressParser",
    # Data sources
    "BaseDataSource",
    "CSVDataSource",
    "DataSourceFactory",
    # Validators
    "BaseValidator",
    "CompositeValidator",
    "StateValidator",
    "ZipCodeValidator",
    # Convenience functions
    "get_zip_info",
    "is_valid_zip",
    "is_valid_state",
    "normalize_state",
    # Pandas integration
    "parse_addresses",
    "parse_address_series",
    "parse_address_to_dict",
    "register_accessor",
]


def get_city_state_from_zip(zip_code: str) -> tuple[str, str] | None:
    """Look up city and state from a ZIP code.

    Args:
        zip_code: US ZIP code (5 digits or ZIP+4).

    Returns:
        Tuple of (city, state_abbreviation) or None if not found.
    """
    return get_default_service().get_city_state_from_zip(zip_code)


def main() -> None:
    """CLI entry point for testing."""
    test_address = "123 Main St, Unit 11, Austin Texas 78749"
    print(f"Parsing: {test_address}")

    result = parse(test_address)
    if result.is_valid:
        print(f"Result: {result.to_dict()}")
    else:
        print(f"Error: {result.error or result.validation}")
