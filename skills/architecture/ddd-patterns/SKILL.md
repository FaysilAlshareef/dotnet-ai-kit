---
name: ddd-patterns
description: >
  Domain-Driven Design tactical patterns. Aggregates, value objects, domain events,
  strongly-typed IDs, bounded contexts, and rich domain models.
  Trigger: DDD, aggregate, value object, domain event, bounded context.
category: architecture
agent: dotnet-architect
---

# Domain-Driven Design Patterns

## Core Principles

- Aggregate roots are consistency boundaries — all changes go through the root
- Value objects are immutable and compared by structural equality
- Domain events communicate side effects across aggregates
- Strongly-typed IDs prevent primitive obsession and accidental ID swaps
- Repository per aggregate root, not per entity
- Rich domain model: behavior lives on entities, not in services

## Patterns

### Strongly-Typed IDs

```csharp
public readonly record struct OrderId(Guid Value)
{
    public static OrderId New() => new(Guid.NewGuid());
    public override string ToString() => Value.ToString();
}

public readonly record struct CustomerId(Guid Value)
{
    public static CustomerId New() => new(Guid.NewGuid());
}

// Prevents accidental: GetOrder(customerId) when OrderId expected
```

### Value Objects

```csharp
public sealed record Money(decimal Amount, string Currency)
{
    public static Money Zero(string currency) => new(0, currency);

    public Money Add(Money other)
    {
        if (Currency != other.Currency)
            throw new DomainException("Cannot add different currencies");
        return this with { Amount = Amount + other.Amount };
    }

    public Money Multiply(int factor) =>
        this with { Amount = Amount * factor };
}

public sealed record Address(
    string Street, string City, string State, string ZipCode, string Country)
{
    // Value objects validate on construction
    public Address
    {
        if (string.IsNullOrWhiteSpace(Street))
            throw new DomainException("Street is required");
        if (string.IsNullOrWhiteSpace(City))
            throw new DomainException("City is required");
    }
}
```

### Aggregate Root Base Class

```csharp
public abstract class AggregateRoot<TId> where TId : struct
{
    public TId Id { get; protected set; }

    private readonly List<IDomainEvent> _domainEvents = [];
    public IReadOnlyList<IDomainEvent> DomainEvents =>
        _domainEvents.AsReadOnly();

    protected void RaiseDomainEvent(IDomainEvent domainEvent) =>
        _domainEvents.Add(domainEvent);

    public void ClearDomainEvents() => _domainEvents.Clear();
}

public interface IAggregateRoot { }

public interface IDomainEvent : INotification
{
    DateTimeOffset OccurredAt { get; }
}
```

### Rich Aggregate Root

```csharp
public sealed class Order : AggregateRoot<OrderId>, IAggregateRoot
{
    public CustomerId CustomerId { get; private set; }
    public Money Total { get; private set; } = Money.Zero("USD");
    public OrderStatus Status { get; private set; } = OrderStatus.Draft;

    private readonly List<OrderLine> _lines = [];
    public IReadOnlyList<OrderLine> Lines => _lines.AsReadOnly();

    private Order() { } // EF Core

    // Factory method — the only way to create an Order
    public static Order Create(CustomerId customerId)
    {
        var order = new Order
        {
            Id = OrderId.New(),
            CustomerId = customerId
        };
        order.RaiseDomainEvent(new OrderCreatedEvent(order.Id));
        return order;
    }

    public void AddLine(ProductId productId, int quantity, Money unitPrice)
    {
        Guard.Against.NegativeOrZero(quantity);

        if (Status != OrderStatus.Draft)
            throw new DomainException("Can only add lines to draft orders");

        var line = new OrderLine(productId, quantity, unitPrice);
        _lines.Add(line);
        RecalculateTotal();
    }

    public void RemoveLine(ProductId productId)
    {
        var line = _lines.FirstOrDefault(l => l.ProductId == productId)
            ?? throw new DomainException("Line not found");
        _lines.Remove(line);
        RecalculateTotal();
    }

    public void Submit()
    {
        if (Status != OrderStatus.Draft)
            throw new DomainException("Only draft orders can be submitted");
        if (_lines.Count == 0)
            throw new DomainException("Cannot submit empty order");

        Status = OrderStatus.Submitted;
        RaiseDomainEvent(new OrderSubmittedEvent(Id, Total));
    }

    public void Cancel(string reason)
    {
        if (Status == OrderStatus.Shipped)
            throw new DomainException("Cannot cancel shipped orders");

        Status = OrderStatus.Cancelled;
        RaiseDomainEvent(new OrderCancelledEvent(Id, reason));
    }

    private void RecalculateTotal()
    {
        Total = _lines.Aggregate(
            Money.Zero("USD"),
            (sum, line) => sum.Add(line.LineTotal));
    }
}
```

### Entity (Non-Root)

```csharp
public sealed class OrderLine
{
    public Guid Id { get; private set; } = Guid.NewGuid();
    public ProductId ProductId { get; private set; }
    public int Quantity { get; private set; }
    public Money UnitPrice { get; private set; }
    public Money LineTotal => UnitPrice.Multiply(Quantity);

    private OrderLine() { } // EF Core

    internal OrderLine(ProductId productId, int quantity, Money unitPrice)
    {
        ProductId = productId;
        Quantity = quantity;
        UnitPrice = unitPrice;
    }
}
```

### Domain Events

```csharp
public abstract record DomainEvent : IDomainEvent
{
    public DateTimeOffset OccurredAt { get; } = DateTimeOffset.UtcNow;
}

public sealed record OrderCreatedEvent(OrderId OrderId) : DomainEvent;

public sealed record OrderSubmittedEvent(
    OrderId OrderId, Money Total) : DomainEvent;

public sealed record OrderCancelledEvent(
    OrderId OrderId, string Reason) : DomainEvent;
```

### Domain Exception

```csharp
public sealed class DomainException : Exception
{
    public DomainException(string message) : base(message) { }
    public DomainException(string message, Exception inner) : base(message, inner) { }
}
```

### Bounded Context Communication

```csharp
// Each bounded context has its own models
// OrderManagement context
namespace {Company}.{Domain}.OrderManagement.Domain;
public sealed class Order : AggregateRoot<OrderId> { /* ... */ }

// Shipping context — different model for the same concept
namespace {Company}.{Domain}.Shipping.Domain;
public sealed class Shipment : AggregateRoot<ShipmentId>
{
    public Guid OrderReference { get; private set; } // not OrderId
}

// Anti-corruption layer translates between contexts
public sealed class ShippingAntiCorruptionLayer(IOrderService orderService)
{
    public async Task<ShipmentRequest> TranslateOrderAsync(
        Guid orderId, CancellationToken ct)
    {
        var order = await orderService.GetOrderSummaryAsync(orderId, ct);
        return new ShipmentRequest(
            OrderReference: order.Id,
            Address: MapToShippingAddress(order.ShippingAddress));
    }
}
```

## Anti-Patterns

- Anemic domain model: entities with only getters/setters, no behavior
- Public setters on aggregate properties (allows bypassing invariants)
- Business logic in application services instead of domain entities
- Repository per entity instead of per aggregate root
- Primitive obsession: using `Guid` everywhere instead of typed IDs
- Exposing internal collections as `List<T>` instead of `IReadOnlyList<T>`

## Detect Existing Patterns

1. Look for `AggregateRoot`, `Entity`, `ValueObject` base classes
2. Check for strongly-typed IDs (record structs wrapping `Guid`)
3. Look for `IDomainEvent` or `DomainEvent` types
4. Check for rich entities with behavior methods (not just properties)
5. Look for private setters and factory methods (`Create`, `Register`)
6. Check for `Guard.Against` or similar invariant enforcement

## Adding to Existing Project

1. **Introduce base classes** — `AggregateRoot<TId>`, `IDomainEvent`
2. **Add typed IDs** to key entities — start with the most-used aggregate
3. **Move behavior into entities** — encapsulate state transitions
4. **Add private setters** and factory methods to enforce invariants
5. **Define bounded context boundaries** before splitting further
6. **Add domain events** for cross-aggregate side effects

## Decision Guide

| Concept | When to Use |
|---------|-------------|
| Value Object | Immutable, identity-less (Money, Address, DateRange) |
| Entity | Has identity, mutable within aggregate boundary |
| Aggregate Root | Consistency boundary, entry point for changes |
| Domain Event | Side effect that other aggregates need to know about |
| Strongly-typed ID | Every aggregate root and key entity ID |
| Factory Method | When creation involves invariants or events |

## References

- https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/
- https://www.domainlanguage.com/ddd/reference/
