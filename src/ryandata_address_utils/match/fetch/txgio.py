"""TxGIO StratMap Address Points downloader.

Catalog: https://api.tnris.org — newest ``Address Points`` vintage, not a pinned UUID.
The download CDN 403s User-Agents that do not start with ``Mozilla/5.0``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

from ryandata_address_utils.match.fetch.http import Opener, download_file, json_get

COLLECTIONS_CATALOG_URL = "https://api.tnris.org/api/v1/collections_catalog"
RESOURCES_URL = "https://api.tnris.org/api/v1/resources"
COLLECTION_NAME = "Address Points"
_FIPS_IN_FILENAME = re.compile(r"_(\d{2,5})_ap\.zip$", re.IGNORECASE)


@dataclass(frozen=True)
class AddressPointCollection:
    collection_id: str
    name: str
    acquisition_date: date

    @property
    def vintage(self) -> str:
        """Acquisition year as a four-digit string."""
        return str(self.acquisition_date.year)


@dataclass(frozen=True)
class AddressPointResource:
    resource_id: str
    url: str
    filesize: int
    area_name: str
    area_type: str
    collection_id: str

    @property
    def fips(self) -> str:
        """County FIPS parsed from the Address Points ZIP filename."""
        match = _FIPS_IN_FILENAME.search(self.url)
        return match.group(1) if match else ""

    @property
    def filename(self) -> str:
        """Last path segment of the download URL."""
        return self.url.rsplit("/", 1)[-1]


def _parse_acquisition_date(raw: str | None) -> date:
    """Parse ``YYYY-MM-DD``; missing or malformed dates sort as oldest."""
    if not raw:
        return date.min
    try:
        return datetime.strptime(raw[:10], "%Y-%m-%d").replace(tzinfo=UTC).date()
    except ValueError:
        return date.min


def list_collections(*, opener: Opener | None = None) -> list[AddressPointCollection]:
    """Address Points collections, newest acquisition date first."""
    payload = json_get(COLLECTIONS_CATALOG_URL, params={"limit": 3000, "offset": 0}, opener=opener)
    collections: list[AddressPointCollection] = []
    for record in payload.get("results", []):
        if (record.get("name") or "").strip().lower() != COLLECTION_NAME.lower():
            continue
        collections.append(
            AddressPointCollection(
                collection_id=str(record["collection_id"]),
                name=str(record["name"]),
                acquisition_date=_parse_acquisition_date(record.get("acquisition_date")),
            )
        )
    collections.sort(key=lambda c: c.acquisition_date, reverse=True)
    return collections


def resolve_latest_collection(*, opener: Opener | None = None) -> AddressPointCollection:
    """Newest Address Points vintage in the TNRIS catalog."""
    collections = list_collections(opener=opener)
    if not collections:
        raise RuntimeError(f"No '{COLLECTION_NAME}' collection at {COLLECTIONS_CATALOG_URL}")
    return collections[0]


def list_resources(
    collection_id: str,
    *,
    include_statewide: bool = False,
    opener: Opener | None = None,
) -> list[AddressPointResource]:
    """County Address Points ZIPs for one collection. Statewide ZIP is skipped."""
    payload = json_get(RESOURCES_URL, params={"collection_id": collection_id}, opener=opener)
    resources: list[AddressPointResource] = []
    for record in payload.get("results", []):
        area_type = record.get("area_type") or ""
        if area_type != "county" and not include_statewide:
            continue
        resources.append(
            AddressPointResource(
                resource_id=str(record["resource_id"]),
                url=str(record["resource"]),
                filesize=int(record.get("filesize") or 0),
                area_name=str(record.get("area_type_name") or ""),
                area_type=str(area_type),
                collection_id=collection_id,
            )
        )
    resources.sort(key=lambda r: (r.area_type != "county", r.area_name))
    return resources


def fetch_txgio_counties(
    fips_list: tuple[str, ...],
    dest: Path,
    *,
    force: bool = False,
    opener: Opener | None = None,
) -> Path:
    """Download county Address Points ZIPs for ``fips_list`` into ``dest``."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    wanted = {str(f) for f in fips_list}
    collection = resolve_latest_collection(opener=opener)
    resources = list_resources(collection.collection_id, opener=opener)
    matched = [r for r in resources if r.fips in wanted]
    missing = wanted - {r.fips for r in matched}
    if missing:
        raise FileNotFoundError(f"TxGIO has no Address Points ZIP for FIPS {sorted(missing)}")
    for resource in matched:
        download_file(
            resource.url,
            dest / resource.filename,
            expected_size=resource.filesize,
            force=force,
            opener=opener,
        )
    return dest
