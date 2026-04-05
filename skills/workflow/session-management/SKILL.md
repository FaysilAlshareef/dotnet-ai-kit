---
name: session-management
description: >
  Session checkpoint, wrap-up, and handoff patterns for AI-assisted development.
  Covers session state persistence, context handoff, and resumption strategies.
  Trigger: session, checkpoint, handoff, wrap-up, resume, context.
metadata:
  category: workflow
  agent: dotnet-architect
  when-to-use: "When managing session checkpoints, wrap-ups, or context handoffs"
---

# Session Management — Checkpoint, Wrap-Up, Handoff

## Core Principles

- Sessions are bounded work periods with clear start and end
- Checkpoints save progress for safe resumption
- Wrap-up summarizes what was done and what remains
- Handoff provides context for the next session/developer
- State is persisted in `.dotnet-ai-kit/sessions/` directory

## Key Patterns

### Session Directory Structure

```
.dotnet-ai-kit/
  sessions/
    2025-03-16-order-creation/
      checkpoint.md        # Current progress snapshot
      decisions.md         # Design decisions made
      next-steps.md        # What to do next
```

### Checkpoint Format

```markdown
# Session Checkpoint

## Date: {date}
## Feature: {feature-name}
## Phase: {current-phase}

## Completed
- [x] Created OrderCreatedData event type
- [x] Implemented Order aggregate with Create factory method
- [x] Added CreateOrderHandler with CommitEventService
- [x] Added FluentValidation for CreateOrderCommand

## In Progress
- [ ] Query-side entity (Order) — started, needs Apply methods
- [ ] Event handler for OrderCreated — not started

## Blocked On
- None

## Files Changed
- src/Domain/Events/OrderCreatedData.cs (new)
- src/Domain/Aggregates/Order.cs (new)
- src/Application/Handlers/CreateOrderHandler.cs (new)
- src/Application/Validators/CreateOrderValidator.cs (new)

## Build Status
- Command project: compiles
- Query project: not started
- Tests: 3 passing, 0 failing
```

### Wrap-Up Summary

```markdown
# Session Wrap-Up

## Summary
Implemented the command side for order creation feature (#001).
All command-side code compiles and passes tests.

## Key Decisions
1. Used decimal for money (not float/double) — consistency with existing
2. OrderCreatedData includes Items list for denormalized projection
3. Validation uses resource strings from Phrases.resx

## What's Left
1. Query-side implementation (entity, event handler, query handler)
2. Gateway endpoint for order creation
3. Integration tests

## Recommended Next Steps
Start with `query-architect` agent to implement:
1. Order query entity with CTO constructor
2. OrderCreatedHandler
3. GetOrdersQuery handler with pagination

## Context for Next Session
- Event types are in shared-contracts repo (already merged)
- Command service is deployable independently
- Proto files for OrderCommands service are ready
```

### Handoff Between Agents

```markdown
# Agent Handoff: command-architect → query-architect

## Context
Order creation feature (#001) command side is complete.
Events are published to `{company}-order-commands` topic.

## What You Need to Know
- Event data type: `OrderCreatedData(CustomerName, Total, List<OrderItemData>)`
- Sequence starts at 1, increments by 1
- SessionId = AggregateId (Guid) for ordered processing

## Your Tasks
1. Create `Order` entity in Query.Domain with CTO constructor
2. Create `OrderCreatedHandler : IRequestHandler<Event<OrderCreatedData>, bool>`
3. Add EF Core configuration for Order entity
4. Add `GetOrdersQuery` with pagination
5. Register event type in EventDeserializer
```

### Resuming a Session

```bash
# Find latest checkpoint
ls -t .dotnet-ai-kit/sessions/*/checkpoint.md | head -1

# Read checkpoint to understand state
cat .dotnet-ai-kit/sessions/{latest}/checkpoint.md

# Check git status since last checkpoint
git log --oneline --since="2025-03-16"
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| No checkpoint before stopping | Always checkpoint before ending session |
| Vague wrap-up ("worked on stuff") | Specific files, decisions, and next steps |
| Missing agent context in handoff | Include event types, topic names, conventions |
| Stale checkpoints | Update checkpoint at each significant milestone |

## Detect Existing Patterns

```bash
# Find session directory
ls -la .dotnet-ai-kit/sessions/ 2>/dev/null

# Find latest session
ls -t .dotnet-ai-kit/sessions/ 2>/dev/null | head -3
```

## Adding to Existing Project

1. **Create session directory** at the start of each work session
2. **Checkpoint regularly** — at minimum before stopping work
3. **Write wrap-up** with specific files changed and decisions made
4. **Include handoff context** when switching between agents or developers
5. **Reference feature directory** for the broader feature context
