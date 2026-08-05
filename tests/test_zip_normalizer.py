"""Tests for ZipCodeNormalizer.parse() and .parse_lenient().

validate_zip5/validate_zip4/normalize already have property coverage in
test_hypothesis_properties.py; this file covers the two orchestrating
methods that call them, which had none.
"""

from __future__ import annotations

from ryandata_address_utils.core.zip_normalizer import ZipCodeNormalizer


class TestParse:
    """ZipCodeNormalizer.parse() — strict: any invalid component fails the whole result."""

    def setup_method(self) -> None:
        self.normalizer = ZipCodeNormalizer()

    def test_none_input(self) -> None:
        result = self.normalizer.parse(None)
        assert result.is_valid is False
        assert result.zip5 is None
        assert result.error == "Missing or invalid zip code"

    def test_empty_string(self) -> None:
        result = self.normalizer.parse("   ")
        assert result.is_valid is False
        assert result.error == "Empty zip code"

    def test_valid_zip5_only(self) -> None:
        result = self.normalizer.parse("75023")
        assert result.is_valid is True
        assert result.zip5 == "75023"
        assert result.zip4 is None
        assert result.full == "75023"
        assert result.error is None

    def test_valid_zip_plus_4_with_dash(self) -> None:
        result = self.normalizer.parse("75023-1234")
        assert result.is_valid is True
        assert result.zip5 == "75023"
        assert result.zip4 == "1234"
        assert result.full == "75023-1234"

    def test_valid_nine_digit_continuous(self) -> None:
        result = self.normalizer.parse("750231234")
        assert result.is_valid is True
        assert result.zip5 == "75023"
        assert result.zip4 == "1234"
        assert result.full == "75023-1234"

    def test_invalid_zip5(self) -> None:
        result = self.normalizer.parse("abcde")
        assert result.is_valid is False
        assert result.zip5 is None
        assert result.error is not None

    def test_valid_zip5_invalid_zip4_fails_strict(self) -> None:
        """Strict parse() fails the whole result if zip4 is present but malformed."""
        result = self.normalizer.parse("75023-abc")
        assert result.is_valid is False
        assert result.zip4 is None
        assert result.error is not None


class TestParseLenient:
    """ZipCodeNormalizer.parse_lenient() — keeps a valid zip5 even if zip4 is malformed."""

    def setup_method(self) -> None:
        self.normalizer = ZipCodeNormalizer()

    def test_none_input(self) -> None:
        result = self.normalizer.parse_lenient(None)
        assert result.is_valid is False
        assert result.error == "Missing or invalid zip code"

    def test_empty_string(self) -> None:
        result = self.normalizer.parse_lenient("")
        assert result.is_valid is False
        assert result.error == "Missing or invalid zip code"

    def test_valid_zip5_only(self) -> None:
        result = self.normalizer.parse_lenient("75023")
        assert result.is_valid is True
        assert result.zip5 == "75023"
        assert result.full == "75023"

    def test_valid_zip_plus_4(self) -> None:
        result = self.normalizer.parse_lenient("75023-1234")
        assert result.is_valid is True
        assert result.zip5 == "75023"
        assert result.zip4 == "1234"
        assert result.full == "75023-1234"

    def test_valid_zip5_invalid_zip4_keeps_zip5(self) -> None:
        """Unlike parse(), an invalid zip4 doesn't invalidate a valid zip5."""
        result = self.normalizer.parse_lenient("75023-abc")
        assert result.is_valid is True
        assert result.zip5 == "75023"
        assert result.zip4 is None
        assert result.full == "75023"

    def test_invalid_zip5_still_fails(self) -> None:
        """Leniency only applies to zip4 — an invalid zip5 still fails."""
        result = self.normalizer.parse_lenient("abcde")
        assert result.is_valid is False
        assert result.zip5 is None
