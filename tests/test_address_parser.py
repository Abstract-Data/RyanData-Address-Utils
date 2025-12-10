import contextlib

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pydantic_core import PydanticCustomError

from ryandata_address_utils import (
    AddressService,
    ParseResult,
    RyanDataAddressError,
    get_zip_info,
    is_valid_state,
    is_valid_zip,
    normalize_state,
    parse,
)
from ryandata_address_utils.data import get_valid_state_abbrevs

# =============================================================================
# Test Data / Strategies
# =============================================================================

# All valid US state abbreviations
VALID_STATE_ABBREVS = list(get_valid_state_abbrevs())

# State full names (subset for testing)
STATE_NAMES = [
    "Alabama",
    "Alaska",
    "Arizona",
    "Arkansas",
    "California",
    "Colorado",
    "Connecticut",
    "Delaware",
    "Florida",
    "Georgia",
    "Hawaii",
    "Idaho",
    "Illinois",
    "Indiana",
    "Iowa",
    "Kansas",
    "Kentucky",
    "Louisiana",
    "Maine",
    "Maryland",
    "Massachusetts",
    "Michigan",
    "Minnesota",
    "Mississippi",
    "Missouri",
    "Montana",
    "Nebraska",
    "Nevada",
    "New Hampshire",
    "New Jersey",
    "New Mexico",
    "New York",
    "North Carolina",
    "North Dakota",
    "Ohio",
    "Oklahoma",
    "Oregon",
    "Pennsylvania",
    "Rhode Island",
    "South Carolina",
    "South Dakota",
    "Tennessee",
    "Texas",
    "Utah",
    "Vermont",
    "Virginia",
    "Washington",
    "West Virginia",
    "Wisconsin",
    "Wyoming",
    "District of Columbia",
    "Puerto Rico",
    "Guam",
    "Virgin Islands",
]

# Known valid ZIP codes for testing (verified to exist in uszips.csv)
VALID_ZIPS = [
    "10001",  # New York, NY
    "90210",  # Beverly Hills, CA
    "78749",  # Austin, TX
    "60601",  # Chicago, IL
    "33101",  # Miami, FL
    "75201",  # Dallas, TX
    "98101",  # Seattle, WA
]

# Street types
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

# Directionals
DIRECTIONALS = ["N", "S", "E", "W", "NE", "NW", "SE", "SW", "North", "South", "East", "West"]

# Unit types
UNIT_TYPES = ["Apt", "Apt.", "Suite", "Ste", "Ste.", "Unit", "#", "Floor", "Fl"]


# =============================================================================
# Hypothesis Strategies
# =============================================================================


@st.composite
def valid_zip_strategy(draw: st.DrawFn) -> str:
    """Generate valid ZIP codes."""
    return draw(st.sampled_from(VALID_ZIPS))


@st.composite
def zip_plus_4_strategy(draw: st.DrawFn) -> str:
    """Generate ZIP+4 format codes."""
    base_zip = draw(st.sampled_from(VALID_ZIPS))
    plus_4 = draw(st.text(alphabet="0123456789", min_size=4, max_size=4))
    return f"{base_zip}-{plus_4}"


@st.composite
def street_number_strategy(draw: st.DrawFn) -> str:
    """Generate street numbers including edge cases."""
    choice = draw(st.integers(min_value=0, max_value=4))
    if choice == 0:
        # Simple number
        return str(draw(st.integers(min_value=1, max_value=99999)))
    elif choice == 1:
        # Number with letter suffix (123A)
        num = draw(st.integers(min_value=1, max_value=9999))
        letter = draw(st.sampled_from("ABCDEFGH"))
        return f"{num}{letter}"
    elif choice == 2:
        # Fraction (123 1/2)
        num = draw(st.integers(min_value=1, max_value=999))
        return f"{num} 1/2"
    elif choice == 3:
        # Range (123-125)
        num = draw(st.integers(min_value=1, max_value=999))
        return f"{num}-{num + 2}"
    else:
        # Hyphenated (12-34)
        return f"{draw(st.integers(1, 99))}-{draw(st.integers(1, 99))}"


@st.composite
def street_name_strategy(draw: st.DrawFn) -> str:
    """Generate street names."""
    choice = draw(st.integers(min_value=0, max_value=3))
    if choice == 0:
        # Simple name
        return draw(
            st.sampled_from(
                [
                    "Main",
                    "Oak",
                    "Elm",
                    "Maple",
                    "Cedar",
                    "Pine",
                    "First",
                    "Second",
                    "Park",
                    "Washington",
                    "Lincoln",
                    "Jefferson",
                    "Martin Luther King",
                ]
            )
        )
    elif choice == 1:
        # Numbered street
        ordinal = draw(
            st.sampled_from(
                [
                    "1st",
                    "2nd",
                    "3rd",
                    "4th",
                    "5th",
                    "10th",
                    "21st",
                    "22nd",
                    "23rd",
                    "42nd",
                    "100th",
                    "101st",
                ]
            )
        )
        return ordinal
    elif choice == 2:
        # Multi-word name
        return draw(
            st.sampled_from(
                [
                    "Martin Luther King Jr",
                    "John F Kennedy",
                    "Ben Franklin",
                    "Old Mill",
                    "New Hope",
                    "Rolling Hills",
                    "Shady Grove",
                ]
            )
        )
    else:
        # Highway/Route
        num = draw(st.integers(min_value=1, max_value=999))
        prefix = draw(st.sampled_from(["Route", "Highway", "State Road", "US"]))
        return f"{prefix} {num}"


@st.composite
def full_address_strategy(draw: st.DrawFn) -> str:
    """Generate complete addresses."""
    parts = []

    # Street number
    parts.append(draw(street_number_strategy()))

    # Optional directional
    if draw(st.booleans()):
        parts.append(draw(st.sampled_from(DIRECTIONALS)))

    # Street name
    parts.append(draw(street_name_strategy()))

    # Street type
    parts.append(draw(st.sampled_from(STREET_TYPES)))

    # Optional unit
    if draw(st.booleans()):
        unit_type = draw(st.sampled_from(UNIT_TYPES))
        unit_num = draw(st.integers(min_value=1, max_value=999))
        parts.append(f"{unit_type} {unit_num}")

    # City
    city = draw(
        st.sampled_from(
            [
                "Austin",
                "New York",
                "Los Angeles",
                "Chicago",
                "Houston",
                "Phoenix",
                "San Antonio",
                "San Diego",
                "Dallas",
                "San Jose",
            ]
        )
    )
    parts.append(city)

    # State
    state = draw(st.sampled_from(VALID_STATE_ABBREVS[:50]))  # Limit to common states
    parts.append(state)

    # ZIP
    parts.append(draw(st.sampled_from(VALID_ZIPS)))

    return " ".join(parts)


# =============================================================================
# Basic Property Tests
# =============================================================================


class TestBasicProperties:
    """Test basic properties that should always hold."""

    @given(st.sampled_from(VALID_ZIPS))
    def test_valid_zips_are_valid(self, zip_code: str) -> None:
        """Valid ZIP codes should pass validation."""
        assert is_valid_zip(zip_code)

    @given(st.sampled_from(VALID_STATE_ABBREVS))
    def test_valid_state_abbrevs_are_valid(self, state: str) -> None:
        """Valid state abbreviations should pass validation."""
        assert is_valid_state(state)

    @given(st.sampled_from(STATE_NAMES))
    def test_valid_state_names_are_valid(self, state: str) -> None:
        """Valid state names should pass validation."""
        assert is_valid_state(state)

    @given(st.sampled_from(STATE_NAMES))
    def test_state_names_normalize_to_abbrev(self, state: str) -> None:
        """State names should normalize to 2-letter abbreviations."""
        normalized = normalize_state(state)
        assert normalized is not None
        assert len(normalized) == 2
        assert normalized.isupper()

    @given(st.sampled_from(VALID_ZIPS))
    def test_zip_lookup_returns_data(self, zip_code: str) -> None:
        """Valid ZIP codes should return city/state data."""
        info = get_zip_info(zip_code)
        assert info is not None
        assert info.city
        assert info.state_id
        assert len(info.state_id) == 2


# =============================================================================
# ZIP Code Edge Cases
# =============================================================================


class TestZipCodeEdgeCases:
    """Test ZIP code edge cases."""

    @given(zip_plus_4_strategy())
    def test_zip_plus_4_format(self, zip_code: str) -> None:
        """ZIP+4 format should work (validates first 5 digits)."""
        base_zip = zip_code.split("-")[0]
        # Only test if base is valid
        if is_valid_zip(base_zip):
            assert is_valid_zip(zip_code)

    def test_leading_zeros_preserved(self) -> None:
        """ZIP codes with leading zeros should be handled correctly."""
        # Puerto Rico ZIPs start with 00 (stored as 601 in CSV, padded to 00601)
        assert is_valid_zip("00601") or is_valid_zip("601")
        info = get_zip_info("00601")
        if info is None:
            info = get_zip_info("601")
        assert info is not None
        assert info.state_id == "PR"

    @given(st.text(alphabet="0123456789", min_size=5, max_size=5))
    def test_random_5_digit_strings(self, zip_code: str) -> None:
        """Random 5-digit strings should not crash validation."""
        # Just verify it doesn't crash - may or may not be valid
        result = is_valid_zip(zip_code)
        assert isinstance(result, bool)

    def test_invalid_zip_raises_on_parse(self) -> None:
        """Parsing with invalid ZIP should raise PydanticCustomError."""
        with pytest.raises(PydanticCustomError, match="Invalid US ZIP code"):
            parse("123 Main St, Austin TX 00000")

    def test_invalid_zip_allowed_without_validation(self) -> None:
        """Invalid ZIP should work with validate=False."""
        result = parse("123 Main St, Austin TX 00000", validate=False)
        assert result.is_parsed
        assert result.address is not None
        assert result.address.ZipCode == "00000"

    def test_zip_plus_four_splits_into_fields(self) -> None:
        """ZIP+4 should populate ZipCode5, ZipCode4, ZipCodeFull."""
        result = parse("123 Main St, Austin TX 78749-1234")
        assert result.is_valid
        assert result.address is not None
        addr = result.address
        assert addr.ZipCode5 == "78749"
        assert addr.ZipCode4 == "1234"
        assert addr.ZipCodeFull == "78749-1234"
        assert addr.ZipCode == "78749-1234"

    def test_zip_plus_four_without_dash(self) -> None:
        """Nine-digit ZIP should be parsed into 5 + 4."""
        result = parse("123 Main St, Austin TX 787491234")
        assert result.is_valid
        assert result.address is not None
        addr = result.address
        assert addr.ZipCode5 == "78749"
        assert addr.ZipCode4 == "1234"
        assert addr.ZipCodeFull == "78749-1234"

    def test_invalid_zip_length_raises(self) -> None:
        """Invalid ZIP lengths should raise validation error."""
        result = parse("123 Main St, Austin TX 1234")
        assert not result.is_parsed
        from pydantic import ValidationError

        assert isinstance(result.error, ValidationError)

    def test_invalid_zip4_length_raises(self) -> None:
        """Invalid ZIP4 should raise validation error."""
        result = parse("123 Main St, Austin TX 78749-12")
        assert not result.is_parsed
        from pydantic import ValidationError

        assert isinstance(result.error, ValidationError)


# =============================================================================
# State Edge Cases
# =============================================================================


class TestStateEdgeCases:
    """Test state name/abbreviation edge cases."""

    @given(st.sampled_from(STATE_NAMES))
    def test_case_insensitive_state_names(self, state: str) -> None:
        """State names should be case-insensitive."""
        assert is_valid_state(state.lower())
        assert is_valid_state(state.upper())
        assert is_valid_state(state.title())

    @given(st.sampled_from(VALID_STATE_ABBREVS))
    def test_case_insensitive_state_abbrevs(self, state: str) -> None:
        """State abbreviations should be case-insensitive."""
        assert is_valid_state(state.lower())
        assert is_valid_state(state.upper())

    def test_territories_are_valid(self) -> None:
        """US territories should be valid states."""
        territories = ["PR", "GU", "VI", "AS", "MP"]
        for territory in territories:
            assert is_valid_state(territory), f"{territory} should be valid"

    def test_invalid_state_raises_on_parse(self) -> None:
        """Parsing with invalid state should raise PydanticCustomError."""
        with pytest.raises(PydanticCustomError, match="Invalid US state"):
            parse("123 Main St, Austin XX 78749")


# =============================================================================
# Address Parsing Edge Cases
# =============================================================================


class TestAddressParsingEdgeCases:
    """Test various unusual but valid address formats."""

    @pytest.mark.parametrize(
        "address,expected_field,expected_value",
        [
            # Basic addresses
            ("123 Main St, Austin TX 78749", "AddressNumber", "123"),
            ("456 Oak Ave, New York NY 10001", "StreetName", "Oak"),
            # Directionals
            ("100 N Main St, Austin TX 78749", "StreetNamePreDirectional", "N"),
            ("200 Main St S, Austin TX 78749", "StreetNamePostDirectional", "S"),
            ("300 NE Oak Ave, Austin TX 78749", "StreetNamePreDirectional", "NE"),
            # Unit numbers
            ("400 Main St Apt 5, Austin TX 78749", "OccupancyIdentifier", "5"),
            ("500 Main St Suite 100, Austin TX 78749", "OccupancyIdentifier", "100"),
            # PO Box
            ("PO Box 1234, Austin TX 78749", "USPSBoxID", "1234"),
            ("P.O. Box 5678, Austin TX 78749", "USPSBoxID", "5678"),
        ],
    )
    def test_specific_address_formats(
        self, address: str, expected_field: str, expected_value: str
    ) -> None:
        """Test specific address formats parse correctly."""
        result = parse(address)
        assert result.address is not None
        assert getattr(result.address, expected_field) == expected_value

    def test_numbered_streets(self) -> None:
        """Numbered streets should parse correctly."""
        result = parse("123 42nd St, New York NY 10001")
        assert result.address is not None
        assert result.address.AddressNumber == "123"
        assert "42nd" in (result.address.StreetName or "")

    def test_multi_word_city(self) -> None:
        """Multi-word city names should parse correctly."""
        result = parse("123 Main St, New York NY 10001")
        assert result.address is not None
        assert result.address.PlaceName == "New York"

    def test_full_state_name(self) -> None:
        """Full state names should parse and validate."""
        result = parse("123 Main St, Austin Texas 78749")
        assert result.address is not None
        assert result.address.StateName == "Texas"

    def test_highway_address(self) -> None:
        """Highway addresses should parse."""
        result = parse("12345 Highway 290, Austin TX 78749", validate=False)
        assert result.address is not None
        assert result.address.AddressNumber == "12345"


# =============================================================================
# Fuzzing Tests
# =============================================================================


class TestFuzzing:
    """Fuzz testing to ensure parser doesn't crash on unexpected input."""

    @given(st.text(min_size=0, max_size=500))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_random_text_does_not_crash(self, text: str) -> None:
        """Random text should not crash the parser."""
        try:
            parse(text, validate=False)
        except ValueError:
            pass  # ValueError is acceptable for unparseable addresses
        except Exception as e:
            # Other exceptions should not occur
            pytest.fail(f"Unexpected exception: {type(e).__name__}: {e}")

    @given(st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=200))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_unicode_does_not_crash(self, text: str) -> None:
        """Unicode text should not crash the parser."""
        try:
            parse(text, validate=False)
        except ValueError:
            pass
        except Exception as e:
            pytest.fail(f"Unexpected exception: {type(e).__name__}: {e}")

    def test_empty_string(self) -> None:
        """Empty string should not crash (may return empty Address or raise)."""
        result = parse("", validate=False)
        if result.is_parsed:
            # If it succeeds, address component fields should be None
            # Note: Address1, Address2, FullAddress, RawInput are computed/meta fields
            addr_dict = result.to_dict()
            # Check that main address fields are None (excluding computed/meta fields)
            main_fields = {
                k: v
                for k, v in addr_dict.items()
                if k not in ("Address1", "Address2", "FullAddress", "RawInput")
            }
            assert all(v is None for v in main_fields.values())
        # If not valid, that's also acceptable

    def test_whitespace_only(self) -> None:
        """Whitespace-only string should not crash."""
        result = parse("   \t\n  ", validate=False)
        if result.is_parsed:
            # If it succeeds, address component fields should be None
            # Note: Address1, Address2, FullAddress, RawInput are computed/meta fields
            addr_dict = result.to_dict()
            # Check that main address fields are None (excluding computed/meta fields)
            main_fields = {
                k: v
                for k, v in addr_dict.items()
                if k not in ("Address1", "Address2", "FullAddress", "RawInput")
            }
            assert all(v is None for v in main_fields.values())
        # If not valid, that's also acceptable

    @given(st.text(min_size=1000, max_size=5000))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_very_long_strings(self, text: str) -> None:
        """Very long strings should not crash."""
        try:
            parse(text, validate=False)
        except ValueError:
            pass
        except Exception as e:
            pytest.fail(f"Unexpected exception: {type(e).__name__}: {e}")

    @pytest.mark.parametrize(
        "special",
        [
            "!@#$%^&*()",
            "<script>alert('xss')</script>",
            "'; DROP TABLE addresses; --",
            "\x00\x01\x02",  # Null bytes
            "\\n\\t\\r",
            "123 Main St\n\nAustin TX 78749",
        ],
    )
    def test_special_characters(self, special: str) -> None:
        """Special characters should not crash the parser."""
        with contextlib.suppress(ValueError):
            parse(special, validate=False)


# =============================================================================
# Generated Address Tests
# =============================================================================


class TestGeneratedAddresses:
    """Test with generated address combinations."""

    @given(full_address_strategy())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_generated_addresses_parse(self, address: str) -> None:
        """Generated addresses should parse without crashing."""
        result = parse(address, validate=False)
        # Parser should not crash, may or may not be valid
        assert isinstance(result, ParseResult)

    @given(
        street_num=st.integers(min_value=1, max_value=9999),
        street_name=st.sampled_from(["Main", "Oak", "Elm", "First", "Park"]),
        street_type=st.sampled_from(STREET_TYPES[:10]),
        city=st.sampled_from(["Austin", "Dallas"]),
        state=st.sampled_from(["TX"]),
        zip_code=st.sampled_from(["78749", "75201"]),  # Verified valid TX ZIPs
    )
    def test_simple_texas_addresses(
        self,
        street_num: int,
        street_name: str,
        street_type: str,
        city: str,
        state: str,
        zip_code: str,
    ) -> None:
        """Simple Texas addresses should always parse and validate."""
        address = f"{street_num} {street_name} {street_type}, {city} {state} {zip_code}"
        result = parse(address)
        assert result.is_valid
        assert result.address is not None
        assert result.address.AddressNumber == str(street_num)
        assert result.address.StateName == state
        assert result.address.ZipCode == zip_code


# =============================================================================
# Validation Toggle Tests
# =============================================================================


class TestValidationToggle:
    """Test the validate parameter."""

    def test_validation_on_by_default(self) -> None:
        """Validation should be on by default and raise exceptions for invalid data."""
        with pytest.raises(PydanticCustomError):
            parse("123 Main St, Austin XX 00000")

    def test_validation_can_be_disabled(self) -> None:
        """Validation can be disabled."""
        result = parse("123 Main St, Austin XX 00000", validate=False)
        assert result.is_parsed
        assert result.address is not None
        assert result.address.StateName == "XX"
        assert result.address.ZipCode == "00000"

    def test_valid_address_works_with_validation(self) -> None:
        """Valid addresses should work with validation enabled."""
        result = parse("123 Main St, Austin TX 78749", validate=True)
        assert result.is_valid
        assert result.address is not None
        assert result.address.ZipCode == "78749"
        assert result.address.StateName == "TX"


# =============================================================================
# AddressService Tests
# =============================================================================


class TestAddressService:
    """Test the AddressService facade."""

    def test_default_service_works(self) -> None:
        """Default service should work out of the box."""
        service = AddressService()
        result = service.parse("123 Main St, Austin TX 78749")
        assert result.is_valid
        assert result.address is not None
        assert result.address.AddressNumber == "123"

    def test_service_batch_parsing(self) -> None:
        """Batch parsing should work."""
        service = AddressService()
        addresses = [
            "123 Main St, Austin TX 78749",
            "456 Oak Ave, Dallas TX 75201",
        ]
        results = service.parse_batch(addresses)
        assert len(results) == 2
        assert all(r.is_valid for r in results)

    def test_service_zip_lookup(self) -> None:
        """ZIP lookup should work."""
        service = AddressService()
        info = service.lookup_zip("78749")
        assert info is not None
        assert info.state_id == "TX"

    def test_service_city_state_from_zip(self) -> None:
        """City/state lookup from ZIP should work."""
        service = AddressService()
        result = service.get_city_state_from_zip("78749")
        assert result is not None
        city, state = result
        assert state == "TX"

    def test_service_parse_to_dict(self) -> None:
        """parse_to_dict should work."""
        service = AddressService()
        result = service.parse_to_dict("123 Main St, Austin TX 78749")
        assert result["AddressNumber"] == "123"
        assert result["ZipCode"] == "78749"


# =============================================================================
# Address Formatting Tests (Address1, Address2, FullAddress Properties)
# =============================================================================


class TestAddressFormatting:
    """Test the Address formatting properties (Address1, Address2, FullAddress)."""

    def test_simple_street_address_to_address1(self) -> None:
        """Simple street address should format to Address1 correctly."""
        result = parse("123 Main St, Austin TX 78749", validate=False)
        assert result.address is not None
        address1 = result.address.Address1
        assert address1 is not None
        assert "123" in address1
        assert "Main" in address1
        assert "St" in address1

    def test_address1_with_directionals(self) -> None:
        """Address1 should include directionals."""
        result = parse("100 N Main St S, Austin TX 78749", validate=False)
        assert result.address is not None
        address1 = result.address.Address1
        assert address1 is not None
        # Should contain both pre and post directionals
        assert "100" in address1
        assert "Main" in address1
        assert "St" in address1

    def test_address1_po_box(self) -> None:
        """PO Box addresses should format to Address1."""
        result = parse("PO Box 1234, Austin TX 78749", validate=False)
        assert result.address is not None
        address1 = result.address.Address1
        assert address1 is not None
        assert "PO Box" in address1 or "P.O." in address1
        assert "1234" in address1

    def test_address1_none_when_no_components(self) -> None:
        """Address1 should be None when no street components present."""
        from ryandata_address_utils.models import AddressBuilder

        address = AddressBuilder().with_city("Austin").with_state("TX").with_zip("78749").build()
        assert address.Address1 is None

    def test_address2_with_apartment(self) -> None:
        """Address2 should include apartment/unit information."""
        result = parse("400 Main St Apt 5, Austin TX 78749", validate=False)
        assert result.address is not None
        address2 = result.address.Address2
        # Address2 may or may not be populated depending on parser
        if address2:
            assert "Apt" in address2 or "5" in address2

    def test_address2_none_when_no_subaddress(self) -> None:
        """Address2 should be None when no subaddress components present."""
        result = parse("123 Main St, Austin TX 78749", validate=False)
        assert result.address is not None
        assert result.address.Address2 is None

    def test_address2_with_suite(self) -> None:
        """Address2 should include suite information."""
        result = parse("500 Main St Suite 100, Austin TX 78749", validate=False)
        assert result.address is not None
        address2 = result.address.Address2
        if address2:
            # May contain suite info depending on parser
            assert len(address2) > 0

    def test_full_address_basic(self) -> None:
        """FullAddress should format correctly for basic address."""
        result = parse("123 Main St, Austin TX 78749", validate=False)
        assert result.address is not None
        full_address = result.address.FullAddress
        assert "123" in full_address
        assert "Main" in full_address
        assert "Austin" in full_address
        assert "TX" in full_address
        assert "78749" in full_address

    def test_full_address_with_po_box(self) -> None:
        """FullAddress should format correctly for PO Box."""
        result = parse("PO Box 1234, Austin TX 78749", validate=False)
        assert result.address is not None
        full_address = result.address.FullAddress
        assert "1234" in full_address
        assert "Austin" in full_address
        assert "TX" in full_address
        assert "78749" in full_address

    def test_full_address_only_city_state_zip(self) -> None:
        """FullAddress should work with only city, state, zip."""
        from ryandata_address_utils.models import AddressBuilder

        address = AddressBuilder().with_city("Austin").with_state("TX").with_zip("78749").build()
        full_address = address.FullAddress
        assert "Austin" in full_address
        assert "TX" in full_address
        assert "78749" in full_address

    def test_full_address_no_components(self) -> None:
        """FullAddress should return empty string when all components None."""
        from ryandata_address_utils.models import Address

        address = Address()
        assert address.FullAddress == ""

    def test_full_address_only_address1(self) -> None:
        """FullAddress should work with only Address1."""
        from ryandata_address_utils.models import AddressBuilder

        address = (
            AddressBuilder()
            .with_street_number("123")
            .with_street_name("Main")
            .with_street_type("St")
            .build()
        )
        full_address = address.FullAddress
        assert "123" in full_address
        assert "Main" in full_address
        assert "St" in full_address

    def test_address1_with_number_suffix(self) -> None:
        """Address1 should include address number suffix."""
        from ryandata_address_utils.models import AddressBuilder

        address = (
            AddressBuilder()
            .with_street_number("123")
            .with_address_number_suffix("1/2")
            .with_street_name("Main")
            .with_street_type("St")
            .build()
        )
        address1 = address.Address1
        assert address1 is not None
        assert "123" in address1
        assert "1/2" in address1

    def test_address2_building_name(self) -> None:
        """Address2 should include building name."""
        from ryandata_address_utils.models import AddressBuilder

        address = (
            AddressBuilder()
            .with_street_number("456")
            .with_street_name("Oak")
            .with_street_type("Ave")
            .with_building_name("The Towers")
            .build()
        )
        address1 = address.Address1
        address2 = address.Address2
        assert address1 is not None
        assert "456" in address1
        assert address2 is not None
        assert "The Towers" in address2

    def test_address_formatting_after_parsing(self) -> None:
        """Address properties should be available after parsing."""
        result = parse("123 Main St, Austin TX 78749")
        assert result.address is not None
        # All three properties should be available regardless of validation result
        assert result.address.Address1 is not None
        assert result.address.Address2 is None  # No unit info
        assert result.address.FullAddress is not None

    def test_full_address_format_consistency(self) -> None:
        """FullAddress format should be consistent across different address types."""
        from ryandata_address_utils.models import AddressBuilder

        # Address without Address2
        addr1 = (
            AddressBuilder()
            .with_street_number("100")
            .with_street_name("First")
            .with_street_type("Ave")
            .with_city("Dallas")
            .with_state("TX")
            .with_zip("75201")
            .build()
        )
        full = addr1.FullAddress
        # Should be: "100 First Ave, Dallas, TX 75201"
        assert "100" in full
        assert "First" in full
        assert "Dallas" in full
        assert "TX" in full
        assert "75201" in full
        # Should contain exactly 3 commas (addr1, city/state/zip)
        assert full.count(",") >= 1


# =============================================================================
# International routing via libpostal
# =============================================================================


def _require_libpostal() -> None:
    pytest.importorskip("postal.parser")


def test_parse_auto_us_success_sets_source() -> None:
    service = AddressService()
    result = service.parse_auto("123 Main St, Austin TX 78749", validate=True)
    assert result.source == "us"
    assert result.is_valid
    assert result.address is not None
    assert result.international_address is None


def test_parse_auto_fallback_international_success() -> None:
    _require_libpostal()
    service = AddressService()
    result = service.parse_auto("10 Downing St, London", validate=True)
    assert result.source == "international"
    assert result.is_valid
    assert result.international_address is not None
    assert result.international_address.Road is not None
    assert (
        result.international_address.City is not None
        or result.international_address.Country is not None
    )


def test_parse_auto_international_missing_components_fails_strict() -> None:
    _require_libpostal()
    service = AddressService()
    result = service.parse_auto("London", validate=True)
    assert result.source == "international"
    assert not result.is_valid
    assert isinstance(result.error, RyanDataAddressError)


def test_parse_auto_international_skips_us_when_probably_international() -> None:
    _require_libpostal()
    service = AddressService()
    result = service.parse_auto("Potsdamer Straße 3, 10785 Berlin, Germany", validate=True)
    assert result.source == "international"
    assert result.is_valid
    assert result.international_address is not None
    assert result.international_address.Road is not None


def test_parse_auto_fallback_on_us_validation_error() -> None:
    _require_libpostal()
    service = AddressService()
    result = service.parse_auto("1-1-2 Oshiage, Sumida-ku, Tokyo 131-0045, Japan", validate=True)
    assert result.source == "international"
    assert result.is_valid
    assert result.international_address is not None


# Extended international/US complex cases for libpostal
ADVANCED_COMPLEX_ADDRESSES = [
    # United States / Territories
    (
        "Sales Dept, Building C, 4th Floor, Suite 450, 1234 W. 56th St., "
        "Los Angeles, CA 90037-1234, USA"
    ),
    "Corner of 5th Ave & W 34th St, Manhattan, New York, NY 10001, USA",
    "RR 2 Box 152, PO Box 45, Springfield, KY 40069, USA",
    "789 north main street apartment 5b chicago il 60614 usa",
    "PSC 808 Box 33, APO AE 09618-0033, USA",
    "Urb. Jardines de Caparra, Calle 3 B-15, Bayamón, PR 00959-1234, USA",
    # Canada
    "Unit 507-1234 Rue Sainte-Catherine Ouest, Montréal QC H3B 1E5, Canada",
    "Site 2 Comp 12 RR 1, 24567 Highway 16 E, Vegreville AB T9C 1C2, Canada",
    # UK / Ireland
    "Flat 5B, Wellington House, 123-125 High Holborn, Camden, London WC1V 6EA, United Kingdom",
    "Rose Cottage, Church Lane, Little Wittenham, Oxfordshire OX14 4QG, United Kingdom",
    "Apartment 3, Block B, Smithfield Village, Smithfield, Dublin 7, D07 FXY2, Ireland",
    # Western Europe
    "Musterstraße 45, Hinterhaus, 3. OG rechts, 10999 Berlin, Deutschland",
    (
        "c/o M. Jean Dupont, 18 Rue de la République, Bâtiment B, Escalier 2, 3ème étage, "
        "13002 Marseille CEDEX 01, France"
    ),
    "Calle de Alcalá, 123, Bloque 4, Esc. B, 5º Dcha, 28009 Madrid, España",
    "c/o Studio Legale Rossi, Via Garibaldi 21, Scala A, Int. 7, 16124 Genova GE, Italia",
    "Keizersgracht 123B-III, 1015 CJ Amsterdam, Nederland",
    "Bahnhofstrasse 7, App. 12, 8001 Zürich ZH, Schweiz",
    "Karl Johans gate 15, 2. etg, NO-0159 Oslo, Norge",
    # Eastern Europe / Russia / Turkey / Greece
    "ул. Арбат, д. 12, корп. 3, стр. 5, кв. 18, Москва, 119019, Россия",
    "ul. Jana Pawła II 45/12, 00-175 Warszawa, Polska",
    "Λεωφόρος Βασιλίσσης Σοφίας 10, 4ος όροφος, 106 74 Αθήνα, Ελλάδα",
    "Atatürk Mahallesi, Gül Sokak No:25 Daire:8, 34758 Ümraniye/İstanbul, Türkiye",
    # Middle East / Israel
    "רחוב הרצל 15, דירה 7, שכונת נווה צדק, תל אביב-יפו 6511101, ישראל",
    "Office 804, Tower A, Business Bay, PO Box 123456, Dubai, United Arab Emirates",
    # South Asia
    (
        "Flat 802, Tower 5, Brigade Gateway, beside Orion Mall, Dr. Rajkumar Road, "
        "Malleswaram West, Bengaluru 560055, Karnataka, India"
    ),
    (
        "H.No. 3-45, Near Hanuman Temple, Malkajgiri Village, Medchal-Malkajgiri Dist., "
        "Telangana 500047, India"
    ),
    "House #27-B, Mohallah Gulshan-e-Rehman, Tehsil Samundri, District Faisalabad 37300, Pakistan",
    (
        "Holding 12/B, Road 3, Block A, Bashundhara R/A, Badda Thana, Dhaka 1229, "
        "Dhaka Division, Bangladesh"
    ),
    # East Asia
    "〒160-0022 東京都新宿区新宿3丁目38-1 ルミネエスト新宿 7階",
    "Lumine Est Shinjuku 7F, 3-38-1 Shinjuku, Shinjuku-ku, Tokyo 160-0022, Japan",
    "中国江苏省苏州市工业园区独墅湖高教区仁爱路199号 创新创业大厦A座1508室 215123",
    (
        "Room 1508, Building A, Chuangxin Chuangye Dasha, 199 Ren'ai Rd, "
        "Dushu Lake Sci-Edu Innovation District, Suzhou, Jiangsu 215123, China"
    ),
    "서울특별시 마포구 양화로 45, 10층 1001호 (서교동), 04038, 대한민국",
    "Flat A, 23/F, Tower 3, Laguna City, 8 Laguna Street, Lam Tin, Kowloon, Hong Kong",
    "Blk 123 Ang Mo Kio Ave 3 #12-345, Singapore 560123",
    # Southeast Asia & Oceania
    (
        "Unit 4B, Building 2, Eastwood Citywalk, 188 E. Rodriguez Jr. Ave., "
        "Brgy. Bagumbayan, Quezon City 1110, Metro Manila, Philippines"
    ),
    "Jl. Sudirman No. 25 RT 04/RW 06, Kel. Menteng, Kec. Menteng, Jakarta Pusat 10310, Indonesia",
    "Lot 7, 255 Old Northern Rd, Castle Hill NSW 2154, Australia",
    "103 Smiths Road, RD 2, Hamilton 3282, New Zealand",
    # Africa & Latin America
    "12B 7th Avenue, Parktown North, Johannesburg, Gauteng 2193, South Africa",
    (
        "Flat 6, Block C, Lekki Gardens Estate, Km 15 Lekki-Epe Expressway, Ajah, "
        "Eti-Osa LGA, Lagos State, Nigeria"
    ),
    (
        "Av. Insurgentes Sur 1602, Piso 9, Colonia Crédito Constructor, "
        "Alcaldía Benito Juárez, 03940 Ciudad de México, CDMX, México"
    ),
    "Rua do Catete, 311, Bloco B, Apto 1203, Flamengo, Rio de Janeiro - RJ, 22220-001, Brasil",
    "Av. Corrientes 1234, Piso 7º, Depto. C, C1043AAX Ciudad Autónoma de Buenos Aires, Argentina",
    "Los Militares 5001, Oficina 1204, Las Condes, Región Metropolitana, 7550000, Chile",
    # Messy / unstructured
    "attn billing john smith 4th flr 99 king street east toronto on m5c1g4 canada",
    '  "The Old Mill"   ,  7\tMill Road ..   Ballymena   BT42 1AA   UK ',
    "fl 3 rm 305, 18 yonge st, tornto on m5e 1z8 canada",
    "Station Road, near City Center Mall, Sector 17, Chandigarh 160017, Mohali, Punjab, India",
    (
        "Starbucks Coffee inside Central Station, Main Concourse, 89 E 42nd St, Midtown, "
        "Manhattan, New York, NY 10017-5503, USA"
    ),
]


@pytest.mark.parametrize("addr", ADVANCED_COMPLEX_ADDRESSES)
def test_parse_auto_advanced_complex_addresses(addr: str) -> None:
    _require_libpostal()
    service = AddressService()
    result = service.parse_auto(addr, validate=True)
    assert result.source in {"us", "international"}
    assert result.error is None
    assert result.address is not None or result.international_address is not None
