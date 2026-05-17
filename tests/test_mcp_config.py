"""T061 — FR-018 / FR-035: .mcp.json shape + version sidecar."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
MCP_JSON = REPO / ".mcp.json"
SCHEMA = REPO / "specs" / "018-fix-token-burn" / "contracts" / "mcp.schema.json"


def test_mcp_schema_validates() -> None:
    """Per feature 018's MCP schema, the current .mcp.json validates.

    Feature 019 / commit 12 removed csharp-ls; the schema still validates
    the remaining entries (codebase-memory-mcp).
    """
    jsonschema = pytest.importorskip("jsonschema")
    data = json.loads(MCP_JSON.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    # The feature-018 schema requires csharp-ls; that requirement is dropped
    # in feature 019 / commit 12 per CHK012. Drop the strict requirement here.
    if "required" in schema:
        schema["required"] = [r for r in schema["required"] if r != "csharp-ls"]
    if "properties" in schema and "mcpServers" in schema["properties"]:
        ms_props = schema["properties"]["mcpServers"]
        if "required" in ms_props:
            ms_props["required"] = [r for r in ms_props["required"] if r != "csharp-ls"]
    jsonschema.validate(data, schema)


def test_csharp_ls_removed_per_feature_019_commit_12() -> None:
    """Feature 019 / commit 12 / CHK012: csharp-ls is REMOVED from .mcp.json.

    Replaces the legacy `test_csharp_ls_preserved` which asserted the
    opposite. The LSP migration now goes through the csharp-lsp plugin
    dependency per FR-028.
    """
    data = json.loads(MCP_JSON.read_text(encoding="utf-8"))
    assert "csharp-ls" not in data["mcpServers"]


def test_codebase_memory_mcp_registered_with_min_version_sidecar() -> None:
    data = json.loads(MCP_JSON.read_text(encoding="utf-8"))
    entry = data["mcpServers"]["codebase-memory-mcp"]
    assert entry["dotnet_ai_kit_min_version"] == "0.6.1"


def test_deploy_preserves_existing_servers(tmp_path: Path) -> None:
    """T066a: merging into a project with pre-existing servers must not clobber.

    Feature 019 / commit 12: after csharp-ls removal, merge MUST preserve
    user-added servers AND the remaining plugin entry (codebase-memory-mcp).
    """
    from dotnet_ai_kit.copier import merge_mcp_config

    project_mcp = tmp_path / ".mcp.json"
    project_mcp.write_text(
        json.dumps({"mcpServers": {"my-custom": {"command": "my-mcp", "transport": "stdio"}}}),
        encoding="utf-8",
    )

    merge_mcp_config(tmp_path, MCP_JSON)

    merged = json.loads(project_mcp.read_text(encoding="utf-8"))
    assert "my-custom" in merged["mcpServers"]
    assert "codebase-memory-mcp" in merged["mcpServers"]
    # csharp-ls is REMOVED per commit 12 — must not reappear via merge
    assert "csharp-ls" not in merged["mcpServers"]
