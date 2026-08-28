"""Geopandas loaders: precinct PIP onto TxGIO points and ADDRFEAT centroids."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ryandata_address_utils.match.fetch.tiger import _existing_shp
from ryandata_address_utils.match.keys import (
    as_str_series,
    canon_dir_series,
    fullname_dir_and_nodir_key,
    precinct_series,
    require_pandas,
)
from ryandata_address_utils.match.ranges import addrfeat_range_field_names
from ryandata_address_utils.match.voters import street_key_series

CRS = "EPSG:4326"


def require_geopandas() -> Any:
    """Import geopandas or raise an install hint for the extra."""
    try:
        import geopandas as gpd  # ty: ignore[unresolved-import]
    except ImportError as exc:
        msg = (
            "ryandata_address_utils.match geo loaders require geopandas. "
            'Install with: pip install "ryandata-address-utils[geo]"'
        )
        raise ImportError(msg) from exc
    return gpd


def attach_precincts(
    frame: Any,
    precincts_path: Path,
    *,
    lon_col: str = "lon",
    lat_col: str = "lat",
    county_fips: str | None = None,
) -> Any:
    """Point-in-polygon TLC ``PREC`` onto rows with lon/lat. Adds ``pct``."""
    gpd = require_geopandas()
    pd = require_pandas()
    layer = gpd.read_file(precincts_path)
    if layer.crs is not None and str(layer.crs) != CRS:
        layer = layer.to_crs(CRS)
    if county_fips and "CNTY" in layer.columns:
        county_part = int(str(county_fips)[2:])
        layer = layer.loc[layer["CNTY"] == county_part]
    if layer.empty or "PREC" not in layer.columns:
        out = frame.copy()
        out["pct"] = ""
        return out
    pts = gpd.GeoDataFrame(
        frame.copy(),
        geometry=gpd.points_from_xy(frame[lon_col], frame[lat_col]),
        crs=CRS,
    )
    joined = gpd.sjoin(pts, layer[["PREC", "geometry"]], how="left", predicate="within")
    joined = joined[~joined.index.duplicated(keep="first")].reindex(pts.index)
    out = pd.DataFrame(frame).copy()
    out["pct"] = precinct_series(joined["PREC"]).to_numpy()
    return out


def load_txgio_points(zip_or_dir: Path, fips: str, precincts_path: Path) -> Any:
    """Read one county TxGIO ZIP (or directory of ZIPs) and attach precinct."""
    gpd = require_geopandas()
    pd = require_pandas()
    zip_path = Path(zip_or_dir)
    if zip_path.is_dir():
        matches = list(zip_path.glob(f"*_{fips}_ap.zip"))
        if not matches:
            return pd.DataFrame(
                columns=[
                    "num",
                    "street_key_nodir",
                    "county",
                    "pct",
                    "pre_dir",
                    "post_dir",
                    "zip5",
                    "lon",
                    "lat",
                ]
            )
        zip_path = matches[0]
    import zipfile

    inner = None
    with zipfile.ZipFile(zip_path) as archive:
        inner = next((n for n in archive.namelist() if n.lower().endswith(".shp")), None)
    if inner is None:
        raise FileNotFoundError(f"{zip_path} has no shapefile")
    gdf = gpd.read_file(f"/vsizip/{zip_path}/{inner}")
    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(CRS)
    pdf = pd.DataFrame(
        {
            "num": as_str_series(
                gdf["Add_Number"] if "Add_Number" in gdf.columns else ""
            ).to_numpy(),
            "street_key_nodir": street_key_series(
                gdf["St_Name"] if "St_Name" in gdf.columns else pd.Series([""] * len(gdf)),
                gdf["St_PosTyp"] if "St_PosTyp" in gdf.columns else pd.Series([""] * len(gdf)),
            ).to_numpy(),
            "pre_dir": canon_dir_series(
                gdf["St_PreDir"] if "St_PreDir" in gdf.columns else pd.Series([""] * len(gdf))
            ).to_numpy(),
            "post_dir": canon_dir_series(
                gdf["St_PosDir"] if "St_PosDir" in gdf.columns else pd.Series([""] * len(gdf))
            ).to_numpy(),
            "zip5": as_str_series(
                gdf["Post_Code"] if "Post_Code" in gdf.columns else pd.Series([""] * len(gdf))
            )
            .str.replace(r"\D", "", regex=True)
            .str.slice(0, 5)
            .to_numpy(),
            "lon": gdf.geometry.x.to_numpy(),
            "lat": gdf.geometry.y.to_numpy(),
            "county": fips,
        }
    )
    if "St_PreTyp" in gdf.columns:
        pdf["street_key_nodir"] = street_key_series(
            (
                as_str_series(gdf["St_PreTyp"])
                + " "
                + as_str_series(gdf["St_Name"] if "St_Name" in gdf.columns else "")
            ).str.strip(),
            gdf["St_PosTyp"] if "St_PosTyp" in gdf.columns else pd.Series([""] * len(gdf)),
        ).to_numpy()
    return attach_precincts(pdf, precincts_path, county_fips=fips)


def load_tiger_ranges(shp: Path, fips: str, precincts_path: Path) -> Any:
    """Read one ADDRFEAT shapefile, attach precinct on centroids."""
    gpd = require_geopandas()
    pd = require_pandas()
    shp_path = Path(shp)
    if shp_path.is_dir():
        resolved = _existing_shp(shp_path, fips)
        if resolved is None:
            raise FileNotFoundError(f"No ADDRFEAT shapefile for {fips} in {shp_path}")
        shp_path = resolved
    gdf = gpd.read_file(shp_path)
    if gdf.crs is not None and str(gdf.crs) != CRS:
        gdf = gdf.to_crs(CRS)
    cents = gdf.geometry.centroid
    lfrom_c, lto_c, rfrom_c, rto_c = addrfeat_range_field_names(list(gdf.columns))
    if "FULLNAME" in gdf.columns:
        fullnames = gdf["FULLNAME"].astype(str)
    else:
        fullnames = pd.Series([""] * len(gdf))
    dirs: list[str] = []
    pres: list[str] = []
    posts: list[str] = []
    keys: list[str] = []
    for name in fullnames.tolist():
        pair, key = fullname_dir_and_nodir_key(name)
        pre, _, post = pair.partition("|")
        dirs.append(pair)
        pres.append(pre)
        posts.append(post)
        keys.append(key)
    pdf = pd.DataFrame(
        {
            "street_key_nodir": keys,
            "pre_dir": pres,
            "post_dir": posts,
            "dir": dirs,
            "lfrom": gdf[lfrom_c].astype(str) if lfrom_c else "",
            "lto": gdf[lto_c].astype(str) if lto_c else "",
            "rfrom": gdf[rfrom_c].astype(str) if rfrom_c else "",
            "rto": gdf[rto_c].astype(str) if rto_c else "",
            "lon": cents.x.to_numpy(),
            "lat": cents.y.to_numpy(),
            "county": fips,
        }
    )
    return attach_precincts(pdf, precincts_path, county_fips=fips)
