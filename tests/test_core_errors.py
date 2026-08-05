"""Tests for the generic core.errors.RyanDataError / RyanDataValidationError base classes.

These are exported via core/__init__.py but had zero direct test coverage —
only the models.errors.RyanDataAddressError subclass was exercised.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError
from pydantic_core import PydanticCustomError

from ryandata_address_utils.core.errors import RyanDataError, RyanDataValidationError


class TestRyanDataError:
    def test_init_sets_package_context(self) -> None:
        err = RyanDataError("my_package", "bad_value", "Something went wrong", {"field": "x"})
        assert err.context == {"package": "my_package", "field": "x"}
        assert err.type == "bad_value"
        assert str(err) == "Something went wrong"

    def test_from_pydantic_error_wraps_with_package(self) -> None:
        original = PydanticCustomError("bad_value", "Original message", {"field": "y"})
        wrapped = RyanDataError.from_pydantic_error("my_package", original)
        assert wrapped.type == "bad_value"
        assert wrapped.context is not None
        assert wrapped.context["package"] == "my_package"
        assert wrapped.context["field"] == "y"

    def test_from_validation_error_extracts_custom_error(self) -> None:
        class Model(BaseModel):
            value: int

        try:
            Model(value="not an int")
        except ValidationError as exc:
            wrapped = RyanDataError.from_validation_error("my_package", exc)

        assert isinstance(wrapped, RyanDataError)
        assert wrapped.context is not None
        assert wrapped.context["package"] == "my_package"

    def test_from_validation_error_generic_exception(self) -> None:
        wrapped = RyanDataError.from_validation_error("my_package", ValueError("boom"))
        assert isinstance(wrapped, RyanDataError)
        assert wrapped.type == "validation_error"


class TestRyanDataValidationError:
    def test_init_wraps_pydantic_validation_error(self) -> None:
        class Model(BaseModel):
            value: int

        try:
            Model(value="not an int")
        except ValidationError as exc:
            wrapped = RyanDataValidationError("my_package", exc)

        assert wrapped.package_name == "my_package"
        assert wrapped.errors()
        assert "my_package" in repr(wrapped)

    def test_init_wraps_generic_exception(self) -> None:
        wrapped = RyanDataValidationError("my_package", ValueError("boom"))
        assert wrapped.errors() == []
        assert str(wrapped) == "boom"

    def test_from_validation_error_classmethod(self) -> None:
        wrapped = RyanDataValidationError.from_validation_error("my_package", ValueError("boom"))
        assert isinstance(wrapped, RyanDataValidationError)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
