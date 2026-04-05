# Changelog

All notable changes to dotnet-ai-kit will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] — Unreleased

### Added
- 27 slash commands for the full SDD lifecycle, code generation, smart workflows, and session management
- `/dotnet-ai.learn` (`/dai.learn`) command — generates a persistent project constitution at `.dotnet-ai-kit/memory/constitution.md` with detected architecture, domain model, naming conventions, key packages, and established patterns. Chains `/dai.detect` internally. Supports `--update` to refresh and `--dry-run` to preview.
- 5 architecture knowledge reference documents: CQRS patterns, DDD patterns, Clean Architecture patterns, Vertical Slice Architecture patterns, Modular Monolith patterns
- Plugin manifest (`plugin.json`) now enumerates all 27 commands, 13 agents, 120 skills (by category), and 4 hooks for marketplace discoverability
- Extension hook execution — `after_install` hooks declared in extension manifests now execute via `subprocess.run()` after successful install
- Extension `min_cli_version` validation — install rejects extensions that require a newer CLI version
- `NamingConfig.domain` field — configurable domain name for template rendering (set via `naming.domain` in `config.yml`), replaces hardcoded "Domain" placeholder in scaffolded projects
- Constitution Check gate in `/dai.plan` wired to `.dotnet-ai-kit/memory/constitution.md` — validates plan compliance against project-specific principles
- `service-map.md` as explicit output of `/dai.specify` for microservice-mode features (Mermaid diagram, per-service summary, affected repos)
- 120 skills across 17 categories covering core .NET, architecture, API, data, CQRS, microservices, testing, DevOps, docs, and more
- 13 specialist agents with skill routing tables (dotnet-architect, api-designer, ef-specialist, command-architect, query-architect, cosmos-architect, gateway-architect, processor-architect, controlpanel-architect, test-engineer, reviewer, devops-engineer, docs-engineer)
- All 13 agents wired to all 27 commands — each command loads the appropriate specialist agent(s) by project type and task type
- Agent skill paths updated from shorthand to full `skills/` directory paths for reliable resolution
- `implement.md` routes to all 13 agents via project-type + task-type routing matrix
- Code-gen commands (`add-aggregate`, `add-entity`, `add-event`, `add-endpoint`, `add-page`, `add-tests`, `add-crud`) load domain-specific specialist agents
- Lifecycle commands (`review`, `docs`, `verify`, `analyze`, `plan`, `tasks`, `specify`, `clarify`) load purpose-specific agents
- 16 always-loaded coding convention rules (architecture, coding-style, configuration, error-handling, existing-projects, localization, naming, testing, tool-calls, api-design, async-concurrency, data-access, observability, performance, security, multi-repo)
- 4 safety/quality hooks: pre-bash-guard (blocks dangerous commands), post-edit-format (auto-format .cs), post-scaffold-restore (auto dotnet restore), pre-commit-lint (format verification)
- Hook toggleability — each hook can be independently enabled/disabled via settings
- 14 project scaffold templates (10 microservice + 4 generic: Clean Arch, DDD, Modular Monolith, VSA)
- 16 knowledge reference documents (event sourcing, outbox, service bus, gRPC, Cosmos DB, deployment, testing, CQRS, DDD, Clean Architecture, VSA, Modular Monolith, etc.)
- 4 permission config templates (minimal, standard, full, MCP) with auto-apply to `.claude/settings.json`
- AI-powered project detection via `/dotnet-ai.detect` smart skill
- Claude Code plugin format (`.claude-plugin/plugin.json`) for marketplace distribution
- Agent Skills specification compliance — all 120 SKILL.md files have `dotnet-ai-` prefixed names for cross-agent compatibility (16+ tools)
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
- 307 tests across 14 test files
- Cross-platform support (Windows, macOS, Linux)
- `--type` flag validation against all 12 known project types
- Support for Claude Code (v1.0)

### Fixed
- **Duplicate skill name resolved** — `skills/api/controller-patterns/SKILL.md` renamed from `dotnet-ai-controller-patterns` to `dotnet-ai-restful-controllers` (was identical to `skills/api/controllers/SKILL.md`)
- **`--dry-run` standardized** — all 27 commands now use `--dry-run` consistently; `--preview` flag removed from 12 command files (add-*, docs, explain, checkpoint, undo, wrap-up)
- **Dead constitution check reference** — `/dai.plan` Constitution Check gate was pointing to non-existent `.specify/memory/constitution.md`; now wired to `.dotnet-ai-kit/memory/constitution.md`
- **Extension hooks never executed** — hooks declared in extension manifests were loaded but silently ignored; now validated and executed via `subprocess.run()`
- **Extension `min_cli_version` never checked** — field was stored but never compared against CLI version; now raises `ExtensionError` if CLI is too old
- **Hardcoded template variables** — `copier.py` always rendered "Domain"/"domain" regardless of config; now reads from `NamingConfig.domain`
- **Permission system now works** — selecting a permission level (minimal/standard/full) previously saved a label to config.yml but never wrote rules to Claude Code's settings file; now `init`, `configure`, and `upgrade` all apply permissions automatically
- Permission templates expanded with bare-command variants (`Bash(ls)` alongside `Bash(ls *)`) to cover zero-argument invocations that previously triggered prompts
- Config template `permissions` nested key changed to flat `permissions_level` (matches pydantic model)
- Hook `pre-commit-lint.sh` find command missing parentheses for OR conditions
- Jinja2 template rendering now uses `StrictUndefined` — raises error on missing variables instead of silent empty strings
- Extension install cleanup — partial files removed on failure
- Extension registry file locking to prevent concurrent corruption
- CLI output no longer shows empty paths for tools without skills/agents support

### Changed
- `CodeRabbitConfig` and `IntegrationsConfig` models removed from `models.py` (deferred to v1.1); `DotnetAiConfig` now uses `ConfigDict(extra="ignore")` to silently handle legacy config files
- `NamingConfig` model gains `domain` field (default: "Domain") for configurable template rendering
- `copier.py` template context now reads `Domain`/`domain` from `config.naming.domain` instead of hardcoded strings
- `extensions.py` validates hook structure (keys must be `after_install`/`after_remove`, values must be lists of command strings)
- `filelock` added as dependency for extension registry safety
- Repo path validation added to config model (`github:org/repo` or valid local path)
- `DotnetAiConfig` model now includes `managed_permissions` field for tracking tool-managed permission entries
- `copier.py` now includes `merge_permissions()` and `copy_permissions()` functions for intelligent permission management
- `configure` command accepts `--global` flag for user-level permission installation

### Added (spec-015: Architecture Enforcement & Multi-Repo)
- `copy_profile()` — deploys architecture-specific profile markdown to each AI tool's rules directory after detection
- `copy_hook()` — injects a PreToolUse enforcement hook into `.claude/settings.json` for architecture compliance checking
- `deploy_to_linked_repos()` — orchestrates full tooling deployment (commands, rules, skills, agents, profile, hook) to all configured secondary repos
- `linked_from` config field — secondary repos record which primary repo deployed their tooling
- `FeatureBrief` model — cross-repo feature projection artifact written to each secondary repo during `/dai.specify`
- `service-map.md` generated by `/dai.specify`, `event-flow.md` generated by `/dai.plan` for microservice mode
- "Secondary Repo Branch Safety" section in 5 commands (clarify, implement, plan, specify, tasks) — ensures feature work lands on `chore/brief-NNN-name` branches
- Secondary repos now use their own `command_style` from their own config.yml (not inheriting primary's)
- 6 enforcement rules added for architecture compliance

### Added (spec-016: Quality Hardening)
- `check` command now shows Skills, Agents, Profile, Hook columns in the AI Tools table
- `check` command reports linked repos status, `linked_from` field, and detected_paths in config panel
- `check --json` includes all new fields plus `linked_repos` and `detected_paths`
- `configure` command exits code 1 if `.dotnet-ai-kit/` not initialized (unless `--dry-run`)
- `configure` re-deploys rules, skills, and agents after saving config (style changes take effect immediately)
- `_get_tool_status()` helper eliminates ~60 lines of duplicated tool-status logic between JSON and rich table paths
- `after_remove` hook execution added to `remove_extension()` (mirrors `after_install` pattern)
- `detected_paths` unknown key validator — logs warning for unrecognized path keys
- `COMMAND_SHORT_ALIASES` alias fixes: `configure→config`, `add-crud→crud`, `add-page→page`
- `--list` flag disambiguated from `--dry-run` in all 9 code-gen commands
- `secondary_repo_uses_own_command_style` and `git_add_stages_tool_directories` tests

### Added (spec-017: Pre-Release v1.0.0 Hardening)
- `utils.py` shared utility module with `parse_version()` (pre-release suffix stripping), `HOOK_MODEL`, and `HOOK_TIMEOUT_MS` constants
- `CatalogInstallError` exception — `dotnet-ai extension-add <name>` (without `--dev`) now shows a user-friendly "not yet supported" message instead of crashing
- `rules/multi-repo.md` — 16th always-loaded rule covering event contract ownership, cross-repo branch naming, deploy order, and circular dependency prohibition
- `dotnet-ai changelog` command — prints CHANGELOG.md or falls back to recent git tags
- `init --permissions` flag — apply permission level during init without a separate `configure` call
- `check --verbose` now shows profile file path and hook model/timeout after the AI Tools table
- `configure --dry-run` works without prior init (shows default config preview instead of hard-fail)
- `extension-list` prints a help message when no extensions are installed
- `bypassPermissions` warning included in `configure --json` output when `permissions_level = "full"`
- Atomic writes in `save_config()` and `save_project()` via `path.with_suffix(".tmp")` + `Path.replace()`
- 5 verbose except blocks now emit `_verbose_log` messages so `--verbose` surfaces skipped operations
- `DotnetAiConfig` model validator logs warnings for unknown top-level config keys
- Rule file name collision detection in `_check_conflicts()` — two extensions cannot ship rules with identical filenames
- `after_remove` hook failures now raise `ExtensionError` (consistent with `after_install`)
- `get_agent_config()` logs a warning when accessing a recognised-but-unsupported tool (cursor/copilot/codex)
- All 27 command files now have `## Usage` and `**Examples:**` sections
- 2 workflow skill files gained missing `category: workflow` metadata field
- Token debug logging in `_resolve_detected_path_tokens()` when `paths:` lines are stripped
- `upgrade --force` unconditionally re-deploys profile and hook (not blocked by version match)
- 14 test files, 307 tests total

### Known Limitations
- Only Claude Code is supported as AI tool; Cursor, GitHub Copilot, and Codex CLI are planned for v1.1
- Extension catalog install not yet available — `dotnet-ai extension-add <name>` shows a user-friendly message directing to `--dev`; full catalog support planned for v1.1
- Project detection requires the `/dotnet-ai.detect` command (AI-driven); there is no built-in Python fallback
