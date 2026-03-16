---
description: "Create an implementation plan from a feature specification"
---

# /dotnet-ai.plan — Implementation Planning

You are an AI coding assistant executing the `/dotnet-ai.plan` command.
Your job is to create a detailed implementation plan from an existing feature spec.

## Input

Flags: `--dry-run` (preview without writing), `--verbose` (diagnostic output)

## Step 1: Load Prerequisites

1. Find the active feature in `.dotnet-ai-kit/features/` (most recent or in-progress).
2. Load `spec.md` — required. If missing: "No spec found. Run /dotnet-ai.specify first."
3. Load `.dotnet-ai-kit/config.yml` if it exists.
4. Note any remaining `[NEEDS CLARIFICATION]` markers — warn but do not block.
5. If `--verbose`, print loaded artifacts and detected mode.

## Step 2: Detect Project Mode

1. From config or spec content, determine: **generic** or **microservice**.
2. Load skills on demand based on mode:
   - Always: `skills/workflow/sdd-lifecycle/SKILL.md`
   - Generic: `skills/architecture/clean-architecture/SKILL.md` or `skills/architecture/vertical-slice/SKILL.md` (based on detected pattern)
   - Microservice: `skills/workflow/multi-repo-workflow/SKILL.md`

## Step 3: Constitution Check Gate

Read `.specify/memory/constitution.md` and verify the plan will comply:
- Detect-First: plan must research existing code before proposing changes
- Pattern Fidelity: plan must follow detected conventions
- Architecture Agnostic: plan must match the project's architecture, not impose one

Document the check result in the plan under `## Constitution Check`.
If violations found, document them in `## Complexity Tracking` with justification.

## Step 4: Research Phase

Scan the existing codebase for patterns:
- Folder structure and naming conventions
- Existing entities, handlers, services (what patterns are already used)
- NuGet packages and framework versions
- DI registration patterns
- Test project structure and frameworks

If `--verbose`, print discovered patterns.

## Step 5: Generate Plan (Mode-Specific)

### Generic .NET Mode

Create `plan.md` in the feature directory:

```markdown
# Implementation Plan: {Feature Name}

**Feature**: {NNN}-{short-name} | **Date**: {DATE} | **Mode**: Generic
**Spec**: spec.md

## Summary
{1-2 sentence overview of what will be built}

## Constitution Check
{PASS/FAIL with notes}

## Technical Context
**Framework**: .NET {version} | **Architecture**: {detected pattern}
**Test Framework**: {detected} | **Key Packages**: {list}

## Research Findings
{Summary of existing patterns discovered in Step 4}

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

### Microservice Mode

Create multiple artifacts in the feature directory:

**plan.md** — overall plan with per-service breakdown:
```markdown
# Implementation Plan: {Feature Name}

**Feature**: {NNN}-{short-name} | **Date**: {DATE} | **Mode**: Microservice

## Summary
## Constitution Check
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
- Handlers: {list}

### {domain}-gateway
- Endpoints: {list}
- Proto clients: {list}

### {domain}-controlpanel (if applicable)
- Pages: {list}
- Facades: {list}

## Dependency Order
command → query/processor (parallel) → gateway → controlpanel
```

**service-map.md** — visual service dependency map:
```markdown
# Service Map: {Feature Name}
{Mermaid diagram of service dependencies}
{Per-service: repo URL, branch name, change summary}
```

**event-flow.md** — event flow documentation:
```markdown
# Event Flow: {Feature Name}
{Mermaid sequence diagram}
{Event catalogue: name, publisher, subscribers, data schema}
```

**contracts/** directory — proto definitions and API contracts:
- Create `.proto` stubs or contract descriptions for new services
- Reference existing protos that need updates

Load additional skills for microservice artifacts:
- `skills/microservice/command/event-design/SKILL.md` for event schemas
- `skills/microservice/grpc/service-definition/SKILL.md` for proto contracts

## Step 6: Report

```
Plan generated for {NNN}-{short-name}.
Mode: {generic|microservice}
Constitution: {PASS|FAIL with count}

Artifacts created:
- plan.md {lines}
{if microservice:}
- service-map.md
- event-flow.md
- contracts/ ({N} files)

{If unresolved clarifications:}
WARNING: {N} [NEEDS CLARIFICATION] markers from spec carried into plan.

Next: /dotnet-ai.tasks    (generate implementation tasks)
      /dotnet-ai.analyze  (check consistency first)
```

## Dry-Run Behavior

When `--dry-run` is active:
- Print the full plan content to the terminal
- Show all file paths that WOULD be created
- Do NOT write any files
- Prefix output with `[DRY-RUN]`

## Error Handling

- Missing spec: direct user to `/dotnet-ai.specify`
- Missing config: proceed with auto-detection, warn user
- Constitution violations: document but do not block (user decides)
