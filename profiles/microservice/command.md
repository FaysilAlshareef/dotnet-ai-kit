---
alwaysApply: true
description: "Architecture profile for command projects — hard constraints"
---

# Architecture Profile: Command (Event-Sourced CQRS)

## HARD CONSTRAINTS

### Aggregate Boundaries
- ALWAYS one aggregate per command handler — NEVER load or modify multiple aggregates in a single handler
- ALWAYS use static factory methods (`Order.Create(command)`) — NEVER use `new Order()` in handlers
- ALWAYS use `LoadFromHistory(events)` to rebuild existing aggregates — NEVER construct manually
- ALWAYS use private setters on aggregate state — NEVER expose public setters
- ALWAYS use dynamic dispatch (`((dynamic)this).Apply(@event)`) for event routing — NEVER use switch statements
- MUST validate domain invariants inside the aggregate — NEVER put business logic in handlers

```csharp
// ANTI-PATTERN: business logic in handler
var order = Order.LoadFromHistory(events);
if (order.Status == OrderStatus.Completed) throw new Exception(); // WRONG
order.UpdateDetails(command); // Aggregate validates internally

// ANTI-PATTERN: multiple aggregates in one handler
var order = Order.LoadFromHistory(orderEvents);
var invoice = Invoice.LoadFromHistory(invoiceEvents); // NEVER
```

### Event Immutability
- NEVER modify existing event schemas — events are immutable once published
- NEVER remove fields or change field types on event data records
- ALWAYS use immutable records for event data — NEVER use mutable classes
- ALWAYS use `EventType` enum for discriminators — NEVER use string constants
- MUST set `Version` field on events — ALWAYS default to 1 unless doing schema migration
- MUST use `[JsonIgnore]` on `IEventData.Type` property

### Outbox Pattern
- ALWAYS save events and outbox messages in a single `SaveChangesAsync` call — NEVER publish before DB save
- ALWAYS use `CommitNewEventsAsync(aggregate)` passing the aggregate — NEVER pass the events list directly
- MUST use the OutboxMessage FK pattern (shared PK with Event) — NEVER serialize event body into OutboxMessage
- `ServiceBusPublisher` MUST be registered as singleton — NEVER as scoped or transient
- ALWAYS call `StartPublish()` as fire-and-forget after save — NEVER await publishing

```csharp
// ANTI-PATTERN: publishing before save
_serviceBusPublisher.StartPublish(); // WRONG — must save first
await _unitOfWork.SaveChangesAsync(ct);

// CORRECT: save then publish
await _commitEventsService.CommitNewEventsAsync(order);
```

### Command Handler Pattern
- ALWAYS use `IUnitOfWork` for data access — NEVER inject `ApplicationDbContext` directly
- ALWAYS use primary constructor with explicit field assignment
- MUST check aggregate existence before create (idempotency guard)
- MUST check aggregate existence before update (not-found guard)
- NEVER return aggregates from handlers — return void or an output DTO
- NEVER create DbContext transactions in handlers — `CommitEventService` handles atomicity

### Event Store (EF Core)
- MUST use TPH with single Events table and discriminator — NEVER separate tables per event type
- MUST maintain unique index on `(AggregateId, Sequence)`
- MUST register both `EventConfiguration` discriminator AND `GenericEventConfiguration` for each event type
- ALWAYS use Newtonsoft.Json for Data column serialization — NEVER System.Text.Json

## Testing Requirements

- MUST use `CustomConstructorFaker<T>` with `RuntimeHelpers.GetUninitializedObject` for event fakers
- MUST use `WebApplicationFactory<Program>` with `DbContextHelper` and `GrpcClientHelper` for integration tests
- MUST use assertion extensions for field-by-field protobuf-to-event comparison
- ALWAYS test both success and failure paths (valid data, already exists, not found)
- ALWAYS verify events persisted in DB and outbox messages created

## Data Access

- ALWAYS use `IUnitOfWork` with `IEventRepository` and `IOutboxMessagesRepository`
- ALWAYS load events with `AsNoTracking()` ordered by `Sequence`
- MUST use `long Id` for Event.Id (database auto-increment) — NEVER `Guid`
- ALWAYS use `protected set` on Event base class properties
