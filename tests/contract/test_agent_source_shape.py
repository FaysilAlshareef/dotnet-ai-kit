"""T161 (commit 23, F-F): agents-source/*.md contract — no host-allow-list
fields at top level (those nest under `host_overrides:`).

Per Codex round-3 guidance: assert "no forbidden top-level fields" rather
than "every source has host_overrides" — don't over-constrain future
minimal agents (e.g., a doc-only stub with just name/description).
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "agents-source"

# Per data-model § 7 / agent-source.contract.md: these host-allow-list keys
# MUST NOT appear at the top level of agents-source/*.md. They belong under
# `host_overrides.<host>:`.
FORBIDDEN_TOP_LEVEL: frozenset[str] = frozenset(
    {
        "role",
        "expertise",
        "complexity",
        "max_iterations",
        "model",
        "readonly",
        "target",
        "tools",
        "disable-model-invocation",
        "user-invocable",
        "mcp-servers",
    }
)


def _parse_frontmatter(text: str) -> dict:
    """Extract the YAML frontmatter from a markdown file."""
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


def test_no_agent_source_has_forbidden_top_level_field() -> None:
    """Every agents-source/*.md MUST have no host-allow-list fields at top level."""
    sources = sorted(SRC.glob("*.md"))
    assert sources, "agents-source/ has no *.md files — unexpected"

    violations: list[str] = []
    for src in sources:
        fm = _parse_frontmatter(src.read_text(encoding="utf-8"))
        bad = [k for k in fm if k in FORBIDDEN_TOP_LEVEL]
        if bad:
            violations.append(f"{src.name}: top-level forbidden fields {bad}")

    assert not violations, (
        "F-F violation: agents-source contains host-allow-list fields at "
        f"top level. These must nest under `host_overrides.<host>:`.\n"
        + "\n".join(f"  - {v}" for v in violations)
    )
