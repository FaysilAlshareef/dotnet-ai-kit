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


def test_claude_plugin_hooks_not_declared_for_standard_path(manifest: dict) -> None:
    """hooks/hooks.json MUST NOT be declared in the manifest.

    Claude Code auto-discovers hooks/hooks.json from the plugin root.
    Declaring './hooks/hooks.json' in the manifest causes:
      'Duplicate hooks file detected: ./hooks/hooks.json resolves to
       already-loaded file. The standard hooks/hooks.json is loaded
       automatically, so manifest.hooks should only reference additional
       hook files.'

    The manifest hooks field is only for NON-default paths (e.g. a second
    hooks file at './config/extra-hooks.json').
    """
    hooks = manifest.get("hooks")
    assert hooks is None, (
        f"manifest.hooks must be absent (auto-discovered). "
        f"Got {hooks!r}. Remove it — Claude Code loads hooks/hooks.json automatically."
    )


def test_claude_plugin_mcp_servers_not_declared_for_standard_path(manifest: dict) -> None:
    """mcpServers (.mcp.json) MUST NOT be declared in the manifest.

    Claude Code auto-discovers .mcp.json from the plugin root. Declaring
    './.mcp.json' is redundant and may cause duplicate-load errors.
    The manifest mcpServers field is only for non-default paths.
    """
    mcp = manifest.get("mcpServers")
    assert mcp is None, (
        f"manifest.mcpServers must be absent (auto-discovered). "
        f"Got {mcp!r}. Remove it — Claude Code loads .mcp.json automatically."
    )


def test_lsp_json_exists_on_disk_with_correct_structure() -> None:
    """.lsp.json must exist on disk and declare at least one server.

    Claude Code auto-discovers .lsp.json from the plugin root — no manifest
    declaration needed. This test verifies the file is present and structurally
    valid (each server must have 'command' + 'extensionToLanguage').
    """
    lsp_path = REPO / ".lsp.json"
    assert lsp_path.is_file(), (
        ".lsp.json is missing. Claude Code auto-discovers it for LSP support."
    )
    lsp_config = json.loads(lsp_path.read_text(encoding="utf-8"))
    assert lsp_config, ".lsp.json must declare at least one server"
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
    for field in ("skills", "commands", "agents"):
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
