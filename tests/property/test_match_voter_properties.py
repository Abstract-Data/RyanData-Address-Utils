"""Properties for voter parsing and normalization."""

from __future__ import annotations

import re
import string

import pytest
from hypothesis import given
from hypothesis import strategies as st

pd = pytest.importorskip("pandas")

from ryandata_address_utils.match.voters import (  # noqa: E402
    canonicalize_voters,
    component_street_key,
    street_key_series,
)

KEY_TEXT = st.text(
    alphabet=string.ascii_letters + string.digits + string.punctuation + " ", max_size=40
)


def _normalized_key(*parts: str) -> str:
    cleaned = [
        re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", part.upper())).strip() for part in parts
    ]
    return " ".join(part for part in cleaned if part)


@given(name=KEY_TEXT, street_type=KEY_TEXT)
def test_component_and_series_street_keys_share_normalization(name: str, street_type: str) -> None:
    expected = _normalized_key(name, street_type)
    assert component_street_key(name, street_type) == expected
    assert street_key_series(pd.Series([name]), pd.Series([street_type])).iloc[0] == expected


@given(
    precinct=st.integers(min_value=0, max_value=999_999),
    zero_padding=st.integers(min_value=0, max_value=6),
    prefix=st.sampled_from(["", "PCT ", "PREC ", "PRECINCT ", "VP "]),
)
def test_canonicalize_voters_normalizes_precinct_notation(
    precinct: int, zero_padding: int, prefix: str
) -> None:
    raw_precinct = prefix + str(precinct).zfill(zero_padding)
    raw = pd.DataFrame(
        {
            "COUNTY": ["DE-WITT"],
            "PCT": [raw_precinct],
            "RHNUM": ["1"],
            "RSTNAME": ["Main"],
            "RSTTYPE": ["St."],
        }
    )

    out = canonicalize_voters(raw)

    assert out["county"].tolist() == ["48123"]
    assert out["pct"].tolist() == [str(precinct)]
    assert out["street_key_nodir"].tolist() == ["MAIN ST"]
