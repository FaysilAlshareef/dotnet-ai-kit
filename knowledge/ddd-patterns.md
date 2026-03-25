# Domain-Driven Design Patterns

Domain-Driven Design tactical patterns reference for .NET applications.
Covers aggregates, entities, value objects, domain events, bounded contexts, and the repository pattern.

---

## Core Concepts

```
+------------------------------------------------------------------+
|                      Bounded Context                              |
|                                                                   |
|  +---------------------------+   +---------------------------+    |
|  |     Aggregate Root        |   |     Aggregate Root        |    |
|  |  (Consistency Boundary)   |   |  (Consistency Boundary)   |    |
|  |                           |   |                           |    |
|  |  +--------+ +--------+   |   |  +--------+               |    |
|  |  | Entity | | Value  |   |   |  | Entity |               |    |
|  |  |        | | Object |   |   |  |        |               |    |
|  |  +--------+ +--------+   |   |  +--------+               |    |
|  |                           |   |                           |    |
|  |  Domain Events raised     |   |  Domain Events raised     |    |
|  +---------------------------+   +---------------------------+    |
|                                                                   |
|  Repository per Aggregate    |   Domain Services                  |
+------------------------------------------------------------------+
```

---

## Aggregates

An aggregate is a cluster of domain objects treated as a single unit for data changes. The aggregate root is the only entry point for external access.

### Aggregate Base Class

```csharp
public abstract class AggregateRoot
{
    private readonly List<IDomainEvent> _domainEvents = [];

    public Guid Id { get; protected set; }
    public int Version { get; protected set; }

    public IReadOnlyList<IDomainEvent> DomainEvents => _domainEvents;

    protected void RaiseDomainEvent(IDomainEvent domainEvent)
    {
        _domainEvents.Add(domainEvent);
    }

    public void ClearDomainEvents() => _domainEvents.Clear();
}
```

### Concrete Aggregate with Factory Method

```csharp
public class Order : AggregateRoot
{
    public Guid CustomerId { get; private set; }
    public OrderStatus Status { get; private set; }
    public Money Total { get; private set; } = Money.Zero("USD");
    private readonly List<OrderLine> _lines = [];
    public IReadOnlyCollection<OrderLine> Lines => _lines;

    private Order() { } // EF Core

    public static Order Create(Guid customerId, string currency)
    {
        var order = new Order
        {
            Id = Guid.NewGuid(), CustomerId = customerId,
            Status = OrderStatus.Draft, Total = Money.Zero(currency)
        };
        order.RaiseDomainEvent(new OrderCreatedEvent(order.Id, customerId));
        return order;
    }

    public void AddLine(Guid productId, int quantity, Money unitPrice)
    {
        if (Status != OrderStatus.Draft)
            throw new DomainException("Cannot modify a submitted order.");
        if (quantity <= 0)
            throw new DomainException("Quantity must be positive.");

        _lines.Add(new OrderLine(Id, productId, quantity, unitPrice));
        Total = _lines.Aggregate(Money.Zero(Total.Currency),
            (sum, l) => sum.Add(l.LineTotal));
    }

    public void Submit()
    {
        if (_lines.Count == 0)
            throw new DomainException("Cannot submit an empty order.");
        Status = OrderStatus.Submitted;
        RaiseDomainEvent(new OrderSubmittedEvent(Id, Total));
    }
}
```

---

## Entities vs Value Objects

### Entity -- Identity Matters

Entities have a unique identity. Two entities with the same data but different IDs are different objects.

```csharp
public class OrderLine
{
    public Guid Id { get; private set; }
    public Guid OrderId { get; private set; }
    public Guid ProductId { get; private set; }
    public int Quantity { get; private set; }
    public Money UnitPrice { get; private set; }
    public Money LineTotal => UnitPrice.Multiply(Quantity);

    private OrderLine() { } // EF Core

    internal OrderLine(Guid orderId, Guid productId, int quantity, Money unitPrice)
    {
        Id = Guid.NewGuid();
        OrderId = orderId;
        ProductId = productId;
        Quantity = quantity;
        UnitPrice = unitPrice;
    }
}
```

### Value Object -- Equality by Value

Value objects have no identity. Two value objects with the same data are equal. They are immutable.

```csharp
public record Money(decimal Amount, string Currency)
{
    public static Money Zero(string currency) => new(0, currency);

    public Money Add(Money other)
    {
        if (Currency != other.Currency)
            throw new DomainException("Currency mismatch.");
        return this with { Amount = Amount + other.Amount };
    }

    public Money Multiply(int factor) => this with { Amount = Amount * factor };
}
```

Use C# records for value objects -- they provide value equality, immutability, and `with` expressions out of the box. Map to EF Core via `OwnsOne` for owned types.

---

## Domain Events

Domain events capture something meaningful that happened in the domain. They decouple side effects from aggregate logic.

```csharp
// Event contract
public interface IDomainEvent
{
    DateTime OccurredOn { get; }
}

// Concrete event
public record OrderSubmittedEvent(Guid OrderId, Money Total) : IDomainEvent
{
    public DateTime OccurredOn { get; } = DateTime.UtcNow;
}

// Dispatcher -- called after SaveChangesAsync
public class DomainEventDispatcher(IMediator mediator)
{
    public async Task DispatchEventsAsync(DbContext context)
    {
        var aggregates = context.ChangeTracker
            .Entries<AggregateRoot>()
            .Where(e => e.Entity.DomainEvents.Count > 0)
            .Select(e => e.Entity)
            .ToList();

        var events = aggregates.SelectMany(a => a.DomainEvents).ToList();
        aggregates.ForEach(a => a.ClearDomainEvents());

        foreach (var domainEvent in events)
        {
            await mediator.Publish(domainEvent);
        }
    }
}
```

---

## Bounded Contexts

A bounded context is a boundary within which a domain model has a consistent meaning. The same real-world concept may have different models in different contexts.

```
  Ordering Context           |    Shipping Context
  --------------------------+---------------------------
  Order (aggregate)          |    Shipment (aggregate)
  Order.CustomerId (Guid)    |    Shipment.RecipientId (Guid)
  OrderLine (entity)         |    Package (entity)
  Money (value object)       |    Weight (value object)
  OrderSubmittedEvent ------>|---> triggers CreateShipment
```

Key rules:
1. Each context owns its database (or schema)
2. Contexts communicate via integration events, not shared models
3. Anti-corruption layers translate between context models
4. A shared kernel is allowed only for truly common types (e.g., `AggregateRoot` base)

---

## Repository Pattern

One repository per aggregate root. The repository encapsulates data access and returns domain objects.

```csharp
// Interface in Domain layer
public interface IOrderRepository
{
    Task<Order?> GetByIdAsync(Guid id, CancellationToken ct);
    Task AddAsync(Order order, CancellationToken ct);
}

// Implementation in Infrastructure layer
public class OrderRepository(AppDbContext context) : IOrderRepository
{
    public async Task<Order?> GetByIdAsync(Guid id, CancellationToken ct)
    {
        return await context.Orders
            .Include(o => o.Lines)
            .FirstOrDefaultAsync(o => o.Id == id, ct);
    }

    public async Task AddAsync(Order order, CancellationToken ct)
    {
        await context.Orders.AddAsync(order, ct);
    }
}
```

---

## Anti-Patterns

1. **Anemic domain model** -- Aggregates with only getters/setters and no business logic
2. **Aggregate too large** -- Including too many entities; each transaction locks the whole aggregate
3. **Cross-aggregate references** -- Holding direct object references instead of IDs between aggregates
4. **Repository per entity** -- Creating repositories for child entities instead of only aggregate roots
5. **Leaking domain logic** -- Placing business rules in application services or controllers
6. **Public setters** -- Allowing external code to bypass invariant checks

---

## Related Skills and Documents

- `skills/codegen/add-aggregate.md` -- Scaffold a new aggregate with factory and events
- `skills/codegen/add-entity.md` -- Add an entity to an existing aggregate
- `skills/codegen/add-event.md` -- Create domain events with handlers
- `knowledge/event-sourcing-flow.md` -- Event-sourced aggregate pattern
- `knowledge/clean-architecture-patterns.md` -- Where DDD objects live in layers
