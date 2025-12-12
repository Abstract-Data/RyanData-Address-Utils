from __future__ import annotations

from typing import Any, ClassVar

from ryandata_address_utils.core.factory import PluginFactory
from ryandata_address_utils.protocols import DataSourceProtocol


class DataSourceFactory(PluginFactory[DataSourceProtocol]):
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

    _registry: ClassVar[dict[str, type[DataSourceProtocol]]] = {}
    _default_type: ClassVar[str] = "csv"
    _entity_name: ClassVar[str] = "data source"

    @classmethod
    def _ensure_defaults_registered(cls) -> None:
        """Ensure default data sources are registered."""
        if "csv" not in cls._registry:
            from ryandata_address_utils.data.csv_source import CSVDataSource

            cls._registry["csv"] = CSVDataSource

    # Backward compatibility: keep the old parameter name in create()
    @classmethod
    def create(  # type: ignore[override]
        cls,
        source_type: str | None = None,
        **kwargs: Any,
    ) -> DataSourceProtocol:
        """Create a data source instance.

        Args:
            source_type: Type of data source to create. Defaults to "csv".
            **kwargs: Arguments to pass to the data source constructor.

        Returns:
            Data source instance.

        Raises:
            ValueError: If the source type is not registered.
        """
        return super().create(source_type, **kwargs)
