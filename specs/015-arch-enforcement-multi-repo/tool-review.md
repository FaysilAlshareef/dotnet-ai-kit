# Full Tool Review: dotnet-ai-kit UX Lifecycle, Feature Compatibility, and Gaps

**Date**: 2026-04-04
**Branch**: `015-arch-enforcement-multi-repo`
**Scope**: Full tool — CLI, commands, copier, config, models, agents, skills, profiles, hooks, permissions, extensions, tests

---

## Table of Contents

1. [CLI Lifecycle & UX Flow](#1-cli-lifecycle--ux-flow)
2. [Command Files Analysis (27 commands)](#2-command-files-analysis)
3. [Cross-Feature Compatibility](#3-cross-feature-compatibility)
4. [Deployment Pipeline](#4-deployment-pipeline)
5. [Config & Models](#5-config--models)
6. [Rules, Skills & Profiles](#6-rules-skills--profiles)
7. [Permission System](#7-permission-system)
8. [Extensions System](#8-extensions-system)
9. [Build & Packaging](#9-build--packaging)
10. [Test Coverage](#10-test-coverage)
11. [Issues Summary](#11-issues-summary)

---

## 1. CLI Lifecycle & UX Flow

### Commands Registered (7)

| Command | Purpose | Key Flags |
|---------|---------|-----------|
| `dotnet-ai init` | Initialize project | `--ai`, `--type`, `--force`, `--dry-run`, `--json` |
| `dotnet-ai check` | Report state / health check | `--verbose`, `--json` |
| `dotnet-ai upgrade` | Upgrade to latest CLI version | `--force`, `--dry-run`, `--json` |
| `dotnet-ai configure` | Interactive config wizard | `--minimal`, `--no-input`, `--reset`, `--global`, `--dry-run` |
| `dotnet-ai extension-add` | Install extension | `--dev` |
| `dotnet-ai extension-remove` | Remove extension | (name only) |
| `dotnet-ai extension-list` | List extensions | (none) |

### Required User Journey

```
dotnet-ai init --ai claude
    |
    v
/dotnet-ai.detect  (slash command — AI detects project type)
    |
    v
dotnet-ai configure  (set company, repos, permissions, style)
    |
    v
dotnet-ai check  (verify setup)
    |
    v
dotnet-ai upgrade  (when CLI version changes)
```

### UX Issues

**ISSUE-L1: `init` requires `--ai` if no `.claude/` directory exists (exit code 3)**
If the user runs `dotnet-ai init` in a project without any AI tool directory, it exits with a vague error. The error message is good ("No AI tool detected. Use --ai flag"), but the UX could auto-default to `claude` since it's the only supported tool in v1.0.

**ISSUE-L2: `configure` works without prior `init`**
`configure` gracefully creates a new config if none exists, but it does NOT create the `.dotnet-ai-kit/` directory structure, `version.txt`, or copy commands/rules/skills/agents. This means a user who skips `init` and goes straight to `configure` gets a half-configured state: config exists but no tooling is deployed.

**ISSUE-L3: `check` command has significant reporting gaps**
The `check` command reports:
- Project type, mode, .NET version
- AI tools status (command count, rule count)
- Extensions, company, repos, permissions
- Permission consistency, version mismatch

It does NOT report:
- Whether an architecture profile is deployed
- Whether the enforcement hook is deployed
- Skills count or agents count
- Linked repo statuses or `linked_from` field
- `detected_paths` from project.yml

Users cannot verify the new features (profiles, hooks, multi-repo) through `check`.

**ISSUE-L4: `upgrade` silently swallows errors in profile/hook/multi-repo deployment**
Multiple `except Exception: pass` blocks at cli.py lines 968-994 hide failures. If profile deployment fails during upgrade, the user gets no feedback.

**ISSUE-L5: No `uninstall` or `reset` command**
There is no way to fully remove dotnet-ai-kit from a project. Users must manually delete `.dotnet-ai-kit/`, `.claude/commands/`, `.claude/rules/`, `.claude/skills/`, `.claude/agents/`.

---

## 2. Command Files Analysis

### Inventory (27 commands, all within 200-line budget)

| File | Lines | $ARGUMENTS | context | agent | Branch Safety |
|------|-------|------------|---------|-------|---------------|
| add-aggregate.md | 112 | Yes | - | - | No |
| add-crud.md | 148 | Yes | - | - | No |
| add-endpoint.md | 104 | Yes | - | - | No |
| add-entity.md | 136 | Yes | - | - | No |
| add-event.md | 108 | Yes | - | - | No |
| add-page.md | 112 | Yes | - | - | No |
| add-tests.md | 138 | Yes | - | - | No |
| analyze.md | 197 | No | fork | general-purpose | No |
| checkpoint.md | 120 | Yes | - | - | No |
| clarify.md | 173 | Yes | - | - | **MISSING** |
| configure.md | 143 | Yes | - | - | No |
| detect.md | 146 | Yes | - | - | No |
| do.md | 176 | Yes | - | - | No |
| docs.md | 189 | Yes | - | - | No |
| explain.md | 135 | Yes | - | - | No |
| implement.md | 184 | No | - | - | **MISSING** |
| init.md | 117 | Yes | - | - | No |
| learn.md | 129 | Yes | - | - | No |
| plan.md | 132 | No | - | - | Yes |
| pr.md | 162 | No | - | - | No |
| review.md | 188 | No | fork | reviewer | No |
| specify.md | 200 | Yes | - | - | Yes |
| status.md | 144 | Yes | - | - | No |
| tasks.md | 200 | No | - | - | Yes |
| undo.md | 113 | Yes | - | - | No |
| verify.md | 186 | No | fork | general-purpose | No |
| wrap-up.md | 142 | Yes | - | - | No |

### Critical Command Issues

**ISSUE-C1: Missing branch safety in `clarify.md` and `implement.md` (HIGH)**
Both commands auto-commit to secondary repos but lack the "Secondary Repo Branch Safety" section that `specify.md`, `plan.md`, and `tasks.md` have. This means:
- `clarify.md` L137-139: auto-commits brief updates with no branch check
- `implement.md` L132-133: auto-commits brief updates with no branch check
Risk: Direct commits to main/master/develop in secondary repos.

**ISSUE-C2: `event-flow.md` is a phantom artifact (HIGH)**
- Referenced by `tasks.md` (L37), `analyze.md` (L42), and `do.md` (L52)
- `do.md` says the plan step generates it
- But `plan.md` has NO instruction to generate `event-flow.md`
- No command explicitly creates this artifact

**ISSUE-C3: Duplicate `--dry-run` flag in 9 commands (MEDIUM)**
All code-gen commands plus `docs.md` and `explain.md` have TWO rows for `--dry-run` in their flags table:
```
| `--dry-run` | Display generated code in terminal without writing to disk |
| `--dry-run` | List files that would be created/modified, no writes |
```
These describe different behaviors under the same flag name. Should be two distinct flags (e.g., `--dry-run` and `--list`).

**ISSUE-C4: `specify.md` misordered steps (MEDIUM)**
Step 4b (L152: "Project Feature Briefs") appears AFTER Step 5 (L130: "Generate Quality Checklist"). Execution order is: Step 4 -> Step 5 -> Step 4b -> Step 6. Step 4b should be before Step 5.

**ISSUE-C5: `service-map.md` dual ownership (MEDIUM)**
- `specify.md` L117: generates `service-map.md` during specification
- `do.md` L52: says plan generates `service-map.md` and `event-flow.md`
- `plan.md`: has no explicit mention of generating `service-map.md`
Unclear which step owns this artifact.

**ISSUE-C6: Frontmatter `agent` vs body agent mismatch (LOW)**
- `analyze.md`: frontmatter says `agent: general-purpose` but body loads specialist architects (L18-28)
- `verify.md`: frontmatter says `agent: general-purpose` but body loads `test-engineer` and `devops-engineer` (L18-19)
The framework uses the frontmatter field; the body instructions add specialists on top. Not a bug but potentially confusing.

**ISSUE-C7: Short aliases in CLAUDE.md don't match deployed filenames (MEDIUM)**
CLAUDE.md documents aliases like `/dai.spec`, `/dai.check`, `/dai.go`. The copier generates filenames from source stems: `dai.specify.md`, `dai.analyze.md`, `dai.implement.md`. The documented short aliases do not correspond to any actual deployed command file name and will not work as slash commands.

**ISSUE-C8: 7 commands lack `$ARGUMENTS` (LOW)**
`analyze`, `implement`, `plan`, `pr`, `review`, `tasks`, `verify` do not use `$ARGUMENTS`. Users cannot pass freeform text to these via slash commands (only flags like `--resume`, `--dry-run`).

**ISSUE-C9: `specify.md` and `tasks.md` at exactly 200 lines (LOW)**
No room for expansion without budget violation.

---

## 3. Cross-Feature Compatibility

### init -> configure -> check -> upgrade Chain

| Transition | Works? | Notes |
|-----------|--------|-------|
| init -> configure | Yes | init creates config.yml; configure reads and updates it |
| init -> check | Yes | check reports on everything init created |
| configure -> check | **Partial** | check doesn't report profiles, hooks, or linked repos |
| configure -> upgrade | Yes | upgrade reads config and re-deploys everything |
| upgrade -> check | **Partial** | same gap as above |

### SDD Lifecycle Chain

```
specify -> clarify -> plan -> tasks -> [analyze] -> implement -> review -> verify -> pr
```

| Transition | Works? | Artifact Flow |
|-----------|--------|---------------|
| specify -> clarify | Yes | spec.md passed through |
| clarify -> plan | Yes | updated spec.md consumed |
| plan -> tasks | Yes | plan.md consumed |
| tasks -> analyze | Yes | tasks.md + plan.md + spec.md consumed |
| analyze -> implement | Yes | analysis.md is optional input |
| implement -> review | Yes | git diff provides input |
| review -> verify | Yes | sequential, no artifact dependency |
| verify -> pr | Yes | verified state enables PR |

**Gaps in lifecycle**:
1. `event-flow.md` is consumed but never produced (ISSUE-C2)
2. `clarify` and `implement` lack branch safety for secondary repos (ISSUE-C1)
3. `analyze` is optional and its insertion point is ambiguous (after plan OR after tasks)

### Plugin Mode Compatibility

| Feature | Plugin Mode Handled? |
|---------|---------------------|
| copy_commands | Yes — skips full-prefix when is_plugin=True |
| copy_rules | N/A — not affected by plugin mode |
| copy_skills | N/A |
| copy_agents | N/A |
| copy_profile | N/A |
| copy_hook | N/A |
| deploy_to_linked_repos | **No** — secondary repos always get all files, ignores plugin mode |

### Command Style Lifecycle (full/short/both)

| Operation | Handles Style? |
|-----------|---------------|
| init | Yes — copies per config.command_style |
| configure | Yes — re-copies commands after style change |
| upgrade | Yes — re-copies per current style |
| deploy_to_linked_repos | **Uses primary config's style** — secondary repos inherit primary's command_style |

---

## 4. Deployment Pipeline

### What Gets Deployed (per AI tool)

| Asset | init | configure | upgrade | deploy_to_linked |
|-------|------|-----------|---------|-----------------|
| Commands | Yes | Yes (style change) | Yes | Yes |
| Rules | Yes | No | Yes | Yes |
| Skills | Yes | No | Yes | Yes |
| Agents | Yes | No | Yes | Yes |
| Profile | No | Yes | Yes | Yes |
| Hook | No | Yes (Claude only) | Yes (Claude only) | Yes (Claude only) |
| Permissions | Yes | Yes | Yes | No |
| version.txt | Yes | No | Yes | Yes (updated) |
| linked_from | N/A | N/A | N/A | Yes (written) |

**ISSUE-D1: `init` does NOT deploy profiles or hooks**
Profile and hook deployment only happens during `configure` and `upgrade`. If a user runs `init --type command` and starts working without running `configure`, they have no architecture profile enforcing constraints. The profile deployment should also happen during `init` when `--type` is provided.

**ISSUE-D2: `configure` does NOT re-deploy rules, skills, or agents**
When `configure` runs, it only re-copies commands (for style changes), deploys profiles, and deploys hooks. If agent frontmatter or skill paths change between versions, `configure` alone won't update them — only `upgrade` does.

**ISSUE-D3: deploy_to_linked_repos uses primary config's command_style**
The function passes `config` (the primary repo's config) to `copy_commands()` for secondary repos. Secondary repos always get the primary's command style, not their own.

**ISSUE-D4: deploy_to_linked_repos has no rollback on partial failure**
If deployment fails mid-way (after branch creation but before commit), the secondary repo is left in a partially modified state on the new branch.

**ISSUE-D5: `git add .claude/ .dotnet-ai-kit/` in deploy may miss tool-specific directories**
For Cursor (`.cursor/rules/`), the `git add` command only stages `.claude/` and `.dotnet-ai-kit/`, missing `.cursor/` changes. Secondary repos configured for non-Claude tools would have unstaged changes.

---

## 5. Config & Models

### Config Loading

**ISSUE-M1: Corrupted YAML crashes CLI with raw traceback**
`config.py:load_config` catches `ValueError` and `FileNotFoundError` but NOT `yaml.YAMLError`. A corrupted `config.yml` (e.g., invalid YAML syntax) produces an unhandled `yaml.scanner.ScannerError` traceback instead of a friendly error.

**ISSUE-M2: Config template has undeclared `integrations:` section**
`templates/config-template.yml` includes a CodeRabbit `integrations:` section (lines 44-52) that the `DotnetAiConfig` model silently ignores via `ConfigDict(extra="ignore")`. Users who configure integrations from the template will find their settings disappear on next save.

### Model Gaps

**ISSUE-M3: `detected_paths` keys are freeform — no validation**
The `detected_paths` field on `DetectedProject` is `Optional[dict[str, str]]` with no key validation. Any string key is accepted. The `_resolve_detected_path_tokens` function only resolves `${detected_paths.*}` tokens — if the detect command uses different key names than what skills expect, tokens silently resolve to empty.

**ISSUE-M4: `linked_from` has no reverse validation**
When `linked_from` is set on a secondary repo, there's no check that the path actually points to an initialized primary repo. If the primary is moved or deleted, `linked_from` becomes a stale dangling reference with no cleanup mechanism.

---

## 6. Rules, Skills & Profiles

### Rules (15 files, 803 lines total)

All 15 rules have `alwaysApply: true` frontmatter. All under 100 lines. Total: 803/~900 budget (89% utilized). With one architecture profile (up to 100 lines), total reaches 903 — just above the ~900 budget target.

### Skills (120 SKILL.md files)

**ISSUE-S1: Only 11 of 120 skills (9.2%) have `when-to-use` frontmatter**
The auto-activation feature added in this commit only benefits 11 skills. The other 109 skills remain passive — loaded only when explicitly referenced by commands.

**ISSUE-S2: Only 3 of 120 skills have `paths` tokens**
Path-based auto-activation using `${detected_paths.*}` tokens only covers:
- `aggregate-design` (paths: `${detected_paths.aggregates}/**/*.cs`)
- `event-design` (paths: `${detected_paths.events}/**/*.cs`)
- `command-handler` (paths: `${detected_paths.handlers}/**/*.cs`)

Skills for query entities, gateway endpoints, cosmos entities, etc. have `when-to-use` but no `paths` token, meaning they can only activate behaviorally, not by file path.

### Profiles (12 files, all under 100 lines)

All 12 profiles have `alwaysApply: true` frontmatter. All follow the same structure (HARD CONSTRAINTS, Testing Requirements, Data Access). Line counts range from 74 (gateway) to 99 (ddd).

### Agents (13 files)

All 13 agents have complete universal frontmatter (role, expertise, complexity, max_iterations). All expertise values resolve to actual skill directory names.

---

## 7. Permission System

### Templates (4 files)

| File | Entries | defaultMode |
|------|---------|-------------|
| permissions-minimal.json | 8 | (none) |
| permissions-standard.json | 48 | (none) |
| permissions-full.json | 110 | bypassPermissions |
| mcp-permissions.json | 11 | (none) |

### Merge Logic

The permission system correctly:
- Tracks which entries it manages (via `managed_permissions` in config.yml)
- Preserves user-added entries during merge
- Creates backup before overwriting
- Verifies after write

**ISSUE-P1: `permissions-bypass.json` listed as untracked in git**
Git status shows `?? config/permissions-bypass.json` but this file was not committed. May be incomplete work.

---

## 8. Extensions System

**ISSUE-E1: Catalog install not implemented**
`extensions.py` line 246: "Catalog-based extension install is not yet supported." Only `--dev` local installs work.

**ISSUE-E2: `after_remove` hooks never execute**
`remove_extension()` does not call any hooks. The `after_remove` hook event is validated and stored in the registry, but never executed during removal.

---

## 9. Build & Packaging

**ISSUE-B1: `profiles/` and `prompts/` directories NOT bundled in wheel (HIGH)**
`pyproject.toml` `force-include` bundles: commands, rules, agents, skills, knowledge, templates, config. But NOT `profiles/` or `prompts/`.

`copy_profile()` looks for `package_dir / "profiles/"`. In wheel installs, `_get_package_dir()` returns the `bundled/` directory, where `profiles/` won't exist. **Profile deployment will fail in wheel installs.** Same for `prompts/architecture-enforcement-and-multi-repo.md`.

This works in dev mode only because `_get_package_dir()` returns the repo root where `profiles/` exists.

**ISSUE-B2: `hooks/` directory not bundled**
The 4 plugin hook scripts (`hooks/*.sh`) are not in `force-include`. In wheel installs, the hook scripts won't be available. However, hooks are registered in `.claude-plugin/plugin.json` using `${CLAUDE_PLUGIN_ROOT}`, which points to the plugin source — so this may only affect non-plugin installations.

---

## 10. Test Coverage

### Test Files (263 tests, all passing)

| File | Tests | Module Covered |
|------|-------|---------------|
| test_cli.py | 61 | cli.py (end-to-end via CliRunner) |
| test_copier.py | 55 | copier.py (core functions) |
| test_models.py | 20 | models.py |
| test_copier_agents.py | 15 | copier.py (agent transform) |
| test_copier_profiles.py | 14 | copier.py (profile deploy) |
| test_config.py | 13 | config.py |
| test_multi_repo_deploy.py | 13 | copier.py (multi-repo) |
| test_detection.py | 12 | detection.py |
| test_copier_hooks.py | 10 | copier.py (hooks) |
| test_models_new_fields.py | 9 | models.py (new fields) |
| test_agents.py | 8 | agents.py |
| test_copier_skills.py | 8 | copier.py (skill tokens) |
| test_extensions.py | 18 | extensions.py |

All 7 source modules have dedicated test files. No module lacks tests.

**Test Gaps**:
- CLI tests do not cover profile, hook, or multi-repo deployment in `configure`/`upgrade` commands
- No integration tests verifying the full init -> configure -> upgrade lifecycle
- No tests for corrupted YAML handling in config.py

---

## 11. Issues Summary

### CRITICAL (Blocks core functionality)

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| B1 | `profiles/` not bundled in wheel | pyproject.toml | Profile deployment fails in production installs |
| C1 | Missing branch safety in clarify/implement | clarify.md, implement.md | Direct commits to main in secondary repos |

### HIGH (Significant functional gap)

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| C2 | `event-flow.md` phantom artifact | tasks.md, analyze.md, do.md | Referenced but never generated |
| D1 | `init` doesn't deploy profiles/hooks | cli.py init() | No enforcement until configure runs |
| L3 | `check` doesn't report profiles/hooks/linked repos | cli.py check() | Users can't verify new features |
| M1 | Corrupted YAML crashes with raw traceback | config.py load_config() | Poor UX on config corruption |

### MEDIUM (Inconsistency or quality issue)

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| C3 | Duplicate `--dry-run` flag in 9 commands | add-*.md, docs.md, explain.md | Ambiguous user experience |
| C4 | `specify.md` misordered steps | specify.md L130/L152 | Confusing execution order |
| C5 | `service-map.md` dual ownership | specify.md, do.md | Unclear which step generates it |
| C7 | Short aliases don't match deployed filenames | CLAUDE.md vs copier.py | Documented aliases won't work |
| D3 | Linked repos inherit primary's command_style | copier.py deploy_to_linked_repos | Wrong style in secondary repos |
| D5 | `git add` misses non-Claude tool directories | copier.py deploy_to_linked_repos | Unstaged changes for Cursor repos |
| M2 | Config template has undeclared integrations field | templates/config-template.yml | Settings silently dropped |
| S1 | 109/120 skills lack `when-to-use` | skills/**/ | Limited auto-activation coverage |
| E2 | `after_remove` hooks never execute | extensions.py | Cleanup hooks don't run |

### LOW (Minor or cosmetic)

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| C6 | Frontmatter agent vs body agent mismatch | analyze.md, verify.md | Potentially confusing |
| C8 | 7 commands lack $ARGUMENTS | Various | No freeform text input |
| C9 | specify.md and tasks.md at 200-line limit | commands/ | No room for expansion |
| D2 | configure doesn't re-deploy rules/skills/agents | cli.py configure() | Stale assets until upgrade |
| D4 | No rollback on partial multi-repo failure | copier.py | Partial state in secondary repos |
| E1 | Catalog extension install not implemented | extensions.py | Only --dev installs work |
| L1 | init requires --ai despite only supporting claude | cli.py init() | Unnecessary friction |
| L2 | configure works without init (half-state) | cli.py configure() | Missing tooling if init skipped |
| L4 | Upgrade silently swallows deployment errors | cli.py upgrade() | Hidden failures |
| L5 | No uninstall/reset command | cli.py | Manual cleanup required |
| M3 | detected_paths keys are freeform | models.py | Silent token mismatches |
| M4 | linked_from has no reverse validation | models.py | Stale dangling references |
| P1 | permissions-bypass.json untracked | config/ | Incomplete work |
| S2 | Only 3/120 skills have path tokens | skills/**/ | Minimal path-based activation |
