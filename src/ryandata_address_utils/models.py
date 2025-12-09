from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Self


class AddressField(str, Enum):
    """Enumeration of all address component fields."""

    ADDRESS_NUMBER_PREFIX = "AddressNumberPrefix"
    ADDRESS_NUMBER = "AddressNumber"
    ADDRESS_NUMBER_SUFFIX = "AddressNumberSuffix"
    STREET_NAME_PRE_MODIFIER = "StreetNamePreModifier"
    STREET_NAME_PRE_DIRECTIONAL = "StreetNamePreDirectional"
    STREET_NAME_PRE_TYPE = "StreetNamePreType"
    STREET_NAME = "StreetName"
    STREET_NAME_POST_TYPE = "StreetNamePostType"
    STREET_NAME_POST_DIRECTIONAL = "StreetNamePostDirectional"
    SUBADDRESS_TYPE = "SubaddressType"
    SUBADDRESS_IDENTIFIER = "SubaddressIdentifier"
    BUILDING_NAME = "BuildingName"
    OCCUPANCY_TYPE = "OccupancyType"
    OCCUPANCY_IDENTIFIER = "OccupancyIdentifier"
    CORNER_OF = "CornerOf"
    LANDMARK_NAME = "LandmarkName"
    PLACE_NAME = "PlaceName"
    STATE_NAME = "StateName"
    ZIP_CODE = "ZipCode"
    USPS_BOX_TYPE = "USPSBoxType"
    USPS_BOX_ID = "USPSBoxID"
    USPS_BOX_GROUP_TYPE = "USPSBoxGroupType"
    USPS_BOX_GROUP_ID = "USPSBoxGroupID"
    INTERSECTION_SEPARATOR = "IntersectionSeparator"
    RECIPIENT = "Recipient"
    NOT_ADDRESS = "NotAddress"


# All field names as a list (for backwards compatibility)
ADDRESS_FIELDS: list[str] = [f.value for f in AddressField]


class Address(BaseModel):
    """Parsed US address components.

    This model represents a parsed US address with all possible
    components. Validation of ZIP codes and states is handled
    separately by validators, not by this model.
    """

    model_config = ConfigDict(
        extra="ignore",  # Ignore extra fields from usaddress
        str_strip_whitespace=True,  # Strip whitespace from strings
    )

    AddressNumberPrefix: Optional[str] = Field(
        default=None,
        description="A modifier before the address number (e.g. 'N' in 'N 123 Main St')",
    )
    AddressNumber: Optional[str] = Field(
        default=None, description="The primary street number of the address"
    )
    AddressNumberSuffix: Optional[str] = Field(
        default=None,
        description="A modifier after the address number, such as a half (e.g. '1/2')",
    )
    StreetNamePreModifier: Optional[str] = Field(
        default=None,
        description="A word or phrase before the street name, such as 'Old' in 'Old Main St'",
    )
    StreetNamePreDirectional: Optional[str] = Field(
        default=None,
        description="A directional that comes before the street, like 'N', 'S', etc.",
    )
    StreetNamePreType: Optional[str] = Field(
        default=None,
        description="A street type before the street name, e.g. 'Avenue' in 'Avenue C'",
    )
    StreetName: Optional[str] = Field(default=None, description="The name of the street")
    StreetNamePostType: Optional[str] = Field(
        default=None,
        description="The type of street following the name, such as 'St', 'Ave', etc.",
    )
    StreetNamePostDirectional: Optional[str] = Field(
        default=None,
        description="A directional that comes after the street, like 'SE' in 'Main St SE'",
    )
    SubaddressType: Optional[str] = Field(
        default=None, description="The type of subaddress (e.g. 'Apt', 'Suite', 'Unit')"
    )
    SubaddressIdentifier: Optional[str] = Field(
        default=None, description="The identifier for the subaddress (e.g. '2B', '101')"
    )
    BuildingName: Optional[str] = Field(
        default=None, description="The name of a building, if included in the address"
    )
    OccupancyType: Optional[str] = Field(
        default=None, description="The type of occupancy (e.g. 'Dept', 'Room')"
    )
    OccupancyIdentifier: Optional[str] = Field(
        default=None, description="The identifier for the occupancy (e.g. 'Dept 34', 'Rm 2')"
    )
    CornerOf: Optional[str] = Field(
        default=None,
        description="Specifies if the address references the corner of two streets",
    )
    LandmarkName: Optional[str] = Field(
        default=None, description="A landmark referenced in the address"
    )
    PlaceName: Optional[str] = Field(default=None, description="The city or place name")
    StateName: Optional[str] = Field(
        default=None, description="The abbreviated or full name of the state"
    )
    ZipCode: Optional[str] = Field(default=None, description="The postal ZIP code")
    USPSBoxType: Optional[str] = Field(
        default=None, description="The type of post office box (e.g. 'PO Box')"
    )
    USPSBoxID: Optional[str] = Field(
        default=None, description="The identifier/number for the PO Box"
    )
    USPSBoxGroupType: Optional[str] = Field(
        default=None, description="The group type for the PO Box (if present)"
    )
    USPSBoxGroupID: Optional[str] = Field(
        default=None, description="The group ID for the PO Box (if present)"
    )
    IntersectionSeparator: Optional[str] = Field(
        default=None, description="The separator for intersections (e.g. '&' or 'and')"
    )
    Recipient: Optional[str] = Field(default=None, description="The recipient or addressee's name")
    NotAddress: Optional[str] = Field(
        default=None, description="Text identified as not part of an address"
    )
    Address1: Optional[str] = Field(
        default=None,
        description="Formatted street address line (auto-computed from components)",
    )
    Address2: Optional[str] = Field(
        default=None,
        description="Formatted unit/apartment line (auto-computed from components)",
    )
    FullAddress: str = Field(
        default="",
        description="Complete formatted address string (auto-computed from components)",
    )

    def to_dict(self) -> dict[str, Optional[str]]:
        """Convert address to dictionary."""
        return self.model_dump()

    @model_validator(mode="after")
    def compute_address_lines(self) -> Self:
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

        # Compute FullAddress (complete formatted address)
        full_parts: list[str] = []

        # Add Address1 (street address)
        if self.Address1:
            full_parts.append(self.Address1)

        # Add Address2 (unit/apartment)
        if self.Address2:
            full_parts.append(self.Address2)

        # Add City, State Zip line
        city_state_zip_parts: list[str] = []
        if self.PlaceName:
            city_state_zip_parts.append(self.PlaceName)

        if self.StateName and self.ZipCode:
            city_state_zip_parts.append(f"{self.StateName} {self.ZipCode}")
        elif self.StateName:
            city_state_zip_parts.append(self.StateName)
        elif self.ZipCode:
            city_state_zip_parts.append(self.ZipCode)

        if city_state_zip_parts:
            full_parts.append(", ".join(city_state_zip_parts))

        self.FullAddress = ", ".join(full_parts)

        return self


@dataclass
class ZipInfo:
    """Information about a US ZIP code."""

    zip_code: str
    city: str
    state_id: str
    state_name: str
    county_name: str


@dataclass
class ValidationError:
    """A single validation error."""

    field: str
    message: str
    value: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of address validation."""

    is_valid: bool
    errors: list[ValidationError] = field(default_factory=list)

    def add_error(self, field: str, message: str, value: Optional[str] = None) -> None:
        """Add a validation error."""
        self.errors.append(ValidationError(field=field, message=message, value=value))
        self.is_valid = False

    def merge(self, other: ValidationResult) -> ValidationResult:
        """Merge another validation result into this one."""
        if not other.is_valid:
            self.is_valid = False
            self.errors.extend(other.errors)
        return self


@dataclass
class ParseResult:
    """Result of address parsing."""

    raw_input: str
    address: Optional[Address] = None
    error: Optional[Exception] = None
    validation: Optional[ValidationResult] = None

    @property
    def is_valid(self) -> bool:
        """Check if parsing was successful and validation passed."""
        if self.error is not None or self.address is None:
            return False
        if self.validation is not None:
            return self.validation.is_valid
        return True

    @property
    def is_parsed(self) -> bool:
        """Check if parsing was successful (regardless of validation)."""
        return self.error is None and self.address is not None

    def to_dict(self) -> dict[str, Optional[str]]:
        """Convert to dictionary of address fields."""
        if self.address:
            return self.address.to_dict()
        return {f: None for f in ADDRESS_FIELDS}


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
        self._data: dict[str, Optional[str]] = {}

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

    def with_field(self, field: Union[str, AddressField], value: str) -> Self:
        """Set an arbitrary field by name or enum."""
        field_name = field.value if isinstance(field, AddressField) else field
        if field_name not in ADDRESS_FIELDS:
            raise ValueError(f"Unknown address field: {field_name}")
        self._data[field_name] = value
        return self

    def build(self) -> Address:
        """Build the Address object.

        Returns:
            Constructed Address object with computed Address1, Address2, FullAddress.
        """
        return Address.model_validate(self._data)

    def build_validated(self) -> Address:
        """Build the Address object with Pydantic validation.

        Returns:
            Validated Address object.

        Raises:
            pydantic.ValidationError: If validation fails.
        """
        return Address.model_validate(self._data)

    def reset(self) -> Self:
        """Reset the builder to empty state."""
        self._data = {}
        return self
