"""T023a (PR2a half) + T052b (PR3 half) — FR-008 / FR-017: profile frontmatter."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
PROFILES = REPO / "profiles"


def _profiles() -> list[Path]:
    return sorted(PROFILES.rglob("*.md"))


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


def test_profiles_have_no_alwaysApply() -> None:
    for profile in _profiles():
        text = profile.read_text(encoding="utf-8")
        assert "alwaysApply" not in text, f"{profile}: alwaysApply still present"


def test_profiles_have_top_level_paths() -> None:
    """FR-017 (T052b half): every profile must declare top-level paths:."""
    for profile in _profiles():
        fm = _frontmatter(profile)
        assert "paths" in fm, f"{profile}: profile must have top-level paths:"
