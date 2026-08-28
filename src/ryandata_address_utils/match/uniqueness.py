"""Drop-direction uniqueness: refuse keys with 2+ distinct directionals."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ryandata_address_utils.match.keys import (
    as_str_series,
    dir_pair_canon_series,
    precinct_series,
    require_pandas,
)

if TYPE_CHECKING:
    import pandas as pd

MATCH = "match"
EXCLUDED_PROBLEM = "excluded_problem"
UNMATCHED = "unmatched"

_KEY = ("num", "street_key_nodir", "county", "pct_norm")


def classify_problem_keys(points: pd.DataFrame, *, include_unit: bool = False) -> pd.DataFrame:
    """Mark keys whose directionless identity has 2+ distinct directionals.

    Blank is a directional state: ``E`` vs empty is a problem. ``EAST`` and
    ``E`` collapse to one state.

    Parameters
    ----------
    points
        Frame with ``num``, ``street_key_nodir``, ``county``, ``pct``,
        ``pre_dir``, ``post_dir``. Optional ``unit`` when ``include_unit``
        is true.
    include_unit
        When true, unit is part of the uniqueness key.

    Returns
    -------
    pandas.DataFrame
        Copy of ``points`` plus ``dir_canon``, ``pct_norm``, ``n_dirs``,
        ``n_points``, and ``is_problem``.
    """
    frame = points.copy()
    frame["dir_canon"] = dir_pair_canon_series(frame["pre_dir"], frame["post_dir"]).to_numpy()
    frame["num"] = as_str_series(frame["num"]).to_numpy()
    frame["street_key_nodir"] = as_str_series(frame["street_key_nodir"]).to_numpy()
    frame["county"] = as_str_series(frame["county"]).to_numpy()
    frame["pct_norm"] = precinct_series(frame["pct"]).to_numpy()
    key_cols: list[str] = list(_KEY)
    if include_unit:
        if "unit" not in frame.columns:
            frame["unit"] = ""
        frame["unit"] = as_str_series(frame["unit"]).to_numpy()
        key_cols.append("unit")
    stats = (
        frame.groupby(key_cols, dropna=False, sort=False, observed=True)
        .agg(n_dirs=("dir_canon", "nunique"), n_points=("dir_canon", "size"))
        .reset_index()
    )
    stats["is_problem"] = stats["n_dirs"] >= 2
    return frame.merge(stats, on=key_cols, how="left")


def match_drop_direction(
    voters: pd.DataFrame,
    points: pd.DataFrame,
    *,
    include_unit: bool = False,
) -> pd.Series:
    """Assign ``match`` / ``excluded_problem`` / ``unmatched`` per voter row.

    A voter matches when its directionless key hits a unique (non-problem)
    point with a non-empty precinct. Problem keys win over a match.

    Parameters
    ----------
    voters
        Frame with ``num``, ``street_key_nodir``, ``county``, ``pct``.
    points
        Reference points with those columns plus ``pre_dir`` and ``post_dir``.
    include_unit
        When true, both frames must carry ``unit`` (filled with ``""`` if
        missing on voters).

    Returns
    -------
    pandas.Series
        Outcome strings aligned to ``voters.index``.
    """
    pd = require_pandas()
    if len(voters) == 0:
        return pd.Series(dtype=object, name="outcome")
    if len(points) == 0:
        return pd.Series(UNMATCHED, index=voters.index, name="outcome")

    classified = classify_problem_keys(points, include_unit=include_unit)
    key_cols = list(_KEY)
    if include_unit:
        key_cols.append("unit")

    problem = classified.loc[classified["is_problem"], key_cols].drop_duplicates()
    problem = problem.assign(_problem=True)
    matchable = classified.loc[
        ~classified["is_problem"] & classified["pct_norm"].ne(""),
        key_cols,
    ].drop_duplicates()
    matchable = matchable.assign(_hit=True)

    vf = voters.copy()
    vf["num"] = as_str_series(vf["num"]).to_numpy()
    vf["street_key_nodir"] = as_str_series(vf["street_key_nodir"]).to_numpy()
    vf["county"] = as_str_series(vf["county"]).to_numpy()
    vf["pct_norm"] = precinct_series(vf["pct"]).to_numpy()
    if include_unit:
        if "unit" not in vf.columns:
            vf["unit"] = ""
        vf["unit"] = as_str_series(vf["unit"]).to_numpy()

    joined = vf.merge(problem, on=key_cols, how="left").merge(matchable, on=key_cols, how="left")
    is_problem = joined["_problem"].eq(True)
    is_hit = joined["_hit"].eq(True)
    outcome: Any = pd.Series(UNMATCHED, index=joined.index)
    outcome = outcome.mask(is_hit, MATCH).mask(is_problem, EXCLUDED_PROBLEM)
    return pd.Series(outcome.to_numpy(), index=voters.index, name="outcome")


_GEO_KEYS: dict[str, tuple[str, ...]] = {
    "precinct": ("num", "street_key_nodir", "county", "pct"),
    "county": ("num", "street_key_nodir", "county"),
    "zip": ("num", "street_key_nodir", "county", "zip5"),
    "cd": ("num", "street_key_nodir", "cd"),
}


def uniqueness_at_geography(
    points: pd.DataFrame,
    *,
    geography: str,
    include_unit: bool = False,
) -> dict[str, int | float]:
    """Problem-key rates at one geographic grain. Missing key columns fail loud."""
    if geography not in _GEO_KEYS:
        raise ValueError(f"unknown geography {geography!r}; use {sorted(_GEO_KEYS)}")
    needed = list(_GEO_KEYS[geography])
    missing = [c for c in needed if c not in points.columns]
    if missing:
        raise ValueError(f"uniqueness_at_geography {geography} missing columns {missing}")
    classified = classify_problem_keys(points, include_unit=include_unit)
    key_cols = ["pct_norm" if c == "pct" else c for c in needed]
    if include_unit:
        key_cols.append("unit")
    stats = (
        classified.groupby(key_cols, dropna=False, sort=False, observed=True)
        .agg(n_dirs=("dir_canon", "nunique"), n_points=("dir_canon", "size"))
        .reset_index()
    )
    stats["is_problem"] = stats["n_dirs"] >= 2
    n_keys = len(stats)
    n_problem = int(stats["is_problem"].sum()) if n_keys else 0
    n_points = len(classified)
    n_points_problem = int(stats.loc[stats["is_problem"], "n_points"].sum()) if n_keys else 0
    geo_col = key_cols[-1] if geography != "county" else None
    n_blank_geo = 0
    if geo_col is not None and geo_col in stats.columns:
        n_blank_geo = int((stats[geo_col].fillna("").astype(str) == "").sum())
    return {
        "n_keys": n_keys,
        "n_problem_keys": n_problem,
        "n_points": n_points,
        "n_points_problem": n_points_problem,
        "pct_keys_excluded": round(100.0 * n_problem / n_keys, 4) if n_keys else 0.0,
        "pct_points_excluded": round(100.0 * n_points_problem / n_points, 4) if n_points else 0.0,
        "n_blank_geo": n_blank_geo,
    }


def cross_precinct_twin_counts(points: pd.DataFrame) -> dict[str, int]:
    """County-level directional twins that precinct uniqueness would accept."""
    classified = classify_problem_keys(points, include_unit=False)
    county_cols = ["num", "street_key_nodir", "county"]
    county = (
        classified.groupby(county_cols, dropna=False, sort=False, observed=True)
        .agg(n_dirs_county=("dir_canon", "nunique"), n_points=("dir_canon", "size"))
        .reset_index()
    )
    pct = (
        classified.groupby([*county_cols, "pct_norm"], dropna=False, sort=False, observed=True)
        .agg(n_dirs_pct=("dir_canon", "nunique"))
        .reset_index()
    )
    pct_max = (
        pct.groupby(county_cols, dropna=False, sort=False, observed=True)
        .agg(max_dirs_pct=("n_dirs_pct", "max"))
        .reset_index()
    )
    split = county.merge(pct_max, on=county_cols, how="left")
    split = split.loc[(split["n_dirs_county"] >= 2) & (split["max_dirs_pct"] < 2)]
    n_keys = len(split)
    n_points = int(split["n_points"].sum()) if n_keys else 0
    return {
        "n_twin_keys_split_by_precinct": n_keys,
        "n_points_on_split_twins": n_points,
    }


def problem_pattern_label(dir_pairs: list[str]) -> str:
    """One primary label per problem key. First match wins."""
    pairs = [str(p) for p in dir_pairs]
    if "E|" in pairs and "W|" in pairs:
        return "ew_prefix"
    if "N|" in pairs and "S|" in pairs:
        return "ns_prefix"
    if pairs and all(p.startswith("|") for p in pairs) and any(p != "|" for p in pairs):
        return "suffix_only"
    if "|" in pairs and any(p != "|" for p in pairs):
        return "blank_vs_dir"
    pres = {p.split("|", 1)[0] for p in pairs if "|" in p}
    posts = {p.split("|", 1)[1] for p in pairs if "|" in p}
    if (pres - {""}) & (posts - {""}):
        return "prefix_vs_suffix"
    tokens = {t for p in pairs for t in p.split("|") if t}
    if any(a != b and (a.startswith(b) or b.startswith(a)) for a in tokens for b in tokens):
        return "diagonal"
    return "other"


def problem_pattern_counts(points: pd.DataFrame) -> dict[str, int]:
    """Count precinct-grain problem keys by :func:`problem_pattern_label`."""
    pd = require_pandas()
    classified = classify_problem_keys(points, include_unit=False)
    counts: dict[str, int] = {
        "ew_prefix": 0,
        "ns_prefix": 0,
        "suffix_only": 0,
        "blank_vs_dir": 0,
        "prefix_vs_suffix": 0,
        "diagonal": 0,
        "other": 0,
    }
    problems = classified.loc[classified["is_problem"]]
    if problems.empty:
        return counts
    grouped = problems.groupby(
        ["num", "street_key_nodir", "county", "pct_norm"],
        dropna=False,
        sort=False,
        observed=True,
    )["dir_canon"]
    for _, dirs in grouped:
        label = problem_pattern_label(list(pd.unique(dirs)))
        counts[label] = counts.get(label, 0) + 1
    return counts
