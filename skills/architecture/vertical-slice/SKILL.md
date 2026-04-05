---
name: vertical-slice
description: >
  Vertical Slice Architecture with feature folders, MediatR handlers per slice,
  minimal abstraction, and co-located code.
  Trigger: vertical slice, VSA, feature folders, feature-based.
metadata:
  category: architecture
  agent: dotnet-architect
  when-to-use: "When organizing code by feature using Vertical Slice Architecture"
---

# Vertical Slice Architecture

## Core Principles

- Organize by feature, not by layer — each slice is self-contained
- Minimize abstractions: handler talks to DbContext directly, no repository layer
- One file per operation containing Request, Response, Handler, Validator
- Each slice can use whatever data access pattern makes sense (EF, Dapper, raw SQL)
- Shared code goes in `Common/` or `Shared/` — extract only when duplication is proven

## Project Structure

```
src/{Company}.{Domain}.WebApi/
  Features/
    Orders/
      CreateOrder.cs          # Command + Handler + Validator
      GetOrder.cs             # Query + Handler
      ListOrders.cs           # Query + Handler + Filter
      OrderEndpoints.cs       # Endpoint group registration
      OrderResponse.cs        # Shared response DTO (if reused)
    Products/
      CreateProduct.cs
      GetProduct.cs
      ProductEndpoints.cs
  Common/
    PagedList.cs
    ValidationBehavior.cs
  Program.cs
```

## Patterns

### Single-File Feature Slice

```csharp
// Features/Orders/CreateOrder.cs
namespace {Company}.{Domain}.Features.Orders;

public static class CreateOrder
{
    public sealed record Command(
        string CustomerName,
        List<LineItem> Items) : IRequest<Result>;

    public sealed record LineItem(Guid ProductId, int Quantity);
    public sealed record Result(Guid OrderId);

    public sealed class Validator : AbstractValidator<Command>
    {
        public Validator()
        {
            RuleFor(x => x.CustomerName).NotEmpty().MaximumLength(200);
            RuleFor(x => x.Items).NotEmpty();
            RuleForEach(x => x.Items).ChildRules(item =>
            {
                item.RuleFor(x => x.Quantity).GreaterThan(0);
            });
        }
    }

    internal sealed class Handler(AppDbContext db)
        : IRequestHandler<Command, Result>
    {
        public async Task<Result> Handle(
            Command request, CancellationToken ct)
        {
            var order = new Order
            {
                CustomerName = request.CustomerName,
                Items = request.Items.Select(i => new OrderItem
                {
                    ProductId = i.ProductId,
                    Quantity = i.Quantity
                }).ToList()
            };

            db.Orders.Add(order);
            await db.SaveChangesAsync(ct);

            return new Result(order.Id);
        }
    }
}
```

### Query Slice with Projection

```csharp
// Features/Orders/ListOrders.cs
namespace {Company}.{Domain}.Features.Orders;

public static class ListOrders
{
    public sealed record Query(
        string? CustomerName,
        int Page = 1,
        int PageSize = 20) : IRequest<PagedList<OrderSummary>>;

    public sealed record OrderSummary(
        Guid Id, string CustomerName, decimal Total, DateTime CreatedAt);

    internal sealed class Handler(AppDbContext db)
        : IRequestHandler<Query, PagedList<OrderSummary>>
    {
        public async Task<PagedList<OrderSummary>> Handle(
            Query request, CancellationToken ct)
        {
            var query = db.Orders.AsNoTracking();

            if (!string.IsNullOrEmpty(request.CustomerName))
                query = query.Where(o =>
                    o.CustomerName.Contains(request.CustomerName));

            var totalCount = await query.CountAsync(ct);

            var items = await query
                .OrderByDescending(o => o.CreatedAt)
                .Skip((request.Page - 1) * request.PageSize)
                .Take(request.PageSize)
                .Select(o => new OrderSummary(
                    o.Id, o.CustomerName, o.Total, o.CreatedAt))
                .ToListAsync(ct);

            return new PagedList<OrderSummary>(
                items, totalCount, request.Page, request.PageSize);
        }
    }
}
```

### Endpoint Group Registration

```csharp
// Features/Orders/OrderEndpoints.cs
namespace {Company}.{Domain}.Features.Orders;

public sealed class OrderEndpoints : IEndpointGroup
{
    public void MapEndpoints(IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/orders")
            .WithTags("Orders")
            .RequireAuthorization();

        group.MapPost("/", async (
            CreateOrder.Command cmd, ISender sender) =>
        {
            var result = await sender.Send(cmd);
            return TypedResults.Created(
                $"/orders/{result.OrderId}", result);
        }).WithSummary("Create a new order");

        group.MapGet("/", async (
            [AsParameters] ListOrders.Query query, ISender sender) =>
        {
            var result = await sender.Send(query);
            return TypedResults.Ok(result);
        }).WithSummary("List orders with filtering");

        group.MapGet("/{id:guid}", async (
            Guid id, ISender sender) =>
        {
            var result = await sender.Send(new GetOrder.Query(id));
            return result is not null
                ? TypedResults.Ok(result)
                : TypedResults.NotFound();
        }).WithSummary("Get order by ID");
    }
}
```

### When to Extract Shared Code

```csharp
// Extract ONLY when the same logic appears in 3+ slices
// Common/Extensions/QueryableExtensions.cs
public static class QueryableExtensions
{
    public static async Task<PagedList<T>> ToPagedListAsync<T>(
        this IQueryable<T> query, int page, int pageSize,
        CancellationToken ct)
    {
        var count = await query.CountAsync(ct);
        var items = await query
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync(ct);
        return new PagedList<T>(items, count, page, pageSize);
    }
}
```

## Anti-Patterns

- Creating repository abstractions for every entity (defeats VSA simplicity)
- Sharing handlers across slices (each slice is independent)
- Premature extraction into shared code (wait for proven duplication)
- Layering VSA into Domain/Application/Infrastructure folders
- Making all classes public (handlers should be `internal`)

## Detect Existing Patterns

1. Check for `Features/` folder structure with operation-named files
2. Look for static classes containing nested `Command`, `Query`, `Handler`
3. Verify MediatR usage without repository abstractions
4. Check if handlers reference `DbContext` directly
5. Look for `IEndpointGroup` or similar endpoint grouping patterns

## Adding to Existing Project

1. **Create `Features/` folder** at the project root
2. **Add one feature folder** per aggregate or domain concept
3. **Create slice files** — one per operation with nested Request + Handler + Validator
4. **Register MediatR** to scan the assembly for handlers
5. **Create endpoint groups** per feature for route registration
6. **Keep shared code minimal** — `Common/` for truly cross-cutting utilities only

## Decision Guide

| Question | VSA Answer |
|----------|-----------|
| Where does the handler go? | Same file as the command/query |
| Do I need a repository? | No — use DbContext directly |
| When do I extract shared code? | After 3+ duplications |
| Can different slices use different data access? | Yes — EF, Dapper, raw SQL per slice |
| How do I handle cross-cutting? | MediatR pipeline behaviors |
| What about domain logic? | Keep in entity methods, call from handler |

## References

- https://www.jimmybogard.com/vertical-slice-architecture/
- https://www.youtube.com/watch?v=SUiWfhAhgQw (Jimmy Bogard NDC talk)
