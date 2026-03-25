# Feature Specification: Fix v1.0 Gap Report Issues

**Feature Branch**: `010-fix-v1-gaps`
**Created**: 2026-03-25
**Status**: Draft
**Input**: User description: "Fix all 11 gaps identified in v1.0 gap report with recommended solutions, and update planning files and docs to cover changes"

## Clarifications

### Session 2026-03-25

- Q: Is `/dai.learn` a CLI-backed command (Python) or a slash-command-only (markdown template)? → A: New slash command (`commands/learn.md`, 27th command) that chains `/dai.detect` internally to reuse scan logic, then extends the output into a constitution file.
- Q: FR-004 — remove unused models or wire them? → A: Wire `NamingConfig` to template rendering (solving FR-006 through the existing model), remove `CodeRabbitConfig` and `IntegrationsConfig` (v1.1 scope).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Project Knowledge Persists Across Sessions (Priority: P1)

A developer initializes dotnet-ai-kit in their .NET project and runs a "learn" command. The tool scans the project's domain model, conventions, tech decisions, and patterns, then generates a persistent knowledge file. In subsequent sessions, the AI assistant automatically loads this project context — eliminating the cold-start problem where every conversation begins from scratch.

**Why this priority**: This is the largest feature gap. Without persistent project knowledge, each AI session starts cold and must re-discover project conventions. This directly impacts every user of the tool on every interaction.

**Independent Test**: Can be fully tested by running the learn command on a .NET project and verifying a constitution/knowledge file is generated with accurate project details, then verifying it is loaded in a new session.

**Acceptance Scenarios**:

1. **Given** a .NET project with dotnet-ai-kit initialized, **When** the user runs `/dai.learn`, **Then** a `.dotnet-ai-kit/memory/constitution.md` file is generated containing the project's architecture type, domain model summary, naming conventions, key NuGet packages, .NET version, and established patterns.
2. **Given** a project with an existing constitution file, **When** a new AI session begins, **Then** the constitution is automatically loaded as project context alongside rules.
3. **Given** a project where features have been implemented, **When** the user runs `/dai.learn --update`, **Then** the constitution is refreshed with any newly detected patterns or conventions.

---

### User Story 2 - Tool Consistency and Correctness (Priority: P1)

A developer installs dotnet-ai-kit and uses it daily. The tool has no duplicate skill names causing lookup conflicts, no dead code references in commands, no broken extension hooks, and standardized flag names across all commands. The developer experiences consistent, predictable behavior.

**Why this priority**: Correctness bugs (duplicate names, dead references, broken hooks) undermine user trust and cause silent failures. These must be fixed before v1.0 ships.

**Independent Test**: Can be tested by verifying unique skill names, running extension hooks, checking all command flags are standardized, and confirming no dead model code exists.

**Acceptance Scenarios**:

1. **Given** the skills directory, **When** all skill YAML frontmatter is parsed, **Then** every `name` field is unique across all 106 skills.
2. **Given** an extension with declared hooks, **When** the extension is installed and the hook trigger fires, **Then** the hook executes as specified.
3. **Given** all 27 command files, **When** checking for preview/dry-run flags, **Then** only `--dry-run` is used (no `--preview` flag exists).
4. **Given** the Python models, **When** inspecting the codebase, **Then** `NamingConfig` is wired to template rendering, and `CodeRabbitConfig`/`IntegrationsConfig` are removed.

---

### User Story 3 - Complete Knowledge Base and Discoverability (Priority: P2)

A developer new to the tool browses the plugin manifest to understand what's included, reads knowledge docs for the architecture they're using (Clean Architecture, DDD, CQRS, VSA), and finds comprehensive reference material. The plugin manifest clearly lists all 27 commands, 106 skills, 13 agents, and 4 hooks.

**Why this priority**: Missing knowledge docs and incomplete plugin manifest reduce discoverability and onboarding quality. Important but not blocking daily usage.

**Independent Test**: Can be tested by verifying knowledge docs exist for all supported architectures, and the plugin manifest enumerates all tool components.

**Acceptance Scenarios**:

1. **Given** the knowledge directory, **When** checking for architecture guides, **Then** reference docs exist for CQRS, DDD, Clean Architecture, and VSA patterns.
2. **Given** the plugin manifest, **When** a user inspects it before installing, **Then** all 27 commands are listed with names and descriptions.
3. **Given** the plugin manifest, **When** reading the capabilities section, **Then** all 13 agents, 106 skills, and 4 hooks are enumerated.

---

### User Story 4 - Template Variables and Explicit Outputs (Priority: P2)

A developer scaffolds a project and specifies their domain name. The generated code uses that domain name in namespaces instead of the literal placeholder "Domain". When running `/dai.specify` for a microservice feature, the output explicitly includes a `service-map.md` file.

**Why this priority**: Hardcoded template variables and implicit outputs create confusion. Users expect generated code to reflect their project, not placeholders.

**Independent Test**: Can be tested by scaffolding a project with `--domain Draw` and verifying namespaces use "Draw" not "Domain". Test `/dai.specify` in microservice mode and verify service-map.md is listed as an explicit output.

**Acceptance Scenarios**:

1. **Given** a config with `domain: Draw`, **When** scaffolding a command project, **Then** generated namespaces use `Draw` (e.g., `Ecom.Draw.Commands`), not `Domain`.
2. **Given** a microservice project, **When** running `/dai.specify` for a cross-service feature, **Then** a `service-map.md` file is explicitly created in the feature directory.
3. **Given** the controlpanel-architect agent, **When** checking its skill list, **Then** the `response-result` skill is included.

---

### Edge Cases

- What happens when `/dai.learn` is run on a project with no .NET files? System reports "No .NET project detected" and creates a minimal constitution with only the config values.
- What happens when a constitution file already exists and `/dai.learn` is run without `--update`? System asks whether to overwrite or update.
- What happens when extension hooks reference commands that don't exist? System logs a warning and skips the hook.
- What happens when the `domain` config value is not set during scaffolding? System falls back to "Domain" as default (current behavior) but logs a note suggesting `/dai.config` to set it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a `/dai.learn` slash command (`commands/learn.md`, 27th command) that chains `/dai.detect` internally to reuse project scan logic, then extends the output into a `.dotnet-ai-kit/memory/constitution.md` file with project-specific knowledge (architecture, domain model, conventions, packages, .NET version).
- **FR-002**: System MUST remove or resolve the dead "Constitution Check" reference in `/dai.plan` command, either by wiring it to the actual constitution file from FR-001 or removing the gate.
- **FR-003**: System MUST ensure all skill `name` fields are unique across the entire skills directory. The duplicate `dotnet-ai-controller-patterns` name must be resolved.
- **FR-004**: System MUST wire `NamingConfig` to template rendering (solving FR-006) and remove `CodeRabbitConfig` and `IntegrationsConfig` (deferred to v1.1). `ReposConfig` must remain (used for multi-repo features).
- **FR-005**: System MUST execute extension hooks that are declared in extension manifests. The `min_cli_version` field must be validated during installation.
- **FR-006**: System MUST wire the existing `NamingConfig` model (with its `solution`, `topic`, `namespace` fields) to `copier.py` template rendering, replacing the hardcoded "Domain"/"domain" strings with values from `config.yml` naming section.
- **FR-007**: System MUST include knowledge reference documents for CQRS, DDD, Clean Architecture, and VSA patterns in the `knowledge/` directory.
- **FR-008**: System MUST expand `plugin.json` to enumerate all commands, skills, agents, and hooks with names and descriptions.
- **FR-009**: System MUST standardize all command files to use `--dry-run` flag only. Any `--preview` references must be replaced.
- **FR-010**: The `/dai.specify` command MUST explicitly list `service-map.md` as a required output for microservice-mode features.
- **FR-011**: ~~The `controlpanel-architect.md` agent MUST include `response-result` in its loaded skills list.~~ **RESOLVED**: Verified during gap analysis — `response-result` is already listed at line 7 of `controlpanel-architect.md`. No action needed.

### Key Entities

- **Constitution**: Project-specific knowledge document containing architecture type, domain model summary, naming patterns, .NET version, key packages, and established conventions. Stored at `.dotnet-ai-kit/memory/constitution.md`.
- **Knowledge Document**: Reference material for a specific architectural pattern or technology concern. Stored in `knowledge/` directory. Read-only reference, not project-specific.
- **Plugin Manifest**: Machine-readable catalog of all tool components (commands, skills, agents, hooks). Stored at `.claude-plugin/plugin.json`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can generate project-specific knowledge in under 60 seconds by running a single command, and that knowledge is automatically available in all subsequent sessions.
- **SC-002**: Zero duplicate skill names exist across the entire skills directory (verified by parsing all YAML frontmatter).
- **SC-003**: All 27 commands use consistent `--dry-run` flag naming with zero instances of `--preview`.
- **SC-004**: Knowledge reference documents cover 100% of supported architecture types (CQRS, DDD, Clean Architecture, VSA, Modular Monolith).
- **SC-005**: Plugin manifest lists 100% of commands (27), agents (13), and hooks (4) with names and descriptions.
- **SC-006**: Extension hooks declared in manifests execute when their trigger conditions are met, with zero silent failures.
- **SC-007**: Template-generated code uses project-specific domain names when configured, not generic placeholders.
