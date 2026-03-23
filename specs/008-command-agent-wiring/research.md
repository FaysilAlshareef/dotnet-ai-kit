# Research: Wire All Commands to Appropriate Agents and Skills

**Feature**: 008-command-agent-wiring | **Date**: 2026-03-23

## R1: Agent-Command Routing Matrix

**Decision**: Each command loads agents based on two axes: (1) project type for the primary architect, and (2) task type for secondary specialists.

**Primary Architect by Project Type**:

| Project Type | Primary Agent |
|-------------|---------------|
| command | `agents/command-architect.md` |
| query-sql | `agents/query-architect.md` |
| query-cosmos | `agents/cosmos-architect.md` |
| processor | `agents/processor-architect.md` |
| gateway | `agents/gateway-architect.md` |
| controlpanel | `agents/controlpanel-architect.md` |
| hybrid | `agents/command-architect.md` + `agents/query-architect.md` |
| vsa | `agents/dotnet-architect.md` |
| clean-arch | `agents/dotnet-architect.md` |
| ddd | `agents/dotnet-architect.md` |
| modular-monolith | `agents/dotnet-architect.md` |
| generic | `agents/dotnet-architect.md` |

**Secondary Agent by Task Type**:

| Task Type | Secondary Agent |
|-----------|----------------|
| API/endpoint | `agents/api-designer.md` |
| Entity/data/EF | `agents/ef-specialist.md` |
| Test generation | `agents/test-engineer.md` |
| DevOps/Docker/CI | `agents/devops-engineer.md` |
| Documentation | `agents/docs-engineer.md` |
| Code review | `agents/reviewer.md` |

**Rationale**: Two-axis routing ensures every task gets both architectural context (from the primary agent) and domain-specific expertise (from the secondary agent).

**Alternatives considered**:
- Single agent per command — rejected because many tasks need both architecture and domain knowledge
- Load all agents — rejected because it overwhelms context window and violates token discipline

## R2: Code Generation Command → Agent Mapping

**Decision**: Each code-gen command has a fixed primary agent and optional secondary agents.

| Command | Primary Agent | Secondary Agent(s) |
|---------|--------------|-------------------|
| add-aggregate | command-architect | — |
| add-entity | query-architect OR cosmos-architect | ef-specialist |
| add-event | command-architect | — |
| add-endpoint | gateway-architect | api-designer |
| add-page | controlpanel-architect | — |
| add-tests | test-engineer | (project's primary architect) |
| add-crud | (project's primary architect) | ef-specialist, api-designer |

**Rationale**: Code-gen commands are domain-specific. The primary agent provides architectural guardrails, the secondary provides task-specific patterns.

## R3: Lifecycle Command → Agent Mapping

**Decision**: Each lifecycle command loads purpose-specific agents.

| Command | Agent(s) | Reason |
|---------|----------|--------|
| review | reviewer | Review standards, quality checks |
| docs | docs-engineer | Documentation patterns |
| verify | test-engineer + devops-engineer | Build/test/deploy verification |
| analyze | (project's primary architect) | Architecture consistency |
| plan | (project's primary architect) | Planning guidance |
| tasks | (project's primary architect) | Task decomposition |
| specify | (project's primary architect) | Feature scoping |
| clarify | (project's primary architect) | Ambiguity detection |
| do | delegates to sub-commands | Chains lifecycle; each sub-command loads its own agents |

**Rationale**: Lifecycle commands need specialist knowledge to produce high-quality output. Loading the right agent ensures the command applies domain-appropriate standards.

## R4: Agent Skill Path Corrections

**Decision**: Fix all agent "Skills Loaded" entries to use actual file paths. Current shorthand references don't match the `skills/` directory structure.

**Known mismatches found in agent scan**:

| Agent | Current Reference | Actual Path |
|-------|------------------|-------------|
| command-architect | `microservice/event-structure` | `skills/microservice/command/event-design/SKILL.md` |
| command-architect | `microservice/aggregate` | `skills/microservice/command/aggregate-design/SKILL.md` |
| command-architect | `microservice/event-sourcing-flow` | (no direct match — remove or map to aggregate-design) |
| command-architect | `microservice/outbox-pattern` | `skills/microservice/command/outbox/SKILL.md` |
| command-architect | `microservice/command-handler` | `skills/microservice/command/command-handler/SKILL.md` |
| command-architect | `microservice/command-db-config` | (no direct match — map to data/ef-core-basics) |
| command-architect | `microservice/event-catalogue` | (no file — remove reference) |
| docs-engineer | `docs/readme-generator` | `skills/docs/readme-gen/SKILL.md` |
| docs-engineer | `docs/api-documentation` | `skills/docs/api-docs/SKILL.md` |
| docs-engineer | `docs/code-documentation` | (no direct match — remove or map to docs/api-docs) |
| docs-engineer | `docs/deployment-guide` | `skills/docs/runbook/SKILL.md` |
| docs-engineer | `docs/release-notes` | `skills/docs/changelog-gen/SKILL.md` |
| docs-engineer | `docs/feature-spec` | (no direct match — remove) |
| docs-engineer | `docs/service-documentation` | `skills/docs/architecture-docs/SKILL.md` |

**Rationale**: Skill paths must resolve to actual files. Shorthand references that don't map to real files provide no value and mislead the AI tool.

**Approach**: During implementation, read each agent file, compare its skill list against `skills/` directory, fix all paths to use actual `skills/{category}/{subcategory}/SKILL.md` format.

## R5: Commands That Should NOT Load Agents

**Decision**: 9 utility commands remain unchanged.

| Command | Reason for No Agent |
|---------|-------------------|
| checkpoint | Session management — saves state, no code generation |
| configure | Configuration wizard — user input, no code generation |
| detect | Project analysis — uses detection logic, not agent knowledge |
| explain | Educational — explains existing patterns, no generation |
| init | Initialization — copies files, no domain knowledge needed |
| pr | PR creation — git/GitHub operations only |
| status | Progress display — reads task files only |
| undo | Reversion — undoes previous actions only |
| wrap-up | Session close — commits and creates handoff only |

**Rationale**: These commands perform mechanical operations that don't benefit from specialist knowledge. Adding agents would waste context tokens.
