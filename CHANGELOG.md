# Changelog

All notable changes to dotnet-ai-kit will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] — Unreleased

### Added
- 26 slash commands for the full SDD lifecycle, code generation, smart workflows, and session management
- 106 skills across 17 categories covering core .NET, architecture, API, data, CQRS, microservices, testing, DevOps, docs, and more
- 13 specialist agents with skill routing tables (dotnet-architect, api-designer, ef-specialist, command-architect, query-architect, cosmos-architect, gateway-architect, processor-architect, controlpanel-architect, test-engineer, reviewer, devops-engineer, docs-engineer)
- All 13 agents wired to all 26 commands — each command loads the appropriate specialist agent(s) by project type and task type
- Agent skill paths updated from shorthand to full `skills/` directory paths for reliable resolution
- `implement.md` routes to all 13 agents via project-type + task-type routing matrix
- Code-gen commands (`add-aggregate`, `add-entity`, `add-event`, `add-endpoint`, `add-page`, `add-tests`, `add-crud`) load domain-specific specialist agents
- Lifecycle commands (`review`, `docs`, `verify`, `analyze`, `plan`, `tasks`, `specify`, `clarify`) load purpose-specific agents
- 9 always-loaded coding convention rules (architecture, coding-style, configuration, error-handling, existing-projects, localization, naming, testing, tool-calls)
- 4 safety/quality hooks: pre-bash-guard (blocks dangerous commands), post-edit-format (auto-format .cs), post-scaffold-restore (auto dotnet restore), pre-commit-lint (format verification)
- Hook toggleability — each hook can be independently enabled/disabled via settings
- 13 project scaffold templates (9 microservice + 4 generic: Clean Arch, DDD, Modular Monolith, VSA)
- 11 knowledge reference documents (event sourcing, outbox, service bus, gRPC, Cosmos DB, deployment, testing, etc.)
- 4 permission config templates (minimal, standard, full, MCP) with auto-apply to `.claude/settings.json`
- AI-powered project detection via `/dotnet-ai.detect` smart skill
- Claude Code plugin format (`.claude-plugin/plugin.json`) for marketplace distribution
- Agent Skills specification compliance — all 106 SKILL.md files have `dotnet-ai-` prefixed names for cross-agent compatibility (16+ tools)
- C# LSP MCP configuration (`.mcp.json`) pointing to csharp-ls for semantic code intelligence
- Skills and agents are now copied to projects during `init` and `upgrade` (git-tracked alongside commands and rules)
- Python CLI (`dotnet-ai`) with `--version` flag, init, check, upgrade, configure, and extension management commands
- Automatic permission application — `init`, `configure`, and `upgrade` now write permission rules to `.claude/settings.json` based on the selected level (minimal/standard/full)
- Full permission level enables `bypassPermissions` mode — zero permission prompts for all development operations
- Permission merge system — tool-managed entries tracked in `config.yml`, user-added custom rules preserved across level changes
- `--global` flag on `configure` — applies permissions to `~/.claude/settings.json` for cross-repository coverage
- Expanded permission templates: full (103 entries + bypass mode), standard (43 entries), minimal (8 entries)
- Pre-write backup of `.claude/settings.json` to `.dotnet-ai-kit/backups/` before permission changes
- One-time security warning when selecting full (bypass) permission level
- Upgrade command auto-detects and fixes projects with configured permissions that were never applied
- 137 test functions across 6 test files (90% coverage)
- Cross-platform support (Windows, macOS, Linux)
- `--type` flag validation against all 12 known project types
- Support for Claude Code (v1.0)

### Fixed
- **Permission system now works** — selecting a permission level (minimal/standard/full) previously saved a label to config.yml but never wrote rules to Claude Code's settings file; now `init`, `configure`, and `upgrade` all apply permissions automatically
- Permission templates expanded with bare-command variants (`Bash(ls)` alongside `Bash(ls *)`) to cover zero-argument invocations that previously triggered prompts
- Config template `permissions` nested key changed to flat `permissions_level` (matches pydantic model)
- Hook `pre-commit-lint.sh` find command missing parentheses for OR conditions
- Jinja2 template rendering now uses `StrictUndefined` — raises error on missing variables instead of silent empty strings
- Extension install cleanup — partial files removed on failure
- Extension registry file locking to prevent concurrent corruption
- CLI output no longer shows empty paths for tools without skills/agents support

### Changed
- `filelock` added as dependency for extension registry safety
- Repo path validation added to config model (`github:org/repo` or valid local path)
- `DotnetAiConfig` model now includes `managed_permissions` field for tracking tool-managed permission entries
- `copier.py` now includes `merge_permissions()` and `copy_permissions()` functions for intelligent permission management
- `configure` command accepts `--global` flag for user-level permission installation

### Known Limitations
- Only Claude Code is supported as AI tool; Cursor, GitHub Copilot, and Codex CLI are planned for v1.1
- Extension catalog install is not yet available; only `--dev` local path installs work
- Project detection requires the `/dotnet-ai.detect` command (AI-driven); there is no built-in Python fallback
