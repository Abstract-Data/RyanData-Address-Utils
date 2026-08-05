"""Verifies AGENTS.md and its cross-tool pointers stay in sync with what this repo requires.

Run directly (`python tests/verify/check_agents_md.py`) or under pytest — both work since the
checks are plain functions with assert statements.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTS_MD = REPO_ROOT / "AGENTS.md"

REQUIRED_SECTIONS = [
    "## Documentation Priority",
    "## Tool Permissions by Mode",
    "## Anti-Pattern Warnings",
    "## Important Notes for AI Assistants",
]


def test_agents_md_exists() -> None:
    assert AGENTS_MD.is_file(), "AGENTS.md is missing from the repo root"


def test_agents_md_has_required_sections() -> None:
    text = AGENTS_MD.read_text(encoding="utf-8")
    missing = [s for s in REQUIRED_SECTIONS if s not in text]
    assert not missing, f"AGENTS.md is missing required section(s): {missing}"


def test_claude_md_symlinks_to_agents_md() -> None:
    claude_md = REPO_ROOT / "CLAUDE.md"
    assert claude_md.is_symlink(), "CLAUDE.md must be a symlink to AGENTS.md"
    assert claude_md.resolve() == AGENTS_MD.resolve(), "CLAUDE.md must resolve to AGENTS.md"


def test_no_dangling_notion_references() -> None:
    """This project deliberately has no Notion/abstract-data coupling (see ADR 0001) —
    guard against a future tool re-introducing a pointer to a file that doesn't exist here."""
    text = AGENTS_MD.read_text(encoding="utf-8")
    assert ".agents/CAPABILITIES.md" not in text, (
        "AGENTS.md references .agents/CAPABILITIES.md, which this repo does not generate"
    )


if __name__ == "__main__":
    test_agents_md_exists()
    test_agents_md_has_required_sections()
    test_claude_md_symlinks_to_agents_md()
    test_no_dangling_notion_references()
    print("check_agents_md: all checks passed")
