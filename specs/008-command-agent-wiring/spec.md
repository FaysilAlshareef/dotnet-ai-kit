# Feature Specification: Wire All Commands to Appropriate Agents and Skills

**Feature Branch**: `008-command-agent-wiring`
**Created**: 2026-03-23
**Status**: Draft
**Input**: User description: "Update all commands to load appropriate agents and skills. Currently only implement.md loads 5 agents — all 13 agents and 106 skills must be properly wired across all 26 commands."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Code Generation Commands Load Full Agent + Skill Context (Priority: P1)

A developer runs a code generation command (`/dai.go`, `/dai.agg`, `/dai.entity`, `/dai.event`, `/dai.ep`, `/dai.page`, `/dai.crud`, `/dai.tests`). The command automatically loads the appropriate specialist agent AND all relevant skills for the task at hand, so that generated code follows the exact architectural patterns and conventions the agent enforces.

**Why this priority**: Code generation commands are where the tool produces actual code. Without the right agent and skills loaded, the tool generates code that violates conventions — as already seen with the IConfiguration issue (missing configuration skill) and entity-on-command-side issue (missing command-architect agent).

**Independent Test**: Run `/dai.agg` on a command-side project and verify that `agents/command-architect.md` is loaded. Run `/dai.entity` on a query project and verify `agents/query-architect.md` or `agents/cosmos-architect.md` is loaded based on DB type. Verify all skill paths referenced in the agent's "Skills Loaded" section are also loaded by the command.

**Acceptance Scenarios**:

1. **Given** a command-side project, **When** `/dai.agg` is run, **Then** `agents/command-architect.md` is loaded along with its 13 skills.
2. **Given** a query-sql project, **When** `/dai.entity` is run, **Then** `agents/query-architect.md` is loaded along with its 11 skills.
3. **Given** a query-cosmos project, **When** `/dai.entity` is run, **Then** `agents/cosmos-architect.md` is loaded along with its 11 skills.
4. **Given** a gateway project, **When** `/dai.ep` is run, **Then** `agents/gateway-architect.md` is loaded along with its 10 skills.
5. **Given** a controlpanel project, **When** `/dai.page` is run, **Then** `agents/controlpanel-architect.md` is loaded along with its 5 skills.
6. **Given** any project, **When** `/dai.tests` is run, **Then** `agents/test-engineer.md` is loaded along with testing skills.
7. **Given** a generic project, **When** `/dai.crud` is run, **Then** `agents/dotnet-architect.md` and `agents/ef-specialist.md` are loaded for architecture + data access guidance.

---

### User Story 2 - Implement Command Loads All 13 Agents by Context (Priority: P1)

A developer runs `/dai.implement` (or `/dai.go`). The command currently only maps 5 agents (command, query, processor, gateway, controlpanel). It must also load `agents/dotnet-architect.md` for generic projects, `agents/api-designer.md` for API tasks, `agents/ef-specialist.md` for data tasks, `agents/cosmos-architect.md` for cosmos projects, `agents/test-engineer.md` for test tasks, `agents/devops-engineer.md` for devops tasks, `agents/docs-engineer.md` for documentation tasks, and `agents/reviewer.md` for review tasks.

**Why this priority**: `implement.md` is the primary execution command and must route to the correct specialist for every task type.

**Independent Test**: Read the updated `implement.md` and verify all 13 agents are reachable through the routing logic (by project type OR by task type).

**Acceptance Scenarios**:

1. **Given** a generic (VSA/Clean Arch/DDD) project, **When** `/dai.implement` runs, **Then** `agents/dotnet-architect.md` is loaded as the primary architect.
2. **Given** a task tagged with API/endpoint work, **When** `/dai.implement` runs that task, **Then** `agents/api-designer.md` is also loaded for API design guidance.
3. **Given** a task tagged with data/entity/EF work on a generic project, **When** `/dai.implement` runs that task, **Then** `agents/ef-specialist.md` is loaded.
4. **Given** a task tagged with test generation, **When** `/dai.implement` runs that task, **Then** `agents/test-engineer.md` is loaded.
5. **Given** a task tagged with devops/docker/CI work, **When** `/dai.implement` runs, **Then** `agents/devops-engineer.md` is loaded.
6. **Given** a query-cosmos project, **When** `/dai.implement` runs, **Then** `agents/cosmos-architect.md` is loaded instead of `agents/query-architect.md`.

---

### User Story 3 - Lifecycle Commands Load Appropriate Agents (Priority: P2)

A developer runs lifecycle commands (`/dai.review`, `/dai.verify`, `/dai.analyze`, `/dai.docs`, `/dai.plan`, `/dai.tasks`, `/dai.spec`, `/dai.clarify`). Each command loads the specialist agent relevant to its purpose — `agents/reviewer.md` for reviews, `agents/test-engineer.md` for verification, `agents/docs-engineer.md` for documentation, the project's primary architect for specification, planning, and analysis, etc.

**Why this priority**: Lifecycle commands need specialist knowledge to produce high-quality output but currently load no agents.

**Independent Test**: Read each updated lifecycle command and verify the correct agent is referenced.

**Acceptance Scenarios**:

1. **Given** any project, **When** `/dai.review` is run, **Then** `agents/reviewer.md` is loaded for review standards.
2. **Given** any project, **When** `/dai.docs` is run, **Then** `agents/docs-engineer.md` is loaded for documentation patterns.
3. **Given** any project, **When** `/dai.verify` is run, **Then** `agents/test-engineer.md` and `agents/devops-engineer.md` are loaded for build/test/deploy verification.
4. **Given** any project, **When** `/dai.analyze` is run, **Then** the project's primary architect agent is loaded for architecture consistency checks.
5. **Given** any project, **When** `/dai.plan` is run, **Then** the project's primary architect agent is loaded for planning guidance.
6. **Given** any project, **When** `/dai.tasks` is run, **Then** the project's primary architect agent is loaded to inform task decomposition.
7. **Given** any project, **When** `/dai.spec` is run, **Then** the project's primary architect agent is loaded for feature scoping.
8. **Given** any project, **When** `/dai.clarify` is run, **Then** the project's primary architect agent is loaded for ambiguity detection.

---

### User Story 4 - Skills Are Wired Consistently with Agent Definitions (Priority: P2)

Every command that loads an agent also loads the skills listed in that agent's "Skills Loaded" section. The skill paths in commands match the actual skill paths on disk. No command references a skill that doesn't exist, and no agent references a skill that isn't loadable.

**Why this priority**: Skills are the detailed knowledge that agents apply. If an agent is loaded but its skills aren't, the agent has no knowledge to work with.

**Independent Test**: For each command, verify that every skill it references exists at the specified path, and that the skills match what the loaded agent(s) define.

**Acceptance Scenarios**:

1. **Given** a command that loads `agents/command-architect.md`, **When** the command is reviewed, **Then** all 13 skills listed in command-architect are loadable by the command.
2. **Given** any skill path referenced in any command, **When** the path is checked, **Then** the file exists in `skills/` directory.
3. **Given** the agent inventory (13 agents, each with a skills list), **When** cross-referenced with commands, **Then** every agent's skills are accessible through at least one command.

---

### Edge Cases

- What happens when a command applies to multiple project types (e.g., `/dai.crud` works for both generic and microservice)? Load the project's primary architect plus task-specific specialists.
- What happens when a project type is `hybrid`? Load both command-architect and query-architect agents, as already defined.
- What happens when a command is project-type-agnostic (e.g., `/dai.checkpoint`, `/dai.undo`)? These utility commands do not need agents — leave them unchanged.
- What happens when a skill path in an agent file doesn't match the actual skill directory structure? Flag it as an error and correct the path.
- What happens when a new agent or skill is added in the future? The wiring convention (agent → skills, command → agent + skills) should be self-documenting enough that new additions follow the pattern.

## Requirements *(mandatory)*

### Functional Requirements

**Code Generation Commands (7 commands)**

- **FR-001**: `/dai.agg` (add-aggregate) MUST load `agents/command-architect.md` and all command-side skills it references.
- **FR-002**: `/dai.entity` (add-entity) MUST load `agents/query-architect.md` for SQL projects or `agents/cosmos-architect.md` for Cosmos projects, plus `agents/ef-specialist.md` for data guidance.
- **FR-003**: `/dai.event` (add-event) MUST load `agents/command-architect.md` and event-specific skills.
- **FR-004**: `/dai.ep` (add-endpoint) MUST load `agents/gateway-architect.md` and `agents/api-designer.md` for endpoint design.
- **FR-005**: `/dai.page` (add-page) MUST load `agents/controlpanel-architect.md` and all control panel skills.
- **FR-006**: `/dai.tests` (add-tests) MUST load `agents/test-engineer.md` and testing skills.
- **FR-007**: `/dai.crud` (add-crud) MUST load `agents/dotnet-architect.md` for generic projects and the appropriate microservice architect for microservice projects, plus `agents/ef-specialist.md` and `agents/api-designer.md`.

**Implementation Command**

- **FR-008**: `/dai.implement` MUST support all 13 agents through a routing matrix that considers both project type AND task type.
- **FR-009**: `/dai.implement` MUST load task-type-specific secondary agents: `api-designer` for API tasks, `ef-specialist` for data tasks, `test-engineer` for test tasks, `devops-engineer` for devops tasks, `docs-engineer` for docs tasks.
- **FR-010**: `/dai.implement` MUST load `agents/dotnet-architect.md` for generic-mode projects (VSA, Clean Arch, DDD, Modular Monolith).

**Lifecycle Commands (6 commands)**

- **FR-011**: `/dai.review` MUST load `agents/reviewer.md` and its quality/security skills.
- **FR-012**: `/dai.docs` MUST load `agents/docs-engineer.md` and its documentation skills.
- **FR-013**: `/dai.verify` MUST load `agents/test-engineer.md` and `agents/devops-engineer.md`.
- **FR-014**: `/dai.analyze` MUST load the project's primary architect agent for architecture consistency.
- **FR-015**: `/dai.plan` MUST load the project's primary architect agent for planning guidance.
- **FR-016**: `/dai.tasks` MUST load the project's primary architect agent for task decomposition.
- **FR-021**: `/dai.spec` (specify) MUST load the project's primary architect agent for feature scoping.
- **FR-022**: `/dai.clarify` (clarify) MUST load the project's primary architect agent for ambiguity detection.

**Skill Path Consistency**

- **FR-017**: Every skill path referenced in any command MUST correspond to an existing file in the `skills/` directory.
- **FR-018**: Every skill listed in an agent's "Skills Loaded" section MUST be mapped to an actual skill path in `skills/`.
- **FR-019**: Agent skill references that use shorthand (e.g., `microservice/event-structure`) MUST be updated to full paths (e.g., `skills/microservice/command/event-design/SKILL.md`).

**Utility Commands (unchanged)**

- **FR-020**: Utility commands (`/dai.do`, `/dai.checkpoint`, `/dai.undo`, `/dai.status`, `/dai.save`, `/dai.done`, `/dai.init`, `/dai.config`, `/dai.detect`, `/dai.explain`) do NOT require agent loading — leave unchanged. `/dai.do` delegates to sub-commands that each load their own agents.

### Key Entities

- **Agent**: A specialist role definition (13 total) with a skills list, responsibilities, boundaries, and routing keywords. Located in `agents/{name}.md`.
- **Skill**: A knowledge document (106 total) with detailed patterns and code examples. Located in `skills/{category}/{subcategory}/SKILL.md`.
- **Command**: A slash command template (26 total) that orchestrates agent loading and skill loading based on task context. Located in `commands/{name}.md`.
- **Agent-Skill Mapping**: The relationship between an agent and the skills it requires. Defined in each agent's "Skills Loaded" section.
- **Command-Agent Routing**: The rules that determine which agent(s) a command loads based on project type and task type.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 7 code generation commands explicitly reference the correct specialist agent(s) for their domain.
- **SC-002**: The `/dai.implement` command can route to all 13 agents through its project-type + task-type routing matrix.
- **SC-003**: All 8 lifecycle commands that need specialist knowledge load the appropriate agent.
- **SC-004**: 100% of skill paths referenced in commands resolve to existing files in `skills/`.
- **SC-005**: 100% of agent "Skills Loaded" references map to actual skill file paths.
- **SC-006**: All commands remain under the 200-line token budget after updates.
- **SC-007**: 10 utility commands remain unchanged (no unnecessary agent loading), including `/dai.do` which delegates to sub-commands.

## Assumptions

- Agent loading is a read instruction in the command markdown — the AI tool reads the agent file for context when executing the command. No Python code changes needed.
- Skill loading is similarly a read instruction — the AI tool reads the skill file for detailed patterns. No code changes needed.
- The existing project type detection (`project.yml` or `--type` flag) provides the routing key for agent selection.
- Commands that work in both generic and microservice modes need conditional agent loading based on detected project mode.
- Some agents are loaded as "primary" (project architect) and others as "secondary" (task-specific specialist). A command may load 1-3 agents depending on context.
- The `agents/docs-engineer.md` references some skill paths that don't match the directory structure (e.g., `docs/readme-generator` vs actual `docs/readme-gen`). These mismatches will be corrected during implementation.
