"""Shapefile downloaders for uniqueness (issue #22). Network is mocked."""

from __future__ import annotations

import json
import urllib.error
import zipfile
from pathlib import Path

import pytest

from ryandata_address_utils.match.fetch import http as http_helpers
from ryandata_address_utils.match.fetch.http import USER_AGENT, download_file, http_status
from ryandata_address_utils.match.fetch.precincts import (
    fetch_tx_precincts,
    parse_election_precinct_filename,
    parse_tlc_precinct_resource,
    rank_tlc_precinct_resources,
    staged_precinct_filename,
)
from ryandata_address_utils.match.fetch.tiger import (
    addrfeat_url,
    fetch_addrfeat,
    fetch_tiger_counties,
)
from ryandata_address_utils.match.fetch.txgio import (
    _parse_acquisition_date,
    fetch_txgio_counties,
    list_resources,
    resolve_latest_collection,
)
from ryandata_address_utils.match.texas import county_fips_from_name


class _BytesResponse:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self, n: int = -1) -> bytes:
        if n < 0:
            out, self._data = self._data, b""
            return out
        out, self._data = self._data[:n], self._data[n:]
        return out

    def __enter__(self) -> _BytesResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def _opener(payloads: dict[str, bytes], *, missing: int = 404):
    def opener(req: object, timeout: object = None) -> _BytesResponse:
        url = getattr(req, "full_url", str(req))
        if url not in payloads:
            raise urllib.error.HTTPError(url, missing, "not found", hdrs={}, fp=None)
        return _BytesResponse(payloads[url])

    return opener


class TestUserAgent:
    def test_starts_with_mozilla_and_names_this_package(self) -> None:
        assert USER_AGENT.startswith("Mozilla/5.0")
        assert "ryandata-address-utils" in USER_AGENT
        assert "Chrome" not in USER_AGENT


class TestTexasFips:
    def test_mclennan_is_not_the_arithmetic_rule(self) -> None:
        assert county_fips_from_name("MCLENNAN") == "48309"
        assert county_fips_from_name("MADISON") == "48313"

    def test_de_witt_alias(self) -> None:
        assert county_fips_from_name("DE WITT") == county_fips_from_name("DEWITT")
        assert county_fips_from_name("DE-WITT") == county_fips_from_name("DEWITT")

    def test_blank_is_none_and_spaced_mc_collapses(self) -> None:
        assert county_fips_from_name(None) is None
        assert county_fips_from_name("") is None
        assert county_fips_from_name("MC CULLOCH") == "48307"


class TestTxgioCatalog:
    def test_newest_vintage_wins(self) -> None:
        payload = {
            "results": [
                {
                    "collection_id": "old",
                    "name": "Address Points",
                    "acquisition_date": "2024-02-01",
                },
                {
                    "collection_id": "new",
                    "name": "Address Points",
                    "acquisition_date": "2026-03-18",
                },
                {
                    "collection_id": "lidar",
                    "name": "Lidar",
                    "acquisition_date": "2027-01-01",
                },
            ]
        }
        catalog = "https://api.tnris.org/api/v1/collections_catalog?limit=3000&offset=0"
        opener = _opener({catalog: json.dumps(payload).encode()})
        latest = resolve_latest_collection(opener=opener)
        assert latest.collection_id == "new"
        assert latest.vintage == "2026"

    def test_statewide_rollup_is_excluded(self) -> None:
        payload = {
            "results": [
                {
                    "resource_id": "c",
                    "resource": "https://cdn.example/stratmap-2026-address-points_48001_ap.zip",
                    "filesize": 10,
                    "area_type_name": "Anderson",
                    "area_type": "county",
                },
                {
                    "resource_id": "s",
                    "resource": "https://cdn.example/stratmap-2026-address-points_48_ap.zip",
                    "filesize": 99,
                    "area_type_name": "Texas",
                    "area_type": "state",
                },
            ]
        }
        opener = _opener(
            {
                "https://api.tnris.org/api/v1/resources?collection_id=new": (
                    json.dumps(payload).encode()
                ),
            }
        )
        resources = list_resources("new", opener=opener)
        assert len(resources) == 1
        assert resources[0].fips == "48001"


class TestDownloadSkip:
    def test_matching_size_is_not_redownloaded(self, tmp_path: Path) -> None:
        dest = tmp_path / "file.zip"
        dest.write_bytes(b"abc")
        calls: list[str] = []

        def opener(req: object, timeout: object = None) -> _BytesResponse:
            calls.append("hit")
            return _BytesResponse(b"zzzz")

        out = download_file("https://example/file.zip", dest, expected_size=3, opener=opener)
        assert out.read_bytes() == b"abc"
        assert calls == []

    def test_unknown_size_is_redownloaded(self, tmp_path: Path) -> None:
        dest = tmp_path / "file.zip"
        dest.write_bytes(b"stale")

        out = download_file(
            "https://example/file.zip", dest, opener=_opener({"https://example/file.zip": b"new"})
        )

        assert out.read_bytes() == b"new"


class TestOpen:
    def test_stdlib_urlopen_receives_finite_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        seen: dict[str, object] = {}

        def urlopen(request: object, *, timeout: float) -> _BytesResponse:
            seen["request"] = request
            seen["timeout"] = timeout
            return _BytesResponse(b"")

        monkeypatch.setattr(http_helpers.urllib.request, "urlopen", urlopen)
        http_helpers._open("https://example/file", opener=None)

        assert seen["timeout"] == http_helpers.HTTP_TIMEOUT_SECONDS
        assert float(seen["timeout"]) > 0

    def test_injected_opener_still_receives_only_request(self) -> None:
        calls: list[object] = []

        def opener(request: object) -> _BytesResponse:
            calls.append(request)
            return _BytesResponse(b"")

        http_helpers._open("https://example/file", opener=opener)
        assert len(calls) == 1


class TestTigerAddrfeat:
    def test_url_uses_five_digit_fips(self) -> None:
        assert addrfeat_url("48201", 2025) == (
            "https://www2.census.gov/geo/tiger/TIGER2025/ADDRFEAT/tl_2025_48201_addrfeat.zip"
        )

    def test_falls_back_to_2024_on_404(self, tmp_path: Path) -> None:
        zip_bytes = _tiny_shp_zip("tl_2024_48001_addrfeat")
        payloads = {
            (
                "https://www2.census.gov/geo/tiger/TIGER2025/ADDRFEAT/tl_2025_48001_addrfeat.zip"
            ): None,
            (
                "https://www2.census.gov/geo/tiger/TIGER2024/ADDRFEAT/tl_2024_48001_addrfeat.zip"
            ): zip_bytes,
        }

        def opener(req: object, timeout: object = None) -> _BytesResponse:
            url = getattr(req, "full_url", str(req))
            body = payloads.get(url)
            if body is None:
                raise urllib.error.HTTPError(url, 404, "not found", hdrs={}, fp=None)
            return _BytesResponse(body)

        shp = fetch_addrfeat("48001", tmp_path, years=(2025, 2024), opener=opener)
        assert shp.name == "tl_2024_48001_addrfeat.shp"
        assert shp.exists()

    def test_existing_unique_shapefile_is_reused(self, tmp_path: Path) -> None:
        shp = tmp_path / "tl_2025_48001_addrfeat.shp"
        shp.write_text("cached", encoding="utf-8")
        out = fetch_addrfeat("48001", tmp_path, opener=_opener({}))
        assert out == shp

    def test_duplicate_shapefiles_fail(self, tmp_path: Path) -> None:
        (tmp_path / "tl_2024_48001_addrfeat.shp").write_text("a", encoding="utf-8")
        (tmp_path / "tl_2025_48001_addrfeat.shp").write_text("b", encoding="utf-8")
        with pytest.raises(ValueError, match="unique"):
            fetch_addrfeat("48001", tmp_path)

    def test_non_404_is_not_swallowed(self, tmp_path: Path) -> None:
        def opener(req: object, timeout: object = None) -> _BytesResponse:
            url = getattr(req, "full_url", str(req))
            raise urllib.error.HTTPError(url, 500, "boom", hdrs={}, fp=None)

        with pytest.raises(urllib.error.HTTPError):
            fetch_addrfeat("48001", tmp_path, years=(2025,), opener=opener)

    def test_zip_without_shapefile_fails(self, tmp_path: Path) -> None:
        from io import BytesIO

        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("readme.txt", "no shp")
        opener = _opener(
            {
                (
                    "https://www2.census.gov/geo/tiger/TIGER2025/ADDRFEAT/"
                    "tl_2025_48001_addrfeat.zip"
                ): buf.getvalue(),
            }
        )
        with pytest.raises(FileNotFoundError, match="contained no ADDRFEAT"):
            fetch_addrfeat("48001", tmp_path, years=(2025,), opener=opener)

    def test_empty_year_list_fails_without_http(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="No ADDRFEAT"):
            fetch_addrfeat("48001", tmp_path, years=(), opener=_opener({}))

    def test_force_replaces_prior_vintage_sidecars(self, tmp_path: Path) -> None:
        old_stem = "tl_2024_48001_addrfeat"
        (tmp_path / f"{old_stem}.shp").write_bytes(b"old shp")
        (tmp_path / f"{old_stem}.dbf").write_bytes(b"old dbf")
        url = "https://www2.census.gov/geo/tiger/TIGER2025/ADDRFEAT/tl_2025_48001_addrfeat.zip"

        shp = fetch_addrfeat(
            "48001",
            tmp_path,
            years=(2025,),
            force=True,
            opener=_opener({url: _tiny_shp_zip("tl_2025_48001_addrfeat")}),
        )

        assert shp.name == "tl_2025_48001_addrfeat.shp"
        assert not (tmp_path / f"{old_stem}.shp").exists()
        assert not (tmp_path / f"{old_stem}.dbf").exists()


class TestHttpStatus:
    def test_http_error_code(self) -> None:
        err = urllib.error.HTTPError("http://x", 404, "no", hdrs={}, fp=None)
        assert http_status(err) == 404
        assert http_status(ValueError("nope")) is None


class TestParseAcquisitionDate:
    def test_blank_and_malformed_sort_as_oldest(self) -> None:
        from datetime import date

        assert _parse_acquisition_date(None) == date.min
        assert _parse_acquisition_date("") == date.min
        assert _parse_acquisition_date("not-a-date") == date.min


class TestTlcRank:
    def test_26p_beats_24g(self) -> None:
        pick = rank_tlc_precinct_resources(
            [
                {"name": "Precincts24G.zip", "format": "ZIP", "url": "http://old"},
                {"name": "Precincts26P.zip", "format": "SHP", "url": "http://new"},
            ]
        )
        assert pick is not None
        assert pick["shp"]["year"] == 2026
        assert pick["shp"]["kind"] == "P"

    def test_filename_helpers(self) -> None:
        assert parse_election_precinct_filename("Precincts26P.shp") == (2026, "P")
        assert staged_precinct_filename(2026, "P") == "Precincts26P.shp"
        assert parse_election_precinct_filename("notes.txt") is None

    def test_resource_roles_and_skips(self) -> None:
        assert parse_tlc_precinct_resource("notes.txt", "ZIP") is None
        assert parse_tlc_precinct_resource("Precincts26P districts.xlsx", "XLSX") == (
            2026,
            "P",
            "districts",
        )
        assert parse_tlc_precinct_resource("Precincts26P.dbf", "DBF") is None
        assert parse_tlc_precinct_resource("Precincts26P.zip", "") == (2026, "P", "shp")

    def test_unparseable_and_districts_only_yield_none(self) -> None:
        assert rank_tlc_precinct_resources([{"name": "readme.txt", "format": "TXT"}]) is None
        pick = rank_tlc_precinct_resources(
            [
                {"name": "Precincts26P.zip", "format": "ZIP", "url": "http://shp"},
                {
                    "name": "Precincts26P districts.xlsx",
                    "format": "XLSX",
                    "url": "http://xls",
                },
            ]
        )
        assert pick is not None
        assert pick["districts"]["url"] == "http://xls"


class TestTxgioEmptyCatalog:
    def test_no_address_points_collection_fails(self) -> None:
        catalog = "https://api.tnris.org/api/v1/collections_catalog?limit=3000&offset=0"
        opener = _opener({catalog: json.dumps({"results": []}).encode()})
        with pytest.raises(RuntimeError, match="Address Points"):
            resolve_latest_collection(opener=opener)

    def test_blank_acquisition_date_is_oldest(self) -> None:
        payload = {
            "results": [
                {
                    "collection_id": "dated",
                    "name": "Address Points",
                    "acquisition_date": "2026-01-01",
                },
                {"collection_id": "blank", "name": "Address Points", "acquisition_date": ""},
            ]
        }
        catalog = "https://api.tnris.org/api/v1/collections_catalog?limit=3000&offset=0"
        latest = resolve_latest_collection(opener=_opener({catalog: json.dumps(payload).encode()}))
        assert latest.collection_id == "dated"


class TestFetchPrecincts:
    def test_stages_ranked_zip(self, tmp_path: Path) -> None:
        payload = {
            "success": True,
            "result": {
                "resources": [
                    {
                        "name": "Precincts26P.zip",
                        "format": "ZIP",
                        "url": "https://example/Precincts26P.zip",
                    }
                ]
            },
        }
        zip_bytes = _tiny_shp_zip("Precincts26P")
        opener = _opener(
            {
                "https://data.capitol.texas.gov/api/3/action/package_show?id=precincts": (
                    json.dumps(payload).encode()
                ),
                "https://example/Precincts26P.zip": zip_bytes,
            }
        )
        shp = fetch_tx_precincts(tmp_path, opener=opener)
        assert shp.name == "Precincts26P.shp"
        assert shp.exists()

    def _ckan(
        self,
        resources: list[dict[str, object]],
        zip_url: str | None = None,
        zip_bytes: bytes | None = None,
    ):
        payload = {"success": True, "result": {"resources": resources}}
        mapping: dict[str, bytes] = {
            "https://data.capitol.texas.gov/api/3/action/package_show?id=precincts": (
                json.dumps(payload).encode()
            ),
        }
        if zip_url is not None and zip_bytes is not None:
            mapping[zip_url] = zip_bytes
        return _opener(mapping)

    def test_ckan_failure_and_no_shapefile(self, tmp_path: Path) -> None:
        opener = _opener(
            {
                "https://data.capitol.texas.gov/api/3/action/package_show?id=precincts": (
                    json.dumps({"success": False}).encode()
                ),
            }
        )
        with pytest.raises(RuntimeError, match="CKAN"):
            fetch_tx_precincts(tmp_path, opener=opener)
        empty = self._ckan([])
        with pytest.raises(FileNotFoundError, match="No Precincts"):
            fetch_tx_precincts(tmp_path, opener=empty)

    def test_cached_shapefile_is_not_redownloaded(self, tmp_path: Path) -> None:
        cached = tmp_path / "Precincts26P.shp"
        cached.write_text("cached", encoding="utf-8")
        opener = self._ckan(
            [
                {
                    "name": "Precincts26P.zip",
                    "format": "ZIP",
                    "url": "https://example/Precincts26P.zip",
                }
            ]
        )
        shp = fetch_tx_precincts(tmp_path, opener=opener)
        assert shp.read_text(encoding="utf-8") == "cached"

    def test_missing_url_and_zip_without_shp(self, tmp_path: Path) -> None:
        no_url = self._ckan([{"name": "Precincts26P.zip", "format": "ZIP", "url": ""}])
        with pytest.raises(FileNotFoundError, match="no URL"):
            fetch_tx_precincts(tmp_path, opener=no_url)
        from io import BytesIO

        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("readme.txt", "no shp")
        opener = self._ckan(
            [
                {
                    "name": "Precincts26P.zip",
                    "format": "ZIP",
                    "url": "https://example/Precincts26P.zip",
                }
            ],
            zip_url="https://example/Precincts26P.zip",
            zip_bytes=buf.getvalue(),
        )
        with pytest.raises(FileNotFoundError, match="contained no .shp"):
            fetch_tx_precincts(tmp_path, opener=opener)

    def test_stage_failure_if_copy_is_skipped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        opener = self._ckan(
            [
                {
                    "name": "Precincts26P.zip",
                    "format": "ZIP",
                    "url": "https://example/Precincts26P.zip",
                }
            ],
            zip_url="https://example/Precincts26P.zip",
            zip_bytes=_tiny_shp_zip("Precincts26P"),
        )
        monkeypatch.setattr(
            "ryandata_address_utils.match.fetch.precincts.shutil.copy2",
            lambda *a, **k: None,
        )
        with pytest.raises(FileNotFoundError, match="Failed to stage"):
            fetch_tx_precincts(tmp_path, opener=opener)

    def test_zip_with_only_unrelated_shapefile_fails(self, tmp_path: Path) -> None:
        url = "https://example/Precincts26P.zip"
        opener = self._ckan(
            [{"name": "Precincts26P.zip", "format": "ZIP", "url": url}],
            zip_url=url,
            zip_bytes=_tiny_shp_zip("Precincts24G"),
        )

        with pytest.raises(FileNotFoundError, match="contained no Precincts26P.shp"):
            fetch_tx_precincts(tmp_path, opener=opener)


class TestFetchTxgioCounties:
    def test_downloads_matching_fips(self, tmp_path: Path) -> None:
        catalog = {
            "results": [
                {
                    "collection_id": "new",
                    "name": "Address Points",
                    "acquisition_date": "2026-03-18",
                }
            ]
        }
        resources = {
            "results": [
                {
                    "resource_id": "c",
                    "resource": "https://cdn.example/stratmap-2026-address-points_48001_ap.zip",
                    "filesize": 4,
                    "area_type_name": "Anderson",
                    "area_type": "county",
                }
            ]
        }
        opener = _opener(
            {
                "https://api.tnris.org/api/v1/collections_catalog?limit=3000&offset=0": (
                    json.dumps(catalog).encode()
                ),
                "https://api.tnris.org/api/v1/resources?collection_id=new": (
                    json.dumps(resources).encode()
                ),
                "https://cdn.example/stratmap-2026-address-points_48001_ap.zip": b"abcd",
            }
        )
        dest = fetch_txgio_counties(("48001",), tmp_path, opener=opener)
        zips = list(dest.glob("*_48001_ap.zip"))
        assert zips and zips[0].read_bytes() == b"abcd"

    def test_missing_fips_fails_loud(self, tmp_path: Path) -> None:
        catalog = {
            "results": [
                {
                    "collection_id": "new",
                    "name": "Address Points",
                    "acquisition_date": "2026-03-18",
                }
            ]
        }
        resources = {"results": []}
        opener = _opener(
            {
                "https://api.tnris.org/api/v1/collections_catalog?limit=3000&offset=0": (
                    json.dumps(catalog).encode()
                ),
                "https://api.tnris.org/api/v1/resources?collection_id=new": (
                    json.dumps(resources).encode()
                ),
            }
        )
        with pytest.raises(FileNotFoundError, match="48001"):
            fetch_txgio_counties(("48001",), tmp_path, opener=opener)


class TestFetchTigerCounties:
    def test_writes_shapefile(self, tmp_path: Path) -> None:
        zip_bytes = _tiny_shp_zip("tl_2025_48001_addrfeat")
        opener = _opener(
            {
                (
                    "https://www2.census.gov/geo/tiger/TIGER2025/ADDRFEAT/"
                    "tl_2025_48001_addrfeat.zip"
                ): zip_bytes,
            }
        )
        dest = fetch_tiger_counties(("48001",), tmp_path, years=(2025,), opener=opener)
        assert (dest / "tl_2025_48001_addrfeat.shp").exists()


def _tiny_shp_zip(stem: str) -> bytes:
    from io import BytesIO

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(f"{stem}.shp", b"shp")
        zf.writestr(f"{stem}.shx", b"shx")
        zf.writestr(f"{stem}.dbf", b"dbf")
        zf.writestr(f"{stem}.prj", b"prj")
    return buf.getvalue()
