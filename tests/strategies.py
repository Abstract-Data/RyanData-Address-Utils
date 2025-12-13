"""Shared Hypothesis strategies for address testing.

This module provides reusable Hypothesis strategies for generating
address components, ZIP codes, and full address structures for
property-based testing.
"""

from __future__ import annotations

import hypothesis.strategies as st

# =============================================================================
# Address Component Constants
# =============================================================================

STREET_NAMES = [
    "Main",
    "Oak",
    "Elm",
    "Maple",
    "Cedar",
    "Pine",
    "First",
    "Second",
    "Third",
    "Fourth",
    "Fifth",
    "Park",
    "Washington",
    "Lincoln",
    "Jefferson",
    "Madison",
    "Adams",
    "Jackson",
    "Franklin",
    "Cherry",
    "Walnut",
    "Spring",
    "Lake",
    "River",
    "Hill",
    "Valley",
    "Forest",
    "Meadow",
    "Sunset",
    "Highland",
]

STREET_TYPES = [
    "St",
    "Street",
    "Ave",
    "Avenue",
    "Blvd",
    "Boulevard",
    "Dr",
    "Drive",
    "Ln",
    "Lane",
    "Rd",
    "Road",
    "Ct",
    "Court",
    "Pl",
    "Place",
    "Way",
    "Cir",
    "Circle",
    "Pkwy",
    "Parkway",
    "Ter",
    "Terrace",
    "Hwy",
    "Highway",
]

DIRECTIONALS = ["N", "S", "E", "W", "NE", "NW", "SE", "SW"]
DIRECTIONALS_FULL = [
    "North",
    "South",
    "East",
    "West",
    "Northeast",
    "Northwest",
    "Southeast",
    "Southwest",
]

UNIT_TYPES = ["Apt", "Suite", "Ste", "Unit", "#", "Floor", "Fl", "Room", "Rm"]

# US cities with their state abbreviations and valid ZIP codes
CITY_STATE_ZIP = [
    ("Austin", "TX", "78749"),
    ("Dallas", "TX", "75201"),
    ("Houston", "TX", "77001"),
    ("New York", "NY", "10001"),
    ("Los Angeles", "CA", "90001"),
    ("Chicago", "IL", "60601"),
    ("Phoenix", "AZ", "85001"),
    ("Philadelphia", "PA", "19101"),
    ("San Antonio", "TX", "78201"),
    ("San Diego", "CA", "92101"),
    ("Miami", "FL", "33101"),
    ("Seattle", "WA", "98101"),
    ("Denver", "CO", "80201"),
    ("Boston", "MA", "02101"),
    ("Atlanta", "GA", "30301"),
]

STATE_ABBREVS = [
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
    "DC",
    "PR",
    "GU",
    "VI",
    "AS",
    "MP",
]

# Known valid ZIP codes from uszips.csv for testing
# These are verified to exist in the bundled uszips.csv
VALID_ZIPS = [
    "78749",  # Austin, TX
    "75201",  # Dallas, TX
    "77001",  # Houston, TX
    "10001",  # New York, NY
    "90001",  # Los Angeles, CA
    "60601",  # Chicago, IL
    "33101",  # Miami, FL
    "98101",  # Seattle, WA
]

# =============================================================================
# Basic Component Strategies
# =============================================================================


@st.composite
def street_number_strategy(draw: st.DrawFn) -> str:
    """Generate realistic street numbers including edge cases."""
    choice = draw(st.integers(min_value=0, max_value=4))
    if choice == 0:
        # Simple number (most common)
        return str(draw(st.integers(min_value=1, max_value=99999)))
    elif choice == 1:
        # Number with letter suffix (e.g., 123A)
        num = draw(st.integers(min_value=1, max_value=9999))
        letter = draw(st.sampled_from("ABCDEFGH"))
        return f"{num}{letter}"
    elif choice == 2:
        # Fraction (e.g., 123 1/2)
        num = draw(st.integers(min_value=1, max_value=999))
        return f"{num} 1/2"
    elif choice == 3:
        # Range (e.g., 123-125)
        num = draw(st.integers(min_value=1, max_value=999))
        return f"{num}-{num + 2}"
    else:
        # Hyphenated (e.g., 12-34, common in NYC)
        return f"{draw(st.integers(1, 99))}-{draw(st.integers(1, 99))}"


@st.composite
def street_name_strategy(draw: st.DrawFn) -> str:
    """Generate street names."""
    return draw(st.sampled_from(STREET_NAMES))


@st.composite
def street_type_strategy(draw: st.DrawFn) -> str:
    """Generate street types (St, Ave, Blvd, etc.)."""
    return draw(st.sampled_from(STREET_TYPES))


@st.composite
def directional_strategy(draw: st.DrawFn) -> str:
    """Generate directional indicators."""
    return draw(st.sampled_from(DIRECTIONALS + DIRECTIONALS_FULL))


@st.composite
def unit_type_strategy(draw: st.DrawFn) -> str:
    """Generate unit types (Apt, Suite, etc.)."""
    return draw(st.sampled_from(UNIT_TYPES))


@st.composite
def unit_number_strategy(draw: st.DrawFn) -> str:
    """Generate unit numbers/identifiers."""
    choice = draw(st.integers(min_value=0, max_value=2))
    if choice == 0:
        # Numeric (e.g., 101, 5)
        return str(draw(st.integers(min_value=1, max_value=999)))
    elif choice == 1:
        # Alphanumeric (e.g., 4B, 12A)
        num = draw(st.integers(min_value=1, max_value=99))
        letter = draw(st.sampled_from("ABCDEFGH"))
        return f"{num}{letter}"
    else:
        # Letter only (e.g., A, B, C)
        return draw(st.sampled_from("ABCDEFGH"))


# =============================================================================
# ZIP Code Strategies
# =============================================================================


@st.composite
def valid_zip5_strategy(draw: st.DrawFn) -> str:
    """Generate a valid 5-digit ZIP code from known valid ZIPs."""
    return draw(st.sampled_from(VALID_ZIPS))


@st.composite
def random_zip5_strategy(draw: st.DrawFn) -> str:
    """Generate a random 5-digit string that looks like a ZIP code."""
    return draw(st.text(alphabet="0123456789", min_size=5, max_size=5))


@st.composite
def zip4_strategy(draw: st.DrawFn) -> str:
    """Generate a 4-digit ZIP+4 extension."""
    return draw(st.text(alphabet="0123456789", min_size=4, max_size=4))


@st.composite
def valid_zip_plus_4_strategy(draw: st.DrawFn) -> str:
    """Generate a valid ZIP+4 (e.g., 78749-1234)."""
    zip5 = draw(valid_zip5_strategy())
    zip4 = draw(zip4_strategy())
    return f"{zip5}-{zip4}"


@st.composite
def invalid_zip5_strategy(draw: st.DrawFn) -> str:
    """Generate invalid ZIP codes for negative testing."""
    choice = draw(st.integers(min_value=0, max_value=3))
    if choice == 0:
        # Too short
        return draw(st.text(alphabet="0123456789", min_size=1, max_size=4))
    elif choice == 1:
        # Too long
        return draw(st.text(alphabet="0123456789", min_size=6, max_size=10))
    elif choice == 2:
        # Contains letters
        return draw(
            st.text(alphabet="0123456789ABCDEF", min_size=5, max_size=5).filter(
                lambda x: not x.isdigit()
            )
        )
    else:
        # Empty or whitespace
        return draw(st.sampled_from(["", "   ", "\t", "\n"]))


@st.composite
def invalid_zip4_strategy(draw: st.DrawFn) -> str:
    """Generate invalid ZIP+4 extensions for negative testing."""
    choice = draw(st.integers(min_value=0, max_value=2))
    if choice == 0:
        # Wrong length
        length = draw(st.integers(min_value=1, max_value=3))
        return draw(st.text(alphabet="0123456789", min_size=length, max_size=length))
    elif choice == 1:
        # Contains letters
        return draw(
            st.text(alphabet="0123456789ABCDEF", min_size=4, max_size=4).filter(
                lambda x: not x.isdigit()
            )
        )
    else:
        # Too long
        return draw(st.text(alphabet="0123456789", min_size=5, max_size=8))


# =============================================================================
# City/State/ZIP Tuple Strategies
# =============================================================================


@st.composite
def city_state_zip_strategy(draw: st.DrawFn) -> tuple[str, str, str]:
    """Generate a consistent city/state/ZIP tuple."""
    return draw(st.sampled_from(CITY_STATE_ZIP))


@st.composite
def state_abbrev_strategy(draw: st.DrawFn) -> str:
    """Generate a valid state abbreviation."""
    return draw(st.sampled_from(STATE_ABBREVS))


# =============================================================================
# Address Dictionary Strategies
# =============================================================================


@st.composite
def minimal_address_dict_strategy(draw: st.DrawFn) -> dict[str, str | None]:
    """Generate a minimal address dictionary with just required fields."""
    city, state, zip_code = draw(city_state_zip_strategy())
    return {
        "AddressNumber": draw(street_number_strategy()),
        "StreetName": draw(street_name_strategy()),
        "StreetNamePostType": draw(street_type_strategy()),
        "PlaceName": city,
        "StateName": state,
        "ZipCode": zip_code,
    }


@st.composite
def full_address_dict_strategy(draw: st.DrawFn) -> dict[str, str | None]:
    """Generate a full address dictionary with optional fields."""
    base = draw(minimal_address_dict_strategy())

    # Optionally add pre-directional
    if draw(st.booleans()):
        base["StreetNamePreDirectional"] = draw(st.sampled_from(DIRECTIONALS))

    # Optionally add post-directional
    if draw(st.booleans()):
        base["StreetNamePostDirectional"] = draw(st.sampled_from(DIRECTIONALS))

    # Optionally add unit
    if draw(st.booleans()):
        base["SubaddressType"] = draw(unit_type_strategy())
        base["SubaddressIdentifier"] = draw(unit_number_strategy())

    # Optionally add ZIP+4
    if draw(st.booleans()):
        base["ZipCode4"] = draw(zip4_strategy())
        # Update ZipCode to include the +4
        base["ZipCode"] = f"{base['ZipCode']}-{base['ZipCode4']}"

    return base


@st.composite
def po_box_address_dict_strategy(draw: st.DrawFn) -> dict[str, str | None]:
    """Generate a PO Box address dictionary."""
    city, state, zip_code = draw(city_state_zip_strategy())
    box_id = str(draw(st.integers(min_value=1, max_value=99999)))

    return {
        "USPSBoxType": draw(st.sampled_from(["PO Box", "P.O. Box", "Post Office Box"])),
        "USPSBoxID": box_id,
        "PlaceName": city,
        "StateName": state,
        "ZipCode": zip_code,
    }


# =============================================================================
# Full Address String Strategies
# =============================================================================


@st.composite
def simple_address_string_strategy(draw: st.DrawFn) -> str:
    """Generate a simple formatted address string."""
    city, state, zip_code = draw(city_state_zip_strategy())
    street_num = draw(st.integers(min_value=1, max_value=9999))
    street_name = draw(street_name_strategy())
    street_type = draw(st.sampled_from(STREET_TYPES[:10]))  # Common types only

    return f"{street_num} {street_name} {street_type}, {city} {state} {zip_code}"


@st.composite
def complex_address_string_strategy(draw: st.DrawFn) -> str:
    """Generate a more complex address string with optional components."""
    parts = []

    # Street number
    parts.append(draw(street_number_strategy()))

    # Optional pre-directional
    if draw(st.booleans()):
        parts.append(draw(st.sampled_from(DIRECTIONALS)))

    # Street name
    parts.append(draw(street_name_strategy()))

    # Street type
    parts.append(draw(street_type_strategy()))

    # Optional post-directional
    if draw(st.booleans()):
        parts.append(draw(st.sampled_from(DIRECTIONALS)))

    # Optional unit
    if draw(st.booleans()):
        unit_type = draw(unit_type_strategy())
        unit_num = draw(unit_number_strategy())
        parts.append(f"{unit_type} {unit_num}")

    # City, State, ZIP
    city, state, zip_code = draw(city_state_zip_strategy())
    parts.append(city)
    parts.append(state)

    # Optionally add ZIP+4
    if draw(st.booleans()):
        zip4 = draw(zip4_strategy())
        parts.append(f"{zip_code}-{zip4}")
    else:
        parts.append(zip_code)

    return " ".join(parts)


# =============================================================================
# Builder Method Sequence Strategies
# =============================================================================


@st.composite
def builder_method_sequence_strategy(draw: st.DrawFn) -> list[tuple[str, str]]:
    """Generate a sequence of builder method calls with values.

    Returns a list of (method_name, value) tuples that can be applied to an AddressBuilder.
    """
    methods = []

    # Always include core components
    methods.append(("with_street_number", draw(street_number_strategy())))
    methods.append(("with_street_name", draw(street_name_strategy())))
    methods.append(("with_street_type", draw(street_type_strategy())))

    city, state, zip_code = draw(city_state_zip_strategy())
    methods.append(("with_city", city))
    methods.append(("with_state", state))
    methods.append(("with_zip", zip_code))

    # Optionally add directionals
    if draw(st.booleans()):
        methods.append(("with_street_pre_directional", draw(st.sampled_from(DIRECTIONALS))))

    if draw(st.booleans()):
        methods.append(("with_street_post_directional", draw(st.sampled_from(DIRECTIONALS))))

    # Optionally add unit
    if draw(st.booleans()):
        methods.append(("with_unit_type", draw(unit_type_strategy())))
        methods.append(("with_unit_number", draw(unit_number_strategy())))

    # Optionally add building name
    if draw(st.booleans()):
        building_name = draw(
            st.sampled_from(
                [
                    "Tower A",
                    "Building 100",
                    "The Plaza",
                    "Center Point",
                    "Main Building",
                    "Annex",
                    "West Wing",
                    "North Tower",
                ]
            )
        )
        methods.append(("with_building_name", building_name))

    # Shuffle to test order independence (builder should work in any order)
    shuffled = draw(st.permutations(methods))
    return list(shuffled)


# =============================================================================
# International Address Strategies (for libpostal testing)
# =============================================================================

INTERNATIONAL_ADDRESSES = [
    "10 Downing St, London SW1A 2AA, UK",
    "Potsdamer Straße 3, 10785 Berlin, Germany",
    "1-1-2 Oshiage, Sumida-ku, Tokyo 131-0045, Japan",
    "Av. Insurgentes Sur 1602, Ciudad de México, CDMX, México",
    "Rua do Catete 311, Rio de Janeiro, RJ, 22220-001, Brasil",
]


@st.composite
def international_address_strategy(draw: st.DrawFn) -> str:
    """Generate an international address string."""
    return draw(st.sampled_from(INTERNATIONAL_ADDRESSES))


# =============================================================================
# Malformed/Edge Case Strategies
# =============================================================================


@st.composite
def whitespace_variant_strategy(draw: st.DrawFn, base_address: str) -> str:
    """Generate whitespace variants of a base address."""
    choice = draw(st.integers(min_value=0, max_value=4))
    if choice == 0:
        # Leading whitespace
        return "  " + base_address
    elif choice == 1:
        # Trailing whitespace
        return base_address + "  "
    elif choice == 2:
        # Both
        return "  " + base_address + "  "
    elif choice == 3:
        # Multiple internal spaces
        return base_address.replace(" ", "  ")
    else:
        # Tabs
        return base_address.replace(" ", "\t")


@st.composite
def case_variant_strategy(draw: st.DrawFn, base_address: str) -> str:
    """Generate case variants of a base address."""
    choice = draw(st.integers(min_value=0, max_value=2))
    if choice == 0:
        return base_address.upper()
    elif choice == 1:
        return base_address.lower()
    else:
        # Mixed case (random per character)
        return "".join(c.upper() if draw(st.booleans()) else c.lower() for c in base_address)
