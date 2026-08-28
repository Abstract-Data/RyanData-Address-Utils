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


def test_parse_sources_empty_defaults_to_txgio() -> None:
    assert parse_sources("") == ("txgio",)
    assert parse_sources(" , ") == ("txgio",)


def _anderson_vf(tmp_path: Path, extra_header: str = "", extra_row: str = "") -> Path:
    vf = tmp_path / "vf.csv"
    header = "COUNTY,PCT,RHNUM,RSTPRE,RSTNAME,RSTTYPE,STATUS" + extra_header
    row = "ANDERSON,1,150,E,MAIN,ST,A" + extra_row
    vf.write_text(f"{header}\n{row}\n", encoding="utf-8")
    return vf


def test_missing_county_column_fails(tmp_path: Path) -> None:
    vf = tmp_path / "vf.csv"
    vf.write_text("PCT,RHNUM,RSTNAME,RSTTYPE\n1,150,MAIN,ST\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no COUNTY column"):
        run_uniqueness(
            vf,
            cache_dir=tmp_path / "c",
            out_dir=tmp_path / "o",
            fetch_precincts_fn=lambda **k: tmp_path,
            fetch_txgio_fn=lambda **k: tmp_path,
            load_txgio_fn=lambda **k: pd.DataFrame(),
        )


def test_default_fetchers_and_loaders_are_imported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vf = _anderson_vf(tmp_path)
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
    calls: list[str] = []

    def fetch_precincts(*, dest: Path, force: bool = False, **kwargs: object) -> Path:
        dest.mkdir(parents=True, exist_ok=True)
        calls.append("precincts")
        marker = dest / "Precincts26P.shp"
        marker.write_text("shp", encoding="utf-8")
        return marker

    def fetch_txgio(*, fips_list: tuple[str, ...], dest: Path, **kwargs: object) -> Path:
        dest.mkdir(parents=True, exist_ok=True)
        calls.append("txgio")
        return dest

    def fetch_tiger(*, fips_list: tuple[str, ...], dest: Path, **kwargs: object) -> Path:
        dest.mkdir(parents=True, exist_ok=True)
        calls.append("tiger")
        return dest

    monkeypatch.setattr(
        "ryandata_address_utils.match.fetch.precincts.fetch_tx_precincts", fetch_precincts
    )
    monkeypatch.setattr(
        "ryandata_address_utils.match.fetch.txgio.fetch_txgio_counties", fetch_txgio
    )
    monkeypatch.setattr(
        "ryandata_address_utils.match.fetch.tiger.fetch_tiger_counties", fetch_tiger
    )
    monkeypatch.setattr(
        "ryandata_address_utils.match.geo.load_txgio_points",
        lambda **k: points,
    )
    monkeypatch.setattr(
        "ryandata_address_utils.match.geo.load_tiger_ranges",
        lambda **k: ranges,
    )
    summary = run_uniqueness(
        vf,
        sources="txgio,tiger",
        cache_dir=tmp_path / "c",
        out_dir=tmp_path / "o",
    )
    assert summary["n"] == 1
    assert "precincts" in calls and "txgio" in calls and "tiger" in calls


def test_skips_fips_with_no_voters_and_concatenates_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ryandata_address_utils.match import voters as voters_mod

    vf = _anderson_vf(tmp_path)
    real_canon = voters_mod.canonicalize_voters

    def drop_county(raw: pd.DataFrame) -> pd.DataFrame:
        out = real_canon(raw)
        out["county"] = "99999"
        return out

    monkeypatch.setattr(voters_mod, "canonicalize_voters", drop_county)
    monkeypatch.setattr("ryandata_address_utils.match.run.canonicalize_voters", drop_county)
    summary = run_uniqueness(
        vf,
        sources="txgio",
        cache_dir=tmp_path / "c",
        out_dir=tmp_path / "o",
        fetch_precincts_fn=lambda **k: tmp_path,
        fetch_txgio_fn=lambda **k: tmp_path,
        load_txgio_fn=lambda **k: pd.DataFrame(
            columns=["num", "street_key_nodir", "county", "pct", "dir"]
        ),
    )
    result = pd.read_csv(tmp_path / "o" / "outcomes.csv", dtype=str)
    assert summary["n"] == 1
    assert result["txgio_outcome"].isna().all() or result["txgio_outcome"].tolist() == [""]


def test_missing_txgio_loader_fails_loud(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    vf = _anderson_vf(tmp_path)
    monkeypatch.setattr("ryandata_address_utils.match.geo.load_txgio_points", None)
    with pytest.raises(RuntimeError, match="txgio loader missing"):
        run_uniqueness(
            vf,
            sources="txgio",
            cache_dir=tmp_path / "c",
            out_dir=tmp_path / "o",
            fetch_precincts_fn=lambda **k: tmp_path,
            fetch_txgio_fn=lambda **k: tmp_path,
        )


def test_missing_tiger_loader_fails_loud(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    vf = _anderson_vf(tmp_path)
    monkeypatch.setattr("ryandata_address_utils.match.geo.load_tiger_ranges", None)
    with pytest.raises(RuntimeError, match="tiger loader missing"):
        run_uniqueness(
            vf,
            sources="tiger",
            cache_dir=tmp_path / "c",
            out_dir=tmp_path / "o",
            fetch_precincts_fn=lambda **k: tmp_path,
            fetch_tiger_fn=lambda **k: tmp_path,
        )
