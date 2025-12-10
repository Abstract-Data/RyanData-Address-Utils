import warnings

from ryandata_address_utils import service


def test_libpostal_warning_emits_once(monkeypatch) -> None:
    monkeypatch.setattr(service, "lp_parse_address", None)
    monkeypatch.setattr(service, "_libpostal_warned", False)
    monkeypatch.setenv("RYANDATA_LIBPOSTAL_WARN", "1")

    with warnings.catch_warnings(record=True) as caught:
        service._maybe_warn_libpostal_missing()
        service._maybe_warn_libpostal_missing()

    assert len(caught) == 1
    assert "libpostal not available" in str(caught[0].message)
