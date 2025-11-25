from __future__ import annotations

import usaddress

from ryandata_address_utils.models import Address
from ryandata_address_utils.parsers.base import BaseAddressParser


class USAddressParser(BaseAddressParser):
    """Parser implementation using the usaddress library.

    This parser uses the usaddress library to parse US addresses
    into structured components.
    """

    @property
    def name(self) -> str:
        """Name of this parser implementation."""
        return "usaddress"

    def _parse_impl(self, address_string: str) -> Address:
        """Parse an address using usaddress library.

        Args:
            address_string: Raw address string to parse.

        Returns:
            Parsed Address object.

        Raises:
            ValueError: If parsing fails due to repeated labels or other issues.
        """
        try:
            parsed_address, address_type = usaddress.tag(address_string)
        except usaddress.RepeatedLabelError as e:
            raise ValueError(f"Failed to parse address (repeated label): {e}") from e

        # Convert OrderedDict to regular dict and create Address
        return Address.model_construct(**dict(parsed_address))

