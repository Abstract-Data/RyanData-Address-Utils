from __future__ import annotations

import csv
from collections.abc import Iterator
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Union

from ryandata_address_utils.data.base import BaseDataSource
from ryandata_address_utils.data.constants import ALL_NAME_TO_ABBREV
from ryandata_address_utils.models import ZipInfo


class CSVDataSource(BaseDataSource):
    """Data source that loads from a CSV file.

    By default, loads from the bundled uszips.csv file, but can be
    configured to load from a custom file path.
    """

    def __init__(
        self,
        csv_path: Union[str, Path] | None = None,
        cache_size: int = 10000,
    ) -> None:
        """Initialize CSV data source.

        Args:
            csv_path: Path to CSV file. If None, uses bundled uszips.csv.
            cache_size: Maximum number of ZIP lookups to cache.
        """
        self._csv_path = csv_path
        self._zip_lookup: dict[str, ZipInfo] = {}
        self._state_abbrevs: set[str] = set()
        self._state_names: dict[str, str] = {}  # lowercase name -> abbreviation
        self._loaded = False

        super().__init__(cache_size=cache_size)

    def _get_csv_path(self) -> Path:
        """Get the path to the CSV file.

        Returns:
            Path to the CSV file.
        """
        if self._csv_path:
            return Path(self._csv_path)

        # Use bundled CSV file
        data_file = resources.files("ryandata_address_utils.data").joinpath("uszips.csv")
        # Convert Traversable to Path via string representation
        return Path(str(data_file))

    def _iter_csv_rows(self) -> Iterator[dict[str, str]]:
        """Iterate over CSV rows.

        Yields:
            Dict for each row in the CSV.
        """
        csv_path = self._get_csv_path()

        # Handle both filesystem paths and importlib resources
        if self._csv_path:
            # Custom path - read directly
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                yield from reader
        else:
            # Bundled file - use importlib.resources
            data_file = resources.files("ryandata_address_utils.data").joinpath("uszips.csv")
            with data_file.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                yield from reader

    def _load_data(self) -> None:
        """Load data from the CSV file."""
        if self._loaded:
            return

        for row in self._iter_csv_rows():
            # Pad ZIP code to 5 digits (CSV may have them without leading zeros)
            zip_code = row["zip"].zfill(5)
            state_id = row["state_id"]
            state_name = row["state_name"]

            self._zip_lookup[zip_code] = ZipInfo(
                zip_code=zip_code,
                city=row["city"],
                state_id=state_id,
                state_name=state_name,
                county_name=row["county_name"],
            )

            self._state_abbrevs.add(state_id)
            self._state_names[state_name.lower()] = state_id

        self._loaded = True

    def _ensure_loaded(self) -> None:
        """Ensure data is loaded before access."""
        if not self._loaded:
            self._load_data()

    def _get_zip_info_impl(self, zip_code: str) -> ZipInfo | None:
        """Get ZIP info from the loaded data.

        Args:
            zip_code: Cleaned 5-digit ZIP code.

        Returns:
            ZipInfo if found, None otherwise.
        """
        self._ensure_loaded()
        return self._zip_lookup.get(zip_code)

    def get_valid_state_abbrevs(self) -> set[str]:
        """Get set of valid US state abbreviations.

        Returns:
            Set of two-letter state abbreviations.
        """
        self._ensure_loaded()
        return self._state_abbrevs.copy()

    def _get_state_name_mapping(self) -> dict[str, str]:
        """Get mapping of lowercase state names to abbreviations.

        Returns the centralized ALL_NAME_TO_ABBREV constant which provides
        the single source of truth for state and territory name mappings.

        Returns:
            Dict mapping lowercase state/territory name to abbreviation.
        """
        return ALL_NAME_TO_ABBREV


@lru_cache(maxsize=1)
def get_default_csv_source() -> CSVDataSource:
    """Get the default CSV data source singleton.

    Uses lru_cache to ensure only one instance is created.

    Returns:
        Shared CSVDataSource instance.
    """
    return CSVDataSource()
