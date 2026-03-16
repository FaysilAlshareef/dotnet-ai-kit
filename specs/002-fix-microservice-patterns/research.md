# Research: Fix Microservice Pattern Content

## Research Summary

All pattern corrections are derived from scanning 7 production projects
at `../projects/` and 3 reference tools at `../references/`. No unknowns
remain — production code is the definitive source for every decision.

## Decision 1: Event Hierarchy

**Decision**: Use abstract `Event` base class with `long Id` and `protected set`,
plus `Event<TData>` subclass with constructor-based initialization.
**Rationale**: Production code at `Anis.competition-commands/Domain/Events/Event.cs`
uses this two-level hierarchy. The abstract base provides shared metadata
(Id, AggregateId, Sequence, UserId, Type, DateTime, Version) while the
generic subclass adds the typed `Data` payload.
**Alternatives rejected**: Single `Event<TData>` with `init` properties
(our current generated pattern) — doesn't match production.

## Decision 2: EventType Enum vs String

**Decision**: Use `EventType` enum for event discrimination, not string.
**Rationale**: Production uses `Anis.Competition.Commands.Domain.Enums.EventType`
enum. `IEventData.Type` returns this enum (JsonIgnored). The enum provides
compile-time safety and matches the discriminator pattern in EF Core config.
**Alternatives rejected**: String-based type (our current pattern) — less
type-safe, doesn't match production.

## Decision 3: OutboxMessage Design

**Decision**: OutboxMessage wraps Event via FK relationship, not duplicated fields.
**Rationale**: Production `OutboxMessage` has `public Event? Event { get; private set; }`
with a foreign key to Event.Id. It uses a static `ToManyMessages()` factory
method. The FK-based approach avoids data duplication and ensures consistency.
**Alternatives rejected**: OutboxMessage with serialized event data fields
(our current pattern) — duplicates data, inconsistent with production.

## Decision 4: CommitEventService Pattern

**Decision**: Use IUnitOfWork with AddRangeAsync for events + outbox, then
SaveChangesAsync, then StartPublish (fire-and-forget).
**Rationale**: Production `CommitEventService` at
`Infra/Services/BaseService/CommitEventService.cs` injects `IUnitOfWork`
and `IServiceBusPublisher`. It calls `AddRangeAsync(newEvents)`,
`AddRangeAsync(OutboxMessage.ToManyMessages(newEvents))`,
`SaveChangesAsync()`, then `_serviceBusPublisher.StartPublish()`.
No manual transaction management (BeginTransactionAsync).
**Alternatives rejected**: Manual transaction with BeginTransactionAsync
+ CommitAsync (our current pattern) — not how production works.

## Decision 5: ServiceBusPublisher Pattern

**Decision**: lock + lockedScopes counter + Task.Run fire-and-forget +
CreateScope + batch-200 + publish-and-remove-one-by-one + MessageBody
with Newtonsoft.Json.
**Rationale**: Production publisher uses `static readonly object _lockObject`,
`lockedScopes` counter (max 2), `Task.Run(PublishNonPublishedMessages)`,
creates DI scope inside lock, reads outbox in batches of 200, publishes
each message individually then removes it. Uses `MessageBody` class with
Newtonsoft.Json serialization and sets SessionId, PartitionKey, Subject,
CorrelationId, MessageId, and ApplicationProperties on ServiceBusMessage.
**Alternatives rejected**: Interlocked.CompareExchange + simple stub
(our current pattern) — too simplistic.

## Decision 6: DI Container Naming

**Decision**: `ApplicationContainer` and `InfraContainer` as static class names.
**Rationale**: Production uses these names in
`Application/ApplicationContainer.cs` and `Infra/InfraContainer.cs`.
**Alternatives rejected**: `ApplicationServiceExtensions` /
`InfraServiceExtensions` (our current pattern) — different naming convention.

## Decision 7: Query Handler Return Type

**Decision**: Event handlers return `bool` via `IRequestHandler<Event<T>, bool>`.
**Rationale**: Production query handlers at `anis.competition-queries`
return `true` for successful processing and `true` for idempotent
duplicate detection. This allows the Service Bus listener to CompleteMessage
on true and AbandonMessage on false.

## Decision 8: ServiceBusSessionProcessor Configuration

**Decision**: Use specific configuration values from production.
**Rationale**: Production listeners use PrefetchCount=1,
MaxConcurrentCallsPerSession=1, MaxConcurrentSessions=1000,
SessionIdleTimeout=1 minute, MaxAutoLockRenewalDuration=5 minutes,
AutoCompleteMessages=false. Each listener has a paired DLQ processor.

## Decision 9: Gateway Rate Limiting

**Decision**: Use `AddPentagon()` for rate limiting in gateways.
**Rationale**: Production gateways at
`anis.gateways-cards-store-management` use this Pentagon library
for rate limiting, along with `AddPolicies(ApiScope.Management)` for
authorization scoping.

## All NEEDS CLARIFICATION Items: Resolved

No unknowns remain. All corrections are directly observable in the
production source code.
