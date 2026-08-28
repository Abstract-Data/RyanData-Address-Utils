"""Directionless address keys and precinct notation.

Blank directional is a real state. ``EAST`` and ``E`` collapse to one state.
Precinct labels (``PCT 3``, ``0003``) collapse to the same identifier.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

#: Directional words -> USPS abbreviation. Longest-first matching matters:
#: ``NORTHEAST`` must be tried before ``NORTH``.
_DIRECTIONALS_RAW: dict[str, str] = {
    "NORTHEAST": "NE",
    "NORTHWEST": "NW",
    "SOUTHEAST": "SE",
    "SOUTHWEST": "SW",
    "NORTH": "N",
    "SOUTH": "S",
    "EAST": "E",
    "WEST": "W",
}
DIRECTIONALS: Mapping[str, str] = MappingProxyType(_DIRECTIONALS_RAW)
_DIRECTIONAL_ABBREVS: frozenset[str] = frozenset(_DIRECTIONALS_RAW.values())

_LABEL_PREFIXES: tuple[str, ...] = ("PRECINCT ", "PREC ", "PCT ", "VP ")
_MISSING = frozenset({"", "NAN", "NONE", "NULL"})
_HOUSE_DIGITS = re.compile(r"\d+")


def canon_dir(value: str | None) -> str:
    """Return a USPS directional abbreviation, or empty.

    Parameters
    ----------
    value
        Raw directional token. ``None`` and whitespace are empty.

    Returns
    -------
    str
        Canonical abbreviation (``E``, ``NE``, …) or ``""``. Unknown tokens
        are returned uppercased so they still count as a distinct state.
    """
    if value is None:
        return ""
    text = str(value).strip().upper()
    if not text:
        return ""
    if text in DIRECTIONALS:
        return str(DIRECTIONALS[text])
    if text in _DIRECTIONAL_ABBREVS:
        return text
    return text


def normalize_precinct_code(value: object) -> str:
    """Reduce a precinct code to a comparable form.

    Sources encode the same precinct as ``0019``, ``19``, ``PCT 3``. Codes are
    upper-cased, stripped, and leading zeros removed. An all-zero code
    normalizes to ``"0"`` so precinct 0 stays distinct from missing.

    Parameters
    ----------
    value
        Raw precinct value.

    Returns
    -------
    str
        Normalized code, or ``""`` when missing.
    """
    if value is None:
        return ""
    text = str(value).strip().upper()
    if not text or text in _MISSING:
        return ""
    for prefix in _LABEL_PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix) :].strip()
            break
    stripped = text.lstrip("0")
    return stripped if stripped else "0"


def drop_direction_key(
    num: str,
    name: str,
    street_type: str,
    county: str,
    pct: str,
    unit: str | None = None,
) -> str:
    """Stable uniqueness key: number + directionless street + county + pct.

    Direction is intentionally omitted. Two sides of the same street share
    this key; ``classify_problem_keys`` then refuses keys with 2+ directionals.

    Parameters
    ----------
    num, name, street_type, county, pct
        Address components. ``pct`` is normalized.
    unit
        When provided, appended so unit-bearing rows do not collapse.

    Returns
    -------
    str
        Pipe-joined key.
    """
    name_part = str(name).strip().upper()
    type_part = str(street_type).strip().upper()
    street = " ".join(part for part in (name_part, type_part) if part)
    parts = [str(num).strip(), street, str(county).strip(), normalize_precinct_code(pct)]
    if unit is not None:
        parts.append(str(unit).strip().upper())
    return "|".join(parts)


def _is_directional_token(token: str) -> bool:
    return token in DIRECTIONALS or token in _DIRECTIONAL_ABBREVS


def fullname_dir_and_nodir_key(fullname: str) -> tuple[str, str]:
    """Split a TIGER ``FULLNAME`` into a directional and a directionless street.

    Census concatenates PREDIR and SUFDIR onto the name. Both are stripped so
    ``E MAIN ST`` and ``MAIN ST W`` share a street key.

    Parameters
    ----------
    fullname
        TIGER FULLNAME (or any space-delimited street string).

    Returns
    -------
    tuple[str, str]
        ``(dir_canon, street_key_nodir)``.
    """
    tokens = str(fullname or "").strip().upper().split()
    pre = ""
    post = ""
    if tokens and _is_directional_token(tokens[0]):
        pre = canon_dir(tokens[0])
        tokens = tokens[1:]
    if tokens and _is_directional_token(tokens[-1]):
        post = canon_dir(tokens[-1])
        tokens = tokens[:-1]
    dir_canon = pre or post
    return dir_canon, " ".join(tokens)


def house_int(value: object) -> int | None:
    """First digit run in a house number, or None."""
    text = str(value or "").strip()
    if not text:
        return None
    match = _HOUSE_DIGITS.search(text)
    if match is None:
        return None
    return int(match.group(0))


def require_pandas() -> Any:
    """Import pandas or raise an install hint for the extra."""
    try:
        import pandas as pd
    except ImportError as exc:
        msg = (
            "ryandata_address_utils.match DataFrame helpers require pandas. "
            'Install with: pip install "ryandata-address-utils[pandas]"'
        )
        raise ImportError(msg) from exc
    return pd


def canon_dir_series(values: Any) -> Any:
    """Vectorized :func:`canon_dir`."""
    pd = require_pandas()
    text = pd.Series(values, dtype="object").fillna("").astype(str).str.strip().str.upper()
    for word, abbr in sorted(DIRECTIONALS.items(), key=lambda kv: -len(kv[0])):
        text = text.mask(text.eq(word), abbr)
    return text


def precinct_series(values: Any) -> Any:
    """Vectorized :func:`normalize_precinct_code`."""
    pd = require_pandas()
    text = pd.Series(values, dtype="object").fillna("").astype(str).str.strip().str.upper()
    text = text.mask(text.isin(_MISSING), "")
    for prefix in _LABEL_PREFIXES:
        stripped = text.str.slice(len(prefix)).str.strip()
        text = text.mask(text.str.startswith(prefix), stripped)
    zeros_gone = text.str.lstrip("0")
    out = zeros_gone.mask(zeros_gone.eq("") & text.ne(""), "0")
    return out.mask(text.eq(""), "")


def as_str_series(values: Any) -> Any:
    """Null-safe string series for join keys."""
    pd = require_pandas()
    return pd.Series(values, dtype="object").fillna("").astype(str)
