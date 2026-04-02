---
name: query-entity
description: >
  Query-side entity pattern with private setters, event-based constructors, behavior methods
  with (TData data, int sequence) signature, and sequence tracking for idempotency.
  Trigger: query entity, read model, projection, private setters, sequence.
when-to-use: "When creating or modifying read-model entities with private setters"
metadata:
  category: microservice/query
  agent: query-architect
---

# Query Entity — Event-Projected Read Model

## Core Principles

- Query entities are **projections** of command-side events
- All properties use `{ get; private set; }` — state changes only through constructors and behavior methods
- Constructor from `Event<TData>` for entity creation, sets `Sequence = @event.Sequence`
- Behavior methods accept `(TData data, int sequence)` and update state + `Sequence`
- `int Sequence { get; private set; }` tracks last applied event for idempotency
- Private constructor with all parameters for EF Core materialization (NOT parameterless)
- No business logic beyond data projection — pure read model
- Collections use `List<T>` initialized with `= []`

## Key Patterns

### Event<T> — The Event Envelope

Every event is wrapped in a generic envelope used by both entities and handlers:

```csharp
namespace {Company}.{Domain}.Query.Domain.Events;

public class Event<T> : IRequest<bool>
{
    public Guid AggregateId { get; set; }
    public int Sequence { get; set; }
    public Guid? UserId { get; set; }
    public required string Type { get; set; }
    public required T Data { get; set; }
    public DateTime DateTime { get; set; }
    public int Version { get; set; }
}
```

### Entity with Private Setters

```csharp
namespace {Company}.{Domain}.Query.Domain.Entities;

public class Order
{
    // Creation constructor — from event envelope
    public Order(Event<OrderCreatedData> @event)
    {
        Id = @event.AggregateId;
        CustomerName = @event.Data.CustomerName;
        Email = @event.Data.Email;
        Total = @event.Data.Total;
        Status = OrderStatus.Pending;
        Sequence = @event.Sequence;
        CreatedAt = @event.DateTime;
    }

    // EF Core materialization constructor — private, all parameters
    private Order(
        Guid id,
        string customerName,
        string email,
        decimal total,
        OrderStatus status,
        int sequence,
        DateTime createdAt)
    {
        Id = id;
        CustomerName = customerName;
        Email = email;
        Total = total;
        Status = status;
        Sequence = sequence;
        CreatedAt = createdAt;
    }

    // All properties: { get; private set; }
    public Guid Id { get; private set; }
    public string CustomerName { get; private set; }
    public string Email { get; private set; }
    public decimal Total { get; private set; }
    public OrderStatus Status { get; private set; }
    public int Sequence { get; private set; }
    public DateTime CreatedAt { get; private set; }

    // Computed property — no setter
    public bool IsActive => Status != OrderStatus.Cancelled;

    // Navigation collections
    public List<OrderItem> Items { get; private set; } = [];

    // Behavior method: (TData data, int sequence) signature
    public void UpdateDetails(OrderUpdatedData data, int sequence)
    {
        CustomerName = data.CustomerName;
        Email = data.Email;
        Total = data.Total;
        Sequence = sequence;
    }

    // Behavior method: data + sequence, updates state
    public void ChangeStatus(OrderStatusChangedData data, int sequence)
    {
        Status = data.NewStatus;
        Sequence = sequence;
    }

    // Behavior method: sequence-only when data is minimal
    public void Cancel(int sequence)
    {
        Status = OrderStatus.Cancelled;
        Sequence = sequence;
    }

    // Some entities use SetSequence for simple tracking
    public void SetSequence(int sequence)
        => Sequence = sequence;
}
```

### Entity with Static Factory Create

Some entities use a static `Create` method instead of a public constructor:

```csharp
public class Product
{
    // Private constructor for EF Core and factory
    private Product(
        int sequence,
        Guid id,
        string name,
        decimal price,
        ProductType type)
    {
        Sequence = sequence;
        Id = id;
        Name = name;
        Price = price;
        Type = type;
    }

    public Guid Id { get; private set; }
    public int Sequence { get; private set; }
    public string Name { get; private set; }
    public decimal Price { get; private set; }
    public ProductType Type { get; private set; }
    public List<ProductVariant> Variants { get; private set; } = [];

    // Static factory from event
    public static Product Create(Event<ProductCreatedData> @event)
        => new(
            1,
            @event.AggregateId,
            @event.Data.Name,
            @event.Data.Price,
            @event.Data.ProductType
            );

    // Update from full event envelope
    public void Update(Event<ProductUpdatedData> @event)
    {
        Name = @event.Data.Name;
        Price = @event.Data.Price;
        Type = @event.Data.ProductType;
    }

    public void IncrementSequence() => Sequence++;
}
```

### Related Entity

```csharp
namespace {Company}.{Domain}.Query.Domain.Entities;

public class OrderItem
{
    public OrderItem(OrderItemData item, Guid orderId)
    {
        OrderId = orderId;
        ProductId = item.ProductId;
        ProductName = item.ProductName;
        Quantity = item.Quantity;
        UnitPrice = item.UnitPrice;
    }

    public Guid OrderId { get; private set; }
    public Guid ProductId { get; private set; }
    public string ProductName { get; private set; }
    public int Quantity { get; private set; }
    public decimal UnitPrice { get; private set; }
}
```

## Two Constructor Styles

| Style | When Used | Example |
|---|---|---|
| Public `Event<T>` constructor | Simple entities, direct mapping | `new Order(@event)` |
| Static `Create` factory | Entities needing computed initial values | `Product.Create(@event)` |

## Two Behavior Method Styles

| Signature | When Used | Example |
|---|---|---|
| `(TData data, int sequence)` | Handler passes data and sequence separately | `order.UpdateDetails(data, sequence)` |
| `(Event<TData> @event)` | Handler passes full event envelope | `product.Update(@event)` |

Both styles always update `Sequence` at the end.

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Public setters on properties | `{ get; private set; }` on every property |
| Parameterless private constructor | Private constructor with ALL parameters for EF Core |
| Missing Sequence property | Every entity needs `int Sequence { get; private set; }` |
| Apply methods accepting full Event | Behavior methods accept `(TData, int sequence)` or full event |
| `sealed` class modifier | Entities are plain `public class`, not sealed |
| `byte[] RowVersion` property | Not used — sequence tracking handles concurrency |

## Detect Existing Patterns

```bash
# Find entities with private setters
grep -r "private set" --include="*.cs" Domain/Entities/

# Find event-based constructors
grep -r "public.*\(Event<" --include="*.cs" Domain/Entities/

# Find behavior methods with sequence parameter
grep -r "int sequence)" --include="*.cs" Domain/Entities/

# Find Sequence property
grep -r "public int Sequence" --include="*.cs" Domain/Entities/
```

## Adding to Existing Project

1. **All properties** use `{ get; private set; }` — no exceptions
2. **Constructor from `Event<TData>`** for creation, sets all fields from `@event.Data`
3. **Private constructor** with all parameters for EF Core (not parameterless)
4. **Behavior methods** use `(TData data, int sequence)` — always update `Sequence` last
5. **Collections** initialized with `= []` syntax
6. **Place in** `Domain/Entities/` directory
