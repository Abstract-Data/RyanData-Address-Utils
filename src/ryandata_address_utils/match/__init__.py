"""Drop-direction uniqueness and TIGER ADDRFEAT range matching.

Callers may supply ``pct`` on each row, or run ``uniqueness --voterfile`` which
fetches TLC precincts and the selected address sources (TxGIO by default). Pass
``--sources txgio,tiger`` to fetch both TxGIO and TIGER ADDRFEAT. Precincts are
attached via PIP.

DataFrame helpers require the ``[pandas]`` extra::

    from ryandata_address_utils.match import (
        MATCH,
        EXCLUDED_PROBLEM,
        UNMATCHED,
        classify_problem_keys,
        match_drop_direction,
        match_addrfeat_ranges,
        house_in_addrfeat_range,
        addrfeat_range_field_names,
        canon_dir,
        normalize_precinct_code,
    )
"""

from __future__ import annotations

from ryandata_address_utils.match.keys import (
    DIRECTIONALS,
    canon_dir,
    dir_pair_canon,
    drop_direction_key,
    fullname_dir_and_nodir_key,
    house_int,
    normalize_precinct_code,
)
from ryandata_address_utils.match.ranges import (
    addrfeat_range_field_names,
    house_in_addrfeat_range,
    match_addrfeat_ranges,
)
from ryandata_address_utils.match.uniqueness import (
    EXCLUDED_PROBLEM,
    MATCH,
    UNMATCHED,
    classify_problem_keys,
    cross_precinct_twin_counts,
    match_drop_direction,
    problem_pattern_counts,
    uniqueness_at_geography,
)

__all__ = [
    "DIRECTIONALS",
    "EXCLUDED_PROBLEM",
    "MATCH",
    "UNMATCHED",
    "addrfeat_range_field_names",
    "canon_dir",
    "classify_problem_keys",
    "cross_precinct_twin_counts",
    "dir_pair_canon",
    "drop_direction_key",
    "fullname_dir_and_nodir_key",
    "house_in_addrfeat_range",
    "house_int",
    "match_addrfeat_ranges",
    "match_drop_direction",
    "normalize_precinct_code",
    "problem_pattern_counts",
    "uniqueness_at_geography",
]
