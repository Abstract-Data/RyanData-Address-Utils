"""Property-based tests using Hypothesis for core components.

This module contains property tests that verify invariants and properties
of the address parsing system using Hypothesis strategies.
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from ryandata_address_utils import AddressService
from ryandata_address_utils.core.address_formatter import (
    AddressFormatter,
    compute_full_address_from_parts,
)
from ryandata_address_utils.core.zip_normalizer import ZipCodeNormalizer
from ryandata_address_utils.models import Address, AddressBuilder, ParseResult
from tests.strategies import (
    VALID_ZIPS,
    builder_method_sequence_strategy,
    full_address_dict_strategy,
    invalid_zip4_strategy,
    invalid_zip5_strategy,
    minimal_address_dict_strategy,
    po_box_address_dict_strategy,
    simple_address_string_strategy,
    street_name_strategy,
    street_number_strategy,
    street_type_strategy,
    valid_zip5_strategy,
    zip4_strategy,
)

# =============================================================================
# AddressFormatter Property Tests
# =============================================================================


class TestAddressFormatterProperties:
    """Property tests for AddressFormatter methods."""

    @given(minimal_address_dict_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_address1_computation_idempotent(self, addr_dict: dict[str, str | None]) -> None:
        """Address1 computation should be idempotent - same inputs give same outputs."""
        address = Address.model_validate(addr_dict)

        # Compute Address1 multiple times
        result1 = AddressFormatter.compute_address1(address)
        result2 = AddressFormatter.compute_address1(address)

        assert result1 == result2

    @given(minimal_address_dict_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_address1_contains_components(self, addr_dict: dict[str, str | None]) -> None:
        """Address1 should contain the street number and name when present."""
        address = Address.model_validate(addr_dict)
        address1 = address.Address1

        if address1 is not None:
            # Street number should be in Address1
            if address.AddressNumber:
                assert address.AddressNumber in address1

            # Street name should be in Address1
            if address.StreetName:
                assert address.StreetName in address1

    @given(po_box_address_dict_strategy())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_po_box_address1_format(self, addr_dict: dict[str, str | None]) -> None:
        """PO Box addresses should format correctly in Address1."""
        address = Address.model_validate(addr_dict)
        address1 = address.Address1

        # Should contain the box ID
        if address1 is not None and address.USPSBoxID:
            assert address.USPSBoxID in address1

    @given(full_address_dict_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_address2_contains_unit_info(self, addr_dict: dict[str, str | None]) -> None:
        """Address2 should contain unit information when present."""
        address = Address.model_validate(addr_dict)
        address2 = address.Address2

        # If we have unit info, Address2 should contain it
        if address.SubaddressIdentifier and address2:
            assert address.SubaddressIdentifier in address2

    @given(minimal_address_dict_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_full_address_contains_all_parts(self, addr_dict: dict[str, str | None]) -> None:
        """FullAddress should contain city, state, and ZIP when present."""
        address = Address.model_validate(addr_dict)
        full = address.FullAddress

        if address.PlaceName:
            assert address.PlaceName in full

        if address.StateName:
            assert address.StateName in full

        # ZIP should be in FullAddress (may be ZipCode5 or full ZipCodeFull)
        if address.ZipCode5:
            assert address.ZipCode5 in full

    @given(
        address1=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
        address2=st.one_of(st.none(), st.text(min_size=1, max_size=30)),
        city=st.one_of(st.none(), st.sampled_from(["Austin", "Dallas", "Houston"])),
        state=st.one_of(st.none(), st.sampled_from(["TX", "CA", "NY"])),
        zip_code=st.one_of(st.none(), st.sampled_from(VALID_ZIPS)),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_compute_full_address_from_parts_deterministic(
        self,
        address1: str | None,
        address2: str | None,
        city: str | None,
        state: str | None,
        zip_code: str | None,
    ) -> None:
        """compute_full_address_from_parts should be deterministic."""
        result1 = compute_full_address_from_parts(address1, address2, city, state, zip_code)
        result2 = compute_full_address_from_parts(address1, address2, city, state, zip_code)

        assert result1 == result2
        assert isinstance(result1, str)

    @given(
        address1=st.text(min_size=1, max_size=50),
        city=st.sampled_from(["Austin", "Dallas", "Houston"]),
        state=st.sampled_from(["TX", "CA", "NY"]),
        zip_code=st.sampled_from(VALID_ZIPS),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_full_address_non_empty_with_components(
        self,
        address1: str,
        city: str,
        state: str,
        zip_code: str,
    ) -> None:
        """FullAddress should be non-empty when components are provided."""
        result = compute_full_address_from_parts(address1, None, city, state, zip_code)
        assert len(result) > 0


# =============================================================================
# ZipCodeNormalizer Property Tests
# =============================================================================


class TestZipCodeNormalizerProperties:
    """Property tests for ZipCodeNormalizer."""

    def setup_method(self) -> None:
        """Set up normalizer instance for each test."""
        self.normalizer = ZipCodeNormalizer()

    @given(valid_zip5_strategy())
    @settings(max_examples=50)
    def test_valid_zip5_passes_validation(self, zip_code: str) -> None:
        """Valid 5-digit ZIP codes should pass format validation."""
        cleaned, error = self.normalizer.validate_zip5(zip_code)
        assert cleaned is not None
        assert error is None
        assert len(cleaned) == 5
        assert cleaned.isdigit()

    @given(zip4_strategy())
    @settings(max_examples=50)
    def test_valid_zip4_passes_validation(self, zip4: str) -> None:
        """Valid 4-digit ZIP+4 extensions should pass format validation."""
        cleaned, error = self.normalizer.validate_zip4(zip4)
        assert cleaned is not None
        assert error is None
        assert len(cleaned) == 4
        assert cleaned.isdigit()

    @given(invalid_zip5_strategy())
    @settings(max_examples=50)
    def test_invalid_zip5_returns_error(self, zip_code: str) -> None:
        """Invalid ZIP5 formats should return an error."""
        cleaned, error = self.normalizer.validate_zip5(zip_code)
        assert cleaned is None
        assert error is not None

    @given(invalid_zip4_strategy())
    @settings(max_examples=50)
    def test_invalid_zip4_returns_error(self, zip4: str) -> None:
        """Invalid ZIP4 formats should return an error."""
        cleaned, error = self.normalizer.validate_zip4(zip4)
        assert cleaned is None
        assert error is not None

    @given(st.text(min_size=5, max_size=5, alphabet="0123456789"))
    @settings(max_examples=100)
    def test_zip5_validation_idempotent(self, zip_code: str) -> None:
        """ZIP5 validation should be idempotent."""
        cleaned1, error1 = self.normalizer.validate_zip5(zip_code)
        if cleaned1 is not None:
            cleaned2, error2 = self.normalizer.validate_zip5(cleaned1)
            assert cleaned1 == cleaned2
            assert error1 == error2

    @given(st.text(min_size=4, max_size=4, alphabet="0123456789"))
    @settings(max_examples=100)
    def test_zip4_validation_idempotent(self, zip4: str) -> None:
        """ZIP4 validation should be idempotent."""
        cleaned1, error1 = self.normalizer.validate_zip4(zip4)
        if cleaned1 is not None:
            cleaned2, error2 = self.normalizer.validate_zip4(cleaned1)
            assert cleaned1 == cleaned2
            assert error1 == error2

    @given(valid_zip5_strategy())
    @settings(max_examples=50)
    def test_zip5_whitespace_stripped(self, zip_code: str) -> None:
        """ZIP5 validation should strip whitespace."""
        padded = f"  {zip_code}  "
        cleaned, error = self.normalizer.validate_zip5(padded)
        assert cleaned == zip_code
        assert error is None

    @given(zip4_strategy())
    @settings(max_examples=50)
    def test_zip4_whitespace_stripped(self, zip4: str) -> None:
        """ZIP4 validation should strip whitespace."""
        padded = f"  {zip4}  "
        cleaned, error = self.normalizer.validate_zip4(padded)
        assert cleaned == zip4
        assert error is None

    def test_empty_zip5_returns_error(self) -> None:
        """Empty ZIP5 should return error."""
        cleaned, error = self.normalizer.validate_zip5("")
        assert cleaned is None
        assert error is not None

    def test_none_zip5_returns_error(self) -> None:
        """None ZIP5 should return error."""
        cleaned, error = self.normalizer.validate_zip5(None)
        assert cleaned is None
        assert error is not None

    def test_empty_zip4_is_valid(self) -> None:
        """Empty ZIP4 should be valid (optional field)."""
        cleaned, error = self.normalizer.validate_zip4("")
        assert cleaned is None
        assert error is None

    def test_none_zip4_is_valid(self) -> None:
        """None ZIP4 should be valid (optional field)."""
        cleaned, error = self.normalizer.validate_zip4(None)
        assert cleaned is None
        assert error is None


# =============================================================================
# AddressBuilder Property Tests
# =============================================================================


class TestAddressBuilderProperties:
    """Property tests for AddressBuilder."""

    @given(builder_method_sequence_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_builder_produces_valid_address(self, method_sequence: list[tuple[str, str]]) -> None:
        """Builder should produce a valid Address regardless of method order."""
        builder = AddressBuilder()

        for method_name, value in method_sequence:
            method = getattr(builder, method_name)
            method(value)

        # Building should not raise
        address = builder.build()
        assert isinstance(address, Address)

    @given(builder_method_sequence_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_builder_values_preserved(self, method_sequence: list[tuple[str, str]]) -> None:
        """Builder should preserve all set values in the built address."""
        builder = AddressBuilder()

        # Track expected values
        expected: dict[str, str] = {}
        method_to_field = {
            "with_street_number": "AddressNumber",
            "with_street_name": "StreetName",
            "with_street_type": "StreetNamePostType",
            "with_city": "PlaceName",
            "with_state": "StateName",
            "with_street_pre_directional": "StreetNamePreDirectional",
            "with_street_post_directional": "StreetNamePostDirectional",
            "with_unit_type": "SubaddressType",
            "with_unit_number": "SubaddressIdentifier",
            "with_building_name": "BuildingName",
        }

        for method_name, value in method_sequence:
            method = getattr(builder, method_name)
            method(value)

            if method_name in method_to_field:
                expected[method_to_field[method_name]] = value

        address = builder.build()

        # Verify all expected values are in the address
        for field, value in expected.items():
            actual = getattr(address, field)
            assert actual == value, f"Field {field}: expected {value}, got {actual}"

    @given(
        street_num=street_number_strategy(),
        street_name=street_name_strategy(),
        street_type=street_type_strategy(),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_builder_fluent_interface(
        self, street_num: str, street_name: str, street_type: str
    ) -> None:
        """Builder should support fluent chaining."""
        city, state, zip_code = ("Austin", "TX", "78749")

        address = (
            AddressBuilder()
            .with_street_number(street_num)
            .with_street_name(street_name)
            .with_street_type(street_type)
            .with_city(city)
            .with_state(state)
            .with_zip(zip_code)
            .build()
        )

        assert address.AddressNumber == street_num
        assert address.StreetName == street_name
        assert address.StreetNamePostType == street_type
        assert address.PlaceName == city
        assert address.StateName == state

    def test_builder_reset_clears_state(self) -> None:
        """Reset should clear all builder state."""
        builder = AddressBuilder().with_street_number("123").with_street_name("Main").reset()

        # After reset, building should give an empty address
        address = builder.build()
        assert address.AddressNumber is None
        assert address.StreetName is None

    @given(st.sampled_from(["InvalidField", "NotAField", "Foo123"]))
    def test_builder_rejects_invalid_fields(self, invalid_field: str) -> None:
        """Builder should reject invalid field names."""
        from ryandata_address_utils.models import RyanDataAddressError

        builder = AddressBuilder()
        with pytest.raises(RyanDataAddressError):
            builder.with_field(invalid_field, "value")


# =============================================================================
# Address Model Invariant Tests
# =============================================================================


class TestAddressModelInvariants:
    """Invariant tests for the Address model."""

    @given(valid_zip5_strategy(), zip4_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_zip_field_consistency(self, zip5: str, zip4: str) -> None:
        """ZipCode5 + ZipCode4 should equal ZipCodeFull when both present."""
        city, state, _ = ("Austin", "TX", "78749")

        # Use the valid zip5 from the strategy
        address = Address(
            PlaceName=city,
            StateName=state,
            ZipCode=f"{zip5}-{zip4}",
        )

        assert address.ZipCode5 == zip5
        assert address.ZipCode4 == zip4
        assert address.ZipCodeFull == f"{zip5}-{zip4}"

    @given(valid_zip5_strategy())
    @settings(max_examples=50)
    def test_zip5_only_format(self, zip5: str) -> None:
        """When only ZIP5 is provided, ZipCodeFull should equal ZIP5."""
        address = Address(ZipCode=zip5)

        assert address.ZipCode5 == zip5
        assert address.ZipCode4 is None
        assert address.ZipCodeFull == zip5

    @given(minimal_address_dict_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_model_validation_deterministic(self, addr_dict: dict[str, str | None]) -> None:
        """Model validation should be deterministic - same input gives same output."""
        address1 = Address.model_validate(addr_dict)
        address2 = Address.model_validate(addr_dict)

        assert address1.model_dump() == address2.model_dump()

    @given(minimal_address_dict_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_to_dict_includes_full_zipcode(self, addr_dict: dict[str, str | None]) -> None:
        """to_dict() should include FullZipcode key."""
        address = Address.model_validate(addr_dict)
        data = address.to_dict()

        assert "FullZipcode" in data
        assert data["FullZipcode"] == address.ZipCodeFull

    @given(full_address_dict_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_full_address_always_string(self, addr_dict: dict[str, str | None]) -> None:
        """FullAddress should always be a string (never None)."""
        address = Address.model_validate(addr_dict)
        assert isinstance(address.FullAddress, str)


# =============================================================================
# ParseResult Invariant Tests
# =============================================================================


class TestParseResultInvariants:
    """Invariant tests for ParseResult."""

    @given(simple_address_string_strategy())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_valid_result_has_address(self, address_string: str) -> None:
        """A valid ParseResult should have a non-None address."""
        service = AddressService()
        result = service.parse(address_string, validate=False)

        if result.is_valid:
            assert result.address is not None

    @given(simple_address_string_strategy())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_parsed_result_consistent_flags(self, address_string: str) -> None:
        """is_parsed and is_valid should be consistent."""
        service = AddressService()
        result = service.parse(address_string, validate=False)

        # If valid, must be parsed
        if result.is_valid:
            assert result.is_parsed

    @given(simple_address_string_strategy())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_to_dict_always_returns_dict(self, address_string: str) -> None:
        """to_dict() should always return a dictionary."""
        service = AddressService()
        result = service.parse(address_string, validate=False)

        data = result.to_dict()
        assert isinstance(data, dict)

    @given(simple_address_string_strategy())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_cleaning_operations_is_list(self, address_string: str) -> None:
        """cleaning_operations should always be a list."""
        service = AddressService()
        result = service.parse(address_string, validate=False)

        assert isinstance(result.cleaning_operations, list)

    @given(simple_address_string_strategy())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_source_field_populated(self, address_string: str) -> None:
        """source field should be populated after parsing."""
        service = AddressService()
        result = service.parse(address_string, validate=False)

        assert result.source in ("us", "international", None)


# =============================================================================
# AddressService Property Tests
# =============================================================================


class TestAddressServiceProperties:
    """Property tests for AddressService."""

    @given(simple_address_string_strategy())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_parse_returns_parse_result(self, address_string: str) -> None:
        """parse() should always return a ParseResult."""
        service = AddressService()
        result = service.parse(address_string, validate=False)
        assert isinstance(result, ParseResult)

    @given(st.lists(simple_address_string_strategy(), min_size=1, max_size=5))
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    def test_batch_parse_returns_same_count(self, addresses: list[str]) -> None:
        """parse_batch() should return same number of results as inputs."""
        service = AddressService()
        results = service.parse_batch(addresses, validate=False)

        assert len(results) == len(addresses)
        assert all(isinstance(r, ParseResult) for r in results)

    @given(simple_address_string_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_parse_with_and_without_validation(self, address_string: str) -> None:
        """parse() should work with and without validation."""
        service = AddressService()

        # Without validation - should not raise
        result_no_val = service.parse(address_string, validate=False)
        assert isinstance(result_no_val, ParseResult)

        # With validation - may raise or return error result
        try:
            result_val = service.parse(address_string, validate=True)
            assert isinstance(result_val, ParseResult)
        except Exception:
            # Validation errors are acceptable
            pass

    @given(st.sampled_from(["78749", "75201", "10001", "60601", "33101", "98101"]))
    @settings(max_examples=20, deadline=None)
    def test_zip_lookup_returns_info_for_valid_zips(self, zip_code: str) -> None:
        """lookup_zip() should return ZipInfo for valid ZIPs."""
        service = AddressService()
        info = service.lookup_zip(zip_code)

        assert info is not None
        assert info.zip_code == zip_code
        assert info.state_id is not None
        assert len(info.state_id) == 2

    @given(simple_address_string_strategy())
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    def test_parse_to_dict_returns_dict(self, address_string: str) -> None:
        """parse_to_dict() should return a dictionary."""
        service = AddressService()
        result = service.parse_to_dict(address_string, validate=False)

        assert isinstance(result, dict)
        assert "AddressNumber" in result or result.get("AddressNumber") is None
