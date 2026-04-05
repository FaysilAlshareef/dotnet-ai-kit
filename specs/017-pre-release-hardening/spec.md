# Feature Specification: Pre-Release v1.0.0 Hardening

**Feature Branch**: `017-pre-release-hardening`
**Created**: 2026-04-04
**Status**: Draft
**Input**: Full tool review (37 issues) + 18 planning/ doc gap scan

---

## Overview

Final quality hardening sprint before tagging v1.0.0. Three categories:
1. **Tool-review findings** — issues from `specs/016-tool-quality-hardening/tool-review.md`
2. **Planning gaps** — items in `planning/` docs never built
3. **Command UX debt** — 14 of 27 commands missing `## Usage` + examples

---

## Clarifications

### Session 2026-04-04

- Q: Should `parse_version("1.0.0-beta")` equal or differ from `parse_version("1.0.0")`? → A: Equal — both return `(1, 0, 0)` after pre-release suffix is stripped. Edge case corrected from "must not compare equal" to "must not compare GREATER THAN" (the original bug produced `(1,0,0,0)` which was greater).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Developer types a documented short alias and it works (Priority: P1)

A developer reads `CLAUDE.md`, sees `/dai.config`, `/dai.crud`, `/dai.page` listed as valid commands, types them in Claude Code, and the command executes. Currently these three are missing from `COMMAND_SHORT_ALIASES` so the deployed files are named `dai.configure.md`, `dai.add-crud.md`, `dai.add-page.md` — none of which are valid slash commands.

**Why this priority**: Broken aliases ship to every user on first install. The mismatch between documentation and deployed files is the most visible bug at v1.0.0.

**Independent Test**: Run `dotnet-ai init --ai claude` in a .NET project, verify `dai.config.md`, `dai.crud.md`, `dai.page.md` all exist in `.claude/commands/`.

**Acceptance Scenarios**:

1. **Given** `COMMAND_SHORT_ALIASES` in `copier.py`, **When** inspected, **Then** it contains `"configure": "config"`, `"add-crud": "crud"`, `"add-page": "page"` and has 13 total entries.
2. **Given** `copy_commands()` called with style `"short"` or `"both"`, **When** it completes, **Then** files `dai.config.md`, `dai.crud.md`, `dai.page.md` are present; `dai.configure.md`, `dai.add-crud.md`, `dai.add-page.md` are absent.

---

### User Story 2 — Developer installs extension by name and gets a clear message (Priority: P1)

A developer runs `dotnet-ai extension-add jira` (no `--dev`) as shown in planning/16-cli-implementation.md. Today this crashes with an unhandled `ExtensionError`. At v1.0.0 it must give a clear "not yet supported — use --dev" message.

**Why this priority**: An unhandled exception on a documented command pattern is a critical first-impression failure at release.

**Independent Test**: Run `dotnet-ai extension-add some-extension`, verify exit non-zero, output contains "not yet supported" and "--dev", no Python traceback visible.

**Acceptance Scenarios**:

1. **Given** `dotnet-ai extension-add jira` without `--dev`, **When** it executes, **Then** exit code is non-zero, output contains "not yet supported" and "--dev", no stack trace.

---

### User Story 3 — Maintainer updates hook model in one place (Priority: P1)

When Claude Haiku 4.6 releases, the maintainer updates `_HOOK_MODEL` in one constant and all users get the correct model on next `dotnet-ai upgrade`. Today the model ID is an inline string literal that must be hunted across the file.

**Why this priority**: A stale hardcoded model ID in deployed `settings.json` will cause hook invocations to fail silently when the old model is deprecated.

**Independent Test**: Grep `copy_hook()` for inline `"claude-haiku-*"` string — none found. Grep for `_HOOK_MODEL` — found at module level.

**Acceptance Scenarios**:

1. **Given** `copier.py`, **When** `copy_hook()` is inspected, **Then** model ID and timeout are referenced via `_HOOK_MODEL` and `_HOOK_TIMEOUT_MS` constants, no inline literals.

---

### User Story 4 — Developer opens any command and sees invocation syntax immediately (Priority: P2)

A developer opens `commands/analyze.md` or `commands/implement.md` and immediately sees how to invoke it and example use cases — matching the UX of code-gen commands like `add-aggregate.md`.

**Why this priority**: 14 of 27 commands are missing Usage and Examples — the majority of the SDD lifecycle commands. planning/04-commands-design.md defines Usage blocks for every command.

**Independent Test**: Check all 27 command files for `## Usage` — all 27 pass. Currently only 13 pass.

**Acceptance Scenarios**:

1. **Given** `commands/analyze.md`, **When** opened, **Then** a `## Usage` block and `**Examples:**` block appear before the first `## Step` section.
2. **Given** all 27 command files, **When** each is checked for `## Usage` and `**Examples:**`, **Then** all 27 contain both sections.
3. **Given** `commands/specify.md` and `commands/tasks.md` (at 200-line limit), **When** Usage+Examples are added, **Then** each file remains ≤ 200 lines (trim internal steps to make room).

---

### User Story 5 — Developer typo in config.yml is warned about (Priority: P2)

A developer writes `permisions_level: full` (typo) in `config.yml`. The tool logs a warning naming the unknown key rather than silently discarding it.

**Why this priority**: Silent field drops make configuration failures nearly impossible to debug.

**Independent Test**: Load config with `foo: bar` at top level, verify WARNING log containing "foo".

**Acceptance Scenarios**:

1. **Given** a config.yml with unknown top-level key `foo`, **When** `load_config()` is called, **Then** a WARNING is logged naming `foo`.
2. **Given** the same config, **When** the returned object is inspected, **Then** known fields are correctly loaded.

---

### User Story 6 — Secondary repo with cursor gets cursor files deployed (Priority: P2)

A secondary repo configured with `ai_tools: [cursor]` receives cursor rules in `.cursor/rules/`, not Claude files in `.claude/`.

**Why this priority**: The deployment loop bug means every secondary repo receives the primary's AI tool configuration — a semantic correctness failure for multi-repo setups.

**Independent Test**: Configure primary=`claude`, secondary=`cursor`; run `deploy_to_linked_repos()`; verify `.cursor/rules/` populated in secondary, `.claude/commands/` absent.

**Acceptance Scenarios**:

1. **Given** primary has `ai_tools: [claude]` and secondary has `ai_tools: [cursor]`, **When** `deploy_to_linked_repos()` runs, **Then** secondary receives cursor-format files not claude-format files.

---

### User Story 7 — upgrade --force refreshes profile and hook (Priority: P2)

A developer upgrades dotnet-ai-kit (architecture profile changed). They run `dotnet-ai upgrade --force`. Profile and hook are re-deployed even if the version file says current.

**Acceptance Scenarios**:

1. **Given** `force=True` and `project.yml` exists, **When** `upgrade --force` runs, **Then** `copy_profile()` and `copy_hook()` are called regardless of version match.

---

### User Story 8 — CI gets bypassPermissions warning in JSON output (Priority: P2)

A CI pipeline runs `dotnet-ai configure --no-input --company Acme --permissions full --json`. The JSON output includes a `"warnings"` field documenting that `bypassPermissions` is active.

**Acceptance Scenarios**:

1. **Given** `configure --json` with `permissions_level = "full"`, **When** it completes, **Then** JSON contains `"warnings": ["bypassPermissions enabled — all operations run without confirmation"]`.

---

### User Story 9 — Config file survives a process kill (Priority: P3)

If the process is killed while writing `config.yml`, the file is never left truncated.

**Acceptance Scenarios**:

1. **Given** `save_config()` completes successfully, **When** the directory is checked, **Then** no `.tmp` file remains.
2. **Given** the implementation, **When** inspected, **Then** it writes to a `.tmp` file and calls `Path.replace()`.

---

### User Story 10 — Developer runs dotnet-ai changelog after upgrade (Priority: P3)

planning/12-version-roadmap.md shows `dotnet-ai changelog` in the upgrade workflow. It exists, exits 0, prints something meaningful.

**Acceptance Scenarios**:

1. **Given** dotnet-ai-kit installed, **When** `dotnet-ai changelog` runs, **Then** exit code 0 and output is non-empty.

---

### User Story 11 — Developer initializes with permissions in one step (Priority: P3)

CI runs `dotnet-ai init --ai claude --permissions standard` without a separate `configure` call. planning/16-cli-implementation.md documents this flag.

**Acceptance Scenarios**:

1. **Given** `dotnet-ai init --ai claude --permissions standard`, **When** complete, **Then** `.claude/settings.json` has the standard allow-list applied.
2. **Given** `--permissions extreme` (invalid), **When** init runs, **Then** clear error message, non-zero exit.

---

### Edge Cases

- `configure --dry-run` in uninitialised directory must NOT exit code 1 — preview or warn and continue.
- `extension-list` with zero extensions must print a non-empty help message.
- Two extensions with same rule filename must conflict at install time of the second.
- `after_remove` hook failures must raise `ExtensionError`, not just log a warning.
- `parse_version("1.0.0-beta")` must not compare GREATER THAN `parse_version("1.0.0")` — after stripping the pre-release suffix both return `(1, 0, 0)` and compare equal. The old bug produced `(1, 0, 0, 0)` (greater), which was wrong.
- `check --verbose` must show more detail than normal mode for Profile/Hook.
- `get_agent_config("cursor")` must log a warning (v1.0 unsupported), not silently return.
- Both workflow skills without `category:` must be findable by category reporting after fix.
- `rules/multi-repo.md` must be ≤ 100 lines with MUST/MUST NOT language.
- `utils.py` `parse_version()` must be the sole implementation used by both copier.py and extensions.py.

---

## Requirements *(mandatory)*

### Functional Requirements

**H1 — Broken aliases**

- **FR-001**: `COMMAND_SHORT_ALIASES` in `copier.py` MUST contain `"configure": "config"`, `"add-crud": "crud"`, `"add-page": "page"` (13 total entries).
- **FR-002**: `copy_commands()` with style `"short"` or `"both"` MUST generate `dai.config.md`, `dai.crud.md`, `dai.page.md`.

**H2 — Hook constants**

- **FR-003**: `copier.py` MUST define `_HOOK_MODEL` and `_HOOK_TIMEOUT_MS` at module level with a comment noting when to update them.
- **FR-004**: `copy_hook()` MUST use `_HOOK_MODEL` and `_HOOK_TIMEOUT_MS`; no inline string/int literals for model or timeout.

**H3 — Extension catalog UX**

- **FR-005**: `install_extension()` without `--dev` MUST raise a user-friendly error containing "not yet supported" and "--dev"; no `ExtensionError` traceback.

**M1 — Command Usage sections**

- **FR-006**: All 27 command markdown files MUST contain `## Usage` and `**Examples:**` blocks before their first step section.
- **FR-007**: All command files MUST remain ≤ 200 lines after changes.

**M2 — Config key validation**

- **FR-008**: `DotnetAiConfig` MUST log a WARNING for any unrecognised top-level key via `model_validator(mode="before")`. Known keys: `version`, `company`, `naming`, `repos`, `permissions_level`, `ai_tools`, `command_style`, `linked_from`.
- **FR-009**: Unknown keys MUST NOT prevent valid fields from loading (`extra="ignore"` retained).

**M3 — Shared version parsing**

- **FR-010**: `src/dotnet_ai_kit/utils.py` MUST exist and export `parse_version(version_str: str) -> tuple[int, ...]`.
- **FR-011**: `copier.py` and `extensions.py` MUST import `parse_version` from `utils.py`; private copies `_parse_version` and `_parse_version_tuple` MUST be removed.
- **FR-012**: `parse_version()` MUST strip pre-release suffixes (`-beta`, `-rc1`, etc.) before parsing numeric parts.

**M4 — Skills token logging**

- **FR-013**: `_resolve_detected_path_tokens()` MUST call `logger.debug(...)` before removing any `paths:` line whose token resolves to empty string.

**M5 — Secondary repo deployment loop**

- **FR-014**: The inner tool loop in `deploy_to_linked_repos()` MUST iterate `sec_ai_tools` (secondary's tools), not `config.ai_tools` (primary's tools).

**M6 — Unsupported tool warning**

- **FR-015**: `get_agent_config()` MUST log a WARNING when the tool is in `AGENT_CONFIG` but not in `SUPPORTED_AI_TOOLS`. MUST NOT raise.

**M7 — Extension hook consistency**

- **FR-016**: `after_remove` hook failures MUST raise `ExtensionError`, consistent with `after_install` behaviour.

**M8 — Extension rule conflict detection**

- **FR-017**: `_check_conflicts()` MUST detect rule file name collisions between extensions and raise `ExtensionError` on conflict.

**M9 — Skill category fields**

- **FR-018**: `skills/workflow/plan-artifacts/SKILL.md` and `skills/workflow/plan-templates/SKILL.md` MUST have `category: workflow` in their `metadata:` block.

**M10 — check --verbose enrichment**

- **FR-019**: `check --verbose` MUST print the profile file path and hook model/timeout after the table for each tool where Profile or Hook is "deployed".

**L1 — configure --dry-run guard**

- **FR-020**: `configure --dry-run` MUST NOT exit code 1 in an uninitialised directory; it MUST warn and continue showing a preview.

**L2 — upgrade --force profile/hook**

- **FR-021**: `upgrade --force` MUST unconditionally run profile and hook re-deployment, bypassing the version comparison guard.

**L3 — extension-list empty state**

- **FR-022**: `extension-list` with no extensions MUST print a non-empty message mentioning `--dev`.

**L4 — bypassPermissions in JSON**

- **FR-023**: `configure --json` with `permissions_level = "full"` MUST include `"warnings": [...]` in JSON output.

**L5 — Atomic config writes**

- **FR-024**: `save_config()` and `save_project()` MUST use atomic write pattern (write `.tmp`, then `Path.replace()`).

**L6 — Verbose except blocks**

- **FR-025**: Each of the 5 `except Exception: pass` blocks in `cli.py` MUST call `_verbose_log(verbose, ...)` surfacing the skip reason.

**L7 — Pre-release version parsing**

- **FR-026**: `parse_version("1.0.0-beta")` MUST return `(1, 0, 0)` — equal to stable `1.0.0` parsed, not containing a `0` for the beta suffix treated as a fourth part.

**P1 — --permissions flag on init**

- **FR-027**: `init()` MUST accept optional `--permissions` flag (`minimal`, `standard`, `full`). If provided, the level MUST be applied during init without a separate `configure` call. Invalid values MUST produce a clear error.

**P2 — changelog command**

- **FR-028**: `@app.command("changelog")` MUST be registered in `cli.py`. It MUST exit 0 and print `CHANGELOG.md` content (if found in package dir) or the 5 most recent git tags with dates.

**P3 — multi-repo rule**

- **FR-029**: `rules/multi-repo.md` MUST exist, be ≤ 100 lines, use MUST/MUST NOT enforcement language, and cover: event contract ownership, branch naming (`chore/brief-NNN-name`), deploy order (command → processor → query → gateway), and prohibition on cross-repo circular dependencies.

**P4 — planning/ docs, README, and CHANGELOG sync**

A full gap analysis (`specs/017-pre-release-hardening/docs-gap-analysis.md`) identified that specs 015, 016, and current 017 added major features never documented in planning/ or user-facing docs. The following must be updated before v1.0.0 release.

**README.md (user-facing — HIGH priority)**

- **FR-030**: README badge line MUST update: `15 rules` → `16 rules` (after multi-repo.md); template count note corrected.
- **FR-031**: README rules section MUST show all 15 rules (currently shows 9) and note 16 after spec-017.
- **FR-032**: README skill category table MUST be corrected: api:11 (not 7), core:12 (not 7), workflow:5 (not 7), architecture:7 (not 6), security:5 (not 3).
- **FR-033**: README test count MUST update from 158 to 280 (295+ after spec-017 tests added).
- **FR-034**: README extension commands MUST use `dotnet-ai extension-add --dev` (not `dotnet-ai extension install`); catalog note MUST say "shows a user-friendly message" not imply catalog works.
- **FR-035**: README structure section MUST update rule count from 15 to 16.

**CHANGELOG.md (user-facing — HIGH priority)**

- **FR-036**: CHANGELOG test count MUST update from "158 test functions across 6 test files" to "280 tests across 13 test files".
- **FR-037**: CHANGELOG MUST add entries for all spec-015 additions: architecture enforcement, `copy_profile()`, `copy_hook()`, `deploy_to_linked_repos()`, `linked_from` config field, `FeatureBrief` model, branch safety sections in 5 commands, secondary repo command_style awareness.
- **FR-038**: CHANGELOG MUST add entries for all spec-016 additions: `check` table now shows Skills/Agents/Profile/Hook columns, configure guard (exit 1 if no init), configure re-deploys rules/skills/agents, `_get_tool_status()` helper, `after_remove` hook execution, `detected_paths` unknown key validator, `COMMAND_SHORT_ALIASES` alias fixes, `--list` flag disambiguation in code-gen commands.
- **FR-039**: CHANGELOG MUST add entries for all spec-017 additions: `utils.py` + `parse_version()`, `CatalogInstallError` (friendly message), `multi-repo.md` rule, `dotnet-ai changelog`, `init --permissions`, atomic config writes, verbose except blocks, configure dry-run guard, upgrade --force profile/hook, extension-list empty state, bypassPermissions in JSON, check --verbose enrichment, rule name conflict detection, DotnetAiConfig unknown key warning, 14 command Usage+Examples blocks, 2 skill category fields.
- **FR-040**: CHANGELOG extension command names MUST use `extension-add`/`extension-remove`/`extension-list` (hyphenated, matching actual CLI).
- **FR-041**: CHANGELOG Known Limitations MUST update: "Extension catalog install" → "Catalog installs show a user-friendly error with --dev guidance instead of crashing".

**planning/ docs (architecture reference — MEDIUM priority)**

- **FR-042**: `planning/05-rules-design.md` MUST update rule count from 15 to 16 and list `multi-repo.md` as rule #16.
- **FR-043**: `planning/06-build-roadmap.md` MUST mark all 15 v1.0 phases status as `Complete` (currently all show `Planned`); Phase 1.2 rule count must update from 6 to 16.
- **FR-044**: `planning/07-project-structure.md` MUST update `src/dotnet_ai_kit/` tree to show all 9 files (currently shows 3); add `utils.py` (10 after spec-017); update rules list from 6 to 16; update test file count from 6 to 13.
- **FR-045**: `planning/08-multi-repo-orchestration.md` MUST document the tooling deploy system: `deploy_to_linked_repos()`, architecture profile deployment, PreToolUse enforcement hook, `linked_from` field, `FeatureBrief` cross-repo projection, branch naming `chore/brief-NNN-name`, secondary repo ai_tools awareness, dirty working directory check.
- **FR-046**: `planning/10-permissions-config.md` MUST update config key from `permissions.level` to `permissions_level` (flat) to match the actual pydantic model.
- **FR-047**: `planning/12-version-roadmap.md` MUST: mark all v1.0 phases `Complete`, add spec-015/016/017 to v1.0 Late Additions, document `dotnet-ai changelog` command, document `init --permissions` flag, update template count from "11 scaffolds" to 13 scaffold dirs.
- **FR-048**: `planning/16-cli-implementation.md` MUST: (a) update `src/` tree to show all source files including `utils.py`; (b) remove `integrations: coderabbit:` from config schema (deferred); (c) fix `permissions.level` → `permissions_level`; (d) add `linked_from` to config schema; (e) update extension command names to hyphenated format; (f) update `dotnet-ai check` output to show Skills/Agents/Profile/Hook columns and linked repos; (g) update `dotnet-ai init` output to show skills/agents/profile copy; (h) fix error table ("AI tool not detected" → now auto-defaults to claude); (i) document `init --permissions` flag; (j) document `dotnet-ai changelog` command; (k) update COMMAND_SHORT_ALIASES to 13 entries; (l) document configure guard and re-deploy behavior.
- **FR-049**: `planning/04-commands-design.md` MUST update COMMAND_SHORT_ALIASES code sample (if any) to show 13 entries.
- **FR-050**: `planning/13-handoff-schemas.md` MUST add `feature-brief.md` schema (FeatureBrief model written to secondary repos during specify).

### Key Entities

- **`COMMAND_SHORT_ALIASES`** (`copier.py`): dict mapping command stem → short alias; 13 entries after fix.
- **`_HOOK_MODEL` / `_HOOK_TIMEOUT_MS`** (`copier.py`): Named constants for hook config; update-point for new models.
- **`parse_version()`** (`utils.py`): Shared version parsing utility; sole implementation across the codebase.
- **`DotnetAiConfig.model_validator`** (`models.py`): Pre-validator warning on unknown top-level keys.
- **`rules/multi-repo.md`**: New always-loaded rule for multi-repo coordination.
- **`dotnet-ai changelog`**: New CLI command in `cli.py`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 27 slash commands have working short aliases matching `CLAUDE.md` — `grep -L "## Usage" commands/*.md` returns empty.
- **SC-002**: `dotnet-ai extension-add <name>` without `--dev` exits non-zero with user-readable message on all platforms — no tracebacks.
- **SC-003**: All 27 command files contain `## Usage` and `**Examples:**` — verified by automated grep check.
- **SC-004**: `parse_version()` exists in exactly one file (`utils.py`); `_parse_version` and `_parse_version_tuple` are absent from copier.py and extensions.py.
- **SC-005**: Test count increases from 280 to ≥ 295 with 0 regressions.
- **SC-006**: `ruff check src/ tests/` and `ruff format --check src/ tests/` pass with 0 errors.
- **SC-007**: A config.yml with a typo key produces a WARNING log entry naming the unknown key — verified by pytest caplog test.
- **SC-008**: `deploy_to_linked_repos()` deploys to secondary's own AI tool directories — verified by new pytest test.
- **SC-009**: `rules/multi-repo.md` exists and is ≤ 100 lines.
- **SC-010**: `dotnet-ai changelog` exits 0 — verified by CLI test.
- **SC-011**: README rule counts, skill table, test count, and extension commands corrected.
- **SC-012**: CHANGELOG entries added for specs 015/016/017; test count updated to 280+.
- **SC-013**: All 8 planning/ docs with HIGH/MEDIUM gaps updated (05, 06, 07, 08, 10, 12, 13, 16).

---

## Assumptions

- The 9 `alwaysApply: true` skills in `core/` are intentionally always-on; no audit required.
- `MOD-2/MOD-3` (confidence cross-validation, top_signals schema) have no known runtime impact and are deferred to v1.1.
- Cursor/Copilot `AGENT_FRONTMATTER_MAP` entries require v1.1 tool support — not in scope.
- `hooks/` omission from `force-include` is intentional (dev-only hooks).
- For `specify.md`/`tasks.md` (200-line limit), trim redundant sub-steps to create room for Usage+Examples.
- `changelog` command may have no `CHANGELOG.md` on first run; git tags fallback is acceptable.
- `configure --dry-run` without init should warn but continue, not silently succeed.
- `parse_version("1.0.0-beta")` should equal `parse_version("1.0.0")` (pre-release suffix stripped, not added as a 4th numeric part).

---

## Deferred (Out of Scope for 017)

| Item | Reason | Target |
|------|---------|--------|
| AGT-2: cursor/copilot AGENT_FRONTMATTER_MAP | Blocked on v1.1 tool support | v1.1 |
| MOD-2/3: confidence + top_signals validation | Low runtime impact | v1.1 |
| SKL-2: alwaysApply audit | 9 core skills correctly always-on | v1.1 |
| SKL-3/4: skill content expansion | Content work | v1.1 |
| CMD-3/4: 200-line budget (accept as-is) | Trim instead of exceed | v1.1 |
| COP-6: partial registration rollback | Complex, no incidents | v1.1 |
| PRF-1: hybrid profile reachability | Detection handles it | v1.1 |
| PKG-1: hooks/ in force-include | Dev-only hooks | v1.1 |
