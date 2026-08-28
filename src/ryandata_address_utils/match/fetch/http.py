"""Stdlib HTTP helpers. User-Agent must start with Mozilla/5.0 for the TxGIO CDN."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

USER_AGENT = (
    "Mozilla/5.0 (compatible; ryandata-address-utils/0.8; "
    "+https://github.com/Abstract-Data/RyanData-Address-Utils)"
)

Opener = Callable[..., Any]


def make_request(url: str) -> urllib.request.Request:
    """GET request with the CDN-safe User-Agent."""
    return urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="GET")


def _open(url: str, *, opener: Opener | None) -> Any:
    open_fn = opener or urllib.request.urlopen
    return open_fn(make_request(url))


def json_get(
    url: str,
    *,
    params: dict[str, str | int] | None = None,
    opener: Opener | None = None,
) -> Any:
    """GET JSON. ``params`` are encoded onto the query string."""
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    with _open(url, opener=opener) as resp:
        return json.loads(resp.read().decode("utf-8"))


def download_file(
    url: str,
    dest: Path,
    *,
    expected_size: int = 0,
    force: bool = False,
    opener: Opener | None = None,
) -> Path:
    """Stream ``url`` to ``dest``. Skip when size already matches ``expected_size``."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not force and (not expected_size or dest.stat().st_size == expected_size):
        return dest
    part = dest.with_suffix(dest.suffix + ".part")
    try:
        with _open(url, opener=opener) as resp, part.open("wb") as handle:
            while True:
                chunk = resp.read(262144)
                if not chunk:
                    break
                handle.write(chunk)
    except Exception:
        part.unlink(missing_ok=True)
        raise
    part.replace(dest)
    return dest


def http_status(exc: BaseException) -> int | None:
    """HTTP status from ``urllib.error.HTTPError``, else None."""
    if isinstance(exc, urllib.error.HTTPError):
        return int(exc.code)
    return None
