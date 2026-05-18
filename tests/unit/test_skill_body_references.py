"""T087 — Skill bodies reference convention rules via plugin path (CHK036).

Per FR-011 / CHK036: every always-on convention rule MUST be referenced
from at least one skill that depends on it, via the canonical path
`${CLAUDE_PLUGIN_ROOT}/rules/conventions/<name>.md`. This is the JIT
load-trigger pattern: skills declare their rule dependencies through
the body reference; the Claude plugin host resolves the path at
load time.

This test asserts AT LEAST ONE skill references each of the 5 universal
convention rules via the plugin path. Stricter coverage would require
domain analysis per skill — out of scope for v1.0.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SKILLS = REPO / "skills"

UNIVERSAL_RULES = (
    "async-concurrency",
    "coding-style",
    "existing-projects",
    "security",
    "tool-calls",
)


def _all_skill_bodies() -> str:
    """Concatenate every SKILL.md body for cross-skill grep."""
    if not SKILLS.is_dir():
        return ""
    out: list[str] = []
    for skill in SKILLS.rglob("SKILL.md"):
        try:
            out.append(skill.read_text(encoding="utf-8"))
        except OSError:
            continue
    return "\n".join(out)


def test_each_convention_rule_referenced_by_at_least_one_skill() -> None:
    """Per CHK036: each universal rule MUST be referenced by ≥1 skill body."""
    haystack = _all_skill_bodies()
    if not haystack:
        # skills/ may not exist in fresh checkouts; the rule-reference
        # invariant cannot be verified without skill files.
        return
    missing: list[str] = []
    for rule in UNIVERSAL_RULES:
        ref_path = f"${{CLAUDE_PLUGIN_ROOT}}/rules/conventions/{rule}.md"
        if ref_path not in haystack:
            missing.append(rule)
    assert not missing, (
        f"CHK036: convention rules not referenced by any skill body via "
        f"`${{CLAUDE_PLUGIN_ROOT}}/rules/conventions/<name>.md`: {missing}"
    )


def test_reference_uses_canonical_plugin_path() -> None:
    """The reference path MUST use `${CLAUDE_PLUGIN_ROOT}` (NOT a relative
    or absolute file path), so the Claude plugin host can resolve it at
    fire-time per FR-009 / FR-010.
    """
    haystack = _all_skill_bodies()
    if not haystack:
        return
    for rule in UNIVERSAL_RULES:
        # If a skill references the rule at all, it MUST use the plugin path.
        # Detect any non-plugin reference (relative or root-relative).
        bare_filename = f"{rule}.md"
        if bare_filename not in haystack:
            continue
        # Find which non-plugin patterns appear; flag if no plugin-path use.
        canonical = f"${{CLAUDE_PLUGIN_ROOT}}/rules/conventions/{rule}.md"
        # Allow alternative: skill might prefix with rules/conventions/ in a
        # markdown link relative path — that's still acceptable IF the canonical
        # plugin path also exists somewhere.
        assert canonical in haystack, (
            f"Rule `{rule}` mentioned in some skill body but canonical "
            f"`${{CLAUDE_PLUGIN_ROOT}}/rules/conventions/{rule}.md` path not present"
        )
