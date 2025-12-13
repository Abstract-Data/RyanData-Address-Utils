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


class OperationType:
    """Standard operation type constants for consistent categorization.

    These constants provide a consistent vocabulary for describing
    the types of transformations that occur during address parsing.
    """

    NORMALIZATION = "normalization"
    """Format standardization (abbreviations, ZIP formats, etc.)"""

    FORMATTING = "formatting"
    """Whitespace, punctuation, case changes"""

    EXPANSION = "expansion"
    """Abbreviation expansion (via libpostal)"""

    CLEANING = "cleaning"
    """Removal of invalid data"""

    PARSING = "parsing"
    """Component extraction from raw input"""


# Street type mappings (full name -> standard abbreviation)
STREET_TYPE_TO_ABBREV: dict[str, str] = {
    "street": "St",
    "avenue": "Ave",
    "boulevard": "Blvd",
    "drive": "Dr",
    "road": "Rd",
    "lane": "Ln",
    "court": "Ct",
    "place": "Pl",
    "circle": "Cir",
    "way": "Way",
    "terrace": "Ter",
    "highway": "Hwy",
    "parkway": "Pkwy",
    "trail": "Trl",
    "square": "Sq",
    "expressway": "Expy",
    "freeway": "Fwy",
    "turnpike": "Tpke",
    "pike": "Pike",
    "alley": "Aly",
    "crossing": "Xing",
    "loop": "Loop",
    "run": "Run",
    "pass": "Pass",
    "ridge": "Rdg",
    "valley": "Vly",
    "view": "Vw",
    "heights": "Hts",
    "grove": "Grv",
    "park": "Park",
    "point": "Pt",
    "cove": "Cv",
    "creek": "Crk",
    "extension": "Ext",
    "garden": "Gdn",
    "gardens": "Gdns",
    "mount": "Mt",
    "mountain": "Mtn",
}

# Direction mappings (full name -> abbreviation)
DIRECTION_TO_ABBREV: dict[str, str] = {
    "north": "N",
    "south": "S",
    "east": "E",
    "west": "W",
    "northeast": "NE",
    "northwest": "NW",
    "southeast": "SE",
    "southwest": "SW",
}

# Unit type mappings (full name -> abbreviation)
UNIT_TYPE_TO_ABBREV: dict[str, str] = {
    "apartment": "Apt",
    "suite": "Ste",
    "unit": "Unit",
    "building": "Bldg",
    "floor": "Fl",
    "room": "Rm",
    "department": "Dept",
    "office": "Ofc",
    "space": "Spc",
    "lot": "Lot",
    "trailer": "Trlr",
    "penthouse": "PH",
    "basement": "Bsmt",
    "lower": "Lowr",
    "upper": "Uppr",
    "front": "Frnt",
    "rear": "Rear",
    "side": "Side",
}


class TransformationTracker:
    """Tracks address transformations that occur during parsing.

    This class encapsulates the logic for detecting and recording
    silent cleaning/normalization operations that transform raw input
    into normalized address components.

    The tracker records various types of transformations:
    - ZIP code normalization (format standardization)
    - State name/abbreviation normalization
    - Whitespace normalization
    - Comma removal from components
    - Case normalization (all caps to title case)
    - Street type standardization (Street -> St)
    - Direction abbreviation (North -> N)
    - Punctuation removal
    - Component parsing (extraction from raw input)
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

        # Core transformations (always tracked)
        self.track_zip_normalization(result, raw_input)
        self.track_state_normalization(result, raw_input)
        self.track_whitespace_normalization(result, raw_input)
        self.track_comma_normalization(result, raw_input)

        # Additional detailed transformations
        self.track_case_normalization(result, raw_input)
        self.track_street_type_changes(result, raw_input)
        self.track_direction_changes(result, raw_input)
        self.track_unit_type_changes(result, raw_input)
        self.track_punctuation_removal(result, raw_input)
        self.track_component_parsing(result, raw_input)

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
                operation_type=OperationType.NORMALIZATION,
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
                operation_type=OperationType.NORMALIZATION,
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
                    operation_type=OperationType.NORMALIZATION,
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
                    operation_type=OperationType.FORMATTING,
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
                operation_type=OperationType.FORMATTING,
            )

        # Check for multiple consecutive spaces that were normalized
        if re.search(r"  +", raw_input):
            result.add_process_cleaning(
                field="raw_input",
                original_value=None,
                reason="Multiple consecutive spaces normalized to single space",
                new_value=None,
                operation_type=OperationType.FORMATTING,
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
                    operation_type=OperationType.FORMATTING,
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
                    operation_type=OperationType.FORMATTING,
                )

    def track_case_normalization(self, result: ParseResult, raw_input: str) -> None:
        """Detect and track case normalization transformations.

        Tracks when components are converted from ALL CAPS or lowercase
        to title case or standard format.

        Args:
            result: The ParseResult to add cleaning operations to.
            raw_input: The original raw address string.
        """
        if result.address is None:
            return

        address = result.address

        # Check street name case normalization
        if address.StreetName:
            # Try to find the street name in raw input with different casing
            street_pattern = rf"\b({re.escape(address.StreetName)})\b"
            match = re.search(street_pattern, raw_input, re.IGNORECASE)
            if match:
                raw_street = match.group(1)
                # Check if case changed (e.g., "MAIN" -> "Main" or "main" -> "Main")
                case_changed = raw_street != address.StreetName
                same_text = raw_street.lower() == address.StreetName.lower()
                if case_changed and same_text:
                    result.add_process_cleaning(
                        field="street_name",
                        original_value=raw_street,
                        reason="Street name case normalized",
                        new_value=address.StreetName,
                        operation_type=OperationType.FORMATTING,
                    )

        # Check city/place name case normalization
        if address.PlaceName:
            city_pattern = rf"\b({re.escape(address.PlaceName)})\b"
            match = re.search(city_pattern, raw_input, re.IGNORECASE)
            if match:
                raw_city = match.group(1)
                if raw_city != address.PlaceName and raw_city.lower() == address.PlaceName.lower():
                    result.add_process_cleaning(
                        field="city",
                        original_value=raw_city,
                        reason="City name case normalized",
                        new_value=address.PlaceName,
                        operation_type=OperationType.FORMATTING,
                    )

    def track_street_type_changes(self, result: ParseResult, raw_input: str) -> None:
        """Detect and track street type standardization.

        Tracks when street types are abbreviated or expanded
        (e.g., "Street" -> "St", "Avenue" -> "Ave").

        Args:
            result: The ParseResult to add cleaning operations to.
            raw_input: The original raw address string.
        """
        if result.address is None:
            return

        address = result.address
        street_type = address.StreetNamePostType

        if not street_type:
            return

        raw_lower = raw_input.lower()

        # Check if full street type was in raw input but got abbreviated
        for full_name, abbrev in STREET_TYPE_TO_ABBREV.items():
            # Check if full name is in raw and parsed type matches abbreviation
            is_in_raw = full_name in raw_lower
            matches_abbrev = street_type.lower() in (abbrev.lower(), full_name)
            is_different = street_type != full_name.title()

            if is_in_raw and matches_abbrev and is_different:
                result.add_process_cleaning(
                    field="street_type",
                    original_value=full_name.title(),
                    reason=f"Street type abbreviated: {full_name.title()} -> {street_type}",
                    new_value=street_type,
                    operation_type=OperationType.NORMALIZATION,
                )
                return

        # Check for case normalization of street type (e.g., "ST" -> "St")
        if street_type:
            type_pattern = rf"\b({re.escape(street_type)})\b"
            match = re.search(type_pattern, raw_input, re.IGNORECASE)
            if match:
                raw_type = match.group(1)
                if raw_type != street_type and raw_type.lower() == street_type.lower():
                    result.add_process_cleaning(
                        field="street_type",
                        original_value=raw_type,
                        reason="Street type case normalized",
                        new_value=street_type,
                        operation_type=OperationType.FORMATTING,
                    )

    def track_direction_changes(self, result: ParseResult, raw_input: str) -> None:
        """Detect and track directional abbreviation/expansion.

        Tracks when directions are abbreviated or expanded
        (e.g., "North" -> "N", "Southeast" -> "SE").

        Args:
            result: The ParseResult to add cleaning operations to.
            raw_input: The original raw address string.
        """
        if result.address is None:
            return

        address = result.address
        raw_lower = raw_input.lower()

        # Check pre-directional
        pre_dir = address.StreetNamePreDirectional
        if pre_dir:
            self._track_direction_field(result, raw_lower, raw_input, pre_dir, "pre_directional")

        # Check post-directional
        post_dir = address.StreetNamePostDirectional
        if post_dir:
            self._track_direction_field(result, raw_lower, raw_input, post_dir, "post_directional")

    def _track_direction_field(
        self,
        result: ParseResult,
        raw_lower: str,
        raw_input: str,
        direction: str,
        field_name: str,
    ) -> None:
        """Helper to track direction changes for a specific field.

        Args:
            result: The ParseResult to add cleaning operations to.
            raw_lower: Lowercase version of raw input.
            raw_input: The original raw address string.
            direction: The parsed direction value.
            field_name: Name of the field being tracked.
        """
        # Check if full direction was in raw input but got abbreviated
        for full_name, abbrev in DIRECTION_TO_ABBREV.items():
            # Check if full name is in raw and parsed direction matches abbreviation
            if full_name in raw_lower and direction.upper() == abbrev:
                result.add_process_cleaning(
                    field=field_name,
                    original_value=full_name.title(),
                    reason=f"Direction abbreviated: {full_name.title()} -> {direction}",
                    new_value=direction,
                    operation_type=OperationType.NORMALIZATION,
                )
                return

        # Check for case normalization (e.g., "n" -> "N")
        dir_pattern = rf"\b({re.escape(direction)})\b"
        match = re.search(dir_pattern, raw_input, re.IGNORECASE)
        if match:
            raw_dir = match.group(1)
            if raw_dir != direction and raw_dir.lower() == direction.lower():
                result.add_process_cleaning(
                    field=field_name,
                    original_value=raw_dir,
                    reason="Direction case normalized",
                    new_value=direction,
                    operation_type=OperationType.FORMATTING,
                )

    def track_unit_type_changes(self, result: ParseResult, raw_input: str) -> None:
        """Detect and track unit type standardization.

        Tracks when unit types are abbreviated or expanded
        (e.g., "Apartment" -> "Apt", "Suite" -> "Ste").

        Args:
            result: The ParseResult to add cleaning operations to.
            raw_input: The original raw address string.
        """
        if result.address is None:
            return

        address = result.address
        unit_type = address.SubaddressType

        if not unit_type:
            return

        raw_lower = raw_input.lower()

        # Check if full unit type was in raw input but got abbreviated
        for full_name, abbrev in UNIT_TYPE_TO_ABBREV.items():
            # Check if full name is in raw and parsed type matches abbreviation
            if full_name in raw_lower and unit_type.lower() == abbrev.lower():
                result.add_process_cleaning(
                    field="unit_type",
                    original_value=full_name.title(),
                    reason=f"Unit type abbreviated: {full_name.title()} -> {unit_type}",
                    new_value=unit_type,
                    operation_type=OperationType.NORMALIZATION,
                )
                return

        # Check for case normalization
        if unit_type:
            type_pattern = rf"\b({re.escape(unit_type)})\b"
            match = re.search(type_pattern, raw_input, re.IGNORECASE)
            if match:
                raw_type = match.group(1)
                if raw_type != unit_type and raw_type.lower() == unit_type.lower():
                    result.add_process_cleaning(
                        field="unit_type",
                        original_value=raw_type,
                        reason="Unit type case normalized",
                        new_value=unit_type,
                        operation_type=OperationType.FORMATTING,
                    )

    def track_punctuation_removal(self, result: ParseResult, raw_input: str) -> None:
        """Detect and track punctuation removal from address.

        Tracks when periods, extra commas, and other punctuation are stripped.

        Args:
            result: The ParseResult to add cleaning operations to.
            raw_input: The original raw address string.
        """
        # Check for periods that were removed (e.g., "St." -> "St", "P.O." -> "PO")
        if "." in raw_input:
            # Check common patterns with periods
            period_patterns = [
                (r"\bSt\.", "St."),
                (r"\bAve\.", "Ave."),
                (r"\bBlvd\.", "Blvd."),
                (r"\bDr\.", "Dr."),
                (r"\bRd\.", "Rd."),
                (r"\bP\.O\.", "P.O."),
                (r"\bApt\.", "Apt."),
                (r"\bSte\.", "Ste."),
                (r"\bN\.", "N."),
                (r"\bS\.", "S."),
                (r"\bE\.", "E."),
                (r"\bW\.", "W."),
            ]

            for pattern, original in period_patterns:
                if re.search(pattern, raw_input, re.IGNORECASE):
                    result.add_process_cleaning(
                        field="raw_input",
                        original_value=original,
                        reason="Period removed from abbreviation",
                        new_value=original.replace(".", ""),
                        operation_type=OperationType.FORMATTING,
                    )
                    # Only track one punctuation removal to avoid noise
                    return

        # Check for hash/pound symbol normalization (e.g., "#123" -> "123")
        if "#" in raw_input:
            result.add_process_cleaning(
                field="raw_input",
                original_value=None,
                reason="Hash/pound symbol removed from unit number",
                new_value=None,
                operation_type=OperationType.FORMATTING,
            )

    def track_component_parsing(self, result: ParseResult, raw_input: str) -> None:
        """Track what components were successfully extracted from raw input.

        This provides visibility into what the parser identified and extracted
        from the original address string.

        Args:
            result: The ParseResult to add cleaning operations to.
            raw_input: The original raw address string.
        """
        if result.address is None:
            return

        address = result.address

        # Build list of extracted components
        extracted_components: list[str] = []

        if address.AddressNumber:
            extracted_components.append("address_number")
        if address.StreetName:
            extracted_components.append("street_name")
        if address.StreetNamePostType:
            extracted_components.append("street_type")
        if address.StreetNamePreDirectional or address.StreetNamePostDirectional:
            extracted_components.append("directional")
        if address.SubaddressType or address.SubaddressIdentifier:
            extracted_components.append("unit")
        if address.PlaceName:
            extracted_components.append("city")
        if address.StateName:
            extracted_components.append("state")
        if address.ZipCode5:
            extracted_components.append("zip")
        if address.USPSBoxType or address.USPSBoxID:
            extracted_components.append("po_box")

        # Record the parsing operation with extracted components
        if extracted_components:
            result.add_process_cleaning(
                field="raw_input",
                original_value=raw_input,
                reason=f"Components extracted: {', '.join(extracted_components)}",
                new_value=address.FullAddress,
                operation_type=OperationType.PARSING,
            )
