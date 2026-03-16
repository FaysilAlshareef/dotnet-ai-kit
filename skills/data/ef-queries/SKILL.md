---
name: ef-queries
description: >
  EF Core query patterns. LINQ queries, raw SQL, compiled queries,
  projection with Select, split queries, and performance optimization.
  Trigger: EF query, LINQ, raw SQL, compiled query, projection, N+1.
category: data
agent: ef-specialist
---

# EF Core Query Patterns

## Core Principles

- Use `AsNoTracking()` for all read-only queries
- Project to DTOs with `Select()` at the database level — avoid loading full entities
- Use split queries to prevent cartesian explosion with multiple includes
- Compile hot-path queries for maximum performance
- Always paginate list queries — never return unbounded result sets

## Patterns

### Basic Queries with Projection

```csharp
// Project to DTO at database level — only selected columns are queried
var orders = await db.Orders
    .AsNoTracking()
    .Where(o => o.Status == OrderStatus.Submitted)
    .OrderByDescending(o => o.CreatedAt)
    .Select(o => new OrderSummaryResponse(
        o.Id,
        o.CustomerName,
        o.Total,
        o.CreatedAt))
    .ToListAsync(ct);
```

### Pagination

```csharp
internal sealed class ListOrdersHandler(AppDbContext db)
    : IRequestHandler<ListOrdersQuery, PagedList<OrderSummaryResponse>>
{
    public async Task<PagedList<OrderSummaryResponse>> Handle(
        ListOrdersQuery request, CancellationToken ct)
    {
        var query = db.Orders.AsNoTracking();

        // Dynamic filtering
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
                o.Id, o.CustomerName, o.Total, o.CreatedAt))
            .ToListAsync(ct);

        return new PagedList<OrderSummaryResponse>(
            items, totalCount, request.Page, request.PageSize);
    }
}
```

### Split Queries for N+1 Prevention

```csharp
// BAD — cartesian explosion with multiple Includes
var order = await db.Orders
    .Include(o => o.Items)
    .Include(o => o.Payments)
    .FirstOrDefaultAsync(o => o.Id == id, ct);

// GOOD — split into separate queries
var order = await db.Orders
    .Include(o => o.Items)
    .Include(o => o.Payments)
    .AsSplitQuery()
    .FirstOrDefaultAsync(o => o.Id == id, ct);

// Configure globally
options.UseSqlServer(connectionString, sql =>
{
    sql.UseQuerySplittingBehavior(
        QuerySplittingBehavior.SplitQuery);
});
```

### Compiled Queries for Hot Paths

```csharp
public sealed class OrderQueries
{
    // Compiled query — parsed once, reused on every call
    public static readonly Func<AppDbContext, Guid, CancellationToken,
        Task<Order?>> GetById =
        EF.CompileAsyncQuery((AppDbContext db, Guid id,
            CancellationToken ct) =>
            db.Orders
                .Include(o => o.Items)
                .FirstOrDefault(o => o.Id == id));

    public static readonly Func<AppDbContext, OrderStatus,
        CancellationToken, IAsyncEnumerable<Order>> GetByStatus =
        EF.CompileAsyncQuery((AppDbContext db, OrderStatus status,
            CancellationToken ct) =>
            db.Orders
                .AsNoTracking()
                .Where(o => o.Status == status)
                .OrderByDescending(o => o.CreatedAt));
}

// Usage
var order = await OrderQueries.GetById(db, orderId, ct);
```

### Raw SQL Queries

```csharp
// Unmapped types with raw SQL (.NET 8+)
var summaries = await db.Database
    .SqlQuery<OrderSummaryDto>(
        $"""
        SELECT o.Id, o.CustomerName, o.Total,
               COUNT(i.Id) AS ItemCount
        FROM Orders o
        LEFT JOIN OrderItems i ON o.Id = i.OrderId
        WHERE o.Status = {status}
        GROUP BY o.Id, o.CustomerName, o.Total
        ORDER BY o.Total DESC
        """)
    .ToListAsync(ct);

// Parameterized — EF Core handles SQL injection protection
var orders = await db.Orders
    .FromSqlInterpolated(
        $"SELECT * FROM Orders WHERE CustomerName LIKE {pattern}")
    .ToListAsync(ct);
```

### Global Query Filters

```csharp
// Entity configuration — automatically applied to all queries
builder.HasQueryFilter(o => !o.IsDeleted);

// Bypass filter when needed
var allOrders = await db.Orders
    .IgnoreQueryFilters()
    .ToListAsync(ct);
```

### Efficient Existence and Count Checks

```csharp
// Check existence — stops at first match
var exists = await db.Orders
    .AnyAsync(o => o.Id == orderId, ct);

// Count with filter
var count = await db.Orders
    .CountAsync(o => o.Status == OrderStatus.Pending, ct);

// BAD — loads all entities just to count
var count = (await db.Orders.ToListAsync(ct)).Count;
```

### Batch Operations (.NET 7+)

```csharp
// Batch update — no entity loading
await db.Orders
    .Where(o => o.Status == OrderStatus.Draft
             && o.CreatedAt < cutoffDate)
    .ExecuteUpdateAsync(setters => setters
        .SetProperty(o => o.Status, OrderStatus.Cancelled)
        .SetProperty(o => o.UpdatedAt, DateTimeOffset.UtcNow), ct);

// Batch delete
await db.Orders
    .Where(o => o.IsDeleted && o.DeletedAt < archiveDate)
    .ExecuteDeleteAsync(ct);
```

## Anti-Patterns

- Loading full entities for read-only display (use `Select` projection)
- Missing `AsNoTracking()` on queries that don't need change tracking
- Using `ToList()` before `Where()` (evaluates entire table in memory)
- Multiple round-trips when a single query would suffice
- Not paginating list queries

## Detect Existing Patterns

1. Check for `AsNoTracking()` usage in query handlers
2. Look for `Select()` projections vs full entity loading
3. Search for `AsSplitQuery()` usage
4. Check for `EF.CompileAsyncQuery` compiled queries
5. Look for `ExecuteUpdateAsync` / `ExecuteDeleteAsync` batch operations

## Adding to Existing Project

1. **Add `AsNoTracking()`** to all read-only queries
2. **Replace full entity loads** with `Select()` projections in query handlers
3. **Add `AsSplitQuery()`** to queries with multiple Includes
4. **Compile hot-path queries** using `EF.CompileAsyncQuery`
5. **Replace load-and-update loops** with `ExecuteUpdateAsync` batch operations
6. **Add global query filters** for soft delete

## Decision Guide

| Scenario | Approach |
|----------|----------|
| Simple read | `AsNoTracking()` + `Select()` projection |
| Hot path | Compiled query |
| Multiple includes | `AsSplitQuery()` |
| Complex aggregation | Raw SQL with `SqlQuery<T>` |
| Bulk update | `ExecuteUpdateAsync` |
| Bulk delete | `ExecuteDeleteAsync` |

## References

- https://learn.microsoft.com/en-us/ef/core/querying/
- https://learn.microsoft.com/en-us/ef/core/performance/efficient-querying
