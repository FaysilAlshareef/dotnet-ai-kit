# Data Model: Plugin Ecosystem v1.0

**Phase**: 1 — Design & Contracts
**Date**: 2026-03-22

## Entities

### Plugin Manifest (`plugin.json`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Plugin identifier: `dotnet-ai-kit` |
| version | string | Yes | SemVer version: `1.0.0` |
| description | string | Yes | One-line description for marketplace |
| author | string | Yes | Author name |
| homepage | string | No | GitHub repository URL |
| tags | string[] | No | Discovery tags: `["dotnet", "csharp", ".net", "cqrs", "microservices", "clean-architecture"]` |
| category | string | No | Marketplace category: `"development"` |

**Relationships**: References commands/, skills/, agents/, hooks/ directories at repo root.

### Agent Skills Metadata (SKILL.md frontmatter)

| Field | Type | Required (spec) | Description |
|-------|------|-----------------|-------------|
| name | string | Yes | Prefixed identifier: `dotnet-ai-{skill-name}` |
| description | string | Yes | Trigger description with keywords |
| category | string | No (optional) | Skill category for internal organization |
| agent | string | No (optional) | Assigned specialist agent |

**Validation rules**:
- `name` MUST start with `dotnet-ai-`
- `name` MUST be lowercase kebab-case
- `description` MUST be non-empty

**State transitions**: None — skills are static configuration files.

### Hook Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| event | string | Yes | Claude Code event: `PreToolUse` or `PostToolUse` |
| pattern | string | Yes | Regex pattern matching the tool or command |
| command | string | Yes | Shell command to execute |
| mode | string | Yes | `block` (prevent action) or `warn` (log and continue) |

**4 hooks defined**:

| Hook ID | Event | Pattern | Mode | Prerequisite |
|---------|-------|---------|------|-------------|
| pre-bash-guard | PreToolUse | `Bash` | block | None |
| post-edit-format | PostToolUse | `Edit\|Write` on `*.cs` | warn | `dotnet` CLI |
| post-scaffold-restore | PostToolUse | `Bash` containing `dotnet new` | warn | `dotnet` CLI |
| pre-commit-lint | PreToolUse | `Bash` containing `git commit` | block | `dotnet` CLI |

### MCP Server Configuration (`.mcp.json`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| servers | object | Yes | Map of server name to config |
| servers.csharp-ls.command | string | Yes | Command to launch: `csharp-ls` |
| servers.csharp-ls.args | string[] | No | Command arguments |
| servers.csharp-ls.transport | string | Yes | Transport type: `stdio` |

**Graceful degradation**: If `csharp-ls` is not found on PATH, the MCP server entry is skipped at startup with no error.

### Hook Settings (user-configurable)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| hooks.pre-bash-guard.enabled | boolean | No | `true` | Toggle bash guard |
| hooks.post-edit-format.enabled | boolean | No | `true` | Toggle auto-format |
| hooks.post-scaffold-restore.enabled | boolean | No | `true` | Toggle auto-restore |
| hooks.pre-commit-lint.enabled | boolean | No | `true` | Toggle lint check |
| hooks.pre-bash-guard.extra_patterns | string[] | No | `[]` | Additional blocklist patterns |
