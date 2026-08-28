"""Census TIGER/Line ADDRFEAT downloader (house-number ranges, not edges/faces)."""

from __future__ import annotations

import zipfile
from pathlib import Path

from ryandata_address_utils.match.fetch.http import Opener, download_file, http_status

TIGER_BASE = "https://www2.census.gov/geo/tiger"
DEFAULT_YEARS: tuple[int, ...] = (2025, 2024)


def addrfeat_url(fips: str, year: int) -> str:
    """``tl_{year}_{fips}_addrfeat.zip`` on the Census TIGER tree."""
    return f"{TIGER_BASE}/TIGER{year}/ADDRFEAT/tl_{year}_{fips}_addrfeat.zip"


def _existing_shp(dest_dir: Path, fips: str) -> Path | None:
    matches = sorted(dest_dir.glob(f"tl_*_{fips}_addrfeat.shp"))
    if len(matches) > 1:
        names = ", ".join(p.name for p in matches)
        raise ValueError(f"expected unique tl_*_{fips}_addrfeat.shp, found {len(matches)}: {names}")
    return matches[0] if matches else None


def fetch_addrfeat(
    fips: str,
    dest_dir: Path,
    *,
    years: tuple[int, ...] = DEFAULT_YEARS,
    force: bool = False,
    opener: Opener | None = None,
) -> Path:
    """Download and extract one county ADDRFEAT shapefile. Try ``years`` in order."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    if not force:
        existing = _existing_shp(dest_dir, fips)
        if existing is not None:
            return existing
    last_error: Exception | None = None
    for year in years:
        url = addrfeat_url(fips, year)
        zip_path = dest_dir / f"tl_{year}_{fips}_addrfeat.zip"
        try:
            download_file(url, zip_path, force=force, opener=opener)
        except Exception as exc:
            if http_status(exc) == 404:
                last_error = exc
                continue
            raise
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(dest_dir)
        shp = _existing_shp(dest_dir, fips)
        if shp is None:
            raise FileNotFoundError(f"{zip_path} contained no ADDRFEAT shapefile")
        return shp
    raise FileNotFoundError(
        f"No ADDRFEAT shapefile for {fips} in years {years}"
        + (f" ({last_error})" if last_error else "")
    )


def fetch_tiger_counties(
    fips_list: tuple[str, ...],
    dest: Path,
    *,
    years: tuple[int, ...] = DEFAULT_YEARS,
    force: bool = False,
    opener: Opener | None = None,
) -> Path:
    """Download ADDRFEAT for each FIPS into ``dest``."""
    dest = Path(dest)
    for fips in fips_list:
        fetch_addrfeat(fips, dest, years=years, force=force, opener=opener)
    return dest
