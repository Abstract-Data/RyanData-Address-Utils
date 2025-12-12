"""Address builder for programmatic address construction.

This module provides a fluent builder interface for constructing
Address objects with validation at build time.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from ryandata_address_utils.models.enums import ADDRESS_FIELDS, AddressField
from ryandata_address_utils.models.errors import PACKAGE_NAME, RyanDataAddressError

if TYPE_CHECKING:
    from ryandata_address_utils.models.address import Address


class AddressBuilder:
    """Builder for programmatic Address construction.

    Provides a fluent interface for building Address objects
    with validation at build time.

    Example:
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

    def __init__(self) -> None:
        self._data: dict[str, str | None] = {}

    def with_address_number_prefix(self, prefix: str) -> Self:
        """Set address number prefix (e.g., 'N' in 'N 123 Main St')."""
        self._data["AddressNumberPrefix"] = prefix
        return self

    def with_street_number(self, number: str) -> Self:
        """Set the street number."""
        self._data["AddressNumber"] = number
        return self

    def with_address_number_suffix(self, suffix: str) -> Self:
        """Set address number suffix (e.g., '1/2')."""
        self._data["AddressNumberSuffix"] = suffix
        return self

    def with_street_name_pre_modifier(self, modifier: str) -> Self:
        """Set street name pre-modifier (e.g., 'Old' in 'Old Main St')."""
        self._data["StreetNamePreModifier"] = modifier
        return self

    def with_street_pre_directional(self, directional: str) -> Self:
        """Set pre-directional (e.g., 'N', 'S', 'E', 'W')."""
        self._data["StreetNamePreDirectional"] = directional
        return self

    def with_street_pre_type(self, street_type: str) -> Self:
        """Set street pre-type (e.g., 'Avenue' in 'Avenue C')."""
        self._data["StreetNamePreType"] = street_type
        return self

    def with_street_name(self, name: str) -> Self:
        """Set the street name."""
        self._data["StreetName"] = name
        return self

    def with_street_type(self, street_type: str) -> Self:
        """Set the street type (e.g., 'St', 'Ave', 'Blvd')."""
        self._data["StreetNamePostType"] = street_type
        return self

    def with_street_post_directional(self, directional: str) -> Self:
        """Set post-directional (e.g., 'SE' in 'Main St SE')."""
        self._data["StreetNamePostDirectional"] = directional
        return self

    def with_unit_type(self, unit_type: str) -> Self:
        """Set unit type (e.g., 'Apt', 'Suite', 'Unit')."""
        self._data["SubaddressType"] = unit_type
        return self

    def with_unit_number(self, unit_number: str) -> Self:
        """Set unit number/identifier."""
        self._data["SubaddressIdentifier"] = unit_number
        return self

    def with_building_name(self, name: str) -> Self:
        """Set building name."""
        self._data["BuildingName"] = name
        return self

    def with_city(self, city: str) -> Self:
        """Set the city/place name."""
        self._data["PlaceName"] = city
        return self

    def with_state(self, state: str) -> Self:
        """Set the state name or abbreviation."""
        self._data["StateName"] = state
        return self

    def with_zip(self, zip_code: str) -> Self:
        """Set the ZIP code."""
        self._data["ZipCode"] = zip_code
        return self

    def with_po_box_type(self, box_type: str) -> Self:
        """Set PO Box type (e.g., 'PO Box')."""
        self._data["USPSBoxType"] = box_type
        return self

    def with_po_box_id(self, box_id: str) -> Self:
        """Set PO Box ID/number."""
        self._data["USPSBoxID"] = box_id
        return self

    def with_recipient(self, recipient: str) -> Self:
        """Set recipient/addressee name."""
        self._data["Recipient"] = recipient
        return self

    def with_field(self, field: str | AddressField, value: str) -> Self:
        """Set an arbitrary field by name or enum."""
        field_name = field.value if isinstance(field, AddressField) else field
        if field_name not in ADDRESS_FIELDS:
            raise RyanDataAddressError(
                "address_builder",
                f"Unknown address field: {field_name}",
                {"package": PACKAGE_NAME, "field": field_name},
            )
        self._data[field_name] = value
        return self

    def build(self) -> Address:
        """Build the Address object.

        Returns:
            Constructed Address object with computed Address1, Address2, FullAddress.
        """
        from ryandata_address_utils.models.address import Address

        return Address.model_validate(self._data)

    def build_validated(self) -> Address:
        """Build the Address object with Pydantic validation.

        Returns:
            Validated Address object.

        Raises:
            pydantic.ValidationError: If validation fails.
        """
        from ryandata_address_utils.models.address import Address

        return Address.model_validate(self._data)

    def reset(self) -> Self:
        """Reset the builder to empty state."""
        self._data = {}
        return self
