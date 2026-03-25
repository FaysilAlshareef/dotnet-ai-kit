# Modular Monolith Patterns

Modular Monolith architecture reference for .NET applications.
Covers module boundaries, inter-module communication, shared kernel, independent deployability, and decision criteria.

---

## Architecture Overview

```
+------------------------------------------------------------------+
|                        Host Application                           |
|  Program.cs -- composes modules, shared middleware, auth          |
+------------------------------------------------------------------+
         |              |              |              |
         v              v              v              v
+------------+  +------------+  +------------+  +------------+
|  Ordering  |  |  Catalog   |  | Shipping   |  |  Identity  |
|   Module   |  |   Module   |  |   Module   |  |   Module   |
|            |  |            |  |            |  |            |
| Domain     |  | Domain     |  | Domain     |  | Domain     |
| Application|  | Application|  | Application|  | Application|
| Infra      |  | Infra      |  | Infra      |  | Infra      |
| API        |  | API        |  | API        |  | API        |
+-----+------+  +-----+------+  +-----+------+  +------+-----+
      |                |                |                |
      v                v                v                v
+----------+    +----------+    +----------+    +----------+
| ordering |    | catalog  |    | shipping |    | identity |
| (schema) |    | (schema) |    | (schema) |    | (schema) |
+----------+    +----------+    +----------+    +----------+
                    One Database
```

---

## Module Boundaries and Encapsulation

Each module is a set of projects (or a single project with folders) that owns its domain, data, and API surface. Modules expose only what is needed via explicit contracts.

### Module Structure

```
src/
  Modules/
    Ordering/
      Ordering.Domain/
        Aggregates/Order.cs
        Events/OrderSubmittedEvent.cs
      Ordering.Application/
        Commands/CreateOrderHandler.cs
        Contracts/IOrderRepository.cs
      Ordering.Infrastructure/
        Persistence/OrderDbContext.cs
        Repositories/OrderRepository.cs
      Ordering.Api/
        Endpoints/OrderEndpoints.cs
      Ordering.Contracts/            <-- public module API
        Events/OrderSubmittedIntegrationEvent.cs
        Interfaces/IOrderModule.cs
        DTOs/OrderSummaryDto.cs

  Shared/
    SharedKernel/                    <-- shared base types
      AggregateRoot.cs
      IDomainEvent.cs
      IIntegrationEvent.cs

  Host/
    Program.cs
```

### Encapsulation Rules

```csharp
// Module contract -- the ONLY public interface other modules can use
public interface IOrderModule
{
    Task<OrderSummaryDto?> GetOrderSummaryAsync(Guid orderId, CancellationToken ct);
    Task<bool> OrderExistsAsync(Guid orderId, CancellationToken ct);
}

// Internal implementation -- not visible to other modules
internal class OrderModuleFacade(AppDbContext db) : IOrderModule
{
    public async Task<OrderSummaryDto?> GetOrderSummaryAsync(
        Guid orderId, CancellationToken ct)
    {
        return await db.Orders
            .Where(o => o.Id == orderId)
            .Select(o => new OrderSummaryDto(o.Id, o.Total, o.Status.ToString()))
            .FirstOrDefaultAsync(ct);
    }

    public async Task<bool> OrderExistsAsync(Guid orderId, CancellationToken ct)
    {
        return await db.Orders.AnyAsync(o => o.Id == orderId, ct);
    }
}
```

---

## Inter-Module Communication

Modules communicate via integration events (async) or module contracts (sync). Never via shared database tables.

### Integration Events (Async, Preferred)

```csharp
// Integration event -- lives in Ordering.Contracts, referenced by Shipping
public record OrderSubmittedIntegrationEvent(
    Guid OrderId, Guid CustomerId, decimal Total) : IIntegrationEvent;

// Ordering module publishes after commit
public class SubmitOrderHandler(
    IOrderRepository repository, IUnitOfWork unitOfWork, IEventBus eventBus)
    : IRequestHandler<SubmitOrderCommand>
{
    public async Task Handle(SubmitOrderCommand request, CancellationToken ct)
    {
        var order = await repository.GetByIdAsync(request.OrderId, ct)
            ?? throw new NotFoundException("Order", request.OrderId);
        order.Submit();
        await unitOfWork.SaveChangesAsync(ct);
        await eventBus.PublishAsync(new OrderSubmittedIntegrationEvent(
            order.Id, order.CustomerId, order.Total.Amount), ct);
    }
}

// Shipping module subscribes -- no direct reference to Ordering internals
public class OrderSubmittedHandler(ShippingDbContext db)
    : IIntegrationEventHandler<OrderSubmittedIntegrationEvent>
{
    public async Task Handle(OrderSubmittedIntegrationEvent @event, CancellationToken ct)
    {
        var shipment = Shipment.CreateFor(@event.OrderId, @event.CustomerId);
        db.Shipments.Add(shipment);
        await db.SaveChangesAsync(ct);
    }
}
```

### Module Contracts (Sync, When Needed)

```csharp
// Shipping module needs to check if order exists before creating shipment
public class CreateShipmentHandler(
    ShippingDbContext db,
    IOrderModule orderModule)
    : IRequestHandler<CreateShipmentCommand, Guid>
{
    public async Task<Guid> Handle(
        CreateShipmentCommand request, CancellationToken ct)
    {
        var exists = await orderModule.OrderExistsAsync(request.OrderId, ct);
        if (!exists)
            throw new NotFoundException("Order", request.OrderId);

        var shipment = Shipment.CreateFor(request.OrderId, request.RecipientId);
        db.Shipments.Add(shipment);
        await db.SaveChangesAsync(ct);

        return shipment.Id;
    }
}
```

---

## Shared Kernel Pattern

The shared kernel contains base types that all modules use. It must be small and stable.

```csharp
// SharedKernel project -- referenced by all modules
public abstract class AggregateRoot
{
    private readonly List<IDomainEvent> _domainEvents = [];
    public Guid Id { get; protected set; }
    public IReadOnlyList<IDomainEvent> DomainEvents => _domainEvents;
    protected void RaiseDomainEvent(IDomainEvent e) => _domainEvents.Add(e);
    public void ClearDomainEvents() => _domainEvents.Clear();
}

public interface IDomainEvent { DateTime OccurredOn { get; } }
public interface IIntegrationEvent { }

public record PaginatedResult<T>(
    List<T> Items, int TotalCount, int Page, int PageSize);
```

Shared kernel rules:
1. Only truly cross-cutting types (base classes, marker interfaces, pagination)
2. No business logic -- if it belongs to a domain, it belongs in a module
3. Changes require agreement across all module teams
4. Versioned independently if extracted to a NuGet package

---

## Module Registration

Each module exposes a single `Add*Module` extension. The host composes all modules.

```csharp
// Ordering module registration
public static class OrderingModuleRegistration
{
    public static IServiceCollection AddOrderingModule(
        this IServiceCollection services, IConfiguration config)
    {
        services.AddDbContext<OrderDbContext>(o =>
            o.UseSqlServer(config.GetConnectionString("Default"),
                sql => sql.MigrationsHistoryTable("__EFMigrationsHistory", "ordering")));
        services.AddScoped<IOrderRepository, OrderRepository>();
        services.AddScoped<IOrderModule, OrderModuleFacade>();
        services.AddMediatR(cfg =>
            cfg.RegisterServicesFromAssembly(typeof(OrderingModuleRegistration).Assembly));
        return services;
    }
}

// Host Program.cs
builder.Services.AddOrderingModule(builder.Configuration);
builder.Services.AddCatalogModule(builder.Configuration);
builder.Services.AddShippingModule(builder.Configuration);
```

---

## Independent Deployability Preparation

A modular monolith can be split into microservices later by replacing in-process communication with network calls.

| Monolith | Microservice Equivalent |
|----------|-------------------------|
| `IOrderModule` (in-process) | HTTP/gRPC client |
| `IEventBus` (in-memory) | Azure Service Bus / RabbitMQ |
| Shared database, separate schemas | Separate databases |
| Single deployment | Independent deployments |

---

## Decision Criteria: Modular Monolith vs Microservices

| Factor | Modular Monolith | Microservices |
|--------|-------------------|---------------|
| Team size | 1-4 teams | 5+ independent teams |
| Deployment cadence | Coordinated releases acceptable | Teams must deploy independently |
| Operational maturity | Standard DevOps | Kubernetes, service mesh, observability |
| Latency sensitivity | In-process calls are fast | Network overhead per call |
| Data consistency | Easier with shared DB | Eventual consistency required |
| Complexity budget | Lower (no distributed systems) | Higher (retries, circuit breakers, sagas) |

---

## Anti-Patterns

1. **Shared database tables** -- Modules reading/writing each other's tables bypasses encapsulation
2. **Circular module dependencies** -- Module A depends on Module B and vice versa; extract shared logic
3. **Fat shared kernel** -- Putting domain logic in the shared kernel instead of in the owning module
4. **Direct class references** -- Importing internal types from another module instead of using contracts
5. **No module boundaries** -- All code in one project with folder-only separation; enforce with project references
6. **Big bang extraction** -- Trying to split all modules to microservices at once instead of one at a time

---

## Related Skills and Documents

- `skills/architecture/modular-monolith-setup.md` -- Scaffold a modular monolith solution
- `skills/architecture/module-extraction.md` -- Extract a module to a microservice
- `knowledge/ddd-patterns.md` -- Bounded contexts map to modules
- `knowledge/clean-architecture-patterns.md` -- Layer structure within each module
- `knowledge/event-sourcing-flow.md` -- Event-based inter-module communication
