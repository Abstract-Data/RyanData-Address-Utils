from __future__ import annotations

import os
from typing import Any, Optional

import httpx

from ryandata_address_utils.models import (
    PACKAGE_NAME,
    Address,
    InternationalAddress,
    ParseResult,
    RyanDataAddressError,
    ValidationResult,
)
from ryandata_address_utils.remote.container import (
    LibpostalContainerConfig,
    ensure_libpostal_container,
)


def _env_auto_start() -> bool:
    return os.getenv("RYANDATA_LIBPOSTAL_AUTOSTART", "1").lower() not in {"0", "false", "no"}


class LibpostalRemoteClient:
    """Simple REST client for the libpostal FastAPI service."""

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
        auto_start: Optional[bool] = None,
        container_config: Optional[LibpostalContainerConfig] = None,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self._timeout = timeout
        self._transport = transport
        self._container_config = container_config or LibpostalContainerConfig()
        self._auto_start = _env_auto_start() if auto_start is None else auto_start

        default_base = (
            os.getenv("RYANDATA_LIBPOSTAL_URL")
            or f"http://{self._container_config.host}:{self._container_config.host_port}"
        )
        self.base_url = base_url or default_base

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self._timeout,
            transport=self._transport,
        )
        self._started = False

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def _ensure_started(self) -> None:
        if self._transport is not None or not self._auto_start or self._started:
            return

        try:
            base_url = ensure_libpostal_container(self._container_config)
        except Exception as exc:  # pragma: no cover - depends on Docker availability
            raise RyanDataAddressError(
                "remote_start",
                str(exc),
                {"package": PACKAGE_NAME},
            ) from exc

        self.base_url = base_url
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self._timeout,
            transport=self._transport,
        )
        self._started = True

    def _request(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        self._ensure_started()
        try:
            response = self._client.get(path, params=params)
        except Exception as exc:
            raise RyanDataAddressError(
                "remote_request",
                str(exc),
                {"package": PACKAGE_NAME},
            ) from exc

        if response.status_code >= 400:
            detail: Optional[str] = None
            try:
                payload = response.json()
                if isinstance(payload, dict):
                    detail = payload.get("detail") or payload.get("message")
            except Exception:
                detail = None
            message = detail or response.text
            raise RyanDataAddressError(
                "remote_http_error",
                f"{response.status_code}: {message}",
                {"package": PACKAGE_NAME, "status": response.status_code},
            )

        payload = response.json()
        if not isinstance(payload, dict):
            raise RyanDataAddressError(
                "remote_parse",
                "Remote API returned non-object payload",
                {"package": PACKAGE_NAME},
            )
        return payload

    def _to_parse_result(
        self,
        address_string: str,
        data: dict[str, Any],
        *,
        fallback_source: str,
    ) -> ParseResult:
        address = None
        international_address = None
        error: Optional[Exception] = None

        address_payload = data.get("address")
        if address_payload:
            try:
                address = Address.model_validate(address_payload)
            except Exception as exc:
                error = RyanDataAddressError(
                    "remote_parse",
                    f"Invalid address payload: {exc}",
                    {"package": PACKAGE_NAME},
                )

        components = data.get("components") or {}
        international_payload = data.get("international_address")
        if international_payload or components:
            merged = {**(international_payload or {}), "Components": components}
            merged.setdefault("RawInput", address_string)
            try:
                international_address = InternationalAddress.model_validate(merged)
            except Exception as exc:
                error = error or RyanDataAddressError(
                    "remote_parse",
                    f"Invalid international payload: {exc}",
                    {"package": PACKAGE_NAME},
                )

        errors = data.get("errors") or []
        validation = ValidationResult(is_valid=not errors)
        for message in errors:
            validation.add_error("remote", message)

        source = data.get("source") or data.get("mode") or fallback_source

        return ParseResult(
            raw_input=address_string,
            address=address,
            international_address=international_address,
            error=error,
            validation=validation,
            source=source,
        )

    def parse(self, address: str, *, validate: bool = True) -> ParseResult:
        try:
            data = self._request("/parse", {"address": address, "validate": validate})
        except RyanDataAddressError as exc:
            return ParseResult(
                raw_input=address,
                error=exc,
                validation=ValidationResult(is_valid=False),
                source="us",
            )
        return self._to_parse_result(address, data, fallback_source="us")

    def parse_international(self, address: str) -> ParseResult:
        try:
            data = self._request("/parse_international", {"address": address})
        except RyanDataAddressError as exc:
            return ParseResult(
                raw_input=address,
                error=exc,
                validation=ValidationResult(is_valid=False),
                source="international",
            )
        return self._to_parse_result(address, data, fallback_source="international")

    def parse_auto(self, address: str, *, validate: bool = True) -> ParseResult:
        try:
            data = self._request("/parse_auto", {"address": address, "validate": validate})
        except RyanDataAddressError as exc:
            return ParseResult(
                raw_input=address,
                error=exc,
                validation=ValidationResult(is_valid=False),
                source="auto",
            )
        return self._to_parse_result(address, data, fallback_source="auto")


_default_remote_client: Optional[LibpostalRemoteClient] = None


def get_remote_client(
    *,
    base_url: Optional[str] = None,
    auto_start: Optional[bool] = None,
    container_config: Optional[LibpostalContainerConfig] = None,
) -> LibpostalRemoteClient:
    global _default_remote_client

    if _default_remote_client is None or base_url is not None or auto_start is not None:
        _default_remote_client = LibpostalRemoteClient(
            base_url=base_url,
            auto_start=auto_start,
            container_config=container_config,
        )
    return _default_remote_client


def parse_remote(
    address: str,
    *,
    validate: bool = True,
    base_url: Optional[str] = None,
    auto_start: Optional[bool] = None,
    client: Optional[LibpostalRemoteClient] = None,
) -> ParseResult:
    """Convenience wrapper that mirrors the local parse API using the remote service."""
    remote_client = client or get_remote_client(base_url=base_url, auto_start=auto_start)
    return remote_client.parse_auto(address, validate=validate)
