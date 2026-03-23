---
name: dotnet-ai-event-handler
description: >
  Query-side event handlers implementing IRequestHandler<Event<T>, bool>. Returns bool
  for message completion. Uses IUnitOfWork with named repository properties, strict
  sequence checking, and idempotent duplicate handling.
  Trigger: event handler, query projection, sequence check, idempotent.
category: microservice/query
agent: query-architect
---

# Event Handler — IRequestHandler<Event<T>, bool>

## Core Principles

- Handlers implement `IRequestHandler<Event<TData>, bool>` via MediatR
- Return `true` = message processed or already processed (CompleteMessage)
- Return `false` = cannot process yet (AbandonMessage, retry from Service Bus)
- Use **IUnitOfWork** with named repository properties (e.g., `_unitOfWork.Orders`)
- Primary constructor with field assignment: `handler(IUnitOfWork unitOfWork)`
- Creation handlers: check if entity exists, return `true` if duplicate (idempotent)
- Update handlers: strict sequence check `entity.Sequence != @event.Sequence - 1`
- Call entity behavior methods, then `_unitOfWork.SaveChangesAsync(cancellationToken)`

## Key Patterns

### Creation Event Handler

```csharp
namespace {Company}.{Domain}.Query.Application.Features.Events;

public class OrderCreatedHandler(IUnitOfWork unitOfWork)
    : IRequestHandler<Event<OrderCreatedData>, bool>
{
    private readonly IUnitOfWork _unitOfWork = unitOfWork;

    public async Task<bool> Handle(
        Event<OrderCreatedData> @event,
        CancellationToken cancellationToken)
    {
        var order = await _unitOfWork.Orders.FindAsync(@event.AggregateId);

        // Already exists — idempotent, return true to complete message
        if (order is not null)
            return true;

        // Create entity from event
        order = new Order(@event);

        await _unitOfWork.Orders.AddAsync(order);
        await _unitOfWork.SaveChangesAsync(cancellationToken);

        return true;
    }
}
```

### Update Event Handler (Standard Pattern)

```csharp
namespace {Company}.{Domain}.Query.Application.Features.Events;

public class OrderUpdatedHandler(IUnitOfWork unitOfWork)
    : IRequestHandler<Event<OrderUpdatedData>, bool>
{
    private readonly IUnitOfWork _unitOfWork = unitOfWork;

    public async Task<bool> Handle(
        Event<OrderUpdatedData> @event,
        CancellationToken cancellationToken)
    {
        var order = await _unitOfWork.Orders.FindAsync(@event.AggregateId);

        // Entity not yet created — return false to abandon and retry
        if (order is null)
            return false;

        // Sequence check: must be exactly current + 1
        if (order.Sequence != @event.Sequence - 1)
            return order.Sequence >= @event.Sequence;
            // Already processed -> true (idempotent)
            // Gap/out-of-order -> false (retry)

        // Apply state change via behavior method
        order.UpdateDetails(@event.Data, @event.Sequence);

        await _unitOfWork.SaveChangesAsync(cancellationToken);

        return true;
    }
}
```

### Update Handler Calling Entity Behavior Method

```csharp
namespace {Company}.{Domain}.Query.Application.Features.Events;

public class OrderStatusChangedHandler(IUnitOfWork unitOfWork)
    : IRequestHandler<Event<OrderStatusChangedData>, bool>
{
    private readonly IUnitOfWork _unitOfWork = unitOfWork;

    public async Task<bool> Handle(
        Event<OrderStatusChangedData> @event,
        CancellationToken cancellationToken)
    {
        var order = await _unitOfWork.Orders.FindAsync(@event.AggregateId);

        if (order is null)
            return false;

        if (order.Sequence != @event.Sequence - 1)
            return order.Sequence >= @event.Sequence;

        order.ChangeStatus(@event.Data, @event.Sequence);

        await _unitOfWork.SaveChangesAsync(cancellationToken);

        return true;
    }
}
```

### Creation Handler with Related Entities

```csharp
namespace {Company}.{Domain}.Query.Application.Features.Events;

public class ProductCreatedHandler(IUnitOfWork unitOfWork)
    : IRequestHandler<Event<ProductCreatedData>, bool>
{
    private readonly IUnitOfWork _unitOfWork = unitOfWork;

    public async Task<bool> Handle(
        Event<ProductCreatedData> @event,
        CancellationToken cancellationToken)
    {
        var product = await _unitOfWork.Products.FindAsync(@event.AggregateId);

        if (product is not null)
            return true;

        product = Product.Create(@event);

        await _unitOfWork.Products.AddAsync(product);

        // Add related entities to their own repositories
        await _unitOfWork.ProductVariants.AddRangeAsync(
            @event.Data.Variants.Select(v => new ProductVariant(v, @event.AggregateId)));

        await _unitOfWork.SaveChangesAsync(cancellationToken);

        return true;
    }
}
```

### Update Handler with IncrementSequence

Some entities use `IncrementSequence()` instead of passing sequence to behavior:

```csharp
public async Task<bool> Handle(
    Event<ProductUpdatedData> @event,
    CancellationToken cancellationToken)
{
    var product = await _unitOfWork.Products.FindAsync(@event.AggregateId);

    if (product != null)
    {
        if (product.Sequence == @event.Sequence - 1)
        {
            product.Update(@event);
            product.IncrementSequence();
            await _unitOfWork.SaveChangesAsync(cancellationToken);
        }

        return product.Sequence >= @event.Sequence;
    }
    return false;
}
```

## Handler Return Values

| Scenario | Return | Why |
|---|---|---|
| Entity created successfully | `true` | Complete message |
| Entity already exists (creation) | `true` | Idempotent — already processed |
| Entity updated successfully | `true` | Complete message |
| Already processed (Sequence >= event) | `true` | Idempotent duplicate |
| Entity not found (update event) | `false` | Abandon — creation event not yet processed |
| Sequence gap (out of order) | `false` | Abandon — wait for missing events |

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| `unitOfWork.Repository<T>()` generic | Named properties: `_unitOfWork.Orders` |
| Throwing exceptions in handlers | Return `false` for retry, `true` for skip |
| `if (@event.Sequence <= order.Sequence)` | `if (order.Sequence != @event.Sequence - 1) return order.Sequence >= @event.Sequence;` |
| Separate sequence check and return | Combine into single conditional expression |
| Direct DbContext usage | Use IUnitOfWork with named repository properties |
| `SaveChangesAsync()` without cancellation token | `SaveChangesAsync(cancellationToken)` — always pass cancellation token |

## Detect Existing Patterns

```bash
# Find event handlers returning bool
grep -r "IRequestHandler<Event<.*>, bool>" --include="*.cs" Application/

# Find sequence checking pattern
grep -r "Sequence != @event.Sequence - 1" --include="*.cs" Application/

# Find UnitOfWork usage
grep -r "IUnitOfWork" --include="*.cs" Application/Features/Events/
```

## Adding to Existing Project

1. **One handler per event type** — naming: `{EventType}Handler`
2. **Use primary constructor** with `IUnitOfWork unitOfWork` parameter
3. **Assign to field**: `private readonly IUnitOfWork _unitOfWork = unitOfWork;`
4. **Place in** `Application/Features/Events/{Aggregate}/` directory
5. **Register via MediatR assembly scanning** (automatic with `AddMediatR`)
6. **Creation handlers**: check existence, return `true` if duplicate
7. **Update handlers**: strict sequence check, call entity behavior method
