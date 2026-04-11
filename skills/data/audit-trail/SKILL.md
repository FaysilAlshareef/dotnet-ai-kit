---
name: audit-trail
description: >
  Use when adding automatic audit trail (CreatedAt, UpdatedBy) via EF Core interceptors.
metadata:
  category: data
  agent: ef-specialist
  when-to-use: "When implementing audit trail with IAuditable interface or EF Core interceptor"
---

# Audit Trail

## IAuditable Interface

```csharp
namespace {Company}.{Domain}.Domain.Interfaces;

public interface IAuditable
{
    DateTime CreatedAt { get; set; }
    DateTime? UpdatedAt { get; set; }
    string? CreatedBy { get; set; }
    string? UpdatedBy { get; set; }
}
```

## Entity Implementation

```csharp
namespace {Company}.{Domain}.Domain.Entities;

public class Order : IAuditable
{
    public Guid Id { get; private set; }
    public string CustomerName { get; private set; } = default!;
    public decimal Total { get; private set; }

    // IAuditable
    public DateTime CreatedAt { get; set; }
    public DateTime? UpdatedAt { get; set; }
    public string? CreatedBy { get; set; }
    public string? UpdatedBy { get; set; }
}
```

## SaveChanges Interceptor

```csharp
namespace {Company}.{Domain}.Infrastructure.Interceptors;

public sealed class AuditableEntityInterceptor(
    IHttpContextAccessor httpContextAccessor,
    TimeProvider timeProvider)
    : SaveChangesInterceptor
{
    public override ValueTask<InterceptionResult<int>> SavingChangesAsync(
        DbContextEventData eventData,
        InterceptionResult<int> result,
        CancellationToken ct = default)
    {
        if (eventData.Context is null) return base.SavingChangesAsync(eventData, result, ct);

        var now = timeProvider.GetUtcNow().UtcDateTime;
        var userId = httpContextAccessor.HttpContext?.User
            .FindFirstValue(ClaimTypes.NameIdentifier);

        foreach (var entry in eventData.Context.ChangeTracker
            .Entries<IAuditable>())
        {
            switch (entry.State)
            {
                case EntityState.Added:
                    entry.Entity.CreatedAt = now;
                    entry.Entity.CreatedBy = userId;
                    break;

                case EntityState.Modified:
                    entry.Entity.UpdatedAt = now;
                    entry.Entity.UpdatedBy = userId;
                    break;
            }
        }

        return base.SavingChangesAsync(eventData, result, ct);
    }
}
```

## Soft Delete

```csharp
public interface ISoftDeletable
{
    bool IsDeleted { get; set; }
    DateTime? DeletedAt { get; set; }
    string? DeletedBy { get; set; }
}

// In interceptor, handle EntityState.Deleted:
case EntityState.Deleted when entry.Entity is ISoftDeletable softDeletable:
    entry.State = EntityState.Modified;
    softDeletable.IsDeleted = true;
    softDeletable.DeletedAt = now;
    softDeletable.DeletedBy = userId;
    break;
```

## Global Query Filter for Soft Delete

```csharp
// In DbContext.OnModelCreating
modelBuilder.Entity<Order>().HasQueryFilter(o => !o.IsDeleted);
```

## Registration

```csharp
services.AddDbContext<ApplicationDbContext>((provider, options) =>
{
    options.UseSqlServer(connectionString)
           .AddInterceptors(provider.GetRequiredService<AuditableEntityInterceptor>());
});

services.AddScoped<AuditableEntityInterceptor>();
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Setting audit fields manually in handlers | Use interceptor |
| Using `DateTime.UtcNow` directly | Inject `TimeProvider` |
| Hard-deleting audited entities | Use soft delete |
| Audit fields with `public set` on domain entities | Acceptable — IAuditable needs setters for interceptor |

## Detect Existing Patterns

```bash
grep -r "IAuditable\|CreatedAt\|UpdatedAt" --include="*.cs"
grep -r "SaveChangesInterceptor\|SavingChangesAsync" --include="*.cs"
```

## Adding to Existing Project

1. Create `IAuditable` interface in Domain
2. Implement on entities that need auditing
3. Create interceptor in Infrastructure
4. Register interceptor in DbContext setup
