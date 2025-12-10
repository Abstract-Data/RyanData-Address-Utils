from pathlib import Path

from typer.testing import CliRunner

from ryandata_address_utils import setup_cli

runner = CliRunner()


def test_setup_cli_dry_run(monkeypatch) -> None:
    monkeypatch.setattr(setup_cli, "check_libpostal", lambda data_dir: (True, None))

    with runner.isolated_filesystem() as tmp_dir:
        data_dir = Path(tmp_dir) / "libpostal-data"
        result = runner.invoke(
            setup_cli.app,
            [f"--data-dir={data_dir}", "--dry-run", "--yes"],
        )

    assert result.exit_code == 0
    assert "Detected platform" in result.stdout
    assert "libpostal is ready to use" in result.stdout
