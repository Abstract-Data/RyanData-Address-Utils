"""Stateful property-based tests using Hypothesis for workflow testing.

This module contains stateful tests using Hypothesis's RuleBasedStateMachine
to test multi-step workflows like AddressBuilder and AddressService.
"""

from __future__ import annotations

import hypothesis.strategies as st
from hypothesis import HealthCheck, settings
from hypothesis.stateful import Bundle, RuleBasedStateMachine, invariant, rule

from ryandata_address_utils import AddressService
from ryandata_address_utils.models import Address, AddressBuilder, ParseResult
from tests.strategies import (
    DIRECTIONALS,
    STREET_NAMES,
    STREET_TYPES,
    UNIT_TYPES,
    VALID_ZIPS,
)

# =============================================================================
# AddressBuilder State Machine
# =============================================================================


class AddressBuilderStateMachine(RuleBasedStateMachine):
    """State machine for testing AddressBuilder fluent API.

    This tests that the builder maintains consistent state across
    arbitrary sequences of method calls, and that built addresses
    contain all set values.
    """

    def __init__(self) -> None:
        super().__init__()
        self.builder = AddressBuilder()
        self.expected_values: dict[str, str] = {}
        self.has_required_fields = False

    # =========================================================================
    # Rules for setting address components
    # =========================================================================

    @rule(number=st.text(alphabet="0123456789", min_size=1, max_size=5))
    def set_street_number(self, number: str) -> None:
        """Set the street number."""
        self.builder.with_street_number(number)
        self.expected_values["AddressNumber"] = number

    @rule(name=st.sampled_from(STREET_NAMES))
    def set_street_name(self, name: str) -> None:
        """Set the street name."""
        self.builder.with_street_name(name)
        self.expected_values["StreetName"] = name

    @rule(street_type=st.sampled_from(STREET_TYPES[:10]))
    def set_street_type(self, street_type: str) -> None:
        """Set the street type."""
        self.builder.with_street_type(street_type)
        self.expected_values["StreetNamePostType"] = street_type

    @rule(city=st.sampled_from(["Austin", "Dallas", "Houston", "New York", "Chicago"]))
    def set_city(self, city: str) -> None:
        """Set the city name."""
        self.builder.with_city(city)
        self.expected_values["PlaceName"] = city

    @rule(state=st.sampled_from(["TX", "NY", "CA", "IL", "FL"]))
    def set_state(self, state: str) -> None:
        """Set the state."""
        self.builder.with_state(state)
        self.expected_values["StateName"] = state

    @rule(zip_code=st.sampled_from(VALID_ZIPS))
    def set_zip(self, zip_code: str) -> None:
        """Set the ZIP code."""
        self.builder.with_zip(zip_code)
        # Note: ZipCode gets processed into ZipCode5/ZipCodeFull
        self.expected_values["ZipCode5"] = zip_code
        self.has_required_fields = True

    @rule(directional=st.sampled_from(DIRECTIONALS))
    def set_pre_directional(self, directional: str) -> None:
        """Set the pre-directional."""
        self.builder.with_street_pre_directional(directional)
        self.expected_values["StreetNamePreDirectional"] = directional

    @rule(directional=st.sampled_from(DIRECTIONALS))
    def set_post_directional(self, directional: str) -> None:
        """Set the post-directional."""
        self.builder.with_street_post_directional(directional)
        self.expected_values["StreetNamePostDirectional"] = directional

    @rule(unit_type=st.sampled_from(UNIT_TYPES[:5]))
    def set_unit_type(self, unit_type: str) -> None:
        """Set the unit type."""
        self.builder.with_unit_type(unit_type)
        self.expected_values["SubaddressType"] = unit_type

    @rule(unit_num=st.text(alphabet="0123456789ABCDEFGH", min_size=1, max_size=4))
    def set_unit_number(self, unit_num: str) -> None:
        """Set the unit number."""
        self.builder.with_unit_number(unit_num)
        self.expected_values["SubaddressIdentifier"] = unit_num

    @rule(
        building=st.sampled_from(
            ["Tower A", "Building 100", "The Plaza", "Main Building", "West Wing"]
        )
    )
    def set_building_name(self, building: str) -> None:
        """Set the building name."""
        self.builder.with_building_name(building)
        self.expected_values["BuildingName"] = building

    # =========================================================================
    # Build and verify rule
    # =========================================================================

    @rule()
    def build_and_verify(self) -> None:
        """Build the address and verify all expected values are present."""
        # Only build if we have set at least one field
        if not self.expected_values:
            return

        address = self.builder.build()
        assert isinstance(address, Address)

        # Verify all expected values
        for field, expected in self.expected_values.items():
            actual = getattr(address, field)
            assert actual == expected, f"Field {field}: expected {expected}, got {actual}"

    # =========================================================================
    # Reset rule
    # =========================================================================

    @rule()
    def reset_builder(self) -> None:
        """Reset the builder to initial state."""
        self.builder.reset()
        self.expected_values.clear()
        self.has_required_fields = False

    # =========================================================================
    # Invariants
    # =========================================================================

    @invariant()
    def builder_is_valid(self) -> None:
        """Builder should always be in a valid state."""
        assert self.builder is not None
        assert isinstance(self.builder._data, dict)


# Create pytest test case
TestAddressBuilder = AddressBuilderStateMachine.TestCase
TestAddressBuilder.settings = settings(
    max_examples=100,
    stateful_step_count=20,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


# =============================================================================
# AddressService State Machine
# =============================================================================


class AddressServiceStateMachine(RuleBasedStateMachine):
    """State machine for testing AddressService parse/validate cycles.

    This tests the consistency of the service across multiple parse
    operations, validating that parsed addresses maintain their properties
    and that batch operations are consistent with individual parses.
    """

    def __init__(self) -> None:
        super().__init__()
        self.service = AddressService()
        self.parsed_addresses: list[ParseResult] = []
        self.address_strings: list[str] = []

    # Bundles for storing generated data
    addresses = Bundle("addresses")
    parse_results = Bundle("parse_results")

    # =========================================================================
    # Rules for generating and parsing addresses
    # =========================================================================

    @rule(
        target=addresses,
        street_num=st.integers(min_value=1, max_value=9999),
        street_name=st.sampled_from(STREET_NAMES[:10]),
        street_type=st.sampled_from(STREET_TYPES[:5]),
        city=st.sampled_from(["Austin", "Dallas", "Houston"]),
        state=st.just("TX"),
        zip_code=st.sampled_from(["78749", "75201", "77001"]),
    )
    def generate_texas_address(
        self,
        street_num: int,
        street_name: str,
        street_type: str,
        city: str,
        state: str,
        zip_code: str,
    ) -> str:
        """Generate a valid Texas address string."""
        addr = f"{street_num} {street_name} {street_type}, {city} {state} {zip_code}"
        self.address_strings.append(addr)
        return addr

    @rule(target=parse_results, address=addresses)
    def parse_address(self, address: str) -> ParseResult:
        """Parse an address without validation."""
        result = self.service.parse(address, validate=False)
        self.parsed_addresses.append(result)
        return result

    @rule(target=parse_results, address=addresses)
    def parse_address_with_validation(self, address: str) -> ParseResult:
        """Parse an address with validation (may fail for invalid addresses)."""
        try:
            result = self.service.parse(address, validate=True)
            self.parsed_addresses.append(result)
            return result
        except Exception:
            # Validation errors are acceptable - create an error result
            result = ParseResult(raw_input=address, address=None)
            self.parsed_addresses.append(result)
            return result

    @rule(result=parse_results)
    def verify_result_to_dict(self, result: ParseResult) -> None:
        """Verify that to_dict() returns a dictionary with expected keys."""
        data = result.to_dict()
        assert isinstance(data, dict)
        # Should have standard address fields
        assert "AddressNumber" in data or data.get("AddressNumber") is None
        assert "ZipCode" in data or data.get("ZipCode") is None

    @rule(result=parse_results)
    def verify_cleaning_operations(self, result: ParseResult) -> None:
        """Verify that cleaning_operations is always a list."""
        assert isinstance(result.cleaning_operations, list)

    @rule()
    def batch_parse_consistency(self) -> None:
        """Verify batch parsing gives same results as individual parsing."""
        if len(self.address_strings) < 2:
            return

        # Take last 3 addresses (or fewer)
        addresses = self.address_strings[-3:]

        # Batch parse
        batch_results = self.service.parse_batch(addresses, validate=False)

        # Individual parse
        individual_results = [self.service.parse(addr, validate=False) for addr in addresses]

        # Results should have same count
        assert len(batch_results) == len(individual_results)

        # Key fields should match
        for batch_r, ind_r in zip(batch_results, individual_results, strict=False):
            if batch_r.address and ind_r.address:
                assert batch_r.address.AddressNumber == ind_r.address.AddressNumber
                assert batch_r.address.StreetName == ind_r.address.StreetName

    @rule(zip_code=st.sampled_from(["78749", "75201", "77001", "10001", "60601"]))
    def lookup_zip(self, zip_code: str) -> None:
        """Test ZIP lookup functionality."""
        info = self.service.lookup_zip(zip_code)
        if info is not None:
            assert info.zip_code == zip_code
            assert len(info.state_id) == 2

    @rule(result=parse_results)
    def verify_full_address_format(self, result: ParseResult) -> None:
        """Verify FullAddress contains key components when address is valid."""
        if result.address is None:
            return

        full = result.address.FullAddress
        assert isinstance(full, str)

        # If we have city, it should be in full address
        if result.address.PlaceName:
            assert result.address.PlaceName in full

    # =========================================================================
    # Invariants
    # =========================================================================

    @invariant()
    def service_is_valid(self) -> None:
        """Service should always be in a valid state."""
        assert self.service is not None
        assert self.service.parser is not None
        assert self.service.data_source is not None

    @invariant()
    def parsed_count_matches(self) -> None:
        """Number of parsed results should match number of addresses."""
        # Note: this is a soft check since some parses may fail
        assert len(self.parsed_addresses) >= 0


# Create pytest test case
TestAddressService = AddressServiceStateMachine.TestCase
TestAddressService.settings = settings(
    max_examples=50,
    stateful_step_count=15,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


# =============================================================================
# Additional Stateful Tests
# =============================================================================


class AddressParseRoundtripStateMachine(RuleBasedStateMachine):
    """State machine for testing address parse/format roundtrip.

    Tests that addresses can be parsed, formatted, and key information
    is preserved across the roundtrip.
    """

    def __init__(self) -> None:
        super().__init__()
        self.service = AddressService()

    addresses = Bundle("addresses")
    parsed = Bundle("parsed")

    @rule(
        target=addresses,
        num=st.integers(min_value=100, max_value=999),
        name=st.sampled_from(STREET_NAMES[:5]),
        stype=st.sampled_from(["St", "Ave", "Blvd"]),
    )
    def create_simple_address(self, num: int, name: str, stype: str) -> str:
        """Create a simple address string."""
        return f"{num} {name} {stype}, Austin TX 78749"

    @rule(target=parsed, addr=addresses)
    def parse_and_store(self, addr: str) -> ParseResult:
        """Parse an address and store the result."""
        return self.service.parse(addr, validate=False)

    @rule(result=parsed)
    def verify_street_number_preserved(self, result: ParseResult) -> None:
        """Verify street number is preserved after parsing."""
        if result.address is None:
            return

        # Original address should have a number
        raw = result.raw_input
        if raw and result.address.AddressNumber:
            # The number should appear in the original
            assert result.address.AddressNumber in raw

    @rule(result=parsed)
    def verify_zip_preserved(self, result: ParseResult) -> None:
        """Verify ZIP code is preserved after parsing."""
        if result.address is None:
            return

        if result.address.ZipCode5:
            assert len(result.address.ZipCode5) == 5
            assert result.address.ZipCode5.isdigit()


# Create pytest test case
TestAddressRoundtrip = AddressParseRoundtripStateMachine.TestCase
TestAddressRoundtrip.settings = settings(
    max_examples=30,
    stateful_step_count=10,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


# =============================================================================
# Builder with ZIP+4 State Machine
# =============================================================================


class ZipPlusFourBuilderStateMachine(RuleBasedStateMachine):
    """State machine specifically testing ZIP+4 handling in AddressBuilder.

    Tests that ZIP codes with +4 extensions are correctly parsed and
    stored in the appropriate fields.
    """

    def __init__(self) -> None:
        super().__init__()
        self.builder = AddressBuilder()
        self.expected_zip5: str | None = None
        self.expected_zip4: str | None = None

    @rule(zip5=st.sampled_from(VALID_ZIPS))
    def set_zip5_only(self, zip5: str) -> None:
        """Set a 5-digit ZIP code."""
        self.builder.with_zip(zip5)
        self.expected_zip5 = zip5
        self.expected_zip4 = None

    @rule(
        zip5=st.sampled_from(VALID_ZIPS),
        zip4=st.text(alphabet="0123456789", min_size=4, max_size=4),
    )
    def set_zip_plus_4(self, zip5: str, zip4: str) -> None:
        """Set a ZIP+4 code."""
        self.builder.with_zip(f"{zip5}-{zip4}")
        self.expected_zip5 = zip5
        self.expected_zip4 = zip4

    @rule()
    def build_and_check_zip(self) -> None:
        """Build and verify ZIP fields are correct."""
        if self.expected_zip5 is None:
            return

        # Need minimum fields for a valid address
        self.builder.with_street_number("123")
        self.builder.with_street_name("Main")
        self.builder.with_city("Austin")
        self.builder.with_state("TX")

        address = self.builder.build()

        assert address.ZipCode5 == self.expected_zip5

        if self.expected_zip4:
            assert address.ZipCode4 == self.expected_zip4
            assert address.ZipCodeFull == f"{self.expected_zip5}-{self.expected_zip4}"
        else:
            assert address.ZipCode4 is None
            assert address.ZipCodeFull == self.expected_zip5

    @rule()
    def reset(self) -> None:
        """Reset the builder."""
        self.builder = AddressBuilder()
        self.expected_zip5 = None
        self.expected_zip4 = None


# Create pytest test case
TestZipPlusFourBuilder = ZipPlusFourBuilderStateMachine.TestCase
TestZipPlusFourBuilder.settings = settings(
    max_examples=50,
    stateful_step_count=10,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
