"""Generic validation infrastructure.

Provides base classes and protocols for building validators
for any model type.
"""

from ryandata_address_utils.core.validation.base import BaseValidator
from ryandata_address_utils.core.validation.composite import CompositeValidator
from ryandata_address_utils.core.validation.protocols import ValidatorProtocol

__all__ = ["BaseValidator", "CompositeValidator", "ValidatorProtocol"]
