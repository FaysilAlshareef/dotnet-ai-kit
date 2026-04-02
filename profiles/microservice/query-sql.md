---
alwaysApply: true
description: "Architecture profile for query (SQL) projects — hard constraints"
---

# Architecture Profile: Query — SQL Read Model

## HARD CONSTRAINTS

### Read-Model Entities
- ALWAYS use `{ get; private set; }` on every property — NEVER expose public setters
- ALWAYS include `int Sequence { get; private set; }` for idempotency tracking
- MUST use private constructor with ALL parameters for EF Core materialization — NEVER parameterless
- ALWAYS use `List<T>` initialized with `= []` for navigation collections
- MUST update `Sequence` in every behavior method — NEVER leave it stale
- NEVER add business logic beyond data projection — entities are pure read models

```csharp
// ANTI-PATTERN: public setters
public string CustomerName { get; set; } // WRONG
public string CustomerName { get; private set; } // CORRECT

// ANTI-PATTERN: missing sequence update
public void UpdateDetails(OrderUpdatedData data, int sequence)
{
    CustomerName = data.CustomerName;
    // WRONG — missing: Sequence = sequence;
}
```

### Event Handler Idempotency
- ALWAYS implement `IRequestHandler<Event<TData>, bool>` — return bool, NEVER void
- Return `true` to CompleteMessage, `false` to AbandonMessage — NEVER throw exceptions in handlers
- Creation handlers: MUST check entity existence, return `true` if duplicate (idempotent)
- Update handlers: MUST use the exact sequence guard pattern — no variations

```csharp
// THE ONLY CORRECT SEQUENCE GUARD — use this exact pattern:
if (entity.Sequence != @event.Sequence - 1)
    return entity.Sequence >= @event.Sequence;

// ANTI-PATTERN: separate if statements
if (@event.Sequence <= entity.Sequence) return true;  // WRONG
if (@event.Sequence > entity.Sequence + 1) return false; // WRONG
```

### Sequence Checking Rules
- ALWAYS inline the sequence check in each handler — NEVER create a `SequenceChecker` helper class
- Duplicate events (entity.Sequence >= event.Sequence) MUST return `true` — NEVER `false`
- Gap events (entity.Sequence < event.Sequence - 1) MUST return `false` for retry
- Entity not found on update events MUST return `false` — NEVER throw NotFoundException

### No Aggregate Access
- NEVER import or reference command-side aggregate classes from query handlers
- NEVER write directly to the event store from query-side code
- NEVER use `ApplyChange` or aggregate factory methods in query projects
- Query entities receive state from `Event<TData>` envelopes only

### Query Handler Patterns
- ALWAYS use `IUnitOfWork` with named repository properties — NEVER `_unitOfWork.Repository<T>()`
- ALWAYS delegate filtering and pagination to repository methods — NEVER filter in handlers
- MUST use `class` output types with `{ get; set; }` properties — NEVER `record` for outputs
- MUST map to output DTOs in handler — NEVER return entities directly
- ALWAYS pass `CancellationToken` to `SaveChangesAsync` — NEVER omit it

### Listener Pattern
- MUST use `IHostedService` with `ServiceBusSessionProcessor` — NEVER `BackgroundService` for listeners
- MUST set `AutoCompleteMessages = false` — NEVER auto-complete
- MUST pair every session processor with a DLQ processor in the same listener
- MUST use `CloseAsync` in StopAsync — NEVER `StopProcessingAsync`
- ALWAYS use inline subject routing via switch expression — NEVER separate EventRouter class
- ALWAYS push Serilog `PropertyEnricher` for EventType, SessionId, MessageId

## Testing Requirements

- MUST test creation handlers with duplicate events to verify idempotent `true` return
- MUST test update handlers with sequence gaps to verify `false` return
- MUST test update handlers with already-processed sequences to verify `true` return
- MUST test entity-not-found scenarios to verify `false` return

## Data Access

- ALWAYS use `IUnitOfWork` with named properties (`_unitOfWork.Orders`, not generic)
- List queries return output DTOs with `PageSize`, `CurrentPage`, `Total`, and collection
- Single queries use `FindAsync` then map to output DTO
- NEVER use `AsNoTracking()` in handlers — let repository/infrastructure handle tracking
