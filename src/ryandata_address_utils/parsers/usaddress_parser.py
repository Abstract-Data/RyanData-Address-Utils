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

    def _merge_consecutive_labels(self, tokens: list[tuple[str, str]]) -> dict[str, str | None]:
        """Merge consecutive tokens with the same label.

        Args:
            tokens: List of (value, label) tuples from usaddress.parse().

        Returns:
            Dictionary mapping labels to merged string values.
        """
        if not tokens:
            return {}

        result: dict[str, str | None] = {}
        current_label: str | None = None
        current_values: list[str] = []

        for value, label in tokens:
            if label == current_label:
                current_values.append(value)
            else:
                if current_label is not None:
                    merged_value = " ".join(current_values).rstrip(",")
                    result[current_label] = merged_value
                current_label = label
                current_values = [value]

        # Don't forget the last group
        if current_label is not None:
            merged_value = " ".join(current_values).rstrip(",")
            result[current_label] = merged_value

        return result

    def _parse_impl(self, address_string: str) -> Address:
        """Parse an address using usaddress library.

        Args:
            address_string: Raw address string to parse.

        Returns:
            Parsed Address object.

        Raises:
            ValueError: If parsing fails due to other issues.
        """
        try:
            parsed_tokens = usaddress.parse(address_string)
        except Exception as e:
            raise ValueError(f"Failed to parse address: {e}") from e

        # Merge consecutive tokens with the same label
        parsed_address = self._merge_consecutive_labels(parsed_tokens)

        # Add the raw input string to the parsed address
        parsed_address["RawInput"] = address_string

        # Create Address from merged dictionary using model_validate to trigger validators
        return Address.model_validate(parsed_address)
