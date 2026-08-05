# AGENTS-pisd.md — AI Coding Assistant Guide: `pisd_shape` Module

**Version:** 1.0.0
**Module:** `pisd_shape` (Pflugerville ISD Attendance Boundary Shapefile Extractor)
**Environment:** Python 3.12+, uv, ruff, pytest, GitHub Actions CI
**Model:** Claude Sonnet 4.6 (claude-sonnet-4-6)
**Repository:** `Abstract-Data/RyanData-Address-Utils`
**Branch convention:** `claude/<slug>-<id>` (e.g., `claude/continue-work-uO5cO`)

---

## Module Purpose

`pisd_shape` extracts Pflugerville ISD (PFISD) school attendance boundary layers from an ArcGIS
Experience Builder WebMap and writes them as ESRI Shapefiles for use in GIS tools (QGIS, ArcGIS Pro, etc.).

Layers extracted:
- `Elementary_School_Locations` — point geometries, school site locations
- `Elementary_Schools_2025-26` — polygon attendance boundaries
- `Middle_School_Locations` — point geometries
- `Middle_Schools_2025-26` — polygon attendance boundaries
- `High_School_Locations` — point geometries
- `High_Schools_2025-26` — polygon attendance boundaries
- `Pflugerville_ISD_Boundary` — district boundary polygon

**Source:** https://experience.arcgis.com/experience/0bc78994af534cd1a703c8959abeac9d
**WebMap JSON:** `https://Pflugervilleisd.maps.arcgis.com/sharing/rest/content/items/bb587c1043a949cca04f1b1904c235e3/data?f=json`

---

## Agent Scope

### Reads
- `src/pisd_shape/pfisd_extract_shapefiles.py` — only source file in this module
- `src/pisd_shape/__init__.py` — module docstring
- `src/pisd_shape/export/` — output shapefiles (read-only reference; agent does not parse them)
- `pyproject.toml` — dependency and tool config

### Writes
- `src/pisd_shape/pfisd_extract_shapefiles.py` — geometry helpers, layer extraction, CLI
- `src/pisd_shape/__init__.py` — module-level exports if any are added
- `src/pisd_shape/export/` — shapefile outputs (`.shp`, `.dbf`, `.shx`, `.prj`, `.cpg`)
- `tests/` — new test files for `pisd_shape` (currently no tests exist)

### Executes
```bash
python src/pisd_shape/pfisd_extract_shapefiles.py                  # fetch from ArcGIS Online
python src/pisd_shape/pfisd_extract_shapefiles.py --local data.json  # load from local JSON
uv run ruff check src/pisd_shape/                                   # lint
uv run ruff format src/pisd_shape/                                  # format
uv run ty check src/pisd_shape/                                     # type check
uv run pytest tests/ -k pisd                                        # run pisd-specific tests
```

### Off-limits (do not touch without explicit instruction)
- `src/ryandata_address_utils/` — main address parsing package; unrelated to this module
- `tests/test_address_parser.py`, `test_factories.py`, `test_unified_model.py`, etc.
- `.github/workflows/` — CI configuration
- `pyproject.toml` `[project.scripts]` section — no CLI entrypoint for pisd_shape currently

---

## File Structure

```
src/pisd_shape/
├── __init__.py                     # Module docstring only; no public API exports yet
└── pfisd_extract_shapefiles.py     # All logic: fetch → parse → reproject → write shapefiles
    ├── CONFIG block                # WEBMAP_URL, OUTPUT_DIR, transformer (EPSG:3857 → 4326)
    ├── Geometry helpers            # reproject_ring(), esri_polygon_to_shapely(), esri_point_to_shapely()
    ├── Layer extraction            # extract_layer() → GeoDataFrame
    ├── Filename sanitizer          # safe_filename()
    └── main()                      # argparse CLI + orchestration

src/pisd_shape/export/              # Committed shapefile outputs (pre-extracted)
├── Elementary_School_Locations.*
├── Elementary_Schools_2025-26.*
├── Middle_School_Locations.*
├── Middle_Schools_2025-26.*
├── High_School_Locations.*
├── High_Schools_2025-26.*
└── Pflugerville_ISD_Boundary.*
```

---

## Data Flow

```
ArcGIS Online WebMap JSON
        │
        ▼  requests.get(WEBMAP_URL)  [or --local <file>]
webmap["operationalLayers"]
        │
        ▼  for each layer
layer["featureCollection"]["layers"]
        │
        ▼  extract_layer(sub_layer, title)
featureSet["features"]
        │
        ├─ esriGeometryPolygon → esri_polygon_to_shapely()
        │       └─ reproject_ring()  [EPSG:3857 → EPSG:4326 via pyproj.Transformer]
        │              └─ Polygon / MultiPolygon (Shapely, .buffer(0) cleaned)
        │
        └─ esriGeometryPoint → esri_point_to_shapely()
                └─ transformer.transform(x, y) → Point (Shapely)
                        │
                        ▼
                gpd.GeoDataFrame(rows, crs="EPSG:4326")
                        │
                        ▼  gdf.to_file(path, driver="ESRI Shapefile")
                src/pisd_shape/export/<safe_filename>.shp
```

### Key data facts
- All source geometry is **Web Mercator (EPSG:3857)**; output is always **WGS84 (EPSG:4326)**
- Layers are **inline Feature Collections** — there is no FeatureServer REST endpoint to query
- ESRI polygon rings use winding order for outer/hole distinction; current code treats each ring as an
  independent polygon with `buffer(0)` cleanup (acceptable for boundary data)
- Shapefile field names are truncated to **10 characters** (dBASE III limitation)
- Missing or empty geometries are skipped and counted; the module logs warnings, not exceptions

---

## CLI Reference

```bash
# Fetch live from ArcGIS Online (requires network access):
python src/pisd_shape/pfisd_extract_shapefiles.py

# Use a pre-downloaded local WebMap JSON (for offline/testing):
python src/pisd_shape/pfisd_extract_shapefiles.py --local path/to/webmap.json
python src/pisd_shape/pfisd_extract_shapefiles.py -l path/to/webmap.json
```

There is currently **no `pyproject.toml` script entrypoint** for this module. Run it directly
via `python` or add one under `[project.scripts]` if a CLI entrypoint is needed.

---

## Code Style

### General
- **Python version:** 3.12+ (matches `pyproject.toml` `requires-python`)
- **Line length:** 100 characters (matches `[tool.ruff]` config)
- **Formatter/linter:** `ruff format` + `ruff check` with `E, F, I, UP, B, SIM` rules
- **Type checker:** `ty` (repo-wide `[tool.ty.environment]` in pyproject.toml). GIS deps
  (`geopandas`, `pyproj`, `shapely`) aren't a dev dependency — heavy, unrelated to the main
  package, and this module isn't part of the built wheel — so their imports carry a per-line
  `# ty: ignore[unresolved-import]` rather than a blanket ignore-missing-imports setting.
- **Function names:** `snake_case`
- **Class names:** `PascalCase` (none currently exist in this module)
- **Type hints:** required on all function signatures

### Geometry helpers pattern
```python
def reproject_ring(ring: list[list[float]]) -> list[tuple[float, float]]:
    """Convert a list of [x, y] Web Mercator coords to (lon, lat) WGS84."""
    return [transformer.transform(x, y) for x, y in ring]
```

### Layer extraction pattern
```python
def extract_layer(layer_data: dict, layer_title: str) -> gpd.GeoDataFrame | None:
    """Return a GeoDataFrame for a single ESRI featureCollection layer, or None on failure."""
    ...
    rows: list[dict] = []
    skipped = 0
    for feat in features:
        geom = ...  # dispatch by geom_type
        if geom is None or geom.is_empty:
            skipped += 1
            continue
        row = {"geometry": geom}
        row.update(attrs)
        rows.append(row)
    ...
    return gpd.GeoDataFrame(rows, crs="EPSG:4326")
```

### Warning/error output convention
- Use `print(f"  [WARN] ...")` for recoverable geometry issues
- Use `print(f"  [INFO] ...")` for skipped feature counts
- Use `print(f"[ERROR] ...")` + `sys.exit(1)` for fatal failures (bad URL, unreadable file)
- Do **not** raise exceptions inside `extract_layer`; return `None` and let `main()` skip

---

## Key Dependencies

| Package | Role |
|---------|------|
| `requests` | Fetch WebMap JSON from ArcGIS Online |
| `geopandas` | Build GeoDataFrames; write ESRI Shapefiles via `to_file()` |
| `shapely` | `Polygon`, `MultiPolygon`, `Point` geometry objects |
| `pyproj` | CRS transformation: EPSG:3857 (Web Mercator) → EPSG:4326 (WGS84) |
| `fiona` | Shapefile I/O backend used by geopandas (indirect dependency) |

These are **not** in `pyproject.toml` — they are expected to be installed in the project
environment separately (e.g., `uv pip install geopandas shapely pyproj requests fiona`).
If adding them to `pyproject.toml`, create an optional extras group (e.g., `[project.optional-dependencies] pisd = [...]`).

---

## Testing

There are currently **no tests** for `pisd_shape`. When adding them:

- **Framework:** pytest (already configured in `pyproject.toml`)
- **Test file:** `tests/test_pisd_shape.py`
- **Hypothesis:** use for property-based geometry tests (ring winding, coordinate validity)
- **Offline-first:** always use `--local` fixture JSON, never hit ArcGIS Online in CI

### Testing patterns

```python
import json
import pytest
from pathlib import Path
from src.pisd_shape.pfisd_extract_shapefiles import (
    reproject_ring,
    esri_polygon_to_shapely,
    esri_point_to_shapely,
    extract_layer,
    safe_filename,
)

# Fixture: minimal WebMap JSON (inline, no network required)
POINT_LAYER = {
    "layerDefinition": {"geometryType": "esriGeometryPoint"},
    "featureSet": {
        "features": [
            {"geometry": {"x": -10880000, "y": 3637000}, "attributes": {"NAME": "Pflugerville HS"}}
        ]
    },
}

def test_reproject_ring_returns_lon_lat_tuples():
    ring = [[-10880000, 3637000], [-10881000, 3637000], [-10881000, 3638000]]
    result = reproject_ring(ring)
    assert all(isinstance(pt, tuple) and len(pt) == 2 for pt in result)
    # WGS84 lon in Texas should be roughly -97 to -100
    assert all(-102 < lon < -94 for lon, _ in result)

@pytest.mark.parametrize("title,expected", [
    ("Elementary Schools 2025-26", "Elementary_Schools_2025-26"),
    ("My Layer/Name!", "My_Layer_Name_"),
])
def test_safe_filename(title, expected):
    assert safe_filename(title) == expected

def test_extract_layer_returns_geodataframe_for_valid_points():
    gdf = extract_layer(POINT_LAYER, "Test Layer")
    assert gdf is not None
    assert len(gdf) == 1
    assert gdf.crs.to_epsg() == 4326

def test_extract_layer_returns_none_for_empty_features():
    empty_layer = {
        "layerDefinition": {"geometryType": "esriGeometryPoint"},
        "featureSet": {"features": []},
    }
    assert extract_layer(empty_layer, "Empty") is None
```

---

## Git Workflow

- **Branch convention:** `claude/<slug>-<id>` (current: `claude/continue-work-uO5cO`)
- **Commit style:** [Conventional Commits](https://www.conventionalcommits.org/)
  - `feat(pisd): add argparse --output-dir flag`
  - `fix(pisd): handle empty rings in esri_polygon_to_shapely`
  - `test(pisd): add offline layer extraction tests`
  - `chore(pisd): add geopandas to optional pisd extras in pyproject.toml`
- **Push target:** `origin/claude/continue-work-uO5cO`
- **PR target:** `main`
- **CI checks that must pass:** `ruff check`, `ruff format --check`, `ty check src/`, `pytest`

---

## Security

- **No hardcoded credentials** — the ArcGIS WebMap is a public endpoint requiring no auth token
- **No secrets in code** — if auth is ever added, use `pydantic-settings` with env vars
- **URL validation** — `WEBMAP_URL` is a module-level constant; do not accept user-supplied URLs
  without validation in a future CLI expansion
- **Local file input** — `--local` accepts arbitrary paths; if expanding, validate with `Path.resolve()`
  and check the file exists before `open()`
- **No parameterized queries** — no database; not applicable

---

## Definition of Done

Before marking any change complete:

- [ ] `uv run ruff check src/pisd_shape/` passes with no errors
- [ ] `uv run ruff format src/pisd_shape/` produces no diff
- [ ] `uv run ty check src/pisd_shape/` reports no errors (GIS-import diagnostics are
      expected to be suppressed via `# ty: ignore[unresolved-import]`, not silent)
- [ ] `uv run pytest tests/ -k pisd` passes (or skipped if no tests exist yet)
- [ ] Geometry output projection is WGS84 (EPSG:4326) — verify with `gdf.crs`
- [ ] `safe_filename()` truncates to ≤60 characters and replaces unsafe chars
- [ ] `--local` flag works end-to-end with a saved WebMap JSON fixture
- [ ] No live network calls in tests (mock `requests.get` or use `--local`)
- [ ] Commit message follows conventional commits format

---

## Tool Resolution Priority

When looking up APIs or documentation:

1. **Context7 MCP** (`resolve-library-id` + `get-library-docs`) — first stop for geopandas,
   shapely, pyproj, fiona, requests
2. **GitHub MCP** — check `Abstract-Data/RyanData-Address-Utils` issues/PRs for known problems
3. **Web search** — ArcGIS REST API docs, EPSG.io for CRS details
4. **Read source** — check `src/pisd_shape/pfisd_extract_shapefiles.py` directly before guessing

---

## Boundaries

### ALWAYS DO
- Reproject all output geometry to WGS84 (EPSG:4326) before writing shapefiles
- Apply `.buffer(0)` to Shapely polygons to fix self-intersections from ESRI rings
- Truncate GeoDataFrame column names to 10 characters before `gdf.to_file()`
- Skip `None` or empty geometries with a `[WARN]` log rather than raising an exception
- Use `OUTPUT_DIR.mkdir(parents=True, exist_ok=True)` before writing
- Run `ruff check` and `ty check` before committing

### ASK FIRST
- Adding new CLI flags to `argparse` beyond `--local`
- Adding a `pyproject.toml` script entrypoint for `pisd_shape`
- Adding `pisd` optional dependencies to `pyproject.toml`
- Changing the output directory from `src/pisd_shape/export/` to somewhere else
- Modifying how ESRI winding order is handled (current simplified approach is intentional)
- Adding geometry type support beyond Polygon and Point (e.g., Polyline)
- Committing updated shapefiles in `export/` (large binary files — confirm with user first)

### NEVER DO
- Touch `src/ryandata_address_utils/` — completely separate package from `pisd_shape`
- Make live HTTP requests to ArcGIS Online in automated tests
- Remove the `--local` flag (required for offline/CI use)
- Raise exceptions inside `extract_layer()` — return `None` and let `main()` handle it
- Write output shapefiles outside `src/pisd_shape/export/` without explicit instruction
- Hardcode auth tokens or API keys anywhere in source code
- Force-push to `main`
