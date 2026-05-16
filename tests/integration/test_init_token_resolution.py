"""T046a — SC-006: end-to-end ``/dai.init`` leaves no `${detected_paths.` tokens."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from dotnet_ai_kit.copier import DeploymentError, copy_skills

REPO = Path(__file__).resolve().parents[2]
SKILLS_SRC = REPO / "skills"


def _make_detected_paths() -> dict[str, str]:
    """Return enough detected_paths keys to cover every token used in skills/."""
    keys: set[str] = set()
    for skill in SKILLS_SRC.rglob("SKILL.md"):
        text = skill.read_text(encoding="utf-8")
        keys.update(re.findall(r"\$\{detected_paths\.(\w+)\}", text))
    return {k: f"src/Fake.{k.title()}" for k in sorted(keys)}


def test_no_unresolved_tokens_in_deployed_skills(tmp_path: Path) -> None:
    detected = _make_detected_paths()
    if not detected:
        pytest.skip("no detected_paths tokens used in shipped skills")

    target = tmp_path / "project"
    tool_config = {"skills_dir": ".claude/skills"}

    try:
        count = copy_skills(SKILLS_SRC, target, tool_config, detected_paths=detected)
    except DeploymentError as exc:
        pytest.fail(f"deployment aborted: {exc}")

    assert count > 0
    # Walk every deployed skill — assert no literal "${detected_paths." remains.
    for deployed in (target / ".claude/skills").rglob("*.md"):
        text = deployed.read_text(encoding="utf-8")
        assert "${detected_paths." not in text, (
            f"{deployed}: unresolved token left in deployed file"
        )
