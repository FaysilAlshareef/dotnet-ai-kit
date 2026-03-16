# Feature Specification: dotnet-ai-kit v1.0 — Foundation Release

**Feature Branch**: `001-v1-foundation-release`
**Created**: 2026-03-15
**Status**: Draft
**Input**: User description: "Implement dotnet-ai-kit v1.0 — Foundation Release"

## Clarifications

### Session 2026-03-16

- Q: Should the CLI support diagnostic/verbosity flags for troubleshooting? → A: `--verbose` flag on all commands (outputs detection results, config values resolved, skill files loaded, git operations performed)
- Q: Where does configuration live when multiple repos are involved? → A: Centralized in the hub project; individual repos receive commands and rules only, no config duplication
- Q: Can teams customize built-in project templates? → A: Yes, via local overrides in `.dotnet-ai-kit/templates/` in the hub project; overrides by name, built-in templates used as fallback

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install Tool and Initialize in Existing Project (Priority: P1)

A .NET developer installs dotnet-ai-kit as a CLI tool, runs it against their
existing project, and the tool auto-detects their architecture, .NET version,
company name, and coding conventions — ready for use with zero configuration.

**Why this priority**: Without installation and project detection, no other
feature works. This is the entry point for all users and must deliver
immediate value (confidence that the tool understands the project).

**Independent Test**: Can be fully tested by installing the CLI, running
`dotnet-ai init . --ai claude` in an existing .NET project, and verifying
that rules, commands, and config files are created correctly with the right
project type detected.

**Acceptance Scenarios**:

1. **Given** a developer with Python 3.10+ installed, **When** they run
   `uv tool install dotnet-ai-kit`, **Then** the CLI is available as the
   `dotnet-ai` command and reports its version.

2. **Given** an existing .NET project (any supported architecture), **When**
   the developer runs `dotnet-ai init . --ai claude`, **Then** the tool
   detects architecture pattern, .NET version, and company name; creates
   `.dotnet-ai-kit/config.yml`, `.claude/commands/` (25 commands), and
   `.claude/rules/` (6 rules); and reports what was detected.

3. **Given** a project with no existing .NET code, **When** the developer
   runs `dotnet-ai init my-project --type command`, **Then** the tool
   scaffolds a new project from the appropriate template with the company
   name from config.

4. **Given** an initialized project, **When** the developer runs
   `dotnet-ai check`, **Then** the tool reports installed version,
   detected project type, and whether all files are up to date.

---

### User Story 2 - One-Command Feature Building (Priority: P1)

A .NET developer describes a feature in natural language and the tool
automatically generates a specification, creates a plan, implements the code,
runs review and verification, and creates a pull request — all from a single
command.

**Why this priority**: This is the primary value proposition of the tool.
90% of daily work should be achievable through this one command. Without it,
the tool is just a collection of utilities rather than a productivity
multiplier.

**Independent Test**: Can be tested by running `/dotnet-ai.do "Add product
catalog with search"` in an initialized project and verifying that a spec,
plan, implementation, review, and PR are produced.

**Acceptance Scenarios**:

1. **Given** an initialized .NET project, **When** the developer runs
   `/dotnet-ai.do "Add order management"`, **Then** the tool chains
   specify, plan, implement, review, verify, and PR creation automatically
   and reports a summary of everything done.

2. **Given** a simple feature (single repo, fewer than 10 tasks), **When**
   the developer uses `/dotnet-ai.do`, **Then** the tool completes without
   pausing for confirmation.

3. **Given** a complex feature (multi-repo or more than 10 tasks), **When**
   the developer uses `/dotnet-ai.do`, **Then** the tool pauses after the
   plan step, shows a summary, and asks "Proceed? [Y/n]" before continuing.

4. **Given** any command, **When** the developer appends `--dry-run`,
   **Then** the tool shows what would happen without writing any files or
   making any git operations.

5. **Given** an ambiguous feature description, **When** the tool detects
   ambiguity, **Then** it asks a maximum of 3 clarifying questions inline
   before continuing.

---

### User Story 3 - Step-by-Step Feature Lifecycle (Priority: P2)

A developer who needs fine-grained control uses individual commands to move
through the feature lifecycle at their own pace: specify, clarify, plan,
generate tasks, analyze consistency, implement, review, verify, and create
a PR.

**Why this priority**: Complex features and team workflows require the
ability to pause, inspect, and modify artifacts between steps. This gives
senior developers the control they need while reusing the same underlying
capabilities as the one-command flow.

**Independent Test**: Can be tested by running each command in sequence
(`/dotnet-ai.specify` through `/dotnet-ai.pr`) and verifying that each
step produces the expected output artifacts and the final PR is created.

**Acceptance Scenarios**:

1. **Given** an initialized project, **When** the developer runs
   `/dotnet-ai.specify "Add user management"`, **Then** a feature directory
   is created with `spec.md` containing user stories, requirements, and a
   quality checklist.

2. **Given** a spec with ambiguities, **When** the developer runs
   `/dotnet-ai.clarify`, **Then** the tool asks up to 5 prioritized
   questions (one at a time), updates the spec after each answer, and
   reports how many markers remain.

3. **Given** a completed spec, **When** the developer runs
   `/dotnet-ai.plan`, **Then** the tool produces `plan.md` with research
   findings, layer/service mapping, and project structure.

4. **Given** a plan, **When** the developer runs `/dotnet-ai.tasks`,
   **Then** the tool generates tasks organized by phase with dependency
   notation, parallel markers, and exact file paths.

5. **Given** feature artifacts (spec, plan, tasks), **When** the developer
   runs `/dotnet-ai.analyze`, **Then** the tool produces a read-only
   analysis report with severity-rated findings (CRITICAL/HIGH/MEDIUM/LOW)
   without modifying any files.

6. **Given** a task list, **When** the developer runs
   `/dotnet-ai.implement`, **Then** the tool creates a feature branch,
   executes tasks in dependency order, runs build after each group, and
   marks tasks complete.

7. **Given** implemented code, **When** the developer runs
   `/dotnet-ai.review`, **Then** the tool checks changes against coding
   standards (naming, architecture, localization, error handling, security)
   and optionally integrates with CodeRabbit CLI.

8. **Given** reviewed code, **When** the developer runs
   `/dotnet-ai.verify`, **Then** the tool runs build, test, format check,
   and mode-specific checks (resource files, proto consistency, K8s
   manifests) and reports PASS/FAIL/WARN per check.

9. **Given** verified code, **When** the developer runs `/dotnet-ai.pr`,
   **Then** the tool pushes the branch and creates a PR with feature
   summary, changes, test results, and review findings.

---

### User Story 4 - Quick Code Generation (Priority: P2)

A developer uses code generation commands to rapidly scaffold entities,
endpoints, events, pages, and full CRUD operations within their existing
project, with generated code that matches existing conventions exactly.

**Why this priority**: Quick code generation handles the most common daily
tasks (adding an entity, adding an endpoint) and provides immediate value
without requiring the full lifecycle. This is the second most-used
capability after `/dotnet-ai.do`.

**Independent Test**: Can be tested by running `/dotnet-ai.add-crud Order`
in an existing project and verifying that entity, handlers, endpoint, and
tests are generated following the project's existing patterns.

**Acceptance Scenarios**:

1. **Given** a project with existing entities, **When** the developer runs
   `/dotnet-ai.add-crud Order`, **Then** the tool generates a complete
   Create/Read/Update/Delete set (entity, handlers, endpoint, tests) using
   the project's architecture pattern (VSA, Clean Arch, DDD, or
   Microservice).

2. **Given** a command-side microservice project, **When** the developer
   runs `/dotnet-ai.add-aggregate Order`, **Then** the tool creates an
   aggregate with an initial event, command handler, and gRPC service
   matching existing naming and patterns.

3. **Given** a query-side project, **When** the developer runs
   `/dotnet-ai.add-entity Order`, **Then** the tool detects SQL vs Cosmos
   automatically and creates the entity with event handlers.

4. **Given** a gateway project, **When** the developer runs
   `/dotnet-ai.add-endpoint GetOrders`, **Then** the tool creates a REST
   endpoint with gRPC client registration matching existing patterns.

5. **Given** any code generation command, **When** the developer appends
   `--preview`, **Then** the tool displays the generated code in the
   terminal without writing to disk.

6. **Given** a project with existing code, **When** the developer runs
   `/dotnet-ai.add-tests`, **Then** the tool scans for untested code,
   detects the test framework and mocking library in use, and generates
   tests following existing patterns.

---

### User Story 5 - Multi-Repository Microservice Features (Priority: P3)

A developer building CQRS microservices implements features that span
3-6 repositories (command, query, processor, gateway, control panel).
The tool orchestrates implementation across all affected repos in the
correct dependency order, creating coordinated PRs with cross-references.

**Why this priority**: Multi-repo orchestration is what differentiates this
tool from simpler code generators. It solves the hardest coordination
problem in microservice development. However, it depends on the single-repo
lifecycle (P1-P2) being solid first.

**Independent Test**: Can be tested by specifying a feature that affects
multiple repos and verifying that the tool clones/opens each repo, creates
branches, implements in dependency order (command first, then query, then
gateway), and creates linked PRs.

**Acceptance Scenarios**:

1. **Given** a microservice configuration with repo URLs, **When** the
   developer runs `/dotnet-ai.specify "Add order management"`, **Then**
   the spec includes a service map showing which repos are affected and
   what each needs.

2. **Given** a multi-repo plan, **When** the developer runs
   `/dotnet-ai.tasks`, **Then** tasks are organized by repo with dependency
   order: Command side first, then Query/Processor (parallel), then
   Gateway, then Control Panel.

3. **Given** multi-repo tasks, **When** the developer runs
   `/dotnet-ai.implement`, **Then** the tool clones or opens each repo,
   creates a feature branch in each, implements tasks in dependency order,
   runs build and test per repo, and tracks progress across all repos.

4. **Given** a multi-repo feature, **When** the developer runs
   `/dotnet-ai.analyze`, **Then** the tool checks event consistency
   (command events match query handlers), proto consistency (request/
   response match across gateway and services), and cross-repo dependencies.

5. **Given** completed multi-repo implementation, **When** the developer
   runs `/dotnet-ai.pr`, **Then** the tool creates a PR in each affected
   repo with cross-links to related PRs in other repos.

---

### User Story 6 - Session Management and Progress Tracking (Priority: P3)

A developer can check feature progress at any time, save mid-session
checkpoints, undo mistakes, resume work from a previous session, and
get a comprehensive handoff when ending a session.

**Why this priority**: Real development happens across multiple sessions.
Without progress tracking, session save/restore, and undo, the tool
cannot support realistic workflows where developers pause, switch context,
and return to features.

**Independent Test**: Can be tested by starting a feature, running
`/dotnet-ai.checkpoint`, closing the session, reopening, running
`/dotnet-ai.status`, and verifying that progress is accurately reported
with a "Next:" suggestion.

**Acceptance Scenarios**:

1. **Given** a feature in progress, **When** the developer runs
   `/dotnet-ai.status`, **Then** the tool shows lifecycle progress
   (which steps are complete), task progress (X/Y tasks done), repo
   status (per-repo for multi-repo), and suggests the next command.

2. **Given** uncommitted changes, **When** the developer runs
   `/dotnet-ai.checkpoint`, **Then** the tool commits progress and writes
   a handoff file with completed tasks, pending tasks, and current context.

3. **Given** a previous checkpoint, **When** the developer runs
   `/dotnet-ai.implement --resume`, **Then** the tool continues from the
   last incomplete task, skipping already-completed tasks.

4. **Given** a recent code generation action, **When** the developer runs
   `/dotnet-ai.undo`, **Then** the tool shows what will be reverted, asks
   for confirmation, and restores the previous state for affected files.

5. **Given** the end of a work session, **When** the developer runs
   `/dotnet-ai.wrap-up`, **Then** the tool commits all changes, writes a
   comprehensive handoff with decisions and deviations, and reports a
   session summary.

---

### User Story 7 - Learning and Pattern Explanation (Priority: P4)

A developer new to the project or to specific patterns uses the tool to
learn architecture patterns, understand the tool's commands, and get
guided onboarding through an interactive tutorial.

**Why this priority**: Onboarding and learning reduce adoption friction
and support tickets. However, this is a complement to the core development
workflow, not a prerequisite.

**Independent Test**: Can be tested by running `/dotnet-ai.explain
"clean architecture"` and verifying that the explanation includes a
description, when-to-use guidance, code examples from the tool's patterns,
and common mistakes.

**Acceptance Scenarios**:

1. **Given** any initialized project, **When** the developer runs
   `/dotnet-ai.explain aggregate`, **Then** the tool provides a 2-3
   sentence description, bullet list of when to use it, a code example
   from the tool's patterns, and common mistakes.

2. **Given** a new developer, **When** they run
   `/dotnet-ai.explain --tutorial`, **Then** the tool runs a 5-step
   guided walkthrough that builds a sample feature (in dry-run mode),
   explaining each lifecycle step.

3. **Given** any topic matching a knowledge doc, skill, or command,
   **When** the developer runs `/dotnet-ai.explain <topic>`, **Then**
   the tool pulls from its knowledge base (not generic AI knowledge) and
   provides project-relevant explanations.

---

### User Story 8 - Documentation Generation (Priority: P4)

A developer uses the tool to generate and maintain project documentation
including README files, API references, architecture decision records,
deployment guides, and release notes.

**Why this priority**: Documentation is important but not blocking for the
core development workflow. It adds polish and professionalism to projects
but can be added after the implementation features are solid.

**Independent Test**: Can be tested by running `/dotnet-ai.docs readme`
and verifying that a README.md is generated from project analysis.

**Acceptance Scenarios**:

1. **Given** a project with code, **When** the developer runs
   `/dotnet-ai.docs`, **Then** the tool scans for documentation gaps
   and reports what is missing.

2. **Given** a project with endpoints, **When** the developer runs
   `/dotnet-ai.docs api`, **Then** the tool generates API documentation
   from OpenAPI specs or controller analysis.

3. **Given** a microservice project, **When** the developer runs
   `/dotnet-ai.docs service`, **Then** the tool generates a service
   catalogue entry with Mermaid dependency diagrams and SLA/SLO details.

4. **Given** git history, **When** the developer runs
   `/dotnet-ai.docs release`, **Then** the tool generates release notes
   and changelog entries from commit messages.

---

### Edge Cases

- What happens when the tool is run on a project with an unrecognized
  architecture? The tool MUST report what it detected, warn about low
  confidence, and allow the developer to specify the architecture manually
  via `/dotnet-ai.configure`.

- How does the tool handle a feature that fails mid-implementation (e.g.,
  build error at task T005)? The tool MUST stop, report the error with
  context, mark T005 as failed in tasks.md, and allow resumption via
  `--resume` after the developer fixes the issue.

- What happens when a multi-repo feature has a repo that is unreachable
  (e.g., clone fails)? The tool MUST report which repo failed to clone,
  skip it, continue with available repos, and mark affected tasks as
  blocked.

- How does the tool behave when `/dotnet-ai.undo` is called with no
  recent actions? The tool MUST report "Nothing to undo" and show the
  undo history (empty or with past entries).

- What happens when two features are in progress simultaneously? The tool
  MUST track features independently in separate directories and allow
  switching between them via `/dotnet-ai.status --all`.

- How does the tool handle a project that uses an unsupported .NET version
  (e.g., .NET 7 or earlier)? The tool MUST warn that the version is below
  the minimum supported (.NET 8.0+) and suggest upgrading, but still
  attempt to work with the detected version.

- What happens when the developer has not configured a company name but
  runs a command that needs it? The tool MUST prompt for the company name
  just-in-time and save it to config, rather than requiring upfront
  configuration.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Tool MUST install as a Python CLI package via `uv tool install`
  and be accessible as the `dotnet-ai` command.

- **FR-002**: Tool MUST auto-detect project architecture (VSA, Clean
  Architecture, DDD, Modular Monolith, or CQRS Microservice), .NET version
  from `<TargetFramework>`, and company name from namespaces.

- **FR-003**: Tool MUST provide 25 slash commands covering the full
  development lifecycle: 9 SDD commands, 4 smart commands, 7 code generation
  commands, 2 project management commands, 1 documentation command, and
  2 session management commands.

- **FR-004**: Tool MUST support both generic .NET (single-repo) and CQRS
  microservice (multi-repo) development modes, auto-detecting the mode
  from project structure.

- **FR-005**: Generated code MUST match the existing project's naming
  conventions, code style, .NET version features, DI patterns, and
  architectural boundaries.

- **FR-006**: Every command MUST support a `--dry-run` or `--preview` flag
  that shows what would happen without making any changes.

- **FR-007**: Tool MUST provide undo capability for code generation
  operations via `/dotnet-ai.undo`, tracking file changes per task.

- **FR-008**: Tool MUST orchestrate multi-repo features across up to 6
  repositories, cloning/opening repos, creating branches, implementing
  in dependency order, and creating linked PRs.

- **FR-009**: Tool MUST work identically on Windows, macOS, and Linux
  with no OS-specific assumptions in generated code or configuration.

- **FR-010**: Tool MUST be company-agnostic, resolving all company/domain
  references from `.dotnet-ai-kit/config.yml` at runtime with `{Company}`
  and `{Domain}` placeholder substitution.

- **FR-011**: Tool MUST provide 6 always-loaded coding convention rules
  (naming, coding style, localization, error handling, architecture,
  existing project respect) with a combined maximum of 600 lines.

- **FR-012**: Tool MUST provide 101 skill files organized in 22 categories,
  each with a maximum of 400 lines, loaded on-demand by commands.

- **FR-013**: Tool MUST provide 13 specialist agent definitions that serve
  as routing logic within commands, mapping user intent to the correct
  skills and patterns.

- **FR-014**: Tool MUST provide 11 knowledge documents capturing reference
  patterns (event sourcing, outbox, service bus, gRPC, Cosmos, testing,
  deployment, dead letter, event versioning, concurrency, documentation
  standards).

- **FR-015**: Tool MUST provide 11 project scaffolding templates (7
  microservice types + 4 generic architecture types) for new project
  creation. Teams MUST be able to override built-in templates by placing
  custom templates in `.dotnet-ai-kit/templates/` in the hub project;
  built-in templates are used as fallback when no override exists.

- **FR-016**: Tool MUST provide 4 permission configuration templates
  (minimal, standard, full, MCP) for controlling tool capabilities.

- **FR-017**: Tool MUST support command aliases (full names like
  `/dotnet-ai.specify` and short names like `/dai.spec`) configurable
  via command style setting.

- **FR-018**: Tool MUST use just-in-time configuration, prompting for
  settings only when a feature that needs them is first used, rather than
  requiring upfront setup.

- **FR-019**: Tool MUST support feature resume across sessions, tracking
  progress in feature directories and allowing `--resume` to continue
  from the last incomplete task.

- **FR-020**: Tool MUST generate a feature specification with prioritized
  user stories, functional requirements, and acceptance scenarios from a
  natural language description, with a maximum of 3 ambiguity markers.

- **FR-021**: Tool MUST optionally integrate with CodeRabbit CLI for
  automated code review, detecting its availability and merging findings
  with the tool's own standards review.

- **FR-022**: Tool MUST support an extension system allowing third-party
  integrations to register additional commands and hooks.

- **FR-023**: Tool MUST respect .NET version features (e.g., primary
  constructors for .NET 8+, collection expressions for .NET 8+) and
  NEVER force-upgrade syntax or framework version.

- **FR-024**: Tool MUST target Claude Code as the first AI tool integration
  for v1.0, with the architecture designed to be portable to Cursor,
  Copilot, Codex, and Antigravity in v1.1+.

- **FR-025**: Every command MUST support a `--verbose` flag that outputs
  diagnostic information including detection results, config values
  resolved, skill files loaded, and git operations performed.

### Key Entities

- **Configuration**: Project settings including company name, GitHub org,
  repo paths, architecture mode, permission level, integration settings,
  and command style preference. In multi-repo mode, configuration is
  centralized in the hub project's `.dotnet-ai-kit/config.yml`; individual
  repos receive only commands and rules, not a copy of the config.

- **Feature**: A development unit tracked through the SDD lifecycle,
  containing specification, plan, tasks, analysis, review, and handoff
  artifacts stored in `.dotnet-ai-kit/features/{id}/`.

- **Rule**: An always-loaded coding convention file (max 100 lines) that
  enforces standards without requiring explicit skill loading.

- **Skill**: A domain-specific code pattern file (max 400 lines) with
  YAML frontmatter, loaded on-demand by commands when relevant.

- **Agent**: A role-based specialist definition (2-4 KB) that maps user
  intent to the correct skills and provides routing logic within commands.

- **Command**: A slash command file (max 200 lines) that orchestrates
  a development workflow step, reading relevant skills on demand.

- **Template**: A project scaffolding directory containing starter files
  for creating new projects of a specific architecture type. Can be
  overridden per-team via `.dotnet-ai-kit/templates/` in the hub project;
  built-in templates serve as fallback.

- **Knowledge Document**: A reference document (unlimited length)
  capturing real-world patterns from production projects.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can go from feature description to pull request
  using a single command (`/dotnet-ai.do`) in under 15 minutes for a
  simple feature (single entity CRUD with tests).

- **SC-002**: Generated code passes the target project's existing build,
  test, and linting pipeline on first generation in 90% or more of cases.

- **SC-003**: The tool correctly detects project architecture, .NET
  version, and naming conventions in 95% or more of supported project
  types without manual configuration.

- **SC-004**: All 25 commands function correctly in both generic .NET
  (single-repo) and microservice (multi-repo) modes.

- **SC-005**: The tool produces identical behavior and output on Windows,
  macOS, and Linux for the same project and commands.

- **SC-006**: A new developer can complete the interactive tutorial
  (`/dotnet-ai.explain --tutorial`) and understand the tool's workflow
  in under 10 minutes.

- **SC-007**: Feature progress can be saved and resumed across sessions
  with no loss of context or task state.

- **SC-008**: Multi-repo features maintain event and proto consistency
  across all affected repositories, verified by `/dotnet-ai.analyze`.

- **SC-009**: The full knowledge base (6 rules, 101 skills, 25 commands,
  13 agents, 11 knowledge docs, 11 templates) is complete and each file
  adheres to its token budget (rules 100 lines, commands 200 lines,
  skills 400 lines).

- **SC-010**: The tool installs and initializes in a project in under
  2 minutes, including auto-detection of project properties.
