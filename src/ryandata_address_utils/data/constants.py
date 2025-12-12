"""Centralized constants for US state and territory data.

This module provides the single source of truth for state name mappings,
abbreviations, and territory codes used throughout the package.
"""

from __future__ import annotations

# State name to abbreviation mapping (lowercase name -> abbreviation)
# Includes all 50 US states plus District of Columbia
STATE_NAME_TO_ABBREV: dict[str, str] = {
    "alabama": "AL",
    "alaska": "AK",
    "arizona": "AZ",
    "arkansas": "AR",
    "california": "CA",
    "colorado": "CO",
    "connecticut": "CT",
    "delaware": "DE",
    "florida": "FL",
    "georgia": "GA",
    "hawaii": "HI",
    "idaho": "ID",
    "illinois": "IL",
    "indiana": "IN",
    "iowa": "IA",
    "kansas": "KS",
    "kentucky": "KY",
    "louisiana": "LA",
    "maine": "ME",
    "maryland": "MD",
    "massachusetts": "MA",
    "michigan": "MI",
    "minnesota": "MN",
    "mississippi": "MS",
    "missouri": "MO",
    "montana": "MT",
    "nebraska": "NE",
    "nevada": "NV",
    "new hampshire": "NH",
    "new jersey": "NJ",
    "new mexico": "NM",
    "new york": "NY",
    "north carolina": "NC",
    "north dakota": "ND",
    "ohio": "OH",
    "oklahoma": "OK",
    "oregon": "OR",
    "pennsylvania": "PA",
    "rhode island": "RI",
    "south carolina": "SC",
    "south dakota": "SD",
    "tennessee": "TN",
    "texas": "TX",
    "utah": "UT",
    "vermont": "VT",
    "virginia": "VA",
    "washington": "WA",
    "west virginia": "WV",
    "wisconsin": "WI",
    "wyoming": "WY",
    "district of columbia": "DC",
}

# US Territory abbreviations (not included in STATE_NAME_TO_ABBREV)
TERRITORY_ABBREVS: set[str] = {
    "PR",  # Puerto Rico
    "VI",  # US Virgin Islands
    "GU",  # Guam
    "AS",  # American Samoa
    "MP",  # Northern Mariana Islands
}

# Territory name to abbreviation mapping
TERRITORY_NAME_TO_ABBREV: dict[str, str] = {
    "puerto rico": "PR",
    "virgin islands": "VI",
    "us virgin islands": "VI",
    "guam": "GU",
    "american samoa": "AS",
    "northern mariana islands": "MP",
}

# All valid state abbreviations (50 states + DC)
STATE_ABBREVS: set[str] = set(STATE_NAME_TO_ABBREV.values())

# All valid US postal codes (states + DC + territories)
ALL_US_ABBREVS: set[str] = STATE_ABBREVS | TERRITORY_ABBREVS

# Combined name to abbreviation mapping (states + territories)
ALL_NAME_TO_ABBREV: dict[str, str] = {**STATE_NAME_TO_ABBREV, **TERRITORY_NAME_TO_ABBREV}
