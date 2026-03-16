---
name: query-handler
description: >
  MediatR query handlers using IUnitOfWork with named repository properties. Repositories
  encapsulate filtering, pagination, and sorting. Single-entity queries use FindAsync
  with DTO mapping. List queries delegate to repository methods returning output DTOs.
  Trigger: query handler, pagination, filtering, read operations.
category: microservice/query
agent: query-architect
---

# Query Handler — IUnitOfWork with Repository Queries

## Core Principles

- Query handlers implement `IRequestHandler<TQuery, TOutput>` via MediatR
- Use **IUnitOfWork** with named repository properties (e.g., `_unitOfWork.Orders`)
- **Repository methods** encapsulate filtering, pagination, and sorting logic
- List queries use record types with pagination and filter parameters
- Output classes have `PageSize`, `CurrentPage`, `Total`, and collection properties
- Single-entity queries use `FindAsync` then map to output DTO
- Not-found cases throw domain-specific exceptions (e.g., `OrderNotFoundException`)
- Primary constructor pattern with field assignment

## Key Patterns

### IUnitOfWork with Named Repositories

```csharp
namespace {Company}.{Domain}.Query.Application.Contracts.Repositories;

public interface IUnitOfWork : IDisposable
{
    IOrderRepository Orders { get; }
    IProductRepository Products { get; }
    IOrderItemRepository OrderItems { get; }
    ICategoryRepository Categories { get; }
    Task SaveChangesAsync();
}
```

### Generic Repository Base

```csharp
namespace {Company}.{Domain}.Query.Application.Contracts.Repositories;

public interface IAsyncRepository<TDomain> where TDomain : class
{
    Task AddAsync(TDomain entity);
    Task AddRangeAsync(IEnumerable<TDomain> entities);
    Task RemoveAsync(TDomain entity);
    Task RemoveRangeAsync(IEnumerable<TDomain> entities);
    Task<TDomain?> FindAsync(Guid id, bool includeRelated = false);
    Task<IEnumerable<TDomain>> GetAllAsync();
    Task<IEnumerable<TResult>> GetAllAsync<TResult>(
        Expression<Func<TDomain, TResult>> target);
    IQueryable<TDomain> GetQueryable();
}
```

### Specific Repository with Query Methods

```csharp
namespace {Company}.{Domain}.Query.Application.Contracts.Repositories;

public interface IOrderRepository : IAsyncRepository<Order>
{
    Task<GetOrdersOutput> GetOrdersAsync(
        GetOrdersQuery query,
        CancellationToken cancellationToken);
}
```

### List Query — Record with Pagination and Filters

```csharp
namespace {Company}.{Domain}.Query.Application.Features.Queries;

public record GetOrdersQuery(
    int PageSize,
    int CurrentPage,
    DateTime? CreatedFrom,
    DateTime? CreatedTo,
    OrderStatus? Status,
    string? CustomerName
) : IRequest<GetOrdersOutput>;
```

### List Output — PageSize, CurrentPage, Total, Collection

```csharp
namespace {Company}.{Domain}.Query.Application.Features.Queries;

public class GetOrdersOutput
{
    public int PageSize { get; set; }
    public int CurrentPage { get; set; }
    public int Total { get; set; }
    public List<OrderOutput> Orders { get; set; } = [];
}
```

### Output DTO — Plain Class with Public Setters

```csharp
namespace {Company}.{Domain}.Query.Application.Features.Queries;

public class OrderOutput
{
    public Guid Id { get; set; }
    public string CustomerName { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public decimal Total { get; set; }
    public OrderStatus Status { get; set; }
    public bool IsActive { get; set; }
    public DateTime CreatedAt { get; set; }
}
```

### List Query Handler — Delegates to Repository

```csharp
namespace {Company}.{Domain}.Query.Application.Features.Queries;

public class GetOrdersHandler(IUnitOfWork unitOfWork)
    : IRequestHandler<GetOrdersQuery, GetOrdersOutput>
{
    private readonly IUnitOfWork _unitOfWork = unitOfWork;

    public async Task<GetOrdersOutput> Handle(
        GetOrdersQuery query,
        CancellationToken cancellationToken)
    {
        return await _unitOfWork.Orders
            .GetOrdersAsync(query, cancellationToken);
    }
}
```

### Single-Entity Query Handler — FindAsync + Map

```csharp
namespace {Company}.{Domain}.Query.Application.Features.Queries;

public record GetOrderByIdQuery(Guid Id) : IRequest<OrderOutput>;

public class GetOrderByIdHandler(IUnitOfWork unitOfWork)
    : IRequestHandler<GetOrderByIdQuery, OrderOutput>
{
    private readonly IUnitOfWork _unitOfWork = unitOfWork;

    public async Task<OrderOutput> Handle(
        GetOrderByIdQuery query,
        CancellationToken cancellationToken)
    {
        var order = await _unitOfWork.Orders.FindAsync(query.Id)
            ?? throw new OrderNotFoundException();

        return new OrderOutput
        {
            Id = order.Id,
            CustomerName = order.CustomerName,
            Email = order.Email,
            Total = order.Total,
            Status = order.Status,
            IsActive = order.IsActive,
            CreatedAt = order.CreatedAt
        };
    }
}
```

### Query Handler with Additional Service

```csharp
public class GetOrderDetailsHandler(
    IUnitOfWork unitOfWork,
    IQueriesService queriesService)
    : IRequestHandler<GetOrderDetailsQuery, OrderDetailsOutput>
{
    private readonly IUnitOfWork _unitOfWork = unitOfWork;
    private readonly IQueriesService _queriesService = queriesService;

    public async Task<OrderDetailsOutput> Handle(
        GetOrderDetailsQuery query,
        CancellationToken cancellationToken)
    {
        var order = await _unitOfWork.Orders.FindAsync(query.Id, true)
            ?? throw new OrderNotFoundException();

        var extraInfo = await _queriesService
            .GetAdditionalInfo(order.ExternalId);

        return new OrderDetailsOutput { /* map fields */ };
    }
}
```

## Handler Architecture

| Query Type | Pattern | Returns |
|---|---|---|
| List with pagination | Delegate to repository method | `GetOrdersOutput` with Total, PageSize, CurrentPage |
| Single by ID | `FindAsync` + map to output | Output DTO or throw `NotFoundException` |
| Single by field | Repository-specific method | Output DTO or throw `NotFoundException` |
| With external data | Additional service injection | Combined output |

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| `ApplicationDbContext` injected directly | Use `IUnitOfWork` with named repositories |
| `Paginated<T>` generic wrapper | Output class with `PageSize`, `CurrentPage`, `Total`, collection |
| `AsNoTracking()` in handlers | Tracking handled at repository/infrastructure level |
| Filtering logic in handlers | Repository methods encapsulate all query logic |
| Returning entities from queries | Map to output DTOs in handler |
| `record` output types | `class` output types with `{ get; set; }` properties |

## Detect Existing Patterns

```bash
# Find query handlers
grep -r "IRequestHandler<.*Query" --include="*.cs" Application/Features/Queries/

# Find IUnitOfWork usage in queries
grep -r "_unitOfWork\." --include="*.cs" Application/Features/Queries/

# Find output classes
grep -r "public class.*Output" --include="*.cs" Application/Features/Queries/

# Find repository interfaces with query methods
grep -r "Task<Get.*Output>" --include="*.cs" Application/Contracts/
```

## Adding to Existing Project

1. **Use IUnitOfWork** with named repository properties, not DbContext
2. **List queries** delegate to repository methods that return typed output
3. **Single queries** use `FindAsync` then map to output DTO in handler
4. **Output classes** use `class` with `PageSize`, `CurrentPage`, `Total`, and collection
5. **Query records** use `record` type with filter parameters as nullable
6. **Place in** `Application/Features/Queries/{Area}/{QueryName}/` directory
7. **One folder per query** containing Query, Handler, Output, and any DTOs
