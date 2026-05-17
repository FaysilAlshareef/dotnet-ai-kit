"""T081 — Constitution v1.0.8 amendment + 5-rule universal whitelist.

PASS-CONDITIONAL gate per plan.md Constitution Check / commit 14.

Asserts:
1. `.specify/memory/constitution.md` version is `1.0.8` (NOT 1.0.7).
2. The universal whitelist enumerates exactly 5 rules:
   async-concurrency, coding-style, existing-projects, security, tool-calls.

This test MUST FAIL before T082 amends the constitution. After T082, this
test MUST PASS before T084+ (rule moves) proceed.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
CONSTITUTION = REPO / ".specify" / "memory" / "constitution.md"

EXPECTED_VERSION = "1.0.8"
EXPECTED_UNIVERSAL_RULES = frozenset(
    {"async-concurrency", "coding-style", "existing-projects", "security", "tool-calls"}
)


def test_constitution_version_is_1_0_8() -> None:
    """Per feature 019 commit 14: constitution MUST be amended to v1.0.8."""
    text = CONSTITUTION.read_text(encoding="utf-8")
    # Look for the version line at the bottom
    match = re.search(r"\*\*Version\*\*:\s*(\d+\.\d+\.\d+)", text)
    assert match, "Constitution must declare a **Version**: N.N.N line"
    actual = match.group(1)
    assert actual == EXPECTED_VERSION, (
        f"Constitution version is {actual}, expected {EXPECTED_VERSION}. "
        f"Per commit 14 PASS-CONDITIONAL gate: this test MUST PASS before "
        f"the rule-move (T084+) proceeds."
    )


def test_constitution_universal_whitelist_is_5_rules() -> None:
    """Per FR-011: universal whitelist MUST be exactly 5 rules."""
    text = CONSTITUTION.read_text(encoding="utf-8")

    # Per feature 019 / FR-011, the constitution must mention "5 universal"
    # and the 5 specific rule names.
    assert "5 universal" in text, (
        "Constitution must declare '5 universal' rules per FR-011"
    )

    for rule_name in EXPECTED_UNIVERSAL_RULES:
        assert rule_name in text, (
            f"Constitution must mention '{rule_name}' as a universal rule"
        )


def test_constitution_total_is_16_rules() -> None:
    """Per FR-011: 16 total rules = 5 universal + 11 path-scoped."""
    text = CONSTITUTION.read_text(encoding="utf-8")
    assert "16 rules" in text, "Constitution must declare total rule count: '16 rules'"
    assert "11 path-scoped" in text, (
        "Constitution must declare 11 path-scoped rules (was 12 before v1.0.8 / async-concurrency promotion)"
    )
