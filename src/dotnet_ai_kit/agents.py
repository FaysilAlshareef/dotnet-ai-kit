"""AGENT_CONFIG for AI tool integration.

Maps AI tool names to their configuration (directory paths, file extensions,
command prefixes) and provides detection and lookup utilities.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Agent configuration per supported AI tool.
# Each entry describes where commands and rules live for that tool.
AGENT_CONFIG: dict[str, dict[str, Any]] = {
    "claude": {
        "name": "Claude Code",
        "commands_dir": ".claude/commands",
        "rules_dir": ".claude/rules",
        "skills_dir": ".claude/skills",
        "agents_dir": ".claude/agents",
        "command_ext": ".md",
        "command_prefix": "dotnet-ai",
        "args_placeholder": "$ARGUMENTS",
    },
    "cursor": {
        "name": "Cursor",
        "commands_dir": None,  # Cursor combines commands into rules files
        "rules_dir": ".cursor/rules",
        "command_ext": ".mdc",
        "command_prefix": "dotnet-ai",
        "args_placeholder": None,
    },
    "copilot": {
        "name": "GitHub Copilot",
        "commands_dir": ".github/agents/commands",
        "rules_dir": None,
        "command_ext": ".agent.md",
        "command_prefix": "dotnet-ai",
        "args_placeholder": "$ARGUMENTS",
    },
    "codex": {
        "name": "Codex CLI",
        "commands_dir": None,
        "rules_dir": None,
        "command_ext": None,
        "command_prefix": "dotnet-ai",
        "args_placeholder": None,
        # T048: `agents_file` mapping deleted per research R13.
        # The root-AGENTS.md emitter (copy_commands_codex) is gone; Codex
        # plugin-native mode uses the plugin install path exclusively.
        # See data-model.md § 1b.
    },
}

# Feature 019 (plugin-native architecture): all four hosts are first-class.
# - claude/codex/cursor: plugin-native install (via each host's plugin model)
# - copilot: render-only into `.github/` (no plugin model per FR-004)
# v1-only single-host frozenset was replaced per T002 / plan.md commit 1.
SUPPORTED_AI_TOOLS: frozenset[str] = frozenset({"claude", "codex", "cursor", "copilot"})

# Feature 019 / T041a: the legacy AGENT_FRONTMATTER_MAP (per-tool universal
# frontmatter transformation table) is deleted per CHK027 / research R1.
# Per-host generation now goes through `dotnet_ai_kit.agent_generators`:
#   - generate_claude_agent()   (commit 4)
#   - generate_codex_agent()    (commit 5 — NotImplementedError per OOS-004)
#   - generate_cursor_agent()   (commit 6)
#   - generate_copilot_agent()  (commit 7)
# See `contracts/agent-source.contract.md` for the per-host allow-lists.


def get_agent_config(tool: str) -> dict[str, Any]:
    """Get the configuration dictionary for a specific AI tool.

    Args:
        tool: AI tool name (claude, cursor, copilot, codex).
              Case-insensitive.

    Returns:
        Configuration dictionary for the tool.

    Raises:
        ValueError: If the tool name is not recognized.
    """
    key = tool.lower()
    if key not in AGENT_CONFIG:
        supported = ", ".join(sorted(AGENT_CONFIG.keys()))
        raise ValueError(f"Unknown AI tool '{tool}'. Supported tools: {supported}")
    if key not in SUPPORTED_AI_TOOLS:
        logger.warning(
            "Tool '%s' is recognised but not fully supported in v1.0. "
            "Full support planned for v1.1.",
            tool,
        )
    return AGENT_CONFIG[key]


def detect_ai_tools(project_root: Path) -> list[str]:
    """Detect which supported AI tools are configured in a project.

    Only returns tools that are in SUPPORTED_AI_TOOLS (v1.0: claude only).

    Args:
        project_root: The root directory of the project.

    Returns:
        List of detected supported AI tool names (lowercase). May be empty.
    """
    detected: list[str] = []

    # Claude Code: .claude/ directory
    claude_dir = project_root / ".claude"
    if claude_dir.is_dir():
        detected.append("claude")

    return detected
