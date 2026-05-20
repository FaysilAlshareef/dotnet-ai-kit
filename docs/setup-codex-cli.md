# Codex CLI Setup Guide

**Mode**: Plugin-native + per-project subagents · **Manifest**: `.codex-plugin/plugin.json`

Codex CLI uses dotnet-ai-kit as a native plugin for skills, MCP, and hooks.
In addition, `dotnet-ai init --ai codex` renders 14 specialist subagents
directly into your project as `.codex/agents/*.toml` files.

---

## Install the plugin

Install via the Codex CLI plugin system (marketplace or local developer symlink):

```bash
# Marketplace install
codex plugin install FaysilAlshareef/dotnet-ai-kit

# Or developer symlink (for contributors)
ln -s /path/to/dotnet-ai-kit ~/.codex/plugins/local/dotnet-ai-kit
```

The plugin serves **124 skills**, **MCP integration** (`codebase-memory-mcp`),
and **7 hooks** from the plugin install path. Commands and plugin-bundled agents
are a v1.1 item — per-project subagents (below) cover the agent surface for v1.0.

---

## Initialize your project

```bash
# Initialize Codex CLI support
dotnet-ai init . --ai codex

# Preview what would be written
dotnet-ai init . --ai codex --dry-run

# Initialize all hosts at once
dotnet-ai init . --ai claude --ai codex --ai cursor --ai copilot
```

### What init writes

| Path | Purpose |
|------|---------|
| `.dotnet-ai-kit/config.yml` | Company, repos, permissions, enabled hosts |
| `.dotnet-ai-kit/project.yml` | Detected architecture, .NET version |
| `.dotnet-ai-kit/manifest.json` | SHA-256 registry of managed files |
| `.dotnet-ai-kit/version.txt` | Installed CLI version |
| `.dotnet-ai-kit/mcp-state.yml` | MCP health outcome |
| `.codex/agents/*.toml` | 14 specialist subagent files (see below) |

---

## Per-project subagents

`dotnet-ai init --ai codex` renders 14 `.toml` subagent files into
`.codex/agents/`. Codex loads them from the project scope automatically:

| File | Specialist |
|------|-----------|
| `dotnet-architect.toml` | Overall .NET architecture decisions |
| `api-designer.toml` | REST, Minimal APIs, gRPC |
| `ef-specialist.toml` | EF Core, migrations, queries |
| `command-architect.toml` | Event-sourced write side |
| `query-architect.toml` | SQL Server read models |
| `cosmos-architect.toml` | Cosmos DB read models |
| `gateway-architect.toml` | API Gateway, routing |
| `processor-architect.toml` | Background processing, Service Bus |
| `controlpanel-architect.toml` | Blazor WASM |
| `test-engineer.toml` | Unit + integration tests |
| `reviewer.toml` | Code review, quality |
| `devops-engineer.toml` | Docker, Azure, CI/CD |
| `docs-engineer.toml` | API docs, standards |
| `dotnet-ai-architect.toml` | dotnet-ai-kit fixture (A-005 spike) |

### Conflict policy

If a `.toml` file already exists, **the existing file is preserved** — user
customizations win. Delete the file and re-run `dotnet-ai init . --ai codex`
to regenerate a specific subagent.

```bash
# Regenerate a single subagent (example)
rm .codex/agents/api-designer.toml
dotnet-ai init . --ai codex
```

Subagents are tracked in `.dotnet-ai-kit/manifest.json` with
`host_owner: "codex"` so `dotnet-ai check` and `dotnet-ai migrate` can
manage them.

---

## MCP integration

`.mcp.json` at the repo root registers `codebase-memory-mcp`:

```json
{
  "mcpServers": {
    "codebase-memory-mcp": {
      "command": "codebase-memory-mcp",
      "args": ["--project", "."],
      "transport": "stdio",
      "dotnet_ai_kit_min_version": "0.6.1"
    }
  }
}
```

Install if missing:

```bash
pip install "codebase-memory-mcp>=0.6.1"
```

---

## Updating the plugin

Plugin-level assets (skills, MCP config, hooks) update automatically when
you update the plugin — restart the Codex session to pick up changes.

Per-project subagents (`.codex/agents/*.toml`) do NOT auto-update because
user customizations are preserved. To regenerate all subagents:

```bash
# Delete managed subagents and re-run init
dotnet-ai migrate --host codex    # moves managed files to backup
dotnet-ai init . --ai codex       # re-renders fresh copies
```

---

## Verify the install

```bash
dotnet-ai check          # validates plugin presence and project files
dotnet-ai check --json   # machine-readable
```

The check validates that `.codex-plugin/plugin.json` is reachable at the
expected Codex plugin cache path:
- Marketplace: `~/.codex/plugins/cache/<marketplace>/dotnet-ai-kit/<version>/`
- Developer local: `~/.codex/plugins/local/dotnet-ai-kit/`

---

## Known limitations (v1.0)

- **Plugin-bundled subagents** are a v1.1 item. The Codex plugin manifest
  does not yet document a top-level `agents` field, so subagents are
  distributed per-project via `init` rather than through the plugin.
- `dotnet-ai render --host codex` (runtime skill/rule rendering for Codex
  shape) is deferred to v1.1.
