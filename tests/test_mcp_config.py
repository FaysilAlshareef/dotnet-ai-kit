"""T061 — FR-018 / FR-035: .mcp.json shape + version sidecar."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
MCP_JSON = REPO / ".mcp.json"
SCHEMA = REPO / "specs" / "018-fix-token-burn" / "contracts" / "mcp.schema.json"


def test_mcp_schema_validates() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    data = json.loads(MCP_JSON.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.validate(data, schema)


def test_csharp_ls_preserved() -> None:
    data = json.loads(MCP_JSON.read_text(encoding="utf-8"))
    assert "csharp-ls" in data["mcpServers"]


def test_codebase_memory_mcp_registered_with_min_version_sidecar() -> None:
    data = json.loads(MCP_JSON.read_text(encoding="utf-8"))
    entry = data["mcpServers"]["codebase-memory-mcp"]
    assert entry["dotnet_ai_kit_min_version"] == "0.6.1"


def test_deploy_preserves_existing_servers(tmp_path: Path) -> None:
    """T066a: merging into a project with pre-existing servers must not clobber."""
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
    assert "csharp-ls" in merged["mcpServers"]
