---
name: dotnet-ai-mediatr-handlers
description: >
  MediatR IRequest, IRequestHandler, and INotificationHandler patterns.
  Command and query handler creation, registration, and dispatch.
  Trigger: MediatR, IRequest, IRequestHandler, handler, Send.
category: cqrs
agent: ef-specialist
---

# MediatR Handlers

## Core Principles

- One handler per request — single responsibility
- Commands use `IRequest<TResponse>` for operations that change state
- Queries use `IRequest<TResponse>` for read-only data retrieval
- Notifications use `INotification` for one-to-many event dispatch
- Register all handlers from assembly with `RegisterServicesFromAssembly`

## Patterns

### Command Handler

```csharp
// Command record — immutable, represents intent
public sealed record CreateOrderCommand(
    string CustomerName,
    List<CreateOrderCommand.ItemDto> Items) : IRequest<Result<Guid>>
{
    public sealed record ItemDto(Guid ProductId, int Quantity);
}

// Handler — internal, one per command
internal sealed class CreateOrderCommandHandler(
    IOrderRepository repository,
    IUnitOfWork unitOfWork,
    ILogger<CreateOrderCommandHandler> logger)
    : IRequestHandler<CreateOrderCommand, Result<Guid>>
{
    public async Task<Result<Guid>> Handle(
        CreateOrderCommand request, CancellationToken ct)
    {
        var order = Order.Create(request.CustomerName);

        foreach (var item in request.Items)
            order.AddItem(item.ProductId, item.Quantity);

        repository.Add(order);
        await unitOfWork.SaveChangesAsync(ct);

        logger.LogInformation(
            "Created order {OrderId} for {Customer}",
            order.Id, request.CustomerName);

        return Result<Guid>.Success(order.Id);
    }
}
```

### Query Handler

```csharp
// Query record
public sealed record GetOrderQuery(Guid OrderId)
    : IRequest<OrderResponse?>;

// Handler with DbContext (read-only, no repository needed)
internal sealed class GetOrderQueryHandler(AppDbContext db)
    : IRequestHandler<GetOrderQuery, OrderResponse?>
{
    public async Task<OrderResponse?> Handle(
        GetOrderQuery request, CancellationToken ct)
    {
        return await db.Orders
            .AsNoTracking()
            .Where(o => o.Id == request.OrderId)
            .Select(o => new OrderResponse(
                o.Id,
                o.CustomerName,
                o.Total,
                o.Status.ToString(),
                o.CreatedAt,
                o.Items.Select(i => new OrderItemResponse(
                    i.ProductId, i.ProductName,
                    i.Quantity, i.UnitPrice)).ToList()))
            .FirstOrDefaultAsync(ct);
    }
}
```

### Void Command (No Return Value)

```csharp
// IRequest with no generic parameter = Unit return
public sealed record DeleteOrderCommand(Guid OrderId) : IRequest;

internal sealed class DeleteOrderCommandHandler(
    IOrderRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeleteOrderCommand>
{
    public async Task Handle(
        DeleteOrderCommand request, CancellationToken ct)
    {
        var order = await repository.FindAsync(request.OrderId, ct)
            ?? throw new NotFoundException("Order", request.OrderId);

        repository.Remove(order);
        await unitOfWork.SaveChangesAsync(ct);
    }
}
```

### Notification Handler

```csharp
// Notification — dispatched to multiple handlers
public sealed record OrderCreatedNotification(
    Guid OrderId,
    string CustomerName) : INotification;

// Handler 1: send email
internal sealed class SendOrderConfirmationEmail(
    IEmailService emailService)
    : INotificationHandler<OrderCreatedNotification>
{
    public async Task Handle(
        OrderCreatedNotification notification,
        CancellationToken ct)
    {
        await emailService.SendOrderConfirmationAsync(
            notification.OrderId, notification.CustomerName, ct);
    }
}

// Handler 2: update analytics
internal sealed class UpdateOrderAnalytics(AppDbContext db)
    : INotificationHandler<OrderCreatedNotification>
{
    public async Task Handle(
        OrderCreatedNotification notification,
        CancellationToken ct)
    {
        var stats = await db.DashboardStats.SingleAsync(ct);
        stats.IncrementOrderCount();
        await db.SaveChangesAsync(ct);
    }
}
```

### Registration

```csharp
// Program.cs — register all handlers from assembly
builder.Services.AddMediatR(cfg =>
{
    cfg.RegisterServicesFromAssembly(typeof(Program).Assembly);

    // Or from multiple assemblies
    cfg.RegisterServicesFromAssemblies(
        typeof(CreateOrderCommand).Assembly,
        typeof(OrderCreatedNotification).Assembly);
});
```

### Dispatching from Endpoints

```csharp
// ISender for commands and queries
app.MapPost("/orders", async (
    CreateOrderCommand cmd,
    ISender sender,
    CancellationToken ct) =>
{
    var result = await sender.Send(cmd, ct);
    return result.Match(
        id => Results.Created($"/orders/{id}", new { id }),
        error => Results.BadRequest(error.ToProblemDetails()));
});

// IPublisher for notifications
app.MapPost("/orders/{id}/submit", async (
    Guid id, ISender sender, IPublisher publisher,
    CancellationToken ct) =>
{
    await sender.Send(new SubmitOrderCommand(id), ct);
    await publisher.Publish(
        new OrderSubmittedNotification(id), ct);
    return Results.NoContent();
});
```

## Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Command | `{Verb}{Noun}Command` | `CreateOrderCommand` |
| Query | `Get{Noun}Query` / `List{Noun}Query` | `GetOrderQuery` |
| Handler | `{Command/Query}Handler` | `CreateOrderCommandHandler` |
| Notification | `{Noun}{PastVerb}Notification` | `OrderCreatedNotification` |
| Validator | `{Command}Validator` | `CreateOrderCommandValidator` |

## Anti-Patterns

- Multiple handlers for one request (MediatR allows only one per IRequest)
- Business logic in notification handlers (keep them for side effects only)
- Public handler classes (use `internal sealed`)
- Not propagating CancellationToken through the handler chain
- Returning full entities from handlers (return DTOs or IDs)

## Detect Existing Patterns

1. Search for `IRequest<` and `IRequestHandler<` implementations
2. Look for `INotification` and `INotificationHandler<` implementations
3. Check for `MediatR` package reference in `.csproj`
4. Look for `ISender` or `IMediator` injection
5. Check for `RegisterServicesFromAssembly` calls

## Adding to Existing Project

1. **Install MediatR** — `dotnet add package MediatR`
2. **Register** with `AddMediatR` in `Program.cs`
3. **Create command/query records** following naming conventions
4. **Create handler classes** — one per command/query, internal sealed
5. **Dispatch from endpoints** using `ISender.Send`
6. **Add notifications** for cross-cutting side effects

## References

- https://github.com/jbogard/MediatR
- https://github.com/jbogard/MediatR/wiki
