"""ADDRFEAT house-range matching (issue #22)."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ryandata_address_utils.match import (
    EXCLUDED_PROBLEM,
    MATCH,
    UNMATCHED,
    addrfeat_range_field_names,
    house_in_addrfeat_range,
    match_addrfeat_ranges,
)

pytest.importorskip("pandas")

import pandas as pd  # noqa: E402


class TestAddrfeatRangeFields:
    def test_tiger_2024_lfromadd_names(self) -> None:
        assert addrfeat_range_field_names(
            ["LFROMADD", "LTOADD", "RFROMADD", "RTOADD", "FULLNAME"]
        ) == ("LFROMADD", "LTOADD", "RFROMADD", "RTOADD")

    def test_tiger_2025_lfromhn_names(self) -> None:
        assert addrfeat_range_field_names(["LFROMHN", "LTOHN", "RFROMHN", "RTOHN", "FULLNAME"]) == (
            "LFROMHN",
            "LTOHN",
            "RFROMHN",
            "RTOHN",
        )

    def test_2024_names_win_when_both_present(self) -> None:
        assert addrfeat_range_field_names(
            ["LFROMADD", "LFROMHN", "LTOADD", "LTOHN", "RFROMADD", "RFROMHN", "RTOADD", "RTOHN"]
        ) == ("LFROMADD", "LTOADD", "RFROMADD", "RTOADD")


class TestAddrfeatRange:
    def test_even_house_inside_left_range_matches(self) -> None:
        assert house_in_addrfeat_range("150", "100", "198", "", "") is True

    def test_house_outside_range_misses(self) -> None:
        assert house_in_addrfeat_range("199", "100", "198", "", "") is False

    def test_right_side_range_matches(self) -> None:
        assert house_in_addrfeat_range("101", "", "", "101", "199") is True

    def test_even_house_does_not_match_odd_side(self) -> None:
        assert house_in_addrfeat_range("150", "", "", "101", "199") is False

    def test_hyphenated_house_uses_leading_digits(self) -> None:
        assert house_in_addrfeat_range("150-1/2", "100", "198", "", "") is True

    def test_reversed_from_to_still_covers(self) -> None:
        assert house_in_addrfeat_range("150", "198", "100", "", "") is True

    @given(
        house=st.integers(min_value=1, max_value=9999),
        start=st.integers(min_value=1, max_value=9999),
        end=st.integers(min_value=1, max_value=9999),
        use_right=st.booleans(),
    )
    def test_matches_normalized_bounds_and_parity(
        self, house: int, start: int, end: int, use_right: bool
    ) -> None:
        lo, hi = (start, end) if start <= end else (end, start)
        expected = lo <= house <= hi
        if expected and lo % 2 == hi % 2 and house % 2 != lo % 2:
            expected = False
        if use_right:
            got = house_in_addrfeat_range(str(house), "", "", str(start), str(end))
        else:
            got = house_in_addrfeat_range(str(house), str(start), str(end), "", "")
        assert got is expected


class TestMatchAddrfeatRanges:
    def _ranges(self, *rows: dict[str, object]) -> pd.DataFrame:
        return pd.DataFrame(list(rows))

    def test_house_in_unique_range_matches(self) -> None:
        ranges = self._ranges(
            {
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "dir": "E",
                "lfrom": "100",
                "lto": "198",
                "rfrom": "",
                "rto": "",
            }
        )
        voters = pd.DataFrame(
            {
                "num": ["150"],
                "street_key_nodir": ["MAIN ST"],
                "county": ["48001"],
                "pct": ["1"],
            }
        )
        assert match_addrfeat_ranges(voters, ranges).tolist() == [MATCH]

    def test_east_and_west_covering_same_number_is_problem(self) -> None:
        ranges = self._ranges(
            {
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "dir": "E",
                "lfrom": "100",
                "lto": "198",
                "rfrom": "",
                "rto": "",
            },
            {
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "dir": "W",
                "lfrom": "100",
                "lto": "198",
                "rfrom": "",
                "rto": "",
            },
        )
        voters = pd.DataFrame(
            {
                "num": ["150"],
                "street_key_nodir": ["MAIN ST"],
                "county": ["48001"],
                "pct": ["1"],
            }
        )
        assert match_addrfeat_ranges(voters, ranges).tolist() == [EXCLUDED_PROBLEM]

    def test_even_east_odd_west_is_unique_not_a_problem(self) -> None:
        ranges = self._ranges(
            {
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "dir": "E",
                "lfrom": "100",
                "lto": "198",
                "rfrom": "",
                "rto": "",
            },
            {
                "street_key_nodir": "MAIN ST",
                "county": "48001",
                "pct": "1",
                "dir": "W",
                "lfrom": "101",
                "lto": "199",
                "rfrom": "",
                "rto": "",
            },
        )
        voters = pd.DataFrame(
            {
                "num": ["150"],
                "street_key_nodir": ["MAIN ST"],
                "county": ["48001"],
                "pct": ["1"],
            }
        )
        assert match_addrfeat_ranges(voters, ranges).tolist() == [MATCH]

    def test_empty_ranges_are_unmatched(self) -> None:
        voters = pd.DataFrame(
            {
                "num": ["150"],
                "street_key_nodir": ["MAIN ST"],
                "county": ["48001"],
                "pct": ["1"],
            }
        )
        ranges = pd.DataFrame(
            columns=["street_key_nodir", "county", "pct", "dir", "lfrom", "lto", "rfrom", "rto"]
        )
        assert match_addrfeat_ranges(voters, ranges).tolist() == [UNMATCHED]
