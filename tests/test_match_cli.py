"""CLI wiring for uniqueness."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from ryandata_address_utils.setup_cli import app

runner = CliRunner()


def test_uniqueness_command_passes_voterfile_and_sources(tmp_path: Path) -> None:
    vf = tmp_path / "vf.csv"
    vf.write_text("COUNTY,PCT,RHNUM,RSTNAME,RSTTYPE\nANDERSON,1,1,MAIN,ST\n", encoding="utf-8")
    captured: dict[str, object] = {}

    def fake_run(voterfile: Path, **kwargs: object) -> dict[str, object]:
        captured["voterfile"] = voterfile
        captured["sources"] = kwargs.get("sources")
        return {"outcomes": str(tmp_path / "outcomes.csv"), "n": 1, "sources": ["txgio", "tiger"]}

    with patch("ryandata_address_utils.match.cli.run_uniqueness", fake_run):
        result = runner.invoke(
            app,
            ["uniqueness", "--voterfile", str(vf), "--sources", "txgio,tiger"],
        )
    assert result.exit_code == 0, result.output
    assert captured["sources"] == "txgio,tiger"
    assert Path(str(captured["voterfile"])) == vf


def test_uniqueness_command_passes_counties(tmp_path: Path) -> None:
    vf = tmp_path / "vf.csv"
    vf.write_text("COUNTY,PCT,RHNUM,RSTNAME,RSTTYPE\nANDERSON,1,1,MAIN,ST\n", encoding="utf-8")
    captured: dict[str, object] = {}

    def fake_run(voterfile: Path, **kwargs: object) -> dict[str, object]:
        captured["counties"] = kwargs.get("counties")
        return {"outcomes": "x", "n": 1, "sources": ["txgio"]}

    with patch("ryandata_address_utils.match.cli.run_uniqueness", fake_run):
        result = runner.invoke(
            app,
            ["uniqueness", "--voterfile", str(vf), "--counties", "ANDERSON"],
        )
    assert result.exit_code == 0, result.output
    assert captured["counties"] == ("ANDERSON",)
