"""Minimal FastAPI service for parsing/validation (US + optional international via libpostal)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query

from ryandata_address_utils.service import AddressService, parse

try:
    from postal.parser import parse_address as lp_parse_address
except ImportError:
    lp_parse_address = None

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
    """Parse an international address via libpostal, if available."""
    if lp_parse_address is None:
        raise HTTPException(status_code=501, detail="libpostal not available in this environment")

    parsed = lp_parse_address(address)
    # Convert list of (component, label) tuples into a dict of lists to preserve duplicates
    components: dict[str, list[str]] = {}
    for value, label in parsed:
        components.setdefault(label, []).append(value)

    return {"address": address, "components": components}


@app.get("/parse_auto")
def parse_auto(address: str = Query(..., min_length=3), validate: bool = True) -> dict[str, Any]:
    """Auto route: try US parser first; if it fails and libpostal is available, fall back."""
    us_result = parse(address, validate=validate)
    if us_result.is_valid:
        return {
            "mode": "us",
            "is_valid": True,
            "is_parsed": True,
            "address": us_result.to_dict(),
            "errors": [],
        }

    if lp_parse_address is None:
        return {
            "mode": "us",
            "is_valid": False,
            "is_parsed": False,
            "errors": ["US parse failed and libpostal is not available"],
        }

    parsed = lp_parse_address(address)
    components: dict[str, list[str]] = {}
    for value, label in parsed:
        components.setdefault(label, []).append(value)

    return {"mode": "international", "is_valid": True, "is_parsed": True, "components": components}


# To run: uvicorn ryandata_address_utils.api:app --host 0.0.0.0 --port 8000
