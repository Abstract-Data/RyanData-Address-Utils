"""Geopandas loaders with gpd mocked so CI does not need the extra."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

pytest.importorskip("pandas")

import pandas as pd  # noqa: E402

from ryandata_address_utils.match import geo  # noqa: E402


def test_require_geopandas_message(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    real_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object):
        if name == "geopandas":
            raise ImportError("no gpd")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ImportError, match="ryandata-address-utils\\[geo\\]"):
        geo.require_geopandas()


def test_attach_precincts_empty_layer(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    layer = MagicMock()
    layer.crs = None
    layer.empty = True
    layer.columns = []
    gpd = MagicMock()
    gpd.read_file.return_value = layer
    monkeypatch.setattr(geo, "require_geopandas", lambda: gpd)
    frame = pd.DataFrame({"lon": [0.0], "lat": [0.0]})
    out = geo.attach_precincts(frame, tmp_path / "p.shp")
    assert out["pct"].tolist() == [""]


def test_attach_precincts_joins(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    layer = MagicMock()
    layer.crs = None
    layer.empty = False
    layer.columns = ["PREC", "CNTY", "geometry"]
    layer.__contains__.side_effect = lambda key: key in {"PREC", "CNTY", "geometry"}
    layer.loc = layer
    layer.__getitem__.side_effect = lambda cols: layer
    pts = MagicMock()
    pts.index = pd.RangeIndex(1)
    gpd = MagicMock()
    gpd.read_file.return_value = layer
    gpd.GeoDataFrame.return_value = pts
    gpd.points_from_xy.return_value = None
    joined = pd.DataFrame({"PREC": ["0003"]})
    gpd.sjoin.return_value = joined
    monkeypatch.setattr(geo, "require_geopandas", lambda: gpd)
    frame = pd.DataFrame({"lon": [-95.0], "lat": [31.0]})
    out = geo.attach_precincts(frame, tmp_path / "p.shp", county_fips="48001")
    assert out["pct"].tolist() == ["3"]


def test_load_txgio_missing_zip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(geo, "require_geopandas", lambda: MagicMock())
    out = geo.load_txgio_points(tmp_path, "48001", tmp_path / "p.shp")
    assert list(out.columns) == ["num", "street_key_nodir", "county", "pct", "dir", "lon", "lat"]
    assert out.empty


def test_load_txgio_zip_without_shp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import zipfile

    zpath = tmp_path / "x_48001_ap.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("readme.txt", "no shp")
    monkeypatch.setattr(geo, "require_geopandas", lambda: MagicMock())
    with pytest.raises(FileNotFoundError, match="no shapefile"):
        geo.load_txgio_points(tmp_path, "48001", tmp_path / "p.shp")


def test_load_tiger_ranges_without_fullname(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    gdf = MagicMock()
    gdf.crs = None
    gdf.columns = ["LFROMHN", "LTOHN", "RFROMHN", "RTOHN"]
    gdf.__contains__.side_effect = lambda key: key in gdf.columns
    gdf.__len__.return_value = 1

    def _col(key: object) -> pd.Series:
        text = str(key)
        return pd.Series(["100"] if "FROM" in text or "TO" in text else [""])

    gdf.__getitem__.side_effect = _col
    gdf.geometry = SimpleNamespace(centroid=SimpleNamespace(x=pd.Series([0.0]), y=pd.Series([0.0])))
    gpd = MagicMock()
    gpd.read_file.return_value = gdf
    monkeypatch.setattr(geo, "require_geopandas", lambda: gpd)
    monkeypatch.setattr(
        geo,
        "attach_precincts",
        lambda frame, path, **k: frame.assign(pct="1"),
    )
    out = geo.load_tiger_ranges(tmp_path / "tl.shp", "48001", tmp_path / "p.shp")
    assert out["pct"].tolist() == ["1"]
    assert "lfrom" in out.columns
