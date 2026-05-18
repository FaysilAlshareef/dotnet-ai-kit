"""Contract test for `.claude-plugin/plugin.json` (T011 / feature 019 commit 3).

Asserts that the Claude Code plugin manifest validates against the
schemas/claude-plugin.schema.json contract. This test ships in commit 3
and is extended by commit 11's T111 to specifically check `csharp-lsp` is
present in `dependencies` after the LSP migration step lands.

The schema is strict (additionalProperties: false). Any future field
addition requires updating both the contract schema and this test.
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
    """Load the Claude plugin manifest as JSON."""
    return json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def schema() -> dict:
    """Load the published Claude plugin JSON Schema."""
    return json.loads(PLUGIN_SCHEMA.read_text(encoding="utf-8"))


def test_claude_plugin_manifest_validates_against_schema(manifest: dict, schema: dict) -> None:
    """`.claude-plugin/plugin.json` MUST validate against the schema contract."""
    jsonschema.validate(instance=manifest, schema=schema)


def test_claude_plugin_includes_agents_field(manifest: dict) -> None:
    """Per data-model.md § 1a / FR-026: `agents` array MUST be present."""
    assert "agents" in manifest, (
        "Claude plugin manifest missing `agents` field (feature 019 / FR-026)"
    )
    assert isinstance(manifest["agents"], list)
    assert len(manifest["agents"]) >= 1, "agents array must contain at least one entry"


def test_claude_plugin_agents_point_to_agents_claude_dir(manifest: dict) -> None:
    """Each `agents` entry MUST reference an `agents-claude/*.md` path per data-model § 1a."""
    for entry in manifest["agents"]:
        assert entry.startswith("agents-claude/"), (
            f"Claude plugin agents entry must point to agents-claude/, got: {entry}"
        )
        assert entry.endswith(".md"), f"Claude plugin agents entry must be .md, got: {entry}"


def test_claude_plugin_has_lsp_servers_field(manifest: dict) -> None:
    """Per data-model.md § 1a / FR-028: `lspServers` MUST be declared (commit 3)."""
    assert "lspServers" in manifest


def test_claude_plugin_has_csharp_lsp_dependency(manifest: dict) -> None:
    """Per data-model.md § 1a / commit 11: `dependencies` MUST contain csharp-lsp.

    Declared from commit 3 (forward declaration). The LSP runtime wiring
    lands in commit 11.
    """
    assert "dependencies" in manifest
    assert "csharp-lsp" in manifest["dependencies"], (
        f"csharp-lsp not declared in dependencies (commit 11 prerequisite): "
        f"{manifest['dependencies']}"
    )


def test_claude_plugin_mcp_servers_references_mcp_json(manifest: dict) -> None:
    """`.claude-plugin/plugin.json mcpServers.configFile` MUST reference `.mcp.json`."""
    assert manifest["mcpServers"]["configFile"] == ".mcp.json"


def test_claude_plugin_hooks_references_hooks_json(manifest: dict) -> None:
    """`.claude-plugin/plugin.json hooks.configFile` MUST reference `hooks/hooks.json`."""
    assert manifest["hooks"]["configFile"] == "hooks/hooks.json"


def test_claude_plugin_name_is_dotnet_ai_kit(manifest: dict) -> None:
    """Plugin name MUST be `dotnet-ai-kit` per schema const constraint."""
    assert manifest["name"] == "dotnet-ai-kit"
