# Vertical Slice Architecture Patterns

Vertical Slice Architecture (VSA) reference for .NET applications.
Covers feature folder organization, handler-per-endpoint, minimal abstraction, slice independence, and decision criteria.

---

## Architecture Overview

```
+------------------------------------------------------------------+
|  Traditional Layers (horizontal)    |  Vertical Slices            |
|                                     |                             |
|  Controllers/                       |  Features/                  |
|  Services/                          |    CreateOrder/             |
|  Repositories/                      |      Endpoint.cs            |
|  Models/                            |      Command.cs             |
|  DTOs/                              |      Handler.cs             |
|  Validators/                        |      Validator.cs           |
|                                     |    GetOrder/                |
|  A change touches ALL folders       |      Endpoint.cs            |
|                                     |      Query.cs               |
|                                     |      Handler.cs             |
|                                     |                             |
|                                     |  A change touches ONE folder|
+------------------------------------------------------------------+
```

---

## Feature Folder Organization

Each feature is a self-contained folder with everything it needs: endpoint, request, handler, validator, and response.

```
src/Ordering.Api/
  Features/
    Orders/
      CreateOrder/
        CreateOrderEndpoint.cs
        CreateOrderCommand.cs
        CreateOrderHandler.cs
        CreateOrderValidator.cs
      GetOrder/
        GetOrderEndpoint.cs
        GetOrderQuery.cs
        GetOrderHandler.cs
        OrderResponse.cs
      CancelOrder/
        CancelOrderEndpoint.cs
        CancelOrderCommand.cs
        CancelOrderHandler.cs
      ListOrders/
        ListOrdersEndpoint.cs
        ListOrdersQuery.cs
        ListOrdersHandler.cs
        OrderSummaryResponse.cs
  Shared/
    AppDbContext.cs
    BaseEntity.cs
    PaginationRequest.cs
```

---

## Handler-Per-Endpoint Pattern

Each endpoint maps to exactly one handler. No shared service layers, no generic repositories.

### Endpoint

```csharp
public static class CreateOrderEndpoint
{
    public static void Map(IEndpointRouteBuilder app)
    {
        app.MapPost("/api/orders", async (
            CreateOrderCommand command,
            IMediator mediator,
            CancellationToken ct) =>
        {
            var id = await mediator.Send(command, ct);
            return Results.Created($"/api/orders/{id}", new { id });
        })
        .WithName("CreateOrder")
        .WithTags("Orders")
        .Produces<object>(StatusCodes.Status201Created)
        .ProducesValidationProblem();
    }
}
```

### Handler with Inline Data Access

```csharp
public record CreateOrderCommand(
    Guid CustomerId, string Currency, List<OrderItemDto> Items) : IRequest<Guid>;

public class CreateOrderHandler(AppDbContext db)
    : IRequestHandler<CreateOrderCommand, Guid>
{
    public async Task<Guid> Handle(CreateOrderCommand request, CancellationToken ct)
    {
        var order = new Order
        {
            Id = Guid.NewGuid(), CustomerId = request.CustomerId,
            Currency = request.Currency, Status = OrderStatus.Draft
        };

        foreach (var item in request.Items)
            order.Lines.Add(new OrderLine
                { ProductId = item.ProductId, Quantity = item.Quantity, UnitPrice = item.UnitPrice });

        order.Total = order.Lines.Sum(l => l.Quantity * l.UnitPrice);
        db.Orders.Add(order);
        await db.SaveChangesAsync(ct);
        return order.Id;
    }
}
```

### Validator

```csharp
public class CreateOrderValidator : AbstractValidator<CreateOrderCommand>
{
    public CreateOrderValidator()
    {
        RuleFor(x => x.CustomerId).NotEmpty();
        RuleFor(x => x.Currency).NotEmpty().Length(3);
        RuleFor(x => x.Items).NotEmpty()
            .WithMessage("Order must have at least one item.");
        RuleForEach(x => x.Items).ChildRules(item =>
        {
            item.RuleFor(i => i.Quantity).GreaterThan(0);
            item.RuleFor(i => i.UnitPrice).GreaterThan(0);
        });
    }
}
```

---

## Minimal Abstraction Principle

VSA avoids unnecessary indirection. If a handler only needs DbContext, inject DbContext directly. Do not create a repository interface, an implementation, and a registration just to wrap `db.Orders.AddAsync()`.

```csharp
// VSA -- direct DbContext access in handlers
public class GetOrderHandler(AppDbContext db)
    : IRequestHandler<GetOrderQuery, OrderResponse?>
{
    public async Task<OrderResponse?> Handle(
        GetOrderQuery request, CancellationToken ct)
    {
        return await db.Orders
            .AsNoTracking()
            .Where(o => o.Id == request.OrderId)
            .Select(o => new OrderResponse(
                o.Id, o.CustomerName, o.Total, o.Status.ToString()))
            .FirstOrDefaultAsync(ct);
    }
}
```

Shared abstractions are introduced only when genuinely reused across multiple slices (e.g., pagination, soft-delete filtering).

---

## Slice Independence

Slices must not call each other directly. If `CancelOrder` needs data that `GetOrder` also reads, each handler queries the database independently. Cross-cutting logic is handled via MediatR notifications or shared infrastructure.

```csharp
// Slice communication via domain events, not direct calls
public class CancelOrderHandler(AppDbContext db, IMediator mediator)
    : IRequestHandler<CancelOrderCommand>
{
    public async Task Handle(CancelOrderCommand request, CancellationToken ct)
    {
        var order = await db.Orders.FindAsync([request.OrderId], ct)
            ?? throw new NotFoundException("Order", request.OrderId);

        order.Status = OrderStatus.Cancelled;
        order.CancelledAt = DateTime.UtcNow;

        await db.SaveChangesAsync(ct);

        // Notify other slices via event, not direct handler call
        await mediator.Publish(
            new OrderCancelledNotification(order.Id, order.CustomerId), ct);
    }
}
```

---

## Endpoint Registration

```csharp
// Program.cs -- register feature endpoints manually or by convention
var app = builder.Build();

CreateOrderEndpoint.Map(app);
GetOrderEndpoint.Map(app);
CancelOrderEndpoint.Map(app);

// Convention-based: scan for static Map(IEndpointRouteBuilder) methods
app.MapFeatureEndpoints();
```

---

## Decision Criteria: VSA vs Clean Architecture

| Factor | Use VSA | Use Clean Architecture |
|--------|---------|------------------------|
| Domain complexity | Low-to-medium | High (rich domain model) |
| Feature independence | Features rarely share logic | Heavy cross-feature logic |
| Team workflow | One dev per feature | Domain experts needed |
| Change frequency | Features change independently | Core domain evolves together |
| Testability target | Integration tests per slice | Unit tests on domain logic |
| Code navigation | Prefer locality (all in one folder) | Prefer separation by concern |
| Project size | Small-to-medium | Large enterprise |

---

## Anti-Patterns

1. **Shared service layer** -- Creating a `OrderService` used by multiple handlers defeats slice independence
2. **Cross-slice imports** -- One feature handler calling another feature handler directly
3. **Premature abstraction** -- Adding repository interfaces when only one handler uses the query
4. **Inconsistent structure** -- Some features use folders, others are loose files; pick one convention
5. **Fat shared folder** -- Moving too much into `Shared/` until it becomes a horizontal layer
6. **Ignoring domain rules** -- VSA does not mean no domain model; complex invariants still belong in entities

---

## Related Skills and Documents

- `skills/architecture/vsa-setup.md` -- Scaffold a VSA project structure
- `skills/codegen/add-endpoint.md` -- Generate a new feature slice
- `knowledge/cqrs-patterns.md` -- MediatR handler patterns used within slices
- `knowledge/clean-architecture-patterns.md` -- Alternative layered approach
- `knowledge/modular-monolith-patterns.md` -- Combining VSA with module boundaries
