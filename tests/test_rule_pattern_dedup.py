"""FR-036 — static check: rules MUST be compact hard policy.

A rule file MUST NOT contain a long block of pattern examples or recipes
that belong in skills. Heuristic: any single fenced code block ≥40 lines
indicates a recipe leaking into a rule and is a violation.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RULES = REPO / "rules"

FENCE_RE = re.compile(r"```[a-zA-Z0-9_+-]*\n(.*?)```", re.DOTALL)
MAX_BLOCK_LINES = 40


def test_no_rule_has_a_long_code_block() -> None:
    offenders: list[tuple[str, int]] = []
    for rule in sorted(RULES.glob("*.md")):
        text = rule.read_text(encoding="utf-8")
        for match in FENCE_RE.finditer(text):
            lines = match.group(1).count("\n")
            if lines > MAX_BLOCK_LINES:
                offenders.append((rule.name, lines))
                break
    assert not offenders, (
        "rules must be compact policy; long pattern examples belong in skills "
        f"(FR-036). Offenders: {offenders}"
    )
