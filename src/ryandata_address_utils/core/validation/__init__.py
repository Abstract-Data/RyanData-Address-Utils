"""Generic validation infrastructure.

Provides base classes and protocols for building validators
for any model type. Re-exports from abstract_validation_base.
"""

from abstract_validation_base import (
    BaseValidator,
    CompositeValidator,
    ValidatorPipelineBuilder,
    ValidatorProtocol,
)

__all__ = ["BaseValidator", "CompositeValidator", "ValidatorProtocol", "ValidatorPipelineBuilder"]
