from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache

from ryandata_address_utils.models import ZipInfo


class BaseDataSource(ABC):
    """Abstract base class for ZIP code and state data sources.

    Provides common caching logic and defines the interface that
    all data source implementations must follow.
    """

    def __init__(self, cache_size: int = 10000) -> None:
        """Initialize the data source.

        Args:
            cache_size: Maximum number of ZIP lookups to cache.
        """
        self._cache_size = cache_size
        self._setup_cache()

    def _setup_cache(self) -> None:
        """Set up LRU cache for ZIP lookups."""
        # Create cached version of the lookup method
        self._cached_get_zip_info = lru_cache(maxsize=self._cache_size)(self._get_zip_info_impl)

    @abstractmethod
    def _load_data(self) -> None:
        """Load data from the underlying source.

        Implementations should load ZIP codes, state abbreviations,
        and state name mappings into internal data structures.
        """
        ...

    @abstractmethod
    def _get_zip_info_impl(self, zip_code: str) -> ZipInfo | None:
        """Internal implementation of ZIP info lookup.

        Args:
            zip_code: Cleaned ZIP code (5 digits).

        Returns:
            ZipInfo if found, None otherwise.
        """
        ...

    @abstractmethod
    def get_valid_state_abbrevs(self) -> set[str]:
        """Get set of valid US state abbreviations.

        Returns:
            Set of two-letter state abbreviations.
        """
        ...

    @abstractmethod
    def _get_state_name_mapping(self) -> dict[str, str]:
        """Get mapping of lowercase state names to abbreviations.

        Returns:
            Dict mapping lowercase state name to abbreviation.
        """
        ...

    def _clean_zip(self, zip_code: str) -> str:
        """Clean and normalize a ZIP code.

        Args:
            zip_code: Raw ZIP code string.

        Returns:
            Cleaned 5-digit ZIP code.
        """
        # Handle ZIP+4 format (12345-6789) and pad to 5 digits
        return zip_code.split("-")[0].strip().zfill(5)

    def get_zip_info(self, zip_code: str) -> ZipInfo | None:
        """Get information about a ZIP code.

        Args:
            zip_code: US ZIP code (5 digits or ZIP+4 format).

        Returns:
            ZipInfo if found, None otherwise.
        """
        cleaned = self._clean_zip(zip_code)
        return self._cached_get_zip_info(cleaned)

    def is_valid_zip(self, zip_code: str) -> bool:
        """Check if a ZIP code is valid.

        Args:
            zip_code: US ZIP code to validate.

        Returns:
            True if valid, False otherwise.
        """
        return self.get_zip_info(zip_code) is not None

    def normalize_state(self, state: str) -> str | None:
        """Normalize a state name to its abbreviation.

        Args:
            state: State name or abbreviation.

        Returns:
            Two-letter state abbreviation if valid, None otherwise.
        """
        state_upper = state.strip().upper()
        state_lower = state.strip().lower()

        # Check if it's already an abbreviation
        if state_upper in self.get_valid_state_abbrevs():
            return state_upper

        # Check if it's a full state name
        state_names = self._get_state_name_mapping()
        if state_lower in state_names:
            return state_names[state_lower]

        return None

    def is_valid_state(self, state: str) -> bool:
        """Check if a state name or abbreviation is valid.

        Args:
            state: State name or abbreviation.

        Returns:
            True if valid, False otherwise.
        """
        return self.normalize_state(state) is not None

    def clear_cache(self) -> None:
        """Clear the ZIP lookup cache."""
        self._cached_get_zip_info.cache_clear()
