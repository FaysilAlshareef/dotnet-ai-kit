---
name: dotnet-ai-dapper-queries
description: >
  Dapper for read-optimized queries alongside EF Core. Multi-mapping,
  pagination, dynamic filtering, CTEs, bulk operations.
category: data
agent: ef-specialist
---

# Dapper Queries

## When to Use Dapper vs EF Core

| Scenario | Use |
|----------|-----|
| Complex read queries with joins | Dapper |
| Reporting and aggregation | Dapper |
| Bulk insert/update | Dapper |
| CRUD operations | EF Core |
| Change tracking | EF Core |
| Migrations | EF Core |

## Basic Query

```csharp
namespace {Company}.{Domain}.Infrastructure.Queries;

public sealed class OrderQueryService(IDbConnectionFactory connectionFactory)
{
    public async Task<OrderDetailDto?> GetByIdAsync(Guid id, CancellationToken ct)
    {
        using var connection = connectionFactory.Create();
        const string sql = """
            SELECT o.Id, o.CustomerName, o.Total, o.Status, o.CreatedAt
            FROM Orders o
            WHERE o.Id = @Id
            """;
        return await connection.QuerySingleOrDefaultAsync<OrderDetailDto>(
            new CommandDefinition(sql, new { Id = id }, cancellationToken: ct));
    }
}
```

## Multi-Mapping (Joins)

```csharp
public async Task<IEnumerable<OrderWithItemsDto>> GetOrdersWithItemsAsync(
    CancellationToken ct)
{
    using var connection = connectionFactory.Create();
    const string sql = """
        SELECT o.Id, o.CustomerName, o.Total,
               i.Id AS ItemId, i.ProductName, i.Quantity, i.UnitPrice
        FROM Orders o
        LEFT JOIN OrderItems i ON i.OrderId = o.Id
        ORDER BY o.CreatedAt DESC
        """;

    var lookup = new Dictionary<Guid, OrderWithItemsDto>();

    await connection.QueryAsync<OrderWithItemsDto, OrderItemDto, OrderWithItemsDto>(
        new CommandDefinition(sql, cancellationToken: ct),
        (order, item) =>
        {
            if (!lookup.TryGetValue(order.Id, out var existing))
            {
                existing = order;
                existing.Items = [];
                lookup[order.Id] = existing;
            }
            if (item is not null)
                existing.Items.Add(item);
            return existing;
        },
        splitOn: "ItemId");

    return lookup.Values;
}
```

## Paginated Query with Dynamic Filtering

```csharp
public async Task<PaginatedResult<OrderSummaryDto>> GetPaginatedAsync(
    string? search, string? status, int page, int pageSize, CancellationToken ct)
{
    using var connection = connectionFactory.Create();

    var builder = new SqlBuilder();
    var countTemplate = builder.AddTemplate(
        "SELECT COUNT(*) FROM Orders o /**where**/");
    var selectTemplate = builder.AddTemplate("""
        SELECT o.Id, o.CustomerName, o.Total, o.Status, o.CreatedAt
        FROM Orders o /**where**/ /**orderby**/
        OFFSET @Offset ROWS FETCH NEXT @PageSize ROWS ONLY
        """);

    if (!string.IsNullOrEmpty(search))
        builder.Where("o.CustomerName LIKE @Search", new { Search = $"%{search}%" });

    if (!string.IsNullOrEmpty(status))
        builder.Where("o.Status = @Status", new { Status = status });

    builder.OrderBy("o.CreatedAt DESC");

    var total = await connection.ExecuteScalarAsync<int>(
        new CommandDefinition(countTemplate.RawSql, countTemplate.Parameters,
            cancellationToken: ct));

    var items = await connection.QueryAsync<OrderSummaryDto>(
        new CommandDefinition(selectTemplate.RawSql,
            new DynamicParameters(selectTemplate.Parameters)
            {
                { "Offset", (page - 1) * pageSize },
                { "PageSize", pageSize }
            }, cancellationToken: ct));

    return new PaginatedResult<OrderSummaryDto>(items.ToList(), total, page, pageSize);
}
```

## Connection Factory

```csharp
public interface IDbConnectionFactory
{
    IDbConnection Create();
}

public sealed class SqlConnectionFactory(IOptions<DatabaseOptions> options)
    : IDbConnectionFactory
{
    public IDbConnection Create() =>
        new SqlConnection(options.Value.ConnectionString);
}
```

## DI Registration

```csharp
services.AddSingleton<IDbConnectionFactory, SqlConnectionFactory>();
services.AddScoped<OrderQueryService>();
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| String concatenation for SQL | Use `SqlBuilder` or parameterized queries |
| Not disposing connections | `using var connection = ...` |
| Using Dapper for simple CRUD | Use EF Core for CRUD |
| Forgetting CancellationToken | Pass via `CommandDefinition` |

## Detect Existing Patterns

```bash
grep -r "Dapper\|SqlMapper\|QueryAsync\|SqlBuilder" --include="*.cs"
grep -r "IDbConnection\|SqlConnection" --include="*.cs"
```

## Adding to Existing Project

1. Add `Dapper` and `Dapper.SqlBuilder` NuGet packages
2. Create `IDbConnectionFactory` if not already present
3. Use alongside EF Core — Dapper for reads, EF Core for writes
