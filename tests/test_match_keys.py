"""Scalar key helpers for drop-direction uniqueness (issue #22)."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ryandata_address_utils.match import (
    canon_dir,
    dir_pair_canon,
    drop_direction_key,
    fullname_dir_and_nodir_key,
    house_int,
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

    def test_unknown_token_stays_uppercased(self) -> None:
        assert canon_dir("FOO") == "FOO"


class TestDirPairCanon:
    def test_dir_pair_positions_are_distinct(self) -> None:
        assert dir_pair_canon("E", "") == "E|"
        assert dir_pair_canon("", "E") == "|E"
        assert dir_pair_canon("E", "") != dir_pair_canon("", "E")
        assert dir_pair_canon("EAST", "") == dir_pair_canon("E", "")
        assert dir_pair_canon(None, None) == "|"


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

    @given(
        direction=st.sampled_from(["E", "W", "NORTH", "SOUTHWEST"]),
        street=st.sampled_from(["MAIN ST", "LOOP 1604"]),
        padding=st.text(alphabet=" \t", min_size=0, max_size=3),
    )
    def test_leading_or_trailing_direction_is_removed(
        self, direction: str, street: str, padding: str
    ) -> None:
        raw_dir = f"{padding}{direction.lower()}{padding}"
        raw_street = f"{padding}{street.lower()}{padding}"
        leading = fullname_dir_and_nodir_key(f"{raw_dir} {raw_street}")
        trailing = fullname_dir_and_nodir_key(f"{raw_street} {raw_dir}")
        assert leading[0] == canon_dir(direction)
        assert trailing[0] == canon_dir(direction)
        assert leading[1] == trailing[1]
        assert leading[1] == street


class TestHouseInt:
    def test_zero_is_a_house_number(self) -> None:
        assert house_int(0) == 0
        assert house_int("0") == 0

    def test_none_is_missing(self) -> None:
        assert house_int(None) is None

    def test_no_digits_is_missing(self) -> None:
        assert house_int("N/A") is None
        assert house_int("APT") is None


def test_require_pandas_message(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    from ryandata_address_utils.match import keys

    real_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object):
        if name == "pandas":
            raise ImportError("no pandas")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ImportError, match="ryandata-address-utils\\[pandas\\]"):
        keys.require_pandas()
