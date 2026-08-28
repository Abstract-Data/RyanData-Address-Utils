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
