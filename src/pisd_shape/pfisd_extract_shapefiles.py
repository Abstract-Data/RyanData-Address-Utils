"""
pfisd_extract_shapefiles.py

Extracts all layers from the Pflugerville ISD Attendance Boundaries
ArcGIS Experience Builder app and saves them as shapefiles.

Source:  https://experience.arcgis.com/experience/0bc78994af534cd1a703c8959abeac9d
WebMap:  https://Pflugervilleisd.maps.arcgis.com/sharing/rest/content/items/bb587c1043a949cca04f1b1904c235e3/data

The layers are embedded as inline Feature Collections (no FeatureServer endpoint).
All geometry arrives in Web Mercator (EPSG:3857) and is reprojected to WGS84 (EPSG:4326).

Dependencies:
    pip install requests geopandas shapely pyproj fiona

Output:
    One .shp file per layer, written to ./export/ (relative to this script)
"""

import argparse
import json
import sys
from pathlib import Path

import geopandas as gpd
import requests
from pyproj import Transformer
from shapely.geometry import MultiPolygon, Point, Polygon

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

WEBMAP_URL = (
    "https://Pflugervilleisd.maps.arcgis.com/sharing/rest/content/items/"
    "bb587c1043a949cca04f1b1904c235e3/data?f=json"
)

# Output into the export/ folder inside this package
OUTPUT_DIR = Path(__file__).resolve().parent / "export"

# Source CRS (Web Mercator) → Target CRS (WGS84 lat/lon)
transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

# ─────────────────────────────────────────────
# GEOMETRY HELPERS
# ─────────────────────────────────────────────

def reproject_ring(ring):
    """Convert a list of [x, y] Web Mercator coords to (lon, lat) WGS84."""
    return [transformer.transform(x, y) for x, y in ring]


def esri_polygon_to_shapely(esri_geom):
    """
    Convert an ESRI polygon geometry dict (with 'rings') to a Shapely geometry.
    Handles single polygons and multipolygons (multiple outer rings).
    """
    rings = esri_geom.get("rings", [])
    if not rings:
        return None

    reprojected = [reproject_ring(r) for r in rings]

    # ESRI uses winding order to distinguish outer vs hole rings.
    # For simplicity we treat each ring as its own polygon; Shapely's
    # buffer(0) trick cleans up any self-intersections.
    polys = [Polygon(r) for r in reprojected if len(r) >= 3]
    if not polys:
        return None
    if len(polys) == 1:
        return polys[0].buffer(0)
    return MultiPolygon([p.buffer(0) for p in polys]).buffer(0)


def esri_point_to_shapely(esri_geom):
    """Convert an ESRI point geometry dict to a Shapely Point in WGS84."""
    x = esri_geom.get("x")
    y = esri_geom.get("y")
    if x is None or y is None:
        return None
    lon, lat = transformer.transform(x, y)
    return Point(lon, lat)


# ─────────────────────────────────────────────
# LAYER EXTRACTION
# ─────────────────────────────────────────────

def extract_layer(layer_data, layer_title):
    """
    Given a single ESRI featureCollection layer dict, return a GeoDataFrame.
    Handles both polygon and point geometry types.
    """
    layer_def = layer_data.get("layerDefinition", {})
    feature_set = layer_data.get("featureSet", {})
    geom_type = layer_def.get("geometryType", "")
    features = feature_set.get("features", [])

    if not features:
        print(f"  [WARN] No features found in layer: {layer_title}")
        return None

    rows = []
    skipped = 0

    for feat in features:
        esri_geom = feat.get("geometry", {})
        attrs = feat.get("attributes", {})

        if geom_type == "esriGeometryPolygon":
            geom = esri_polygon_to_shapely(esri_geom)
        elif geom_type == "esriGeometryPoint":
            geom = esri_point_to_shapely(esri_geom)
        else:
            print(f"  [WARN] Unsupported geometry type '{geom_type}' — skipping feature.")
            skipped += 1
            continue

        if geom is None or geom.is_empty:
            skipped += 1
            continue

        row = {"geometry": geom}
        row.update(attrs)
        rows.append(row)

    if skipped:
        print(f"  [INFO] Skipped {skipped} invalid/empty features.")

    if not rows:
        print(f"  [WARN] No valid geometries extracted from: {layer_title}")
        return None

    gdf = gpd.GeoDataFrame(rows, crs="EPSG:4326")
    return gdf


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def safe_filename(title):
    """Strip characters that are unsafe in filenames."""
    keep = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_- "
    name = "".join(c if c in keep else "_" for c in title)
    return name.strip().replace(" ", "_")[:60]


def main():
    parser = argparse.ArgumentParser(description="Extract PFISD attendance boundary shapefiles")
    parser.add_argument(
        "--local", "-l",
        type=str,
        default=None,
        help="Path to a local WebMap JSON file (skip HTTP fetch)",
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR.resolve()}\n")

    # ------------------------------------------------------------------
    # 1. Fetch the WebMap JSON (or load from local file)
    # ------------------------------------------------------------------
    if args.local:
        local_path = Path(args.local)
        print(f"Loading WebMap data from local file: {local_path}")
        try:
            with open(local_path) as f:
                webmap = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load local file: {e}")
            sys.exit(1)
    else:
        print("Fetching WebMap data from ArcGIS Online...")
        try:
            resp = requests.get(WEBMAP_URL, timeout=30)
            resp.raise_for_status()
            webmap = resp.json()
        except Exception as e:
            print(f"[ERROR] Failed to fetch WebMap: {e}")
            sys.exit(1)

    operational_layers = webmap.get("operationalLayers", [])
    if not operational_layers:
        print("[ERROR] No operationalLayers found in WebMap JSON.")
        sys.exit(1)

    print(f"Found {len(operational_layers)} operational layer(s).\n")

    # ------------------------------------------------------------------
    # 2. Iterate layers and export each as a shapefile
    # ------------------------------------------------------------------
    exported = 0

    for layer in operational_layers:
        layer_title = layer.get("title", "unnamed_layer")
        feature_collection = layer.get("featureCollection", {})
        sub_layers = feature_collection.get("layers", [])

        if not sub_layers:
            print(f"[SKIP] '{layer_title}' — no featureCollection layers found.")
            continue

        print(f"Processing: {layer_title}")

        for i, sub_layer in enumerate(sub_layers):
            suffix = f"_{i}" if len(sub_layers) > 1 else ""
            fname = safe_filename(layer_title) + suffix

            gdf = extract_layer(sub_layer, layer_title)
            if gdf is None:
                continue

            out_path = OUTPUT_DIR / f"{fname}.shp"

            # Shapefile field names are limited to 10 characters
            gdf.columns = [c[:10] for c in gdf.columns]

            try:
                gdf.to_file(out_path, driver="ESRI Shapefile")
                print(f"  -> Saved {len(gdf)} features -> {out_path}")
                exported += 1
            except Exception as e:
                print(f"  [ERROR] Could not write {out_path}: {e}")

        print()

    # ------------------------------------------------------------------
    # 3. Summary
    # ------------------------------------------------------------------
    print("-" * 50)
    print(f"Done. {exported} shapefile(s) written to: {OUTPUT_DIR.resolve()}")
    print("\nProjection: WGS84 (EPSG:4326)")
    print("Open in QGIS, ArcGIS Pro, or any GIS tool that reads .shp files.")


if __name__ == "__main__":
    main()
