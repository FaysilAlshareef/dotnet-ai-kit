---
name: repository-patterns
description: >
  Repository pattern with Unit of Work, specification pattern, generic and
  specialized repositories, and proper EF Core integration.
  Trigger: repository, unit of work, specification, IRepository, data access.
metadata:
  category: data
  agent: ef-specialist
  when-to-use: "When implementing repository pattern, Unit of Work, or data access abstractions"
---

# Repository & Unit of Work Patterns

## Core Principles

- Repository per aggregate root — not per entity
- Unit of Work coordinates transaction boundaries (DbContext is already a UoW)
- Generic repository for common CRUD, specialized for aggregate-specific queries
- Repositories return domain entities, not DTOs
- Read-only repository interface for CQRS query side

## Patterns

### Generic Repository Interface

```csharp
public interface IRepository<T> where T : class, IAggregateRoot
{
    Task<T?> FindAsync(Guid id, CancellationToken ct = default);
    Task<List<T>> ListAsync(CancellationToken ct = default);
    void Add(T entity);
    void Update(T entity);
    void Remove(T entity);
}

public interface IReadRepository<T> where T : class
{
    Task<T?> FindAsync(Guid id, CancellationToken ct = default);
    Task<List<T>> ListAsync(CancellationToken ct = default);
    Task<bool> ExistsAsync(Guid id, CancellationToken ct = default);
}
```

### Unit of Work

```csharp
public interface IUnitOfWork
{
    Task<int> SaveChangesAsync(CancellationToken ct = default);
}

// DbContext IS the Unit of Work
internal sealed class UnitOfWork(AppDbContext db) : IUnitOfWork
{
    public Task<int> SaveChangesAsync(CancellationToken ct)
        => db.SaveChangesAsync(ct);
}
```

### Generic Repository Implementation

```csharp
internal class EfRepository<T>(AppDbContext db)
    : IRepository<T> where T : class, IAggregateRoot
{
    protected readonly AppDbContext Db = db;
    private readonly DbSet<T> _set = db.Set<T>();

    public virtual async Task<T?> FindAsync(
        Guid id, CancellationToken ct)
        => await _set.FindAsync([id], ct);

    public virtual async Task<List<T>> ListAsync(CancellationToken ct)
        => await _set.ToListAsync(ct);

    public void Add(T entity) => _set.Add(entity);
    public void Update(T entity) => _set.Update(entity);
    public void Remove(T entity) => _set.Remove(entity);
}
```

### Specialized Repository

```csharp
public interface IOrderRepository : IRepository<Order>
{
    Task<Order?> FindWithItemsAsync(
        Guid id, CancellationToken ct = default);
    Task<List<Order>> FindByCustomerAsync(
        Guid customerId, CancellationToken ct = default);
    Task<List<Order>> FindPendingAsync(CancellationToken ct = default);
}

internal sealed class OrderRepository(AppDbContext db)
    : EfRepository<Order>(db), IOrderRepository
{
    public async Task<Order?> FindWithItemsAsync(
        Guid id, CancellationToken ct)
        => await Db.Orders
            .Include(o => o.Items)
            .AsSplitQuery()
            .FirstOrDefaultAsync(o => o.Id == id, ct);

    public async Task<List<Order>> FindByCustomerAsync(
        Guid customerId, CancellationToken ct)
        => await Db.Orders
            .Where(o => o.CustomerId == customerId)
            .OrderByDescending(o => o.CreatedAt)
            .ToListAsync(ct);

    public async Task<List<Order>> FindPendingAsync(CancellationToken ct)
        => await Db.Orders
            .Where(o => o.Status == OrderStatus.Pending)
            .ToListAsync(ct);
}
```

### Specification Pattern

```csharp
// Using Ardalis.Specification
public sealed class OrdersByCustomerSpec : Specification<Order>
{
    public OrdersByCustomerSpec(
        Guid customerId, int page, int pageSize)
    {
        Query
            .Where(o => o.CustomerId == customerId)
            .Include(o => o.Items)
            .OrderByDescending(o => o.CreatedAt)
            .Skip((page - 1) * pageSize)
            .Take(pageSize);
    }
}

public sealed class OrderByIdSpec : SingleResultSpecification<Order>
{
    public OrderByIdSpec(Guid orderId)
    {
        Query
            .Where(o => o.Id == orderId)
            .Include(o => o.Items)
            .AsSplitQuery();
    }
}

// Projection specification
public sealed class OrderSummarySpec
    : Specification<Order, OrderSummaryDto>
{
    public OrderSummarySpec(DateTime fromDate)
    {
        Query
            .Where(o => o.CreatedAt >= fromDate)
            .OrderByDescending(o => o.Total)
            .Select(o => new OrderSummaryDto(
                o.Id, o.CustomerName, o.Total));
    }
}
```

### Repository with Specification Support

```csharp
public interface ISpecRepository<T> where T : class
{
    Task<T?> FirstOrDefaultAsync(
        ISpecification<T> spec, CancellationToken ct = default);
    Task<List<T>> ListAsync(
        ISpecification<T> spec, CancellationToken ct = default);
    Task<int> CountAsync(
        ISpecification<T> spec, CancellationToken ct = default);
    Task<List<TResult>> ListAsync<TResult>(
        ISpecification<T, TResult> spec, CancellationToken ct = default);
}
```

### DI Registration

```csharp
public static class DependencyInjection
{
    public static IServiceCollection AddRepositories(
        this IServiceCollection services)
    {
        // Generic repository
        services.AddScoped(typeof(IRepository<>), typeof(EfRepository<>));

        // Specialized repositories
        services.AddScoped<IOrderRepository, OrderRepository>();
        services.AddScoped<ICustomerRepository, CustomerRepository>();

        // Unit of Work
        services.AddScoped<IUnitOfWork, UnitOfWork>();

        return services;
    }
}
```

### Usage in Handler

```csharp
internal sealed class CreateOrderHandler(
    IOrderRepository orderRepository,
    IUnitOfWork unitOfWork,
    ILogger<CreateOrderHandler> logger)
    : IRequestHandler<CreateOrderCommand, Result<Guid>>
{
    public async Task<Result<Guid>> Handle(
        CreateOrderCommand request, CancellationToken ct)
    {
        var order = Order.Create(request.CustomerName);

        foreach (var item in request.Items)
            order.AddItem(item.ProductId, item.Quantity, item.Price);

        orderRepository.Add(order);
        await unitOfWork.SaveChangesAsync(ct);

        logger.LogInformation("Order {OrderId} created", order.Id);
        return Result<Guid>.Success(order.Id);
    }
}
```

## Anti-Patterns

- Repository per entity instead of per aggregate root
- Exposing `IQueryable<T>` from repository (leaky abstraction)
- Generic repository that covers all data access needs (too generic)
- Saving within repository methods (UoW should coordinate saves)
- Returning DTOs from repositories (return domain entities)

## Detect Existing Patterns

1. Search for `IRepository<` interface definitions
2. Look for `IUnitOfWork` interface
3. Check for `Repositories/` folder in Infrastructure project
4. Look for `Ardalis.Specification` package reference
5. Search for `Specifications/` folder

## Adding to Existing Project

1. **Define interfaces** in Domain/Application: `IRepository<T>`, `IUnitOfWork`
2. **Create generic implementation** in Infrastructure using EF Core
3. **Add specialized repositories** for aggregate-specific queries
4. **Register with DI** using open generics for the generic repository
5. **Consider specifications** for complex, reusable query criteria
6. **Refactor handlers** to use repository + UoW instead of raw DbContext

## Decision Guide

| Scenario | Approach |
|----------|----------|
| Simple CRUD | Generic `IRepository<T>` |
| Complex aggregate queries | Specialized repository interface |
| Reusable query criteria | Specification pattern |
| Read-only queries | `IReadRepository<T>` or direct DbContext |
| VSA style | Skip repository, use DbContext directly |

## References

- https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/infrastructure-persistence-layer-design
- https://specification.ardalis.com/
