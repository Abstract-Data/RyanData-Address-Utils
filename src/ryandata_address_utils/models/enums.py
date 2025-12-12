"""Address field enumerations and constants."""

from __future__ import annotations

from enum import Enum


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
