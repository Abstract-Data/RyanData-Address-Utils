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
    match_drop_direction,
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
