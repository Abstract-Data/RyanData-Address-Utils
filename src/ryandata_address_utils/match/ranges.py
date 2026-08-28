"""TIGER ADDRFEAT house-number range matching.

TIGER 2024 uses ``LFROMADD`` / ``LTOADD``; TIGER 2025+ uses ``LFROMHN`` /
``LTOHN``. House containment is inclusive. When both ends of a side share
even/odd parity, the house must share that parity.
"""

from __future__ import annotations

from collections.abc import Collection
from typing import TYPE_CHECKING, Any

from ryandata_address_utils.match.keys import (
    as_str_series,
    dir_pair_canon_series,
    house_int,
    precinct_series,
    require_pandas,
)
from ryandata_address_utils.match.uniqueness import EXCLUDED_PROBLEM, MATCH, UNMATCHED

if TYPE_CHECKING:
    import pandas as pd

# TIGER 2024: LFROMADD/LTOADD. TIGER 2025+: LFROMHN/LTOHN.
_ADDRFEAT_RANGE_FIELDS: tuple[tuple[str, ...], ...] = (
    ("LFROMADD", "LFROMHN"),
    ("LTOADD", "LTOHN"),
    ("RFROMADD", "RFROMHN"),
    ("RTOADD", "RTOHN"),
)


def addrfeat_range_field_names(
    columns: Collection[str],
) -> tuple[str | None, str | None, str | None, str | None]:
    """Resolve left/right from-to house-number columns for ADDRFEAT vintages.

    2024 names win when both vintages are present.

    Parameters
    ----------
    columns
        Column names from an ADDRFEAT table.

    Returns
    -------
    tuple[str | None, str | None, str | None, str | None]
        ``(lfrom, lto, rfrom, rto)``.
    """
    present = set(columns)
    picked: list[str | None] = []
    for aliases in _ADDRFEAT_RANGE_FIELDS:
        picked.append(next((name for name in aliases if name in present), None))
    return picked[0], picked[1], picked[2], picked[3]


def _pair_covers(num: str, start: object, end: object) -> bool:
    """Inclusive house containment with even/odd parity when both ends agree."""
    n = house_int(num)
    lo = house_int(start)
    hi = house_int(end)
    if n is None or lo is None or hi is None:
        return False
    if lo > hi:
        lo, hi = hi, lo
    in_range = lo <= n <= hi
    parity_mismatch = lo % 2 == hi % 2 and n % 2 != lo % 2
    return in_range and not parity_mismatch


def house_in_addrfeat_range(
    num: str,
    lfrom: object,
    lto: object,
    rfrom: object,
    rto: object,
) -> bool:
    """True when ``num`` falls in the left or right ADDRFEAT range, inclusive."""
    return _pair_covers(num, lfrom, lto) or _pair_covers(num, rfrom, rto)


def _house_int_series(values: Any) -> Any:
    """Vectorized first digit run; non-numeric values become NA."""
    pd = require_pandas()
    digits = as_str_series(values).str.extract(r"(\d+)", expand=False)
    return pd.to_numeric(digits, errors="coerce")


def _pair_covers_series(num: Any, start: Any, end: Any) -> Any:
    """Vectorized :func:`_pair_covers` for ADDRFEAT from/to columns."""
    n = _house_int_series(num)
    lo_raw = _house_int_series(start)
    hi_raw = _house_int_series(end)
    use_lo = lo_raw <= hi_raw
    lo = lo_raw.where(use_lo, hi_raw)
    hi = hi_raw.where(use_lo, lo_raw)
    present = n.notna() & lo_raw.notna() & hi_raw.notna()
    in_range = (lo <= n) & (n <= hi)
    same_end_parity = (lo % 2) == (hi % 2)
    parity_ok = (~same_end_parity) | ((n % 2) == (lo % 2))
    return present & in_range & parity_ok


def match_addrfeat_ranges(voters: pd.DataFrame, ranges: pd.DataFrame) -> pd.Series:
    """Ryan Data uniqueness against ADDRFEAT ranges (house containment).

    Join voters to ranges on directionless street + county + precinct, keep
    rows whose house number sits in a left or right range, then refuse keys
    with 2+ distinct covering directionals.

    Parameters
    ----------
    voters
        Frame with ``num``, ``street_key_nodir``, ``county``, ``pct``.
    ranges
        Frame with those street/county/pct columns plus ``dir``, ``lfrom``,
        ``lto``, ``rfrom``, ``rto``.

    Returns
    -------
    pandas.Series
        Outcome strings aligned to ``voters.index``.
    """
    pd = require_pandas()
    if len(voters) == 0:
        return pd.Series(dtype=object, name="outcome")
    if len(ranges) == 0:
        return pd.Series(UNMATCHED, index=voters.index, name="outcome")

    vf = pd.DataFrame(
        {
            "_i": range(len(voters)),
            "_street": as_str_series(voters["street_key_nodir"]).to_numpy(),
            "_county": as_str_series(voters["county"]).to_numpy(),
            "_pct": precinct_series(voters["pct"]).to_numpy(),
            "_num": as_str_series(voters["num"]).to_numpy(),
        }
    )
    rng = pd.DataFrame(
        {
            "_street": as_str_series(ranges["street_key_nodir"]).to_numpy(),
            "_county": as_str_series(ranges["county"]).to_numpy(),
            "_pct": precinct_series(ranges["pct"]).to_numpy(),
            "_dir": dir_pair_canon_series(ranges["pre_dir"], ranges["post_dir"]).to_numpy(),
            "lfrom": as_str_series(ranges["lfrom"]).to_numpy(),
            "lto": as_str_series(ranges["lto"]).to_numpy(),
            "rfrom": as_str_series(ranges["rfrom"]).to_numpy(),
            "rto": as_str_series(ranges["rto"]).to_numpy(),
        }
    )
    hits = vf.merge(rng, on=["_street", "_county", "_pct"], how="inner")
    covers = _pair_covers_series(hits["_num"], hits["lfrom"], hits["lto"]) | _pair_covers_series(
        hits["_num"], hits["rfrom"], hits["rto"]
    )
    hits = hits.loc[covers.to_numpy()]
    n_dirs = hits.groupby("_i", sort=False)["_dir"].nunique()
    outcome = pd.Series(UNMATCHED, index=vf["_i"], name="outcome")
    if len(n_dirs):
        hit_out = pd.Series(MATCH, index=n_dirs.index)
        hit_out = hit_out.mask(n_dirs >= 2, EXCLUDED_PROBLEM)
        outcome.loc[hit_out.index] = hit_out
    return pd.Series(outcome.to_numpy(), index=voters.index, name="outcome")
