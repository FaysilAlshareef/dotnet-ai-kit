---
name: aggregate-design
description: >
  Aggregate root pattern for event-sourced microservices. Covers Aggregate<T> base class,
  LoadFromHistory replay, ApplyChange for new events, factory methods, and domain invariants.
  Trigger: aggregate, event sourcing, domain model, CQRS command side.
category: microservice/command
agent: command-architect
---

# Aggregate Design -- Event-Sourced Aggregate Root

## Core Principles

- Aggregates are the **consistency boundary** for the command side
- All state changes produce events via `ApplyChange`
- State is rebuilt from events via static `LoadFromHistory`
- Factory methods (not constructors) create new aggregates
- Private setters enforce encapsulation; behavior lives on the aggregate
- Uncommitted events are collected for persistence by `CommitEventService`
- Dynamic dispatch (`((dynamic)this).Apply(@event)`) routes each event to a typed `Apply` method

## Key Patterns

### Aggregate Base Class

The base class is generic over itself (`Aggregate<T>` where T is the concrete aggregate). It uses `dynamic` dispatch to route events to typed `Apply` overloads on the concrete aggregate.

```csharp
namespace {Company}.{Domain}.Commands.Domain.Core;

public abstract class Aggregate<T>
{
    private readonly List<Event> _uncommittedEvents = new();

    public Guid Id { get; protected set; }
    public int Sequence { get; internal set; }

    public IReadOnlyList<Event> GetUncommittedEvents() => _uncommittedEvents;
    public void MarkChangesAsCommitted() => _uncommittedEvents.Clear();

    public static T LoadFromHistory(IEnumerable<Event> history)
    {
        if (!history.Any())
            throw new ArgumentOutOfRangeException(nameof(history), "history.Count == 0");

        var aggregate = (T?)Activator.CreateInstance(typeof(T), nonPublic: true)
                ?? throw new NullReferenceException("Unable to generate aggregate entity");

        foreach (var e in history)
        {
            ((dynamic)aggregate).ApplyChange(e, false);
        }

        return aggregate;
    }

    protected void ApplyChange(dynamic @event, bool isNew = true)
    {
        if (@event.Sequence == 1)
        {
            Id = @event.AggregateId;
        }

        Sequence++;

        if (Id == Guid.Empty)
            throw new InvalidOperationException("Id == Guid.Empty");

        if (@event.Sequence != Sequence)
            throw new InvalidOperationException("@event.Sequence != Sequence");

        ((dynamic)this).Apply(@event);

        if (isNew)
            _uncommittedEvents.Add(@event);
    }
}
```

### Key details of ApplyChange

1. **Sequence 1 sets Id**: On the first event (`Sequence == 1`), the aggregate's `Id` is set from `@event.AggregateId`
2. **Sequence auto-increments**: `Sequence++` happens before validation, so it tracks expected next sequence
3. **Sequence validation**: `@event.Sequence != Sequence` throws if the event is out of order
4. **Dynamic dispatch**: `((dynamic)this).Apply(@event)` calls the concrete aggregate's typed `Apply` overload
5. **Uncommitted tracking**: Only new events (`isNew = true`) are added to `_uncommittedEvents`

### LoadFromHistory details

- **Static method** that returns `T` (the concrete aggregate type)
- Uses `Activator.CreateInstance(typeof(T), nonPublic: true)` to invoke the private parameterless constructor
- Replays all events with `isNew: false` so they are NOT added to uncommitted events

### Concrete Aggregate with Factory Method

```csharp
namespace {Company}.{Domain}.Commands.Domain.Core;

public class Order : Aggregate<Order>
{
    public string CustomerName { get; private set; } = null!;
    public decimal Total { get; private set; }
    public OrderStatus Status { get; private set; }

    private List<Guid> _items = [];
    public IReadOnlyCollection<Guid> Items => _items;

    // Factory method -- NOT a public constructor
    public static Order Create(ICreateOrderCommand command)
    {
        var order = new Order();

        var @event = command.ToEvent();

        order.ApplyChange(@event);

        return order;
    }

    // Apply overload for OrderCreated event
    public void Apply(OrderCreated @event)
    {
        CustomerName = @event.Data.CustomerName;
        Total = @event.Data.Total;
        Status = OrderStatus.Pending;
        _items = @event.Data.Items;
    }

    // Business method producing event
    public void UpdateDetails(IUpdateOrderCommand command)
    {
        if (Status == OrderStatus.Completed)
            throw new OrderAlreadyCompletedException(command.UserId);

        var @event = command.ToEvent(sequence: Sequence + 1);

        ApplyChange(@event);
    }

    // Apply overload for OrderUpdated event
    public void Apply(OrderUpdated @event)
    {
        CustomerName = @event.Data.CustomerName;
        Total = @event.Data.Total;
    }

    // Business method with domain validation
    public void AddItems(IAddItemsCommand command)
    {
        if (command.Items.All(_items.Contains))
            throw new ItemAlreadyAddedException(command.UserId);

        var @event = command.ToEvent(sequence: Sequence + 1, _items);

        ApplyChange(@event);
    }

    public void Apply(OrderItemsAdded @event)
    {
        _items.AddRange(@event.Data.Items);
    }
}
```

### Pattern: Each event type gets its own `Apply` overload

The aggregate does NOT use a switch statement. Instead, `((dynamic)this).Apply(@event)` resolves to the correct typed `Apply` method at runtime. Each concrete event class dispatches to its own `Apply(ConcreteEvent @event)` method.

### Loading Aggregate from Event Store

```csharp
// In command handler -- load existing aggregate
var events = await _unitOfWork.Events.GetAllByAggregateIdAsync(aggregateId, ct);

if (!events.Any())
    throw new OrderNotFoundException(command.UserId);

var order = Order.LoadFromHistory(events);

// Apply business operation
order.UpdateDetails(command);

// Persist uncommitted events
await _commitEventsService.CommitNewEventsAsync(order);
```

### Creating a New Aggregate

```csharp
// In command handler -- create new aggregate
var events = await _unitOfWork.Events.GetAllByAggregateIdAsync(command.Id, ct);

if (events.Any())
    throw new OrderAlreadyExistException();

var order = Order.Create(command);

await _commitEventsService.CommitNewEventsAsync(order);
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Public constructors for creation | Use static factory methods |
| Public setters on aggregate state | Private setters, change via events only |
| Switch-based Apply routing | Use dynamic dispatch with typed Apply overloads |
| Manual sequence management | Let ApplyChange auto-increment and validate |
| `new Order()` in handler | Use `Order.Create(command)` or `Order.LoadFromHistory(events)` |
| Returning aggregate from handler | Return output DTO or void |
| Business logic outside aggregate | Domain invariants belong on the aggregate |

## Detect Existing Patterns

```bash
# Find aggregate base classes
grep -r "class.*:.*Aggregate<" --include="*.cs" src/

# Find LoadFromHistory usage
grep -r "LoadFromHistory" --include="*.cs" src/

# Find factory methods on aggregates
grep -r "public static.*Create\|Register\|Open" --include="*.cs" src/Domain/

# Find Apply overloads
grep -r "public void Apply(" --include="*.cs" src/Domain/Core/

# Find ApplyChange calls
grep -r "ApplyChange" --include="*.cs" src/
```

## Adding to Existing Project

1. **Check for existing aggregate base** in `Domain/Core/Aggregate.cs`
2. **Match the Apply pattern** -- each event type gets its own `public void Apply(ConcreteEvent)` method
3. **Follow existing factory method naming** (e.g., `Create`, `Register`, `Open`)
4. **Verify command interface** pattern (e.g., `ICreateOrderCommand` with `ToEvent()` extension)
5. **Ensure sequence starts at 1** for creation events, pass `Sequence + 1` for subsequent events
6. **Domain exceptions** should implement `IProblemDetailsProvider` for gRPC error mapping

## Decision Guide

| Scenario | Recommendation |
|---|---|
| New aggregate for a new entity | Create factory method + Apply overloads for each event |
| Adding behavior to existing aggregate | Add business method + new event type + Apply overload |
| Complex invariant validation | Validate in business method before creating event |
| Cross-aggregate validation | Use IQueriesServices in handler, not aggregate |
