# Feature Specification: Fix All 25 Identified Tool Issues

**Feature Branch**: `007-fix-tool-issues`
**Created**: 2026-03-23
**Status**: Draft
**Input**: User description: "Fix all 25 identified tool issues with suggested solutions. For issue 8 (agents never referenced), go with adding agent loading to commands approach."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tool Init Copies Skills and Agents (Priority: P1)

A developer runs `dotnet-ai init` (or the `/dai.init` slash command) on a new .NET project. After initialization, the project's `.claude/` directory contains not only commands and rules but also skills and agents, so that all slash commands have access to the specialist knowledge they need during code generation.

**Why this priority**: This is the root cause of the most impactful downstream issues. Without skills being available locally, commands like `/dai.implement` and `/dai.tasks` generate code without architectural guidance, leading to wrong patterns (e.g., `IConfiguration` instead of Options pattern, entities on command side).

**Independent Test**: Can be tested by running init on a fresh project and verifying that `.claude/skills/` and `.claude/agents/` directories exist with the correct files.

**Acceptance Scenarios**:

1. **Given** a .NET project without `.dotnet-ai-kit/` directory, **When** the user runs init, **Then** skills are copied to `.claude/skills/` preserving the category folder structure.
2. **Given** a .NET project without `.dotnet-ai-kit/` directory, **When** the user runs init, **Then** agents are copied to `.claude/agents/` as markdown files.
3. **Given** a project already initialized with a previous version, **When** the user runs `upgrade`, **Then** skills and agents are updated to the latest version without losing user customizations outside of those directories.
4. **Given** the init process fails partway through skill copying, **When** the error is raised, **Then** no partial skill files remain on disk.

---

### User Story 2 - Commands Enforce Correct Architectural Patterns (Priority: P1)

A developer uses `/dai.implement` or `/dai.tasks` on a microservice project. The tool always generates infrastructure code using the Options pattern (not raw `IConfiguration`), never creates entities or read models on the event-sourced command side, and loads the appropriate specialist agent for architectural guidance.

**Why this priority**: Directly prevents the real-world bugs found in production services: wrong DI patterns, anti-pattern entities on the command side, and missing architectural guardrails.

**Independent Test**: Can be tested by running `/dai.tasks` on a command-side microservice project and verifying no entity tasks are generated for the command side, and by inspecting `implement.md` to verify always-loaded skills and agent loading directives.

**Acceptance Scenarios**:

1. **Given** a microservice project with project_type "command", **When** `/dai.tasks` generates Phase 2 (Command Side), **Then** only aggregates, events, value objects, enums, and domain exceptions are generated. No entities, projections, or lookup tables.
2. **Given** any task that generates DI/infrastructure code, **When** `/dai.implement` executes, **Then** the configuration skill and dependency-injection skill are always loaded regardless of task type.
3. **Given** a command-side task, **When** `/dai.implement` executes, **Then** `agents/command-architect.md` is loaded for architectural guidance.
4. **Given** a query-side task, **When** `/dai.implement` executes, **Then** `agents/query-architect.md` is loaded for architectural guidance.
5. **Given** a processor task, **When** `/dai.implement` executes, **Then** `agents/processor-architect.md` is loaded for architectural guidance.

---

### User Story 3 - Config Template and Hooks Work Correctly (Priority: P2)

A developer generates a config file from the template or relies on the pre-commit hook. The config template produces valid YAML that passes pydantic validation, and the hook correctly detects all project files.

**Why this priority**: These are straightforward bugs that cause immediate failures for new users attempting to set up the tool.

**Independent Test**: Can be tested by generating a config from the template and loading it with pydantic, and by running the pre-commit hook on a project with both `.sln` and `.csproj` files.

**Acceptance Scenarios**:

1. **Given** the config template, **When** a user generates a config file from it, **Then** it loads successfully with `DotnetAiConfig` pydantic model without validation errors.
2. **Given** a project with `.sln` and `.csproj` files at various depths, **When** the pre-commit-lint hook runs, **Then** all project files within 3 levels are found regardless of OS.
3. **Given** the config template comments, **When** a user reads the supported AI tools, **Then** only actually supported tools are listed (currently: claude).

---

### User Story 4 - Feature Numbering and Cross-Repo Tracking (Priority: P2)

A developer uses `/dai.spec` to create a feature. Feature numbers always start at 001 when no prior features exist in the current repo. For multi-repo features, a lightweight spec-link file is created in each affected repo.

**Why this priority**: Prevents confusion with feature numbering gaps and ensures traceability across microservice repos.

**Independent Test**: Can be tested by running `/dai.spec` on a repo with no features and verifying it starts at 001, and by running `/dai.tasks` on a multi-repo feature and verifying spec-link files are created.

**Acceptance Scenarios**:

1. **Given** a repo with an empty `.dotnet-ai-kit/features/` directory, **When** `/dai.spec` is run, **Then** the feature is numbered 001 regardless of feature numbers in other repos.
2. **Given** a multi-repo feature spanning multiple service repos, **When** `/dai.tasks` generates tasks, **Then** a `spec-link.md` is created in each affected repo's features directory.
3. **Given** a `spec-link.md` in a secondary repo, **When** a developer reads it, **Then** it contains the feature name, source repo, and path to the primary spec.

---

### User Story 5 - Robust Extension and Template System (Priority: P3)

A developer installs an extension or uses template rendering. Failed extension installs are cleaned up, template rendering fails loudly on missing variables, and the extension registry is safe from concurrent corruption.

**Why this priority**: These are defensive improvements that prevent subtle data corruption and silent failures.

**Independent Test**: Can be tested by simulating a failed extension install and verifying no partial files remain, and by rendering a template with a missing variable and verifying an error is raised.

**Acceptance Scenarios**:

1. **Given** an extension install that fails after copying files but before registry update, **When** the error occurs, **Then** all copied files are cleaned up and no partial state remains.
2. **Given** a Jinja2 template with a placeholder and no matching context variable, **When** the template is rendered, **Then** a clear error is raised instead of a silent empty string.
3. **Given** two concurrent CLI invocations installing different extensions, **When** both write to the registry, **Then** neither corrupts the other's entry.

---

### User Story 6 - Missing Skills, Rules, and Documentation (Priority: P3)

The tool ships with a configuration rule, a testing rule, an error-handling skill, an event-versioning skill, and consistent documentation so that generated code follows best practices by default.

**Why this priority**: These are additive improvements that raise the quality floor for all generated code.

**Independent Test**: Can be tested by verifying each new rule/skill file exists, follows the token budget constraints, and contains the expected patterns.

**Acceptance Scenarios**:

1. **Given** the rules directory, **When** a developer lists rules, **Then** `configuration.md` and `testing.md` exist and are under 100 lines each.
2. **Given** the skills directory, **When** a developer lists skills, **Then** `skills/core/error-handling/SKILL.md` and `skills/microservice/command/event-versioning/SKILL.md` exist and are under 400 lines each.
3. **Given** all skills that reference `SaveChangesAsync`, **When** reviewed, **Then** all consistently pass `cancellationToken` as a parameter.
4. **Given** the `analyze.md` command, **When** reviewed, **Then** the `event-catalogue/` reference has been removed; event data is derived from code at runtime.

---

### Edge Cases

- What happens when init is run on a project that already has a `.claude/skills/` directory from a previous version? Skills should be overwritten with the latest version.
- What happens when a command references a skill file that doesn't exist on disk? The command should log a warning and continue without that skill's guidance rather than failing.
- What happens when two developers run `/dai.spec` simultaneously on the same repo? Feature numbering should be based on filesystem scan at execution time; the second invocation will see the first's directory and increment.
- What happens when the `hybrid` project type is selected but no microservice-specific templates exist for it? It should be treated as microservice mode with both command and query capabilities.
- What happens when `plan.md` checks for constitution file and it doesn't exist? The gate should be skipped with a warning, not cause a failure.

## Clarifications

### Session 2026-03-23

- Q: Should copied skills/agents be git-tracked or gitignored? → A: Git-tracked (committed), same as commands/rules today. Upgrade is explicit via `dotnet-ai upgrade`.
- Q: For FR-021, should analyze.md generate event-catalogue or remove the reference? → A: Remove the reference. Analysis derives event info from code at runtime.

## Requirements *(mandatory)*

### Functional Requirements

**Critical Bugs**

- **FR-001**: System MUST produce a `config-template.yml` where the permissions field is `permissions_level: "standard"` (flat key, not nested YAML).
- **FR-002**: System MUST use correct `find` syntax with parentheses in `pre-commit-lint.sh` for OR conditions.
- **FR-003**: System MUST copy skills to `.claude/skills/` during init, preserving the category/subcategory folder structure.
- **FR-004**: System MUST copy agents to `.claude/agents/` during init as markdown files.

**Command Behavior**

- **FR-005**: The `implement.md` command MUST always load `skills/core/configuration/SKILL.md` and `skills/core/dependency-injection/SKILL.md` regardless of task type.
- **FR-006**: The `tasks.md` command MUST include a constraint in Phase 2 (Command Side) that explicitly forbids entities, projections, read models, and lookup tables.
- **FR-007**: The `implement.md` command MUST load the appropriate specialist agent based on task repo type: command-architect for command tasks, query-architect for query tasks, processor-architect for processor tasks, gateway-architect for gateway tasks, controlpanel-architect for control panel tasks.
- **FR-008**: The `specify.md` command MUST start feature numbering at 001 when no features exist in the current repo, regardless of feature numbers in other repos.
- **FR-009**: The `tasks.md` command MUST create a `spec-link.md` file in each affected secondary repo's feature directory for multi-repo features.

**Template and Extension Robustness**

- **FR-010**: The Jinja2 template environment MUST use strict undefined mode to raise errors on missing variables.
- **FR-011**: The extension install process MUST clean up all copied files if installation fails before registry update.
- **FR-012**: The extension registry MUST use file locking to prevent corruption from concurrent CLI invocations.
- **FR-013**: The `hybrid` project type MUST be included in the microservice types list.

**Missing Rules and Skills**

- **FR-014**: System MUST include a `rules/configuration.md` rule that enforces Options pattern and `ValidateOnStart()`.
- **FR-015**: System MUST include a `rules/testing.md` rule covering CQRS test patterns.
- **FR-016**: System MUST include a `skills/core/error-handling/SKILL.md` skill covering domain exceptions and error mapping.
- **FR-017**: System MUST include a `skills/microservice/command/event-versioning/SKILL.md` skill covering event schema evolution.
- **FR-018**: All skills that call `SaveChangesAsync` MUST consistently pass `cancellationToken`.
- **FR-019**: The `config-template.yml` comments MUST list only actually supported AI tools.
- **FR-020**: The `plan.md` constitution check gate MUST be optional with a warning when the file is missing.
- **FR-021**: The `analyze.md` command MUST remove the `event-catalogue/` reference. Event information is derived from code at analysis runtime.
- **FR-022**: The `[P]` parallel marker in `tasks.md` MUST be documented with a clear definition.
- **FR-023**: CLI exit codes MUST be standardized: 1 for user input errors, 2 for config/file errors, 3 for missing dependencies.
- **FR-024**: The `agents/query-architect.md` MUST include routing guidance for Cosmos DB queries to `agents/cosmos-architect.md`.
- **FR-025**: Repository paths in config MUST be validated for correct format.

### Key Entities

- **Skill File**: A markdown document containing specialist knowledge for a specific domain. Located in `skills/{category}/{subcategory}/SKILL.md`. Max 400 lines.
- **Agent File**: A markdown document describing a specialist role with responsibilities and referenced skills. Located in `agents/{name}.md`.
- **Rule File**: An always-loaded convention document that guides all code generation. Located in `rules/{name}.md`. Max 100 lines.
- **Config Template**: A YAML file serving as the starting point for new project configurations. Located in `templates/config-template.yml`.
- **Spec Link**: A lightweight markdown file for cross-repo feature tracking. Located in `.dotnet-ai-kit/features/{feature-name}/spec-link.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the 25 identified issues are resolved with corresponding fixes.
- **SC-002**: All config templates produce valid configurations that pass validation on first use.
- **SC-003**: Running init on a new project results in skills and agents being available locally, verified by file existence checks.
- **SC-004**: The `/dai.tasks` command never generates entity, projection, or read model tasks for event-sourced command-side repos.
- **SC-005**: The `/dai.implement` command always loads configuration and DI skills, verified by checking the always-loaded skills list in the command file.
- **SC-006**: All existing tests continue to pass after changes.
- **SC-007**: New rules and skills comply with token budgets (rules <= 100 lines, skills <= 400 lines).
- **SC-008**: Feature numbering starts at 001 for repos with no prior features, verified by the specify command logic.

## Assumptions

- The tool is primarily used with Claude Code as the AI tool (other tools like Cursor/Copilot are future work).
- Skills and agents are small enough that copying them to each project is acceptable (no significant disk or git overhead). They are git-tracked (committed), consistent with the existing commands and rules copy behavior. Updates happen explicitly via `dotnet-ai upgrade`.
- A file locking dependency can be added for extension registry safety.
- The constitution check path is part of the speckit plugin, not dotnet-ai-kit, so making it optional is the correct approach.
- The `hybrid` project type represents a service that combines command and query responsibilities in a single project.
