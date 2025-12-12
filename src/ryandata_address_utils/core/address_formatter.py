"""Address formatting utilities.

This module provides a unified interface for computing formatted address strings
from address components, eliminating code duplication across models and services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ryandata_address_utils.models.address import Address


class AddressFormatter:
    """Utility class for formatting address strings from components.

    Provides static methods for computing Address1, Address2, FullAddress,
    and international address formatting. All methods are stateless and can
    be used without instantiation via the module-level singleton.

    Example:
        >>> from ryandata_address_utils.core.address_formatter import get_formatter
        >>> formatter = get_formatter()
        >>> full = formatter.compute_full_address(address)
    """

    @staticmethod
    def compute_address1(address: Address) -> str | None:
        """Compute the Address1 (street address) line from address components.

        For PO Box addresses, returns the box type and ID.
        For street addresses, returns the complete street line.

        Args:
            address: The Address object with components to format.

        Returns:
            Formatted Address1 string, or None if no street components.
        """
        address1_parts: list[str] = []

        # Check if this is a PO Box address
        if address.USPSBoxType and address.USPSBoxID:
            address1_parts.append(address.USPSBoxType)
            address1_parts.append(address.USPSBoxID)
            return " ".join(address1_parts)

        # Build street address
        if address.AddressNumberPrefix:
            address1_parts.append(address.AddressNumberPrefix)
        if address.AddressNumber:
            address1_parts.append(address.AddressNumber)
        if address.AddressNumberSuffix:
            address1_parts.append(address.AddressNumberSuffix)
        if address.StreetNamePreModifier:
            address1_parts.append(address.StreetNamePreModifier)
        if address.StreetNamePreDirectional:
            address1_parts.append(address.StreetNamePreDirectional)
        if address.StreetNamePreType:
            address1_parts.append(address.StreetNamePreType)
        if address.StreetName:
            address1_parts.append(address.StreetName)
        if address.StreetNamePostType:
            address1_parts.append(address.StreetNamePostType)
        if address.StreetNamePostDirectional:
            address1_parts.append(address.StreetNamePostDirectional)

        return " ".join(address1_parts) if address1_parts else None

    @staticmethod
    def compute_address2(address: Address) -> str | None:
        """Compute the Address2 (unit/apartment) line from address components.

        Includes subaddress (Apt, Suite, Unit), building name, and
        occupancy (Dept, Room) information.

        Args:
            address: The Address object with components to format.

        Returns:
            Formatted Address2 string, or None if no unit components.
        """
        address2_parts: list[str] = []

        # Subaddress (Apt, Suite, Unit, etc.)
        if address.SubaddressType and address.SubaddressIdentifier:
            address2_parts.append(f"{address.SubaddressType} {address.SubaddressIdentifier}")
        elif address.SubaddressType:
            address2_parts.append(address.SubaddressType)
        elif address.SubaddressIdentifier:
            address2_parts.append(address.SubaddressIdentifier)

        # Building name
        if address.BuildingName:
            address2_parts.append(address.BuildingName)

        # Occupancy (Dept, Room, etc.)
        if address.OccupancyType and address.OccupancyIdentifier:
            address2_parts.append(f"{address.OccupancyType} {address.OccupancyIdentifier}")
        elif address.OccupancyType:
            address2_parts.append(address.OccupancyType)
        elif address.OccupancyIdentifier:
            address2_parts.append(address.OccupancyIdentifier)

        return ", ".join(address2_parts) if address2_parts else None

    @staticmethod
    def compute_full_address(address: Address) -> str:
        """Compute the complete formatted address string from an Address object.

        Combines Address1, Address2, and City/State/ZIP into a single formatted string.

        Args:
            address: The Address object with components to format.

        Returns:
            Complete formatted address string.
        """
        return compute_full_address_from_parts(
            address1=address.Address1,
            address2=address.Address2,
            place_name=address.PlaceName,
            state_name=address.StateName,
            zip_code_full=address.ZipCodeFull,
        )

    @staticmethod
    def build_international_full_address(
        house_number: str | None,
        road: str | None,
        city: str | None,
        state: str | None,
        postal_code: str | None,
        country: str | None,
    ) -> str:
        """Build a full address string from international address components.

        Used by InternationalAddress.from_libpostal to format the complete
        address from libpostal-parsed components.

        Args:
            house_number: House/building number.
            road: Street/road name.
            city: City or locality.
            state: State, region, or province.
            postal_code: Postal/ZIP code.
            country: Country name.

        Returns:
            Complete formatted international address string.
        """
        line1_parts = [part for part in [house_number, road] if part]
        line1 = " ".join(line1_parts).strip()
        locality_parts = [part for part in [city, state, postal_code] if part]
        parts: list[str] = []
        if line1:
            parts.append(line1)
        if locality_parts:
            parts.append(", ".join(locality_parts))
        if country:
            parts.append(country)
        return ", ".join(parts)


def compute_full_address_from_parts(
    address1: str | None,
    address2: str | None,
    place_name: str | None,
    state_name: str | None,
    zip_code_full: str | None,
) -> str:
    """Compute the full formatted address string from individual parts.

    This is a standalone function for use when you have individual components
    rather than an Address object. Used by both Address model validation
    and AddressService to avoid duplication.

    Args:
        address1: Street address line (e.g., "123 Main St")
        address2: Unit/apartment line (e.g., "Apt 2B")
        place_name: City name
        state_name: State abbreviation or name
        zip_code_full: Full ZIP code (5-digit or ZIP+4)

    Returns:
        Complete formatted address string with components separated by commas.
    """
    full_parts: list[str] = []

    if address1:
        full_parts.append(address1)
    if address2:
        full_parts.append(address2)

    city_state_zip_parts: list[str] = []
    if place_name:
        city_state_zip_parts.append(place_name)

    if state_name and zip_code_full:
        city_state_zip_parts.append(f"{state_name} {zip_code_full}")
    elif state_name:
        city_state_zip_parts.append(state_name)
    elif zip_code_full:
        city_state_zip_parts.append(zip_code_full)

    if city_state_zip_parts:
        full_parts.append(", ".join(city_state_zip_parts))

    return ", ".join(full_parts)


def recompute_full_address(address: Address) -> None:
    """Recompute FullAddress field on an Address object in-place.

    This is a convenience function for updating the FullAddress field
    after modifying address components (e.g., after cleaning ZIP codes).

    Args:
        address: The Address object to update (modified in-place).
    """
    address.FullAddress = compute_full_address_from_parts(
        address1=address.Address1,
        address2=address.Address2,
        place_name=address.PlaceName,
        state_name=address.StateName,
        zip_code_full=address.ZipCodeFull,
    )


# Module-level singleton for convenience
_formatter: AddressFormatter | None = None


def get_formatter() -> AddressFormatter:
    """Get the singleton AddressFormatter instance.

    Returns:
        Shared AddressFormatter instance.
    """
    global _formatter
    if _formatter is None:
        _formatter = AddressFormatter()
    return _formatter
