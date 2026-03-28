---
name: specification-pattern
description: >
  Specification pattern for composable query criteria. ISpecification interface,
  BaseSpecification with expression trees, repository integration.
metadata:
  category: data
  agent: ef-specialist
---

# Specification Pattern

## ISpecification Interface

```csharp
namespace {Company}.{Domain}.Domain.Interfaces;

public interface ISpecification<T>
{
    Expression<Func<T, bool>>? Criteria { get; }
    List<Expression<Func<T, object>>> Includes { get; }
    List<string> IncludeStrings { get; }
    Expression<Func<T, object>>? OrderBy { get; }
    Expression<Func<T, object>>? OrderByDescending { get; }
    int? Take { get; }
    int? Skip { get; }
    bool IsPagingEnabled { get; }
}
```

## Base Specification

```csharp
namespace {Company}.{Domain}.Domain.Specifications;

public abstract class BaseSpecification<T> : ISpecification<T>
{
    public Expression<Func<T, bool>>? Criteria { get; private set; }
    public List<Expression<Func<T, object>>> Includes { get; } = [];
    public List<string> IncludeStrings { get; } = [];
    public Expression<Func<T, object>>? OrderBy { get; private set; }
    public Expression<Func<T, object>>? OrderByDescending { get; private set; }
    public int? Take { get; private set; }
    public int? Skip { get; private set; }
    public bool IsPagingEnabled { get; private set; }

    protected BaseSpecification() { }

    protected BaseSpecification(Expression<Func<T, bool>> criteria)
        => Criteria = criteria;

    protected void AddInclude(Expression<Func<T, object>> include)
        => Includes.Add(include);

    protected void AddInclude(string include)
        => IncludeStrings.Add(include);

    protected void ApplyOrderBy(Expression<Func<T, object>> orderBy)
        => OrderBy = orderBy;

    protected void ApplyOrderByDescending(Expression<Func<T, object>> orderByDesc)
        => OrderByDescending = orderByDesc;

    protected void ApplyPaging(int skip, int take)
    {
        Skip = skip;
        Take = take;
        IsPagingEnabled = true;
    }
}
```

## Concrete Specification

```csharp
public sealed class ActiveOrdersByCustomerSpec : BaseSpecification<Order>
{
    public ActiveOrdersByCustomerSpec(Guid customerId, int page, int pageSize)
        : base(o => o.CustomerId == customerId && o.Status != OrderStatus.Cancelled)
    {
        AddInclude(o => o.Items);
        ApplyOrderByDescending(o => o.CreatedAt);
        ApplyPaging((page - 1) * pageSize, pageSize);
    }
}
```

## Repository Integration

```csharp
public interface IRepository<T> where T : class
{
    Task<T?> GetBySpecAsync(ISpecification<T> spec, CancellationToken ct = default);
    Task<List<T>> ListAsync(ISpecification<T> spec, CancellationToken ct = default);
    Task<int> CountAsync(ISpecification<T> spec, CancellationToken ct = default);
}

public sealed class Repository<T>(ApplicationDbContext context)
    : IRepository<T> where T : class
{
    public async Task<List<T>> ListAsync(
        ISpecification<T> spec, CancellationToken ct = default)
    {
        return await ApplySpecification(spec).ToListAsync(ct);
    }

    public async Task<int> CountAsync(
        ISpecification<T> spec, CancellationToken ct = default)
    {
        return await ApplySpecification(spec).CountAsync(ct);
    }

    private IQueryable<T> ApplySpecification(ISpecification<T> spec)
    {
        return SpecificationEvaluator<T>.GetQuery(
            context.Set<T>().AsQueryable(), spec);
    }
}
```

## Specification Evaluator

```csharp
public static class SpecificationEvaluator<T> where T : class
{
    public static IQueryable<T> GetQuery(
        IQueryable<T> query, ISpecification<T> spec)
    {
        if (spec.Criteria is not null)
            query = query.Where(spec.Criteria);

        query = spec.Includes.Aggregate(query,
            (current, include) => current.Include(include));

        query = spec.IncludeStrings.Aggregate(query,
            (current, include) => current.Include(include));

        if (spec.OrderBy is not null)
            query = query.OrderBy(spec.OrderBy);
        else if (spec.OrderByDescending is not null)
            query = query.OrderByDescending(spec.OrderByDescending);

        if (spec.IsPagingEnabled)
            query = query.Skip(spec.Skip!.Value).Take(spec.Take!.Value);

        return query;
    }
}
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Complex Where clauses in repositories | Encapsulate in specification |
| Duplicating query logic | Reuse specifications |
| Specifications with side effects | Keep specifications pure (queries only) |

## Detect Existing Patterns

```bash
grep -r "ISpecification\|BaseSpecification" --include="*.cs"
grep -r "SpecificationEvaluator" --include="*.cs"
```

## Adding to Existing Project

1. Create `ISpecification<T>` interface in Domain layer
2. Create `BaseSpecification<T>` in Domain
3. Create `SpecificationEvaluator<T>` in Infrastructure
4. Add spec parameter to repository methods
