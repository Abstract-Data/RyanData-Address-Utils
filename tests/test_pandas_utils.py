import pytest

# Skip all tests if pandas is not installed
pytest.importorskip("pandas")

import pandas as pd  # noqa: E402

from ryandata_address_utils import (  # noqa: E402
    AddressService,
    RyanDataAddressError,
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

    def test_full_zipcode_us_in_dataframe(self) -> None:
        """US ZIP+4 should populate FullZipcode in dataframe output."""
        df = pd.DataFrame({"address": ["123 Main St, Austin TX 78749-1234"]})
        result = parse_addresses(df, "address", inplace=False)

        assert "FullZipcode" in result.columns
        assert result.loc[0, "FullZipcode"] == "78749-1234"
        assert result.loc[0, "ZipCodeFull"] == "78749-1234"
        assert result.loc[0, "ZipCode5"] == "78749"
        assert result.loc[0, "ZipCode4"] == "1234"

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

    def test_errors_ignore_returns_original(self) -> None:
        """errors='ignore' should return original address string on failure."""
        df = pd.DataFrame({"address": ["invalid address"]})
        result = parse_addresses(df, "address", validate=True, errors="ignore")
        # Should include original column untouched plus parsed columns
        assert "address" in result.columns
        assert result.loc[0, "address"] == "invalid address"
        assert result["AddressNumber"].iloc[0] is None

    def test_parse_address_series_ignore_and_accessor(self) -> None:
        """Series parsing via function and accessor with errors='ignore'."""
        series = pd.Series(["invalid address", None, ""])
        df = parse_address_series(series, validate=True, errors="ignore")
        assert df["AddressNumber"].tolist() == [None, None, None]

        # Accessor path
        from ryandata_address_utils.pandas_ext import register_accessor

        register_accessor()
        parsed = series.addr.parse(validate=True, errors="ignore")
        assert parsed["AddressNumber"].tolist() == [None, None, None]

    def test_parse_dataframe_errors_raise_from_to_series(self, monkeypatch) -> None:
        """parse_dataframe should propagate errors when errors='raise'."""
        service = AddressService()

        def fake_to_series(*_args, **_kwargs):
            raise RyanDataAddressError(
                "validation_error",
                "boom",
                {"package": "ryandata_address_utils"},
            )

        monkeypatch.setattr(service, "to_series", fake_to_series)
        df = pd.DataFrame({"address": ["123 Main St, Austin TX"]})
        with pytest.raises(RyanDataAddressError):
            service.parse_dataframe(df, "address", errors="raise")

    def test_series_accessor_prefix_and_none(self) -> None:
        """Accessor parse should handle None/empty and support prefix."""
        from ryandata_address_utils.pandas_ext import register_accessor

        register_accessor()
        series = pd.Series(["123 Main St, Austin TX 78749", None, ""])
        parsed = series.addr.parse(validate=False, errors="coerce")
        assert parsed["AddressNumber"].tolist()[0] == "123"
        assert parsed["AddressNumber"].tolist()[1] is None
        assert parsed["AddressNumber"].tolist()[2] is None


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

    def test_full_zipcode_international_in_dataframe(self) -> None:
        """International postal code should surface via FullZipcode with US ZIP fields empty."""
        pytest.importorskip("postal.parser")
        service = AddressService()
        df = pd.DataFrame({"address": ["10 Downing St, London SW1A 2AA, UK"]})

        result = service.parse_dataframe(df, "address")
        assert "FullZipcode" in result.columns
        postal = result.loc[0, "FullZipcode"]
        if pd.isna(postal):
            pytest.skip("libpostal did not return a postal code for this address")
        assert result.loc[0, "ZipCode"] is None
        assert result.loc[0, "ZipCode5"] is None
        assert result.loc[0, "ZipCode4"] is None
        assert result.loc[0, "ZipCodeFull"] is None

    def test_parse_addresses_errors_raise(self) -> None:
        """errors='raise' should raise on invalid address in parse_addresses."""
        df = pd.DataFrame({"address": ["123 Main St, Austin XX 00000"]})
        with pytest.raises(RyanDataAddressError):
            parse_addresses(df, "address", errors="raise")


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
