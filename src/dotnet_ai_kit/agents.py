"""AGENT_CONFIG for AI tool integration.

Maps AI tool names to their configuration (directory paths, file extensions,
command prefixes) and provides detection and lookup utilities.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

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
        "agents_file": "AGENTS.md",
    },
}

# v1.0: Only Claude Code is fully supported.
# Cursor, Copilot, Codex planned for v1.1.
SUPPORTED_AI_TOOLS: frozenset[str] = frozenset({"claude"})

# Per-tool transformation mapping for universal agent frontmatter.
# Agent source files use tool-agnostic fields (role, expertise, complexity,
# max_iterations). This map converts them to tool-specific frontmatter
# during deployment via copy_agents().
AGENT_FRONTMATTER_MAP: dict[str, dict[str, Any]] = {
    "claude": {
        "role": {
            "advisory": {"disallowedTools": ["Write", "Edit"]},
            "implementation": {},
            "testing": {},
            "review": {"disallowedTools": ["Write", "Edit"]},
        },
        "expertise": lambda skills: {"skills": skills},
        "complexity": {
            "high": {"effort": "high", "model": "opus"},
            "medium": {"effort": "medium", "model": "sonnet"},
            "low": {"effort": "low", "model": "haiku"},
        },
        "max_iterations": lambda n: {"maxTurns": n},
    },
    # v1.0.1: "cursor": { ... }
    # v1.0.1: "copilot": { ... }
}


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
