"""Address models package.

This package contains all address-related models, dataclasses, and builders.

Re-exports all public symbols for backward compatibility with the original
monolithic models.py module.
"""

from __future__ import annotations

# Re-export ValidationResult from core for backward compatibility
# (some code may have imported it from models)
from ryandata_address_utils.core import ValidationResult
from ryandata_address_utils.models.address import (
    Address,
    InternationalAddress,
)
from ryandata_address_utils.models.builder import (
    AddressBuilder,
)
from ryandata_address_utils.models.enums import (
    ADDRESS_FIELDS,
    AddressField,
)

# Import from submodules - order matters for avoiding circular imports
from ryandata_address_utils.models.errors import (
    PACKAGE_NAME,
    RyanDataAddressError,
    RyanDataValidationError,
)
from ryandata_address_utils.models.results import (
    ParseResult,
    ZipInfo,
)

__all__ = [
    # Errors
    "PACKAGE_NAME",
    "RyanDataAddressError",
    "RyanDataValidationError",
    # Enums and constants
    "AddressField",
    "ADDRESS_FIELDS",
    # Address models
    "Address",
    "InternationalAddress",
    # Results
    "ParseResult",
    "ZipInfo",
    # Builder
    "AddressBuilder",
    # Re-exported from core
    "ValidationResult",
]
