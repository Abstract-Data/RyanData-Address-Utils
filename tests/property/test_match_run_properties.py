"""Properties for uniqueness source-list parsing."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ryandata_address_utils.match.run import parse_sources

SOURCE_SPELLINGS = {
    "txgio": ("txgio", "TXGIO", "TxGiO"),
    "tiger": ("tiger", "TIGER", "Tiger"),
}


@given(
    sources=st.lists(st.sampled_from(["txgio", "tiger"]), min_size=1, max_size=8),
    padding=st.sampled_from(["", " ", "  "]),
    data=st.data(),
)
def test_parse_sources_normalizes_supported_lists(
    sources: list[str], padding: str, data: st.DataObject
) -> None:
    spellings = [data.draw(st.sampled_from(SOURCE_SPELLINGS[source])) for source in sources]
    raw = ",".join(f"{padding}{source}{padding}" for source in spellings)
    assert parse_sources(raw) == tuple(sources)


@given(empty_parts=st.lists(st.sampled_from(["", " ", "\t"]), max_size=8))
def test_parse_sources_empty_lists_use_default(empty_parts: list[str]) -> None:
    assert parse_sources(",".join(empty_parts)) == ("txgio",)


@given(token=st.sampled_from(["census", "addrfeat", "tlc", "unknown"]))
def test_parse_sources_rejects_unsupported_tokens(token: str) -> None:
    with pytest.raises(ValueError, match="unknown --sources"):
        parse_sources(token)
