from __future__ import annotations

from typing import Any

from ryandata_address_utils.protocols import AddressParserProtocol


class ParserFactory:
    """Factory for creating address parser instances.

    Supports registration of custom parser types and creation
    of parsers by type name.

    Example:
        >>> parser = ParserFactory.create("usaddress")

        # Register custom parser
        >>> ParserFactory.register("libpostal", LibPostalParser)
        >>> parser = ParserFactory.create("libpostal")
    """

    _registry: dict[str, type] = {}

    @classmethod
    def _ensure_defaults_registered(cls) -> None:
        """Ensure default parsers are registered."""
        if "usaddress" not in cls._registry:
            from ryandata_address_utils.parsers.usaddress_parser import USAddressParser

            cls._registry["usaddress"] = USAddressParser

    @classmethod
    def register(
        cls,
        parser_type: str,
        parser_class: type[AddressParserProtocol],
    ) -> None:
        """Register a parser type.

        Args:
            parser_type: Type name for the parser.
            parser_class: Class implementing AddressParserProtocol.
        """
        cls._registry[parser_type] = parser_class

    @classmethod
    def unregister(cls, parser_type: str) -> None:
        """Unregister a parser type.

        Args:
            parser_type: Type name to unregister.
        """
        cls._registry.pop(parser_type, None)

    @classmethod
    def create(
        cls,
        parser_type: str = "usaddress",
        **kwargs: Any,
    ) -> AddressParserProtocol:
        """Create a parser instance.

        Args:
            parser_type: Type of parser to create.
            **kwargs: Arguments to pass to the parser constructor.

        Returns:
            Parser instance.

        Raises:
            ValueError: If the parser type is not registered.
        """
        cls._ensure_defaults_registered()

        if parser_type not in cls._registry:
            available = ", ".join(sorted(cls._registry.keys()))
            raise ValueError(f"Unknown parser type: {parser_type}. Available types: {available}")

        parser_class = cls._registry[parser_type]
        return parser_class(**kwargs)  # type: ignore[no-any-return]

    @classmethod
    def available_types(cls) -> list[str]:
        """Get list of available parser types.

        Returns:
            List of registered type names.
        """
        cls._ensure_defaults_registered()
        return sorted(cls._registry.keys())

    @classmethod
    def clear_registry(cls) -> None:
        """Clear the registry (mainly for testing)."""
        cls._registry.clear()
