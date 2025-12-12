"""Generic plugin factory base class.

Provides a reusable factory pattern for creating instances from a registry
of registered types. Subclasses specify the protocol type, default type,
and how to register defaults.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Generic, TypeVar

T = TypeVar("T")


class PluginFactory(ABC, Generic[T]):
    """Generic factory for creating plugin instances from a registry.

    Subclasses should define:
        - _registry: Class-level dict mapping type names to implementation classes
        - _default_type: The default type name to use when none specified
        - _entity_name: Human-readable name for error messages (e.g., "parser", "data source")
        - _ensure_defaults_registered(): Method to register default implementations

    Example subclass:
        class ParserFactory(PluginFactory[AddressParserProtocol]):
            _registry: ClassVar[dict[str, type[AddressParserProtocol]]] = {}
            _default_type: ClassVar[str] = "usaddress"
            _entity_name: ClassVar[str] = "parser"

            @classmethod
            def _ensure_defaults_registered(cls) -> None:
                if "usaddress" not in cls._registry:
                    from ... import USAddressParser
                    cls._registry["usaddress"] = USAddressParser
    """

    _registry: ClassVar[dict[str, type[Any]]]
    _default_type: ClassVar[str]
    _entity_name: ClassVar[str]

    @classmethod
    @abstractmethod
    def _ensure_defaults_registered(cls) -> None:
        """Ensure default implementations are registered.

        Subclasses must implement this to lazily register their default
        implementations. This method is called before registry access.
        """
        ...

    @classmethod
    def register(cls, name: str, impl_class: type[T]) -> None:
        """Register an implementation type.

        Args:
            name: Type name for the implementation.
            impl_class: Class implementing the protocol.
        """
        cls._registry[name] = impl_class

    @classmethod
    def unregister(cls, name: str) -> None:
        """Unregister an implementation type.

        Args:
            name: Type name to unregister.
        """
        cls._registry.pop(name, None)

    @classmethod
    def create(cls, name: str | None = None, **kwargs: Any) -> T:
        """Create an instance of the specified type.

        Args:
            name: Type name to create. If None, uses the default type.
            **kwargs: Arguments to pass to the constructor.

        Returns:
            Instance of the requested type.

        Raises:
            ValueError: If the type name is not registered.
        """
        cls._ensure_defaults_registered()

        type_name = name if name is not None else cls._default_type

        if type_name not in cls._registry:
            available = ", ".join(sorted(cls._registry.keys()))
            raise ValueError(
                f"Unknown {cls._entity_name} type: {type_name}. Available types: {available}"
            )

        impl_class = cls._registry[type_name]
        return impl_class(**kwargs)  # type: ignore[no-any-return]

    @classmethod
    def available_types(cls) -> list[str]:
        """Get list of available types.

        Returns:
            List of registered type names.
        """
        cls._ensure_defaults_registered()
        return sorted(cls._registry.keys())

    @classmethod
    def clear_registry(cls) -> None:
        """Clear the registry (mainly for testing)."""
        cls._registry.clear()
