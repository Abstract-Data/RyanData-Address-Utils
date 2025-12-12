"""Generic error classes with package identification.

These classes provide a foundation for package-specific error handling
that can be extended by domain-specific packages.
"""

from __future__ import annotations

from pydantic_core import PydanticCustomError


class RyanDataError(PydanticCustomError):
    """Generic Pydantic error with package identification.

    Args:
        package_name: Identifier of the package raising the error.
        error_type: Type/category of the error.
        message_template: Error message (can include {placeholders}).
        context: Additional context dict merged into error context.
    """

    def __init__(
        self,
        package_name: str,
        error_type: str,
        message_template: str,
        context: dict | None = None,
    ):
        ctx = {"package": package_name, **(context or {})}
        super().__init__(error_type, message_template, ctx)

    @classmethod
    def from_pydantic_error(cls, package_name: str, error: PydanticCustomError) -> RyanDataError:
        """Wrap a PydanticCustomError with package identification."""
        return cls(
            package_name,
            error.type,
            error.message_template,
            error.context,
        )

    @classmethod
    def from_validation_error(
        cls, package_name: str, error: Exception, context: dict | None = None
    ) -> RyanDataError:
        """Wrap a pydantic.ValidationError or extract contained PydanticCustomError."""
        from pydantic import ValidationError

        if isinstance(error, ValidationError):
            for err_dict in error.errors():
                # Try to extract custom error details
                ctx = {"package": package_name, **(err_dict.get("ctx", {}))}
                return cls(
                    package_name,
                    err_dict.get("type", "validation_error"),
                    err_dict.get("msg", str(error)),
                    ctx,
                )

            # No custom error found, create generic one
            error_messages = "; ".join(e.get("msg", str(e)) for e in error.errors())
            return cls(package_name, "validation_error", error_messages, context)
        else:
            return cls(package_name, "validation_error", str(error), context)


class RyanDataValidationError(Exception):
    """Exception wrapper for pydantic.ValidationError with package identification.

    Provides access to the original error while adding package context.
    """

    def __init__(
        self,
        package_name: str,
        validation_error: Exception,
        context: dict | None = None,
    ):
        from pydantic import ValidationError as PydanticValidationError

        self.package_name = package_name
        self.original_error = validation_error
        self.context = {"package": package_name, **(context or {})}

        if isinstance(validation_error, PydanticValidationError):
            self.errors_list = validation_error.errors()
            error_messages = "; ".join(e.get("msg", str(e)) for e in self.errors_list)
        else:
            self.errors_list = []
            error_messages = str(validation_error)

        super().__init__(error_messages)

    @classmethod
    def from_validation_error(
        cls, package_name: str, error: Exception, context: dict | None = None
    ) -> RyanDataValidationError:
        """Wrap a pydantic.ValidationError with package context."""
        return cls(package_name, error, context)

    def errors(self) -> list:
        """Get the list of validation errors."""
        return self.errors_list

    def __repr__(self) -> str:
        return f"RyanDataValidationError({self.original_error!r}, context={self.context})"
