"""Contract test for `.claude-plugin/plugin.json`.

Validates the Claude Code plugin manifest against the updated schema
(scalar path strings for all component fields, per the official docs at
https://code.claude.com/docs/en/plugins-reference#component-path-fields).

Key invariants:
- skills, commands, agents, hooks, mcpServers, lspServers are all scalar
  relative-path strings (NOT arrays of individual files, NOT {"configFile":...}).
- The `./` prefix is required for all component paths.
- hooks must NOT use the custom `{"configFile": "..."}` wrapper format.
- mcpServers must NOT use the `{"configFile": "..."}` wrapper format.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

REPO = Path(__file__).resolve().parent.parent.parent

PLUGIN_MANIFEST = REPO / ".claude-plugin" / "plugin.json"
PLUGIN_SCHEMA = REPO / "schemas" / "claude-plugin.schema.json"


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(PLUGIN_SCHEMA.read_text(encoding="utf-8"))


def test_claude_plugin_manifest_validates_against_schema(manifest: dict, schema: dict) -> None:
    jsonschema.validate(instance=manifest, schema=schema)


def test_claude_plugin_name_is_dotnet_ai_kit(manifest: dict) -> None:
    assert manifest["name"] == "dotnet-ai-kit"


def test_claude_plugin_skills_is_scalar_path(manifest: dict) -> None:
    """skills MUST be a scalar directory path string, not an array of SKILL.md files.

    Claude Code expects './skills/' (a directory), not individual file paths.
    See https://code.claude.com/docs/en/plugins-reference#component-path-fields.
    """
    assert "skills" in manifest
    assert isinstance(manifest["skills"], str), (
        f"skills must be a scalar path string, got {type(manifest['skills']).__name__}. "
        "Arrays of individual SKILL.md paths are not valid."
    )
    assert manifest["skills"].startswith("./"), "skills path must use the './' prefix"


def test_claude_plugin_commands_is_scalar_path(manifest: dict) -> None:
    assert "commands" in manifest
    assert isinstance(manifest["commands"], str), (
        f"commands must be a scalar path string, got {type(manifest['commands']).__name__}"
    )
    assert manifest["commands"].startswith("./")


def test_claude_plugin_agents_is_array_of_file_paths(manifest: dict) -> None:
    """agents MUST be an array of individual .md file paths with './' prefix.

    Per https://code.claude.com/docs/en/plugins-reference#component-path-fields:
    - `agents` description: "Custom agent FILES" (not directories)
    - Example value: `["./custom/agents/reviewer.md"]`
    - A scalar directory path like './agents-claude/' is invalid — the validator
      expects file paths, not a directory.
    - Paths without the './' prefix are also rejected.

    skills/commands accept directory paths; agents does not — it's 'files' not 'directories'.
    """
    assert "agents" in manifest
    agents = manifest["agents"]
    assert isinstance(agents, list), (
        f"agents must be an array of './agents-claude/<name>.md' file paths, "
        f"got {type(agents).__name__}: {agents!r}. "
        "A scalar directory path is invalid for agents per the Claude Code docs."
    )
    assert len(agents) >= 1, "agents array must contain at least one entry"
    for entry in agents:
        assert isinstance(entry, str), f"agents entry must be a string, got {entry!r}"
        assert entry.startswith("./"), (
            f"agents entry must start with './', got {entry!r}. "
            "The './' prefix is required per the Claude Code plugin path rules."
        )
        assert entry.startswith("./agents-claude/"), (
            f"Claude plugin agents entry must be in agents-claude/, got {entry!r}"
        )
        assert entry.endswith(".md"), f"agents entry must be a .md file path, got {entry!r}"


def test_claude_plugin_hooks_is_string_not_configfile_object(manifest: dict) -> None:
    """hooks MUST be a scalar path string.

    The custom {'configFile': '...'} wrapper is NOT a documented Claude Code
    format and causes 'hooks: Invalid input' validation errors at install time.
    See https://code.claude.com/docs/en/plugins-reference#component-path-fields.
    """
    assert "hooks" in manifest
    hooks = manifest["hooks"]
    assert isinstance(hooks, str), (
        f"hooks must be a scalar path string like './hooks/hooks.json', "
        f"got {type(hooks).__name__}: {hooks!r}. "
        "Do not use the {'configFile': '...'} wrapper."
    )
    assert hooks.startswith("./")


def test_claude_plugin_mcp_servers_is_string_not_configfile_object(manifest: dict) -> None:
    """mcpServers MUST be a scalar path string.

    The custom {'configFile': '...'} wrapper is NOT a documented format and
    causes 'mcpServers: Invalid input' validation errors at install time.
    """
    assert "mcpServers" in manifest
    mcp = manifest["mcpServers"]
    assert isinstance(mcp, str), (
        f"mcpServers must be a scalar path string like './.mcp.json', "
        f"got {type(mcp).__name__}: {mcp!r}. "
        "Do not use the {'configFile': '...'} wrapper."
    )
    assert mcp.startswith("./")


def test_claude_plugin_lspservers_is_string(manifest: dict) -> None:
    """lspServers MUST be a scalar path string pointing to .lsp.json."""
    assert "lspServers" in manifest
    lsp = manifest["lspServers"]
    assert isinstance(lsp, str), (
        f"lspServers must be a scalar path string, got {type(lsp).__name__}: {lsp!r}"
    )
    assert lsp == "./.lsp.json", f"lspServers must be './.lsp.json', got {lsp!r}"
    lsp_path = REPO / ".lsp.json"
    assert lsp_path.is_file(), f".lsp.json declared but missing on disk ({lsp_path})"
    lsp_config = json.loads(lsp_path.read_text(encoding="utf-8"))
    for server_name, server_cfg in lsp_config.items():
        assert "command" in server_cfg, f".lsp.json server '{server_name}' missing 'command'"
        assert "extensionToLanguage" in server_cfg, (
            f".lsp.json server '{server_name}' missing 'extensionToLanguage'"
        )


def test_claude_plugin_no_configfile_wrappers(manifest: dict) -> None:
    """Ensure no field uses the {'configFile': '...'} anti-pattern.

    This wrapper was never documented by Anthropic and causes 'Invalid input'
    errors in the Claude Code plugin validator.
    """
    for field in ("hooks", "mcpServers", "lspServers", "skills", "commands", "agents"):
        value = manifest.get(field)
        if isinstance(value, dict):
            assert "configFile" not in value, (
                f"manifest.{field} uses undocumented {{'configFile': '...'}} wrapper. "
                f"Replace with a scalar path string."
            )


def test_claude_plugin_dependencies_does_not_contain_orphan_csharp_lsp(manifest: dict) -> None:
    """'csharp-lsp' is not a marketplace plugin name — must not be in dependencies."""
    deps = manifest.get("dependencies", [])
    if isinstance(deps, list):
        names = [d if isinstance(d, str) else d.get("name", "") for d in deps]
        assert "csharp-lsp" not in names, (
            "'csharp-lsp' is not a marketplace plugin; remove it from dependencies. "
            "LSP config lives under lspServers."
        )
