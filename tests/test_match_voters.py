"""Voter-file canonicalize for uniqueness CLI."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("pandas")

from ryandata_address_utils.match.voters import (  # noqa: E402
    canonicalize_voters,
    component_street_key,
    load_voterfile,
)


def test_sos_columns_become_match_keys(tmp_path: Path) -> None:
    path = tmp_path / "vf.csv"
    path.write_text(
        "COUNTY,PCT,RHNUM,RSTPRE,RSTNAME,RSTTYPE,STATUS\n"
        "ANDERSON,1,900,E,MAIN,ST,A\n"
        "MCLENNAN,3,150,,OAK,AVE,A\n",
        encoding="utf-8",
    )
    raw = load_voterfile(path)
    out = canonicalize_voters(raw)
    assert out["county"].tolist() == ["48001", "48309"]
    assert out["num"].tolist() == ["900", "150"]
    assert out["street_key_nodir"].tolist() == ["MAIN ST", "OAK AVE"]
    assert "E" not in out["street_key_nodir"].iloc[0]


def test_counties_filter(tmp_path: Path) -> None:
    path = tmp_path / "vf.csv"
    path.write_text(
        "COUNTY,PCT,RHNUM,RSTNAME,RSTTYPE\nANDERSON,1,1,MAIN,ST\nTRAVIS,2,2,OAK,AVE\n",
        encoding="utf-8",
    )
    raw = load_voterfile(path, counties=("TRAVIS",))
    assert raw["COUNTY"].tolist() == ["TRAVIS"]


def test_component_street_key_drops_punctuation() -> None:
    assert component_street_key("Main", "St.") == "MAIN ST"
    assert component_street_key("", None) == ""


def test_missing_sos_columns_fail(tmp_path: Path) -> None:
    path = tmp_path / "vf.csv"
    path.write_text("foo,bar\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="expected SOS"):
        load_voterfile(path)


def test_missing_optional_columns_are_blank_and_vuid_is_kept(tmp_path: Path) -> None:
    path = tmp_path / "vf.csv"
    path.write_text("COUNTY,PCT,VUID,RSTNAME\nANDERSON,1,123,MAIN\n", encoding="utf-8")
    raw = load_voterfile(path)
    out = canonicalize_voters(raw)
    assert out["num"].tolist() == [""]
    assert out["vuid"].tolist() == ["123"]
    assert out["street_key_nodir"].tolist() == ["MAIN"]


def test_de_witt_alias_maps_in_canonicalize(tmp_path: Path) -> None:
    path = tmp_path / "vf.csv"
    path.write_text("COUNTY,PCT,RHNUM,RSTNAME,RSTTYPE\nDE WITT,1,1,MAIN,ST\n", encoding="utf-8")
    out = canonicalize_voters(load_voterfile(path))
    assert out["county"].tolist() == ["48123"]
