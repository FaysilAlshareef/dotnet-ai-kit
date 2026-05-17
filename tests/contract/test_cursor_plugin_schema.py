"""Contract test for `.cursor-plugin/plugin.json` (T013 / feature 019 commit 3).

Asserts that the Cursor plugin manifest validates against
schemas/cursor-plugin.schema.json. Per data-model.md § 1c, all field values
are scalar relative paths with `./` prefix. The agent-bearing field is
`agents` (NOT `subagents`) and the verified path is `./agents/`.

The `agents` field is CONDITIONAL on the A-005 spike fixture
(commit 6 T051). Until the spike outcome lands, commit 3 may emit the field
optimistically — commit 6 T061 removes it on fail-path per
cursor-fixture-decision.contract.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

REPO = Path(__file__).resolve().parent.parent.parent

PLUGIN_MANIFEST = REPO / ".cursor-plugin" / "plugin.json"
PLUGIN_SCHEMA = REPO / "schemas" / "cursor-plugin.schema.json"


@pytest.fixture(scope="module")
def manifest() -> dict:
    """Load the Cursor plugin manifest as JSON."""
    return json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def schema() -> dict:
    """Load the published Cursor plugin JSON Schema."""
    return json.loads(PLUGIN_SCHEMA.read_text(encoding="utf-8"))


def test_cursor_plugin_manifest_validates_against_schema(
    manifest: dict, schema: dict
) -> None:
    """`.cursor-plugin/plugin.json` MUST validate against the schema contract."""
    jsonschema.validate(instance=manifest, schema=schema)


def test_cursor_plugin_skills_is_scalar_path(manifest: dict) -> None:
    """Per data-model.md § 1c: `skills` MUST be `"./skills/"` (scalar)."""
    assert isinstance(manifest["skills"], str)
    assert manifest["skills"] == "./skills/"


def test_cursor_plugin_rules_is_scalar_path_to_cursor_dir(manifest: dict) -> None:
    """`rules` MUST be `"./rules/cursor/"` — the generated `.mdc` directory."""
    assert isinstance(manifest["rules"], str)
    assert manifest["rules"] == "./rules/cursor/"


def test_cursor_plugin_mcp_servers_is_scalar_path(manifest: dict) -> None:
    """`mcpServers` MUST be `"./.mcp.json"` (scalar)."""
    assert isinstance(manifest["mcpServers"], str)
    assert manifest["mcpServers"] == "./.mcp.json"


def test_cursor_plugin_hooks_is_scalar_path(manifest: dict) -> None:
    """`hooks` MUST be `"./hooks/hooks.json"` (scalar)."""
    assert isinstance(manifest["hooks"], str)
    assert manifest["hooks"] == "./hooks/hooks.json"


def test_cursor_plugin_has_no_subagents_field(manifest: dict) -> None:
    """The agent-bearing field is `agents`, NOT `subagents` per verified Cursor evidence."""
    assert "subagents" not in manifest, (
        "Cursor plugin must NOT use the `subagents` field — the documented field is `agents`"
    )


def test_cursor_plugin_agents_field_if_present_uses_verified_path(
    manifest: dict,
) -> None:
    """If `agents` is present, it MUST be `"./agents/"` (verified Cursor path)."""
    if "agents" in manifest:
        assert manifest["agents"] == "./agents/", (
            f"Cursor agents field, when present, must be the verified `./agents/` path; "
            f"got {manifest['agents']}"
        )


def test_cursor_plugin_name_is_dotnet_ai_kit(manifest: dict) -> None:
    """Plugin name MUST be `dotnet-ai-kit`."""
    assert manifest["name"] == "dotnet-ai-kit"
