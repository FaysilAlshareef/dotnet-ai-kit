"""T047 (PR3 half) + T063 (PR4 half) — FR-012 / FR-021 / FR-022."""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
COMMANDS = REPO / "commands"

OPERATIONAL_COMMANDS_PR4: tuple[str, ...] = (
    "detect.md",
    "learn.md",
    "analyze.md",
    "plan.md",
    "implement.md",
    "review.md",
    "add-tests.md",
)

MCP_FIRST_MARKER = "MCP-first"
EXACT_FALLBACK_LINE = (
    "MCP unavailable: codebase-memory-mcp is not connected or below >=0.6.1; "
    "falling back to csharp-ls + grep/read."
)

FORBIDDEN_BULK_LOAD = re.compile(r"load\s+all\s+skills\s+listed", re.IGNORECASE)


def _cmd_files() -> list[Path]:
    return sorted(COMMANDS.glob("*.md"))


def test_no_load_all_skills_block_in_any_command() -> None:
    """FR-012 — wording-tolerant assertion that the historical
    "Load all skills listed in the agent's Skills Loaded section" line
    no longer appears in any command."""
    offenders: list[str] = []
    for cmd in _cmd_files():
        text = cmd.read_text(encoding="utf-8")
        if FORBIDDEN_BULK_LOAD.search(text):
            offenders.append(cmd.name)
    assert not offenders, f"bulk-load instruction still present in: {offenders}"


def test_operational_commands_carry_mcp_first_block() -> None:
    """T063 — FR-021: every operational command names the MCP-first division."""
    missing: list[str] = []
    for name in OPERATIONAL_COMMANDS_PR4:
        text = (COMMANDS / name).read_text(encoding="utf-8")
        if MCP_FIRST_MARKER not in text:
            missing.append(name)
    assert not missing, f"missing MCP-first block: {missing}"


def test_operational_commands_carry_exact_fallback_line() -> None:
    """T063 — FR-022: every operational command carries the EXACT fallback line."""
    missing: list[str] = []
    for name in OPERATIONAL_COMMANDS_PR4:
        text = (COMMANDS / name).read_text(encoding="utf-8")
        if EXACT_FALLBACK_LINE not in text:
            missing.append(name)
    assert not missing, f"missing exact fallback line in: {missing}"
