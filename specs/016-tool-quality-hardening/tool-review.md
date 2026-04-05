# Full Tool Review: dotnet-ai-kit — Post-016 Hardening Pass

**Date**: 2026-04-04  
**Branch**: `015-arch-enforcement-multi-repo` (post-016 working tree)  
**Reviewer**: Claude Sonnet 4.6  
**Scope**: Full tool — CLI, commands, copier, config, models, agents, skills, rules, profiles, hooks, permissions, extensions, tests  
**Baseline**: 280 tests passing · 0 lint errors · 142 files changed in 016 pass

---

## Table of Contents

1. [CLI Commands](#1-cli-commands)
2. [Command Files (27)](#2-command-files)
3. [Copier & Deployment Pipeline](#3-copier--deployment-pipeline)
4. [Config & Models](#4-config--models)
5. [Skills (120)](#5-skills)
6. [Rules (15)](#6-rules)
7. [Agents & Profiles](#7-agents--profiles)
8. [Permissions System](#8-permissions-system)
9. [Extensions System](#9-extensions-system)
10. [Build & Packaging](#10-build--packaging)
11. [Test Coverage](#11-test-coverage)
12. [Issues Summary](#12-issues-summary)

---

## 1. CLI Commands

### Registered Commands (7)

| Command | Entry Point | Key Flags |
|---------|------------|-----------|
| `dotnet-ai init` | `cli.py:287` | `--ai`, `--type`, `--force`, `--dry-run`, `--json` |
| `dotnet-ai check` | `cli.py:628` | `--verbose`, `--json` |
| `dotnet-ai upgrade` | `cli.py:922` | `--force`, `--dry-run`, `--json` |
| `dotnet-ai configure` | `cli.py:1363` | `--minimal`, `--no-input`, `--reset`, `--global`, `--dry-run`, `--json` |
| `dotnet-ai extension-add` | `cli.py:1787` | `--dev`, `--verbose` |
| `dotnet-ai extension-remove` | `cli.py:1822` | (name only) |
| `dotnet-ai extension-list` | `cli.py:1841` | (none) |

### User Journey

```
dotnet-ai init --ai claude [--type <type>]
  └─ auto-defaults to claude if no AI detected (post-016)
  └─ deploys profile + hook if --type provided (post-016)
      ↓
/dotnet-ai.detect   (slash command — AI detects project type)
      ↓
dotnet-ai configure --no-input --company Acme
  └─ guarded: exits code 1 if init not run first (post-016)
  └─ re-deploys rules, skills, agents (post-016)
      ↓
dotnet-ai check     (reports all 8 table columns post-016)
      ↓
dotnet-ai upgrade   (on CLI version bump)
```

### Issues Found

**CLI-1 [LOW] — 5 remaining `except Exception: pass` blocks**  
After the 016 pass, 4 of the original silent swallows were fixed. Five remain (all intentional but undocumented):

| Location | Context | Verdict |
|----------|---------|---------|
| `cli.py:463` | Load `detected_paths` from `project.yml` in `init()` | Acceptable — optional pre-fill |
| `cli.py:567` | `copy_hook()` during `init()` | Acceptable — hook is optional at init time |
| `cli.py:1642` | Load `detected_paths` in `configure()` | Acceptable — optional |
| `cli.py:1683` | Load `project.yml` for profile type in `configure()` | Acceptable — falls back to "generic" |
| `cli.py:1709` | `copy_hook()` during `configure()` | Acceptable — hook is optional |

All 5 are semantically sound (optional operations with safe defaults). The only improvement would be a `_verbose_log` call inside each so verbose mode surfaces what was skipped.

**CLI-2 [MEDIUM] — `check` command has no `--verbose` enrichment for profile/hook**  
The `check` table shows "deployed" / "—" for Profile and Hook. In verbose mode (`-v`) there is no additional detail (e.g., which profile file, what the hook model is). Non-verbose users see the same output as verbose users for these columns.

**CLI-3 [LOW] — `configure --dry-run` doesn't skip the init guard**  
If a user runs `dotnet-ai configure --dry-run` without a prior `init`, they get exit code 1 ("not initialized") instead of a dry-run preview. The guard at `cli.py:1440` fires before the dry-run check at `cli.py:1448`. For a dry-run operation the guard should allow pass-through with a warning.

**CLI-4 [LOW] — `upgrade` has no `--force` with profile re-deploy**  
`upgrade --force` re-copies commands, rules, skills, agents. It does NOT force-redeploy the profile or hook regardless of `--force`. If a profile file changes between CLI versions, `upgrade` won't update it unless the profile path changes. The profile deploy block only runs if `project.yml` exists and is readable.

**CLI-5 [LOW] — `extension-list` outputs nothing when empty**  
When no extensions are installed `extension-list` prints no output and exits 0. There is no "No extensions installed" message. This is silent and potentially confusing.

---

## 2. Command Files

### Structure Audit (all 27)

| Command | Lines | $ARGS | Usage | Flags | Examples |
|---------|-------|-------|-------|-------|----------|
| `add-aggregate.md` | 112 | ✅ | ✅ | ✅ | ✅ |
| `add-crud.md` | 148 | ✅ | ✅ | ✅ | ✅ |
| `add-endpoint.md` | 104 | ✅ | ✅ | ✅ | ✅ |
| `add-entity.md` | 136 | ✅ | ✅ | ✅ | ✅ |
| `add-event.md` | 108 | ✅ | ✅ | ✅ | ✅ |
| `add-page.md` | 112 | ✅ | ✅ | ✅ | ✅ |
| `add-tests.md` | 138 | ✅ | ✅ | ✅ | ✅ |
| `analyze.md` | 197 | ❌ | ❌ | ❌ | ❌ |
| `checkpoint.md` | 120 | ✅ | ✅ | ✅ | ✅ |
| `clarify.md` | 185 | ✅ | ❌ | ❌ | ❌ |
| `configure.md` | 143 | ✅ | ❌ | ✅ | ❌ |
| `detect.md` | 146 | ✅ | ❌ | ✅ | ❌ |
| `do.md` | 179 | ✅ | ❌ | ✅ | ❌ |
| `docs.md` | 189 | ✅ | ✅ | ✅ | ✅ |
| `explain.md` | 135 | ✅ | ✅ | ✅ | ✅ |
| `implement.md` | 196 | ❌ | ❌ | ❌ | ❌ |
| `init.md` | 117 | ✅ | ❌ | ✅ | ❌ |
| `learn.md` | 129 | ✅ | ❌ | ✅ | ❌ |
| `plan.md` | 143 | ❌ | ❌ | ❌ | ❌ |
| `pr.md` | 162 | ❌ | ❌ | ❌ | ❌ |
| `review.md` | 188 | ❌ | ❌ | ❌ | ❌ |
| `specify.md` | 200 | ✅ | ❌ | ❌ | ❌ |
| `status.md` | 144 | ✅ | ✅ | ✅ | ✅ |
| `tasks.md` | 200 | ❌ | ❌ | ❌ | ❌ |
| `undo.md` | 113 | ✅ | ✅ | ✅ | ✅ |
| `verify.md` | 186 | ❌ | ❌ | ❌ | ❌ |
| `wrap-up.md` | 142 | ✅ | ✅ | ✅ | ✅ |

**Summary**: 14 of 27 commands are missing Usage sections. 14 are missing Examples. The 7 code-gen commands and 6 session commands follow a consistent, well-structured template. The 14 lifecycle/SDD commands (analyze, clarify, plan, tasks, implement, specify, review, verify, pr, init, configure, detect, learn, do) use an internal-step documentation format that omits user-facing invocation syntax.

### CMD-1 [MEDIUM] — 14 lifecycle commands missing Usage + Examples sections

Commands in the SDD lifecycle and project group document internal steps for the AI but provide no quick-reference Usage block or Examples. A user opening `analyze.md` sees 197 lines of steps with no entry-point syntax. The 7 code-gen commands show the right pattern.

**Affected**: analyze, clarify, configure, detect, do, implement, init, learn, plan, pr, review, specify, tasks, verify.

### CMD-2 [HIGH] — 3 short aliases missing from `COMMAND_SHORT_ALIASES`

`CLAUDE.md` documents `/dai.config`, `/dai.crud`, `/dai.page` but `COMMAND_SHORT_ALIASES` in `copier.py:40` does not include entries for `configure`, `add-crud`, or `add-page`. The deployed files will be `dai.configure.md`, `dai.add-crud.md`, `dai.add-page.md` — none of which match the documented slash commands.

| CLAUDE.md documents | Copier generates | Gap |
|--------------------|-----------------|-----|
| `/dai.config` | `dai.configure.md` | missing `"configure": "config"` |
| `/dai.crud` | `dai.add-crud.md` | missing `"add-crud": "crud"` |
| `/dai.page` | `dai.add-page.md` | missing `"add-page": "page"` |

### CMD-3 [LOW] — `specify.md` and `tasks.md` are at the 200-line budget limit

Both files are exactly 200 lines and cannot absorb further additions without a refactor. Future spec additions (e.g., new artifact types, new multi-repo steps) will push them over the limit.

### CMD-4 [LOW] — `analyze.md` at 197 lines with no room for `$ARGUMENTS`

`analyze.md` is the heaviest file without `$ARGUMENTS`. It currently processes artifacts from a fixed feature directory. If future work adds optional filtering or scope flags, there is no room (197/200 lines) to add them without refactoring.

---

## 3. Copier & Deployment Pipeline

### Key Functions

| Function | Location | Purpose |
|----------|----------|---------|
| `copy_commands()` | `copier.py:149` | Deploy slash commands per AI tool |
| `copy_rules()` | `copier.py:202` | Deploy always-on rules |
| `copy_skills()` | `copier.py:372` | Deploy skills with token resolution |
| `copy_agents()` | `copier.py:469` | Deploy agent definitions with frontmatter transform |
| `copy_profile()` | `copier.py:563` | Deploy architecture profile to rules dir |
| `copy_hook()` | `copier.py:615` | Inject PreToolUse hook into settings.json |
| `deploy_to_linked_repos()` | `copier.py:691` | Orchestrate full deploy to secondary repos |
| `copy_permissions()` | `copier.py:1099` | Apply permission allow-list to settings.json |
| `verify_permissions()` | `copier.py:1192` | Verify settings match config level |
| `scaffold_project()` | `copier.py:963` | Create project from template |

### COP-1 [HIGH] — Hook model hardcoded in `copy_hook()` (`copier.py:674`)

```python
"model": "claude-haiku-4-5-20251001",
"timeout": 15000,
```

Both values are hardcoded strings. The model ID will become stale when new Claude versions release (e.g., `claude-haiku-4-6`). The timeout has no rationale comment. These should be constants at the module top or configurable via `DotnetAiConfig`.

### COP-2 [MEDIUM] — Duplicate `_parse_version` functions

`copier.py:58` defines `_parse_version()` and `extensions.py:31` defines `_parse_version_tuple()`. Both are identical in logic (split on `.`, cast to int, treat non-numeric as 0). They differ only in: `copier.py` version strips extra whitespace with `.strip()` while `extensions.py` version does not. Should be a shared utility in a `utils.py` or `__init__.py`.

### COP-3 [MEDIUM] — `copy_skills()` silently removes entire skills directory

`copy_skills()` (`copier.py:372`) replaces the entire skills destination with fresh content. If `_resolve_detected_path_tokens()` fails silently (token resolves to empty), the `paths:` line is removed from the skill with no log. Users running `dotnet-ai configure` after changing `detected_paths` may get silently stripped skill activation paths.

### COP-4 [MEDIUM] — `deploy_to_linked_repos()` uses primary `ai_tools` for deployment loop

The inner tool loop (`copier.py:854`) iterates `config.ai_tools` (primary). Skills, agents, rules, and commands are all deployed to whichever tools the primary repo is configured for — not the secondary's. If a secondary repo uses only `cursor` while the primary uses `claude`, the secondary gets Claude files deployed to it. The `sec_ai_tools` variable (introduced in the 016 fix) is used only for `staged_dirs` — the deployment loop still uses `config.ai_tools`.

### COP-5 [LOW] — Non-atomic config writes in `config.py`

`save_config()` and `save_project()` write directly with `path.write_text()`. If the process is killed mid-write, the YAML file is truncated. Pattern should be: write to temp file in same directory → `os.replace()`. This is OS-atomic on all platforms.

### COP-6 [LOW] — `_register_extension_files()` has no rollback on partial failure

If `_register_extension_files()` copies command files for Claude but then fails when copying for Cursor, the extension directory was already installed but files are only partially registered. No rollback occurs.

---

## 4. Config & Models

### Models Overview

| Model | Location | Key Fields |
|-------|----------|-----------|
| `DotnetAiConfig` | `models.py:207` | company, repos, permissions_level, ai_tools, command_style, linked_from |
| `DetectedProject` | `models.py:278` | project_type, mode, confidence, detected_paths, top_signals |
| `ReposConfig` | `models.py:150` | command, query, processor, gateway, controlpanel |
| `CompanyConfig` | `models.py:92` | name, github_org, default_branch |
| `FeatureBrief` | `models.py:403` | feature_id, feature_name, phase, source_repo, required_changes |

### MOD-1 [MEDIUM] — `DotnetAiConfig` silently ignores unknown fields (`extra="ignore"`)

`ConfigDict(extra="ignore")` at `models.py:213` causes typos in config.yml to be silently dropped. For example `permisions_level: full` (typo) is ignored rather than warned about. Post-016, `config-template.yml` no longer has an `integrations:` block, which removes one known source of this problem. However, user-created keys (e.g., `company_name:` instead of `company.name:`) are still silently discarded.

**Recommended**: Change to `extra="forbid"` or `extra="allow"` with a validator that logs warnings for unknown top-level keys — matching the `detected_paths` approach added in 016.

### MOD-2 [LOW] — Confidence string and confidence_score not cross-validated

`DetectedProject` has both `confidence: str` ("high"/"medium"/"low") and `confidence_score: float` (0.0–1.0) with no validation that they agree. A project could have `confidence="high"` and `confidence_score=0.1`. This inconsistency can be set programmatically without error.

### MOD-3 [LOW] — `top_signals: list[dict]` has no schema validation

The field is declared as `list[dict]` with no inner schema. Any dict structure is accepted. Skills and detection commands rely on this field but there's no guarantee it contains expected keys (`signal`, `weight`, `category`).

### MOD-4 [INFO] — `FeatureBrief` validator regex is strict but undocumented

`validate_feature_id()` at `models.py:464` requires the format `NNN-short-name`. The regex and error message exist but the constraint isn't documented in the field description. Users constructing `FeatureBrief` from the Python API will get a cryptic `ValueError`.

---

## 5. Skills

### Coverage Summary

| Metric | Count |
|--------|-------|
| Total skills | 120 |
| With `when-to-use` (under `metadata:`) | 111 |
| With `alwaysApply: true` | 9 |
| With `paths` tokens | 9 |
| Without any activation mechanism | 0 |
| Over 400 lines | 0 |
| With missing `category` field | 2 |

All 9 `alwaysApply: true` skills are in `skills/core/` — appropriate for always-active .NET fundamentals (async patterns, coding conventions, dependency injection, etc.).

All 111 `when-to-use` values are correctly nested under `metadata:` (post-016 fix; 0 top-level violations remain).

All 9 `paths` tokens are correctly nested under `metadata:` with `${detected_paths.*}` template syntax.

All 13 `agent:` references resolve to real files in `agents/`.

### SKL-1 [MEDIUM] — 2 skills missing `category` in metadata

`skills/workflow/plan-artifacts/SKILL.md` and `skills/workflow/plan-templates/SKILL.md` have no `category:` field in their metadata block. Category is used for agent-context grouping. Without it they fall outside any category for reporting purposes.

### SKL-2 [LOW] — 9 skills without `when-to-use` (only `alwaysApply`)

The 9 `core/` skills use `alwaysApply: true` instead of `when-to-use`. This is semantically correct (they apply always). However 9 means ~7.5% of skills are always loaded regardless of context, which affects token budget in every session. Worth auditing whether all 9 truly need always-on loading vs. being high-frequency enough to warrant `when-to-use`.

### SKL-3 [INFO] — `detection/` category has only 1 skill

The `detection` category has 1 skill (`skills/detection/`). Detection logic is mostly delegated to the `/dotnet-ai.detect` slash command. Expanding this category with skills for specific detection patterns (e.g., "identifying CQRS boundaries", "detecting data layer patterns") would improve the detect command's intelligence.

### SKL-4 [INFO] — `observability/` and `resilience/` each have 3 skills

These are growing .NET 8+ concerns. The current 3 skills each cover basics but miss modern patterns: OpenTelemetry tracing, Polly v8 pipeline builder, Health check UI, Circuit breaker with Polly. Not a defect, but a content gap for production-grade projects.

---

## 6. Rules

### Coverage Summary

| Rule File | Lines | Focus |
|-----------|-------|-------|
| `api-design.md` | 51 | REST conventions, versioning, error responses |
| `architecture.md` | 65 | Layer boundaries, dependency inversion |
| `async-concurrency.md` | 49 | Async/await, CancellationToken propagation |
| `coding-style.md` | 49 | Naming, formatting, conventions |
| `configuration.md` | 72 | Options pattern, validation |
| `data-access.md` | 52 | EF Core patterns, repositories |
| `error-handling.md` | 46 | Exceptions, Result<T>, logging |
| `existing-projects.md` | 50 | Legacy code, migration notes |
| `localization.md` | 34 | Resource files, resx |
| `naming.md` | 60 | C# naming conventions |
| `observability.md` | 50 | Logging, metrics, tracing |
| `performance.md` | 50 | Query optimization, caching |
| `security.md` | 51 | Auth, secrets, input validation |
| `testing.md` | 66 | Unit/integration test patterns |
| `tool-calls.md` | 58 | Command invocation guidelines |

All 15 rules are under the 100-line limit. All use clear enforcement language (MUST / MUST NOT / ALWAYS / NEVER). No problematic overlaps.

### RUL-1 [INFO] — No rule for multi-repo or cross-service patterns

The rules cover single-project .NET best practices thoroughly. There is no rule covering multi-repo coordination (e.g., "event contracts must be defined in the command service before query services consume them"). Given that multi-repo support is the headline feature of spec-015/016, a `multi-repo.md` rule would align the rules set with the tool's core use case.

---

## 7. Agents & Profiles

### Agent Files (13)

All agent files exist and all `agent:` references in skill frontmatter resolve. Agents are deployed with frontmatter transformation via `AGENT_FRONTMATTER_MAP` (claude-specific; cursor/copilot stubs exist but are commented out).

### AGT-1 [MEDIUM] — `SUPPORTED_AI_TOOLS` is `{"claude"}` but `AGENT_CONFIG` has 4 tools

`AGENT_CONFIG` defines `claude`, `cursor`, `copilot`, `codex`. `SUPPORTED_AI_TOOLS` at `agents.py:54` is only `{"claude"}`. The `get_agent_config()` function will return configs for all 4 tools — there is no enforcement that only supported tools are used. If a user sets `ai_tools: [cursor]` in config.yml, `configure()` will attempt to deploy to cursor directories (which partially works for rules via `.cursor/rules/`) but skills and agents silently fail because cursor has no `skills_dir` or `agents_dir` in `AGENT_CONFIG`.

### AGT-2 [LOW] — `AGENT_FRONTMATTER_MAP` only has claude entry

The `# v1.0.1: "cursor": { ... }` stubs have been in place since before spec-015. No timeline for implementing them. Users who install with `--ai cursor` get agent files deployed but with unrecognized frontmatter (the tool-agnostic format) because no transformation is applied.

### Profiles (12)

All 12 profiles exist and are correctly mapped in `PROFILE_MAP`. The fallback is `profiles/generic/generic.md`. Profile files are now bundled in the wheel via `pyproject.toml` (post-016 fix).

### PRF-1 [INFO] — No profile for `hybrid` project type in detection output

`PROFILE_MAP` contains `"hybrid": "profiles/microservice/hybrid.md"`. The `/dotnet-ai.detect` command documentation mentions hybrid mode, but the detect skill doesn't explicitly list `hybrid` as a valid `project_type` output. If detection never produces `project_type: hybrid`, the profile is unreachable.

---

## 8. Permissions System

### Permission Levels

| File | Allow entries | Mode |
|------|-------------|------|
| `permissions-minimal.json` | 8 | Minimal — read-only plus essential build ops |
| `permissions-standard.json` | 43 | Standard — full dev workflow |
| `permissions-full.json` | 104 | Full — bypassPermissions enabled |
| `mcp-permissions.json` | 11 | MCP server operations |

### PRM-1 [LOW] — `bypassPermissions` warning only shown in non-JSON mode

In `configure()` at `cli.py:1610`, the `bypassPermissions` warning for "full" mode is guarded by `not json_output`. A CI/CD pipeline using `--json` will silently apply full permissions with no audit trail warning in the output. The warning should appear in JSON mode as a `"warnings"` array in the output.

### PRM-2 [INFO] — No `--permissions` flag on `init`

`init` copies permission files but the level is set only via config. Users who want a specific permission level must run `configure --permissions full` separately. Adding `--permissions` to `init` would allow `dotnet-ai init --ai claude --permissions standard` in one step.

---

## 9. Extensions System

### Flow

```
extension-add --dev ./my-ext
  └─ validate manifest (extension.yml)
  └─ check CLI version compatibility
  └─ file lock on registry
  └─ conflict check (id, command names)
  └─ copytree to .dotnet-ai-kit/extensions/{id}/
  └─ _register_extension_files() → copies to AI tool dirs
  └─ update extensions.yml registry
  └─ execute after_install hooks
```

### EXT-1 [HIGH] — Catalog-based installation raises `ExtensionError` (not implemented)

`install_extension()` at `extensions.py:243` raises `ExtensionError` for any non-`--dev` install. This means `dotnet-ai extension-add my-extension` fails with an error rather than a friendly "not yet supported" message. The error text is reasonable but should be an info-level message, not an exception, since it's an expected limitation not a bug.

### EXT-2 [MEDIUM] — `after_install` hook failure aborts; `after_remove` failure is a warning

`after_install` hooks that fail raise `ExtensionError` (`extensions.py:316-319`). `after_remove` hooks that fail log a warning (`extensions.py:449-455`). This inconsistency means removing an extension always succeeds even if cleanup hooks fail — which could leave the host system in a state the extension author didn't intend.

### EXT-3 [MEDIUM] — Rule file name collision between extensions

In `_register_extension_files()` at `extensions.py:368`, rule files are copied using `src.name` (filename only). If two extensions ship a rule file with the same name (e.g., `conventions.md`), the second install silently overwrites the first. There is no conflict detection for rule files, only for command names.

### EXT-4 [LOW] — Version pre-release segments treated as `0`

`_parse_version_tuple()` at `extensions.py:31` turns `"1.0.0-beta"` into `(1, 0, 0, 0)` by treating non-numeric parts as 0. This means a pre-release version is treated as equivalent to the stable release for compatibility checks. An extension requiring `min_cli_version: 1.1.0-rc1` would install against CLI `1.1.0` (which would be fine) but also against CLI `1.1.0-beta1` (which might not be stable enough).

---

## 10. Build & Packaging

### pyproject.toml `force-include`

| Entry | Maps to | Status |
|-------|---------|--------|
| `commands` | `dotnet_ai_kit/bundled/commands` | ✅ |
| `rules` | `dotnet_ai_kit/bundled/rules` | ✅ |
| `agents` | `dotnet_ai_kit/bundled/agents` | ✅ |
| `skills` | `dotnet_ai_kit/bundled/skills` | ✅ |
| `knowledge` | `dotnet_ai_kit/bundled/knowledge` | ✅ |
| `templates` | `dotnet_ai_kit/bundled/templates` | ✅ |
| `config` | `dotnet_ai_kit/bundled/config` | ✅ |
| `profiles` | `dotnet_ai_kit/bundled/profiles` | ✅ (post-016) |
| `prompts` | `dotnet_ai_kit/bundled/prompts` | ✅ (post-016) |

No packaging issues. All 9 asset directories are bundled. `_get_package_dir()` correctly resolves to `bundled/` in wheel installs and to repo root in dev mode.

### PKG-1 [INFO] — `hooks/` directory not bundled

The `hooks/` directory (bash-guard, edit-format, scaffold-restore, commit-lint) is not in `force-include`. These are hooks for Claude Code itself (not deployed to user projects). If they should be deployable, they need an entry. If they are only for development use within this repo, the omission is correct but should be documented.

---

## 11. Test Coverage

### Summary

| File | Lines | Tests | Primary Coverage |
|------|-------|-------|-----------------|
| `test_cli.py` | 1,515 | 70 | init, check, upgrade, configure, extensions |
| `test_copier.py` | 1,060 | 57 | commands, rules, skills, agents, permissions, scaffold |
| `test_extensions.py` | 456 | 19 | install, remove, list, hooks, conflicts |
| `test_multi_repo_deploy.py` | 448 | 15 | deploy pipeline, version checks, branch creation |
| `test_config.py` | 194 | 14 | load/save, YAML errors, validation |
| `test_models.py` | 175 | 22 | all pydantic models, validators |
| `test_detection.py` | 188 | 12 | grep helpers, architecture classification |
| `test_copier_agents.py` | 193 | 15 | agent frontmatter transformation per tool |
| `test_copier_hooks.py` | 217 | 10 | hook injection, settings.json manipulation |
| `test_copier_profiles.py` | 186 | 14 | profile selection, confidence-based deployment |
| `test_copier_skills.py` | 118 | 8 | skill token resolution, metadata preservation |
| `test_agents.py` | 81 | 8 | AGENT_CONFIG lookup, detect_ai_tools |
| `test_models_new_fields.py` | 69 | 9 | ReposConfig, FeatureBrief field validators |
| **Total** | **4,900** | **280** | |

### Per-Command Coverage

| CLI Command | Test Count | Notable Gaps |
|-------------|-----------|-------------|
| `init` | 22 | Codex/Cursor tool paths, `--force` on partial state |
| `check` | 13 | `--verbose` output, linked repos with github: prefix |
| `upgrade` | 10 | Profile re-deploy with `--force`, hook upgrade |
| `configure` | 16 | `--dry-run` guard interaction, full interactive flow |
| `extension-add` | 7 | Version mismatch error message, conflict resolution |
| `extension-remove` | 6 | After-remove hook failure path |
| `extension-list` | 3 | Empty-list silent output |

### TST-1 [MEDIUM] — `deploy_to_linked_repos()` deployment loop not tested with secondary `ai_tools`

The test `test_secondary_repo_uses_own_command_style` (added in 016) checks command_style. There is no test verifying that `staged_dirs` uses the secondary's `ai_tools` (the COP-4 issue above — the deployment loop still uses `config.ai_tools`). This gap makes the COP-4 bug invisible to CI.

### TST-2 [LOW] — No test for `check --verbose` output enrichment

All 13 `check` tests use default or `--json` mode. There is no test exercising the `--verbose` path, meaning the verbose permission verification branch (`cli.py:929`) has no dedicated test.

### TST-3 [LOW] — `configure --dry-run` without init not tested (CLI-3 issue)

No test covers the interaction between the `configure` init guard and the `--dry-run` flag.

### TST-4 [INFO] — `scaffold_project()` has 14 grep hits in tests but via `test_copier.py`

`scaffold_project()` is covered indirectly. No dedicated test for template override files or deeply nested template variable substitution edge cases.

---

## 12. Issues Summary

### Severity Legend
- **CRITICAL**: Data loss, security, or broken core workflow
- **HIGH**: User-visible malfunction or documentation-vs-code mismatch
- **MEDIUM**: Degraded UX, silent failures with workarounds, code smell
- **LOW**: Minor inconvenience, edge case, or polish item
- **INFO**: Observation, no action required

### All Issues

| ID | Severity | Area | Description |
|----|----------|------|-------------|
| CMD-2 | HIGH | Commands | 3 short aliases missing from `COMMAND_SHORT_ALIASES` (`configure→config`, `add-crud→crud`, `add-page→page`) — deployed files don't match CLAUDE.md |
| EXT-1 | HIGH | Extensions | Catalog install raises `ExtensionError` instead of friendly unsupported message |
| COP-1 | HIGH | Copier | Hook model `claude-haiku-4-5-20251001` and timeout `15000` hardcoded — will go stale |
| CMD-1 | MEDIUM | Commands | 14 lifecycle commands missing Usage and Examples sections |
| COP-2 | MEDIUM | Copier | Duplicate `_parse_version` / `_parse_version_tuple` in copier.py and extensions.py |
| COP-3 | MEDIUM | Copier | `copy_skills()` silently strips `paths:` lines when tokens resolve empty — no log |
| COP-4 | MEDIUM | Copier | `deploy_to_linked_repos()` inner tool loop uses primary `config.ai_tools`, not secondary's |
| MOD-1 | MEDIUM | Models | `DotnetAiConfig` silently drops unknown fields (`extra="ignore"`) — typos undetected |
| AGT-1 | MEDIUM | Agents | `get_agent_config()` accepts unsupported tools (cursor/copilot) without validation |
| EXT-2 | MEDIUM | Extensions | `after_install` failure aborts; `after_remove` failure is just a warning — inconsistent |
| EXT-3 | MEDIUM | Extensions | Rule file name collision between extensions silently overwrites earlier rule |
| TST-1 | MEDIUM | Tests | No test for secondary `ai_tools` usage in `deploy_to_linked_repos()` loop |
| CLI-2 | MEDIUM | CLI | `check --verbose` provides no additional detail for Profile/Hook columns |
| CLI-3 | LOW | CLI | `configure --dry-run` blocked by init guard instead of pass-through with warning |
| CLI-4 | LOW | CLI | `upgrade --force` doesn't force re-deploy profile/hook |
| CLI-5 | LOW | CLI | `extension-list` outputs nothing when no extensions installed |
| COP-5 | LOW | Copier | Non-atomic config writes — truncation risk on process kill |
| COP-6 | LOW | Extensions | `_register_extension_files()` has no rollback on partial failure |
| MOD-2 | LOW | Models | `confidence` string and `confidence_score` not cross-validated |
| MOD-3 | LOW | Models | `top_signals: list[dict]` has no inner schema |
| EXT-4 | LOW | Extensions | Pre-release version segments treated as 0 in `_parse_version_tuple()` |
| AGT-2 | LOW | Agents | `AGENT_FRONTMATTER_MAP` only has claude; cursor/copilot stubs not implemented |
| PRM-1 | LOW | Permissions | `bypassPermissions` warning not emitted in `--json` mode |
| CMD-3 | LOW | Commands | `specify.md` and `tasks.md` at 200-line budget limit — no room for additions |
| CMD-4 | LOW | Commands | `analyze.md` at 197 lines, no room for `$ARGUMENTS` |
| TST-2 | LOW | Tests | No test for `check --verbose` output |
| TST-3 | LOW | Tests | No test for `configure --dry-run` without init |
| CLI-1 | LOW | CLI | 5 remaining `except Exception: pass` blocks not surfaced in verbose mode |
| SKL-1 | MEDIUM | Skills | 2 skills missing `category` field in metadata |
| SKL-2 | LOW | Skills | 9 `alwaysApply` skills — audit whether all need always-on loading |
| PRM-2 | INFO | Permissions | No `--permissions` flag on `init` (requires separate `configure` call) |
| RUL-1 | INFO | Rules | No rule covering multi-repo coordination patterns |
| SKL-3 | INFO | Skills | `detection/` category has only 1 skill |
| SKL-4 | INFO | Skills | `observability/` and `resilience/` could expand for .NET 8+ patterns |
| AGT-2 | INFO | Agents | Cursor/Copilot agent frontmatter transform not implemented |
| PRF-1 | INFO | Profiles | `hybrid` project type in PROFILE_MAP may not be reachable from detection |
| PKG-1 | INFO | Build | `hooks/` directory not in `force-include` — intentional or oversight? |
| MOD-4 | INFO | Models | `FeatureBrief.validate_feature_id()` constraint undocumented in field description |

### Count by Severity

| Severity | Count |
|----------|-------|
| HIGH | 3 |
| MEDIUM | 9 |
| LOW | 17 |
| INFO | 8 |
| **Total** | **37** |

### Recommended Priority Order

**Immediate (before next release):**
1. **CMD-2** — Fix 3 missing aliases in `COMMAND_SHORT_ALIASES` (3-line change, high user impact)
2. **COP-1** — Extract hook model/timeout to named constants
3. **COP-4** — Use secondary's `ai_tools` in deploy loop (not just `staged_dirs`)

**Next sprint:**
4. **CMD-1** — Add Usage + Examples to 14 lifecycle commands
5. **MOD-1** — Change `extra="ignore"` to log warnings for unknown top-level keys
6. **EXT-1** — Replace catalog install `ExtensionError` with friendly unsupported message
7. **COP-2** — Deduplicate `_parse_version` into shared utility
8. **SKL-1** — Add `category:` to 2 workflow skills
9. **TST-1** — Add test covering secondary `ai_tools` in deploy loop

**Backlog:**
- CLI-3, CLI-4, CLI-5, EXT-2, EXT-3, PRM-1, COP-5, COP-6, MOD-2, MOD-3
