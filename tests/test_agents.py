"""Tests for agent configuration and AI tool detection."""

from __future__ import annotations

from pathlib import Path

import pytest

from dotnet_ai_kit.agents import (
    AGENT_CONFIG,
    SUPPORTED_AI_TOOLS,
    detect_ai_tools,
    get_agent_config,
)

# ---------------------------------------------------------------------------
# AGENT_CONFIG
# ---------------------------------------------------------------------------


def test_agent_config_has_claude() -> None:
    """AGENT_CONFIG must include a 'claude' entry (existing v1 behavior preserved)."""
    assert "claude" in AGENT_CONFIG
    cfg = AGENT_CONFIG["claude"]
    assert cfg["name"] == "Claude Code"
    assert cfg["commands_dir"] == ".claude/commands"
    assert cfg["rules_dir"] == ".claude/rules"
    assert cfg["command_ext"] == ".md"


def test_agent_config_has_codex() -> None:
    """AGENT_CONFIG must include a 'codex' entry (T001 — feature 019 multi-host)."""
    assert "codex" in AGENT_CONFIG
    cfg = AGENT_CONFIG["codex"]
    assert cfg["name"] == "Codex CLI"


def test_agent_config_has_cursor() -> None:
    """AGENT_CONFIG must include a 'cursor' entry (T001 — feature 019 multi-host)."""
    assert "cursor" in AGENT_CONFIG
    cfg = AGENT_CONFIG["cursor"]
    assert cfg["name"] == "Cursor"


def test_agent_config_has_copilot() -> None:
    """AGENT_CONFIG must include a 'copilot' entry (T001 — feature 019 multi-host)."""
    assert "copilot" in AGENT_CONFIG
    cfg = AGENT_CONFIG["copilot"]
    assert cfg["name"] == "GitHub Copilot"


def test_supported_ai_tools_multi_host() -> None:
    """Feature 019: all four plugin hosts are first-class supported.

    Replaces the v1-only single-host frozenset({"claude"}) per T001/T002 /
    plan.md commit 1. Hosts are equal members of the supported set; Codex
    and Cursor are plugin-native, Copilot is render-only.
    """
    assert SUPPORTED_AI_TOOLS == frozenset({"claude", "codex", "cursor", "copilot"})


# ---------------------------------------------------------------------------
# get_agent_config
# ---------------------------------------------------------------------------


def test_get_agent_config_valid() -> None:
    """get_agent_config should return config for known tools."""
    cfg = get_agent_config("claude")
    assert cfg["name"] == "Claude Code"


def test_get_agent_config_case_insensitive() -> None:
    """get_agent_config should be case-insensitive."""
    cfg = get_agent_config("CLAUDE")
    assert cfg["name"] == "Claude Code"


def test_get_agent_config_unknown_tool() -> None:
    """get_agent_config should raise ValueError for unknown tools."""
    with pytest.raises(ValueError, match="Unknown AI tool"):
        get_agent_config("nonexistent")


# ---------------------------------------------------------------------------
# detect_ai_tools
# ---------------------------------------------------------------------------


def test_detect_ai_tools_finds_claude(tmp_path: Path) -> None:
    """detect_ai_tools should detect .claude/ directory."""
    (tmp_path / ".claude").mkdir()
    detected = detect_ai_tools(tmp_path)
    assert detected == ["claude"]


def test_detect_ai_tools_empty_project(tmp_path: Path) -> None:
    """detect_ai_tools should return empty list when no tools found."""
    detected = detect_ai_tools(tmp_path)
    assert detected == []


def test_detect_ai_tools_ignores_files(tmp_path: Path) -> None:
    """detect_ai_tools should not detect a .claude file (only directories)."""
    (tmp_path / ".claude").write_text("not a dir", encoding="utf-8")
    detected = detect_ai_tools(tmp_path)
    assert detected == []
