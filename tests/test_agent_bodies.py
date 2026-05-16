"""T024 — FR-014 / FR-015: agent bodies free of bulk Skills Loaded blocks."""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
AGENTS = REPO / "agents"


def _agents() -> list[Path]:
    return sorted(AGENTS.glob("*.md"))


def test_no_skills_loaded_section() -> None:
    for agent in _agents():
        text = agent.read_text(encoding="utf-8")
        assert not re.search(r"^##\s+Skills Loaded\s*$", text, re.MULTILINE), (
            f"{agent}: still contains '## Skills Loaded' section"
        )


def test_no_availability_always_line() -> None:
    for agent in _agents():
        text = agent.read_text(encoding="utf-8")
        assert "**Availability**: Always" not in text, (
            f"{agent}: still has '**Availability**: Always' line"
        )
