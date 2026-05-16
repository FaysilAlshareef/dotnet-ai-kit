"""T022 — FR-006 / FR-007 / FR-008: SKILL.md frontmatter canonical shape."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"

# Activation fields that MUST NOT live under metadata: (FR-006).
FORBIDDEN_NESTED = {
    "paths",
    "when-to-use",
    "when_to_use",
    "alwaysApply",
    "disable-model-invocation",
    "user-invocable",
}

# Allow-list for any legacy skill that an author can't realistically rewrite.
LEGACY_SKILL_ALLOWLIST: set[str] = set()


def _skills() -> list[Path]:
    return sorted(SKILLS.rglob("SKILL.md"))


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        pytest.fail(f"{path}: missing YAML frontmatter")
    return yaml.safe_load(m.group(1)) or {}


def test_no_forbidden_nested_metadata_fields() -> None:
    for skill in _skills():
        if skill.name in LEGACY_SKILL_ALLOWLIST:
            continue
        fm = _frontmatter(skill)
        metadata = fm.get("metadata") or {}
        if not isinstance(metadata, dict):
            continue
        offenders = set(metadata.keys()) & FORBIDDEN_NESTED
        assert not offenders, (
            f"{skill}: nested metadata still contains activation fields: {offenders}"
        )


def test_no_alwaysApply_anywhere() -> None:
    for skill in _skills():
        text = skill.read_text(encoding="utf-8")
        assert "alwaysApply" not in text, f"{skill}: alwaysApply still present"


def test_top_level_description_is_use_when_trigger() -> None:
    valid_prefixes = ("Use when ", "Use during ", "Use for ")
    for skill in _skills():
        if skill.name in LEGACY_SKILL_ALLOWLIST:
            continue
        fm = _frontmatter(skill)
        desc = (fm.get("description") or "").strip()
        assert desc, f"{skill}: missing top-level description"
        assert desc.startswith(valid_prefixes), (
            f"{skill}: description must start with a trigger ('Use when …'); got: {desc[:60]!r}"
        )
