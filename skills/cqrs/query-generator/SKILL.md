---
name: query-generator
description: >
  Use when creating a new CQRS query with handler, response DTO, and pagination support.
metadata:
  category: cqrs
  agent: ef-specialist
  when-to-use: "When generating CQRS query records with handler and response DTO scaffolding"
---

# CQRS Query Generator

## Query Record

```csharp
namespace {Company}.{Domain}.Application.Features.Orders.Queries.GetAll;

public sealed record GetOrdersQuery(
    int Page = 1,
    int PageSize = 20,
    string? Search = null,
    string? Status = null,
    string? SortBy = "CreatedAt",
    bool SortDescending = true) : IRequest<Result<PaginatedList<OrderSummaryDto>>>;
```

## Response DTO

```csharp
namespace {Company}.{Domain}.Application.Features.Orders.Queries.GetAll;

public sealed record OrderSummaryDto(
    Guid Id,
    string CustomerName,
    decimal Total,
    string Status,
    DateTime CreatedAt);
```

## Paginated List

```csharp
namespace {Company}.{Domain}.Application.Common;

public sealed class PaginatedList<T>
{
    public List<T> Items { get; }
    public int TotalCount { get; }
    public int Page { get; }
    public int PageSize { get; }
    public int TotalPages => (int)Math.Ceiling(TotalCount / (double)PageSize);
    public bool HasPrevious => Page > 1;
    public bool HasNext => Page < TotalPages;

    public PaginatedList(List<T> items, int totalCount, int page, int pageSize)
    {
        Items = items;
        TotalCount = totalCount;
        Page = page;
        PageSize = pageSize;
    }
}
```

## Handler (EF Core Path)

```csharp
namespace {Company}.{Domain}.Application.Features.Orders.Queries.GetAll;

internal sealed class GetOrdersQueryHandler(
    IUnitOfWork unitOfWork)
    : IRequestHandler<GetOrdersQuery, Result<PaginatedList<OrderSummaryDto>>>
{
    public async Task<Result<PaginatedList<OrderSummaryDto>>> Handle(
        GetOrdersQuery request, CancellationToken cancellationToken)
    {
        var query = unitOfWork.Orders.GetQueryable();

        // Apply filters
        if (!string.IsNullOrEmpty(request.Search))
            query = query.Where(o =>
                o.CustomerName.Contains(request.Search));

        if (!string.IsNullOrEmpty(request.Status))
            query = query.Where(o => o.Status == request.Status);

        // Apply sorting
        query = request.SortBy switch
        {
            "CustomerName" => request.SortDescending
                ? query.OrderByDescending(o => o.CustomerName)
                : query.OrderBy(o => o.CustomerName),
            "Total" => request.SortDescending
                ? query.OrderByDescending(o => o.Total)
                : query.OrderBy(o => o.Total),
            _ => request.SortDescending
                ? query.OrderByDescending(o => o.CreatedAt)
                : query.OrderBy(o => o.CreatedAt)
        };

        var totalCount = await query.CountAsync(cancellationToken);

        var items = await query
            .Skip((request.Page - 1) * request.PageSize)
            .Take(request.PageSize)
            .Select(o => new OrderSummaryDto(
                o.Id, o.CustomerName, o.Total,
                o.Status, o.CreatedAt))
            .ToListAsync(cancellationToken);

        return Result<PaginatedList<OrderSummaryDto>>.Success(
            new PaginatedList<OrderSummaryDto>(
                items, totalCount, request.Page, request.PageSize));
    }
}
```

## Get By ID Query

```csharp
public sealed record GetOrderByIdQuery(Guid Id)
    : IRequest<Result<OrderDetailDto>>;

internal sealed class GetOrderByIdQueryHandler(
    IUnitOfWork unitOfWork)
    : IRequestHandler<GetOrderByIdQuery, Result<OrderDetailDto>>
{
    public async Task<Result<OrderDetailDto>> Handle(
        GetOrderByIdQuery request, CancellationToken cancellationToken)
    {
        var order = await unitOfWork.Orders
            .GetQueryable()
            .Include(o => o.Items)
            .Where(o => o.Id == request.Id)
            .Select(o => new OrderDetailDto(
                o.Id, o.CustomerName, o.Total, o.Status,
                o.CreatedAt,
                o.Items.Select(i => new OrderItemDto(
                    i.ProductName, i.Quantity, i.UnitPrice)).ToList()))
            .FirstOrDefaultAsync(cancellationToken);

        return order is not null
            ? Result<OrderDetailDto>.Success(order)
            : Result<OrderDetailDto>.Failure("Order not found");
    }
}
```

## File Structure

```
Application/Features/Orders/Queries/
├── GetAll/
│   ├── GetOrdersQuery.cs
│   ├── GetOrdersQueryHandler.cs
│   └── OrderSummaryDto.cs
└── GetById/
    ├── GetOrderByIdQuery.cs
    ├── GetOrderByIdQueryHandler.cs
    └── OrderDetailDto.cs
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Query modifying data | Queries are read-only |
| Returning domain entities | Project to DTOs with `Select` |
| Loading full entity graph | Use `Select` projection |
| No pagination on list queries | Always paginate |

## Detect Existing Patterns

```bash
grep -r "IRequest<.*PaginatedList\|IRequest<.*Paginated" --include="*.cs"
grep -r "IRequestHandler.*Query" --include="*.cs"
```

## Adding to Existing Project

1. Follow existing query/handler structure
2. Use same pagination model as project
3. Project to DTOs — never return domain entities
