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


def test_claude_plugin_lspservers_points_to_external_file(manifest: dict) -> None:
    """B-CX-4 (round-2 review, corrected): per the Anthropic docs at
    https://code.claude.com/docs/en/plugins-reference, `lspServers` is
    `string|array|object`. The recommended form is a scalar path to an
    external `.lsp.json` file at the plugin root.

    The PREVIOUS shipped shape was an inline object with a `_note`-only
    entry (`{"csharp-lsp": {"_note": "..."}}`) — structurally invalid
    because the docs require `command` + `extensionToLanguage` for every
    inline server entry. This was identified during round-2 cross-review.

    The FIX uses the scalar-path form: `"lspServers": "./.lsp.json"`. The
    referenced file declares the actual server config with both required
    fields. See `.lsp.json` at the repo root."""
    assert "lspServers" in manifest, (
        "lspServers MUST be declared. Per the Anthropic docs, this is "
        "how Claude Code's LSP loader discovers C# diagnostics integration."
    )
    lsp = manifest["lspServers"]
    assert isinstance(lsp, str), (
        f"lspServers MUST be a scalar path per the round-2 contract; "
        f"inline objects must declare command + extensionToLanguage. "
        f"Got: {type(lsp).__name__} = {lsp!r}"
    )
    assert lsp == "./.lsp.json", (
        f"lspServers MUST point to ./.lsp.json (the canonical location). Got: {lsp!r}"
    )
    # The referenced file MUST exist on disk and have the proper shape.
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent.parent
    lsp_path = repo_root / ".lsp.json"
    assert lsp_path.is_file(), (
        f"`{lsp}` is declared in the manifest but the file is missing on disk "
        f"({lsp_path}). Wheel-build will fail at runtime."
    )
    import json as _json

    lsp_config = _json.loads(lsp_path.read_text(encoding="utf-8"))
    assert isinstance(lsp_config, dict) and lsp_config, (
        f".lsp.json must declare at least one server config. Got: {lsp_config!r}"
    )
    for server_name, server_cfg in lsp_config.items():
        assert "command" in server_cfg, (
            f".lsp.json server '{server_name}' missing required `command` field"
        )
        assert "extensionToLanguage" in server_cfg, (
            f".lsp.json server '{server_name}' missing required `extensionToLanguage` field"
        )


def test_claude_plugin_dependencies_does_not_contain_orphan_csharp_lsp(manifest: dict) -> None:
    """Round-2 review correction: the previous `dependencies: ["csharp-lsp"]`
    entry was a misread of the docs.

    Per https://code.claude.com/docs/en/plugins-reference, the `dependencies`
    array declares **other plugins** this plugin requires (with optional
    semver constraints). No marketplace plugin literally named `csharp-lsp`
    exists; this entry was effectively dead code.

    LSP server configuration lives under `lspServers` (verified by
    `test_claude_plugin_lspservers_points_to_external_file` above), NOT
    under `dependencies`.

    If a real plugin dependency is added later (e.g., a future
    `csharp-lsp-marketplace-plugin`), update this test to allow it — but
    do NOT re-introduce the dead `csharp-lsp` string entry."""
    deps = manifest.get("dependencies", [])
    # Allow `dependencies` to be absent OR present but empty/non-orphan
    if isinstance(deps, list):
        names = [d if isinstance(d, str) else d.get("name", "") for d in deps]
        assert "csharp-lsp" not in names, (
            "`csharp-lsp` is not a marketplace plugin; it must not appear in "
            "`dependencies`. LSP wiring lives under `lspServers` per the docs."
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
