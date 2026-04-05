# dotnet-ai-kit - Handoff Schemas

## Overview

Define exact markdown schemas for all feature artifact files. These schemas enable consistent communication between agents and commands across the SDD lifecycle.

All files live in `.dotnet-ai-kit/features/NNN-feature-name/`.

---

## Generic Mode Summary

For generic .NET projects (VSA, Clean Arch, DDD), the following applies:

| Schema | Applies? | Adaptation |
|--------|----------|------------|
| 1. spec.md | Yes | Uses "Architecture Scope" section instead of "Service Map" |
| 2. plan.md | Yes | No service map, no proto definitions. Uses layer-based phases (Domain → Application → Infrastructure → API) |
| 3. service-map.md | No | Not created. Single-repo, no service dependencies |
| 4. tasks.md | Yes | Phases organized by layer, not by service. No `[Repo:*]` prefix needed |
| 5. analysis.md | Yes | Passes: Architecture Consistency, Layer Boundaries, Naming, Coverage Gaps, Concurrency |
| 6. review.md | Yes | Same structure, no proto/cross-service checks |
| 7. handoff.md | Yes | Single repo in status table |
| 8. event-catalogue/ | No | Not created. No event sourcing in generic mode |

Generic mode uses 6 of 8 schemas. Schemas 3 and 8 are microservice-only.

---

## 1. spec.md — Feature Specification

Created by: `/dotnet-ai.specify`
Read by: All agents, `/dotnet-ai.clarify`, `/dotnet-ai.plan`

### Schema

```markdown
---
feature_id: "NNN"
feature_name: "short-name"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
status: "draft | clarified | planned | in-progress | completed"
mode: "microservice | generic"
---

# Feature: {Feature Title}

## Description
{Natural language description of the feature}

## User Stories
- [ ] [P1] As a {role}, I want to {action} so that {benefit}
- [ ] [P2] ...
- [ ] [P3] ...

## Service Map (microservice mode only)
| Service | Repo | Status | Changes |
|---------|------|--------|---------|
| Command | {repo-path-or-url} | EXISTS/CREATE NEW | + {changes} |
| Query | ... | ... | ... |
| Processor | ... | ... | ... |
| Gateway | ... | ... | ... |
| ControlPanel | ... | ... | ... |

## Architecture Scope (generic mode only)
| Layer | Changes |
|-------|---------|
| Domain | + {entities, value objects, events} |
| Application | + {commands, queries, handlers} |
| Infrastructure | + {repositories, services} |
| API | + {endpoints} |

## Events
| Event | Producer | Consumers | Data Schema |
|-------|----------|-----------|-------------|
| {EventName} | {Service} | {Service1, Service2} | {DataRecord fields} |

## Entities
| Entity | Service | Type | Key Fields |
|--------|---------|------|------------|
| {Name} | {Service} | New/Modified | {fields} |

## Endpoints
| Method | Path | Service | Description |
|--------|------|---------|-------------|
| GET | /api/v1/{resource} | Gateway | {description} |

## Pages (if applicable)
| Page | Module | Description |
|------|--------|-------------|
| {PageName} | {Module} | {description} |

## Clarifications
| # | Question | Answer | Date |
|---|----------|--------|------|
| 1 | {question} | {answer} | YYYY-MM-DD |

## [NEEDS CLARIFICATION] Markers
- [ ] {Unresolved item 1}
- [ ] {Unresolved item 2}

## Quality Checklist
- [ ] All user stories have acceptance criteria
- [ ] Events have data schemas defined
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Service map is complete (microservice) / layer scope defined (generic)
```

### Field Rules
- `feature_id`: Auto-incremented 3-digit number (001, 002, ...)
- `status`: Updated by each command (specify->draft, clarify->clarified, plan->planned, implement->in-progress, pr->completed)
- `mode`: Set by `/dotnet-ai.init` or detected from project
- Service Map: Only in microservice mode. Status is EXISTS or CREATE NEW
- Architecture Scope: Only in generic mode
- Max 3 [NEEDS CLARIFICATION] markers on initial creation
- Clarifications section grows as `/dotnet-ai.clarify` resolves items

---

## 2. plan.md — Implementation Plan

Created by: `/dotnet-ai.plan`
Read by: `/dotnet-ai.tasks`, `/dotnet-ai.implement`, `/dotnet-ai.analyze`

### Schema

````markdown
---
feature_id: "NNN"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
status: "draft | approved | in-progress | completed"
unresolved_markers: 0
---

# Implementation Plan: {Feature Title}

## Research Summary
{What was discovered by scanning existing repos}

### Existing Patterns Found
| Repo | Pattern | Notes |
|------|---------|-------|
| {repo} | {pattern found} | {how to follow it} |

### .NET Versions Detected
| Repo | Version | Key Implications |
|------|---------|-----------------|
| {repo} | net{X}.0 | {version-specific notes} |

## Service Map (microservice mode)
{Copied from spec, enriched with details}

| Service | Repo | Status | .NET Version | Changes |
|---------|------|--------|--------------|---------|
| Command | {path/url} | EXISTS | net10.0 | + OrderAggregate, + 3 events, + 2 handlers |

### Per-Feature Repo Overrides
{Only if different from config.yml}
| Service | Override Path | Reason |
|---------|--------------|--------|
| Gateway | {path} | {reason for override} |

## Event Design

### New Events
| Event | Aggregate | Data Fields | Topic |
|-------|-----------|-------------|-------|
| OrderCreated | Order | OrderId, CustomerId, Items[], CreatedAt | {company}-order-commands |

### Event Flow
```
{EventName} (Command)
  → {HandlerName} (Query) → {action}
  → {ListenerName} (Processor) → {action}
```

## Contract Design

### Proto Definitions
| Proto File | Service | Role | Methods |
|------------|---------|------|---------|
| order_commands.proto | Command | Server | CreateOrder, UpdateOrder |
| order_queries.proto | Query | Server, Gateway(Client) | GetOrder, GetOrders |

### API Contracts (Gateway)
| Endpoint | Method | Request Body | Response |
|----------|--------|--------------|----------|
| /api/v1/orders | POST | CreateOrderRequest | OrderOutput |

## Implementation Phases
| Phase | Services | Dependency |
|-------|----------|------------|
| 1 | Command | None (first) |
| 2 | Query, Processor | After Phase 1 |
| 3 | Gateway | After Phase 2 |
| 4 | ControlPanel | After Phase 3 |

## Risks & Decisions
| # | Decision/Risk | Resolution |
|---|--------------|------------|
| 1 | {decision or risk} | {resolution} |
````

### Field Rules
- `unresolved_markers`: Count of remaining [NEEDS CLARIFICATION] from spec. Carried forward as warnings.
- Per-Feature Repo Overrides: Stored here, NOT in config.yml. Apply only to this feature.
- Implementation Phases: Define the dependency order for `/dotnet-ai.tasks` to follow.
- For generic mode: no service map, no proto definitions. Uses layer-based phases instead.

---

## 3. service-map.md — Service Dependency Map (Microservice Only)

Created by: `/dotnet-ai.plan`
Read by: `/dotnet-ai.implement`, `/dotnet-ai.analyze`

### Schema

````markdown
---
feature_id: "NNN"
created: "YYYY-MM-DD"
---

# Service Map: {Feature Title}

## Services
| Service | Repo | Status | .NET | Changes Summary |
|---------|------|--------|------|-----------------|
| Command | {repo} | EXISTS | net10.0 | + OrderAggregate, +3 events |
| Query | {repo} | EXISTS | net9.0 | + Order entity, +3 handlers, +2 queries |
| Processor | {repo} | EXISTS | net10.0 | + OrderListener, +2 routing handlers |
| Gateway | {repo} | CREATE NEW | net10.0 | Full project scaffold |
| ControlPanel | {repo} | EXISTS | net9.0 | + Orders module |

## Dependency Graph
```
Command ──→ Query ──→ Gateway ──→ ControlPanel
       └──→ Processor ──┘
```

## Communication Patterns
| From | To | Method | Details |
|------|----|--------|---------|
| Command | Query | Azure Service Bus | Topic: {company}-order-commands |
| Command | Processor | Azure Service Bus | Topic: {company}-order-commands |
| Gateway | Query | gRPC | order_queries.proto |
| Gateway | Command | gRPC | order_commands.proto |
| ControlPanel | Gateway | REST/HTTP | /api/v1/orders/* |

## New Proto Definitions
| File | Server | Clients |
|------|--------|---------|
| order_commands.proto | Command | Gateway |
| order_queries.proto | Query | Gateway |
````

---

## 4. tasks.md — Task List

Created by: `/dotnet-ai.tasks`
Read by: `/dotnet-ai.implement`

### Schema

```markdown
---
feature_id: "NNN"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
total_tasks: 0
completed_tasks: 0
failed_task: null
---

# Tasks: {Feature Title}

## Phase 1: Setup
- [ ] T001 [Repo:all] Clone repos and create feature branches

## Phase 2: Command Side
- [ ] T002 [Repo:command] Create OrderAggregate with OrderCreated event
      Files: Domain/Aggregates/Order.cs, Domain/Events/OrderCreated.cs
- [ ] T003 [Repo:command] Add OrderUpdated event to OrderAggregate
      Files: Domain/Events/OrderUpdated.cs
- [ ] T004 [Repo:command] Implement CreateOrderHandler
      Files: Application/Commands/CreateOrderHandler.cs
- [ ] T005 [Repo:command] Add proto definitions
      Files: Grpc/Protos/order_commands.proto
- [ ] T006 [Repo:command] Add unit tests
      Files: Test/Commands/CreateOrderHandlerTests.cs

## Phase 3: Query Side + Processor
- [ ] T007 [P] [Repo:query] Create Order entity with event constructors
      Files: Domain/Entities/Order.cs
- [ ] T008 [P] [Repo:query] Add OrderCreatedHandler
      Files: Application/EventHandlers/OrderCreatedHandler.cs
- [ ] T009 [P] [depends: T007] [Repo:query] Add GetOrdersQuery handler
      Files: Application/Queries/GetOrdersHandler.cs
- [ ] T010 [P] [Repo:processor] Add OrderListener
      Files: Application/Listeners/OrderListener.cs

## Phase 4: Gateway
- [ ] T011 [depends: T005] [Repo:gateway] Register gRPC clients
      Files: Infra/GrpcRegistration.cs
- [ ] T012 [Repo:gateway] Create OrderController with endpoints
      Files: Controllers/OrderController.cs

## Phase 5: Control Panel
- [ ] T013 [depends: T012] [Repo:controlpanel] Add OrdersGateway facade
      Files: API/Orders/OrdersGateway.cs
- [ ] T014 [Repo:controlpanel] Create Orders page
      Files: Presentation/Orders/OrdersPage.razor

## Phase 6: Documentation
- [ ] T015 [P] [Repo:all] Update README per repo
- [ ] T016 [P] [Repo:all] Add/update API documentation

## Phase 7: Review & Verify
- [ ] T017 [Repo:all] Run standards review
- [ ] T018 [Repo:all] Run verification pipeline
```

### Field Rules
- Task ID: `T{NNN}` sequential across all phases
- `[Repo:{name}]`: Which repo this task targets (command, query, processor, gateway, controlpanel, all)
- `[P]`: Can run in parallel with previous task
- `[depends: T{NNN}]`: Blocked until specified task completes
- No notation = depends on previous task (sequential)
- `Files:` line: Expected file paths (relative to repo root). Indented under the task.
- Status: `[ ]` = pending, `[x]` = completed, `[!]` = failed
- `failed_task` in frontmatter: Set to task ID if implementation stopped due to failure
- `/dotnet-ai.implement --resume` reads this to find where to continue
- For generic mode: phases are by layer (Domain -> Application -> Infrastructure -> API) instead of by service

---

## 5. analysis.md — Cross-Service Analysis

Created by: `/dotnet-ai.analyze`
Read by: `/dotnet-ai.implement` (warnings), `/dotnet-ai.review`

### Schema

```markdown
---
feature_id: "NNN"
created: "YYYY-MM-DD"
total_findings: 0
critical: 0
high: 0
medium: 0
low: 0
---

# Analysis: {Feature Title}

## Summary
{total} findings: {critical} CRITICAL, {high} HIGH, {medium} MEDIUM, {low} LOW

## Findings

### CRITICAL
| # | Category | Location | Finding | Suggested Fix |
|---|----------|----------|---------|---------------|
| 1 | Event Consistency | command/OrderCreated → query | Missing handler for OrderCreated in query service | Add OrderCreatedHandler |

### HIGH
| # | Category | Location | Finding | Suggested Fix |
|---|----------|----------|---------|---------------|

### MEDIUM
| # | Category | Location | Finding | Suggested Fix |
|---|----------|----------|---------|---------------|

### LOW
| # | Category | Location | Finding | Suggested Fix |
|---|----------|----------|---------|---------------|

## Analysis Passes Run
- [x] Event Consistency
- [x] Proto Consistency
- [x] Naming Consistency
- [x] Coverage Gaps
- [x] Sequence Gaps
- [x] Cross-Repo Dependencies
- [x] Event Catalogue Completeness
- [x] Event Version Compatibility
- [x] Concurrency & Idempotency
```

### Field Rules
- Max 50 findings total
- Categories: Event Consistency, Proto Consistency, Naming Consistency, Coverage Gaps, Sequence Gaps, Cross-Repo Dependencies, Event Catalogue, Event Version Compatibility, Concurrency/Idempotency
- CRITICAL findings are logged and warned on `/dotnet-ai.implement` but do NOT block it
- For generic mode: analysis passes are Architecture Consistency, Layer Boundaries, Naming, Coverage Gaps, Concurrency

---

## 6. review.md — Review Report

Created by: `/dotnet-ai.review`
Read by: `/dotnet-ai.pr`

### Schema

```markdown
---
feature_id: "NNN"
created: "YYYY-MM-DD"
overall_status: "PASS | NEEDS FIXES | FAIL"
auto_fix_applied: false
coderabbit_used: false
---

# Review: {Feature Title}

## Summary
Reviewed changes across {N} repos. {N} issues need fixing.

## Per-Repo Results

### {Repo Name} ({PASS | NEEDS FIXES | FAIL})

| Category | Status | Findings |
|----------|--------|----------|
| Architecture | PASS/WARN/FAIL | {count or -} |
| Naming | PASS/WARN/FAIL | - |
| Localization | PASS/WARN/FAIL | - |
| Error Handling | PASS/WARN/FAIL | - |
| Testing | PASS/WARN/FAIL | - |
| Security | PASS/WARN/FAIL | - |
| CodeRabbit | PASS/WARN/SKIP | - |

**Findings:**
1. [{FAIL|WARN|SUGGESTION}] `{file}:{line}` - {description}
   → Fix: {suggested fix}
   → Source: Standards / CodeRabbit

{Repeat for each repo}

## Auto-Fix Summary
| # | File | Change | Status |
|---|------|--------|--------|
| 1 | {file} | {change} | Applied / Skipped / Pending |
```

---

## 7. handoff.md — Session Handoff

Created by: `/dotnet-ai.checkpoint`, `/dotnet-ai.wrap-up`
Read by: Next session (via `/dotnet-ai.specify` resume)

### Schema

```markdown
---
feature_id: "NNN"
session_date: "YYYY-MM-DD"
session_type: "checkpoint | wrap-up"
---

# Session Handoff: {Feature Title}

## Completed This Session
- {What was accomplished, per repo}

## Pending Tasks
- {Tasks remaining, with task IDs from tasks.md}

## Blocked Items
- {Items that couldn't proceed, with reason}

## Context for Next Session
- {Key decisions made}
- {Patterns discovered in existing code}
- {Any deviations from plan and why}

## Repos Status
| Repo | Branch | Committed | Pushed | PR |
|------|--------|-----------|--------|-----|
| {repo} | feature/{NNN}-{name} | Yes/No | Yes/No | {url or -} |

## Learnings
- {Patterns or conventions discovered that should inform future work}
```

---

## 8. event-catalogue/ — Event Catalogue (Microservice Only)

Created by: `/dotnet-ai.plan`, updated by `/dotnet-ai.implement`
Read by: `/dotnet-ai.analyze`

### Directory Structure

```
features/NNN-feature-name/event-catalogue/
├── command-events.md
├── query-handlers.md
└── processor-routing.md
```

### command-events.md Schema

```markdown
# Event Catalogue: Command Side

## Events Produced

### {EventName}
- **Aggregate**: {AggregateName}
- **Version**: {N}
- **Topic**: {company}-{domain}-commands
- **Data Schema**: {DataRecord} { Field1 Type, Field2 Type, ... }
- **Idempotency**: Client-sent ID
- **Consumers**: {list of services/handlers}
```

### query-handlers.md Schema

```markdown
# Event Catalogue: Query Side

## Events Consumed

### {EventName}
- **Source**: Command ({AggregateName})
- **Handler**: {HandlerName}
- **Entity**: {EntityName}
- **Action**: Create / Update / Delete
- **Sequence Check**: Yes (strict)
- **Idempotent**: Yes (returns true if already processed)
```

### processor-routing.md Schema

```markdown
# Event Catalogue: Processor

## Events Routed

### {EventName}
- **Source**: Command ({AggregateName})
- **Listener**: {ListenerName}
- **Routing**: {subject-based / direct}
- **Action**: {gRPC call to service / notification / etc.}
- **Error Handling**: {retry / dead-letter / abandon}
```

---

## Schema Validation Rules

1. **Feature ID Consistency**: All files in a feature directory MUST have the same `feature_id`
2. **Status Progression**: spec.status follows: draft -> clarified -> planned -> in-progress -> completed
3. **Event Consistency**: Events in spec.md must appear in plan.md event design and event-catalogue/
4. **Task Coverage**: Every entity/event/endpoint in spec.md must have at least one task in tasks.md
5. **Repo Consistency**: Repos referenced in tasks.md must match service-map.md
6. **Date Format**: Always YYYY-MM-DD
7. **Generic Mode**: Files marked "(microservice only)" are not created. Generic mode uses Architecture Scope instead of Service Map.

---

## 9. feature-brief.md — Cross-Repo Feature Projection *(microservice only)*

Created by: `/dotnet-ai.specify`
Written to: Each secondary repo at `.dotnet-ai-kit/features/{NNN}-{name}/feature-brief.md`
Read by: `/dai.plan`, `/dai.implement` in each secondary repo

### Schema

```markdown
---
feature_id: "NNN-short-name"
feature_name: "Human Readable Name"
phase: "Specified | Planned | In-Progress | Completed"
projected_date: "YYYY-MM-DD"
source_repo: "company-domain-command"
source_repo_path: "/absolute/or/github:org/repo"
this_repo_role: "query | processor | gateway | controlpanel | command"
---

# Feature Brief: {Feature Title}

## Required Changes for This Repo

{Filtered subset of changes relevant to this repo's role.
Derived from spec.md Service Map section.}

## Events Consumed

| Event | Source Service | Contract Location |
|-------|---------------|-------------------|
| OrderCreated | command | contracts/events/order-created.proto |

## Events Produced

| Event | Consumers | Contract Location |
|-------|-----------|-------------------|
| OrderProjected | gateway | contracts/events/order-projected.proto |

## Notes

{Any cross-repo coordination notes for this repo.}
```

### Constraints

- `feature_id` MUST match the primary repo's feature directory name exactly
- `phase` is updated by each lifecycle command as it runs in the secondary repo
- `this_repo_role` MUST match the role in `service-map.md`
- `events_consumed` / `events_produced` lists are filtered from the primary's spec.md — only events relevant to this repo are included
