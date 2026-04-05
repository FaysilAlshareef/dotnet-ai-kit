---
name: cqrs-basics
description: >
  Command/Query Responsibility Segregation basics. Separate read and write models,
  MediatR integration, and pipeline behaviors.
  Trigger: CQRS, command query separation, read model, write model.
metadata:
  category: architecture
  agent: dotnet-architect
  when-to-use: "When implementing CQRS patterns with separate read and write models"
---

# CQRS Basics

## Core Principles

- Commands change state, Queries read state — never mix them
- Commands return at most an ID or success/failure; Queries return data
- Read and write models can use different storage or projections
- MediatR provides the dispatch mechanism for both commands and queries
- Pipeline behaviors add cross-cutting concerns (validation, logging, transactions)

## Patterns

### Command Definition

```csharp
// Commands represent intent to change state
// Naming: {Verb}{Noun}Command
public sealed record CreateOrderCommand(
    string CustomerName,
    List<CreateOrderCommand.OrderItemDto> Items) : IRequest<Result<Guid>>
{
    public sealed record OrderItemDto(Guid ProductId, int Quantity);
}

public sealed record UpdateOrderStatusCommand(
    Guid OrderId,
    OrderStatus NewStatus) : IRequest<Result>;

public sealed record DeleteOrderCommand(Guid OrderId) : IRequest<Result>;
```

### Query Definition

```csharp
// Queries represent requests for data — never modify state
// Naming: Get{Noun}Query or List{Noun}Query
public sealed record GetOrderQuery(Guid OrderId)
    : IRequest<OrderResponse?>;

public sealed record ListOrdersQuery(
    string? CustomerName,
    OrderStatus? Status,
    int Page = 1,
    int PageSize = 20) : IRequest<PagedList<OrderSummaryResponse>>;
```

### Command Handler

```csharp
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

        logger.LogInformation("Order {OrderId} created", order.Id);
        return Result<Guid>.Success(order.Id);
    }
}
```

### Query Handler

```csharp
internal sealed class ListOrdersQueryHandler(AppDbContext db)
    : IRequestHandler<ListOrdersQuery, PagedList<OrderSummaryResponse>>
{
    public async Task<PagedList<OrderSummaryResponse>> Handle(
        ListOrdersQuery request, CancellationToken ct)
    {
        var query = db.Orders.AsNoTracking();

        if (!string.IsNullOrEmpty(request.CustomerName))
            query = query.Where(o =>
                o.CustomerName.Contains(request.CustomerName));

        if (request.Status.HasValue)
            query = query.Where(o => o.Status == request.Status.Value);

        var totalCount = await query.CountAsync(ct);

        var items = await query
            .OrderByDescending(o => o.CreatedAt)
            .Skip((request.Page - 1) * request.PageSize)
            .Take(request.PageSize)
            .Select(o => new OrderSummaryResponse(
                o.Id, o.CustomerName, o.Total, o.Status.ToString()))
            .ToListAsync(ct);

        return new PagedList<OrderSummaryResponse>(
            items, totalCount, request.Page, request.PageSize);
    }
}
```

### Response DTOs

```csharp
public sealed record OrderResponse(
    Guid Id,
    string CustomerName,
    decimal Total,
    string Status,
    DateTimeOffset CreatedAt,
    List<OrderItemResponse> Items);

public sealed record OrderSummaryResponse(
    Guid Id, string CustomerName, decimal Total, string Status);

public sealed record OrderItemResponse(
    Guid ProductId, string ProductName, int Quantity, decimal UnitPrice);

public sealed record PagedList<T>(
    List<T> Items,
    int TotalCount,
    int Page,
    int PageSize)
{
    public int TotalPages =>
        (int)Math.Ceiling(TotalCount / (double)PageSize);
    public bool HasNext => Page < TotalPages;
    public bool HasPrevious => Page > 1;
}
```

### MediatR Registration

```csharp
// Program.cs
builder.Services.AddMediatR(cfg =>
{
    cfg.RegisterServicesFromAssembly(typeof(Program).Assembly);

    // Pipeline behaviors (order matters: first = outermost)
    cfg.AddBehavior(typeof(IPipelineBehavior<,>),
        typeof(LoggingBehavior<,>));
    cfg.AddBehavior(typeof(IPipelineBehavior<,>),
        typeof(ValidationBehavior<,>));
});

builder.Services.AddValidatorsFromAssembly(typeof(Program).Assembly);
```

### Endpoint Integration

```csharp
// Minimal API
app.MapPost("/orders", async (
    CreateOrderCommand cmd, ISender sender, CancellationToken ct) =>
{
    var result = await sender.Send(cmd, ct);
    return result.Match(
        id => Results.Created($"/orders/{id}", new { id }),
        error => Results.BadRequest(error.ToProblemDetails()));
});

app.MapGet("/orders", async (
    [AsParameters] ListOrdersQuery query,
    ISender sender, CancellationToken ct) =>
{
    return Results.Ok(await sender.Send(query, ct));
});

// Controller
[ApiController]
[Route("api/orders")]
public sealed class OrdersController(ISender sender) : ControllerBase
{
    [HttpPost]
    public async Task<IActionResult> Create(
        CreateOrderCommand command, CancellationToken ct)
    {
        var result = await sender.Send(command, ct);
        return result.Match<IActionResult>(
            id => CreatedAtAction(nameof(Get), new { id }, null),
            error => BadRequest(error.ToProblemDetails()));
    }

    [HttpGet("{id:guid}")]
    public async Task<IActionResult> Get(Guid id, CancellationToken ct)
    {
        var result = await sender.Send(new GetOrderQuery(id), ct);
        return result is not null ? Ok(result) : NotFound();
    }
}
```

## Folder Organization

```
// Clean Architecture + CQRS
Application/
  Orders/
    Commands/
      CreateOrder/
        CreateOrderCommand.cs
        CreateOrderCommandHandler.cs
        CreateOrderCommandValidator.cs
    Queries/
      GetOrder/
        GetOrderQuery.cs
        GetOrderQueryHandler.cs
      ListOrders/
        ListOrdersQuery.cs
        ListOrdersQueryHandler.cs

// VSA + CQRS
Features/
  Orders/
    CreateOrder.cs      # Command + Handler + Validator in one file
    GetOrder.cs         # Query + Handler in one file
    ListOrders.cs       # Query + Handler in one file
```

## Anti-Patterns

- Commands that return full entity data (return only IDs or status)
- Queries that modify state (side effects in read handlers)
- Shared handler for both command and query
- Skipping validation behavior (always validate commands)
- Over-engineering: CQRS with separate databases when a single DB suffices

## Detect Existing Patterns

1. Search for `IRequest<` and `IRequestHandler<` implementations
2. Look for `Command` and `Query` suffixes in class names
3. Check for `MediatR` package reference in `.csproj`
4. Look for `Commands/` and `Queries/` folder structure
5. Check for `IPipelineBehavior<` implementations

## Adding to Existing Project

1. **Install MediatR** and FluentValidation packages
2. **Define command/query naming convention** — `{Verb}{Noun}Command` / `Get{Noun}Query`
3. **Create pipeline behaviors** — validation and logging at minimum
4. **Refactor controllers** — extract logic into command/query handlers
5. **Add validators** for all commands using FluentValidation
6. **Use `AsNoTracking()`** in all query handlers

## Decision Guide

| Scenario | Use |
|----------|-----|
| Creating/updating data | Command |
| Reading/listing data | Query |
| Cross-cutting validation | Pipeline behavior |
| Cross-cutting logging | Pipeline behavior |
| Transaction wrapping | Pipeline behavior on commands only |

## References

- https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/cqrs-microservice-reads
- https://github.com/jbogard/MediatR
