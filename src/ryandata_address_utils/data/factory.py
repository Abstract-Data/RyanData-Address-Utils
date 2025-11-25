from __future__ import annotations

from typing import Any

from ryandata_address_utils.protocols import DataSourceProtocol


class DataSourceFactory:
    """Factory for creating data source instances.

    Supports registration of custom data source types and creation
    of data sources by type name.

    Example:
        >>> source = DataSourceFactory.create("csv")
        >>> source = DataSourceFactory.create("csv", csv_path="/path/to/data.csv")

        # Register custom source
        >>> DataSourceFactory.register("sqlite", SQLiteDataSource)
        >>> source = DataSourceFactory.create("sqlite", db_path="zips.db")
    """

    _registry: dict[str, type] = {}

    @classmethod
    def _ensure_defaults_registered(cls) -> None:
        """Ensure default data sources are registered."""
        if "csv" not in cls._registry:
            from ryandata_address_utils.data.csv_source import CSVDataSource

            cls._registry["csv"] = CSVDataSource

    @classmethod
    def register(
        cls,
        source_type: str,
        source_class: type[DataSourceProtocol],
    ) -> None:
        """Register a data source type.

        Args:
            source_type: Type name for the data source.
            source_class: Class implementing DataSourceProtocol.
        """
        cls._registry[source_type] = source_class

    @classmethod
    def unregister(cls, source_type: str) -> None:
        """Unregister a data source type.

        Args:
            source_type: Type name to unregister.
        """
        cls._registry.pop(source_type, None)

    @classmethod
    def create(
        cls,
        source_type: str = "csv",
        **kwargs: Any,
    ) -> DataSourceProtocol:
        """Create a data source instance.

        Args:
            source_type: Type of data source to create.
            **kwargs: Arguments to pass to the data source constructor.

        Returns:
            Data source instance.

        Raises:
            ValueError: If the source type is not registered.
        """
        cls._ensure_defaults_registered()

        if source_type not in cls._registry:
            available = ", ".join(sorted(cls._registry.keys()))
            raise ValueError(
                f"Unknown data source type: {source_type}. Available types: {available}"
            )

        source_class = cls._registry[source_type]
        return source_class(**kwargs)  # type: ignore[no-any-return]

    @classmethod
    def available_types(cls) -> list[str]:
        """Get list of available data source types.

        Returns:
            List of registered type names.
        """
        cls._ensure_defaults_registered()
        return sorted(cls._registry.keys())

    @classmethod
    def clear_registry(cls) -> None:
        """Clear the registry (mainly for testing)."""
        cls._registry.clear()
