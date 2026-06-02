# Contract: MCP / LSP Projection

Covers FR-015..FR-018. Verifiable by `Acceptance.Tests` (+ `generate --check` drift, `Hosts.Tests` golden).

## C-ML-1 — MCP config projected per host from one descriptor

> **Open decision D-MCP**: the *payload* is pending — the root `.mcp.json` (`codebase-memory-mcp`) is the kit's dev config and must not be projected to users. This contract governs the projection *mechanism*; the descriptor source is resolved by D-MCP (target-facing `artifacts/` descriptor / placeholder / descope to 029).

- **Given** the single MCP descriptor (the D-MCP-resolved target-facing source),
- **Then** each supported host receives its MCP configuration in the native shape from that one source:
  - Claude: `build/claude/.mcp.json` (`mcpServers`)
  - Codex: `[mcp_servers]` in its config form
  - Cursor: `mcpServers` (cursor plugin manifest / `.cursor/mcp.json`)
  - Copilot: its MCP config form
- **And** the server identity (command/args/transport) is preserved consistently across hosts (same descriptor → equivalent config).

## C-ML-2 — LSP projected where supported; unsupported is explicit

- **Given** the single LSP descriptor (root `.lsp.json`: `csharp` → `csharp-ls`),
- **Then** `build/claude/.lsp.json` is emitted (GA) and Copilot receives LSP config (Preview),
- **And** Codex/Cursor receive an **explicit unsupported marker** (documented absence), not a silent omission (FR-016/FR-008).

## C-ML-3 — Agent navigation wiring

- **Then** `reviewer`, `dotnet-architect`, and `ef-specialist` agent bodies instruct preferring symbol-precise navigation (`goToDefinition`/`findReferences`) over text search when LSP is available (FR-017) — assertable by a content check on the projected agent files.

## C-ML-4 — Determinism

- **Then** all projected MCP/LSP files are byte-stable: re-running `generate` yields identical bytes and `generate --check` is drift-clean (FR-018/FR-020).

## Tests

- `McpLspProjectionTests`: C-ML-1 (per-host MCP presence + server identity), C-ML-2 (LSP present for Claude/Copilot; explicit marker for Codex/Cursor), C-ML-3 (agent nav content), C-ML-4 (determinism — project twice, compare).
- `Hosts.Tests` golden + `generate --check`: new MCP/LSP files re-accepted and drift-clean.
