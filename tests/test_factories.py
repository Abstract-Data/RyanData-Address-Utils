import pytest

from ryandata_address_utils.data.factory import DataSourceFactory
from ryandata_address_utils.parsers.factory import ParserFactory


def test_parser_factory_default_and_error() -> None:
    """ParserFactory should provide default usaddress and raise on unknown."""
    parser = ParserFactory.create()
    assert parser is not None
    with pytest.raises(ValueError):
        ParserFactory.create("unknown-type")


def test_data_source_factory_default_and_error() -> None:
    """DataSourceFactory should provide default csv source and raise on unknown."""
    source = DataSourceFactory.create()
    assert source is not None
    with pytest.raises(ValueError):
        DataSourceFactory.create("unknown-type")
