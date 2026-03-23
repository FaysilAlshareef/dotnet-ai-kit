# Data Model: Wire All Commands to Appropriate Agents and Skills

**Feature**: 008-command-agent-wiring | **Date**: 2026-03-23

## Entities

### Command (26 total)

- **Location**: `commands/{name}.md`
- **Identity**: File name (unique)
- **Attributes**: Description, steps, skill loading directives, agent loading directives
- **Categories**:
  - Code generation (7): add-aggregate, add-crud, add-endpoint, add-entity, add-event, add-page, add-tests
  - Lifecycle (10): specify, clarify, plan, tasks, implement, review, verify, analyze, pr, do
  - Session (2): checkpoint, wrap-up
  - Setup (3): init, configure, detect
  - Documentation (1): docs
  - Utility (3): status, undo, explain
- **Constraint**: Max 200 lines per file

### Agent (13 total)

- **Location**: `agents/{name}.md`
- **Identity**: File name (unique)
- **Attributes**: Role, skills loaded (list of skill paths), responsibilities, boundaries, routing keywords
- **Types**:
  - Microservice architects (6): command-architect, query-architect, cosmos-architect, processor-architect, gateway-architect, controlpanel-architect
  - Generic architect (1): dotnet-architect
  - Domain specialists (3): api-designer, ef-specialist, test-engineer
  - Cross-cutting (3): devops-engineer, docs-engineer, reviewer

### Skill (106 total)

- **Location**: `skills/{category}/{subcategory}/SKILL.md`
- **Identity**: Full path (unique)
- **Attributes**: Markdown content with patterns, code examples, conventions
- **Categories** (17): api, architecture, core, cqrs, data, detection, devops, docs, infra, microservice/command, microservice/controlpanel, microservice/cosmos, microservice/gateway, microservice/grpc, microservice/processor, microservice/query, observability, quality, resilience, security, testing, workflow

## Relationships

### Command → Agent (loads)

- A command loads 0-3 agents depending on project type and task type
- Primary agent: based on project type (1 per command execution)
- Secondary agent: based on task domain (0-2 per command execution)
- Utility commands load 0 agents

### Agent → Skill (references)

- Each agent lists 4-14 skills in its "Skills Loaded" section
- Skills are loaded on-demand when the agent is loaded
- Skill paths must resolve to actual files

### Command → Skill (loads directly)

- Some commands load skills directly without going through an agent
- These are "always-loaded" skills (e.g., configuration, dependency-injection)
- Direct skill loading supplements agent-provided skills

## Routing Rules

### Primary Agent Selection (by project type)

```
project_type → primary_agent:
  command        → command-architect
  query-sql      → query-architect
  query-cosmos   → cosmos-architect
  processor      → processor-architect
  gateway        → gateway-architect
  controlpanel   → controlpanel-architect
  hybrid         → command-architect + query-architect
  vsa            → dotnet-architect
  clean-arch     → dotnet-architect
  ddd            → dotnet-architect
  modular-monolith → dotnet-architect
  generic        → dotnet-architect
```

### Secondary Agent Selection (by task domain)

```
task_domain → secondary_agent:
  api/endpoint   → api-designer
  entity/data/ef → ef-specialist
  test           → test-engineer
  devops/docker  → devops-engineer
  documentation  → docs-engineer
  review         → reviewer
```
