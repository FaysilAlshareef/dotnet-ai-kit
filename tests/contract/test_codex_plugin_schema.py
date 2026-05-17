"""Contract test for `.codex-plugin/plugin.json` (T012 / feature 019 commit 3).

Asserts that the Codex CLI plugin manifest validates against
schemas/codex-plugin.schema.json. Per data-model.md § 1b / Codex docs
developers.openai.com/codex/plugins/build:843-899, all manifest field values
are scalar relative-path strings with `./` prefix (NOT arrays/objects), and
the `agents`, `lspServers`, `monitors`, `settings`, `bin` fields MUST NOT
appear (per FR-002 / OOS-004).
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

REPO = Path(__file__).resolve().parent.parent.parent

PLUGIN_MANIFEST = REPO / ".codex-plugin" / "plugin.json"
PLUGIN_SCHEMA = REPO / "schemas" / "codex-plugin.schema.json"


@pytest.fixture(scope="module")
def manifest() -> dict:
    """Load the Codex plugin manifest as JSON."""
    return json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def schema() -> dict:
    """Load the published Codex plugin JSON Schema."""
    return json.loads(PLUGIN_SCHEMA.read_text(encoding="utf-8"))


def test_codex_plugin_manifest_validates_against_schema(
    manifest: dict, schema: dict
) -> None:
    """`.codex-plugin/plugin.json` MUST validate against the schema contract."""
    jsonschema.validate(instance=manifest, schema=schema)


def test_codex_plugin_skills_is_scalar_path(manifest: dict) -> None:
    """Per data-model.md § 1b: `skills` MUST be a scalar string `"./skills/"`."""
    assert isinstance(manifest["skills"], str), (
        f"Codex plugin `skills` must be a scalar string per docs:843-860, "
        f"got {type(manifest['skills']).__name__}"
    )
    assert manifest["skills"] == "./skills/"


def test_codex_plugin_mcp_servers_is_scalar_path(manifest: dict) -> None:
    """`mcpServers` MUST be a scalar path string `"./.mcp.json"`."""
    assert isinstance(manifest["mcpServers"], str)
    assert manifest["mcpServers"] == "./.mcp.json"


def test_codex_plugin_hooks_is_scalar_path(manifest: dict) -> None:
    """`hooks` MUST be a scalar path string `"./hooks/hooks.json"`."""
    assert isinstance(manifest["hooks"], str)
    assert manifest["hooks"] == "./hooks/hooks.json"


def test_codex_plugin_has_no_agents_field(manifest: dict) -> None:
    """Per OOS-004: native Codex agents are deferred to v1.1 — `agents` MUST be absent."""
    assert "agents" not in manifest, (
        "Codex plugin must NOT declare `agents` (OOS-004 — deferred to v1.1)"
    )


def test_codex_plugin_has_no_lsp_servers_field(manifest: dict) -> None:
    """Per FR-002: `lspServers` is not documented for Codex — MUST be absent."""
    assert "lspServers" not in manifest


def test_codex_plugin_has_no_undocumented_fields(manifest: dict) -> None:
    """Per FR-002 / schema `not.anyOf`: monitors / settings / bin MUST be absent."""
    for forbidden in ("monitors", "settings", "bin"):
        assert forbidden not in manifest, (
            f"Codex plugin must NOT declare `{forbidden}` (FR-002 / schema constraint)"
        )


def test_codex_plugin_name_is_dotnet_ai_kit(manifest: dict) -> None:
    """Plugin name MUST be `dotnet-ai-kit`."""
    assert manifest["name"] == "dotnet-ai-kit"
