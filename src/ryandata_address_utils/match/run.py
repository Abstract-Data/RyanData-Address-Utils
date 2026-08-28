"""Fetch reference layers (if missing) and run uniqueness against a voter file."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from ryandata_address_utils.match.keys import require_pandas
from ryandata_address_utils.match.ranges import match_addrfeat_ranges
from ryandata_address_utils.match.texas import county_fips_from_name
from ryandata_address_utils.match.uniqueness import (
    MATCH,
    cross_precinct_twin_counts,
    match_drop_direction,
    problem_pattern_counts,
    uniqueness_at_geography,
)
from ryandata_address_utils.match.voters import canonicalize_voters, load_voterfile

DEFAULT_CACHE = Path.home() / ".cache" / "ryandata-address-utils"
ALLOWED_SOURCES = frozenset({"txgio", "tiger"})
FetchFn = Callable[..., Path]
LoadFn = Callable[..., Any]


def parse_sources(sources: str) -> tuple[str, ...]:
    """Parse ``txgio,tiger``. Empty defaults to txgio. Unknown tokens fail loud."""
    parts = tuple(p.strip().lower() for p in sources.split(",") if p.strip())
    bad = [p for p in parts if p not in ALLOWED_SOURCES]
    if bad:
        raise ValueError(f"unknown --sources {bad}; use txgio,tiger")
    return parts or ("txgio",)


def default_cache_dir() -> Path:
    """User-level cache for TxGIO, ADDRFEAT, and TLC precinct downloads."""
    return DEFAULT_CACHE


def _fips_for_counties(names: Sequence[str]) -> tuple[str, ...]:
    """Map county names to unique 5-digit FIPS; unknown names fail loud."""
    fips: list[str] = []
    missing: list[str] = []
    for name in names:
        code = county_fips_from_name(name)
        if code is None:
            missing.append(str(name))
        else:
            fips.append(code)
    if missing:
        raise ValueError(f"unknown county names: {missing}")
    return tuple(dict.fromkeys(fips))


def _concat_outcomes(parts: list[Any], column: str, index: Any) -> Any:
    """Stack per-county outcome series onto the voter index."""
    pd = require_pandas()
    if not parts:
        return pd.Series([None] * len(index), index=index, name=column)
    return pd.concat(parts).reindex(index)


def run_uniqueness(
    voterfile: Path,
    *,
    sources: str = "txgio",
    cache_dir: Path | None = None,
    out_dir: Path | None = None,
    counties: tuple[str, ...] | None = None,
    tiger_years: tuple[int, ...] = (2025, 2024),
    force_fetch: bool = False,
    fetch_txgio_fn: FetchFn | None = None,
    fetch_tiger_fn: FetchFn | None = None,
    fetch_precincts_fn: FetchFn | None = None,
    load_txgio_fn: LoadFn | None = None,
    load_tiger_fn: LoadFn | None = None,
) -> dict[str, Any]:
    """Download reference data as needed, match, write ``outcomes.csv`` + ``summary.json``."""
    pd = require_pandas()
    wanted = parse_sources(sources)
    cache = Path(cache_dir) if cache_dir is not None else default_cache_dir()
    out = Path(out_dir) if out_dir is not None else Path("uniqueness_out")
    out.mkdir(parents=True, exist_ok=True)

    raw = load_voterfile(voterfile, counties=counties)
    if raw.empty:
        raise ValueError(f"no voter rows in {voterfile}")
    if "COUNTY" not in raw.columns:
        raise ValueError(f"{voterfile} has no COUNTY column")
    county_names = tuple(sorted({str(v) for v in raw["COUNTY"].tolist()}))
    fips_list = _fips_for_counties(county_names)
    voters = canonicalize_voters(raw)

    precincts_dir = cache / "precincts"
    txgio_dir = cache / "txgio"
    tiger_dir = cache / "tiger" / "addrfeat"
    if fetch_precincts_fn is None:
        from ryandata_address_utils.match.fetch.precincts import fetch_tx_precincts

        fetch_precincts_fn = fetch_tx_precincts
    precincts_path = fetch_precincts_fn(dest=precincts_dir, force=force_fetch)

    txgio_loader = load_txgio_fn
    tiger_loader = load_tiger_fn
    if "txgio" in wanted:
        if fetch_txgio_fn is None:
            from ryandata_address_utils.match.fetch.txgio import fetch_txgio_counties

            fetch_txgio_fn = fetch_txgio_counties
        fetch_txgio_fn(fips_list=fips_list, dest=txgio_dir, force=force_fetch)
        if txgio_loader is None:
            from ryandata_address_utils.match.geo import load_txgio_points

            txgio_loader = load_txgio_points
    if "tiger" in wanted:
        if fetch_tiger_fn is None:
            from ryandata_address_utils.match.fetch.tiger import fetch_tiger_counties

            fetch_tiger_fn = fetch_tiger_counties
        fetch_tiger_fn(fips_list=fips_list, dest=tiger_dir, years=tiger_years, force=force_fetch)
        if tiger_loader is None:
            from ryandata_address_utils.match.geo import load_tiger_ranges

            tiger_loader = load_tiger_ranges

    txgio_parts: list[Any] = []
    tiger_parts: list[Any] = []
    txgio_frames: list[Any] = []
    for fips in fips_list:
        vf = voters.loc[voters["county"] == fips]
        if vf.empty:
            continue
        if "txgio" in wanted:
            if txgio_loader is None:
                raise RuntimeError("txgio loader missing")
            points = txgio_loader(zip_or_dir=txgio_dir, fips=fips, precincts_path=precincts_path)
            if not points.empty:
                txgio_frames.append(points)
            series = match_drop_direction(vf, points)
            txgio_parts.append(pd.Series(series.to_numpy(), index=vf.index, name="txgio_outcome"))
        if "tiger" in wanted:
            if tiger_loader is None:
                raise RuntimeError("tiger loader missing")
            ranges = tiger_loader(shp=tiger_dir, fips=fips, precincts_path=precincts_path)
            series = match_addrfeat_ranges(vf, ranges)
            tiger_parts.append(pd.Series(series.to_numpy(), index=vf.index, name="tiger_outcome"))

    result = voters.copy()
    if "txgio" in wanted:
        result["txgio_outcome"] = _concat_outcomes(txgio_parts, "txgio_outcome", result.index)
    if "tiger" in wanted:
        result["tiger_outcome"] = _concat_outcomes(tiger_parts, "tiger_outcome", result.index)

    csv_path = out / "outcomes.csv"
    result.to_csv(csv_path, index=False)
    summary = {
        "voterfile": str(voterfile),
        "sources": list(wanted),
        "counties": list(county_names),
        "fips": list(fips_list),
        "n": int(len(result)),
        "outcomes": str(csv_path),
    }
    if "txgio_outcome" in result.columns:
        summary["txgio_match"] = int((result["txgio_outcome"] == MATCH).sum())
    if "tiger_outcome" in result.columns:
        summary["tiger_match"] = int((result["tiger_outcome"] == MATCH).sum())
    if txgio_frames:
        all_points = pd.concat(txgio_frames, ignore_index=True)
        grains = ["precinct", "county"]
        if "zip5" in all_points.columns:
            grains.append("zip")
        if "cd" in all_points.columns:
            grains.append("cd")
        summary["uniqueness"] = {
            grain: uniqueness_at_geography(all_points, geography=grain, include_unit=False)
            for grain in grains
        }
        summary["twins"] = cross_precinct_twin_counts(all_points)
        summary["patterns"] = problem_pattern_counts(all_points)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary
