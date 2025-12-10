from pathlib import Path
from types import ModuleType

import pytest

from ryandata_address_utils import setup_cli


def test_default_args_inserts_setup_when_missing() -> None:
    assert setup_cli._default_args([]) == ["setup"]
    assert setup_cli._default_args(["--dry-run"]) == ["setup", "--dry-run"]
    assert setup_cli._default_args(["setup", "--yes"]) == ["setup", "--yes"]


def test_default_data_dir_macos() -> None:
    info = setup_cli.PlatformInfo(name="macos")
    assert setup_cli.default_data_dir(info) == Path.home() / ".libpostal-data"


def test_default_data_dir_windows_and_linux() -> None:
    assert setup_cli.default_data_dir(setup_cli.PlatformInfo(name="windows")) == Path(
        "C:/libpostal"
    )
    assert setup_cli.default_data_dir(setup_cli.PlatformInfo(name="linux")) == Path(
        "/usr/local/share/libpostal"
    )


def test_data_present_detects_any_file(tmp_path: Path) -> None:
    assert not setup_cli.data_present(tmp_path)
    marker = tmp_path / "libpostal"
    marker.mkdir()
    assert setup_cli.data_present(tmp_path)


def test_check_libpostal_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    parser_mod = ModuleType("postal.parser")

    def parse_address(addr: str):
        return [("10", "house_number")]

    parser_mod.parse_address = parse_address  # type: ignore[attr-defined]
    postal_mod = ModuleType("postal")
    monkeypatch.setitem(setup_cli.sys.modules, "postal", postal_mod)
    monkeypatch.setitem(setup_cli.sys.modules, "postal.parser", parser_mod)
    ok, reason = setup_cli.check_libpostal(tmp_path)
    assert ok
    assert reason is None

