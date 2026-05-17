"""T112 — `.mcp.json` no longer contains csharp-ls server (commit 12 / CHK012).

Asserts that:
1. `csharp-ls` server entry is REMOVED from `.mcp.json` (its diagnostics
   role now goes through the `csharp-lsp` plugin dependency / LSP primitive
   per FR-028 / commit 11).
2. `codebase-memory-mcp` server entry is RETAINED per final-merged-findings.md:195.

CI gate per CHK012: csharp-ls MUST stay until CHK009/010/011 are green in
the same PR's CI run. This test, combined with the smoke transcript test
(test_smoke_claude_lsp.py), is the gate check.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
MCP_JSON = REPO / ".mcp.json"


def test_mcp_json_no_longer_contains_csharp_ls() -> None:
    """`csharp-ls` MUST be absent from .mcp.json (LSP migration complete)."""
    data = json.loads(MCP_JSON.read_text(encoding="utf-8"))
    assert "csharp-ls" not in data.get("mcpServers", {}), (
        "csharp-ls is still in .mcp.json. Per CHK012, this should only be "
        "removed AFTER CHK009 + CHK010 + CHK011 are green in CI. "
        "If those checks haven't passed, this commit should be reverted."
    )


def test_mcp_json_retains_codebase_memory_mcp() -> None:
    """`codebase-memory-mcp` MUST be retained per final-merged-findings.md:195."""
    data = json.loads(MCP_JSON.read_text(encoding="utf-8"))
    assert "codebase-memory-mcp" in data.get("mcpServers", {}), (
        "codebase-memory-mcp removed from .mcp.json. This is NOT part of the "
        "LSP migration — only csharp-ls should be removed."
    )


def test_mcp_json_codebase_memory_mcp_min_version_pinned() -> None:
    """`codebase-memory-mcp` MUST keep its `dotnet_ai_kit_min_version` pin."""
    data = json.loads(MCP_JSON.read_text(encoding="utf-8"))
    entry = data["mcpServers"]["codebase-memory-mcp"]
    assert "dotnet_ai_kit_min_version" in entry
    assert entry["dotnet_ai_kit_min_version"] == "0.6.1"


def test_ci_gate_csharp_lsp_dep_present_before_csharp_ls_removal() -> None:
    """T113 CI gate: csharp-lsp dependency MUST be declared in plugin manifest.

    Per CHK012: csharp-ls removal from .mcp.json MUST NOT ship without the
    csharp-lsp plugin dependency being declared. This static check is the
    CI-side gate that fails the build if the LSP migration is incomplete.
    """
    plugin_manifest_path = REPO / ".claude-plugin" / "plugin.json"
    manifest = json.loads(plugin_manifest_path.read_text(encoding="utf-8"))

    deps = manifest.get("dependencies", [])
    assert "csharp-lsp" in deps, (
        "T113 CI gate FAILED: .mcp.json removed csharp-ls but .claude-plugin/"
        "plugin.json does NOT declare csharp-lsp in dependencies. Per CHK012, "
        "the LSP migration MUST be complete before this commit ships."
    )

    lsp_servers = manifest.get("lspServers", {})
    assert "csharp-lsp" in lsp_servers, (
        "T113 CI gate FAILED: csharp-lsp not declared in lspServers. "
        "Per CHK010, the dependency must be wired up before csharp-ls is "
        "removed from .mcp.json."
    )
