"""Address model classes.

This module contains the Address and InternationalAddress Pydantic models
for representing parsed address data.
"""

from __future__ import annotations

from typing import Self

from pydantic import AliasChoices, ConfigDict, Field, model_validator

from ryandata_address_utils.core import ValidationResult
from ryandata_address_utils.core.address_formatter import (
    AddressFormatter,
    compute_full_address_from_parts,
)
from ryandata_address_utils.core.address_formatter import (
    recompute_full_address as _recompute_full_address_impl,
)
from ryandata_address_utils.models.errors import PACKAGE_NAME, RyanDataAddressError
from ryandata_address_utils.validation.base import RyanDataValidationBase


class Address(RyanDataValidationBase):
    """Parsed US address components.

    This model represents a parsed US address with all possible
    components. Validation of ZIP codes and states is handled
    separately by validators, not by this model.

    Inherits from ValidationBase, providing:
    - process_log: ProcessLog field (excluded from serialization)
    - add_error(): Log an error and optionally raise ValidationError
    - add_cleaning_process(): Log a cleaning/transformation operation
    - audit_log(): Export combined entries for DataFrame analysis
    """

    model_config = ConfigDict(
        extra="ignore",  # Ignore extra fields from usaddress
        str_strip_whitespace=True,  # Strip whitespace from strings
    )

    AddressNumberPrefix: str | None = Field(
        default=None,
        description="A modifier before the address number (e.g. 'N' in 'N 123 Main St')",
    )
    AddressNumber: str | None = Field(
        default=None,
        description="The primary street number of the address",
        validation_alias=AliasChoices("AddressNumber", "house_number"),
    )
    AddressNumberSuffix: str | None = Field(
        default=None,
        description="A modifier after the address number, such as a half (e.g. '1/2')",
    )
    StreetNamePreModifier: str | None = Field(
        default=None,
        description="A word or phrase before the street name, such as 'Old' in 'Old Main St'",
    )
    StreetNamePreDirectional: str | None = Field(
        default=None,
        description="A directional that comes before the street, like 'N', 'S', etc.",
    )
    StreetNamePreType: str | None = Field(
        default=None,
        description="A street type before the street name, e.g. 'Avenue' in 'Avenue C'",
    )
    StreetName: str | None = Field(
        default=None,
        description="The name of the street",
        validation_alias=AliasChoices("StreetName", "road"),
    )
    StreetNamePostType: str | None = Field(
        default=None,
        description="The type of street following the name, such as 'St', 'Ave', etc.",
    )
    StreetNamePostDirectional: str | None = Field(
        default=None,
        description="A directional that comes after the street, like 'SE' in 'Main St SE'",
    )
    SubaddressType: str | None = Field(
        default=None, description="The type of subaddress (e.g. 'Apt', 'Suite', 'Unit')"
    )
    SubaddressIdentifier: str | None = Field(
        default=None,
        description="The identifier for the subaddress (e.g. '2B', '101')",
        validation_alias=AliasChoices("SubaddressIdentifier", "unit"),
    )
    BuildingName: str | None = Field(
        default=None,
        description="The name of a building, if included in the address",
        validation_alias=AliasChoices("BuildingName", "house"),
    )
    OccupancyType: str | None = Field(
        default=None, description="The type of occupancy (e.g. 'Dept', 'Room')"
    )
    OccupancyIdentifier: str | None = Field(
        default=None, description="The identifier for the occupancy (e.g. 'Dept 34', 'Rm 2')"
    )
    CornerOf: str | None = Field(
        default=None,
        description="Specifies if the address references the corner of two streets",
    )
    LandmarkName: str | None = Field(
        default=None, description="A landmark referenced in the address"
    )
    PlaceName: str | None = Field(
        default=None,
        description="The city or place name",
        validation_alias=AliasChoices("PlaceName", "city"),
    )
    StateName: str | None = Field(
        default=None,
        description="The abbreviated or full name of the state",
        validation_alias=AliasChoices("StateName", "state"),
    )
    # Legacy ZIP field (backwards compatibility)
    ZipCode: str | None = Field(
        default=None,
        description="The postal ZIP code",
        validation_alias=AliasChoices("ZipCode", "postcode"),
    )
    # New ZIP fields
    ZipCode5: str | None = Field(default=None, description="5-digit ZIP")
    ZipCode4: str | None = Field(default=None, description="ZIP+4 extension")
    ZipCodeFull: str | None = Field(default=None, description="Full ZIP (5 or 5-4)")
    USPSBoxType: str | None = Field(
        default=None, description="The type of post office box (e.g. 'PO Box')"
    )
    USPSBoxID: str | None = Field(
        default=None,
        description="The identifier/number for the PO Box",
        validation_alias=AliasChoices("USPSBoxID", "po_box"),
    )
    USPSBoxGroupType: str | None = Field(
        default=None, description="The group type for the PO Box (if present)"
    )
    USPSBoxGroupID: str | None = Field(
        default=None, description="The group ID for the PO Box (if present)"
    )
    IntersectionSeparator: str | None = Field(
        default=None, description="The separator for intersections (e.g. '&' or 'and')"
    )
    Recipient: str | None = Field(default=None, description="The recipient or addressee's name")
    NotAddress: str | None = Field(
        default=None, description="Text identified as not part of an address"
    )
    RawInput: str | None = Field(
        default=None,
        description="The original raw input string (useful for comparing with validated output)",
    )
    IsInternational: bool | None = Field(
        default=None,
        description="True if derived from an international/libpostal parse; otherwise None",
    )
    ParserSource: str | None = Field(
        default=None,
        description="Parser backend used to produce this address (e.g., 'usaddress', 'libpostal')",
    )
    Country: str | None = Field(
        default=None,
        description="Country name (mostly for international addresses)",
        validation_alias=AliasChoices("Country", "country"),
    )
    AddressHash: str | None = Field(
        default=None,
        description="SHA-256 hash of the normalized full address",
    )
    Address1: str | None = Field(
        default=None,
        description="Formatted street address line (auto-computed from components)",
    )
    Address2: str | None = Field(
        default=None,
        description="Formatted unit/apartment line (auto-computed from components)",
    )
    FullAddress: str = Field(
        default="",
        description="Complete formatted address string (auto-computed from components)",
    )

    def to_dict(self) -> dict[str, str | None]:
        """Convert address to dictionary."""

        data = self.model_dump()
        data["FullZipcode"] = self.ZipCodeFull
        return data

    @model_validator(mode="after")
    def compute_and_validate_address(self) -> Self:
        """Compute Address1, Address2, and FullAddress from address components.

        This validator is called after all field validation and computes the
        formatted address lines from the individual components.
        """
        # Compute Address1 (street address line)
        address1_parts: list[str] = []

        # Check if this is a PO Box address
        if self.USPSBoxType and self.USPSBoxID:
            address1_parts.append(self.USPSBoxType)
            address1_parts.append(self.USPSBoxID)
            self.Address1 = " ".join(address1_parts)
        else:
            # Build street address
            if self.AddressNumberPrefix:
                address1_parts.append(self.AddressNumberPrefix)
            if self.AddressNumber:
                address1_parts.append(self.AddressNumber)
            if self.AddressNumberSuffix:
                address1_parts.append(self.AddressNumberSuffix)
            if self.StreetNamePreModifier:
                address1_parts.append(self.StreetNamePreModifier)
            if self.StreetNamePreDirectional:
                address1_parts.append(self.StreetNamePreDirectional)
            if self.StreetNamePreType:
                address1_parts.append(self.StreetNamePreType)
            if self.StreetName:
                address1_parts.append(self.StreetName)
            if self.StreetNamePostType:
                address1_parts.append(self.StreetNamePostType)
            if self.StreetNamePostDirectional:
                address1_parts.append(self.StreetNamePostDirectional)

            self.Address1 = " ".join(address1_parts) if address1_parts else None

        # Compute Address2 (unit/apartment line)
        address2_parts: list[str] = []

        # Subaddress (Apt, Suite, Unit, etc.)
        if self.SubaddressType and self.SubaddressIdentifier:
            address2_parts.append(f"{self.SubaddressType} {self.SubaddressIdentifier}")
        elif self.SubaddressType:
            address2_parts.append(self.SubaddressType)
        elif self.SubaddressIdentifier:
            address2_parts.append(self.SubaddressIdentifier)

        # Building name
        if self.BuildingName:
            address2_parts.append(self.BuildingName)

        # Occupancy (Dept, Room, etc.)
        if self.OccupancyType and self.OccupancyIdentifier:
            address2_parts.append(f"{self.OccupancyType} {self.OccupancyIdentifier}")
        elif self.OccupancyType:
            address2_parts.append(self.OccupancyType)
        elif self.OccupancyIdentifier:
            address2_parts.append(self.OccupancyIdentifier)

        self.Address2 = ", ".join(address2_parts) if address2_parts else None

        # ZIP normalization/validation
        zip_input = self.ZipCodeFull or self.ZipCode

        def validate_zip_parts(zip5: str, zip4: str | None) -> tuple[str, str | None, str]:
            if not zip5.isdigit() or len(zip5) != 5:
                raise RyanDataAddressError(
                    "address_validation",
                    "ZipCode5 must be 5 digits",
                    {"package": PACKAGE_NAME, "value": zip5},
                )
            if zip4 is not None:
                if not zip4.isdigit() or len(zip4) != 4:
                    raise RyanDataAddressError(
                        "address_validation",
                        "ZipCode4 must be 4 digits",
                        {"package": PACKAGE_NAME, "value": zip4},
                    )
                full = f"{zip5}-{zip4}"
            else:
                full = zip5
            return zip5, zip4, full

        if zip_input:
            cleaned = zip_input.strip()

            # Skip strict US ZIP validation if international
            if self.IsInternational:
                self.ZipCodeFull = cleaned
                self.ZipCode = cleaned
            else:
                zip5: str | None = None
                zip4: str | None = None
                if "-" in cleaned:
                    parts = cleaned.split("-", 1)
                    zip5 = parts[0]
                    zip4 = parts[1] if len(parts) > 1 else None
                else:
                    if len(cleaned) == 9 and cleaned.isdigit():
                        zip5, zip4 = cleaned[:5], cleaned[5:]
                    else:
                        zip5 = cleaned
                        zip4 = None

                try:
                    zip5, zip4, zip_full = validate_zip_parts(zip5, zip4)
                    self.ZipCode5 = zip5
                    self.ZipCode4 = zip4
                    self.ZipCodeFull = zip_full
                    # Keep legacy ZipCode populated for compatibility
                    self.ZipCode = zip_full
                except RyanDataAddressError:
                    # Fallback? Or raise?
                    # Original logic raised.
                    raise
        elif self.ZipCode5:
            # If ZipCode5 provided directly
            zip5, zip4, zip_full = validate_zip_parts(self.ZipCode5, self.ZipCode4)
            self.ZipCode5 = zip5
            self.ZipCode4 = zip4
            self.ZipCodeFull = zip_full
            self.ZipCode = zip_full

        # Compute FullAddress using the shared utility function
        self.FullAddress = compute_full_address_from_parts(
            address1=self.Address1,
            address2=self.Address2,
            place_name=self.PlaceName,
            state_name=self.StateName,
            zip_code_full=self.ZipCodeFull,
        )

        return self

    def recompute_full_address(self) -> None:
        """Recompute FullAddress from current component values.

        Call this method after modifying address components (e.g., after
        cleaning/normalizing ZIP codes) to update the FullAddress field.

        Example:
            >>> address.ZipCode4 = None  # Remove invalid ZIP+4
            >>> address.ZipCodeFull = address.ZipCode5
            >>> address.recompute_full_address()  # Update FullAddress
        """
        _recompute_full_address_impl(self)

    def validate_external_results(self, validation_result: ValidationResult) -> None:
        """Validate external validation results and raise RyanDataAddressError for ZIP/state errors.

        Args:
            validation_result: Validation result from external validators.

        Raises:
            RyanDataAddressError: For ZIP code and state validation errors.
        """
        for error in validation_result.errors:
            if error.field in ("ZipCode", "StateName"):
                raise RyanDataAddressError(
                    "address_validation",
                    error.message,
                    {"package": PACKAGE_NAME, "field": error.field, "value": error.value},
                )


class InternationalAddress(RyanDataValidationBase):
    """Parsed international address components from libpostal.

    Inherits from RyanDataValidationBase, providing:
    - process_log: ProcessLog field (excluded from serialization)
    - add_error(): Log an error and optionally raise RyanDataAddressError
    - add_cleaning_process(): Log a cleaning/transformation operation
    - audit_log(): Export combined entries for DataFrame analysis
    """

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )

    RawInput: str
    HouseNumber: str | None = Field(default=None, description="House number")
    Road: str | None = Field(default=None, description="Street/road name")
    City: str | None = Field(default=None, description="City or locality")
    State: str | None = Field(default=None, description="State/region/province")
    PostalCode: str | None = Field(default=None, description="Postal/ZIP code")
    Country: str | None = Field(default=None, description="Country name")
    CountryCode: str | None = Field(default=None, description="Country code (if available)")
    FullAddress: str = Field(
        default="",
        description="Complete formatted address string derived from parsed components",
    )
    NormalizedAddresses: list[str] = Field(
        default_factory=list,
        description="libpostal normalized forms of the raw input (if available)",
    )
    Components: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Raw libpostal components (lists to preserve duplicates)",
    )

    def to_dict(self) -> dict[str, str | None]:
        """Convert international address to dictionary (excluding raw components)."""
        data = self.model_dump(exclude={"Components"})
        # For downstream consumers expecting a unified ZIP field, expose postal code as FullZipcode
        data["FullZipcode"] = self.PostalCode
        # Ensure US-specific ZIP fields are present but empty for international parses
        data.setdefault("ZipCode", None)
        data.setdefault("ZipCode5", None)
        data.setdefault("ZipCode4", None)
        data.setdefault("ZipCodeFull", None)
        return data

    @classmethod
    def from_libpostal(
        cls,
        raw_input: str,
        components: dict[str, list[str]],
        normalized_addresses: list[str] | None = None,
    ) -> InternationalAddress:
        """Build InternationalAddress from libpostal components with strict validation."""

        def join(label: str) -> str | None:
            values = components.get(label)
            if not values:
                return None
            return " ".join(values)

        if not components:
            raise RyanDataAddressError(
                "international_validation",
                "No components parsed from libpostal",
                {"package": PACKAGE_NAME, "value": raw_input},
            )

        road = join("road")
        house_number = join("house_number")
        city = join("city") or join("suburb")
        state = join("state") or join("state_district")
        postal_code = join("postcode")
        country = join("country")
        if road is None:
            street_like_labels = (
                "road",
                "house_number",
                "po_box",
                "suburb",
                "city_district",
                "neighbourhood",
                "building",
                "unit",
                "level",
                "staircase",
                "entrance",
            )
            for label in street_like_labels:
                candidate = join(label)
                if candidate:
                    road = candidate
                    break

        if not (city or state or postal_code or country):
            raise RyanDataAddressError(
                "international_validation",
                "International address missing location components",
                {"package": PACKAGE_NAME, "value": raw_input},
            )
        if road is None:
            raise RyanDataAddressError(
                "international_validation",
                "International address missing road component",
                {"package": PACKAGE_NAME, "value": raw_input},
            )

        # Use the shared formatter for building the full address
        full_address = AddressFormatter.build_international_full_address(
            house_number=house_number,
            road=road,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
        )

        return cls(
            RawInput=raw_input,
            HouseNumber=house_number,
            Road=road,
            City=city,
            State=state,
            PostalCode=postal_code,
            Country=country,
            Components=components,
            FullAddress=full_address,
            NormalizedAddresses=normalized_addresses or [],
        )
