# Cursor Setup Guide

**Mode**: Plugin-native · **Manifest**: `.cursor-plugin/plugin.json`

Cursor gets the full content set from dotnet-ai-kit as a native plugin:
27 commands, 124 skills, 16 rules in `.mdc` format, 14 sub-agents, MCP
integration, and 7 hooks — all served from the plugin install path.

---

## Install the plugin

```bash
# From the Cursor plugin marketplace
cursor plugin install FaysilAlshareef/dotnet-ai-kit
```

After install, skills, rules, commands, agents, hooks, and MCP config are
available in every Cursor session for any project. No `dotnet-ai init`
required just to use the plugin.

---

## Initialize your project

Run `dotnet-ai init` once per solution to write the per-solution config files:

```bash
# Initialize Cursor support
dotnet-ai init . --ai cursor

# Preview what would be written
dotnet-ai init . --ai cursor --dry-run

# Initialize all hosts at once
dotnet-ai init . --ai claude --ai codex --ai cursor --ai copilot
```

### What init writes (≤18 files)

| Path | Purpose |
|------|---------|
| `.dotnet-ai-kit/config.yml` | Company, repos, permissions, enabled hosts |
| `.dotnet-ai-kit/project.yml` | Detected architecture, .NET version |
| `.dotnet-ai-kit/manifest.json` | SHA-256 registry of managed files |
| `.dotnet-ai-kit/version.txt` | Installed CLI version |
| `.dotnet-ai-kit/mcp-state.yml` | MCP health outcome |

Commands, skills, agents, rules, and hooks are served from the plugin install
path — nothing is copied per-solution.

---

## What the plugin provides

### Rules — Cursor `.mdc` format

All 16 rules are served from `rules/cursor/` in Cursor's native `.mdc` format.
They are split into two groups per constitution v1.0.8:

**5 Universal rules** (`alwaysApply: true` — active in every session):

| Rule | Purpose |
|------|---------|
| `async-concurrency.mdc` | Async/await patterns, CancellationToken propagation |
| `coding-style.mdc` | Code formatting and patterns |
| `existing-projects.mdc` | Respects your existing codebase patterns |
| `security.mdc` | Auth, secrets, input validation |
| `tool-calls.mdc` | Sequential tool usage, verification |

**11 Path-scoped rules** (`globs:` from source `paths:` — load on demand):

| Rule | Activates when |
|------|----------------|
| `api-design.mdc` | API files touched |
| `architecture.mdc` | Architecture/project files |
| `configuration.mdc` | `appsettings*.json`, Options files |
| `data-access.mdc` | EF Core, migration files |
| `error-handling.mdc` | Exception/middleware files |
| `localization.mdc` | Resource files, culture handling |
| `multi-repo.mdc` | Cross-repo event contracts |
| `naming.mdc` | C# naming conventions, namespaces |
| `observability.mdc` | Logging, metrics, tracing files |
| `performance.mdc` | Query, caching files |
| `testing.mdc` | Test files |

### Sub-agents

14 specialist sub-agents are served from `agents/` (A-005 PASS branch).
Cursor loads them from the plugin install path — no per-project files needed.

### Commands, Skills, MCP

- **27 slash commands** from `commands/`
- **124 skills** from `skills/`
- **MCP**: `codebase-memory-mcp` via `.mcp.json`
- **7 hooks** via `hooks/hooks.json`

---

## MCP integration

`.mcp.json` registers `codebase-memory-mcp`:

```json
{
  "mcpServers": {
    "codebase-memory-mcp": {
      "command": "codebase-memory-mcp",
      "args": ["--project", "."],
      "transport": "stdio"
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

Plugin updates propagate automatically — the plugin install path is the
single source of truth. Reload the window to pick up changes:

1. Open the command palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
2. Run **Reload Window**

`dotnet-ai upgrade` is intentionally a no-op for Cursor (plugin-native host).

---

## Verify the install

```bash
dotnet-ai check          # validates plugin presence and project files
dotnet-ai check --json   # machine-readable
```

The check verifies that `.cursor-plugin/plugin.json` is reachable at the
expected Cursor plugin cache path.
