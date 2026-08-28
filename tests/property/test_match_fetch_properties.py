"""Properties for TLC precinct filename and resource parsing."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from ryandata_address_utils.match.fetch.precincts import (
    parse_election_precinct_filename,
    parse_tlc_precinct_resource,
)


@given(
    year=st.integers(min_value=0, max_value=99),
    kind=st.sampled_from(["P", "G", "p", "g"]),
    extension=st.sampled_from(["shp", "zip", "SHP", "ZIP"]),
)
def test_valid_precinct_filename_parses_year_and_kind(year: int, kind: str, extension: str) -> None:
    name = f"Precincts{year:02d}{kind}.{extension}"
    assert parse_election_precinct_filename(name) == (2000 + year, kind.upper())


@given(
    year=st.integers(min_value=0, max_value=99),
    kind=st.sampled_from(["Q", "X", "1"]),
    prefix=st.sampled_from(["Districts", "Precinct", "Voting"]),
)
def test_invalid_precinct_filenames_return_none(year: int, kind: str, prefix: str) -> None:
    assert parse_election_precinct_filename(f"{prefix}{year:02d}{kind}.shp") is None


@given(
    year=st.integers(min_value=0, max_value=99),
    kind=st.sampled_from(["P", "G"]),
    fmt=st.sampled_from(["SHP", "ZIP", ""]),
)
def test_supported_shapefile_resources_are_classified(year: int, kind: str, fmt: str) -> None:
    name = f"Precincts{year:02d}{kind}.zip"
    assert parse_tlc_precinct_resource(name, fmt) == (2000 + year, kind, "shp")


@given(
    year=st.integers(min_value=0, max_value=99),
    kind=st.sampled_from(["P", "G"]),
    fmt=st.sampled_from(["XLSX", "CSV", ""]),
)
def test_supported_district_resources_are_classified(year: int, kind: str, fmt: str) -> None:
    name = f"Precincts{year:02d}{kind} districts.xlsx"
    assert parse_tlc_precinct_resource(name, fmt) == (2000 + year, kind, "districts")


@given(
    year=st.integers(min_value=0, max_value=99),
    kind=st.sampled_from(["P", "G"]),
    extension=st.sampled_from(["dbf", "csv", "txt"]),
)
def test_unsupported_resource_extensions_return_none(year: int, kind: str, extension: str) -> None:
    name = f"Precincts{year:02d}{kind}.{extension}"
    assert parse_tlc_precinct_resource(name, extension.upper()) is None


@given(name=st.text(alphabet=st.characters(whitelist_categories=("Nd",)), max_size=20))
def test_resources_without_a_supported_role_return_none(name: str) -> None:
    assert parse_tlc_precinct_resource(name, "ZIP") is None
