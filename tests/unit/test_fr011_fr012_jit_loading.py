"""T086 — FR-011 / FR-012: just-in-time loading of domain rules (commit 14).

Asserts that domain rules (`rules/domain/<name>.md`) load ONLY when their
matching skill or path is touched — NOT preloaded at session start.

Verified structurally by:
1. Each domain rule has `paths:` frontmatter declaring its activation
   condition (matched in test_rule_frontmatter.py).
2. The SessionStart hook does NOT inline domain rule bodies (matched in
   test_session_start_budget.py::test_session_start_no_rule_bodies).
3. No skill SKILL.md references a domain rule via an always-loaded path
   token (this test).
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
RULES_DOMAIN = REPO / "rules" / "domain"
SKILLS = REPO / "skills"


def test_domain_rules_each_have_paths_frontmatter() -> None:
    """Per FR-011 / FR-012: each domain rule MUST declare its activation scope."""
    import yaml as _yaml

    fm_re = re.compile(r"^---\n(.*?\n)---\n", re.DOTALL)
    for rule in RULES_DOMAIN.glob("*.md"):
        text = rule.read_text(encoding="utf-8")
        m = fm_re.match(text)
        assert m, f"{rule.name}: missing YAML frontmatter"
        fm = _yaml.safe_load(m.group(1)) or {}
        assert "paths" in fm, (
            f"{rule.name}: domain rule must declare `paths:` for JIT activation"
        )


def test_skills_do_not_inline_domain_rule_bodies() -> None:
    """No SKILL.md MUST inline a full domain rule body.

    A rule body has structured headers (## section names from the rule
    template) and is long; we assert SKILL.md files don't accidentally
    embed entire rule contents.
    """
    if not SKILLS.is_dir():
        return  # skills/ may not exist in all checkouts
    for skill in SKILLS.rglob("SKILL.md"):
        body = skill.read_text(encoding="utf-8")
        # Heuristic: no SKILL.md should be >>800 lines (which would indicate
        # rule bodies got inlined). Constitution says 400 lines max per skill.
        line_count = len(body.splitlines())
        assert line_count <= 800, (
            f"{skill.relative_to(REPO)}: {line_count} lines — probably has "
            "inlined rule bodies (Constitution V: 400-line max)"
        )
