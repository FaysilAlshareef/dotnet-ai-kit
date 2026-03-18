# Feature Specification: Fix Tool Quality Issues

**Feature Branch**: `004-fix-tool-issues`
**Created**: 2026-03-18
**Status**: Draft
**Input**: User description: "Fix multiple tool quality issues found during testing: smart detection system that analyzes real project features instead of naming, permission handling fixes for compound commands, plan generation completeness, and interactive configure mode with selectable choices."

## Clarifications

### Session 2026-03-18

- Q: When a project has both command handlers and query handlers, how should detection classify it? → A: Classify as a new `hybrid` project type with its own dedicated template set.
- Q: Should detection show the user what signals it found and its confidence level? → A: Yes, show a summary by default (classification + top signals + confidence). Also allow the user to override/change the detected type if they see it is wrong.
- Q: Is "VCA" a distinct pattern from VSA (Vertical Slice Architecture)? → A: No, VCA and VSA refer to the same pattern. The canonical term is VSA (Vertical Slice Architecture).
- UX Research (2026-03-18): Permission JSON files use wrong syntax — colon `Bash(cmd:*)` instead of Claude Code's official space syntax `Bash(cmd *)`. Also identified 10 CLI UX gaps from clig.dev guidelines and dotnet scaffold patterns: progress spinners, next-command suggestions, `--json`, `NO_COLOR`, `--no-input`, stderr routing, Ctrl-C handling, exit codes, `$schema` in JSON files.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Smart Project Detection (Priority: P1)

A developer runs `dotnet-ai init` on a .NET microservice project. The tool should analyze the actual project structure, code patterns, and build configuration to accurately classify the project type -- not just check file/folder names.

For example, a **command-side** project should be identified by the presence of event definitions, command handlers that persist events, and the absence of query handlers. A **query-side** project should be identified by query handlers, event handlers subscribed via hosted services or message listeners, and the absence of command processing. A **processor** project should be identified by message listeners that receive events and route them to queues, topics, or other command-side services. A **gateway** should be identified as a Web API project that routes requests to downstream services.

The detection should also reliably identify architectural patterns (clean architecture, vertical slice architecture, modular monolith, DDD) by analyzing actual project structure and code rather than relying solely on directory naming.

**Why this priority**: Detection is the foundation of the entire tool. Incorrect detection leads to wrong templates, wrong rules, and wrong commands being installed. Every other feature depends on accurate detection.

**Independent Test**: Can be tested by running detection against real .NET projects of each type and verifying the classification matches the actual architecture.

**Acceptance Scenarios**:

1. **Given** a .NET project with command handlers that persist domain events and publish to a message bus, **When** detection runs, **Then** the project is classified as `command` regardless of naming conventions
2. **Given** a .NET project with query handlers and event handlers subscribed via a hosted service or message queue listener, **When** detection runs, **Then** the project is classified as `query-sql` or `query-cosmos` based on the data access patterns used
3. **Given** a .NET project with a hosted service that listens for events and routes them to different queues or topics, **When** detection runs, **Then** the project is classified as `processor`
4. **Given** a Web API project that acts as a request router forwarding to downstream services, **When** detection runs, **Then** the project is classified as `gateway`
5. **Given** a project with Domain, Application, and Infrastructure layers implemented as actual project references (not just directory names), **When** detection runs, **Then** the architecture is classified as `clean-arch`
6. **Given** a project with Features folders containing self-contained vertical slices with handlers, **When** detection runs, **Then** the architecture is classified as `vsa`
7. **Given** a project where naming does not follow conventions (e.g., no `.Commands` suffix) but code patterns clearly indicate command-side behavior, **When** detection runs, **Then** detection still correctly classifies the project based on code analysis
8. **Given** detection has completed and displayed its classification summary, **When** the user sees the result is incorrect, **Then** they can override the project type by selecting the correct one from a list of available types
9. **Given** detection completes on any project, **When** the result is shown, **Then** the output includes the classification, top contributing signals, and a confidence level (high/medium/low)
10. **Given** detection is scanning a project with many files, **When** the scan is in progress, **Then** a progress spinner or indicator is shown so the user knows the tool is working

---

### User Story 2 - Permission Handling for Compound Commands (Priority: P2)

A developer configures standard permissions for the AI tool. When the AI assistant constructs a shell command that combines multiple allowed operations (e.g., `cd path && gh pr create --title "..."` or `dotnet build && dotnet test`), the permission system should correctly evaluate each command in the chain against the allowed list and grant or deny appropriately.

Currently, compound commands with `&&` chains or commands with complex arguments may fail due to how the permission configuration resolves allowed commands against actual shell invocations.

**Why this priority**: Permission failures block core AI workflows like creating pull requests, running builds, and managing git operations. This directly impacts productivity and causes frustration.

**Independent Test**: Can be tested by configuring standard permissions and verifying that compound commands containing only allowed operations are permitted, while compound commands containing disallowed operations are denied.

**Acceptance Scenarios**:

1. **Given** standard permissions are configured allowing `gh pr`, **When** the AI constructs `cd /path && gh pr create --title "feature"`, **Then** the command executes successfully without permission errors
2. **Given** standard permissions allowing `dotnet build` and `dotnet test`, **When** the AI constructs `dotnet build && dotnet test`, **Then** both commands execute successfully
3. **Given** standard permissions not allowing `dotnet run`, **When** the AI constructs `dotnet build && dotnet run`, **Then** the command is denied with a clear message indicating which operation is not permitted
4. **Given** a command with complex arguments including quoted strings, special characters, and flags, **When** permission validation runs, **Then** the command is correctly parsed and validated against the allowed list
5. **Given** the tool generates permission JSON files, **When** those files are installed, **Then** the permission patterns use Claude Code's official syntax `Bash(command *)` with space separator (not colon), and include the `$schema` reference for editor autocomplete

---

### User Story 3 - Interactive Configure with Selectable Choices (Priority: P3)

A developer runs `dotnet-ai configure` to set up the tool. Instead of being presented with plain text prompts where they must type exact values, the tool presents interactive questions with numbered or selectable choices. The developer picks from predefined options using arrow keys or by typing a number.

**Why this priority**: Interactive selection reduces input errors, speeds up configuration, and provides a better user experience. Users don't need to remember valid values.

**Independent Test**: Can be tested by running the configure command and verifying that each configuration option presents selectable choices rather than free-text input.

**Acceptance Scenarios**:

1. **Given** a developer runs `dotnet-ai configure`, **When** prompted for permission level, **Then** they see a numbered menu (1. Minimal, 2. Standard, 3. Full) with descriptions and can select by number or arrow keys
2. **Given** a developer runs `dotnet-ai configure`, **When** prompted for AI tools to enable, **Then** they see a multi-select checklist of available tools (Claude Code, Cursor, GitHub Copilot, Codex) and can toggle each on/off
3. **Given** a developer runs `dotnet-ai configure`, **When** prompted for command style, **Then** they see options (Full names only, Short aliases only, Both) with examples and can select one
4. **Given** a developer runs `dotnet-ai configure`, **When** prompted for company name, **Then** a text input is used (since this requires free-form entry) with validation feedback shown inline
5. **Given** a developer runs `dotnet-ai configure` in a CI/CD pipeline (no TTY), **When** the `--no-input` flag is passed with all values as flags, **Then** the command completes without any interactive prompts

---

### User Story 4 - Complete Plan Generation (Priority: P3)

When a developer triggers plan generation for a feature, the tool should produce not just a plan file but also supporting research artifacts, data model outlines, contract definitions, and quickstart guidance -- at least for non-trivial features. For simple tasks, a lightweight plan is acceptable, but the system should distinguish between simple and complex features.

**Why this priority**: Incomplete plans lead to incomplete implementations. Developers expect the planning phase to surface key decisions about data models and contracts before coding begins.

**Independent Test**: Can be tested by triggering plan generation for a feature that involves data models and verifying that the output includes data model definitions, contract outlines, and implementation guidance beyond just the plan file.

**Acceptance Scenarios**:

1. **Given** a feature that involves data entities and service interactions, **When** plan generation runs, **Then** the output includes data model outlines, contract definitions, and implementation notes alongside the plan
2. **Given** a simple bug fix or single-file change, **When** plan generation runs, **Then** a lightweight plan is produced without unnecessary artifacts
3. **Given** a feature with external service dependencies, **When** plan generation runs, **Then** the plan identifies integration points and required contracts

---

### User Story 5 - CLI UX Polish and Quality Audit (Priority: P3)

The tool should follow CLI UX best practices (per clig.dev guidelines and dotnet scaffold patterns). This includes progress indicators during long operations, next-command suggestions after completions, proper exit codes, `NO_COLOR` support, `--json` output mode, error output to stderr, and graceful Ctrl-C handling. Additionally, known quality issues like script parameter binding and cross-platform command execution should be fixed.

**Why this priority**: Professional CLI UX builds trust with developers. Following industry conventions (clig.dev) makes the tool feel polished and reduces friction.

**Independent Test**: Can be tested by running each CLI command and verifying: progress indicators appear during long operations, next-command suggestions are shown, errors go to stderr, `--json` produces valid JSON, `NO_COLOR=1` disables colors, Ctrl-C exits cleanly.

**Acceptance Scenarios**:

1. **Given** the CLI tool is installed, **When** each command is run with valid inputs, **Then** all commands execute without unexpected errors
2. **Given** the CLI tool is run on Windows with bash shell, **When** commands invoke external tools, **Then** PATH resolution works correctly for tools like `gh`, `dotnet`, and `git`
3. **Given** `dotnet-ai init` completes successfully, **When** the output is shown, **Then** it suggests the next command to run (e.g., "Run `dotnet-ai configure` to customize settings")
4. **Given** `dotnet-ai configure` completes successfully, **When** the output is shown, **Then** it suggests relevant next steps
5. **Given** any CLI command is run with `--json` flag, **When** the command completes, **Then** the output is valid JSON written to stdout with no decorative text mixed in
6. **Given** `NO_COLOR=1` environment variable is set, **When** any CLI command runs, **Then** all color and formatting is disabled
7. **Given** detection is running a long scan, **When** the user presses Ctrl-C, **Then** the tool exits cleanly with a message (no Python traceback)
8. **Given** any CLI command fails, **When** the error is output, **Then** the error message goes to stderr (not stdout) and includes what went wrong and how to fix it
9. **Given** any CLI command fails, **When** the process exits, **Then** the exit code is non-zero and mapped to the failure type (1=general, 2=config error, 3=detection failed)

---

### Edge Cases

- When a project uses a hybrid architecture (e.g., command handlers and query handlers in the same project), detection classifies it as a `hybrid` project type with its own template set that supports both command and query patterns.
- When detection encounters projects that use non-standard frameworks or custom base classes instead of well-known patterns, it falls back to `generic` type with `low` confidence and prompts the user to override.
- What happens when the permission config references a command that is not installed on the system (e.g., `gh` not in PATH)?
- How does the configure command behave when run in a non-interactive terminal (CI/CD pipeline)?
- What happens when plan generation is triggered for a feature with no clear data model or external dependencies?
- How does detection handle multi-project solutions where different projects have different types?

## Requirements *(mandatory)*

### Functional Requirements

**Detection System**

- **FR-001**: Detection MUST analyze actual code patterns (command handlers, event definitions, query handlers, hosted services, message listeners) to classify project types, not rely solely on naming conventions
- **FR-002**: Detection MUST correctly identify command-side projects by the presence of domain events, command handlers, and event publishing -- and the absence of query handlers
- **FR-003**: Detection MUST correctly identify query-side projects by the presence of query handlers, read models, and event handlers subscribed via background services -- and the absence of command processing
- **FR-004**: Detection MUST correctly identify processor projects by the presence of message listeners that receive events and route them to other services
- **FR-005**: Detection MUST correctly identify gateway projects by the presence of API routing to downstream services
- **FR-006**: Detection MUST identify architectural patterns (clean architecture, vertical slice, DDD, modular monolith) based on actual project structure and references, not just directory names
- **FR-007**: Detection MUST use name-based hints as supplementary signals that increase confidence, not as the sole determining factor
- **FR-008**: Detection MUST handle multi-project solutions by classifying each project independently
- **FR-008a**: When a project contains both command-side and query-side patterns, detection MUST classify it as a `hybrid` project type with its own dedicated template set that supports both patterns
- **FR-008b**: After detection completes, the system MUST display a summary showing the classification, the top signals that led to it, and the confidence level (e.g., "Detected: command (found 3 command handlers, 2 event definitions, confidence: high)")
- **FR-008c**: After displaying the detection summary, the system MUST allow the user to override the detected project type if they believe it is incorrect
- **FR-008d**: During detection scanning, the system MUST display a progress spinner or indicator so the user knows the tool is working

**Permission Handling**

- **FR-009**: The tool MUST ensure external tools referenced in permission configs are available in the system PATH, and AI guidance rules MUST instruct assistants to use sequential tool calls instead of compound `&&` chains to avoid PATH resolution failures
- **FR-009a**: Permission JSON files MUST use Claude Code's official syntax `Bash(command *)` with space separator, not colon (`Bash(command:*)`)
- **FR-009b**: Permission JSON files MUST include `"$schema": "https://json.schemastore.org/claude-code-settings.json"` for editor autocomplete and validation
- **FR-010**: The permission system MUST handle commands with complex arguments including quoted strings, flags, and special characters without misclassifying them
- **FR-011**: When a compound command contains a disallowed operation, the system MUST clearly identify which specific operation is not permitted

**Configure Command**

- **FR-012**: The configure command MUST present multiple-choice options as interactive selectable menus rather than free-text prompts
- **FR-013**: The configure command MUST use text input only for values that require free-form entry (e.g., company name, GitHub organization)
- **FR-014**: Each menu option MUST include a brief description explaining what it does
- **FR-015**: The configure command MUST show the current/default value when presenting options
- **FR-015a**: The configure command MUST support a `--no-input` flag that requires all values via flags/env vars and fails if required values are missing (for CI/CD pipelines)

**Plan Generation**

- **FR-016**: Plan generation MUST distinguish between simple and complex features based on scope indicators (number of entities, external dependencies, affected components)
- **FR-017**: For complex features, plan generation MUST produce supporting artifacts (data model outlines, contract definitions, integration notes) alongside the plan file
- **FR-018**: For simple features, plan generation MUST produce a lightweight plan without unnecessary artifacts

**General Quality**

- **FR-019**: All CLI commands MUST provide clear, actionable error messages when they fail
- **FR-020**: External tool invocations MUST handle missing tools gracefully with guidance on how to install them
- **FR-021**: CLI commands that complete an operation MUST suggest the next command to run (e.g., after `init` → suggest `configure`)
- **FR-022**: All CLI commands MUST support a `--json` flag that outputs machine-readable JSON to stdout with no decorative text
- **FR-023**: The CLI MUST respect the `NO_COLOR` environment variable and disable all color/formatting when it is set
- **FR-024**: The CLI MUST handle Ctrl-C (SIGINT) gracefully — exit quickly with a message, no Python traceback shown to users
- **FR-025**: Error messages MUST go to stderr; primary data output MUST go to stdout
- **FR-026**: CLI commands MUST return mapped exit codes (0=success, 1=general error, 2=config error, 3=detection failed)

### Key Entities

- **DetectionSignal**: A code pattern or structural indicator found during project analysis (type: naming, code-pattern, structural, build-config; confidence: high, medium, low)
- **DetectedProject (extended)**: The existing project classification model, extended with confidence scoring, top signals, and user override fields (project type -- including `hybrid` for mixed command/query projects, architecture mode, confidence score, supporting evidence)
- **ConfigOption**: A configurable setting with its presentation type (select-single, select-multiple, text-input), available choices, and current value

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Detection correctly classifies 95% of standard .NET microservice projects (command, query, processor, gateway) when tested against real-world project samples -- regardless of naming conventions
- **SC-002**: Detection correctly identifies architectural patterns (clean-arch, VSA, DDD, modular monolith) in 90% of projects that follow those patterns
- **SC-003**: Compound shell commands containing only allowed operations succeed 100% of the time without permission errors
- **SC-004**: 100% of configure options that have predefined valid values use interactive selection menus
- **SC-005**: Complex feature plans include at minimum a data model outline and contract definitions when the feature involves data entities or service interactions
- **SC-006**: All CLI commands produce actionable error messages (include what went wrong and how to fix it) for common failure scenarios
- **SC-007**: Users can complete the full configure workflow in under 2 minutes using the interactive selection mode
- **SC-008**: Permission JSON files pass Claude Code's JSON schema validation (`$schema` reference included)
- **SC-009**: Every CLI command that completes an operation outputs a "next step" suggestion
- **SC-010**: `--json` flag produces valid, parseable JSON for all CLI commands
- **SC-011**: No Python tracebacks are visible to users during normal operation (including Ctrl-C)

## Assumptions

- The tool runs in environments where .NET SDK is installed and .NET projects are valid (compilable or at least parseable)
- Developers have standard development tools available (git, dotnet CLI) but optional tools (gh, docker) may not be present
- Projects follow recognizable .NET patterns even if they don't follow strict naming conventions
- The interactive configure mode requires a TTY-capable terminal; CI/CD environments should use the `--minimal` flag or environment variables
- Permission configuration files are generated by the tool and not manually edited by users
- Plan generation complexity detection is heuristic-based and may occasionally misclassify; this is acceptable as users can override
