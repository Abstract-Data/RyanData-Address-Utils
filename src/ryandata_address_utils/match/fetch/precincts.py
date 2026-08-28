"""Texas Legislative Council election-precinct shapefile downloader."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from ryandata_address_utils.match.fetch.http import Opener, download_file, json_get

TX_CKAN_API = "https://data.capitol.texas.gov/api/3/action/package_show"
TX_PRECINCTS_DATASET = "precincts"
_PRECINCT_NAME_RE = re.compile(r"precincts(\d{2})([pg])", re.IGNORECASE)


def parse_election_precinct_filename(name: str) -> tuple[int, str] | None:
    """Parse ``Precincts26P.shp`` / ``Precincts24G.zip`` into ``(year, kind)``."""
    match = _PRECINCT_NAME_RE.search(Path(name).name)
    if match is None:
        return None
    return 2000 + int(match.group(1)), match.group(2).upper()


def staged_precinct_filename(year: int, kind: str) -> str:
    """On-disk shapefile name: ``Precincts26P.shp`` from year and P/G kind."""
    return f"Precincts{year % 100:02d}{kind.upper()}.shp"


def _rank_key(year: int, kind: str) -> tuple[int, int]:
    """Sort key: newer year first; general (G) beats primary (P) in a year."""
    return year, 1 if kind.upper() == "G" else 0


def parse_tlc_precinct_resource(name: str, fmt: str) -> tuple[int, str, str] | None:
    """Classify a CKAN resource as shapefile, districts workbook, or skip."""
    parsed = parse_election_precinct_filename(name)
    if parsed is None:
        return None
    year, kind = parsed
    name_lower = name.lower()
    fmt_upper = (fmt or "").upper()
    if "district" in name_lower:
        return year, kind, "districts"
    if fmt_upper in {"SHP", "ZIP", ""} or name_lower.endswith(".zip"):
        return year, kind, "shp"
    return None


def rank_tlc_precinct_resources(resources: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Newest year wins; within a year G beats P. District workbooks are not shapefiles."""
    shp_candidates: list[dict[str, Any]] = []
    district_candidates: list[dict[str, Any]] = []
    for res in resources:
        name = str(res.get("name") or "")
        fmt = str(res.get("format") or "")
        parsed = parse_tlc_precinct_resource(name, fmt)
        if parsed is None:
            continue
        year, kind, role = parsed
        payload = {
            "year": year,
            "kind": kind,
            "name": name,
            "url": str(res.get("url") or ""),
            "format": fmt,
        }
        if role == "districts":
            district_candidates.append(payload)
        else:
            shp_candidates.append(payload)
    if not shp_candidates:
        return None
    shp = max(shp_candidates, key=lambda c: _rank_key(int(c["year"]), str(c["kind"])))
    matching = [
        d for d in district_candidates if d["year"] == shp["year"] and d["kind"] == shp["kind"]
    ]
    return {"shp": shp, "districts": matching[0] if matching else None}


def fetch_tx_precincts(
    dest: Path,
    *,
    force: bool = False,
    opener: Opener | None = None,
) -> Path:
    """Download the current TLC precinct shapefile into ``dest``."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    payload = json_get(TX_CKAN_API, params={"id": TX_PRECINCTS_DATASET}, opener=opener)
    if not payload.get("success"):
        raise RuntimeError("CKAN package_show failed for TLC precincts")
    resources = list(payload.get("result", {}).get("resources") or [])
    pick = rank_tlc_precinct_resources(resources)
    if pick is None:
        raise FileNotFoundError("No Precincts##P/G shapefile on the TLC portal")
    shp_meta = pick["shp"]
    year = int(shp_meta["year"])
    kind = str(shp_meta["kind"])
    target = dest / staged_precinct_filename(year, kind)
    if target.exists() and not force:
        return target
    url = str(shp_meta.get("url") or "")
    if not url:
        raise FileNotFoundError("Ranked TLC precinct resource has no URL")
    zip_path = dest / f"{target.stem}.zip"
    download_file(url, zip_path, force=force, opener=opener)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(tmp_path)
        shps = list(tmp_path.rglob("*.shp"))
        if not shps:
            raise FileNotFoundError(f"{zip_path} contained no .shp")
        src = next(
            (s for s in shps if parse_election_precinct_filename(s.name) == (year, kind)),
            shps[0],
        )
        for sibling in src.parent.iterdir():
            if sibling.is_file() and sibling.stem == src.stem:
                shutil.copy2(sibling, dest / f"{target.stem}{sibling.suffix}")
    sidecar = {
        "filename": target.name,
        "year": year,
        "kind": kind,
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
    }
    (dest / "current.json").write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")
    if not target.exists():
        raise FileNotFoundError(f"Failed to stage {target.name}")
    return target
