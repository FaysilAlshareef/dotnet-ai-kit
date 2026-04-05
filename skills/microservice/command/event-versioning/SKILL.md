---
name: event-versioning
description: >
  Event schema evolution for Event<TData> pattern. Covers backward-compatible changes,
  upcasting, versioned event data classes, migration strategies, and snapshot compatibility.
  Trigger: event versioning, event migration, schema evolution, upcaster, event version.
metadata:
  category: microservice/command
  agent: command-architect
  when-to-use: "When creating or modifying event schema versions, upcasters, or migration strategies"
---

# Event Versioning — Schema Evolution

## Core Principles

- Events are immutable once published — never modify existing event schemas
- Add new fields as nullable with defaults for backward-compatible changes
- Use upcasters to transform old event shapes to new at read time
- Version field on `Event<TData>` tracks the schema version
- Never remove fields, never change field types — add new event types instead
- Prefer lazy upcasting on read over batch migration

## Backward-Compatible Changes (Safe)

Adding new nullable fields with defaults is always safe:

```csharp
// V1 — original event data
public record OrderCreatedDataV1(
    string CustomerName,
    decimal Total,
    OrderStatus Status,
    List<Guid> Items
) : IEventData
{
    public EventType Type => EventType.OrderCreated;
}

// V2 — added nullable fields (backward compatible)
public record OrderCreatedDataV2(
    string CustomerName,
    decimal Total,
    OrderStatus Status,
    List<Guid> Items,
    string? CustomerEmail = null,
    string? ShippingAddress = null,
    decimal? DiscountAmount = null
) : IEventData
{
    public EventType Type => EventType.OrderCreated;
}
```

Key details:
- New fields are `nullable` with default `null`
- Deserialization of V1 JSON into V2 class succeeds — new fields are `null`
- No upcaster needed for nullable additions
- The `Version` field on the event distinguishes which schema was used

## Upcaster Pattern

For structural changes that cannot be handled by nullable defaults:

```csharp
namespace {Company}.{Domain}.Commands.Application.EventUpcast;

public interface IEventUpcaster<in TOld, out TNew>
    where TOld : IEventData
    where TNew : IEventData
{
    TNew Upcast(TOld oldData);
}

public class OrderCreatedV1ToV2Upcaster
    : IEventUpcaster<OrderCreatedDataV1, OrderCreatedDataV2>
{
    public OrderCreatedDataV2 Upcast(OrderCreatedDataV1 oldData)
    {
        return new OrderCreatedDataV2(
            CustomerName: oldData.CustomerName,
            Total: oldData.Total,
            Status: oldData.Status,
            Items: oldData.Items,
            CustomerEmail: null,
            ShippingAddress: null,
            DiscountAmount: 0m
        );
    }
}
```

### Upcaster Registration

```csharp
// In DI container
builder.Services.AddSingleton<
    IEventUpcaster<OrderCreatedDataV1, OrderCreatedDataV2>,
    OrderCreatedV1ToV2Upcaster>();
```

## Versioned Event Data Classes

Maintain version suffixes when schemas diverge significantly:

```csharp
// V1 — single winner
public record WinnerSelectedDataV1(
    Guid WinnerId,
    decimal PrizeAmount
) : IEventData
{
    public EventType Type => EventType.WinnerSelected;
}

// V2 — multiple winners with ranking
public record WinnerSelectedDataV2(
    List<WinnerEntry> Winners,
    decimal TotalPrizePool
) : IEventData
{
    public EventType Type => EventType.WinnerSelected;
}

public record WinnerEntry(
    Guid WinnerId,
    int Rank,
    decimal PrizeAmount);
```

## Event Type Discriminator Patterns

Use `EventType` enum combined with `Version` for deserialization:

```csharp
public Event DeserializeEvent(string json, EventType type, int version)
{
    return (type, version) switch
    {
        (EventType.OrderCreated, 1) => Deserialize<OrderCreatedDataV1>(json),
        (EventType.OrderCreated, 2) => Deserialize<OrderCreatedDataV2>(json),
        (EventType.WinnerSelected, 1) => Deserialize<WinnerSelectedDataV1>(json),
        (EventType.WinnerSelected, 2) => Deserialize<WinnerSelectedDataV2>(json),
        _ => throw new InvalidOperationException(
            $"Unknown event type/version: {type}/{version}")
    };
}
```

## Aggregate Replay with Versioning

When replaying events for aggregate rehydration, apply upcasters:

```csharp
public class OrderAggregate
{
    public void Apply(Event @event)
    {
        switch (@event)
        {
            case Event<OrderCreatedDataV2> e:
                ApplyCreated(e.Data);
                break;
            case Event<OrderCreatedDataV1> e:
                // Upcast V1 to V2, then apply
                var upcast = _upcaster.Upcast(e.Data);
                ApplyCreated(upcast);
                break;
        }
    }

    private void ApplyCreated(OrderCreatedDataV2 data)
    {
        CustomerName = data.CustomerName;
        Total = data.Total;
        Status = data.Status;
    }
}
```

## Migration Strategies

### Lazy Upcasting on Read (Preferred)

- Upcast events when loading aggregates or projections
- No database migration needed
- Old events remain in their original format
- Upcasters are chained: V1 → V2 → V3

```csharp
public TNew UpcastChain<TOld, TMid, TNew>(
    TOld data,
    IEventUpcaster<TOld, TMid> first,
    IEventUpcaster<TMid, TNew> second)
    where TOld : IEventData
    where TMid : IEventData
    where TNew : IEventData
{
    var mid = first.Upcast(data);
    return second.Upcast(mid);
}
```

### Batch Migration (Use Sparingly)

- Run a one-time migration job to rewrite event data
- Needed when upcasting is too expensive at runtime
- Always keep a backup of original events
- Update the `Version` field after migration

## Snapshot Compatibility

Snapshots must account for event versioning:

```csharp
public class AggregateSnapshot
{
    public Guid AggregateId { get; init; }
    public int Version { get; init; }        // Snapshot schema version
    public int LastSequence { get; init; }   // Last event sequence included
    public string StateJson { get; init; }   // Serialized aggregate state
}
```

Key rules:
- When the aggregate's `Apply` logic changes due to event versioning, invalidate old snapshots
- Include a `Version` field on snapshots to detect stale schemas
- On version mismatch: discard snapshot, replay all events from the beginning
- Snapshots are an optimization — the system must work without them

## Breaking vs Non-Breaking Changes

| Change Type | Breaking? | Strategy |
|---|---|---|
| Add nullable field with default | No | Direct deserialization |
| Add required field | Yes | New version + upcaster |
| Remove field | Yes | New event type |
| Change field type | Yes | New event type |
| Rename field | Yes | New version + upcaster |
| Change enum values | Yes | New version + mapping |
| Add new event type | No | Add to EventType enum |

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Modifying existing event data records | Create a new versioned record (V2) |
| Removing fields from event data | Add new event type, deprecate old |
| Changing field types (e.g., `string` to `int`) | New version with upcaster |
| Batch-migrating all events on every schema change | Lazy upcast on read |
| Ignoring Version field on events | Always set and check Version |
| Snapshots without version tracking | Include Version, invalidate on schema change |

## Detect Existing Patterns

```bash
# Find versioned event data classes
grep -r "DataV[0-9]" --include="*.cs" Domain/Events/

# Find upcasters
grep -r "IEventUpcaster" --include="*.cs" Application/

# Find event version handling
grep -r "\.Version" --include="*.cs" Domain/Events/

# Find snapshot classes
grep -r "Snapshot" --include="*.cs" Domain/
```

## Adding Event Versioning to Existing Project

1. **Create new versioned data record** (e.g., `OrderCreatedDataV2`) with new fields
2. **Implement upcaster** from V1 to V2 (`IEventUpcaster<V1, V2>`)
3. **Register upcaster** in DI container
4. **Update aggregate Apply method** to handle both versions (or upcast first)
5. **Update event deserialization** to use type + version switch
6. **Set Version = 2** on new events created with the V2 data class
7. **Update query-side handlers** to handle both versions or upcast before processing
