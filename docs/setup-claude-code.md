# Claude Code Setup Guide

**Mode**: Plugin-native · **Manifest**: `.claude-plugin/plugin.json`

Claude Code is the primary host for dotnet-ai-kit with full feature parity: all
27 commands, 124 skills, 13 agents, 16 rules, 7 hooks, and MCP integration.
Nothing is copied per-solution — assets are served from the plugin install path.

---

## Install the plugin

```bash
# From the Claude Code marketplace
/plugin marketplace add FaysilAlshareef/dotnet-ai-kit
/plugin install dotnet-ai-kit
```

After install, all 27 commands, 124 skills, 13 agents, and 7 hooks are live
immediately. No `dotnet-ai init` required just to use the plugin.

---

## Initialize your project

Run `dotnet-ai init` once per solution to write the per-solution config files
and wire up MCP + permissions:

```bash
# Auto-detect architecture and initialize
dotnet-ai init . --ai claude

# With a permission level applied in the same step
dotnet-ai init . --ai claude --permissions standard

# Preview every file that would be written
dotnet-ai init . --ai claude --dry-run

# Skip auto-install of csharp-ls and codebase-memory-mcp (offline / restricted)
dotnet-ai init . --ai claude --no-install-deps
```

### What init writes (≤18 files)

| Path | Purpose |
|------|---------|
| `.dotnet-ai-kit/config.yml` | Company, repos, permissions, command style |
| `.dotnet-ai-kit/project.yml` | Detected architecture, .NET version, detected paths |
| `.dotnet-ai-kit/manifest.json` | SHA-256 registry of every managed file |
| `.dotnet-ai-kit/version.txt` | Installed CLI version (used by upgrade) |
| `.dotnet-ai-kit/mcp-state.yml` | MCP health outcome (accepted / below-minimum / unavailable) |
| `.dotnet-ai-kit/.gitignore` | Ignores backups and scratch files |
| `.claude/settings.json` | Permission rules for the selected level |

Commands, skills, agents, and rules are **not** copied — they are served
from the plugin install path on every session start.

---

## Dependencies

`dotnet-ai init` auto-installs both when missing. Pass `--no-install-deps` to skip.

### csharp-ls

C# language server for semantic symbol and reference navigation. Declared as a
`csharp-lsp` plugin dependency in `.claude-plugin/plugin.json`.

```bash
# Manual install if auto-install is skipped
dotnet tool install -g csharp-ls
```

### codebase-memory-mcp ≥ 0.6.1

Provides lazy project-graph queries instead of broad file reads. Registered in
`.mcp.json`. MCP health is checked during init and stored in
`.dotnet-ai-kit/mcp-state.yml`.

```bash
# Manual install
pip install "codebase-memory-mcp>=0.6.1"
```

Without `codebase-memory-mcp`, project-graph questions fall back to
`csharp-ls + grep/read`. Without `csharp-ls`, the AI uses grep-based analysis
(works, but burns more context tokens on large codebases).

---

## Permission levels

Set during init (`--permissions`) or any time via `configure`:

```bash
dotnet-ai configure --permissions standard
dotnet-ai configure --permissions full --global   # apply to all repos
dotnet-ai configure --permissions standard --dry-run  # preview
```

| Level | Mode | What it allows |
|-------|------|----------------|
| **minimal** | Default (prompts most) | `dotnet build/test/restore`, `cd`, `ls` |
| **standard** | Default + allow-list | + `git`, `gh`, `grep`, `find`, `python`, `powershell` |
| **full** | `bypassPermissions` | All dev commands — no confirmation prompts |

`full` shows a one-time warning because it enables `bypassPermissions`.
The existing `.claude/settings.json` is backed up to `.dotnet-ai-kit/backups/`
before every permission change.

---

## Architecture detection

After init, run `/dai.detect` inside Claude Code to trigger AI-powered
architecture detection. The result is saved to `.dotnet-ai-kit/project.yml`
and an architecture-specific profile becomes active for every subsequent session.

```bash
# Or via CLI
dotnet-ai status --verbose   # shows current profile path and hook model
```

The PreToolUse enforcement hook in `.claude/settings.json` reads `project.yml`
at every Write/Edit call and enforces the detected architecture pattern before
any code is written.

---

## Updating the plugin

Plugin updates propagate automatically — there is nothing to copy.

```bash
# Reload within a running session (no restart needed)
/reload-plugins
```

`dotnet-ai upgrade` is intentionally a no-op for Claude Code (plugin-native host).
The command exits cleanly with a message explaining this. To re-render Copilot
files on a mixed-host project, use `dotnet-ai upgrade --copilot`.

---

## Verify the install

```bash
dotnet-ai check          # validates plugin install, csharp-ls, project.yml, manifest
dotnet-ai check --json   # machine-readable output for CI
```

Exit codes identify the failing check class (0 = pass, 10–16 = specific failures,
99 = unexpected error). Run `dotnet-ai check --verbose` for the profile path and
hook model/timeout after the AI tools table.

---

## Quick command reference

```bash
# Inside Claude Code — most common starting points
/dai.do "Add order management with tracking"   # full 9-phase lifecycle
/dai.detect                                     # (re-)detect architecture
/dai.learn                                      # generate project constitution
/dai.status                                     # see feature progress
```

All 27 commands support `--dry-run` to preview and `--verbose` for step-by-step output.
