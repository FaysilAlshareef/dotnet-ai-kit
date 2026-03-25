# Clean Architecture Patterns

Clean Architecture reference for .NET applications.
Covers layer separation, the dependency rule, use cases, ports and adapters, and decision criteria.

---

## Layer Overview

```
+------------------------------------------------------------------+
|                        API / Presentation                         |
|  Controllers, Minimal API endpoints, gRPC services, middleware    |
|  References: Application                                          |
+------------------------------------------------------------------+
         |                                              ^
         | calls                                        | implements
         v                                              |
+------------------------------------------------------------------+
|                         Application                               |
|  Use cases (command/query handlers), DTOs, interfaces (ports)     |
|  References: Domain                                               |
+------------------------------------------------------------------+
         |                                              ^
         | calls                                        | implements
         v                                              |
+------------------------------------------------------------------+
|                            Domain                                 |
|  Aggregates, entities, value objects, domain events, enums        |
|  References: nothing (innermost layer)                            |
+------------------------------------------------------------------+
         ^
         | implements interfaces defined in Application
         |
+------------------------------------------------------------------+
|                        Infrastructure                             |
|  EF Core DbContext, repositories, external service clients,       |
|  message bus, file system, email, caching                         |
|  References: Application, Domain                                  |
+------------------------------------------------------------------+
```

---

## The Dependency Rule

Dependencies point inward only. Inner layers never reference outer layers.

```
API --> Application --> Domain
Infrastructure --> Application --> Domain
```

Key constraints:
1. **Domain** has zero project references and zero NuGet dependencies (except shared kernel)
2. **Application** references only Domain; defines interfaces that Infrastructure implements
3. **Infrastructure** references Application and Domain; implements persistence and external services
4. **API** references Application; wires up DI and maps HTTP to commands/queries

---

## Project Structure

```
src/
  Ordering.Domain/
    Aggregates/Order.cs
    ValueObjects/Money.cs
    Events/OrderSubmittedEvent.cs
    Enums/OrderStatus.cs
    Exceptions/DomainException.cs

  Ordering.Application/
    Orders/
      Commands/CreateOrder/CreateOrderCommand.cs
      Commands/CreateOrder/CreateOrderHandler.cs
      Commands/CreateOrder/CreateOrderValidator.cs
      Queries/GetOrder/GetOrderQuery.cs
      Queries/GetOrder/GetOrderHandler.cs
      Queries/GetOrder/OrderDto.cs
    Contracts/
      IOrderRepository.cs
      IUnitOfWork.cs
      IEmailService.cs

  Ordering.Infrastructure/
    Persistence/
      AppDbContext.cs
      Repositories/OrderRepository.cs
      Configurations/OrderConfiguration.cs
    Services/
      EmailService.cs

  Ordering.Api/
    Endpoints/OrderEndpoints.cs
    Program.cs
```

---

## Use Cases / Application Services

Each use case is a single MediatR handler. It orchestrates domain objects and infrastructure ports.

### Command Use Case

```csharp
public record CreateOrderCommand(
    Guid CustomerId,
    string Currency,
    List<OrderItemDto> Items
) : IRequest<Guid>;

public class CreateOrderHandler(
    IOrderRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateOrderCommand, Guid>
{
    public async Task<Guid> Handle(
        CreateOrderCommand request, CancellationToken ct)
    {
        var order = Order.Create(request.CustomerId, request.Currency);

        foreach (var item in request.Items)
        {
            order.AddLine(item.ProductId, item.Quantity,
                new Money(item.UnitPrice, request.Currency));
        }

        await repository.AddAsync(order, ct);
        await unitOfWork.SaveChangesAsync(ct);

        return order.Id;
    }
}
```

### Query Use Case

```csharp
public record GetOrderQuery(Guid OrderId) : IRequest<OrderDto>;

public class GetOrderHandler(IReadDbContext db)
    : IRequestHandler<GetOrderQuery, OrderDto>
{
    public async Task<OrderDto> Handle(
        GetOrderQuery request, CancellationToken ct)
    {
        return await db.Orders
            .AsNoTracking()
            .Where(o => o.Id == request.OrderId)
            .Select(o => new OrderDto
            {
                Id = o.Id,
                CustomerName = o.CustomerName,
                Total = o.TotalAmount,
                Status = o.Status.ToString(),
                LineCount = o.Lines.Count
            })
            .FirstOrDefaultAsync(ct)
            ?? throw new NotFoundException(nameof(Order), request.OrderId);
    }
}
```

---

## Ports and Adapters

Ports are interfaces defined in the Application layer. Adapters are implementations in Infrastructure.

```csharp
// Port -- defined in Application layer
public interface IEmailService
{
    Task SendOrderConfirmationAsync(Guid orderId, string email, CancellationToken ct);
}

// Adapter -- implemented in Infrastructure layer
public class SmtpEmailService(IConfiguration config) : IEmailService
{
    public async Task SendOrderConfirmationAsync(
        Guid orderId, string email, CancellationToken ct)
    {
        // SMTP implementation -- domain and application never know about SMTP
    }
}
```

### DI Registration Pattern

Each layer exposes a single extension method. The API composes them at startup.

```csharp
// Application/DependencyInjection.cs
public static IServiceCollection AddApplication(this IServiceCollection services)
{
    services.AddMediatR(cfg =>
        cfg.RegisterServicesFromAssembly(Assembly.GetExecutingAssembly()));
    services.AddValidatorsFromAssembly(Assembly.GetExecutingAssembly());
    return services;
}

// Infrastructure/DependencyInjection.cs
public static IServiceCollection AddInfrastructure(
    this IServiceCollection services, IConfiguration config)
{
    services.AddDbContext<AppDbContext>(o =>
        o.UseSqlServer(config.GetConnectionString("Default")));
    services.AddScoped<IUnitOfWork, UnitOfWork>();
    services.AddScoped<IOrderRepository, OrderRepository>();
    services.AddScoped<IEmailService, SmtpEmailService>();
    return services;
}

// Program.cs
builder.Services.AddApplication();
builder.Services.AddInfrastructure(builder.Configuration);
```

---

## Decision Criteria: When to Use Clean Architecture

| Factor | Use Clean Architecture | Use Simpler Structure |
|--------|------------------------|-----------------------|
| Domain complexity | Rich business rules | Simple CRUD |
| Project lifespan | Long-lived (years) | Short-lived / prototype |
| Team size | Multiple teams / devs | Solo developer |
| Testability needs | High (unit test domain in isolation) | Integration tests suffice |
| Infrastructure changes | Likely (swap DB, add message bus) | Stable tech stack |
| Regulatory requirements | Audit trail, compliance logic | None |

---

## Anti-Patterns

1. **Layer skipping** -- API calling Infrastructure directly, bypassing Application
2. **Domain depending on Infrastructure** -- Aggregate importing EF Core namespaces
3. **Anemic Application layer** -- Handlers that just pass through to repositories with no orchestration
4. **Shared DTOs across layers** -- Using the same class for API response, handler result, and DB entity
5. **God DbContext** -- Single DbContext for all bounded contexts instead of one per module
6. **Infrastructure in Domain** -- Putting `[JsonProperty]` or `[Column]` attributes on domain entities

---

## Related Skills and Documents

- `skills/architecture/clean-arch-setup.md` -- Scaffold a Clean Architecture solution
- `skills/architecture/cqrs-setup.md` -- Add CQRS to a Clean Architecture project
- `knowledge/cqrs-patterns.md` -- Command/Query handlers in the Application layer
- `knowledge/ddd-patterns.md` -- Domain layer patterns
- `knowledge/modular-monolith-patterns.md` -- Multi-module Clean Architecture
