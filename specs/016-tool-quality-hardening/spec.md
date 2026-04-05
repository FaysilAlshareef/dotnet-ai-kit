# Feature Specification: Tool-Wide Quality Hardening

**Feature Branch**: `016-tool-quality-hardening`
**Created**: 2026-04-04
**Status**: Draft
**Input**: User description: "Tool-Wide Quality Fixes, UX Lifecycle Hardening, and Command Consistency — 8-part feature covering build packaging fixes, command branch safety, CLI lifecycle gaps, config error handling, command file quality, deployment pipeline completeness, skill activation coverage, and extension system fixes."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Production Install Works End-to-End (Priority: P1)

A developer installs dotnet-ai-kit via `pip install` (from wheel) and runs `dotnet-ai init --type command --ai claude`. The tool deploys commands, rules, skills, agents, the architecture profile, and the enforcement hook — all in one step. No additional commands are needed for full enforcement to be active.

**Why this priority**: Without bundled profiles/prompts in the wheel, production installs silently fail to deploy architecture enforcement. This is the most critical blocker — users on pip-installed versions get zero value from profile and hook features.

**Independent Test**: Install from built wheel, run `init --type command --ai claude`, verify `architecture-profile.md` and PreToolUse hook exist.

**Acceptance Scenarios**:

1. **Given** a wheel built with `python -m build`, **When** a user installs via `pip install` and runs `dotnet-ai init --type command --ai claude`, **Then** `.claude/rules/architecture-profile.md` exists with command-pattern constraints and `.claude/settings.json` contains a PreToolUse hook with `_source: "dotnet-ai-kit-arch"`.
2. **Given** a wheel built with `python -m build`, **When** inspecting the wheel contents, **Then** `dotnet_ai_kit/bundled/profiles/` contains all 12 profile subdirectories and `dotnet_ai_kit/bundled/prompts/` contains the hook prompt template.

---

### User Story 2 - Secondary Repo Branch Safety (Priority: P1)

A developer working in a multi-repo microservice solution runs any SDD lifecycle command that touches secondary repos (specify, clarify, plan, tasks, implement). Each command checks the current branch in each secondary repo before committing — never commits directly to main, master, or develop. If a feature branch does not exist, the command creates one following the `chore/brief-{NNN}-{name}` pattern.

**Why this priority**: Direct commits to protected branches in secondary repos can break CI/CD pipelines and violate team policies. All 5 commands that touch secondary repos must have consistent branch safety.

**Independent Test**: Run `/dai.clarify` with linked secondary repos on the `main` branch; verify a feature branch is created before any commit.

**Acceptance Scenarios**:

1. **Given** a secondary repo with its current branch set to `main`, **When** the `clarify` command updates a feature brief, **Then** the command creates a `chore/brief-{NNN}-{name}` branch before committing and never commits to `main`.
2. **Given** a secondary repo with its current branch set to `develop`, **When** the `implement` command updates a feature brief, **Then** the command creates a feature branch before committing.
3. **Given** five commands (specify, clarify, plan, tasks, implement), **When** comparing their "Secondary Repo Branch Safety" sections, **Then** all five have identical branch safety rules.

---

### User Story 3 - CLI Lifecycle Completeness (Priority: P2)

A developer runs `dotnet-ai init --type command --ai claude`, then `dotnet-ai check`, then later `dotnet-ai configure`, and finally `dotnet-ai upgrade`. Each step in this lifecycle produces complete, accurate output and never silently drops errors.

**Why this priority**: The init-configure-check-upgrade lifecycle is the core UX of the tool. Gaps in this chain (init not deploying profiles, check not reporting hooks, configure not updating skills, upgrade hiding errors) degrade trust and make debugging difficult.

**Independent Test**: Run the full lifecycle and verify each command produces the expected output and file artifacts.

**Acceptance Scenarios**:

1. **Given** a fresh project, **When** running `dotnet-ai init --type command --ai claude`, **Then** architecture profile and enforcement hook are deployed alongside commands, rules, skills, and agents.
2. **Given** an initialized project, **When** running `dotnet-ai check`, **Then** the output includes profile status, hook status, skills count, agents count, linked repos summary, linked_from, and detected_paths.
3. **Given** an initialized project, **When** running `dotnet-ai check --json`, **Then** the JSON output includes the same fields as the rich table output.
4. **Given** a corrupted `config.yml` with invalid YAML, **When** running any CLI command, **Then** the error message reads "Invalid YAML syntax in .dotnet-ai-kit/config.yml: ..." instead of a raw Python traceback.
5. **Given** a project where profile deployment fails during upgrade, **When** the user runs `dotnet-ai upgrade`, **Then** a yellow warning message appears with an actionable suggestion.
6. **Given** a project with no `.dotnet-ai-kit/` directory, **When** running `dotnet-ai configure`, **Then** the tool displays "dotnet-ai-kit is not initialized. Run 'dotnet-ai init' first" and exits with code 1. *(Also tested in User Story 6, scenario 3 — implemented once in US6.)*

---

### User Story 4 - Command File Quality and Consistency (Priority: P2)

A developer using the SDD lifecycle commands finds that artifact ownership is clear (each artifact is generated by exactly one command), step ordering is logical, flags are unambiguous, and short aliases match deployed filenames.

**Why this priority**: Ambiguous command behavior (phantom artifacts, duplicate flags, wrong step order) causes developer confusion and reduces trust in the AI-guided workflow.

**Independent Test**: Verify `plan.md` generates `event-flow.md`, all 9 code-gen commands have distinct `--dry-run` and `--list` flags, and deployed short-alias filenames match CLAUDE.md documentation.

**Acceptance Scenarios**:

1. **Given** a microservice project, **When** running `/dai.plan`, **Then** the plan step generates `event-flow.md` with inter-service event contracts.
2. **Given** any of the 9 code-gen commands, **When** reading the flags table, **Then** `--dry-run` and `--list` are two distinct flags with different descriptions.
3. **Given** `specify.md`, **When** reading the execution steps, **Then** steps appear in sequential order: gather context, analyze, produce spec, project feature briefs, quality checklist, write output.
4. **Given** `command_style: both` configuration, **When** running `dotnet-ai init --ai claude`, **Then** short-alias files like `dai.spec.md`, `dai.check.md`, `dai.go.md` are deployed matching CLAUDE.md documentation.
5. **Given** the `do.md` orchestrator, **When** reading artifact ownership, **Then** `service-map.md` is attributed to the specify step and `event-flow.md` is attributed to the plan step.

---

### User Story 5 - Full Deployment Pipeline (Priority: P3)

A developer runs `dotnet-ai configure` after upgrading the CLI and expects all deployed assets (commands, rules, skills, agents, profiles, hooks) to be refreshed. When deploying to linked repos, each secondary repo uses its own command style and all tool-specific directories are staged for commit.

**Why this priority**: Incomplete re-deployment during configure leaves stale assets. Wrong command style in secondary repos and unstaged directories cause inconsistencies across multi-repo solutions.

**Independent Test**: Run `configure` and verify rules, skills, and agents are re-deployed; deploy to a secondary repo with Cursor configured and verify `.cursor/` changes are staged.

**Acceptance Scenarios**:

1. **Given** an initialized project with updated skills, **When** running `dotnet-ai configure`, **Then** rules, skills, and agents are re-deployed (not just commands).
2. **Given** a primary repo with `command_style: full` and a secondary repo with `command_style: short`, **When** deploying to linked repos, **Then** the secondary repo gets short-style commands.
3. **Given** a secondary repo configured for Cursor, **When** deploying via `deploy_to_linked_repos()`, **Then** the `git add` command stages `.cursor/` directories alongside `.dotnet-ai-kit/`.

---

### User Story 6 - Config and Model Robustness (Priority: P3)

A developer's configuration is validated and preserved reliably — template fields that are declared are kept, unknown `detected_paths` keys trigger warnings, and running `configure` without `init` is blocked.

**Why this priority**: Silent data loss (integrations dropped) and silent key mismatches (detected_paths) create hard-to-diagnose issues.

**Independent Test**: Edit config-template.yml, run configure, and verify no fields are silently dropped.

**Acceptance Scenarios**:

1. **Given** `config-template.yml`, **When** a user fills in all sections, **Then** no fields are silently dropped when the config is saved (undeclared sections are removed from the template).
2. **Given** a `project.yml` with `detected_paths: {aggr: "src/Core"}`, **When** loading the project, **Then** a warning log appears: "Unknown detected_paths key: aggr".
3. **Given** no `.dotnet-ai-kit/` directory, **When** running `dotnet-ai configure`, **Then** the tool shows "dotnet-ai-kit is not initialized" and exits with code 1.

---

### User Story 7 - Skill Auto-Activation Coverage (Priority: P3)

A developer working on a .NET project benefits from context-aware skill activation — skills automatically engage when the developer is working in relevant file paths or performing relevant tasks. At least 67% of skills have behavioral triggers and path-relevant skills have file path tokens.

**Why this priority**: With only 9% of skills having `when-to-use` and 2.5% having `paths`, the auto-activation system delivers minimal value. Expanding coverage makes the AI assistant significantly more context-aware.

**Independent Test**: Count skills with `when-to-use` frontmatter (target: 80+) and `paths` tokens (target: 9+).

**Acceptance Scenarios**:

1. **Given** the 120 skill files, **When** counting files with `when-to-use` frontmatter, **Then** at least 80 have it.
2. **Given** the 120 skill files, **When** counting files with `paths` tokens using `${detected_paths.*}`, **Then** at least 9 have them.
3. **Given** any skill file, **When** counting lines, **Then** all remain under 400 lines.
4. **Given** skills with `when-to-use`, **When** reading the text, **Then** phrasing follows consistent patterns: "When creating or modifying ...", "When configuring ...", "When writing ...".

---

### User Story 8 - Extension Cleanup and Init Friction (Priority: P4)

A developer uninstalling an extension sees cleanup hooks execute. A new user running `dotnet-ai init` without `--ai` is auto-defaulted to Claude instead of seeing an error. Untracked config files are resolved.

**Why this priority**: These are quality-of-life improvements that reduce friction. Lower priority because they affect edge cases, not the primary workflow.

**Independent Test**: Install an extension with `after_remove` hooks, then remove it and verify hooks run. Run `dotnet-ai init` without `--ai` and verify Claude is auto-selected.

**Acceptance Scenarios**:

1. **Given** an installed extension with `after_remove` hooks, **When** running `dotnet-ai extension-remove <name>`, **Then** the after_remove hooks execute.
2. **Given** a fresh project with no `.claude/` directory, **When** running `dotnet-ai init` without `--ai`, **Then** the tool auto-defaults to Claude with an info message.
3. **Given** `config/permissions-bypass.json` as an untracked file, **When** resolving its status, **Then** it is either committed to git or removed.

---

### Edge Cases

- What happens when a secondary repo has no `config.yml` during `deploy_to_linked_repos()`? Falls back to `command_style: "both"`.
- What happens when `init` is run with `--type` but the profile source file is missing? Raises `FileNotFoundError` with a clear message.
- What happens when `configure` is run in a project initialized by an older CLI version that has no `detected_paths`? The check command gracefully reports "not set" for detected_paths fields.
- What happens when a skill's `when-to-use` text exceeds the 400-line budget when added? The `when-to-use` is kept concise (1 line) so this never pushes a skill over budget.
- What happens when `upgrade` encounters a secondary repo with uncommitted changes? The `git add` and `git commit` operate only on the tool-managed directories; the dirty working directory check in branch safety prevents commits.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Build system MUST bundle `profiles/` directory into wheel at `dotnet_ai_kit/bundled/profiles/` with all 12 profile subdirectories
- **FR-002**: Build system MUST bundle `prompts/` directory into wheel at `dotnet_ai_kit/bundled/prompts/`
- **FR-003**: `clarify.md` MUST include "Secondary Repo Branch Safety" section with identical rules to `specify.md`
- **FR-004**: `implement.md` MUST include "Secondary Repo Branch Safety" section with identical rules to `specify.md`
- **FR-005**: Both `clarify.md` and `implement.md` MUST remain under 200 lines after the addition
- **FR-006**: `init` command MUST deploy architecture profile when project type is known (via `--type` flag or existing `project.yml`)
- **FR-007**: `init` command MUST deploy enforcement hook for Claude when project type is known
- **FR-008**: `check` command MUST report architecture profile status, enforcement hook status, skills count, agents count, linked repos summary, linked_from, and detected_paths
- **FR-009**: `check --json` MUST include all fields from FR-008 in JSON output
- **FR-010**: Config loader MUST catch YAML syntax errors and produce a user-friendly message instead of a raw traceback
- **FR-011**: `upgrade` command MUST display warning messages when profile, hook, or multi-repo deployment fails instead of silently swallowing errors
- **FR-012**: `plan.md` MUST include explicit instructions to generate `event-flow.md` for microservice mode projects
- **FR-013**: The 9 code-gen commands MUST have distinct `--dry-run` and `--list` flags with different descriptions
- **FR-014**: `specify.md` execution steps MUST appear in correct sequential order (briefs before quality checklist)
- **FR-015**: `do.md` MUST clearly assign `service-map.md` ownership to the specify step and `event-flow.md` to the plan step
- **FR-016**: Short-alias command filenames MUST match CLAUDE.md documentation (e.g., `dai.spec.md`, `dai.check.md`, `dai.go.md`)
- **FR-017**: `configure` command MUST re-deploy rules, skills, and agents in addition to commands, profiles, and hooks
- **FR-018**: `deploy_to_linked_repos()` MUST use each secondary repo's own `command_style` configuration
- **FR-019**: `deploy_to_linked_repos()` `git add` MUST stage all tool-specific directories, not just `.claude/`
- **FR-020**: Config template MUST NOT contain undeclared fields that are silently dropped by the model
- **FR-021**: `detected_paths` MUST warn on unknown keys while still accepting them for forward compatibility
- **FR-022**: `configure` command MUST block execution if `.dotnet-ai-kit/` directory does not exist
- **FR-023**: At least 80 of 120 skills MUST have `when-to-use` frontmatter
- **FR-024**: At least 9 skills MUST have `paths` tokens using `${detected_paths.*}`
- **FR-025**: All skills MUST remain under 400 lines
- **FR-026**: `remove_extension()` MUST execute `after_remove` hooks when they are defined
- **FR-027**: `init` command MUST auto-default to Claude when no AI tool is detected and no `--ai` flag is provided
- **FR-028**: ~~`config/permissions-bypass.json` MUST be either committed or removed from the repository~~ *Pre-resolved: file does not exist on disk (research R9). No action needed.*

### Key Entities

- **Architecture Profile**: Per-project-type constraint file (12 variants) deployed to AI tool rules directories. Key attributes: project type, constraints list, line count (max 100).
- **Enforcement Hook**: PreToolUse prompt hook in `.claude/settings.json` that validates Write/Edit operations against profile constraints. Key attributes: model, timeout, matcher, _source tag.
- **Command File**: Slash command template (27 total) with flags, steps, and artifact references. Key attributes: line count (max 200), flags table, artifact inputs/outputs, branch safety section.
- **Skill File**: Specialist knowledge document (120 total) with optional auto-activation frontmatter. Key attributes: `when-to-use` trigger, `paths` token, `alwaysApply` flag, line count (max 400).
- **Linked Repo Config**: Secondary repository configuration within `repos` section of `config.yml`. Key attributes: local path, AI tools list, command style, version state.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of production installs (from wheel) successfully deploy architecture profiles and hooks — zero silent failures due to missing bundled files
- **SC-002**: All 5 SDD commands that touch secondary repos (specify, clarify, plan, tasks, implement) enforce branch safety before any commit, preventing direct commits to protected branches
- **SC-003**: `dotnet-ai check` provides a complete health report in under 5 seconds, covering all deployed features without requiring users to manually inspect file system
- **SC-004**: Zero raw Python tracebacks reach end users for config errors — all error conditions produce actionable, human-readable messages
- **SC-005**: At least 67% of skills (80 of 120) have behavioral auto-activation triggers, up from 9%
- **SC-006**: At least 9 skills have path-based activation tokens, up from 3
- **SC-007**: All 9 code-gen commands have unambiguous flag tables with zero duplicate flag names
- **SC-008**: Short-alias command filenames match documented aliases in 100% of cases (10 alias mappings)
- **SC-009**: `configure` re-deploys the complete tooling stack (commands + rules + skills + agents + profiles + hooks), eliminating stale-asset scenarios
- **SC-010**: Secondary repos receive their own command style during multi-repo deployment, not the primary's style

## Assumptions

- Claude Code remains the only fully supported AI tool in v1.0; Cursor has partial support (rules/commands only), Copilot and Codex have no rules directory support
- The `permissions-bypass.json` file is a valid permission template intended for commit (not work-in-progress)
- Skills that have `alwaysApply: true` do not need `when-to-use` since they load unconditionally
- The `event-flow.md` artifact format is: event name, producer service, consumer service, payload schema
- Forward compatibility for `detected_paths` means unknown keys are accepted with a warning, not rejected
- The integrations section in config-template.yml is removed (option b) rather than adding model support, since integrations are not yet implemented

## Scope Boundaries

**In scope**: All issues from `specs/015-arch-enforcement-multi-repo/tool-review.md` at CRITICAL, HIGH, and MEDIUM severity, plus selected LOW issues (L1, L2, L4, P1). Each part is independently valuable and testable.

**Out of scope**:
- Catalog extension install (E1 — requires registry infrastructure)
- Uninstall/reset command (L5 — new feature, not a fix)
- Rollback on partial multi-repo failure (D4 — complex git operations requiring transaction semantics)
- `linked_from` reverse validation (M4 — requires cross-repo coordination)
- `$ARGUMENTS` addition to 7 commands (C8 — changes command input semantics)
- Agent frontmatter `context`/`agent` body mismatch (C6 — Claude Code framework behavior, not a bug)
- `specify.md` and `tasks.md` at 200-line limit (C9 — cosmetic, no functional impact)

## Dependencies

- This feature depends on `015-arch-enforcement-multi-repo` being merged first, as it fixes issues introduced and discovered during that feature's review
- No external service dependencies — all fixes are to local CLI tool, command files, and build configuration
