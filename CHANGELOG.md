# Changelog

All notable changes to dotnet-ai-kit will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] — 2026-05-18

First stable release. Combines work from features 001–019.

---

### Plugin-Native Architecture (feature 019)

Single-PR pivot to a plugin-native architecture for Claude Code / Codex CLI /
Cursor (Copilot stays render-only). Closes 35 functional requirements
(FR-001 — FR-035), 14 success criteria (SC-001 — SC-014), 8 release-gating
BLOCKERS (B-1 – B-8: 4 P0 + 4 P1), 12 content findings (F-A – F-L), and
5 C# accuracy issues (C-Q1 – C-Q5) found during the cross-AI review phase.
Full detail in [docs/release-notes-v1.0.md](docs/release-notes-v1.0.md).

#### Added
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
- Codex CLI subagent render (OOS-004 partial lift): `dotnet-ai init --ai codex`
  writes 14 `.codex/agents/<name>.toml` files from `agents-source/*.md`.
  Conflict policy: existing files preserved on re-init (user customizations win).
- Cursor sub-agent set (A-005 PASS branch): 14 files under `agents/`,
  `.cursor-plugin/plugin.json` declares `"agents": "./agents/"`,
  `rules/cursor/*.mdc` (16 Cursor-format rule files — 5 with `alwaysApply:true`,
  11 path-scoped with `globs:`).
- SessionStart compact + PreToolUse arch-profile hooks (commit 13);
  rules reclassified into `rules/conventions/` (5 universal, always-loaded)
  + `rules/domain/` (11 path-scoped). Constitution v1.0.8 codifies it.
- `bin/dotnet-ai` + `bin/dotnet-ai.cmd` — source-tree wrappers for contributors.
- CI smoke job rewritten as a 3-OS matrix (ubuntu/macos/windows) with
  preflight gate for the 4 binaries (claude/codex/cursor/csharp-ls).
- 16+ new tests covering FR-029, FR-031, FR-032, FR-033, host symmetry,
  manifest integrity, manifest-path resolution, Copilot freshness,
  config-yml + project-yml schema, agent-source shape, bin/ wrappers,
  C# skill snippet compile scaffold, and the OOS-005 fail-branch path.

#### Changed
- Plugin-native hosts (Claude/Codex/Cursor): init writes only per-solution
  files (`.dotnet-ai-kit/*` + `.claude/settings.json` for Claude). NO bulk
  copy of commands / skills / agents / rules. The prior `copy_profile()` /
  `copy_hook()` call sites are gated by `tool_name in PLUGIN_NATIVE_HOSTS`.
- `dotnet-ai upgrade` is a no-op for plugin-native hosts (FR-015);
  `dotnet-ai upgrade --copilot` re-renders Copilot files only.
- `dotnet-ai configure` interactive picker shows all 4 hosts
  (claude/codex/cursor/copilot) per FR-016.
- `.mcp.json` retains only `codebase-memory-mcp`; `csharp-ls` migrated
  to the Claude plugin manifest as a `csharp-lsp` dependency (FR-028).
- 13 of 14 `agents-source/*.md` migrated to nest Claude allow-list fields
  under `host_overrides.claude:` (F-F fix). `agents-claude/*.md` regenerated.
- Skill / rule frontmatter cleanups (F-A – F-I): 9 core skills gain
  `when_to_use`; 5 rules gain `## Related Skills`; 4 gRPC skills gain
  `## Related Knowledge`; 3 empty section headers filled; RFC 2119 normalised.
- C# skill bodies fixed (C-Q1-Q5): CancellationToken propagation in
  gRPC service + minimal-api filter; `Problem(detail:, statusCode:)` in
  controllers; minor-unit integers replacing `double` for money in proto
  files; primary-constructor description corrected.
- AGENTS.md + CONTRIBUTING.md project-structure counts updated
  (rules 15 → 16, hooks 5 → 7, templates 13 → 12).

#### Notes
- **`dotnet-ai upgrade` for plugin-native hosts**: the command is intentionally
  a no-op. Plugin updates propagate automatically at the next AI session —
  there is nothing to copy.
- **T200 release gate**: all 3-OS CI lanes (static-unit × 3 Python × 3 OS = 9,
  plus smoke × 3 OS = 3) must be green on `workflow_dispatch` before tagging.

---

### Fix Token Burn (feature 018)

#### Changed — startup safety
- Session-start hook rewritten with lazy-default + MCP-first wording (≤30 lines).
- `pre-bash-guard.sh` and `pre-commit-lint.sh` exit `2` (block) instead of `1`.
- `hooks/hooks.json` restructured: `matcher` carries tool names only; permission
  patterns moved to handler `if:` (Claude Code v2.1.85+).
- Dynamic architecture hook in `copier.py` uses `if: Edit(*.cs)` / `Write(*.cs)`
  on v2.1.85+; falls back to command-pattern matcher on older.
- `.claude/settings.json` no longer duplicates plugin hooks.

#### Changed — frontmatter discipline
- 124 `skills/**/SKILL.md` rewritten: activation fields lifted from nested
  `metadata:` to top level; `when-to-use` → `when_to_use`; `alwaysApply`
  removed everywhere.
- 16 rules, 12 profiles, 13 agents stripped of `alwaysApply` and
  `## Skills Loaded` blocks.

#### Added — manifest + atomic upgrade
- `src/dotnet_ai_kit/manifest.py` — pydantic v2 `Manifest` / `DeployedFile`.
- `src/dotnet_ai_kit/upgrade.py` — `run_upgrade()` orchestrator with SHA-256
  user-modified detection, per-file backups, atomic rollback, last-3-runs
  rotation.
- `.dotnet-ai-kit/.gitignore` generated on init/upgrade.
- Atomic writes in `save_config()` and `save_project()` via temp-file + replace.

#### Changed — lazy loading
- 11 non-universal rules now carry top-level `paths:`; 5 universal rules
  combined ≤300 lines.
- 12 profiles carry `paths:`.
- 16 commands replaced "Load all skills listed" with bounded-selection wording.
- `agents.py` no longer lifts `expertise` → `skills` (FR-013).

#### Added — MCP + memory split
- `.mcp.json` registers `codebase-memory-mcp >= 0.6.1`.
- `src/dotnet_ai_kit/mcp_check.py` runtime version check; outcome persisted
  to `.dotnet-ai-kit/mcp-state.yml`.
- 7 operational commands carry the MCP-first block + FR-022 fallback line.
- `/dai.learn` produces a 6-file memory split + ≤100-line index; `/dai.plan`
  and `/dai.review` selectively load topic files (cuts context ~80%).

#### Added — measurement + CI gates
- `scripts/measure.py`, `scripts/check.py`, `scripts/check.ps1`.
- `scripts/violation_harness.py` — 17-class SC-010 coverage proof.
- `.github/workflows/ci.yml` split into `static-unit` (every PR) + gated
  `smoke` (label `[smoke]` OR nightly cron).

---

### Agent Discipline + Foundation (features 001–017)

#### Added — agent discipline (inspired by [obra/superpowers](https://github.com/obra/superpowers))
- 4 workflow skills: `verification-gate`, `receiving-review-feedback`,
  `systematic-debugging`, `git-worktree-isolation`
- **Iron Laws**, **Rationalization Tables**, and **Red Flags Checklists** in
  `review-checklist`, `code-review-workflow`, and `testing` rule.
- **2-stage code review** in `code-review-workflow` skill — Pass 1: spec
  compliance; Pass 2: code quality. Pass 2 cannot start until Pass 1 approves.
- Per-task review gate in `/dai.go` — after each task: run `dotnet build` +
  `dotnet test` with evidence, compare against spec.
- CSO (Claude Search Optimization) applied to all 124 skill descriptions —
  rewritten to trigger-only "Use when..." format.

#### Added — core features
- 27 slash commands for the full SDD lifecycle, code generation, smart
  workflows, and session management.
- `/dotnet-ai.learn` (`/dai.learn`) — generates a persistent project
  constitution at `.dotnet-ai-kit/memory/constitution.md`.
- 124 skills across 17 categories; 13 specialist agents; 16 convention rules.
- All 13 agents wired to all 27 commands via project-type + task-type routing.
- `rules/multi-repo.md` — 16th rule covering event contract ownership,
  cross-repo branch naming, deploy order, circular dependency prohibition.
- 14 project scaffold templates (10 microservice + 4 generic).
- 16 knowledge reference documents (event sourcing, outbox, service bus,
  gRPC, Cosmos DB, deployment, testing, CQRS, DDD, Clean Architecture, VSA,
  Modular Monolith, concurrency, documentation standards).
- 4 permission config templates (minimal, standard, full, MCP) with auto-apply
  to `.claude/settings.json`.
- Claude Code plugin manifest (`.claude-plugin/plugin.json`).
- `dotnet-ai` CLI: init, check, upgrade, configure, extension management.
- `NamingConfig.domain` field — configurable domain name for template rendering.
- `dotnet-ai changelog` command.
- `init --permissions` flag — apply permission level during init.
- Extension `min_cli_version` validation.
- Extension hook execution (`after_install` / `after_remove`).
- Extension registry file locking (concurrent install safety).
- `deploy_to_linked_repos()` — full tooling sync to all configured secondary repos.
- `FeatureBrief` model — cross-repo feature projection written to each secondary
  repo during `/dai.specify`.
- `service-map.md` generated by `/dai.specify`; `event-flow.md` by `/dai.plan`.
- PreToolUse enforcement hook (architecture profile compliance check on every
  Write/Edit via fast Haiku model).
- 12 architecture profiles (auto-deployed on `/dai.detect`).
- `dotnet-ai configure --global` — applies permissions to `~/.claude/settings.json`.

#### Fixed
- Duplicate skill name `dotnet-ai-controller-patterns` renamed to
  `dotnet-ai-restful-controllers`.
- `--dry-run` standardized across all 27 commands; `--preview` flag removed.
- Dead constitution check reference in `/dai.plan` (was pointing to
  `.specify/memory/constitution.md`, now `.dotnet-ai-kit/memory/constitution.md`).
- Extension hooks never executed — now validated and run via `subprocess.run()`.
- Extension `min_cli_version` never checked — now raises `ExtensionError`.
- Permission system — level was saved to config but never written to
  `.claude/settings.json`; now applied automatically on init/configure/upgrade.
- Jinja2 template rendering now uses `StrictUndefined`.

#### Known Limitations
- Extension catalog install not yet available — `dotnet-ai extension-add <name>`
  (without `--dev`) shows a user-friendly message directing to `--dev`; full
  catalog support planned for v1.1.
- Standalone-executable packaging deferred to v1.1 (OOS-003).
- Plugin-manifest-bundled Codex subagents deferred to v1.1 (OOS-004 plugin
  portion); v1.0 writes subagents per-project via `dotnet-ai init --ai codex`.
- Multi-repository activity monitor deferred to v1.1 (OOS-006).
- `dotnet-ai render --host` supports `claude` only in v1.0; other host shapes
  deferred to v1.1.
