# CQRS Patterns

Command Query Responsibility Segregation reference for .NET applications.
Covers command/query separation, MediatR handlers, pipeline behaviors, event sourcing integration, and decision criteria.

---

## Architecture Overview

```
+------------------------------------------------------------------+
|                         API / Presentation                        |
|                                                                   |
|  POST /orders          GET /orders/{id}                           |
|      |                      |                                     |
|      v                      v                                     |
|  +----------+          +----------+                               |
|  | Command  |          |  Query   |                               |
|  | (IRequest)|         | (IRequest<T>)                            |
|  +----+-----+          +----+-----+                               |
|       |                      |                                    |
|       v                      v                                    |
|  +----------+  MediatR  +----------+                              |
|  | Command  |  Pipeline | Query    |                              |
|  | Handler  |           | Handler  |                              |
|  +----+-----+           +----+-----+                              |
|       |                      |                                    |
|       v                      v                                    |
|  Write Model            Read Model                                |
|  (Domain Aggregates)    (Projections / DTOs)                      |
|  (Event Store / SQL)    (Read-optimized DB / Views)               |
+------------------------------------------------------------------+
```

---

## Core Principle: Command/Query Separation

Commands change state and return nothing (or an ID). Queries return data and change nothing.

```csharp
// Command -- changes state, returns nothing
public record CreateOrderCommand(
    Guid CustomerId,
    List<OrderItemDto> Items
) : IRequest;

// Command that returns a created ID
public record CreateOrderCommand(
    Guid CustomerId,
    List<OrderItemDto> Items
) : IRequest<Guid>;

// Query -- returns data, no side effects
public record GetOrderByIdQuery(Guid OrderId) : IRequest<OrderDto>;
```

---

## MediatR Handlers

### Command Handler

```csharp
public class CreateOrderHandler(
    IOrderRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateOrderCommand, Guid>
{
    public async Task<Guid> Handle(
        CreateOrderCommand request, CancellationToken ct)
    {
        var order = Order.Create(request.CustomerId, request.Items);

        await repository.AddAsync(order, ct);
        await unitOfWork.SaveChangesAsync(ct);

        return order.Id;
    }
}
```

### Query Handler

```csharp
public class GetOrderByIdHandler(IReadDbContext db)
    : IRequestHandler<GetOrderByIdQuery, OrderDto>
{
    public async Task<OrderDto> Handle(
        GetOrderByIdQuery request, CancellationToken ct)
    {
        return await db.Orders
            .Where(o => o.Id == request.OrderId)
            .Select(o => new OrderDto(o.Id, o.CustomerName, o.Total))
            .FirstOrDefaultAsync(ct)
            ?? throw new OrderNotFoundException(request.OrderId);
    }
}
```

---

## Pipeline Behaviors

MediatR pipeline behaviors wrap every request, providing cross-cutting concerns without polluting handlers.

### Validation Behavior

```csharp
public class ValidationBehavior<TRequest, TResponse>(
    IEnumerable<IValidator<TRequest>> validators)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : IRequest<TResponse>
{
    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken ct)
    {
        var context = new ValidationContext<TRequest>(request);
        var failures = validators
            .Select(v => v.Validate(context))
            .SelectMany(r => r.Errors)
            .Where(f => f is not null)
            .ToList();

        if (failures.Count > 0)
            throw new ValidationException(failures);

        return await next();
    }
}
```

### Logging Behavior

```csharp
public class LoggingBehavior<TRequest, TResponse>(
    ILogger<LoggingBehavior<TRequest, TResponse>> logger)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : IRequest<TResponse>
{
    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken ct)
    {
        var name = typeof(TRequest).Name;
        logger.LogInformation("Handling {RequestName}: {@Request}", name, request);

        var response = await next();

        logger.LogInformation("Handled {RequestName}", name);
        return response;
    }
}
```

### Registration

```csharp
services.AddMediatR(cfg =>
{
    cfg.RegisterServicesFromAssembly(Assembly.GetExecutingAssembly());
    cfg.AddBehavior(typeof(IPipelineBehavior<,>), typeof(ValidationBehavior<,>));
    cfg.AddBehavior(typeof(IPipelineBehavior<,>), typeof(LoggingBehavior<,>));
});
```

---

## Integration with Event Sourcing

When combining CQRS with event sourcing, commands produce events on the write side, and the read side builds projections from those events.

```csharp
// Write side -- command handler produces events via aggregate
public class PlaceOrderHandler(ICommitEventService commitService, IUnitOfWork uow)
    : IRequestHandler<PlaceOrderCommand>
{
    public async Task Handle(PlaceOrderCommand request, CancellationToken ct)
    {
        var events = await uow.Events
            .GetAllByAggregateIdAsync(request.OrderId, ct);

        var order = Order.LoadFromHistory(events);
        order.Place(request.UserId);

        await commitService.CommitNewEventsAsync(order);
    }
}

// Read side -- event handler updates projection
public class OrderPlacedProjection(IReadDbContext db)
    : INotificationHandler<OrderPlacedEvent>
{
    public async Task Handle(OrderPlacedEvent notification, CancellationToken ct)
    {
        var view = await db.OrderViews.FindAsync(notification.AggregateId, ct);
        view!.Status = "Placed";
        view.PlacedAt = notification.DateTime;
        await db.SaveChangesAsync(ct);
    }
}
```

---

## Decision Criteria: CQRS vs Simple CRUD

| Factor | Use CQRS | Use Simple CRUD |
|--------|----------|-----------------|
| Read/write ratio | Heavily skewed (10:1+) | Roughly equal |
| Read model complexity | Multiple projections needed | Single model works |
| Domain complexity | Rich business rules | Mostly data in/out |
| Scaling needs | Read and write scale independently | Single DB is fine |
| Team size | Multiple teams on same domain | Small team |
| Event sourcing | Already using or planned | Not needed |

---

## Anti-Patterns

1. **CQS violation** -- Commands that return complex objects or queries that trigger writes
2. **Shared models** -- Using the same DTO for commands and queries defeats the purpose
3. **Over-engineering** -- Applying CQRS to simple CRUD forms with no domain logic
4. **Missing validation** -- Relying on handlers for input validation instead of pipeline behaviors
5. **Fat handlers** -- Putting business logic in handlers instead of domain aggregates
6. **Synchronous projections** -- Updating read models inside command handlers instead of via events

---

## Related Skills and Documents

- `skills/architecture/cqrs-setup.md` -- Scaffold a CQRS project structure
- `skills/architecture/mediatr-pipeline.md` -- Configure MediatR with behaviors
- `knowledge/event-sourcing-flow.md` -- Full event sourcing lifecycle
- `knowledge/clean-architecture-patterns.md` -- Layer separation for CQRS projects
- `knowledge/vsa-patterns.md` -- Alternative: handler-per-feature without layers
