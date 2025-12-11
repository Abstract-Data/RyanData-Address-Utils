"""Data sources for ZIP code and state validation.

This module provides data source implementations and utilities
for geographic validation data.
"""

from __future__ import annotations

from ryandata_address_utils.data.base import BaseDataSource
from ryandata_address_utils.data.csv_source import CSVDataSource, get_default_csv_source
from ryandata_address_utils.data.factory import DataSourceFactory
from ryandata_address_utils.models import ZipInfo

__all__ = [
    "BaseDataSource",
    "CSVDataSource",
    "DataSourceFactory",
    "ZipInfo",
    "get_default_csv_source",
    # Backwards compatibility functions
    "get_zip_info",
    "is_valid_zip",
    "is_valid_state",
    "normalize_state",
    "get_valid_state_abbrevs",
]


# Backwards compatibility functions using default CSV source
def get_zip_info(zip_code: str) -> ZipInfo | None:
    """Get information about a ZIP code.

    Args:
        zip_code: US ZIP code (5 digits or ZIP+4 format).

    Returns:
        ZipInfo if found, None otherwise.
    """
    return get_default_csv_source().get_zip_info(zip_code)


def is_valid_zip(zip_code: str) -> bool:
    """Check if a ZIP code is valid.

    Args:
        zip_code: US ZIP code to validate.

    Returns:
        True if valid, False otherwise.
    """
    return get_default_csv_source().is_valid_zip(zip_code)


def is_valid_state(state: str) -> bool:
    """Check if a state name or abbreviation is valid.

    Args:
        state: State name or abbreviation.

    Returns:
        True if valid, False otherwise.
    """
    return get_default_csv_source().is_valid_state(state)


def normalize_state(state: str) -> str | None:
    """Normalize a state name to its abbreviation.

    Args:
        state: State name or abbreviation.

    Returns:
        Two-letter state abbreviation if valid, None otherwise.
    """
    return get_default_csv_source().normalize_state(state)


def get_valid_state_abbrevs() -> set[str]:
    """Get set of valid US state abbreviations.

    Returns:
        Set of two-letter state abbreviations.
    """
    return get_default_csv_source().get_valid_state_abbrevs()
