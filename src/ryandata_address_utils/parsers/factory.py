from __future__ import annotations

from typing import Any, ClassVar

from ryandata_address_utils.core.factory import PluginFactory
from ryandata_address_utils.protocols import AddressParserProtocol


class ParserFactory(PluginFactory[AddressParserProtocol]):
    """Factory for creating address parser instances.

    Supports registration of custom parser types and creation
    of parsers by type name.

    Example:
        >>> parser = ParserFactory.create("usaddress")

        # Register custom parser
        >>> ParserFactory.register("libpostal", LibPostalParser)
        >>> parser = ParserFactory.create("libpostal")
    """

    _registry: ClassVar[dict[str, type[AddressParserProtocol]]] = {}
    _default_type: ClassVar[str] = "usaddress"
    _entity_name: ClassVar[str] = "parser"

    @classmethod
    def _ensure_defaults_registered(cls) -> None:
        """Ensure default parsers are registered."""
        if "usaddress" not in cls._registry:
            from ryandata_address_utils.parsers.usaddress_parser import USAddressParser

            cls._registry["usaddress"] = USAddressParser

    # Backward compatibility: keep the old parameter name in create()
    @classmethod
    def create(  # type: ignore[override]
        cls,
        parser_type: str | None = None,
        **kwargs: Any,
    ) -> AddressParserProtocol:
        """Create a parser instance.

        Args:
            parser_type: Type of parser to create. Defaults to "usaddress".
            **kwargs: Arguments to pass to the parser constructor.

        Returns:
            Parser instance.

        Raises:
            ValueError: If the parser type is not registered.
        """
        return super().create(parser_type, **kwargs)
