---
name: dotnet-ai-sdd-lifecycle
description: >
  Specification-Driven Development lifecycle phases. Covers plan, spec, implement,
  review, and ship phases adapted for microservice and generic .NET projects.
  Trigger: SDD, specification driven, lifecycle, phases, plan, implement.
category: workflow
agent: dotnet-architect
---

# SDD Lifecycle — Specification-Driven Development

## Core Principles

- Features progress through defined phases: Plan -> Spec -> Implement -> Review -> Ship
- Each phase produces artifacts stored in `.dotnet-ai-kit/features/{NNN}/`
- Specification is written before implementation (design-first)
- Cross-service features coordinate via dependency chains
- Status tracking enables handoffs between sessions and team members

## Key Patterns

### Phase Definitions

```
Phase 1: PLAN
  Input:  User requirement or feature request
  Output: Feature brief with scope, affected services, acceptance criteria
  Status: planned

Phase 2: SPEC
  Input:  Feature brief
  Output: Technical specification with:
    - Event data types and aggregate changes
    - Query entity projections
    - API endpoint definitions
    - UI wireframe descriptions
  Status: specified

Phase 3: IMPLEMENT
  Input:  Technical specification
  Output: Working code across affected services
  Status: implementing -> implemented

Phase 4: REVIEW
  Input:  Implemented code
  Output: Review feedback, CodeRabbit analysis
  Status: reviewing -> approved

Phase 5: SHIP
  Input:  Approved code
  Output: Deployed to target environment
  Status: shipped
```

### Feature Directory Structure

```
.dotnet-ai-kit/
  features/
    001-order-creation/
      brief.md              # Phase 1: scope and requirements
      spec.md               # Phase 2: technical specification
      status.json           # Current phase and metadata
      implementation-log.md # Phase 3: what was done
      review-notes.md       # Phase 4: review feedback
    002-order-export/
      brief.md
      spec.md
      status.json
```

### status.json Format

```json
{
  "featureId": "001",
  "name": "order-creation",
  "phase": "implementing",
  "createdAt": "2025-03-15T10:00:00Z",
  "updatedAt": "2025-03-16T14:30:00Z",
  "affectedServices": [
    "{domain}-command",
    "{domain}-query",
    "{domain}-gateway"
  ],
  "dependencies": [],
  "assignedAgent": "command-architect"
}
```

### Microservice Feature Flow

```
1. Plan: Identify affected services (command, query, processor, gateway, CP)
2. Spec: Define events, queries, endpoints per service
3. Implement: Start with command side (events), then query, then gateway
4. Review: Review each service, verify cross-service integration
5. Ship: Deploy in dependency order (command first, then query, then gateway)
```

### Generic .NET Feature Flow

```
1. Plan: Identify affected layers (domain, application, infrastructure, API)
2. Spec: Define entities, commands/queries, endpoints
3. Implement: Start with domain, then application, then infrastructure
4. Review: Review full vertical slice
5. Ship: Single deployment
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Implementing without spec | Always write spec before code |
| Skipping review phase | Every feature gets reviewed |
| Not tracking status | Update status.json at each transition |
| Single massive feature | Break into small, deployable increments |

## Detect Existing Patterns

```bash
# Find feature directory
find . -path "*/.dotnet-ai-kit/features/*" -name "status.json"

# Check current feature status
cat .dotnet-ai-kit/features/*/status.json 2>/dev/null

# Find existing specs
find . -path "*/.dotnet-ai-kit/features/*/spec.md"
```

## Adding to Existing Project

1. **Check for `.dotnet-ai-kit/features/` directory** structure
2. **Follow existing feature numbering** — sequential NNN format
3. **Match spec template** from existing features
4. **Update `status.json`** when transitioning phases
5. **For multi-repo features**, coordinate across service repositories
