from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Self

from abstract_validation_base import ProcessEntry, ProcessLog, ValidationResult
from pydantic import AliasChoices, ConfigDict, Field, model_validator
from pydantic_core import PydanticCustomError

from ryandata_address_utils.validation.base import RyanDataValidationBase

# Package identifier for error context
PACKAGE_NAME = "ryandata_address_utils"


class RyanDataAddressError(PydanticCustomError):
    """Custom exception for ryandata_address_utils that wraps Pydantic errors.

    Inherits from PydanticCustomError to maintain full compatibility with Pydantic's
    error handling while providing package identification.

    Can wrap:
    - PydanticCustomError: Preserves original error details
    - pydantic.ValidationError: Extracts PydanticCustomError if present, otherwise converts
    """

    @classmethod
    def from_pydantic_error(cls, error: PydanticCustomError) -> RyanDataAddressError:
        """Wrap a PydanticCustomError as RyanDataAddressError.

        Args:
            error: The PydanticCustomError to wrap.

        Returns:
            RyanDataAddressError instance with same type, message, and context.
        """
        return cls(
            error.type,
            error.message_template,
            error.context,
        )

    @classmethod
    def from_validation_error(
        cls, error: Exception, context: dict | None = None
    ) -> RyanDataAddressError:
        """Wrap a pydantic.ValidationError or extract contained PydanticCustomError.

        Args:
            error: The ValidationError to wrap.
            context: Additional context to include in the error.

        Returns:
            RyanDataAddressError instance with extracted or converted error details.
        """
        from pydantic import ValidationError

        if isinstance(error, ValidationError):
            # Try to extract PydanticCustomError from ValidationError
            for err_dict in error.errors():
                if err_dict.get("type") == "address_validation":
                    # Found a custom error, extract its details
                    ctx = {
                        "package": PACKAGE_NAME,
                        **(err_dict.get("ctx", {})),
                    }
                    return cls(
                        err_dict.get("type", "validation_error"),
                        err_dict.get("msg", str(error)),
                        ctx,
                    )

            # No custom error found, create one from ValidationError
            error_messages = "; ".join(e.get("msg", str(e)) for e in error.errors())
            ctx = {
                "package": PACKAGE_NAME,
                **(context or {}),
            }
            return cls(
                "validation_error",
                error_messages,
                ctx,
            )
        else:
            # Generic exception wrapping
            ctx = {
                "package": PACKAGE_NAME,
                **(context or {}),
            }
            return cls(
                "validation_error",
                str(error),
                ctx,
            )


class RyanDataValidationError(Exception):
    """Custom exception that wraps pydantic.ValidationError with package identification.

    Inherits from Exception and wraps ValidationError to provide package context
    while maintaining access to the original error details.
    """

    def __init__(self, validation_error: Exception, context: dict | None = None):
        """Initialize RyanDataValidationError.

        Args:
            validation_error: The pydantic.ValidationError to wrap.
            context: Optional additional context to include.
        """
        from pydantic import ValidationError as PydanticValidationError

        self.original_error = validation_error
        self.context = {"package": PACKAGE_NAME, **(context or {})}

        if isinstance(validation_error, PydanticValidationError):
            self.errors_list = validation_error.errors()
            error_messages = "; ".join(e.get("msg", str(e)) for e in self.errors_list)
        else:
            self.errors_list = []
            error_messages = str(validation_error)

        super().__init__(error_messages)

    @classmethod
    def from_validation_error(
        cls, error: Exception, context: dict | None = None
    ) -> RyanDataValidationError:
        """Wrap a pydantic.ValidationError with package context.

        Args:
            error: The ValidationError to wrap.
            context: Optional additional context to include.

        Returns:
            RyanDataValidationError instance wrapping the original error.
        """
        return cls(error, context)

    def errors(self) -> list:
        """Get the list of validation errors.

        Returns:
            List of error dictionaries from the original ValidationError.
        """
        return self.errors_list

    def __str__(self) -> str:
        """String representation of the validation error."""
        return super().__str__()

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"RyanDataValidationError({self.original_error!r}, context={self.context})"


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
ADDRESS_FIELDS: list[str] = [f.value for f in AddressField] + [
    "FullZipcode",  # unified zip/postal output (US ZIP+4 or international postal)
]


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

        # Compute FullAddress (complete formatted address)
        full_parts: list[str] = []

        # Add Address1 (street address)
        if self.Address1:
            full_parts.append(self.Address1)

        # Add Address2 (unit/apartment)
        if self.Address2:
            full_parts.append(self.Address2)

        # ZIP normalization/validation using ZipCodeNormalizer
        from ryandata_address_utils.core.zip_normalizer import ZipCodeNormalizer

        zip_input = self.ZipCodeFull or self.ZipCode

        if zip_input:
            cleaned = zip_input.strip()

            # Skip strict US ZIP validation if international
            if self.IsInternational:
                self.ZipCodeFull = cleaned
                self.ZipCode = cleaned
            else:
                normalizer = ZipCodeNormalizer()
                result = normalizer.parse(cleaned)

                if not result.is_valid:
                    raise RyanDataAddressError(
                        "address_validation",
                        result.error or "Invalid ZIP code",
                        {"package": PACKAGE_NAME, "value": cleaned},
                    )

                self.ZipCode5 = result.zip5
                self.ZipCode4 = result.zip4
                self.ZipCodeFull = result.full
                # Keep legacy ZipCode populated for compatibility
                self.ZipCode = result.full

        elif self.ZipCode5:
            # If ZipCode5 provided directly, validate and normalize
            normalizer = ZipCodeNormalizer()
            zip5_cleaned, zip5_error = normalizer.validate_zip5(self.ZipCode5)
            if zip5_error:
                raise RyanDataAddressError(
                    "address_validation",
                    "ZipCode5 must be 5 digits",
                    {"package": PACKAGE_NAME, "value": self.ZipCode5},
                )

            zip4_cleaned: str | None = None
            if self.ZipCode4:
                zip4_cleaned, zip4_error = normalizer.validate_zip4(self.ZipCode4)
                if zip4_error:
                    raise RyanDataAddressError(
                        "address_validation",
                        "ZipCode4 must be 4 digits",
                        {"package": PACKAGE_NAME, "value": self.ZipCode4},
                    )

            self.ZipCode5 = zip5_cleaned
            self.ZipCode4 = zip4_cleaned
            self.ZipCodeFull = normalizer.normalize(zip5_cleaned, zip4_cleaned)  # type: ignore[arg-type]
            self.ZipCode = self.ZipCodeFull

        # Add City, State Zip line
        city_state_zip_parts: list[str] = []
        if self.PlaceName:
            city_state_zip_parts.append(self.PlaceName)

        if self.StateName and self.ZipCodeFull:
            city_state_zip_parts.append(f"{self.StateName} {self.ZipCodeFull}")
        elif self.StateName:
            city_state_zip_parts.append(self.StateName)
        elif self.ZipCodeFull:
            city_state_zip_parts.append(self.ZipCodeFull)

        if city_state_zip_parts:
            full_parts.append(", ".join(city_state_zip_parts))

        self.FullAddress = ", ".join(full_parts)

        return self

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

        def build_full_address() -> str:
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

        return cls(
            RawInput=raw_input,
            HouseNumber=house_number,
            Road=road,
            City=city,
            State=state,
            PostalCode=postal_code,
            Country=country,
            Components=components,
            FullAddress=build_full_address(),
            NormalizedAddresses=normalized_addresses or [],
        )


@dataclass
class ZipInfo:
    """Information about a US ZIP code."""

    zip_code: str
    city: str
    state_id: str
    state_name: str
    county_name: str


# ProcessLog, ProcessEntry, ValidationResult imported from abstract_validation_base


@dataclass
class ParseResult:
    """Result of address parsing with log aggregation.

    Extended to support partial validation with component-level cleaning tracking.
    ParseResult has its own ProcessLog for process-level operations (things that
    happen before/during model creation), and can aggregate logs from child models.
    """

    raw_input: str
    address: Address | None = None
    international_address: InternationalAddress | None = None
    error: Exception | None = None
    validation: ValidationResult | None = None
    source: str | None = None  # "us" or "international"
    is_international: bool | None = None
    # Process-level log (for operations before model exists)
    process_log: ProcessLog = field(default_factory=ProcessLog)
    # Partial validation tracking fields
    cleaned_components: dict[str, Any] = field(default_factory=dict)
    invalid_components: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        """Check if parsing was successful and validation passed."""
        if self.error is not None:
            return False
        if self.address is None and self.international_address is None:
            return False
        if self.validation is not None:
            return self.validation.is_valid
        return True

    @property
    def is_parsed(self) -> bool:
        """Check if parsing was successful (regardless of validation)."""
        return self.error is None and (
            self.address is not None or self.international_address is not None
        )

    def to_dict(self) -> dict[str, str | None]:
        """Convert to dictionary of address fields."""
        # Prefer international address data when available to preserve postal codes
        if self.international_address:
            return self.international_address.to_dict()
        if self.address:
            return self.address.to_dict()
        return {f: None for f in ADDRESS_FIELDS}

    def add_process_error(
        self,
        field: str,
        message: str,
        value: Any = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Track process-level errors (before model exists).

        Args:
            field: Name of the field with the error.
            message: Error message describing the issue.
            value: The problematic value (optional).
            context: Additional context dict (optional).
        """
        entry = ProcessEntry(
            entry_type="error",
            field=field,
            message=message,
            original_value=str(value) if value is not None else None,
            context=context or {},
        )
        self.process_log.errors.append(entry)

    def add_process_cleaning(
        self,
        field: str,
        original_value: Any,
        new_value: Any,
        reason: str,
        operation_type: str = "cleaning",
    ) -> None:
        """Track process-level cleaning (before model exists).

        Args:
            field: Name of the field that was cleaned.
            original_value: The original value before transformation.
            new_value: The value after transformation.
            reason: Explanation of why the cleaning was performed.
            operation_type: Category of operation (cleaning, normalization, etc.).
        """
        entry = ProcessEntry(
            entry_type="cleaning",
            field=field,
            message=reason,
            original_value=str(original_value) if original_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            context={"operation_type": operation_type},
        )
        self.process_log.cleaning.append(entry)

    def aggregate_logs(self) -> list[dict[str, Any]]:
        """Combine logs from self + all child models.

        Returns:
            List of dicts suitable for pd.DataFrame(), sorted by timestamp.
            Each entry includes a 'source' field identifying where it originated:
            - "parse_result": Process-level operations
            - "address": Operations from the Address model
            - "international_address": Operations from the InternationalAddress model
        """
        all_entries: list[dict[str, Any]] = []

        # Add process-level operations
        for entry in self.process_log.cleaning:
            all_entries.append({**entry.model_dump(), "source": "parse_result"})
        for entry in self.process_log.errors:
            all_entries.append({**entry.model_dump(), "source": "parse_result"})

        # Add model-level operations
        if self.address:
            all_entries.extend(self.address.audit_log(source="address"))
        if self.international_address:
            all_entries.extend(self.international_address.audit_log(source="international_address"))

        return sorted(all_entries, key=lambda x: x.get("timestamp", ""))

    # Backward-compatible methods (delegate to ProcessLog-based implementation)
    # These methods are deprecated but kept for compatibility with existing code.

    @property
    def cleaning_operations(self) -> list[ProcessEntry]:
        """Get all cleaning operations from the process log.

        .. deprecated::
            Access `process_log.cleaning` directly instead.

        Returns:
            List of ProcessEntry objects representing cleaning operations.
        """
        return self.process_log.cleaning

    def add_cleaning_operation(
        self,
        component: str,
        original_value: Any,
        reason: str,
        new_value: Any = None,
        operation_type: str = "cleaning",
    ) -> None:
        """Track a cleaning operation (backward-compatible method).

        .. deprecated::
            Use `add_process_cleaning()` instead.

        Args:
            component: Name of the component that was cleaned.
            original_value: The original value before transformation.
            reason: Explanation of why the cleaning was performed.
            new_value: The value after transformation (optional).
            operation_type: Category of operation (default: "cleaning").
        """
        self.add_process_cleaning(
            field=component,
            original_value=original_value,
            new_value=new_value,
            reason=reason,
            operation_type=operation_type,
        )

    def has_cleaning_operations(self) -> bool:
        """Check if any cleaning operations were performed.

        .. deprecated::
            Check `len(process_log.cleaning) > 0` directly instead.

        Returns:
            True if any cleaning operations exist.
        """
        return len(self.process_log.cleaning) > 0

    def get_cleaning_report(self) -> list[dict[str, Any]]:
        """Get cleaning operations as a list of dictionaries for export.

        .. deprecated::
            Use `aggregate_logs()` instead for a more comprehensive report.

        Returns:
            List of dicts with component, original_value, new_value, reason,
            operation_type, and timestamp fields.
        """
        return [
            {
                "component": op.field,
                "original_value": op.original_value,
                "new_value": op.new_value,
                "reason": op.message,
                "operation_type": op.context.get("operation_type", "cleaning"),
                "timestamp": op.timestamp,
            }
            for op in self.process_log.cleaning
        ]

    def get_cleaning_summary(self) -> dict[str, int]:
        """Get summary counts of cleaning operations by component.

        .. deprecated::
            Use `aggregate_logs()` with DataFrame groupby instead.

        Returns:
            Dict mapping component names to operation counts.
        """
        from collections import Counter

        return dict(Counter(op.field for op in self.process_log.cleaning))

    def get_cleaning_summary_by_type(self) -> dict[str, int]:
        """Get summary counts of cleaning operations by operation type.

        .. deprecated::
            Use `aggregate_logs()` with DataFrame groupby instead.

        Returns:
            Dict mapping operation types to counts.
        """
        from collections import Counter

        return dict(
            Counter(
                op.context.get("operation_type", "cleaning") for op in self.process_log.cleaning
            )
        )


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
