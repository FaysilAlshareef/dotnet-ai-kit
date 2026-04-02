---
alwaysApply: true
description: "Architecture profile for hybrid (command+query) projects — hard constraints"
---

# Architecture Profile: Hybrid (Command + Query Combined)

This profile applies to microservices that host both command and query responsibilities.
Only the highest-severity constraints from each side are included.

## HARD CONSTRAINTS

### Aggregate Boundaries (from Command)
- ALWAYS one aggregate per command handler/transaction — NEVER load multiple aggregates
- ALWAYS use static factory methods for aggregate creation — NEVER `new Aggregate()` in handlers
- ALWAYS use `LoadFromHistory(events)` to rebuild aggregates — NEVER manual construction
- ALWAYS use private setters on aggregate state — NEVER public setters
- MUST validate domain invariants inside the aggregate — NEVER in handlers

```csharp
// ANTI-PATTERN: multiple aggregates
var order = Order.LoadFromHistory(orderEvents);
var invoice = Invoice.LoadFromHistory(invoiceEvents); // NEVER in same handler
```

### Event Immutability (from Command)
- NEVER modify existing event schemas — events are immutable once published
- NEVER remove fields or change field types — create new versioned records
- ALWAYS use immutable records for event data
- ALWAYS save events and outbox messages in a single `SaveChangesAsync` — NEVER publish first
- MUST pass the aggregate to `CommitNewEventsAsync` — NEVER pass events list directly

### Event Handler Idempotency (from Query)
- ALWAYS return `bool` from event handlers — `true` for CompleteMessage, `false` for Abandon
- NEVER throw exceptions in event handlers — return `false` for retry scenarios
- Creation handlers: return `true` if entity already exists (idempotent duplicate)
- Update handlers: MUST use the exact sequence guard — no variations

```csharp
// THE ONLY CORRECT SEQUENCE GUARD:
if (entity.Sequence != @event.Sequence - 1)
    return entity.Sequence >= @event.Sequence;
```

### Sequence Checking (from Query)
- Every query entity MUST track `int Sequence { get; private set; }`
- ALWAYS inline the sequence check in each handler — NEVER a helper class
- Already-processed events (Sequence >= event.Sequence) MUST return `true`
- Gap events (Sequence < event.Sequence - 1) MUST return `false` for retry
- Entity behavior methods MUST update `Sequence` as the last operation

### Read-Model Entities (from Query)
- ALWAYS use `{ get; private set; }` on all query entity properties
- MUST use private constructor with ALL parameters for EF Core
- MUST use the `(TData data, int sequence)` signature for behavior methods
- NEVER access command-side aggregates from query handlers
- NEVER write to the event store from query-side code

### Cross-Side Boundaries
- Command-side and query-side MUST use separate `IUnitOfWork` implementations
- NEVER share DbContext between command and query sides
- Command-side uses `IEventRepository` and `IOutboxMessagesRepository`
- Query-side uses named repository properties (`_unitOfWork.Orders`)
- Event handlers on query side receive `Event<TData>` envelopes — not raw aggregates

### Outbox Pattern (from Command)
- MUST use OutboxMessage FK pattern (shared PK with Event) — NEVER serialize event body
- `ServiceBusPublisher` MUST be singleton with `lock` + `Task.Run` pattern
- ALWAYS call `StartPublish()` fire-and-forget after DB save

## Testing Requirements

- MUST test aggregate creation and update through full command handler flow
- MUST test event handler idempotency with duplicate events (returns `true`)
- MUST test event handler sequence gaps (returns `false`)
- MUST verify events persisted in DB AND outbox messages created
- MUST use `WebApplicationFactory<Program>` for integration tests

## Data Access

- Command side: `IUnitOfWork` with `Events` and `OutboxMessages` repositories
- Query side: `IUnitOfWork` with named entity repositories
- MUST maintain unique index on `(AggregateId, Sequence)` in event store
- MUST use `AsNoTracking()` for event loading on command side
- Query-side entities use EF Core tracking (no `AsNoTracking` in handlers)
