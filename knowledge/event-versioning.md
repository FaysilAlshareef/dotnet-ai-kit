# Event Versioning

Event schema evolution, versioned handlers, backward compatibility, and event catalogue management for CQRS microservices.

---

## Overview

Events are immutable records. Once published, their schema cannot change without breaking consumers. Event versioning provides a structured approach to evolve event schemas while maintaining backward compatibility.

### Core Principles

1. **Never remove fields** — old consumers expect them
2. **Never rename fields** — serialization will break
3. **Add new fields with defaults** — old events can still deserialize
4. **Use the Version field** — route to versioned handlers
5. **Upcast old events** — transform at read time, not at rest

---

## Event Version Field

Every event carries a Version field that identifies its schema version:

```csharp
public sealed class Event<TData> where TData : IEventData
{
    public Guid AggregateId { get; init; }
    public int Sequence { get; init; }
    public string Type { get; init; } = string.Empty;
    public DateTime DateTime { get; init; }
    public int Version { get; init; } = 1;  // Schema version
    public TData Data { get; init; } = default!;
}
```

---

## Schema Evolution Strategies

### Strategy 1: Additive Changes (Preferred)

Add new optional fields with sensible defaults. This is backward-compatible — old events deserialize with null/default values.

```csharp
// Version 1 — original
public sealed record OrderCreatedData(
    string CustomerName,
    decimal Total,
    List<OrderItemData> Items
) : IEventData;

// Version 2 — added optional fields
public sealed record OrderCreatedData(
    string CustomerName,
    decimal Total,
    List<OrderItemData> Items,
    string? Currency = null,         // New in v2
    string? CustomerEmail = null     // New in v2
) : IEventData;
```

Old v1 events deserialize correctly because `Currency` and `CustomerEmail` default to `null`.

### Strategy 2: Versioned Event Data Classes

When changes are not backward-compatible, create separate data classes per version:

```csharp
// V1: Total as single field
public sealed record OrderCreatedDataV1(
    string CustomerName,
    decimal Total,
    List<OrderItemData> Items
) : IEventData;

// V2: Total split into subtotal + tax
public sealed record OrderCreatedDataV2(
    string CustomerName,
    decimal Subtotal,
    decimal Tax,
    string Currency,
    List<OrderItemData> Items
) : IEventData;
```

### Strategy 3: Upcasting

Transform old event data to the latest schema at read time:

```csharp
public static class EventUpcaster
{
    public static Event<OrderCreatedDataV2> Upcast(Event<OrderCreatedDataV1> oldEvent)
    {
        return new Event<OrderCreatedDataV2>
        {
            AggregateId = oldEvent.AggregateId,
            Sequence = oldEvent.Sequence,
            Type = oldEvent.Type,
            DateTime = oldEvent.DateTime,
            Version = 2,
            Data = new OrderCreatedDataV2(
                CustomerName: oldEvent.Data.CustomerName,
                Subtotal: oldEvent.Data.Total,
                Tax: 0m,  // V1 events did not track tax
                Currency: "USD",  // Default currency for v1
                Items: oldEvent.Data.Items
            )
        };
    }
}
```

---

## Versioned Event Deserialization

### Version-Aware Deserializer

```csharp
public static class EventDeserializer
{
    public static object Deserialize(string subject, string body)
    {
        // Peek at version to determine correct data type
        var versionInfo = JsonConvert.DeserializeAnonymousType(
            body, new { Version = 1 });
        var version = versionInfo?.Version ?? 1;

        return subject switch
        {
            EventTypes.OrderCreated => DeserializeOrderCreated(body, version),
            EventTypes.OrderUpdated => DeserializeOrderUpdated(body, version),
            _ => throw new UnknownEventTypeException(subject)
        };
    }

    private static object DeserializeOrderCreated(string body, int version)
    {
        return version switch
        {
            1 => UpcastToLatest(
                JsonConvert.DeserializeObject<Event<OrderCreatedDataV1>>(body)!),
            2 => JsonConvert.DeserializeObject<Event<OrderCreatedDataV2>>(body)!,
            _ => throw new UnsupportedEventVersionException(
                EventTypes.OrderCreated, version)
        };
    }

    private static Event<OrderCreatedDataV2> UpcastToLatest(
        Event<OrderCreatedDataV1> v1Event)
    {
        return EventUpcaster.Upcast(v1Event);
    }
}
```

---

## Versioned Handlers

### Single Handler with Version Routing

```csharp
public sealed class OrderCreatedHandler(ApplicationDbContext db)
    : IRequestHandler<Event<OrderCreatedDataV2>, bool>
{
    public async Task<bool> Handle(
        Event<OrderCreatedDataV2> @event, CancellationToken ct)
    {
        var exists = await db.Orders.AnyAsync(
            o => o.Id == @event.AggregateId, ct);
        if (exists) return true;

        // All events arrive as V2 (upcasted if needed)
        var order = new Order(@event);
        db.Orders.Add(order);
        await db.SaveChangesAsync(ct);
        return true;
    }
}
```

### Separate Handlers per Version (Alternative)

When upcasting is not practical:

```csharp
// V1 handler — handles legacy events
public sealed class OrderCreatedV1Handler(ApplicationDbContext db)
    : IRequestHandler<Event<OrderCreatedDataV1>, bool>
{
    public async Task<bool> Handle(
        Event<OrderCreatedDataV1> @event, CancellationToken ct)
    {
        var order = new Order
        {
            Id = @event.AggregateId,
            CustomerName = @event.Data.CustomerName,
            Total = @event.Data.Total,
            Currency = "USD",  // Default for v1
            Sequence = @event.Sequence
        };
        db.Orders.Add(order);
        await db.SaveChangesAsync(ct);
        return true;
    }
}

// V2 handler — handles current events
public sealed class OrderCreatedV2Handler(ApplicationDbContext db)
    : IRequestHandler<Event<OrderCreatedDataV2>, bool>
{
    public async Task<bool> Handle(
        Event<OrderCreatedDataV2> @event, CancellationToken ct)
    {
        var order = new Order
        {
            Id = @event.AggregateId,
            CustomerName = @event.Data.CustomerName,
            Subtotal = @event.Data.Subtotal,
            Tax = @event.Data.Tax,
            Currency = @event.Data.Currency,
            Sequence = @event.Sequence
        };
        db.Orders.Add(order);
        await db.SaveChangesAsync(ct);
        return true;
    }
}
```

---

## Backward Compatibility Rules

### Safe Changes (No Version Bump Required)

| Change                         | Safe? | Notes                                      |
|--------------------------------|-------|--------------------------------------------|
| Add optional field             | Yes   | Old events deserialize with null/default   |
| Add field with default value   | Yes   | Old events get the default                 |
| Widen numeric type (int->long) | Yes   | Newtonsoft handles this automatically      |

### Breaking Changes (Version Bump Required)

| Change                    | Breaking | Migration                            |
|---------------------------|----------|--------------------------------------|
| Remove field              | Yes      | Keep field, mark obsolete            |
| Rename field              | Yes      | Add new field, keep old, upcast      |
| Change field type         | Yes      | New data class + upcaster            |
| Change field semantics    | Yes      | New data class + upcaster            |
| Split field into multiple | Yes      | New data class + upcaster            |

### Migration Checklist

1. Create new event data class (V{n+1})
2. Create upcaster from V{n} to V{n+1}
3. Update deserializer to handle both versions
4. Update handlers to work with latest version
5. Update command-side producer to emit new version
6. Deploy consumers FIRST (they handle both versions)
7. Deploy producers SECOND (they emit new version)
8. Update event catalogue documentation

---

## Event Catalogue

Each service maintains a catalogue of all events it produces and consumes.

### Catalogue Format

```markdown
# {Domain} Event Catalogue

## Events Produced

### OrderCreated
- **Type**: `OrderCreated`
- **Current Version**: 2
- **Data Class**: `OrderCreatedDataV2`
- **Producer**: `CreateOrderHandler`
- **Topic**: `{company}-order-commands`

| Field         | Type          | Version | Required | Description            |
|---------------|---------------|---------|----------|------------------------|
| CustomerName  | string        | 1       | Yes      | Customer full name     |
| Total         | decimal       | 1       | Yes (V1) | Order total (V1 only)  |
| Items         | OrderItem[]   | 1       | Yes      | Line items             |
| Subtotal      | decimal       | 2       | Yes      | Pre-tax amount         |
| Tax           | decimal       | 2       | Yes      | Tax amount             |
| Currency      | string        | 2       | Yes      | ISO 4217 currency code |

### OrderUpdated
- **Type**: `OrderUpdated`
- **Current Version**: 1
- **Data Class**: `OrderUpdatedData`
- **Producer**: `UpdateOrderHandler`

## Events Consumed

| Event Type    | Handler                 | Version Supported | Projection |
|---------------|-------------------------|-------------------|------------|
| OrderCreated  | OrderCreatedHandler     | 1, 2 (upcast)    | Orders     |
| OrderUpdated  | OrderUpdatedHandler     | 1                 | Orders     |
```

### Maintaining the Catalogue

- Update when adding new events
- Update when changing event schemas
- Review during cross-service integration
- Include in PR review checklist

---

## Testing Version Compatibility

```csharp
public sealed class EventVersioningTests
{
    [Fact]
    public void V1Event_DeserializesWithNewSchema()
    {
        // V1 JSON (no Currency or Tax fields)
        var v1Json = """
        {
            "AggregateId": "550e8400-e29b-41d4-a716-446655440000",
            "Sequence": 1,
            "Type": "OrderCreated",
            "DateTime": "2026-01-15T10:30:00Z",
            "Version": 1,
            "Data": {
                "CustomerName": "John Doe",
                "Total": 150.00,
                "Items": []
            }
        }
        """;

        var @event = EventDeserializer.Deserialize(
            EventTypes.OrderCreated, v1Json);

        // Should upcast to V2
        var v2Event = Assert.IsType<Event<OrderCreatedDataV2>>(@event);
        Assert.Equal("John Doe", v2Event.Data.CustomerName);
        Assert.Equal(150.00m, v2Event.Data.Subtotal);
        Assert.Equal(0m, v2Event.Data.Tax);
        Assert.Equal("USD", v2Event.Data.Currency);
    }

    [Fact]
    public void V2Event_DeserializesDirectly()
    {
        var v2Json = """
        {
            "AggregateId": "550e8400-e29b-41d4-a716-446655440000",
            "Sequence": 1,
            "Type": "OrderCreated",
            "DateTime": "2026-01-15T10:30:00Z",
            "Version": 2,
            "Data": {
                "CustomerName": "Jane Doe",
                "Subtotal": 100.00,
                "Tax": 20.00,
                "Currency": "EUR",
                "Items": []
            }
        }
        """;

        var @event = EventDeserializer.Deserialize(
            EventTypes.OrderCreated, v2Json);

        var v2Event = Assert.IsType<Event<OrderCreatedDataV2>>(@event);
        Assert.Equal("EUR", v2Event.Data.Currency);
        Assert.Equal(20.00m, v2Event.Data.Tax);
    }
}
```

---

## Deployment Order for Version Changes

```
1. Deploy CONSUMERS first (query, processor)
   └── They handle V1 AND V2 (via upcasting)

2. Deploy PRODUCERS second (command)
   └── They start emitting V2 events

3. Monitor for errors
   └── Check DLQ for version-related failures

4. After stabilization period
   └── Consider removing V1 handling (optional)
```

---

## Related Documents

- `knowledge/event-sourcing-flow.md` — Event flow context
- `knowledge/dead-letter-reprocessing.md` — Handling version failures
- `knowledge/testing-patterns.md` — Version compatibility tests
