"""Load a Texas SOS voter extract and build directionless match keys."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ryandata_address_utils.match.keys import precinct_series, require_pandas
from ryandata_address_utils.match.texas import TEXAS_COUNTY_FIPS, county_fips_from_name

if TYPE_CHECKING:
    import pandas as pd

_NON_KEY = re.compile(r"[^A-Z0-9 ]")
_WS = re.compile(r"\s+")

VF_COLUMNS: tuple[str, ...] = (
    "COUNTY",
    "PCT",
    "VUID",
    "STATUS",
    "RHNUM",
    "RSTPRE",
    "RSTNAME",
    "RSTTYPE",
    "RSTSFX",
    "RUNUM",
    "RUTYPE",
    "RZIP",
)


def component_street_key(*parts: object) -> str:
    """Uppercase, drop punctuation, join non-empty parts. Direction is omitted by caller."""
    cleaned: list[str] = []
    for part in parts:
        text = _WS.sub(" ", _NON_KEY.sub(" ", str(part or "").upper())).strip()
        if text:
            cleaned.append(text)
    return " ".join(cleaned)


def _col(frame: pd.DataFrame, name: str) -> Any:
    """Return a string series for ``name``, or blanks when the column is absent."""
    pd = require_pandas()
    if name in frame.columns:
        return frame[name].fillna("").astype(str)
    return pd.Series([""] * len(frame), index=frame.index)


def street_key_series(name: Any, street_type: Any) -> Any:
    """Vectorized ``component_street_key`` for name + type (no direction)."""
    text = (name.fillna("") + " " + street_type.fillna("")).str.upper()
    return (
        text.str.replace(r"[^A-Z0-9 ]", " ", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )


def load_voterfile(
    path: Path,
    *,
    counties: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """Read a SOS-style CSV as strings. Optional county-name filter."""
    pd = require_pandas()
    frame = pd.read_csv(path, dtype=str, encoding="utf-8", encoding_errors="replace")
    frame.columns = [str(c).lstrip("\ufeff").strip() for c in frame.columns]
    keep = [c for c in VF_COLUMNS if c in frame.columns]
    if not keep:
        raise ValueError(f"{path} has none of the expected SOS columns {VF_COLUMNS}")
    frame = frame.loc[:, keep].fillna("")
    for col in frame.columns:
        frame[col] = frame[col].astype(str).str.strip().str.upper()
    if counties is not None and "COUNTY" in frame.columns:
        wanted_fips = {
            fips
            for county in counties
            if (fips := county_fips_from_name(county.replace("_", " "))) is not None
        }
        row_fips = frame["COUNTY"].map(county_fips_from_name)
        frame = frame.loc[row_fips.isin(wanted_fips)]
    return frame.reset_index(drop=True)


def canonicalize_voters(raw: pd.DataFrame) -> pd.DataFrame:
    """Map SOS columns onto uniqueness keys: ``num``, ``street_key_nodir``, ``county``, ``pct``."""
    pd = require_pandas()
    county_code = _col(raw, "COUNTY")
    fips = county_code.replace(TEXAS_COUNTY_FIPS)
    unknown = ~fips.isin(set(TEXAS_COUNTY_FIPS.values()))
    if unknown.any():
        mapped = [county_fips_from_name(v) or "" for v in county_code.loc[unknown].tolist()]
        fips.loc[unknown] = mapped
    out = pd.DataFrame(
        {
            "num": _col(raw, "RHNUM").str.strip(),
            "street_key_nodir": street_key_series(_col(raw, "RSTNAME"), _col(raw, "RSTTYPE")),
            "county": fips,
            "pct": precinct_series(_col(raw, "PCT")).to_numpy(),
        },
        index=raw.index,
    )
    if "VUID" in raw.columns:
        out["vuid"] = _col(raw, "VUID")
    out["pre_dir"] = _col(raw, "RSTPRE")
    out["post_dir"] = _col(raw, "RSTSFX")
    return out
