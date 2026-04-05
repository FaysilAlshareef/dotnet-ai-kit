---
name: adr
description: >
  Architecture Decision Records using MADR format. Covers numbered sequence,
  status lifecycle, decision documentation, and cross-references.
  Trigger: ADR, architecture decision, MADR, decision record.
metadata:
  category: docs
  agent: docs-engineer
  when-to-use: "When writing or reviewing Architecture Decision Records"
---

# ADR — Architecture Decision Records

## Core Principles

- ADRs capture important architecture decisions and their context
- Use MADR (Markdown Any Decision Records) format
- Numbered sequentially: `0001-use-event-sourcing.md`
- Status lifecycle: proposed -> accepted -> deprecated/superseded
- Stored in `docs/adr/` directory
- Index file lists all ADRs with status

## Key Patterns

### MADR Template

```markdown
# {NUMBER}. {Title}

Date: {YYYY-MM-DD}

## Status

{Proposed | Accepted | Deprecated | Superseded by [ADR-NNNN](NNNN-title.md)}

## Context

{What is the issue? What forces are at play?
Include technical and business context.}

## Decision

{What is the change that we're proposing and/or doing?
State the decision clearly.}

## Consequences

### Positive
- {Benefit 1}
- {Benefit 2}

### Negative
- {Trade-off 1}
- {Trade-off 2}

### Neutral
- {Side effect that is neither clearly positive nor negative}

## References
- [Related ADR](NNNN-related.md)
- [External reference](https://...)
```

### Example ADR

```markdown
# 0001. Use Event Sourcing for Command Side

Date: 2025-01-15

## Status

Accepted

## Context

We need to build a microservice system that supports:
- Complete audit trail of all state changes
- Temporal queries (what was the state at time X?)
- Reliable event-driven communication between services
- CQRS pattern with separate read/write models

Traditional CRUD would lose change history and make event-driven
communication harder to implement reliably.

## Decision

We will use Event Sourcing on the command side of all microservices:
- Events are the source of truth for all state changes
- Aggregates produce events via factory methods and ApplyChange
- Events are stored in SQL Server with discriminator pattern
- Outbox pattern ensures reliable event publishing to Service Bus

## Consequences

### Positive
- Complete audit trail of every change
- Natural fit for event-driven architecture
- Enables temporal queries and event replay
- Decouples command and query models

### Negative
- Higher complexity than simple CRUD
- Event schema evolution needs careful management
- Developers need to learn event sourcing patterns

### Neutral
- Query side is eventually consistent (acceptable for our use cases)
- Need separate read models for query optimization

## References
- [0002. Use Azure Service Bus for Inter-Service Communication](0002-use-azure-service-bus.md)
- [Event Sourcing Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)
```

### ADR Index

```markdown
# Architecture Decision Records

| ADR | Title | Status | Date |
|---|---|---|---|
| [0001](0001-use-event-sourcing.md) | Use Event Sourcing for Command Side | Accepted | 2025-01-15 |
| [0002](0002-use-azure-service-bus.md) | Use Azure Service Bus | Accepted | 2025-01-15 |
| [0003](0003-use-cosmos-for-reports.md) | Use Cosmos DB for Report Queries | Accepted | 2025-02-01 |
| [0004](0004-replace-swagger-with-scalar.md) | Replace Swagger UI with Scalar | Accepted | 2025-03-01 |
```

### Creating a New ADR

```bash
# Find next number
ls docs/adr/*.md | tail -1
# Create new ADR
cp docs/adr/template.md docs/adr/0005-{title}.md
# Update index
echo "| [0005](0005-{title}.md) | {Title} | Proposed | $(date +%Y-%m-%d) |" >> docs/adr/README.md
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Not recording decisions | Write ADR for every significant decision |
| Missing context section | Always explain why the decision was needed |
| No consequences analysis | Include positive, negative, and neutral |
| Deleting old ADRs | Mark as deprecated or superseded, never delete |
| ADRs without dates | Always include the decision date |

## Detect Existing Patterns

```bash
# Find ADR directory
find . -path "*/adr/*" -name "*.md"

# Find ADR index
find . -name "README.md" -path "*/adr/*"

# Count existing ADRs
ls docs/adr/*.md 2>/dev/null | wc -l
```

## Adding to Existing Project

1. **Create `docs/adr/` directory** if it doesn't exist
2. **Continue numbering** from existing ADRs
3. **Use the MADR template** consistently
4. **Update the index** when adding new ADRs
5. **Cross-reference** related ADRs and external documentation
