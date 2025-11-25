import pytest

# Skip all tests if pandas is not installed
pytest.importorskip("pandas")

import pandas as pd

from ryandata_address_utils import (
    AddressService,
    parse_address_series,
    parse_address_to_dict,
    parse_addresses,
)


class TestParseAddressToDict:
    """Test parse_address_to_dict function."""

    def test_valid_address(self) -> None:
        """Valid address should return populated dict."""
        result = parse_address_to_dict("123 Main St, Austin TX 78749")
        assert result["AddressNumber"] == "123"
        assert result["StreetName"] == "Main"
        assert result["ZipCode"] == "78749"

    def test_invalid_address_coerce(self) -> None:
        """Invalid address with errors='coerce' should return None values."""
        result = parse_address_to_dict("invalid", validate=False, errors="coerce")
        # Should have all fields as keys
        assert "AddressNumber" in result
        assert "ZipCode" in result

    def test_invalid_address_raise(self) -> None:
        """Invalid address with errors='raise' should raise."""
        with pytest.raises(ValueError):
            parse_address_to_dict("123 Main St, Austin XX 00000", errors="raise")


class TestParseAddresses:
    """Test parse_addresses DataFrame function."""

    def test_basic_parsing(self) -> None:
        """Basic DataFrame parsing should work."""
        df = pd.DataFrame(
            {
                "address": [
                    "123 Main St, Austin TX 78749",
                    "456 Oak Ave, Dallas TX 75201",
                ]
            }
        )

        result = parse_addresses(df, "address")

        assert "AddressNumber" in result.columns
        assert "StreetName" in result.columns
        assert "ZipCode" in result.columns
        assert result["AddressNumber"].iloc[0] == "123"
        assert result["AddressNumber"].iloc[1] == "456"

    def test_with_prefix(self) -> None:
        """Prefix should be added to column names."""
        df = pd.DataFrame({"address": ["123 Main St, Austin TX 78749"]})
        result = parse_addresses(df, "address", prefix="parsed_")

        assert "parsed_AddressNumber" in result.columns
        assert "parsed_ZipCode" in result.columns

    def test_inplace(self) -> None:
        """inplace=True should modify original DataFrame."""
        df = pd.DataFrame({"address": ["123 Main St, Austin TX 78749"]})
        original_id = id(df)

        result = parse_addresses(df, "address", inplace=True)

        assert id(result) == original_id
        assert "AddressNumber" in df.columns

    def test_not_inplace(self) -> None:
        """inplace=False should return a copy."""
        df = pd.DataFrame({"address": ["123 Main St, Austin TX 78749"]})
        original_id = id(df)

        result = parse_addresses(df, "address", inplace=False)

        assert id(result) != original_id
        assert "AddressNumber" not in df.columns
        assert "AddressNumber" in result.columns

    def test_handles_none_values(self) -> None:
        """None/NaN values should be handled gracefully."""
        df = pd.DataFrame({"address": ["123 Main St, Austin TX 78749", None, ""]})

        result = parse_addresses(df, "address", validate=False)

        assert result["AddressNumber"].iloc[0] == "123"
        assert result["AddressNumber"].iloc[1] is None
        assert result["AddressNumber"].iloc[2] is None

    def test_validation_off(self) -> None:
        """validate=False should skip ZIP/state validation."""
        df = pd.DataFrame({"address": ["123 Main St, Austin XX 00000"]})

        result = parse_addresses(df, "address", validate=False)
        assert result["ZipCode"].iloc[0] == "00000"

    def test_validation_on_with_errors_coerce(self) -> None:
        """errors='coerce' should set None for invalid addresses."""
        df = pd.DataFrame(
            {
                "address": [
                    "123 Main St, Austin TX 78749",  # Valid
                    "456 Oak Ave, Austin XX 00000",  # Invalid state/ZIP
                ]
            }
        )

        result = parse_addresses(df, "address", validate=True, errors="coerce")

        assert result["ZipCode"].iloc[0] == "78749"
        assert result["ZipCode"].iloc[1] is None  # Coerced to None


class TestParseAddressSeries:
    """Test parse_address_series function."""

    def test_returns_dataframe(self) -> None:
        """Should return a DataFrame with all address columns."""
        series = pd.Series(
            [
                "123 Main St, Austin TX 78749",
                "456 Oak Ave, Dallas TX 75201",
            ]
        )

        result = parse_address_series(series)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "AddressNumber" in result.columns
        assert result["AddressNumber"].iloc[0] == "123"

    def test_preserves_index(self) -> None:
        """Should preserve the original Series index."""
        series = pd.Series(["123 Main St, Austin TX 78749"], index=["custom_index"])

        result = parse_address_series(series)

        assert result.index[0] == "custom_index"


class TestAddressServicePandas:
    """Test AddressService pandas methods."""

    def test_to_series(self) -> None:
        """to_series should return a pandas Series."""
        service = AddressService()
        result = service.to_series("123 Main St, Austin TX 78749")

        assert isinstance(result, pd.Series)
        assert result["AddressNumber"] == "123"

    def test_parse_dataframe(self) -> None:
        """parse_dataframe should work."""
        service = AddressService()
        df = pd.DataFrame({"address": ["123 Main St, Austin TX 78749"]})

        result = service.parse_dataframe(df, "address")

        assert "AddressNumber" in result.columns
        assert result["AddressNumber"].iloc[0] == "123"


class TestEdgeCases:
    """Test edge cases in pandas integration."""

    def test_large_dataframe(self) -> None:
        """Should handle larger DataFrames efficiently."""
        addresses = ["123 Main St, Austin TX 78749"] * 100
        df = pd.DataFrame({"address": addresses})

        result = parse_addresses(df, "address")

        assert len(result) == 100
        assert all(result["AddressNumber"] == "123")

    def test_mixed_valid_invalid(self) -> None:
        """Should handle mix of valid and invalid addresses."""
        df = pd.DataFrame(
            {
                "address": [
                    "123 Main St, Austin TX 78749",
                    "garbage",
                    "456 Oak Ave, Dallas TX 75201",
                    None,
                    "",
                ]
            }
        )

        result = parse_addresses(df, "address", validate=False, errors="coerce")

        assert len(result) == 5
        assert result["AddressNumber"].iloc[0] == "123"
        assert result["AddressNumber"].iloc[2] == "456"

    def test_all_address_fields_present(self) -> None:
        """All address fields should be present as columns."""
        df = pd.DataFrame({"address": ["123 Main St, Austin TX 78749"]})
        result = parse_addresses(df, "address")

        expected_fields = [
            "AddressNumber",
            "StreetName",
            "StreetNamePostType",
            "PlaceName",
            "StateName",
            "ZipCode",
        ]
        for field in expected_fields:
            assert field in result.columns
