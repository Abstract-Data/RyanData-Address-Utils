from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence

from ryandata_address_utils.models import Address, ParseResult

logger = logging.getLogger(__name__)


class BaseAddressParser(ABC):
    """Abstract base class for address parsers.

    Provides common error handling, logging, and batch processing logic.
    Subclasses must implement the _parse_impl method.
    """

    def __init__(self) -> None:
        """Initialize the parser."""
        self._parse_count = 0
        self._error_count = 0

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of this parser implementation."""
        ...

    @abstractmethod
    def _parse_impl(self, address_string: str) -> Address:
        """Internal implementation of address parsing.

        Args:
            address_string: Raw address string to parse.

        Returns:
            Parsed Address object.

        Raises:
            Exception: If parsing fails.
        """
        ...

    def parse(self, address_string: str) -> ParseResult:
        """Parse a single address string.

        Args:
            address_string: Raw address string to parse.

        Returns:
            ParseResult containing the parsed address or error information.
        """
        self._parse_count += 1

        try:
            address = self._parse_impl(address_string)
            logger.debug("Successfully parsed address: %s", address_string[:50])
            return ParseResult(
                raw_input=address_string,
                address=address,
            )
        except Exception as e:
            self._error_count += 1
            logger.warning(
                "Failed to parse address: %s - %s",
                address_string[:50],
                str(e),
            )
            return ParseResult(
                raw_input=address_string,
                error=e,
            )

    def parse_batch(self, addresses: Sequence[str]) -> list[ParseResult]:
        """Parse multiple address strings.

        Default implementation processes addresses sequentially.
        Subclasses may override for parallel processing.

        Args:
            addresses: Sequence of raw address strings to parse.

        Returns:
            List of ParseResult objects, one for each input address.
        """
        return [self.parse(addr) for addr in addresses]

    @property
    def stats(self) -> dict[str, int]:
        """Get parsing statistics.

        Returns:
            Dict with parse_count and error_count.
        """
        return {
            "parse_count": self._parse_count,
            "error_count": self._error_count,
        }

    def reset_stats(self) -> None:
        """Reset parsing statistics."""
        self._parse_count = 0
        self._error_count = 0

