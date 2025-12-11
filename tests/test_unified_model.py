from unittest.mock import MagicMock, patch

from ryandata_address_utils.models import Address
from ryandata_address_utils.service import AddressService, ParseResult

# Mock data for libpostal
MOCK_LIBPOSTAL_PARSE = [
    ("123", "house_number"),
    ("Main St", "road"),
    ("Apt 4B", "unit"),
    ("New York", "city"),
    ("NY", "state"),
    ("10001", "postcode"),
    ("USA", "country"),
]

MOCK_EXPANDED = ["123 Main Street Apartment 4B New York NY 10001 USA"]


class TestUnifiedAddressModel:
    def test_address_model_aliases(self):
        """Test that Address model accepts libpostal keys via aliases."""
        data = {
            "house_number": "123",
            "road": "Main St",
            "unit": "4B",
            "city": "New York",
            "state": "NY",
            "postcode": "10001",
            "country": "USA",
        }
        addr = Address.model_validate(data)

        assert addr.AddressNumber == "123"
        assert addr.StreetName == "Main St"
        assert addr.SubaddressIdentifier == "4B"
        assert addr.PlaceName == "New York"
        assert addr.StateName == "NY"
        assert addr.ZipCode == "10001"
        assert addr.Country == "USA"

    def test_address_model_mixed_keys(self):
        """Test mixing standard keys and aliases."""
        data = {
            "AddressNumber": "123",
            "road": "Main St",  # Alias
            "PlaceName": "New York",
            "state": "NY",  # Alias
        }
        addr = Address.model_validate(data)
        assert addr.AddressNumber == "123"
        assert addr.StreetName == "Main St"
        assert addr.PlaceName == "New York"
        assert addr.StateName == "NY"


@patch("ryandata_address_utils.service.lp_parse_address")
@patch("ryandata_address_utils.service.lp_expand_address")
class TestAddressServiceExpansion:
    def test_parse_international_expansion_and_hash(self, mock_expand, mock_parse):
        """Test parse_international uses expand and computes hash."""
        # Setup mocks
        mock_parse.return_value = MOCK_LIBPOSTAL_PARSE
        mock_expand.return_value = MOCK_EXPANDED

        service = AddressService()
        result = service.parse_international("123 Main St, NY", expand=True)

        assert result.is_valid
        assert result.is_international
        assert result.address is not None
        assert result.address.StreetName == "Main St"
        assert result.address.Country == "USA"

        # Check Hash
        assert result.address.AddressHash is not None
        # SHA256 of "123 Main Street Apartment 4B New York NY 10001 USA"
        assert len(result.address.AddressHash) == 64

        # Check FullAddress update from expansion
        assert result.address.FullAddress == MOCK_EXPANDED[0]

    def test_parse_auto_delegates_expansion(self, mock_expand, mock_parse):
        """Test parse_auto delegates to parse_international with expand=True."""
        mock_parse.return_value = MOCK_LIBPOSTAL_PARSE
        mock_expand.return_value = MOCK_EXPANDED

        service = AddressService()
        # Should route to international if it looks distinct or just by default fallback
        # "123 Main St" might look US, so it might try US parse first.
        # But if US parse fails or we force international look:
        result = service.parse_auto("London, UK", expand=True)

        assert result.is_international
        assert result.address is not None
        assert result.address.AddressHash is not None
        assert result.address.FullAddress == MOCK_EXPANDED[0]

    def test_us_parse_with_expansion(self, mock_expand, mock_parse):
        """Test that standard US parse also attempts expansion if available."""
        # Setup US parser mock to return something valid.
        # Here we test the service logic.

        mock_expand.return_value = ["123 Main Street"]

        # Create a mock parser that returns a basic result
        mock_parser = MagicMock()
        mock_address = Address(AddressNumber="123", StreetName="Main St")
        mock_parser.parse.return_value = ParseResult(raw_input="123 Main St", address=mock_address)

        service = AddressService(parser=mock_parser)

        # Force expand=True
        result = service.parse("123 Main St", expand=True, validate=False)

        mock_expand.assert_called_with("123 Main St")
        assert result.address is not None
        assert result.address.FullAddress == "123 Main Street"
        assert result.address.AddressHash is not None
