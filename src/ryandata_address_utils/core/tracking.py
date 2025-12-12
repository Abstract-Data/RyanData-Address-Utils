"""Transformation tracking for address parsing.

Tracks normalization and cleaning operations that occur during
address parsing to provide transparency about data transformations.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from ryandata_address_utils.data.constants import STATE_NAME_TO_ABBREV

if TYPE_CHECKING:
    from ryandata_address_utils.models import ParseResult


class TransformationTracker:
    """Tracks address transformations that occur during parsing.

    This class encapsulates the logic for detecting and recording
    silent cleaning/normalization operations that transform raw input
    into normalized address components.
    """

    # Use centralized state name mapping from constants
    STATE_NAMES: dict[str, str] = STATE_NAME_TO_ABBREV

    def track_all(self, result: ParseResult, raw_input: str) -> None:
        """Track all address transformations that occurred during parsing.

        This method detects and records all silent cleaning operations that
        transform the raw input into a normalized address.

        Args:
            result: The ParseResult to add cleaning operations to.
            raw_input: The original raw address string.
        """
        if not result.is_parsed or result.address is None:
            return

        self.track_zip_normalization(result, raw_input)
        self.track_state_normalization(result, raw_input)
        self.track_whitespace_normalization(result, raw_input)
        self.track_comma_normalization(result, raw_input)

    def track_zip_normalization(self, result: ParseResult, raw_input: str) -> None:
        """Detect and track ZIP code normalization transformations.

        Args:
            result: The ParseResult to add cleaning operations to.
            raw_input: The original raw address string.
        """
        if result.address is None:
            return

        address = result.address

        # Try to extract ZIP from raw input using various patterns
        # Pattern 1: ZIP+4 with dash (12345-6789)
        # Pattern 2: 9-digit ZIP without dash (123456789)
        # Pattern 3: 5-digit ZIP (12345)
        zip_patterns = [
            r"\b(\d{5})-(\d{4})\b",  # ZIP+4 with dash
            r"\b(\d{5})(\d{4})\b",  # 9-digit continuous
            r"\b(\d{5})\b",  # 5-digit ZIP
        ]

        raw_zip5 = None
        raw_zip4 = None
        raw_zip_full = None

        for pattern in zip_patterns:
            match = re.search(pattern, raw_input)
            if match:
                if len(match.groups()) == 2:
                    raw_zip5, raw_zip4 = match.groups()
                    # Check if it was continuous 9-digit (no dash in original)
                    if "-" not in match.group(0):
                        raw_zip_full = raw_zip5 + raw_zip4  # continuous format
                    else:
                        raw_zip_full = f"{raw_zip5}-{raw_zip4}"
                else:
                    raw_zip5 = match.group(1)
                    raw_zip_full = raw_zip5
                break

        if raw_zip5 is None:
            return

        # Track ZIP5 normalization (leading zeros added)
        if address.ZipCode5 and raw_zip5 and raw_zip5 != address.ZipCode5:
            result.add_process_cleaning(
                field="zip5",
                original_value=raw_zip5,
                reason="ZIP5 normalized (leading zeros or format change)",
                new_value=address.ZipCode5,
                operation_type="normalization",
            )

        # Track ZIP format normalization (9-digit continuous -> 5-4 format)
        # Check if format changed (e.g., 123456789 -> 12345-6789)
        if (
            raw_zip_full
            and address.ZipCodeFull
            and raw_zip_full != address.ZipCodeFull
            and raw_zip4
            and "-" not in raw_zip_full
            and "-" in (address.ZipCodeFull or "")
        ):
            result.add_process_cleaning(
                field="zip_format",
                original_value=raw_zip_full,
                reason="ZIP format normalized from continuous to hyphenated format",
                new_value=address.ZipCodeFull,
                operation_type="normalization",
            )

    def track_state_normalization(self, result: ParseResult, raw_input: str) -> None:
        """Detect and track state name normalization transformations.

        Args:
            result: The ParseResult to add cleaning operations to.
            raw_input: The original raw address string.
        """
        if result.address is None:
            return

        address = result.address
        if not address.StateName:
            return

        raw_lower = raw_input.lower()

        # Look for full state names in the raw input
        for full_name, abbrev in self.STATE_NAMES.items():
            # Check if the parsed state is the abbreviation
            if full_name in raw_lower and address.StateName.upper() == abbrev:
                result.add_process_cleaning(
                    field="state",
                    original_value=full_name.title(),
                    reason="State name normalized from full name to abbreviation",
                    new_value=abbrev,
                    operation_type="normalization",
                )
                return

        # Check for case normalization (e.g., "tx" -> "TX")
        # Try to find state abbreviation in raw input with different casing
        state_pattern = rf"\b({address.StateName})\b"
        match = re.search(state_pattern, raw_input, re.IGNORECASE)
        if match:
            raw_state = match.group(1)
            if raw_state != address.StateName:
                result.add_process_cleaning(
                    field="state",
                    original_value=raw_state,
                    reason="State abbreviation case normalized",
                    new_value=address.StateName,
                    operation_type="formatting",
                )

    def track_whitespace_normalization(self, result: ParseResult, raw_input: str) -> None:
        """Detect and track whitespace normalization transformations.

        Args:
            result: The ParseResult to add cleaning operations to.
            raw_input: The original raw address string.
        """
        # Check if the raw input had leading/trailing whitespace
        stripped = raw_input.strip()
        if stripped != raw_input:
            result.add_process_cleaning(
                field="raw_input",
                original_value=raw_input,
                reason="Leading/trailing whitespace removed",
                new_value=stripped,
                operation_type="formatting",
            )

        # Check for multiple consecutive spaces that were normalized
        if re.search(r"  +", raw_input):
            result.add_process_cleaning(
                field="raw_input",
                original_value=None,
                reason="Multiple consecutive spaces normalized to single space",
                new_value=None,
                operation_type="formatting",
            )

    def track_comma_normalization(self, result: ParseResult, raw_input: str) -> None:
        """Detect and track comma normalization from address components.

        The parser strips trailing commas from parsed tokens. This method
        detects when commas were present in component positions and records
        the cleaning operation.

        Args:
            result: The ParseResult to add cleaning operations to.
            raw_input: The original raw address string.
        """
        if result.address is None:
            return

        address = result.address

        # Check street name - if raw input had "Main St," but we have "Main St"
        if address.StreetName:
            street_pattern = rf"\b{re.escape(address.StreetName)}\s*,"
            if re.search(street_pattern, raw_input, re.IGNORECASE):
                result.add_process_cleaning(
                    field="street_name",
                    original_value=f"{address.StreetName},",
                    reason="Trailing comma removed from street name component",
                    new_value=address.StreetName,
                    operation_type="formatting",
                )

        # Check city name - similar pattern
        if address.PlaceName:
            city_pattern = rf"\b{re.escape(address.PlaceName)}\s*,"
            match = re.search(city_pattern, raw_input, re.IGNORECASE)
            if match:
                result.add_process_cleaning(
                    field="city",
                    original_value=f"{address.PlaceName},",
                    reason="Trailing comma removed from city component",
                    new_value=address.PlaceName,
                    operation_type="formatting",
                )
