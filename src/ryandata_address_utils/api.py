"""Minimal FastAPI service for parsing/validation (US + optional international via libpostal)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query

from ryandata_address_utils.service import AddressService, parse

app = FastAPI(title="RyanData Address Utils API", version="0.3.1")
service = AddressService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/parse")
def parse_us_address(
    address: str = Query(..., min_length=3),
    validate: bool = True,
) -> dict[str, Any]:
    """Parse a US address using the standard service."""
    result = parse(address, validate=validate)
    return {
        "is_valid": result.is_valid,
        "is_parsed": result.is_parsed,
        "address": result.to_dict() if result.address else None,
        "errors": [e.message for e in (result.validation.errors if result.validation else [])]
        if result.validation
        else [],
    }


@app.get("/parse_international")
def parse_international(address: str = Query(..., min_length=3)) -> dict[str, Any]:
    """Parse an international address via libpostal with strict validation."""
    result = service.parse_international(address)
    if result.error:
        status = 501 if "libpostal not available" in str(result.error).lower() else 400
        raise HTTPException(status_code=status, detail=str(result.error))
    if not result.is_valid or result.international_address is None:
        raise HTTPException(status_code=400, detail="International parse failed")

    intl = result.international_address
    return {
        "mode": "international",
        "is_valid": True,
        "is_parsed": True,
        "address": intl.to_dict(),
        "components": intl.Components,
        "errors": [],
    }


@app.get("/parse_auto")
def parse_auto(address: str = Query(..., min_length=3), validate: bool = True) -> dict[str, Any]:
    """Auto route: try US parser first; if it fails and libpostal is available, fall back."""
    result = service.parse_auto_route(address, validate=validate)

    if result.is_valid:
        if result.source == "international":
            intl = result.international_address
            return {
                "mode": "international",
                "is_valid": True,
                "is_parsed": True,
                "address": intl.to_dict() if intl else None,
                "components": intl.Components if intl else {},
                "errors": [],
                "source": result.source,
            }
        return {
            "mode": "us",
            "is_valid": True,
            "is_parsed": True,
            "address": result.to_dict(),
            "errors": [],
            "source": result.source,
        }

    if result.error:
        status = 501 if "libpostal not available" in str(result.error).lower() else 400
        raise HTTPException(status_code=status, detail=str(result.error))

    if result.source == "international":
        return {
            "mode": "international",
            "is_valid": False,
            "is_parsed": False,
            "errors": ["International parse failed"],
            "source": result.source,
        }

    return {
        "mode": "us",
        "is_valid": False,
        "is_parsed": False,
        "errors": ["US parse failed"],
        "source": result.source,
    }


# To run: uvicorn ryandata_address_utils.api:app --host 0.0.0.0 --port 8000
