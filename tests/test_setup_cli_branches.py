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


def test_check_libpostal_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    parser_mod = ModuleType("postal.parser")

    def parse_address(addr: str):
        raise RuntimeError("missing data")  # force failure path

    parser_mod.parse_address = parse_address  # type: ignore[attr-defined]
    postal_mod = ModuleType("postal")
    monkeypatch.setitem(setup_cli.sys.modules, "postal", postal_mod)
    monkeypatch.setitem(setup_cli.sys.modules, "postal.parser", parser_mod)
    ok, reason = setup_cli.check_libpostal(tmp_path)
    assert not ok
    assert reason is not None


def test_install_libpostal_macos_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """macOS install should invoke brew when available (dry-run)."""
    calls: list[list[str]] = []

    def fake_run_command(cmd: list[str], *, dry_run: bool = False) -> None:
        calls.append(cmd)

    monkeypatch.setattr(setup_cli.shutil, "which", lambda name: "/usr/local/bin/brew")
    monkeypatch.setattr(setup_cli, "run_command", fake_run_command)
    info = setup_cli.PlatformInfo(name="macos")
    setup_cli.install_libpostal(info, dry_run=True)
    assert calls == [["brew", "install", "libpostal"]]


def test_install_libpostal_linux_unknown_dry_run(capsys, monkeypatch: pytest.MonkeyPatch) -> None:
    """Unknown linux distro should print manual instructions."""
    monkeypatch.setattr(setup_cli.shutil, "which", lambda name: None)
    info = setup_cli.PlatformInfo(name="linux", distro="mystery")
    setup_cli.install_libpostal(info, dry_run=True)
    out = capsys.readouterr().out
    assert "Unknown Linux distribution" in out
    assert "install libpostal from source" in out


def test_install_libpostal_linux_apt_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ubuntu/Debian path should call apt-get commands."""
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], *, dry_run: bool = False) -> None:
        calls.append(cmd)

    monkeypatch.setattr(setup_cli, "run_command", fake_run)
    monkeypatch.setattr(setup_cli.shutil, "which", lambda name: "/usr/bin/apt-get")
    info = setup_cli.PlatformInfo(name="linux", distro="ubuntu")
    setup_cli.install_libpostal(info, dry_run=True)
    assert calls[0] == ["sudo", "apt-get", "update"]
    assert calls[1][:3] == ["sudo", "apt-get", "install"]


def test_install_libpostal_linux_dnf_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fedora/RHEL path should call dnf install."""
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], *, dry_run: bool = False) -> None:
        calls.append(cmd)

    monkeypatch.setattr(setup_cli, "run_command", fake_run)
    monkeypatch.setattr(setup_cli.shutil, "which", lambda name: "/usr/bin/dnf")
    info = setup_cli.PlatformInfo(name="linux", distro="fedora")
    setup_cli.install_libpostal(info, dry_run=True)
    assert calls == [["sudo", "dnf", "install", "-y", "libpostal", "libpostal-data"]]


def test_install_libpostal_linux_yum_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fallback to yum when dnf missing."""
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], *, dry_run: bool = False) -> None:
        calls.append(cmd)

    # Simulate no dnf but yum present
    def fake_which(name: str):
        return "/usr/bin/yum" if name == "yum" else None

    monkeypatch.setattr(setup_cli, "run_command", fake_run)
    monkeypatch.setattr(setup_cli.shutil, "which", fake_which)
    info = setup_cli.PlatformInfo(name="linux", distro="fedora")
    setup_cli.install_libpostal(info, dry_run=True)
    assert calls == [["sudo", "yum", "install", "-y", "libpostal", "libpostal-data"]]


def test_install_libpostal_windows_message(capsys) -> None:
    """Windows path should emit guidance message."""
    info = setup_cli.PlatformInfo(name="windows")
    setup_cli.install_libpostal(info, dry_run=True)
    out = capsys.readouterr().out
    assert "not officially supported" in out


def test_ensure_postal_binding_attempts_install(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    """When postal is missing, ensure_postal_binding should attempt install guidance."""
    import builtins

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "postal":
            raise ImportError("postal missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    calls: list[list[str]] = []

    def fake_run_command(cmd: list[str], *, dry_run: bool = False) -> None:
        calls.append(cmd)

    monkeypatch.setattr(setup_cli, "run_command", fake_run_command)
    monkeypatch.setattr(setup_cli.shutil, "which", lambda name: "pip")
    setup_cli.ensure_postal_binding(dry_run=True)
    out = capsys.readouterr().out
    assert "pip install postal" in out
    assert calls == []  # dry_run=True should not invoke pip


def test_ensure_postal_binding_installs_when_not_dry(monkeypatch: pytest.MonkeyPatch) -> None:
    """ensure_postal_binding should invoke pip when dry_run=False."""
    import builtins

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "postal":
            raise ImportError("postal missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    calls: list[list[str]] = []

    def fake_run_command(cmd: list[str], *, dry_run: bool = False) -> None:
        calls.append(cmd)

    monkeypatch.setattr(setup_cli, "run_command", fake_run_command)
    monkeypatch.setattr(setup_cli.shutil, "which", lambda name: "pip")
    setup_cli.ensure_postal_binding(dry_run=False)
    assert calls == [["pip", "install", "postal"]]
