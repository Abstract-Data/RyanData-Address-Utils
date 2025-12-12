from pathlib import Path

import pytest
from typer.testing import CliRunner

from ryandata_address_utils import setup_cli

runner = CliRunner()


def test_setup_cli_dry_run(monkeypatch) -> None:
    monkeypatch.setattr(setup_cli, "check_libpostal", lambda data_dir: (True, None))

    with runner.isolated_filesystem() as tmp_dir:
        data_dir = Path(tmp_dir) / "libpostal-data"
        result = runner.invoke(
            setup_cli.app,
            ["setup", f"--data-dir={data_dir}", "--dry-run", "--yes"],
        )

    assert result.exit_code == 0
    assert "Detected platform" in result.stdout
    assert "libpostal is ready to use" in result.stdout


def test_setup_cli_check_only(monkeypatch) -> None:
    """check-only should only perform checks."""
    monkeypatch.setattr(setup_cli, "check_libpostal", lambda data_dir: (False, "not installed"))

    with runner.isolated_filesystem() as tmp_dir:
        data_dir = Path(tmp_dir) / "libpostal-data"
        result = runner.invoke(
            setup_cli.app,
            ["setup", f"--data-dir={data_dir}", "--check-only", "--yes"],
        )

    assert result.exit_code == 1  # check_only with failed check should exit 1
    assert "libpostal check failed" in result.stdout
    assert "not installed" in result.stdout


def test_setup_cli_yes_triggers_download(monkeypatch) -> None:
    """--yes should trigger download/install steps (dry-run mocked)."""
    calls: list[str] = []

    def fake_check(data_dir):
        return False, "missing"

    def fake_download(target_dir, *, dry_run=False):
        calls.append(f"download:{target_dir}")

    def fake_install(info, *, dry_run=False):
        calls.append(f"install:{info.name}")

    monkeypatch.setattr(setup_cli, "check_libpostal", fake_check)
    monkeypatch.setattr(setup_cli, "download_archives", fake_download)
    monkeypatch.setattr(setup_cli, "install_libpostal", fake_install)
    monkeypatch.setattr(
        setup_cli,
        "ensure_postal_binding",
        lambda dry_run=False: calls.append("ensure"),
    )

    with runner.isolated_filesystem() as tmp_dir:
        data_dir = Path(tmp_dir) / "libpostal-data"
        result = runner.invoke(
            setup_cli.app,
            ["setup", f"--data-dir={data_dir}", "--yes", "--dry-run"],
        )

    assert result.exit_code == 1  # final check still fails because fake check returns False
    assert "libpostal verification failed" in result.stdout
    assert any(c.startswith("download:") for c in calls)
    assert any(c.startswith("install:") for c in calls)
    assert "ensure" in calls


def test_setup_cli_check_only_success(monkeypatch) -> None:
    """check-only should exit 0 when libpostal is ready."""
    monkeypatch.setattr(setup_cli, "check_libpostal", lambda data_dir: (True, None))

    with runner.isolated_filesystem() as tmp_dir:
        data_dir = Path(tmp_dir) / "libpostal-data"
        result = runner.invoke(
            setup_cli.app,
            ["setup", f"--data-dir={data_dir}", "--check-only", "--yes"],
        )

    assert result.exit_code == 0
    assert "libpostal is available" in result.stdout


def test_ensure_postal_binding_noop_when_present(monkeypatch: pytest.MonkeyPatch) -> None:
    """If postal is already installed, ensure_postal_binding should do nothing."""
    fake_postal = object()
    monkeypatch.setitem(setup_cli.sys.modules, "postal", fake_postal)
    calls: list[list[str]] = []
    monkeypatch.setattr(setup_cli, "run_command", lambda *a, **k: calls.append(list(a[0])))
    setup_cli.ensure_postal_binding(dry_run=False)
    assert calls == []


def test_data_present_markers(tmp_path: Path) -> None:
    """data_present should detect common marker directories/files."""
    markers = ["language_classifier", "parser", "libpostal", "libpostal_data"]
    for marker in markers:
        path = tmp_path / marker
        path.mkdir()
        assert setup_cli.data_present(tmp_path)
        path.rmdir()
    # fallback: any file
    file_marker = tmp_path / "anything.bin"
    file_marker.write_text("x")
    assert setup_cli.data_present(tmp_path)


def test_download_archives_dry_run(capsys, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """download_archives should emit dry-run messages and skip downloads."""
    messages: list[str] = []

    def fake_echo(msg: str) -> None:
        messages.append(msg)

    monkeypatch.setattr(setup_cli.typer, "echo", fake_echo)
    setup_cli.download_archives(tmp_path, dry_run=True)
    assert any("Would fetch" in m for m in messages)


def test_setup_cli_final_success(monkeypatch, tmp_path: Path) -> None:
    """Setup should exit 0 when check passes after download/install mocks."""

    def fake_check(data_dir):
        return True, None

    monkeypatch.setattr(setup_cli, "check_libpostal", fake_check)
    monkeypatch.setattr(setup_cli, "download_archives", lambda *a, **k: None)
    monkeypatch.setattr(setup_cli, "install_libpostal", lambda *a, **k: None)
    monkeypatch.setattr(setup_cli, "ensure_postal_binding", lambda **k: None)

    with runner.isolated_filesystem() as tmp_dir:
        data_dir = Path(tmp_dir) / "libpostal-data"
        result = runner.invoke(
            setup_cli.app,
            ["setup", f"--data-dir={data_dir}", "--yes"],
        )

    assert result.exit_code == 0
    assert "libpostal is ready to use." in result.stdout


def test_setup_cli_prompted_data_dir(monkeypatch) -> None:
    """When data_dir not provided, prompt should be used."""
    prompt_calls: list[str] = []
    confirm_calls: list[bool] = []

    def fake_prompt(msg: str, default: str):
        prompt_calls.append(default)
        return default

    def fake_confirm(msg: str, default: bool = True):
        confirm_calls.append(default)
        return False  # skip installs/downloads

    def fake_default_data_dir(info):
        # Return a path within the current working directory (isolated filesystem)
        return Path.cwd() / "libpostal-data"

    monkeypatch.setattr(setup_cli.typer, "prompt", fake_prompt)
    monkeypatch.setattr(setup_cli.typer, "confirm", fake_confirm)
    monkeypatch.setattr(setup_cli, "default_data_dir", fake_default_data_dir)
    monkeypatch.setattr(setup_cli, "check_libpostal", lambda data_dir: (True, None))
    monkeypatch.setattr(setup_cli, "install_libpostal", lambda *a, **k: None)
    monkeypatch.setattr(setup_cli, "download_archives", lambda *a, **k: None)
    monkeypatch.setattr(setup_cli, "ensure_postal_binding", lambda **k: None)

    with runner.isolated_filesystem():
        result = runner.invoke(setup_cli.app, ["setup", "--dry-run"])

    assert result.exit_code == 0
    assert prompt_calls  # prompt was used
    assert confirm_calls  # confirm was invoked


def test_setup_cli_final_failure(monkeypatch, tmp_path: Path) -> None:
    """Final verification failure should exit with code 1."""
    monkeypatch.setattr(setup_cli, "check_libpostal", lambda data_dir: (False, "still broken"))
    monkeypatch.setattr(setup_cli, "download_archives", lambda *a, **k: None)
    monkeypatch.setattr(setup_cli, "install_libpostal", lambda *a, **k: None)
    monkeypatch.setattr(setup_cli, "ensure_postal_binding", lambda **k: None)

    result = runner.invoke(
        setup_cli.app,
        ["setup", f"--data-dir={tmp_path}", "--yes", "--dry-run"],
    )

    assert result.exit_code == 1
    assert "libpostal verification failed." in result.stdout


def test_setup_cli_existing_data_redownload(monkeypatch, tmp_path: Path) -> None:
    """When data already present and user confirms, download should run."""
    confirms = iter([True, True])  # install yes, redownload yes
    calls: list[str] = []

    monkeypatch.setattr(setup_cli, "data_present", lambda path: True)
    monkeypatch.setattr(setup_cli.typer, "confirm", lambda *_args, **_kwargs: next(confirms))
    monkeypatch.setattr(setup_cli, "check_libpostal", lambda data_dir: (True, None))
    monkeypatch.setattr(setup_cli, "install_libpostal", lambda *a, **k: calls.append("install"))
    monkeypatch.setattr(setup_cli, "download_archives", lambda *a, **k: calls.append("download"))
    monkeypatch.setattr(setup_cli, "ensure_postal_binding", lambda **k: None)

    result = runner.invoke(
        setup_cli.app,
        ["setup", f"--data-dir={tmp_path}", "--dry-run"],
    )

    assert result.exit_code == 0
    assert "download" in calls
