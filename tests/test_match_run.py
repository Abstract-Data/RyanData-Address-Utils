"""Orchestrator: voterfile path + sources, fetchers injected."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("pandas")

import pandas as pd  # noqa: E402

from ryandata_address_utils.match import MATCH  # noqa: E402
from ryandata_address_utils.match.run import (  # noqa: E402
    default_cache_dir,
    parse_sources,
    run_uniqueness,
)


def test_parse_sources_txgio_tiger_or_both() -> None:
    assert parse_sources("txgio") == ("txgio",)
    assert parse_sources("TIGER") == ("tiger",)
    assert parse_sources("txgio,tiger") == ("txgio", "tiger")
    with pytest.raises(ValueError, match="unknown"):
        parse_sources("census")


def test_run_writes_outcomes_for_both_sources(tmp_path: Path) -> None:
    vf = tmp_path / "vf.csv"
    vf.write_text(
        "COUNTY,PCT,RHNUM,RSTPRE,RSTNAME,RSTTYPE,STATUS\nANDERSON,1,150,E,MAIN,ST,A\n",
        encoding="utf-8",
    )
    cache = tmp_path / "cache"
    out = tmp_path / "out"

    def fetch_txgio(*, fips_list: tuple[str, ...], dest: Path, **kwargs: object) -> Path:
        dest.mkdir(parents=True, exist_ok=True)
        return dest

    def fetch_tiger(*, fips_list: tuple[str, ...], dest: Path, **kwargs: object) -> Path:
        dest.mkdir(parents=True, exist_ok=True)
        return dest

    def fetch_precincts(*, dest: Path, **kwargs: object) -> Path:
        dest.mkdir(parents=True, exist_ok=True)
        marker = dest / "Precincts26P.shp"
        marker.write_text("shp", encoding="utf-8")
        return marker

    points = pd.DataFrame(
        {
            "num": ["150"],
            "street_key_nodir": ["MAIN ST"],
            "county": ["48001"],
            "pct": ["1"],
            "dir": ["E"],
        }
    )
    ranges = pd.DataFrame(
        {
            "street_key_nodir": ["MAIN ST"],
            "county": ["48001"],
            "pct": ["1"],
            "dir": ["E"],
            "lfrom": ["100"],
            "lto": ["198"],
            "rfrom": [""],
            "rto": [""],
        }
    )

    summary = run_uniqueness(
        vf,
        sources="txgio,tiger",
        cache_dir=cache,
        out_dir=out,
        fetch_txgio_fn=fetch_txgio,
        fetch_tiger_fn=fetch_tiger,
        fetch_precincts_fn=fetch_precincts,
        load_txgio_fn=lambda **k: points,
        load_tiger_fn=lambda **k: ranges,
    )
    result = pd.read_csv(out / "outcomes.csv", dtype=str)
    assert result["txgio_outcome"].tolist() == [MATCH]
    assert result["tiger_outcome"].tolist() == [MATCH]
    assert summary["sources"] == ["txgio", "tiger"]
    assert summary["n"] == 1


def test_empty_voterfile_fails(tmp_path: Path) -> None:
    vf = tmp_path / "vf.csv"
    vf.write_text("COUNTY,PCT,RHNUM,RSTNAME,RSTTYPE\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no voter rows"):
        run_uniqueness(
            vf,
            cache_dir=tmp_path / "c",
            out_dir=tmp_path / "o",
            fetch_precincts_fn=lambda **k: tmp_path,
            fetch_txgio_fn=lambda **k: tmp_path,
            load_txgio_fn=lambda **k: pd.DataFrame(),
        )


def test_unknown_county_fails(tmp_path: Path) -> None:
    vf = tmp_path / "vf.csv"
    vf.write_text("COUNTY,PCT,RHNUM,RSTNAME,RSTTYPE\nNARNIA,1,1,MAIN,ST\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unknown county"):
        run_uniqueness(
            vf,
            cache_dir=tmp_path / "c",
            out_dir=tmp_path / "o",
            fetch_precincts_fn=lambda **k: tmp_path,
        )


def test_default_cache_dir_is_home_cache() -> None:
    path = default_cache_dir()
    assert path.name == "ryandata-address-utils"
