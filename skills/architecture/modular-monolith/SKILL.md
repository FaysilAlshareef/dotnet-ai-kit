---
name: modular-monolith
description: >
  Modular monolith architecture. Module isolation, inter-module communication,
  shared kernel, and migration path to microservices.
  Trigger: modular monolith, modules, module isolation, module communication.
metadata:
  category: architecture
  agent: dotnet-architect
  when-to-use: "When designing modular monolith structure, module isolation, or inter-module communication"
---

# Modular Monolith

## Core Principles

- Each module is a self-contained unit with its own domain, data, and API surface
- Modules communicate through well-defined contracts — never share database tables
- Each module owns its data: separate DbContext per module, potentially separate schemas
- Shared kernel contains only truly cross-cutting types (base classes, common interfaces)
- A modular monolith is the ideal stepping stone toward microservices

## Project Structure

```
src/
  {Company}.{Domain}.WebApi/              # Host — composition root
  {Company}.{Domain}.SharedKernel/        # Base classes, common interfaces

  Modules/
    Orders/
      {Company}.{Domain}.Orders.Api/       # Public contracts (DTOs, interfaces)
      {Company}.{Domain}.Orders.Core/      # Domain + Application logic
      {Company}.{Domain}.Orders.Infrastructure/  # Data access, external services
    Inventory/
      {Company}.{Domain}.Inventory.Api/
      {Company}.{Domain}.Inventory.Core/
      {Company}.{Domain}.Inventory.Infrastructure/
    Shipping/
      {Company}.{Domain}.Shipping.Api/
      {Company}.{Domain}.Shipping.Core/
      {Company}.{Domain}.Shipping.Infrastructure/
```

## Patterns

### Module Public API (Contracts)

```csharp
// Modules/Orders/Orders.Api/IOrderModule.cs
namespace {Company}.{Domain}.Orders.Api;

// Only this project is referenced by other modules
public interface IOrderModule
{
    Task<OrderSummaryDto?> GetOrderSummaryAsync(
        Guid orderId, CancellationToken ct);
    Task<bool> OrderExistsAsync(Guid orderId, CancellationToken ct);
}

public sealed record OrderSummaryDto(
    Guid Id, string CustomerName, decimal Total, string Status);
```

### Module Internal Implementation

```csharp
// Modules/Orders/Orders.Core/OrderModule.cs
namespace {Company}.{Domain}.Orders.Core;

internal sealed class OrderModule(OrderDbContext db) : IOrderModule
{
    public async Task<OrderSummaryDto?> GetOrderSummaryAsync(
        Guid orderId, CancellationToken ct)
    {
        return await db.Orders
            .Where(o => o.Id == orderId)
            .Select(o => new OrderSummaryDto(
                o.Id, o.CustomerName, o.Total, o.Status.ToString()))
            .FirstOrDefaultAsync(ct);
    }

    public async Task<bool> OrderExistsAsync(
        Guid orderId, CancellationToken ct)
    {
        return await db.Orders.AnyAsync(o => o.Id == orderId, ct);
    }
}
```

### Separate DbContext Per Module

```csharp
// Modules/Orders/Orders.Infrastructure/OrderDbContext.cs
namespace {Company}.{Domain}.Orders.Infrastructure;

internal sealed class OrderDbContext(
    DbContextOptions<OrderDbContext> options) : DbContext(options)
{
    public DbSet<Order> Orders => Set<Order>();
    public DbSet<OrderItem> OrderItems => Set<OrderItem>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.HasDefaultSchema("orders"); // schema isolation
        modelBuilder.ApplyConfigurationsFromAssembly(
            typeof(OrderDbContext).Assembly);
    }
}
```

### Inter-Module Communication via Events

```csharp
// SharedKernel/Events/IIntegrationEvent.cs
public interface IIntegrationEvent : INotification
{
    Guid EventId { get; }
    DateTimeOffset OccurredAt { get; }
}

// Orders module publishes
public sealed record OrderPlacedIntegrationEvent(
    Guid OrderId,
    string CustomerName,
    decimal Total) : IIntegrationEvent
{
    public Guid EventId { get; } = Guid.NewGuid();
    public DateTimeOffset OccurredAt { get; } = DateTimeOffset.UtcNow;
}

// Inventory module handles
internal sealed class ReserveInventoryOnOrderPlaced(
    InventoryDbContext db)
    : INotificationHandler<OrderPlacedIntegrationEvent>
{
    public async Task Handle(
        OrderPlacedIntegrationEvent notification,
        CancellationToken ct)
    {
        // Reserve inventory for the order
        var reservation = InventoryReservation.Create(
            notification.OrderId, notification.OccurredAt);
        db.Reservations.Add(reservation);
        await db.SaveChangesAsync(ct);
    }
}
```

### Module Registration

```csharp
// Each module has a registration extension
// Modules/Orders/Orders.Infrastructure/OrderModuleRegistration.cs
public static class OrderModuleRegistration
{
    public static IServiceCollection AddOrderModule(
        this IServiceCollection services, IConfiguration configuration)
    {
        services.AddDbContext<OrderDbContext>(options =>
            options.UseSqlServer(
                configuration.GetConnectionString("Default"),
                sql => sql.MigrationsHistoryTable(
                    "__EFMigrationsHistory", "orders")));

        services.AddScoped<IOrderModule, OrderModule>();

        services.AddMediatR(cfg =>
            cfg.RegisterServicesFromAssembly(
                typeof(OrderModule).Assembly));

        return services;
    }
}

// WebApi/Program.cs
builder.Services
    .AddOrderModule(builder.Configuration)
    .AddInventoryModule(builder.Configuration)
    .AddShippingModule(builder.Configuration);
```

### Shared Kernel

```csharp
// SharedKernel/BaseEntity.cs
public abstract class BaseEntity
{
    public Guid Id { get; protected set; } = Guid.NewGuid();

    private readonly List<IDomainEvent> _domainEvents = [];
    public IReadOnlyList<IDomainEvent> DomainEvents =>
        _domainEvents.AsReadOnly();

    protected void AddDomainEvent(IDomainEvent e) => _domainEvents.Add(e);
    public void ClearDomainEvents() => _domainEvents.Clear();
}

// SharedKernel/IUnitOfWork.cs
public interface IUnitOfWork
{
    Task<int> SaveChangesAsync(CancellationToken ct = default);
}
```

## Anti-Patterns

- Modules sharing database tables or DbContext instances
- Module A directly querying Module B's DbContext
- Circular dependencies between modules
- Putting business logic in the shared kernel (keep it minimal)
- Making module internals public (use `InternalsVisibleTo` for tests only)
- Synchronous cross-module calls during write operations

## Detect Existing Patterns

1. Look for `Modules/` folder structure in the solution
2. Check for multiple DbContext classes with separate schemas
3. Look for integration event types and handlers
4. Check for module API/contracts projects referenced by other modules
5. Verify modules have their own DI registration extension methods

## Adding to Existing Project

1. **Identify bounded contexts** — group related features into modules
2. **Create module structure** — Api (contracts), Core (logic), Infrastructure (data)
3. **Separate DbContexts** — one per module with schema isolation
4. **Define module interfaces** — public contracts in the Api project
5. **Implement integration events** for cross-module communication
6. **Create module registration** extension methods for the host

## Decision Guide

| Question | Answer |
|----------|--------|
| How do modules communicate? | Integration events (async) or module interfaces (sync reads) |
| Can modules share a database? | Same server is OK, but use separate schemas |
| What goes in SharedKernel? | Base classes, common interfaces, integration event contracts |
| When to split into microservices? | When independent deployment or scaling is needed |
| How to handle transactions across modules? | Eventual consistency via events; avoid distributed transactions |

## References

- https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/
- https://www.youtube.com/watch?v=5OjqD-ow8GE (Modular Monolith with DDD)
