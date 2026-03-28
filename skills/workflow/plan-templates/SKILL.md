---
name: plan-templates
description: "Mode-specific plan templates for /dotnet-ai.plan"
---

# Plan Templates Skill

Generate the plan.md structure based on project mode.

## Generic .NET Mode

```markdown
# Implementation Plan: {Feature Name}

**Feature**: {NNN}-{short-name} | **Date**: {DATE} | **Mode**: Generic
**Spec**: spec.md

## Summary
{1-2 sentence overview}

## Constitution Check
Source: `.dotnet-ai-kit/memory/constitution.md`
{PASS/FAIL with notes}

## Technical Context
**Framework**: .NET {version} | **Architecture**: {detected pattern}
**Test Framework**: {detected} | **Key Packages**: {list}

## Research Findings
{Summary of existing patterns from codebase scan}

## Layer Plan

### Domain Layer
- Entities: {list with file paths}
- Value Objects: {list}
- Domain Events: {list}

### Application Layer
- Commands: {list with handlers}
- Queries: {list with handlers}
- Validators: {list}
- Interfaces: {list}

### Infrastructure Layer
- Repositories: {list}
- Services: {list}
- Configurations: {EF configs, DI registrations}

### API Layer
- Endpoints: {list with HTTP methods and paths}
- DTOs: {request/response models}
- Mapping: {profiles or extensions}

## Complexity Tracking
{Only if constitution violations need justification}
```

## Microservice Mode

**plan.md** — per-service breakdown:
```markdown
# Implementation Plan: {Feature Name}

**Feature**: {NNN}-{short-name} | **Date**: {DATE} | **Mode**: Microservice

## Summary
## Constitution Check
Source: `.dotnet-ai-kit/memory/constitution.md`
## Research Findings

## Service Plan
### {domain}-command
- Aggregates: {list}
- Events: {list with data schemas}
- Commands: {list}

### {domain}-query
- Entities: {list}
- Event Handlers: {list}
- Queries: {list}

### {domain}-processor (if applicable)
- Listeners: {list}
- Handlers: {list — what each handler forwards to}

### {domain}-gateway
- Endpoints: {list}
- Proto clients: {list}

### {domain}-controlpanel (if applicable)
- Pages: {list}
- Facades: {list}

## Dependency Order
command → query/processor (parallel) → gateway → controlpanel
```

**service-map.md** — Mermaid diagram of service dependencies + per-service change summary.

**event-flow.md** — Mermaid sequence diagram + event catalogue (name, publisher, subscribers, data schema).

**contracts/** — Proto definitions, event schemas for new/updated services.
