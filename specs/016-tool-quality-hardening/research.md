# Research: Tool-Wide Quality Hardening

**Branch**: `016-tool-quality-hardening` | **Date**: 2026-04-04

## R1: Build Packaging — force-include gaps

**Decision**: Add `profiles/` and `prompts/` to `pyproject.toml` `force-include` section.

**Rationale**: Current `force-include` (pyproject.toml:48-56) bundles 7 directories: commands, rules, agents, skills, knowledge, templates, config. Both `profiles/` (12 files in 2 subdirs: generic/5, microservice/7) and `prompts/` (1 file) exist at repo root but are missing. `_get_package_dir()` (cli.py:106-118) returns `{package}/bundled/` in wheel mode — profile resolution via `package_dir / "profiles/"` fails silently in production installs.

**Alternatives considered**: (a) Move profiles into an existing bundled dir — rejected, would break PROFILE_MAP paths. (b) Inline profiles into Python code — rejected, profiles are user-facing markdown.

## R2: Short-alias command filenames

**Decision**: Add `COMMAND_SHORT_ALIASES` dict mapping source stems to short names. Apply during short-prefix generation in `copy_commands()`.

**Rationale**: `copy_commands()` (copier.py:115-185) generates short-prefix files as `dai.{stem}.md` using the source filename's stem directly. CLAUDE.md documents aliases like `/dai.spec`, `/dai.check`, `/dai.go` but deployed files are `dai.specify.md`, `dai.analyze.md`, `dai.implement.md`. The alias mapping (10 entries) resolves this by substituting the stem before filename generation.

**Alternatives considered**: (a) Rename source command files — rejected, would break full-prefix names and existing references. (b) Create symlinks — rejected, not cross-platform.

## R3: CLI init — profile and hook deployment

**Decision**: Add `copy_profile()` and `copy_hook()` calls to `init()` after existing skill/agent deployment, gated on project type being known.

**Rationale**: `init()` (cli.py:228) deploys commands, rules, skills, agents, permissions but NOT profiles or hooks. These only happen in `configure()` (line 1461) and `upgrade()` (line 963). When `--type` is provided or `project.yml` exists, the project type is known and profile can be deployed immediately.

**Alternatives considered**: (a) Auto-run configure after init — rejected, too heavy for init flow. (b) Prompt user to run configure — rejected, adds unnecessary friction.

## R4: CLI check — missing fields

**Decision**: Extend `check()` to report profile status, hook status, skills count, agents count, linked repos, linked_from, and detected_paths in both rich table and JSON output.

**Rationale**: `check()` (cli.py:530) currently reports 4 columns for AI tools (tool, status, commands, rules). Missing: profiles (check `architecture-profile.md` existence), hooks (check `settings.json` for `_source: "dotnet-ai-kit-arch"`), skills count, agents count. Config panel shows repos as "X of 5" but no per-repo details. `linked_from` and `detected_paths` are not shown at all.

**Alternatives considered**: None — this is purely additive reporting.

## R5: Config YAML error handling

**Decision**: Wrap `yaml.safe_load()` in `config.py:load_config()` with `yaml.YAMLError` catch, re-raise as `ValueError`.

**Rationale**: `load_config()` (config.py:32) catches `pydantic.ValidationError` (line 59) but not `yaml.YAMLError`. Malformed YAML produces a raw `yaml.scanner.ScannerError` traceback.

**Alternatives considered**: (a) Catch all exceptions — rejected, too broad. (b) Pre-validate YAML syntax — rejected, redundant with catch.

## R6: deploy_to_linked_repos — command style and git add

**Decision**: (a) Load secondary repo's config.yml to get its command_style; pass a modified config to copy_commands(). (b) Collect all deployed directories dynamically for git add.

**Rationale**: `deploy_to_linked_repos()` (copier.py:674) passes primary `config` to `copy_commands()` (line 821), so secondaries inherit primary's command_style. `git add` (line 871) hardcodes `.claude/` and `.dotnet-ai-kit/`, missing `.cursor/` for Cursor-configured repos. Fix: read secondary config for style, build git add directory list from AGENT_CONFIG per tool.

**Alternatives considered**: (a) Always use "both" style for secondaries — rejected, wastes disk and may confuse devs who configured short-only. (b) Stage all files with `git add .` — rejected, would stage unrelated files.

## R7: Skill activation coverage

**Decision**: Add `when-to-use` to 69+ more skills (target: 80+/120 total). Add `paths` tokens to 6+ more skills (target: 9+/120 total).

**Rationale**: Only 11/120 skills have `when-to-use` and 3/120 have `paths`. Skills with `alwaysApply: true` (9 core skills) don't need `when-to-use`. Remaining 111 non-alwaysApply skills are candidates; targeting 80+ total means adding to ~69+ skills.

**Alternatives considered**: (a) Add to all 120 — rejected, `alwaysApply` skills and some generic skills don't benefit. (b) Only expand paths tokens — rejected, `when-to-use` provides broader behavioral activation.

## R8: Extension after_remove hooks

**Decision**: Add hook execution to `remove_extension()` mirroring `install_extension()` pattern.

**Rationale**: `install_extension()` (extensions.py:308-319) reads `hooks.after_install` from registry and executes commands. `remove_extension()` (extensions.py:379) removes files and updates registry but never reads or executes `hooks.after_remove`. The `target_entry` dict (retrieved at line 402) already contains hook data stored during install (line 301).

**Alternatives considered**: None — this is a clear missing feature matching the existing install pattern.

## R9: permissions-bypass.json status

**Decision**: File does not exist on disk. The git status entry was stale. No action needed.

**Rationale**: `config/` contains only: mcp-permissions.json, permissions-full.json, permissions-minimal.json, permissions-standard.json. The `?? config/permissions-bypass.json` entry in git status was a snapshot artifact. FR-028 can be closed as resolved.

**Alternatives considered**: N/A.

## R10: Configure without init guard

**Decision**: Add `.dotnet-ai-kit/` existence check at start of `configure()`.

**Rationale**: `configure()` (cli.py:1153) creates `.dotnet-ai-kit/config.yml` directory via `mkdir(parents=True, exist_ok=True)` (line 1387) but never checks if `init` was run first. This creates a half-state: config exists but no version.txt, no commands, no rules, no skills, no agents.

**Alternatives considered**: (a) Auto-run init from configure — rejected, init has interactive prompts and different flags. (b) Warning but continue — rejected, the half-state is harmful.
