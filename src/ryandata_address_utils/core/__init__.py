"""RyanData Address Utils Core - Reusable validation and cleaning utilities.

This module contains generic, domain-agnostic components that can be used
by other packages requiring validation, error tracking, and data cleaning.

Usage:
    from ryandata_address_utils.core import (
        # Process logging (preferred for new code)
        ProcessEntry,
        ProcessLog,
        # Legacy cleaning (deprecated, kept for compatibility)
        CleaningOperation,
        CleaningMixin,
        CleaningTracker,
        # Validation
        ValidationError,
        ValidationResult,
        RyanDataError,
        RyanDataValidationError,
        BaseValidator,
        CompositeValidator,
        ValidatorProtocol,
    )
"""

from __future__ import annotations

from ryandata_address_utils.core.address_formatter import (
    AddressFormatter,
    compute_full_address_from_parts,
    get_formatter,
    recompute_full_address,
)
from ryandata_address_utils.core.cleaning import (
    CleaningMixin,
    CleaningOperation,
    CleaningTracker,
)
from ryandata_address_utils.core.errors import RyanDataError, RyanDataValidationError
from ryandata_address_utils.core.factory import PluginFactory
from ryandata_address_utils.core.process_log import ProcessEntry, ProcessLog
from ryandata_address_utils.core.results import ValidationError, ValidationResult
from ryandata_address_utils.core.tracking import TransformationTracker
from ryandata_address_utils.core.validation import (
    BaseValidator,
    CompositeValidator,
    ValidatorProtocol,
)
from ryandata_address_utils.core.zip_normalizer import (
    ZipCodeNormalizer,
    ZipCodeResult,
    get_zip_normalizer,
)

__all__ = [
    # Errors
    "RyanDataError",
    "RyanDataValidationError",
    # Results
    "ValidationError",
    "ValidationResult",
    # Process logging (preferred for new code)
    "ProcessEntry",
    "ProcessLog",
    # Cleaning (deprecated, kept for compatibility)
    "CleaningOperation",
    "CleaningMixin",
    "CleaningTracker",
    # Transformation tracking
    "TransformationTracker",
    # Validation
    "BaseValidator",
    "CompositeValidator",
    "ValidatorProtocol",
    # ZIP code normalization
    "ZipCodeNormalizer",
    "ZipCodeResult",
    "get_zip_normalizer",
    # Factory
    "PluginFactory",
    # Address formatting
    "AddressFormatter",
    "compute_full_address_from_parts",
    "get_formatter",
    "recompute_full_address",
]
