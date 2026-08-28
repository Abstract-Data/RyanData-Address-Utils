"""README documents suffix-pair uniqueness and precinct-join caveats."""

from __future__ import annotations

from pathlib import Path

README = Path(__file__).resolve().parents[1] / "README.md"


def test_readme_documents_suffix_pair_and_cross_precinct_caveats() -> None:
    text = README.read_text(encoding="utf-8")
    assert "PRE|POST" in text
    assert "cross-precinct" in text
    assert "St_PosDir" in text or "RSTSFX" in text
