"""Drop-direction uniqueness on pandas frames (issue #22)."""

from __future__ import annotations

import pytest

pytest.importorskip("pandas")

import pandas as pd  # noqa: E402

from ryandata_address_utils.match import (  # noqa: E402
    EXCLUDED_PROBLEM,
    MATCH,
    UNMATCHED,
    classify_problem_keys,
    cross_precinct_twin_counts,
    match_drop_direction,
    problem_pattern_counts,
    uniqueness_at_geography,
)


def _points(*rows: dict[str, object]) -> pd.DataFrame:
    return pd.DataFrame(list(rows))


class TestClassifyProblemKeys:
    def test_east_and_west_same_key_is_problem(self) -> None:
        frame = _points(
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "E",
                "post_dir": "",
                "unit": "",
            },
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "W",
                "post_dir": "",
                "unit": "",
            },
        )
        out = classify_problem_keys(frame, include_unit=False)
        assert out["is_problem"].tolist() == [True, True]
        assert out["n_dirs"].tolist() == [2, 2]

    def test_east_and_e_collapse_and_are_not_a_problem(self) -> None:
        frame = _points(
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "E",
                "post_dir": "",
                "unit": "",
            },
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "EAST",
                "post_dir": "",
                "unit": "",
            },
        )
        out = classify_problem_keys(frame, include_unit=False)
        assert out["is_problem"].tolist() == [False, False]
        assert out["n_dirs"].tolist() == [1, 1]

    def test_blank_versus_directional_is_problem(self) -> None:
        frame = _points(
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "E",
                "post_dir": "",
                "unit": "",
            },
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "",
                "post_dir": "",
                "unit": "",
            },
        )
        out = classify_problem_keys(frame, include_unit=False)
        assert out["is_problem"].unique().tolist() == [True]

    def test_north_versus_south_is_problem(self) -> None:
        frame = _points(
            {
                "num": "100",
                "street_key_nodir": "OAK AVE",
                "county": "48001",
                "pct": "2",
                "pre_dir": "N",
                "post_dir": "",
                "unit": "",
            },
            {
                "num": "100",
                "street_key_nodir": "OAK AVE",
                "county": "48001",
                "pct": "2",
                "pre_dir": "S",
                "post_dir": "",
                "unit": "",
            },
        )
        out = classify_problem_keys(frame, include_unit=False)
        assert out["is_problem"].unique().tolist() == [True]

    def test_diagonal_counts_as_distinct_directional(self) -> None:
        frame = _points(
            {
                "num": "10",
                "street_key_nodir": "LOOP",
                "county": "48001",
                "pct": "1",
                "pre_dir": "N",
                "post_dir": "",
                "unit": "",
            },
            {
                "num": "10",
                "street_key_nodir": "LOOP",
                "county": "48001",
                "pct": "1",
                "pre_dir": "NE",
                "post_dir": "",
                "unit": "",
            },
        )
        out = classify_problem_keys(frame, include_unit=False)
        assert out["n_dirs"].unique().tolist() == [2]
        assert out["is_problem"].unique().tolist() == [True]

    def test_unit_included_splits_keys_unit_ignored_does_not(self) -> None:
        frame = _points(
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "E",
                "post_dir": "",
                "unit": "#1",
            },
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "W",
                "post_dir": "",
                "unit": "#2",
            },
        )
        ignored = classify_problem_keys(frame, include_unit=False)
        split = classify_problem_keys(frame, include_unit=True)
        assert ignored["is_problem"].unique().tolist() == [True]
        assert split["is_problem"].unique().tolist() == [False]

    def test_pct_notation_variants_share_a_key(self) -> None:
        frame = _points(
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "PCT 3",
                "pre_dir": "E",
                "post_dir": "",
                "unit": "",
            },
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "0003",
                "pre_dir": "W",
                "post_dir": "",
                "unit": "",
            },
        )
        out = classify_problem_keys(frame, include_unit=False)
        assert out["is_problem"].unique().tolist() == [True]


class TestMatchDropDirection:
    def test_unique_point_matches(self) -> None:
        points = _points(
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "E",
                "post_dir": "",
            }
        )
        voters = _points(
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
            }
        )
        assert match_drop_direction(voters, points).tolist() == [MATCH]

    def test_east_and_west_same_key_is_excluded(self) -> None:
        points = _points(
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "E",
                "post_dir": "",
            },
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "W",
                "post_dir": "",
            },
        )
        voters = _points(
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
            }
        )
        assert match_drop_direction(voters, points).tolist() == [EXCLUDED_PROBLEM]

    def test_no_point_is_unmatched(self) -> None:
        points = _points(
            {
                "num": "100",
                "street_key_nodir": "OAK AVE",
                "county": "48001",
                "pct": "1",
                "pre_dir": "E",
                "post_dir": "",
            }
        )
        voters = _points(
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
            }
        )
        assert match_drop_direction(voters, points).tolist() == [UNMATCHED]

    def test_empty_pct_does_not_match(self) -> None:
        points = _points(
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "",
                "pre_dir": "E",
                "post_dir": "",
            }
        )
        voters = _points(
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "",
            }
        )
        assert match_drop_direction(voters, points).tolist() == [UNMATCHED]

    def test_preserves_voter_index(self) -> None:
        points = _points(
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "E",
                "post_dir": "",
            }
        )
        voters = pd.DataFrame(
            {
                "num": ["900"],
                "street_key_nodir": ["MAIN ST"],
                "county": ["48001"],
                "pct": ["1"],
            },
            index=[42],
        )
        out = match_drop_direction(voters, points)
        assert out.index.tolist() == [42]
        assert out.tolist() == [MATCH]

    def test_empty_voters_and_points(self) -> None:
        empty = pd.DataFrame(
            columns=["num", "street_key_nodir", "county", "pct", "pre_dir", "post_dir"]
        )
        voters = _points(
            {"num": "900", "street_key_nodir": "MAIN ST", "county": "48001", "pct": "1"}
        )
        assert match_drop_direction(empty, empty).empty
        assert match_drop_direction(voters, empty).tolist() == [UNMATCHED]

    def test_include_unit_fills_missing_unit_column(self) -> None:
        points = _points(
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "E",
                "post_dir": "",
            }
        )
        voters = _points(
            {"num": "900", "street_key_nodir": "MAIN ST", "county": "48001", "pct": "1"}
        )
        classified = classify_problem_keys(points, include_unit=True)
        assert "unit" in classified.columns
        assert match_drop_direction(voters, points, include_unit=True).tolist() == [MATCH]


class TestDirPairUniqueness:
    def test_suffix_only_north_south_same_key_is_problem(self) -> None:
        frame = _points(
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "",
                "post_dir": "N",
                "unit": "",
            },
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "",
                "post_dir": "S",
                "unit": "",
            },
        )
        out = classify_problem_keys(frame, include_unit=False)
        assert out["is_problem"].unique().tolist() == [True]
        assert out["n_dirs"].unique().tolist() == [2]

    def test_prefix_east_and_suffix_east_same_nodir_key_is_problem(self) -> None:
        frame = _points(
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "E",
                "post_dir": "",
                "unit": "",
            },
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "",
                "post_dir": "E",
                "unit": "",
            },
        )
        out = classify_problem_keys(frame, include_unit=False)
        assert out["is_problem"].unique().tolist() == [True]

    def test_match_drop_direction_excludes_suffix_twin(self) -> None:
        points = _points(
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "",
                "post_dir": "N",
            },
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "",
                "post_dir": "S",
            },
        )
        voters = _points(
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
            }
        )
        assert match_drop_direction(voters, points).tolist() == [EXCLUDED_PROBLEM]


class TestUniquenessAtGeography:
    def test_ew_twins_are_a_problem_at_county_not_when_precinct_splits(self) -> None:
        frame = _points(
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "zip5": "75701",
                "pre_dir": "E",
                "post_dir": "",
                "unit": "",
            },
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "2",
                "zip5": "75701",
                "pre_dir": "W",
                "post_dir": "",
                "unit": "",
            },
        )
        county = uniqueness_at_geography(frame, geography="county", include_unit=False)
        precinct = uniqueness_at_geography(frame, geography="precinct", include_unit=False)
        assert county["n_problem_keys"] == 1
        assert precinct["n_problem_keys"] == 0

    def test_zip_grain_splits_twins_and_missing_zip5_fails_loud(self) -> None:
        frame = _points(
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "zip5": "75701",
                "pre_dir": "E",
                "post_dir": "",
            },
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "zip5": "75702",
                "pre_dir": "W",
                "post_dir": "",
            },
        )
        assert (
            uniqueness_at_geography(frame, geography="zip", include_unit=False)["n_problem_keys"]
            == 0
        )
        assert (
            uniqueness_at_geography(frame, geography="precinct", include_unit=False)[
                "n_problem_keys"
            ]
            == 1
        )
        no_zip = frame.drop(columns=["zip5"])
        with pytest.raises(ValueError, match="zip5"):
            uniqueness_at_geography(no_zip, geography="zip", include_unit=False)


class TestCrossPrecinctTwins:
    def test_cross_precinct_twins_are_unique_at_pct_problem_at_county(self) -> None:
        frame = _points(
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "E",
                "post_dir": "",
            },
            {
                "num": "900",
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "2",
                "pre_dir": "W",
                "post_dir": "",
            },
            {
                "num": "100",
                "street_key_nodir": "OAK AVE",
                "county": "48001",
                "pct": "1",
                "pre_dir": "N",
                "post_dir": "",
            },
            {
                "num": "100",
                "street_key_nodir": "OAK AVE",
                "county": "48001",
                "pct": "1",
                "pre_dir": "S",
                "post_dir": "",
            },
        )
        out = cross_precinct_twin_counts(frame)
        assert out["n_twin_keys_split_by_precinct"] == 1
        assert out["n_points_on_split_twins"] == 2


class TestProblemPatterns:
    def test_ew_prefix_suffix_blank_and_position(self) -> None:
        ew = _points(
            {
                "num": "1",
                "street_key_nodir": "A ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "E",
                "post_dir": "",
            },
            {
                "num": "1",
                "street_key_nodir": "A ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "W",
                "post_dir": "",
            },
        )
        suffix = _points(
            {
                "num": "2",
                "street_key_nodir": "B ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "",
                "post_dir": "N",
            },
            {
                "num": "2",
                "street_key_nodir": "B ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "",
                "post_dir": "S",
            },
        )
        blank = _points(
            {
                "num": "3",
                "street_key_nodir": "C ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "E",
                "post_dir": "",
            },
            {
                "num": "3",
                "street_key_nodir": "C ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "",
                "post_dir": "",
            },
        )
        position = _points(
            {
                "num": "4",
                "street_key_nodir": "D ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "E",
                "post_dir": "",
            },
            {
                "num": "4",
                "street_key_nodir": "D ST",
                "county": "48001",
                "pct": "1",
                "pre_dir": "",
                "post_dir": "E",
            },
        )
        combined = pd.concat([ew, suffix, blank, position], ignore_index=True)
        out = problem_pattern_counts(combined)
        assert out["ew_prefix"] == 1
        assert out["suffix_only"] == 1
        assert out["blank_vs_dir"] == 1
        assert out["prefix_vs_suffix"] == 1
