import httpx
import pytest

from ryandata_address_utils.remote.client import LibpostalRemoteClient, parse_remote


def test_parse_maps_us_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/parse"
        return httpx.Response(
            200,
            json={
                "mode": "us",
                "source": "us",
                "is_valid": True,
                "is_parsed": True,
                "address": {
                    "AddressNumber": "123",
                    "StreetName": "Main",
                    "StreetNamePostType": "St",
                    "RawInput": "123 Main St",
                },
                "international_address": None,
                "components": {},
                "errors": [],
            },
        )

    client = LibpostalRemoteClient(
        base_url="http://test",
        auto_start=False,
        transport=httpx.MockTransport(handler),
    )
    result = client.parse("123 Main St")

    assert result.is_valid
    assert result.address is not None
    assert result.address.StreetName == "Main"
    assert result.source == "us"


def test_parse_international_maps_components() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/parse_international"
        return httpx.Response(
            200,
            json={
                "mode": "international",
                "source": "international",
                "is_valid": True,
                "is_parsed": True,
                "address": {
                    "RawInput": "10 Downing St, London",
                    "HouseNumber": "10",
                    "Road": "Downing St",
                    "City": "London",
                    "Country": "United Kingdom",
                },
                "international_address": {
                    "RawInput": "10 Downing St, London",
                    "HouseNumber": "10",
                    "Road": "Downing St",
                    "City": "London",
                    "Country": "United Kingdom",
                },
                "components": {
                    "road": ["Downing St"],
                    "city": ["London"],
                    "country": ["United Kingdom"],
                },
                "errors": [],
            },
        )

    client = LibpostalRemoteClient(
        base_url="http://test",
        auto_start=False,
        transport=httpx.MockTransport(handler),
    )
    result = client.parse_international("10 Downing St, London")

    assert result.is_valid
    assert result.international_address is not None
    assert result.international_address.Components["road"] == ["Downing St"]
    assert result.source == "international"


def test_remote_http_error_returns_error_parse_result() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"detail": "bad address"})

    client = LibpostalRemoteClient(
        base_url="http://test",
        auto_start=False,
        transport=httpx.MockTransport(handler),
    )
    result = client.parse("bad")

    assert not result.is_valid
    assert result.error is not None
    assert "bad address" in str(result.error)


def test_auto_start_invokes_container(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, bool] = {}

    def fake_ensure(*args, **kwargs) -> str:
        called["used"] = True
        return "http://localhost:9999"

    monkeypatch.setattr(
        "ryandata_address_utils.remote.client.ensure_libpostal_container",
        fake_ensure,
    )

    client = LibpostalRemoteClient(auto_start=True, transport=None)
    client._ensure_started()

    assert called.get("used") is True
    assert client.base_url == "http://localhost:9999"


def test_parse_remote_uses_parse_auto() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/parse_auto"
        return httpx.Response(
            200,
            json={
                "mode": "us",
                "source": "us",
                "is_valid": True,
                "is_parsed": True,
                "address": {
                    "AddressNumber": "50",
                    "StreetName": "Congress",
                    "StreetNamePostType": "Ave",
                    "RawInput": "50 Congress Ave, Austin TX",
                },
                "international_address": None,
                "components": {},
                "errors": [],
            },
        )

    client = LibpostalRemoteClient(
        base_url="http://test",
        auto_start=False,
        transport=httpx.MockTransport(handler),
    )
    result = parse_remote("50 Congress Ave, Austin TX", client=client)

    assert result.is_valid
    assert result.address is not None
    assert result.address.StreetName == "Congress"
