"""Reference shapefile downloaders (TxGIO, TIGER ADDRFEAT, TLC precincts)."""

from __future__ import annotations

from ryandata_address_utils.match.fetch.http import USER_AGENT, download_file, json_get
from ryandata_address_utils.match.fetch.precincts import (
    fetch_tx_precincts,
    rank_tlc_precinct_resources,
)
from ryandata_address_utils.match.fetch.tiger import addrfeat_url, fetch_addrfeat
from ryandata_address_utils.match.fetch.txgio import (
    fetch_txgio_counties,
    list_resources,
    resolve_latest_collection,
)

__all__ = [
    "USER_AGENT",
    "addrfeat_url",
    "download_file",
    "fetch_addrfeat",
    "fetch_tx_precincts",
    "fetch_txgio_counties",
    "json_get",
    "list_resources",
    "rank_tlc_precinct_resources",
    "resolve_latest_collection",
]
