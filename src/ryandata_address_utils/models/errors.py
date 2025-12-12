"""Address-specific error classes.

These classes provide package-specific error handling for address validation
and parsing operations.
"""

from __future__ import annotations

from pydantic_core import PydanticCustomError

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
