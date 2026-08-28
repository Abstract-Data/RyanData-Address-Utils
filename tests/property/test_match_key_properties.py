"""Properties for scalar key parsers and ADDRFEAT ranges."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from ryandata_address_utils.match import (
    canon_dir,
    dir_pair_canon,
    drop_direction_key,
    fullname_dir_and_nodir_key,
    house_in_addrfeat_range,
    house_int,
    normalize_precinct_code,
)

DIRECTIONS = {
    "NORTH": "N",
    "SOUTH": "S",
    "EAST": "E",
    "WEST": "W",
    "NORTHEAST": "NE",
    "NORTHWEST": "NW",
    "SOUTHEAST": "SE",
    "SOUTHWEST": "SW",
}


@given(direction=st.sampled_from(tuple(DIRECTIONS)), padding=st.text(alphabet=" \t", max_size=4))
def test_canon_dir_handles_words_abbreviations_case_and_padding(
    direction: str, padding: str
) -> None:
    abbreviation = DIRECTIONS[direction]
    assert canon_dir(f"{padding}{direction.lower()}{padding}") == abbreviation
    assert canon_dir(f"{padding}{abbreviation.lower()}{padding}") == abbreviation


@given(
    precinct=st.integers(min_value=0, max_value=999_999),
    prefix=st.sampled_from(["", "PCT ", "PREC ", "PRECINCT ", "VP "]),
    width=st.integers(min_value=1, max_value=8),
)
def test_precinct_parser_normalizes_labels_and_zero_padding(
    precinct: int, prefix: str, width: int
) -> None:
    assert normalize_precinct_code(prefix + str(precinct).zfill(width)) == str(precinct)


@given(number=st.integers(min_value=0, max_value=2_147_483_647))
def test_house_parser_accepts_full_nonnegative_integer_range(number: int) -> None:
    assert house_int(f"APT-{number}-B") == number


@given(
    number=st.integers(min_value=0, max_value=999_999),
    county=st.from_regex(r"48[0-9]{3}", fullmatch=True),
    precinct=st.integers(min_value=0, max_value=9999),
)
def test_drop_direction_key_preserves_components_and_normalizes_precinct(
    number: int, county: str, precinct: int
) -> None:
    key = drop_direction_key(str(number), "main", "st", county, f"PCT {precinct:04d}")
    assert key == f"{number}|MAIN ST|{county}|{precinct}"


@given(
    direction=st.sampled_from(tuple(DIRECTIONS) + tuple(DIRECTIONS.values())),
    street=st.sampled_from(["MAIN ST", "LOOP 1604", "FM  road 12"]),
)
def test_fullname_parser_removes_leading_or_trailing_direction(direction: str, street: str) -> None:
    expected_street = " ".join(street.upper().split())
    leading = fullname_dir_and_nodir_key(f"{direction.lower()} {street}")
    trailing = fullname_dir_and_nodir_key(f"{street} {direction.lower()}")
    assert leading == (dir_pair_canon(direction, ""), expected_street)
    assert trailing == (dir_pair_canon("", direction), expected_street)
    assert leading[0] != trailing[0]


@given(
    house=st.integers(min_value=0, max_value=999_999),
    start=st.integers(min_value=0, max_value=999_999),
    end=st.integers(min_value=0, max_value=999_999),
    use_right=st.booleans(),
)
def test_addrfeat_range_parser_handles_bounds_parity_and_both_sides(
    house: int, start: int, end: int, use_right: bool
) -> None:
    lo, hi = sorted((start, end))
    expected = lo <= house <= hi and (lo % 2 != hi % 2 or house % 2 == lo % 2)
    if use_right:
        actual = house_in_addrfeat_range(str(house), "", "", str(start), str(end))
    else:
        actual = house_in_addrfeat_range(str(house), str(start), str(end), "", "")
    assert actual is expected
