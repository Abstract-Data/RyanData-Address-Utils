"""ZIP code normalization and validation utilities.

Consolidates all ZIP code parsing, validation, and normalization logic
into a single, reusable module.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ZipCodeResult:
    """Result of ZIP code parsing and validation.

    Attributes:
        zip5: The 5-digit ZIP code (None if invalid).
        zip4: The 4-digit ZIP+4 extension (None if not present or invalid).
        full: The full formatted ZIP code ("12345" or "12345-6789").
        is_valid: True if the ZIP code is valid.
        error: Error message if invalid, None otherwise.
    """

    zip5: str | None
    zip4: str | None
    full: str | None
    is_valid: bool
    error: str | None


class ZipCodeNormalizer:
    """Consolidates ZIP code parsing, validation, and normalization.

    This class provides a single source of truth for all ZIP code
    operations, eliminating duplication across the codebase.

    Example:
        >>> normalizer = ZipCodeNormalizer()
        >>> result = normalizer.parse("12345-6789")
        >>> print(result.zip5)  # "12345"
        >>> print(result.zip4)  # "6789"
        >>> print(result.full)  # "12345-6789"

        >>> result = normalizer.parse("123456789")  # 9-digit continuous
        >>> print(result.full)  # "12345-6789"
    """

    @staticmethod
    def validate_zip5(zip5: str | None) -> tuple[str | None, str | None]:
        """Validate a 5-digit ZIP code.

        Args:
            zip5: The ZIP code string to validate.

        Returns:
            Tuple of (cleaned_value, error_message).
            cleaned_value is None if invalid.
            error_message is None if valid.
        """
        if not zip5 or not isinstance(zip5, str):
            return None, "Missing or invalid zip code"

        cleaned = zip5.strip()
        if len(cleaned) == 5 and cleaned.isdigit():
            return cleaned, None
        else:
            return None, f"Invalid zip5 format: {zip5}"

    @staticmethod
    def validate_zip4(zip4: str | None) -> tuple[str | None, str | None]:
        """Validate a 4-digit ZIP+4 extension.

        Args:
            zip4: The ZIP+4 extension string to validate.

        Returns:
            Tuple of (cleaned_value, error_message).
            cleaned_value is None if invalid or empty.
            error_message is None if valid or if zip4 is empty (zip4 is optional).
        """
        if not zip4:  # Zip4 is optional - empty is valid
            return None, None

        if isinstance(zip4, str):
            cleaned = zip4.strip()
            if len(cleaned) == 4 and cleaned.isdigit():
                return cleaned, None

        return None, f"Invalid zip4 format: {zip4}"

    @staticmethod
    def normalize(zip5: str, zip4: str | None = None) -> str:
        """Format ZIP code as "12345" or "12345-6789".

        Args:
            zip5: The 5-digit ZIP code.
            zip4: The optional 4-digit extension.

        Returns:
            Formatted ZIP string.
        """
        if zip4:
            return f"{zip5}-{zip4}"
        return zip5

    def parse(self, zip_string: str | None) -> ZipCodeResult:
        """Parse any ZIP format into normalized components.

        Handles the following formats:
        - 5-digit ZIP: "12345"
        - ZIP+4 with dash: "12345-6789"
        - 9-digit continuous: "123456789"

        Args:
            zip_string: The ZIP code string to parse.

        Returns:
            ZipCodeResult with parsed components and validation status.
        """
        if not zip_string or not isinstance(zip_string, str):
            return ZipCodeResult(
                zip5=None,
                zip4=None,
                full=None,
                is_valid=False,
                error="Missing or invalid zip code",
            )

        cleaned = zip_string.strip()

        if not cleaned:
            return ZipCodeResult(
                zip5=None,
                zip4=None,
                full=None,
                is_valid=False,
                error="Empty zip code",
            )

        zip5: str | None = None
        zip4: str | None = None

        # Parse based on format
        if "-" in cleaned:
            # ZIP+4 with dash: "12345-6789"
            parts = cleaned.split("-", 1)
            zip5 = parts[0]
            zip4 = parts[1] if len(parts) > 1 else None
        elif len(cleaned) == 9 and cleaned.isdigit():
            # 9-digit continuous: "123456789"
            zip5 = cleaned[:5]
            zip4 = cleaned[5:]
        else:
            # Assume 5-digit ZIP or invalid
            zip5 = cleaned
            zip4 = None

        # Validate components
        validated_zip5, zip5_error = self.validate_zip5(zip5)
        if zip5_error:
            return ZipCodeResult(
                zip5=None,
                zip4=None,
                full=None,
                is_valid=False,
                error=zip5_error,
            )

        validated_zip4: str | None = None
        zip4_error: str | None = None
        if zip4:
            validated_zip4, zip4_error = self.validate_zip4(zip4)
            if zip4_error:
                return ZipCodeResult(
                    zip5=validated_zip5,
                    zip4=None,
                    full=None,
                    is_valid=False,
                    error=zip4_error,
                )

        # Build full ZIP
        full = self.normalize(validated_zip5, validated_zip4)  # type: ignore[arg-type]

        return ZipCodeResult(
            zip5=validated_zip5,
            zip4=validated_zip4,
            full=full,
            is_valid=True,
            error=None,
        )

    def parse_lenient(self, zip_string: str | None) -> ZipCodeResult:
        """Parse ZIP code, keeping valid zip5 even if zip4 is invalid.

        This is useful for partial validation where you want to keep
        a valid 5-digit ZIP even if the +4 extension is malformed.

        Args:
            zip_string: The ZIP code string to parse.

        Returns:
            ZipCodeResult with parsed components. If zip4 is invalid,
            it will be None but zip5 may still be valid.
        """
        if not zip_string or not isinstance(zip_string, str):
            return ZipCodeResult(
                zip5=None,
                zip4=None,
                full=None,
                is_valid=False,
                error="Missing or invalid zip code",
            )

        cleaned = zip_string.strip()

        if not cleaned:
            return ZipCodeResult(
                zip5=None,
                zip4=None,
                full=None,
                is_valid=False,
                error="Empty zip code",
            )

        zip5: str | None = None
        zip4: str | None = None

        # Parse based on format
        if "-" in cleaned:
            parts = cleaned.split("-", 1)
            zip5 = parts[0]
            zip4 = parts[1] if len(parts) > 1 else None
        elif len(cleaned) == 9 and cleaned.isdigit():
            zip5 = cleaned[:5]
            zip4 = cleaned[5:]
        else:
            zip5 = cleaned
            zip4 = None

        # Validate zip5
        validated_zip5, zip5_error = self.validate_zip5(zip5)
        if zip5_error:
            return ZipCodeResult(
                zip5=None,
                zip4=None,
                full=None,
                is_valid=False,
                error=zip5_error,
            )

        # Validate zip4 leniently - keep zip5 even if zip4 is invalid
        validated_zip4: str | None = None
        if zip4:
            validated_zip4, zip4_error = self.validate_zip4(zip4)
            # Don't fail if zip4 is invalid, just set it to None

        # Build full ZIP
        full = self.normalize(validated_zip5, validated_zip4)  # type: ignore[arg-type]

        return ZipCodeResult(
            zip5=validated_zip5,
            zip4=validated_zip4,
            full=full,
            is_valid=True,
            error=None,
        )


# Module-level singleton for convenience
_default_normalizer: ZipCodeNormalizer | None = None


def get_zip_normalizer() -> ZipCodeNormalizer:
    """Get the default ZipCodeNormalizer singleton.

    Returns:
        Shared ZipCodeNormalizer instance.
    """
    global _default_normalizer
    if _default_normalizer is None:
        _default_normalizer = ZipCodeNormalizer()
    return _default_normalizer
