# Changelog

All notable changes to dotnet-ai-kit will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] — 2026-05-18 — Plugin-Native Architecture (feature 019)

Single-PR release that pivots the kit to a plugin-native architecture
for Claude Code / Codex CLI / Cursor (Copilot stays render-only). Closes
35 functional requirements (FR-001 — FR-035), 14 success criteria
(SC-001 — SC-014), and 8 release-gating BLOCKERS (B-1 through B-8: 4 P0
+ 4 P1) plus 12 content findings (F-A through F-L) and 5 C# accuracy
issues (C-Q1 — C-Q5) found in the cross-AI review-phase debate. Full
detail per fix lives in `docs/release-notes-v1.0.md`.

### Added
- Per-host plugin manifests under `.claude-plugin/`, `.codex-plugin/`,
  `.cursor-plugin/`. Each declares scalar relative paths to skills /
  rules / hooks / agents (where supported).
- `dotnet-ai render` (FR-019) — read-only CLI surface for rendering
  individual skill / rule bodies with current project metadata
  substituted. Exit codes 0/20/21/22/23 per `contracts/render-cli.contract.md`.
- `dotnet-ai migrate` (FR-020) — relocates pre-019 layout artifacts
  with 3-keep backup rotation; `--include-linked` recurses into
  linked secondaries (FR-033).
- ProjectMetadata schema (`schemas/project-yml.schema.json`); `dotnet-ai
  check` raw-validates project.yml via jsonschema before pydantic load,
  mapping violations to FR-031 exit class 12.
- UserConfig schema (`schemas/config-yml.schema.json`); init emits
  canonical `enabled_hosts:` and `permission_profile:` (legacy
  `ai_tools` / `permissions_level` accepted via pydantic AliasChoices).
- Copilot render orchestrator: `.github/copilot-instructions.md`,
  `.github/instructions/<area>.instructions.md`, `.github/agents/*.agent.md`,
  with two-tier freshness check (hash + fresh re-render) per B-5 fix.
- SessionStart compact + PreToolUse arch-profile hooks (commit 13);
  rules reclassified into `rules/conventions/` (5 universal, always-loaded)
  + `rules/domain/` (11 path-scoped). Constitution v1.0.8 codifies it.
- `bin/dotnet-ai` + `bin/dotnet-ai.cmd` — source-tree wrappers for
  contributors. End-user installs via pip / uv / pipx use
  `[project.scripts]`. Standalone-executable packaging deferred to v1.1
  per OOS-003.
- CI smoke job rewritten as a 3-OS matrix (ubuntu/macos/windows) with
  preflight gate for the 4 binaries (claude/codex/cursor/csharp-ls) per
  B-7 + Codex r2 finding.
- 16+ new tests covering FR-029, FR-031, FR-032, FR-033, host symmetry,
  manifest integrity, manifest-path resolution, Copilot freshness,
  config-yml + project-yml schema, agent-source shape, bin/ wrappers,
  C# skill snippet compile scaffold, and the OOS-005 fail-branch path.

### Changed
- Plugin-native hosts (Claude/Codex/Cursor): init writes only the
  per-solution files (`.dotnet-ai-kit/*` + `.claude/settings.json` for
  Claude). NO bulk copy of commands / skills / agents / rules. The
  prior `copy_profile()` / `copy_hook()` call sites are gated by
  `tool_name in PLUGIN_NATIVE_HOSTS` (B-1 fix).
- `dotnet-ai upgrade` is a no-op for plugin-native hosts (FR-015);
  `dotnet-ai upgrade --copilot` re-renders Copilot files only.
- `dotnet-ai configure` interactive picker shows all 4 hosts
  (claude/codex/cursor/copilot) per FR-016 / CHK037 (B-6 fix).
- `.mcp.json` description swapped over to "codebase-memory-mcp for
  memory + retrieval" (csharp-ls MCP integration removed in commit 12;
  F5 fix). The legacy MCP description has been deleted everywhere it
  surfaced.
- 13 of 14 `agents-source/*.md` migrated to nest Claude-allow-list
  fields under `host_overrides.claude:` (F-F fix). `agents-claude/*.md`
  regenerated so the allow-list metadata now reaches Claude.
- Skill / rule frontmatter cleanups (F-A through F-I): 9 core skills
  gain `when_to_use`; 5 rules gain `## Related Skills`; 4 gRPC skills
  gain `## Related Knowledge`; 3 empty section headers filled; RFC 2119
  language normalised.
- C# skill bodies fixed (C-Q1-Q5): CancellationToken propagation in
  gRPC service + minimal-api filter; `Problem(detail:, statusCode:)` in
  controllers; minor-unit integers replacing `double` for money in
  proto files; primary-constructor description corrected.
- AGENTS.md + CONTRIBUTING.md project-structure counts updated
  (rules 15 → 16, hooks 5 → 7, templates 13 → 12; F4/F5 fix).

### Notes
- **OOS-005 fail-safe default**: the Cursor sub-agent A-005 spike fixture
  has never executed in CI; the outcome JSON remains `pending`. v1.0
  ships with `.cursor-plugin/plugin.json::agents` ABSENT,
  `generate_cursor_agent()` raises NotImplementedError, release notes
  use neutral 'pending' language. First post-tag `workflow_dispatch`
  smoke run flips the outcome; T171 (PASS branch) restores generation
  if the spike succeeds.
- **T200 release gate**: ALL 3-OS CI lanes (static-unit × 3 Python ×
  3 OS = 9, plus smoke × 3 OS = 3) must be green on `workflow_dispatch`
  before tagging v1.0.0. Maintainer triggers the workflow.

## [Unreleased] — Fix Token Burn (feature 018)

7-PR feature branch tackling 18 token-burn issues from `issues/token-burn-optimization/FINAL-REPORT.md`.

### Changed — startup safety (PR1)
- Session-start hook rewritten with lazy-default + MCP-first wording (≤30 lines).
- `pre-bash-guard.sh` and `pre-commit-lint.sh` exit `2` (block) instead of `1`.
- `hooks/hooks.json` restructured: `matcher` carries tool names only; permission patterns moved to handler `if:` (Claude Code v2.1.85+).
- Dynamic architecture hook in `copier.py` uses `if: Edit(*.cs)` / `Write(*.cs)` on v2.1.85+; falls back to command-pattern matcher on older.
- `.claude/settings.json` no longer duplicates plugin hooks.
- Wheel bundles `.claude-plugin/`, `hooks/`, `.mcp.json`.

### Changed — frontmatter discipline (PR2a)
- 124 `skills/**/SKILL.md` rewritten: activation fields lifted from nested `metadata:` to top level; `when-to-use` → `when_to_use`; `alwaysApply` removed everywhere.
- 16 rules, 12 profiles, 13 agents stripped of `alwaysApply` and `## Skills Loaded` blocks.

### Added — manifest + atomic upgrade (PR2b)
- `src/dotnet_ai_kit/manifest.py` — pydantic v2 `Manifest` / `DeployedFile`.
- `src/dotnet_ai_kit/upgrade.py` — `run_upgrade()` orchestrator with SHA-256 user-modified detection, per-file backups under `.dotnet-ai-kit/backups/upgrade/<iso>/`, atomic rollback, last-3-runs rotation.
- `.dotnet-ai-kit/.gitignore` generated on init/upgrade.
- `copier._resolve_detected_path_tokens()` raises `DeploymentError` on missing keys; `copy_skills` catches per-skill so a project missing one token key (e.g. `cosmos_entities` on a command service) skips that skill instead of aborting the whole deploy.
- `cli.py::upgrade` is atomic via the `_atomic_upgrade()` context manager: snapshots every managed path into `.dotnet-ai-kit/backups/upgrade/<iso>-<uuid>/`, restores byte-for-byte on any exception, rotates to last 3 runs on success. Closes SC-013 + FR-031 through the actual CLI surface, not just the orchestrator in isolation. Manifest pre-check additionally refuses to clobber user-modified files without `--force`. The standalone `upgrade.run_upgrade()` orchestrator stays as the reference implementation for callers that want per-file backup granularity.

### Changed — lazy loading (PR3)
- 11 non-universal rules now carry top-level `paths:`; 5 universal rules combined ≤300 lines (feature 019 v1.0.8 reclassification, see CHANGELOG v1.0.0 above).
- 12 profiles carry `paths:`.
- 16 commands replaced "Load all skills listed" with bounded-selection wording (FR-012).
- `agents.py` no longer lifts `expertise` → `skills` (FR-013).
- `implement.md`, `tasks.md`, `clarify.md` trimmed to ≤200 physical lines.
- Constitution amended to v1.0.7: 16 rules = 4 universal + 12 path-scoped.

### Added — MCP + memory split (PR4)
- `.mcp.json` registers `codebase-memory-mcp >= 0.6.1` alongside `csharp-ls`.
- `src/dotnet_ai_kit/mcp_check.py` runtime version check; outcome persisted to `.dotnet-ai-kit/mcp-state.yml` (sibling of `config.yml`).
- 7 operational commands carry the MCP-first block + exact FR-022 fallback line.
- `/dai.learn` produces a 6-file memory split + ≤100-line index; `/dai.plan` and `/dai.review` selectively load topic files.

### Added — measurement + CI gates (PR5)
- `scripts/measure.py`, `scripts/check.py`, `scripts/check.ps1`.
- `scripts/violation_harness.py` — 17-class SC-010 coverage proof.
- `.github/workflows/ci.yml` split into `static-unit` (every PR) + gated `smoke` (label `[smoke]` OR nightly cron).
- `specs/018-fix-token-burn/traceability.md` — every FR + finding maps to ≥1 test row.

### Token-reduction targets (soft, captured by maintainer with live Claude Code)

| Scenario | Baseline → Post-fix | Target |
|---|---|---|
| Session startup | DEFERRED | ≥ 40% reduction |
| Implementation | DEFERRED | ≥ 30% reduction |
| Review | DEFERRED | ≥ 30% reduction |
| Graph question | DEFERRED | ≥ 30% reduction (answer parity) |

Hard release gates (SC-004/005/006/013/014/015/016) are binary and verified by the static + unit suite.

## [1.0.0] — Unreleased

### Added (Superpowers-Inspired Agent Discipline Features)
- 4 new workflow skills: `verification-gate`, `receiving-review-feedback`, `systematic-debugging`, `git-worktree-isolation`
- **Verification Gate skill** — Iron Law: no completion claims without fresh `dotnet build`/`dotnet test` evidence. Includes forbidden phrases list, .NET-specific verification commands table, rationalization table, and red flags checklist
- **Receiving Review Feedback skill** — Anti-sycophancy enforcement for code review. Bans performative agreement ("Great point!", "You're absolutely right!"), requires technical verification before implementing suggestions, source priority hierarchy (user > project rules > CodeRabbit > external reviewers), YAGNI gate for reviewer suggestions, .NET-specific checks (DI, layer boundaries, middleware pipeline)
- **Systematic Debugging skill** — 4-phase root cause investigation (investigate → pattern analysis → hypothesis → implementation). 3-fix escalation rule: if 3+ fixes fail, question the architecture. .NET-specific escalation examples (EF Core migrations, DI resolution, middleware pipeline)
- **Git Worktree Isolation skill** — Isolated workspace setup with smart directory selection, safety verification (.gitignore check), .NET project auto-detection (`dotnet restore` → `dotnet build` → `dotnet test`), baseline verification, and cleanup procedures
- **Session-start bootstrap hook** — `SessionStart` hook in `hooks.json` that reminds the agent to check skills before every action. Lists key workflow skills for quick discovery
- **Per-task review gate** in `/dai.go` (implement command) — after each task: run `dotnet build` + `dotnet test` with evidence, compare against spec, check against rules. No batching failures across tasks
- **Spec approval gate** in `/dai.plan` — verifies spec exists AND has been approved before planning proceeds
- **2-stage review process** in `code-review-workflow` skill — Pass 1: spec compliance (built the right thing?), Pass 2: code quality (built it well?). Pass 2 cannot start until Pass 1 approves
- **Rationalization tables** added to 3 existing files: `review-checklist` skill, `code-review-workflow` skill, `testing` rule — each gains an Iron Law, rationalization table (agent excuses + rebuttals), and red flags checklist
- **CSO (Claude Search Optimization)** applied to all 124 skill descriptions — rewritten from workflow summaries to trigger-only "Use when..." format so agents read full skills instead of shortcutting from descriptions

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
