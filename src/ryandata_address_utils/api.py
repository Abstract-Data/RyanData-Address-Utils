"""Minimal FastAPI service for parsing/validation (US + optional international via libpostal)."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query

from ryandata_address_utils.models import ParseResult
from ryandata_address_utils.service import AddressService, parse

app = FastAPI(title="RyanData Address Utils API", version="0.3.1")
service = AddressService()


def _format_result(result: ParseResult, *, forced_mode: Optional[str] = None) -> dict[str, Any]:
    """Normalize ParseResult into a consistent API payload."""
    errors: list[str] = []
    if result.validation and result.validation.errors:
        errors.extend([err.message for err in result.validation.errors])
    if result.error:
        errors.append(str(result.error))

    international = result.international_address
    return {
        "mode": forced_mode or result.source or ("international" if international else "us"),
        "source": result.source or forced_mode,
        "is_valid": result.is_valid,
        "is_parsed": result.is_parsed,
        "address": result.address.to_dict() if result.address else None,
        "international_address": international.to_dict() if international else None,
        "components": international.Components if international else {},
        "errors": errors,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/parse")
def parse_us_address(
    address: str = Query(..., min_length=3),
    validate: bool = True,
) -> dict[str, Any]:
    """Parse a US address using the standard service."""
    try:
        result = parse(address, validate=validate)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if result.error:
        raise HTTPException(status_code=400, detail=str(result.error))

    return _format_result(result, forced_mode="us")


@app.get("/parse_international")
def parse_international(address: str = Query(..., min_length=3)) -> dict[str, Any]:
    """Parse an international address via libpostal with strict validation."""
    result = service.parse_international(address)
    if result.error:
        status = 501 if "libpostal not available" in str(result.error).lower() else 400
        raise HTTPException(status_code=status, detail=str(result.error))
    if not result.is_valid or result.international_address is None:
        raise HTTPException(status_code=400, detail="International parse failed")

    return _format_result(result, forced_mode="international")


@app.get("/parse_auto")
def parse_auto(address: str = Query(..., min_length=3), validate: bool = True) -> dict[str, Any]:
    """Auto route: try US parser first; if it fails and libpostal is available, fall back."""
    result = service.parse_auto_route(address, validate=validate)

    if result.error:
        status = 501 if "libpostal not available" in str(result.error).lower() else 400
        raise HTTPException(status_code=status, detail=str(result.error))

    return _format_result(result)


# To run: uvicorn ryandata_address_utils.api:app --host 0.0.0.0 --port 8000
