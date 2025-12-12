"""RyanData Address Utils Core - Reusable validation and cleaning utilities.

This module contains generic, domain-agnostic components that can be used
by other packages requiring validation, error tracking, and data cleaning.

Usage:
    from ryandata_address_utils.core import (
        # Process logging (from abstract_validation_base)
        ProcessEntry,
        ProcessLog,
        # Validation (from abstract_validation_base)
        ValidationError,
        ValidationResult,
        BaseValidator,
        CompositeValidator,
        ValidatorProtocol,
        ValidatorPipelineBuilder,
        ValidationRunner,
        RowResult,
        RunnerStats,
        # Legacy cleaning (deprecated, kept for compatibility)
        CleaningOperation,
        CleaningMixin,
        CleaningTracker,
        # Errors
        RyanDataError,
        RyanDataValidationError,
    )
"""

from __future__ import annotations

from abstract_validation_base import (
    BaseValidator,
    CompositeValidator,
    ProcessEntry,
    ProcessLog,
    RowResult,
    RunnerStats,
    ValidationError,
    ValidationResult,
    ValidationRunner,
    ValidatorPipelineBuilder,
    ValidatorProtocol,
)

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
from ryandata_address_utils.core.tracking import TransformationTracker
from ryandata_address_utils.core.zip_normalizer import (
    ZipCodeNormalizer,
    ZipCodeResult,
    get_zip_normalizer,
)

__all__ = [
    # Errors
    "RyanDataError",
    "RyanDataValidationError",
    # Results (from abstract_validation_base)
    "ValidationError",
    "ValidationResult",
    # Process logging (from abstract_validation_base)
    "ProcessEntry",
    "ProcessLog",
    # Cleaning (deprecated, kept for compatibility)
    "CleaningOperation",
    "CleaningMixin",
    "CleaningTracker",
    # Transformation tracking
    "TransformationTracker",
    # Validation (from abstract_validation_base)
    "BaseValidator",
    "CompositeValidator",
    "ValidatorProtocol",
    "ValidatorPipelineBuilder",
    # ValidationRunner (from abstract_validation_base)
    "ValidationRunner",
    "RowResult",
    "RunnerStats",
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
