# Research: Fix Permission System

**Feature**: 009-fix-permission-bypass
**Date**: 2026-03-25

## R1: Claude Code Settings File Format

**Decision**: Use the standard `settings.json` schema with `permissions.allow` array and `permissions.defaultMode` field.

**Rationale**: Claude Code reads `.claude/settings.json` (project-level, committed) and `~/.claude/settings.json` (user-level, global). The schema is documented at `https://json.schemastore.org/claude-code-settings.json`. Project-level settings take precedence over global.

**Key findings**:
- Permission allow rules use the format: `Bash(command *)` for bash commands with glob wildcards
- `Bash(ls *)` requires at least one argument — bare `ls` won't match. Use `Bash(ls)` AND `Bash(ls *)` for full coverage
- Built-in tools (Read, Edit, Write, Glob, Grep) do NOT need allow rules — they are controlled by permission mode
- Permission modes: `default`, `acceptEdits`, `bypassPermissions`, `dontAsk`, `plan`, `auto`
- `bypassPermissions` skips ALL prompts (equivalent to `--dangerously-skip-permissions`)
- Setting `"permissions": {"defaultMode": "bypassPermissions"}` in settings.json activates bypass mode

**Alternatives considered**:
- `settings.local.json` (gitignored): Rejected by user — permissions must be committed and shared
- Custom schema fields: Rejected — would be ignored by Claude Code; use standard schema only

## R2: Permission Merge Strategy

**Decision**: Track managed entries in `config.yml` under a `managed_permissions` list. On level change, remove old managed entries from settings.json and add new ones.

**Rationale**: This avoids polluting the Claude Code settings file with non-standard metadata. The tool already reads/writes `config.yml` during init/configure, so adding a field is natural.

**Merge algorithm**:
1. Load current `.claude/settings.json` (or create empty structure)
2. Load `managed_permissions` list from `config.yml` (entries the tool previously wrote)
3. Compute `user_entries = current_allow_list - managed_permissions`
4. Load new permission template for selected level
5. Write `new_allow_list = template_entries + user_entries` (deduplicated)
6. Save `managed_permissions = template_entries` to `config.yml`
7. If level is "full": set `permissions.defaultMode = "bypassPermissions"`
8. If level is NOT "full": remove `permissions.defaultMode` (or set to `"default"`)
9. Write updated settings.json

**Alternatives considered**:
- `_managedBy` key in settings.json: Non-standard field, Claude Code might ignore or warn
- Full array replacement: Destroys user-added custom entries
- Comment markers in JSON: JSON doesn't support comments

## R3: Expanded Permission Template (Full Level)

**Decision**: Expand `permissions-full.json` to ~80+ entries covering all common development commands, plus set `defaultMode: bypassPermissions`.

**Rationale**: Even with bypass mode, having a comprehensive allow-list serves as documentation and provides fallback if a user later downgrades from full to standard.

**Command categories to add**:
- **File system**: ls, dir, find, grep, cat, head, tail, wc, cp, mv, rm, mkdir, echo, pwd, touch, chmod, stat, file, tree, less, more
- **.NET**: dotnet (all subcommands: build, test, run, publish, format, new, ef, restore, watch, clean, add, remove, list, tool, nuget, pack, migrate)
- **Version control**: git (all subcommands), gh (all subcommands)
- **Web dev**: npm, node, ng, yarn, pnpm, npx, tsc, webpack, vite
- **Container**: docker, docker-compose, docker compose, podman
- **Search**: rg, grep, ag, ack, find
- **Utilities**: curl, wget, which, where, env, set, export, sed, awk, sort, uniq, xargs, tee, tr, cut, paste, diff, patch, tar, zip, unzip, jq, yq
- **Python**: python, pip, pytest, ruff (for the tool itself)
- **PowerShell**: powershell, pwsh (common on Windows)

**Pattern note**: Use both bare command (`Bash(ls)`) and wildcard (`Bash(ls *)`) to cover zero-arg and multi-arg invocations.

**Alternatives considered**:
- Rely solely on bypass mode: Works but provides no granularity for standard/minimal levels
- Single `Bash(*)` catch-all: Too broad for standard level; appropriate only for full level

## R4: Global Installation Target

**Decision**: Use `~/.claude/settings.json` as the global settings location. Expose via `--global` flag on the `configure` command.

**Rationale**: Claude Code documents `~/.claude/settings.json` as the user-level settings file. It is read for all projects where no project-level settings exist. Using `Path.home() / ".claude" / "settings.json"` is cross-platform.

**Alternatives considered**:
- New `dotnet-ai permissions --global` subcommand: Adds CLI complexity; a flag on existing `configure` is simpler
- `--scope project|global` flag: Over-engineered for two options; `--global` is clearer

## R5: Bypass Mode Security Warning

**Decision**: Display a one-time rich console warning panel during init/configure when "full" is selected. No recurring warnings.

**Rationale**: The developer has made a deliberate choice. The warning educates about implications at decision time. Recurring warnings add friction that defeats the purpose of full mode.

**Warning content**: "Full permission mode enables bypassPermissions — the AI assistant will execute all operations without prompting. Only use in trusted environments."
