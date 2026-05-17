"""T023 (PR2a half) + T049 (PR3 half) — FR-008 / FR-011: rule frontmatter."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
RULES = REPO / "rules"

UNIVERSAL_RULES = {"existing-projects", "tool-calls", "coding-style", "security"}


def _rules() -> list[Path]:
    return sorted(RULES.glob("*.md"))


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


def test_rules_have_no_alwaysApply() -> None:
    for rule in _rules():
        text = rule.read_text(encoding="utf-8")
        assert "alwaysApply" not in text, f"{rule}: alwaysApply still present"


def test_rules_frontmatter_parses() -> None:
    for rule in _rules():
        fm = _frontmatter(rule)
        # description is optional; we only verify the YAML parses.
        assert isinstance(fm, dict), f"{rule}: frontmatter is not a mapping"


def test_non_universal_rules_have_paths() -> None:
    """FR-011 (T049): rules outside the 4-file universal whitelist must
    declare a top-level ``paths:`` scope."""
    for rule in _rules():
        if rule.stem in UNIVERSAL_RULES:
            continue
        fm = _frontmatter(rule)
        assert "paths" in fm, (
            f"{rule}: non-universal rule must have top-level paths: "
            f"(stem={rule.stem!r}, universal={sorted(UNIVERSAL_RULES)})"
        )


def test_universal_rules_combined_line_budget() -> None:
    """FR-011 (T049): the 4 universal rules combined must stay <= 300 physical lines."""
    total = 0
    missing = []
    for stem in UNIVERSAL_RULES:
        p = RULES / f"{stem}.md"
        if not p.is_file():
            missing.append(stem)
            continue
        total += len(p.read_text(encoding="utf-8").splitlines())
    if missing:
        pytest.fail(f"missing universal rules: {missing}")
    assert total <= 300, f"universal rules total {total} lines (>300)"
