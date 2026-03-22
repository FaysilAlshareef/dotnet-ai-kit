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
    """AGENT_CONFIG must include a 'claude' entry."""
    assert "claude" in AGENT_CONFIG
    cfg = AGENT_CONFIG["claude"]
    assert cfg["name"] == "Claude Code"
    assert cfg["commands_dir"] == ".claude/commands"
    assert cfg["rules_dir"] == ".claude/rules"
    assert cfg["command_ext"] == ".md"


def test_supported_ai_tools_v1() -> None:
    """v1.0 only supports Claude."""
    assert SUPPORTED_AI_TOOLS == frozenset({"claude"})


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
