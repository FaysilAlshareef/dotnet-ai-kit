---
name: multi-tenancy
description: >
  Multi-tenant architecture patterns — tenant isolation strategies, per-tenant database,
  schema separation, shared with discriminator, tenant resolution, and EF Core global query filters.
  Trigger: multi-tenant, tenant, tenancy, tenant isolation, shared database, tenant resolution.
metadata:
  category: architecture
  agent: dotnet-architect
  when-to-use: "When implementing multi-tenant architecture, tenant isolation, or tenant resolution"
---

# Multi-Tenancy

## Core Principles

- Tenant isolation is non-negotiable — one tenant must never see another tenant's data
- Data safety must be enforced at the infrastructure level, not just application logic
- Performance isolation prevents one tenant's workload from degrading others
- Tenant context must be resolved early in the pipeline and available everywhere via DI
- Every database query must be tenant-scoped — defense in depth with global query filters
- Onboarding and offboarding tenants should be automated, not manual SQL scripts

## When to Use

- SaaS applications serving multiple organizations from a single deployment
- B2B platforms where each customer requires logical or physical data separation
- White-label products where each tenant has custom branding or configuration

## When NOT to Use

- Single-customer deployments or internal tools for one organization
- Prototypes or MVPs where multi-tenancy adds premature complexity
- Systems where regulatory requirements mandate fully separate deployments (not tenants)

## Patterns

### Tenant Resolution Middleware

Resolve the tenant early in the pipeline. Support multiple strategies.
```csharp
// Abstractions/ITenantProvider.cs
public interface ITenantProvider
{
    Guid TenantId { get; }
    string TenantName { get; }
}

// Abstractions/ITenantEntity.cs
public interface ITenantEntity
{
    Guid TenantId { get; }
}

// Infrastructure/TenantProvider.cs
internal sealed class TenantProvider : ITenantProvider
{
    public Guid TenantId { get; set; }
    public string TenantName { get; set; } = default!;
}
```

```csharp
// Infrastructure/Middleware/TenantResolutionMiddleware.cs
internal sealed class TenantResolutionMiddleware(
    RequestDelegate next,
    ITenantStore tenantStore,
    ILogger<TenantResolutionMiddleware> logger)
{
    public async Task InvokeAsync(HttpContext context)
    {
        var tenantId = ResolveTenantId(context);
        if (tenantId is null)
        {
            context.Response.StatusCode = StatusCodes.Status400BadRequest;
            await context.Response.WriteAsJsonAsync(
                new { error = "Tenant could not be resolved" });
            return;
        }

        var tenant = await tenantStore.GetByIdAsync(tenantId.Value);
        if (tenant is null)
        {
            context.Response.StatusCode = StatusCodes.Status404NotFound;
            await context.Response.WriteAsJsonAsync(
                new { error = "Tenant not found" });
            return;
        }

        var provider = context.RequestServices
            .GetRequiredService<TenantProvider>();
        provider.TenantId = tenant.Id;
        provider.TenantName = tenant.Name;

        logger.LogDebug("Resolved tenant {TenantId} ({TenantName})",
            tenant.Id, tenant.Name);

        await next(context);
    }

    private static Guid? ResolveTenantId(HttpContext context)
    {
        // Strategy 1: JWT claim
        var claim = context.User.FindFirst("tenant_id");
        if (claim is not null && Guid.TryParse(claim.Value, out var fromClaim))
            return fromClaim;

        // Strategy 2: Custom header
        if (context.Request.Headers.TryGetValue("X-Tenant-Id", out var header)
            && Guid.TryParse(header, out var fromHeader))
            return fromHeader;

        // Strategy 3: Subdomain (e.g., acme.app.com)
        var host = context.Request.Host.Host;
        var subdomain = host.Split('.')[0];
        if (Guid.TryParse(subdomain, out var fromSubdomain))
            return fromSubdomain;

        // Strategy 4: Route or query parameter
        if (context.Request.Query.TryGetValue("tenantId", out var qs)
            && Guid.TryParse(qs, out var fromQuery))
            return fromQuery;

        return null;
    }
}
```

### Tenant Store

```csharp
// Abstractions/ITenantStore.cs
public interface ITenantStore
{
    Task<TenantInfo?> GetByIdAsync(Guid tenantId, CancellationToken ct = default);
    Task<TenantInfo?> GetByHostAsync(string hostname, CancellationToken ct = default);
}

// Domain/TenantInfo.cs
public sealed class TenantInfo
{
    public Guid Id { get; init; }
    public string Name { get; init; } = default!;
    public string? ConnectionString { get; init; }
    public string? SchemaName { get; init; }
    public bool IsActive { get; init; } = true;
}
```

### Pattern 1 — Database-per-Tenant (Strongest Isolation)

```csharp
// Infrastructure/Persistence/TenantDbContextFactory.cs
internal sealed class TenantDbContextFactory(
    ITenantProvider tenantProvider,
    ITenantStore tenantStore) : IDbContextFactory<AppDbContext>
{
    public async Task<AppDbContext> CreateDbContextAsync(
        CancellationToken ct = default)
    {
        var tenant = await tenantStore.GetByIdAsync(
            tenantProvider.TenantId, ct)
            ?? throw new InvalidOperationException("Tenant not found");

        var options = new DbContextOptionsBuilder<AppDbContext>()
            .UseSqlServer(tenant.ConnectionString)
            .Options;

        return new AppDbContext(options, tenantProvider);
    }

    // Synchronous overload required by IDbContextFactory
    public AppDbContext CreateDbContext()
        => CreateDbContextAsync().GetAwaiter().GetResult();
}
```

### Pattern 2 — Schema-per-Tenant (Moderate Isolation)

```csharp
// Infrastructure/Persistence/SchemaPerTenantDbContext.cs
internal sealed class SchemaPerTenantDbContext(
    DbContextOptions<SchemaPerTenantDbContext> options,
    ITenantProvider tenantProvider,
    ITenantStore tenantStore) : DbContext(options)
{
    public DbSet<Order> Orders => Set<Order>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        var tenant = tenantStore.GetByIdAsync(tenantProvider.TenantId)
            .GetAwaiter().GetResult();

        var schema = tenant?.SchemaName ?? "dbo";
        modelBuilder.HasDefaultSchema(schema);
        modelBuilder.ApplyConfigurationsFromAssembly(
            typeof(SchemaPerTenantDbContext).Assembly);
    }
}
```

### Pattern 3 — Shared Database with Discriminator (Simplest)

```csharp
// Infrastructure/Persistence/AppDbContext.cs
internal sealed class AppDbContext(
    DbContextOptions<AppDbContext> options,
    ITenantProvider tenantProvider) : DbContext(options)
{
    public DbSet<Order> Orders => Set<Order>();
    public DbSet<Product> Products => Set<Product>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(
            typeof(AppDbContext).Assembly);

        // Global query filter — every query is automatically tenant-scoped
        modelBuilder.Entity<Order>()
            .HasQueryFilter(e => e.TenantId == tenantProvider.TenantId);

        modelBuilder.Entity<Product>()
            .HasQueryFilter(e => e.TenantId == tenantProvider.TenantId);
    }

    public override Task<int> SaveChangesAsync(
        CancellationToken cancellationToken = default)
    {
        // Stamp TenantId on new entities automatically
        foreach (var entry in ChangeTracker.Entries<ITenantEntity>()
            .Where(e => e.State == EntityState.Added))
        {
            entry.Entity.GetType()
                .GetProperty(nameof(ITenantEntity.TenantId))!
                .SetValue(entry.Entity, tenantProvider.TenantId);
        }

        return base.SaveChangesAsync(cancellationToken);
    }
}
```

### Applying Global Query Filters Generically

```csharp
// Infrastructure/Persistence/Extensions/ModelBuilderExtensions.cs
internal static class ModelBuilderExtensions
{
    public static void ApplyTenantQueryFilters(
        this ModelBuilder modelBuilder, ITenantProvider tenantProvider)
    {
        foreach (var entityType in modelBuilder.Model.GetEntityTypes())
        {
            if (!typeof(ITenantEntity).IsAssignableFrom(entityType.ClrType))
                continue;

            var parameter = Expression.Parameter(entityType.ClrType, "e");
            var tenantIdProp = Expression.Property(parameter,
                nameof(ITenantEntity.TenantId));
            var tenantIdValue = Expression.Property(
                Expression.Constant(tenantProvider),
                nameof(ITenantProvider.TenantId));
            var filter = Expression.Lambda(
                Expression.Equal(tenantIdProp, tenantIdValue), parameter);

            entityType.SetQueryFilter(filter);
        }
    }
}
```

### Tenant-Aware DI Registration

```csharp
// Infrastructure/DependencyInjection.cs
public static class DependencyInjection
{
    public static IServiceCollection AddMultiTenancy(
        this IServiceCollection services, IConfiguration configuration)
    {
        // Tenant provider — scoped so it lives for the request
        services.AddScoped<TenantProvider>();
        services.AddScoped<ITenantProvider>(sp =>
            sp.GetRequiredService<TenantProvider>());

        // Tenant store — singleton with caching
        services.AddSingleton<ITenantStore, CachedTenantStore>();

        // DbContext — scoped, receives tenant from provider
        services.AddDbContext<AppDbContext>((sp, options) =>
        {
            var tenantProvider = sp.GetRequiredService<ITenantProvider>();
            var tenantStore = sp.GetRequiredService<ITenantStore>();
            var tenant = tenantStore.GetByIdAsync(tenantProvider.TenantId)
                .GetAwaiter().GetResult();

            if (tenant?.ConnectionString is not null)
            {
                // Database-per-tenant
                options.UseSqlServer(tenant.ConnectionString);
            }
            else
            {
                // Shared database fallback
                options.UseSqlServer(
                    configuration.GetConnectionString("Default"));
            }
        });

        return services;
    }
}

// Program.cs
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddMultiTenancy(builder.Configuration);

var app = builder.Build();

app.UseMiddleware<TenantResolutionMiddleware>();
app.MapEndpointGroups();
app.Run();
```

### Connection String per Tenant with Options Pattern

```csharp
// Infrastructure/TenantConnectionFactory.cs
internal sealed class TenantConnectionFactory(
    ITenantProvider tenantProvider,
    ITenantStore tenantStore,
    IConfiguration configuration)
{
    public async Task<string> GetConnectionStringAsync(
        CancellationToken ct = default)
    {
        var tenant = await tenantStore.GetByIdAsync(
            tenantProvider.TenantId, ct);

        return tenant?.ConnectionString
            ?? configuration.GetConnectionString("Default")
            ?? throw new InvalidOperationException(
                "No connection string configured");
    }
}
```

## Decision Guide

| Criterion | Database-per-Tenant | Schema-per-Tenant | Shared + Discriminator |
|-----------|--------------------|--------------------|------------------------|
| Data isolation | Strongest — separate databases | Moderate — separate schemas | Weakest — row-level |
| Cost | Highest — one DB per tenant | Moderate — one DB, N schemas | Lowest — one DB, one schema |
| Complexity | High — connection management, migrations per tenant | Moderate — schema management | Low — query filters only |
| Compliance | Best for regulated industries (HIPAA, SOC 2) | Acceptable for most | Depends on auditor |
| Cross-tenant queries | Hard — requires federation | Moderate — schema prefix | Easy — remove filter |
| Tenant onboarding | Slow — provision database | Moderate — create schema + migrate | Fast — insert row |
| Backup/restore per tenant | Easy — backup one database | Moderate — schema export | Hard — extract rows |
| Performance isolation | Full — no resource contention | Partial — shared I/O | None — shared everything |
| Max tenants | Hundreds | Thousands | Unlimited |

## Anti-Patterns

| Anti-Pattern | Risk | Fix |
|-------------|------|-----|
| No global query filter | Data leak — tenant sees other tenant's data | Apply `HasQueryFilter` on every `ITenantEntity` |
| Hardcoded tenant ID | Testing/debugging shortcut becomes production bug | Always resolve from `ITenantProvider` |
| Missing tenant context in background jobs | Jobs run without HTTP context, tenant is null | Pass `TenantId` explicitly to job payload and restore provider |
| `IgnoreQueryFilters()` without re-adding tenant filter | Bypasses all filters including tenant scoping | Add explicit `.Where(e => e.TenantId == tenantId)` when using `IgnoreQueryFilters()` |
| Tenant resolution after authentication middleware | Auth may fail because tenant DB is not yet known | Place tenant resolution before auth when tenant drives connection |
| Caching without tenant key | Shared cache returns wrong tenant's data | Always include `TenantId` in cache keys |
| Seeding shared lookup data with tenant ID | Reference data duplicated per tenant | Use a separate unfiltered `DbSet` for shared lookups |
| Connection string in logs | Credentials exposed in structured logs | Sanitize or exclude connection strings from log output |

## Detect Existing Patterns

1. Search for `TenantId` property on entities or a base class
2. Look for `HasQueryFilter` calls in `OnModelCreating`
3. Check for middleware resolving tenant from headers, claims, or subdomain
4. Look for `ITenantProvider`, `ITenantAccessor`, or `ITenantContext` interfaces
5. Check if `IDbContextFactory` is used for per-tenant connection management
6. Search for `X-Tenant-Id` header usage in middleware or delegating handlers

## Adding to Existing Project

1. **Define `ITenantEntity`** interface with `Guid TenantId` and add it to all tenant-scoped entities
2. **Create `ITenantProvider`** and `TenantProvider` — register as scoped
3. **Add tenant resolution middleware** — place before auth if tenant drives DB selection
4. **Apply global query filters** in `OnModelCreating` for every `ITenantEntity`
5. **Override `SaveChangesAsync`** to auto-stamp `TenantId` on new entities
6. **Add `TenantId` column** migration to all existing tenant-scoped tables
7. **Backfill `TenantId`** for existing rows — use a default tenant for migration
8. **Audit cache keys** — prefix or include `TenantId` in every cache entry
9. **Update background jobs** — pass `TenantId` in job payload, restore context before execution
10. **Add integration tests** verifying tenant A cannot read tenant B's data

## References

- https://learn.microsoft.com/en-us/ef/core/miscellaneous/multitenancy
