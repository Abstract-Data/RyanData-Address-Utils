from __future__ import annotations

from typing import TYPE_CHECKING

from ryandata_address_utils.models import ADDRESS_FIELDS

if TYPE_CHECKING:
    import pandas as pd

    from ryandata_address_utils.service import AddressService


class AddressParserAccessor:
    """Pandas accessor for address parsing.

    Provides convenient methods for parsing addresses directly
    on pandas Series objects.

    Usage:
        >>> from ryandata_address_utils.pandas_ext import register_accessor
        >>> register_accessor()
        >>> df = pd.DataFrame({"address": ["123 Main St, Austin TX 78749"]})
        >>> df["address"].addr.parse()
    """

    def __init__(self, pandas_obj: pd.Series) -> None:
        """Initialize the accessor.

        Args:
            pandas_obj: The pandas Series this accessor is attached to.
        """
        self._obj = pandas_obj
        self._service: AddressService | None = None

    def _get_service(self) -> AddressService:
        """Get or create the AddressService instance."""
        if self._service is None:
            from ryandata_address_utils.service import AddressService

            self._service = AddressService()
        return self._service

    def parse(
        self,
        *,
        validate: bool = True,
        errors: str = "coerce",
        service: AddressService | None = None,
    ) -> pd.DataFrame:
        """Parse addresses in the Series.

        Args:
            validate: If True, validate ZIP codes and states.
            errors: How to handle errors ("raise", "coerce", "ignore").
            service: Optional AddressService to use.

        Returns:
            DataFrame with columns for each address component.
        """
        import pandas as pd

        svc = service or self._get_service()

        parsed_data = self._obj.apply(
            lambda x: svc.to_series(x, validate=validate, errors=errors)
            if pd.notna(x) and x
            else pd.Series({field: None for field in ADDRESS_FIELDS})
        )

        return parsed_data


def register_accessor(name: str = "addr") -> None:
    """Register the address accessor on pandas Series.

    After calling this, you can use:
        >>> series.addr.parse()

    Args:
        name: Name for the accessor (default: "addr").

    Example:
        >>> import pandas as pd
        >>> from ryandata_address_utils.pandas_ext import register_accessor
        >>> register_accessor()
        >>> s = pd.Series(["123 Main St, Austin TX 78749"])
        >>> s.addr.parse()
    """
    import pandas as pd

    if not hasattr(pd.Series, name):
        pd.api.extensions.register_series_accessor(name)(AddressParserAccessor)


# -------------------------------------------------------------------------
# Backwards compatibility functions
# -------------------------------------------------------------------------


def parse_address_to_dict(
    address: str,
    validate: bool = True,
    errors: str = "raise",
) -> dict[str, str | None]:
    """Parse an address string and return a dictionary of components.

    Note: Prefer using AddressService.parse_to_dict() instead.

    Args:
        address: The address string to parse.
        validate: If True, validate ZIP code and state.
        errors: How to handle errors ("raise", "coerce", "ignore").

    Returns:
        Dictionary mapping field names to values.
    """
    from ryandata_address_utils.service import get_default_service

    service = get_default_service()
    return service.parse_to_dict(address, validate=validate, errors=errors)


def parse_addresses(
    df: pd.DataFrame,
    address_column: str,
    validate: bool = True,
    errors: str = "coerce",
    prefix: str = "",
    inplace: bool = False,
) -> pd.DataFrame:
    """Parse addresses in a DataFrame and add columns for each component.

    Note: Prefer using AddressService.parse_dataframe() instead.

    Args:
        df: Input DataFrame containing addresses.
        address_column: Name of the column containing address strings.
        validate: If True, validate ZIP codes and states.
        errors: How to handle parse errors ("raise", "coerce", "ignore").
        prefix: Prefix to add to new column names.
        inplace: If True, modify DataFrame in place.

    Returns:
        DataFrame with new columns for each address component.
    """
    from ryandata_address_utils.service import get_default_service

    service = get_default_service()
    return service.parse_dataframe(
        df,
        address_column,
        validate=validate,
        errors=errors,
        prefix=prefix,
        inplace=inplace,
    )


def parse_address_series(
    series: pd.Series,
    validate: bool = True,
    errors: str = "coerce",
) -> pd.DataFrame:
    """Parse a Series of addresses and return a DataFrame.

    Note: Prefer using series.addr.parse() after registering the accessor.

    Args:
        series: Pandas Series containing address strings.
        validate: If True, validate ZIP codes and states.
        errors: How to handle errors ("raise", "coerce", "ignore").

    Returns:
        DataFrame with columns for each address component.
    """
    import pandas as pd

    from ryandata_address_utils.service import get_default_service

    service = get_default_service()

    parsed_data = series.apply(
        lambda x: service.to_series(x, validate=validate, errors=errors)
        if pd.notna(x) and x
        else pd.Series({field: None for field in ADDRESS_FIELDS})
    )

    return parsed_data
