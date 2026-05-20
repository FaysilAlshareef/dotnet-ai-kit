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
    """T113 CI gate (round-2 review correction): the C# LSP migration MUST
    be wired via the documented `lspServers` field, not via a `dependencies`
    entry.

    Per https://code.claude.com/docs/en/plugins-reference, `lspServers` is
    `string|array|object`. The shipped form is the scalar path
    `"./.lsp.json"` which references an external config file declaring
    `csharp-ls` with the required `command` + `extensionToLanguage` fields.

    The previous gate at this location asserted `csharp-lsp` was in
    `dependencies` — that was incorrect per the docs (`dependencies`
    declares marketplace plugin requirements, not LSP config). The
    `dependencies` field may or may not be present; if present, it MUST NOT
    contain an orphan `csharp-lsp` entry.
    """
    plugin_manifest_path = REPO / ".claude-plugin" / "plugin.json"
    manifest = json.loads(plugin_manifest_path.read_text(encoding="utf-8"))

    # The migration gate: lspServers MUST be wired up.
    lsp = manifest.get("lspServers")
    assert lsp is not None, (
        "T113 CI gate FAILED: .mcp.json removed csharp-ls but .claude-plugin/"
        "plugin.json does NOT declare `lspServers`. Per the docs, this is "
        "how Claude Code's LSP loader picks up the C# diagnostics integration. "
        'Add `"lspServers": "./.lsp.json"` to the manifest.'
    )

    # When `lspServers` is a path string, the referenced file MUST declare
    # at least one server with command + extensionToLanguage.
    if isinstance(lsp, str):
        # `lsp` is `./.lsp.json` style — strip the `./` prefix, not individual chars.
        lsp_rel = lsp[2:] if lsp.startswith("./") else lsp
        lsp_path = REPO / lsp_rel
        assert lsp_path.is_file(), (
            f"lspServers points at {lsp} but no such file exists ({lsp_path})."
        )
        lsp_config = json.loads(lsp_path.read_text(encoding="utf-8"))
        assert lsp_config, f"{lsp_path} declares no servers"
        # At least one server should drive csharp diagnostics.
        has_csharp = any(
            "csharp" in str(name).lower()
            or any(ext.endswith(".cs") for ext in (cfg.get("extensionToLanguage") or {}).keys())
            for name, cfg in lsp_config.items()
            if isinstance(cfg, dict)
        )
        assert has_csharp, (
            f"{lsp_path} does not declare a C# server (no `csharp` key and no "
            f"`.cs` extension mapping). Got: {list(lsp_config.keys())}"
        )

    # Orphan check: `csharp-lsp` is not a real marketplace plugin name, so
    # it must not appear in `dependencies` (round-2 review correction).
    deps = manifest.get("dependencies", [])
    if isinstance(deps, list):
        dep_names = [d if isinstance(d, str) else d.get("name", "") for d in deps]
        assert "csharp-lsp" not in dep_names, (
            "`csharp-lsp` is not a marketplace plugin; it must not appear in "
            "`dependencies`. LSP wiring belongs under `lspServers`."
        )
