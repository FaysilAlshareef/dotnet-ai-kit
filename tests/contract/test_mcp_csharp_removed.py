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


def test_ci_gate_csharp_lsp_config_present_before_csharp_ls_removal() -> None:
    """T113 CI gate: .lsp.json must exist on disk with a valid C# server config.

    Claude Code auto-discovers .lsp.json from the plugin root — no manifest
    `lspServers` declaration is needed (and declaring the standard path causes
    duplicate errors). The gate therefore checks the FILE ON DISK, not the
    manifest field.

    Per https://code.claude.com/docs/en/plugins-reference, each server in
    .lsp.json must declare `command` + `extensionToLanguage`.
    """
    lsp_path = REPO / ".lsp.json"
    assert lsp_path.is_file(), (
        "T113 CI gate FAILED: .lsp.json is missing. Claude Code auto-discovers "
        "it for C# LSP diagnostics — the file must exist at the plugin root."
    )

    lsp_config = json.loads(lsp_path.read_text(encoding="utf-8"))
    assert lsp_config, ".lsp.json must declare at least one server"

    for server_name, cfg in lsp_config.items():
        assert isinstance(cfg, dict), f".lsp.json server '{server_name}' must be an object"
        assert "command" in cfg, f".lsp.json server '{server_name}' missing 'command'"
        assert "extensionToLanguage" in cfg, (
            f".lsp.json server '{server_name}' missing 'extensionToLanguage'"
        )

    has_csharp = any(
        "csharp" in str(name).lower()
        or any(ext.endswith(".cs") for ext in (cfg.get("extensionToLanguage") or {}).keys())
        for name, cfg in lsp_config.items()
        if isinstance(cfg, dict)
    )
    assert has_csharp, (
        f".lsp.json does not declare a C# server (no 'csharp' key, no '.cs' extension). "
        f"Got: {list(lsp_config.keys())}"
    )

    # Orphan check: `csharp-lsp` must not appear in manifest dependencies.
    plugin_manifest_path = REPO / ".claude-plugin" / "plugin.json"
    manifest = json.loads(plugin_manifest_path.read_text(encoding="utf-8"))
    deps = manifest.get("dependencies", [])
    if isinstance(deps, list):
        dep_names = [d if isinstance(d, str) else d.get("name", "") for d in deps]
        assert "csharp-lsp" not in dep_names, (
            "`csharp-lsp` is not a marketplace plugin; remove from `dependencies`. "
            "LSP config belongs in .lsp.json (auto-discovered)."
        )
