"""T023 (PR2a half) + T049 (PR3 half) — FR-008 / FR-011: rule frontmatter."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
RULES = REPO / "rules"

# Feature 019 / commit 14: 5-rule universal whitelist (added async-concurrency).
# Rules now live in `rules/conventions/` (5 universal) + `rules/domain/`
# (11 path-scoped). Legacy top-level `rules/*.md` was migrated by T088/T089.
UNIVERSAL_RULES = {
    "async-concurrency",
    "existing-projects",
    "tool-calls",
    "coding-style",
    "security",
}


def _all_rules() -> list[Path]:
    """All 16 rules under rules/{conventions,domain}/."""
    return sorted((RULES / "conventions").glob("*.md")) + sorted((RULES / "domain").glob("*.md"))


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


def test_rules_have_no_alwaysApply() -> None:
    for rule in _all_rules():
        text = rule.read_text(encoding="utf-8")
        assert "alwaysApply" not in text, f"{rule}: alwaysApply still present"


def test_rules_frontmatter_parses() -> None:
    for rule in _all_rules():
        fm = _frontmatter(rule)
        # description is optional; we only verify the YAML parses.
        assert isinstance(fm, dict), f"{rule}: frontmatter is not a mapping"


def test_non_universal_rules_have_paths() -> None:
    """FR-011: domain rules (path-scoped) MUST declare top-level `paths:` scope."""
    for rule in (RULES / "domain").glob("*.md"):
        fm = _frontmatter(rule)
        assert "paths" in fm, (
            f"{rule}: path-scoped (domain) rule must have top-level paths: (stem={rule.stem!r})"
        )


def test_universal_rules_combined_line_budget() -> None:
    """FR-011: the 5 universal rules combined must stay <= 300 physical lines.

    Feature 019 / commit 14: rules moved to `rules/conventions/`. The 300-line
    budget is unchanged from the 4-rule constitution (v1.0.7) — the constitution
    v1.0.8 amendment retained the budget while adding async-concurrency.
    """
    total = 0
    missing = []
    for stem in UNIVERSAL_RULES:
        p = RULES / "conventions" / f"{stem}.md"
        if not p.is_file():
            missing.append(stem)
            continue
        total += len(p.read_text(encoding="utf-8").splitlines())
    if missing:
        pytest.fail(f"missing universal rules under rules/conventions/: {missing}")
    assert total <= 300, f"universal rules total {total} lines (>300)"
