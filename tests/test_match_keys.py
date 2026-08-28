"""Scalar key helpers for drop-direction uniqueness (issue #22)."""

from __future__ import annotations

from ryandata_address_utils.match import (
    canon_dir,
    drop_direction_key,
    fullname_dir_and_nodir_key,
    normalize_precinct_code,
)


class TestCanonDir:
    def test_east_collapses_to_e(self) -> None:
        assert canon_dir("EAST") == "E"
        assert canon_dir("E") == "E"
        assert canon_dir(" east ") == "E"

    def test_northeast_is_not_north(self) -> None:
        assert canon_dir("NORTHEAST") == "NE"
        assert canon_dir("NORTH") == "N"

    def test_blank_is_a_real_state(self) -> None:
        assert canon_dir("") == ""
        assert canon_dir(None) == ""
        assert canon_dir("   ") == ""


class TestNormalizePrecinctCode:
    def test_notation_variants_agree(self) -> None:
        assert normalize_precinct_code("PCT 3") == normalize_precinct_code("0003")
        assert normalize_precinct_code("0003") == normalize_precinct_code("3")
        assert normalize_precinct_code("PRECINCT 3") == "3"
        assert normalize_precinct_code("PREC 3") == "3"
        assert normalize_precinct_code("VP 3") == "3"

    def test_all_zeros_stay_zero_not_empty(self) -> None:
        assert normalize_precinct_code("0000") == "0"

    def test_missing_is_empty(self) -> None:
        assert normalize_precinct_code("") == ""
        assert normalize_precinct_code(None) == ""
        assert normalize_precinct_code("NAN") == ""


class TestDropDirectionKey:
    def test_east_and_west_collapse_when_dir_is_dropped(self) -> None:
        east = drop_direction_key("900", "MAIN", "ST", "48001", "1")
        west = drop_direction_key("900", "MAIN", "ST", "48001", "1")
        assert east == west
        assert "MAIN" in east
        assert "ST" in east

    def test_unit_included_splits_keys_unit_ignored_does_not(self) -> None:
        a = drop_direction_key("900", "MAIN", "ST", "48001", "1", unit="#1")
        b = drop_direction_key("900", "MAIN", "ST", "48001", "1", unit="#2")
        c = drop_direction_key("900", "MAIN", "ST", "48001", "1")
        d = drop_direction_key("900", "MAIN", "ST", "48001", "1", unit=None)
        assert a != b
        assert c == d

    def test_pct_notation_does_not_split_the_key(self) -> None:
        a = drop_direction_key("900", "MAIN", "ST", "48001", "PCT 3")
        b = drop_direction_key("900", "MAIN", "ST", "48001", "0003")
        assert a == b


class TestFullnameDirAndNodirKey:
    def test_strips_leading_directional(self) -> None:
        d, key = fullname_dir_and_nodir_key("E MAIN ST")
        assert d == "E"
        assert "MAIN" in key
        assert key == fullname_dir_and_nodir_key("W MAIN ST")[1]

    def test_strips_trailing_sufdir_so_keys_match(self) -> None:
        pre_dir, pre_key = fullname_dir_and_nodir_key("E MAIN ST")
        suf_dir, suf_key = fullname_dir_and_nodir_key("MAIN ST W")
        assert pre_key == suf_key
        assert not pre_key.endswith(" W")
        assert suf_dir == "W"
        loop_dir, loop_key = fullname_dir_and_nodir_key("LOOP 1604 W")
        assert loop_dir == "W"
        assert not loop_key.endswith(" W")
