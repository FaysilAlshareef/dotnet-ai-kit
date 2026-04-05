---
name: ef-core-basics
description: >
  Entity Framework Core fundamentals. DbContext configuration, entity
  configuration with IEntityTypeConfiguration, value converters, and
  connection resiliency.
  Trigger: EF Core, DbContext, entity configuration, database, ORM.
metadata:
  category: data
  agent: ef-specialist
  when-to-use: "When configuring EF Core DbContext, entity configurations, migrations"
---

# EF Core Basics

## Core Principles

- Use `IEntityTypeConfiguration<T>` for fluent configuration in separate files
- Apply configurations from assembly to keep DbContext clean
- Use value converters for strongly-typed IDs and custom types
- Enable connection resiliency with retry on failure
- Register interceptors for cross-cutting concerns (audit, domain events)

## Patterns

### DbContext Setup

```csharp
public sealed class AppDbContext(
    DbContextOptions<AppDbContext> options) : DbContext(options)
{
    public DbSet<Order> Orders => Set<Order>();
    public DbSet<Product> Products => Set<Product>();
    public DbSet<Customer> Customers => Set<Customer>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(
            typeof(AppDbContext).Assembly);
    }
}
```

### Entity Configuration

```csharp
internal sealed class OrderConfiguration
    : IEntityTypeConfiguration<Order>
{
    public void Configure(EntityTypeBuilder<Order> builder)
    {
        builder.HasKey(o => o.Id);

        // Strongly-typed ID conversion
        builder.Property(o => o.Id)
            .HasConversion(
                id => id.Value,
                value => new OrderId(value));

        builder.Property(o => o.CustomerName)
            .HasMaxLength(200)
            .IsRequired();

        builder.Property(o => o.Status)
            .HasConversion<string>()
            .HasMaxLength(50);

        // Row version for concurrency
        builder.Property(o => o.RowVersion)
            .IsRowVersion();

        // Relationships
        builder.HasMany(o => o.Items)
            .WithOne()
            .HasForeignKey(i => i.OrderId)
            .OnDelete(DeleteBehavior.Cascade);

        // Soft delete filter
        builder.HasQueryFilter(o => !o.IsDeleted);

        // Indexes
        builder.HasIndex(o => o.CustomerName);
        builder.HasIndex(o => o.CreatedAt);
    }
}
```

### Value Converters

```csharp
// Strongly-typed ID converter
internal sealed class OrderIdConverter
    : ValueConverter<OrderId, Guid>
{
    public OrderIdConverter()
        : base(id => id.Value, value => new OrderId(value)) { }
}

// Value object converter (owned type is preferred for complex VOs)
builder.OwnsOne(o => o.ShippingAddress, address =>
{
    address.Property(a => a.Street).HasMaxLength(200);
    address.Property(a => a.City).HasMaxLength(100);
    address.Property(a => a.ZipCode).HasMaxLength(20);
});
```

### Registration with Interceptors

```csharp
builder.Services.AddDbContext<AppDbContext>((sp, options) =>
{
    options.UseSqlServer(
        builder.Configuration.GetConnectionString("Default"),
        sql =>
        {
            sql.EnableRetryOnFailure(
                maxRetryCount: 3,
                maxRetryDelay: TimeSpan.FromSeconds(5),
                errorNumbersToAdd: null);
            sql.CommandTimeout(30);
            sql.MigrationsAssembly(
                typeof(AppDbContext).Assembly.FullName);
        });

    options.AddInterceptors(
        sp.GetRequiredService<AuditableInterceptor>(),
        sp.GetRequiredService<DomainEventInterceptor>());
});

// PostgreSQL alternative
options.UseNpgsql(connectionString, npgsql =>
{
    npgsql.EnableRetryOnFailure(3);
    npgsql.CommandTimeout(30);
});
```

### Domain Event Dispatch Interceptor

```csharp
public sealed class DomainEventInterceptor(IPublisher publisher)
    : SaveChangesInterceptor
{
    public override async ValueTask<int> SavedChangesAsync(
        SaveChangesCompletedEventData eventData,
        int result,
        CancellationToken ct = default)
    {
        var context = eventData.Context!;
        var aggregates = context.ChangeTracker
            .Entries<AggregateRoot<object>>()
            .Where(e => e.Entity.DomainEvents.Count != 0)
            .Select(e => e.Entity)
            .ToList();

        foreach (var aggregate in aggregates)
        {
            foreach (var domainEvent in aggregate.DomainEvents)
                await publisher.Publish(domainEvent, ct);
            aggregate.ClearDomainEvents();
        }

        return result;
    }
}
```

### Design-Time Factory

```csharp
// For running migrations from CLI without the app host
internal sealed class AppDbContextFactory
    : IDesignTimeDbContextFactory<AppDbContext>
{
    public AppDbContext CreateDbContext(string[] args)
    {
        var config = new ConfigurationBuilder()
            .AddJsonFile("appsettings.json")
            .AddJsonFile("appsettings.Development.json", optional: true)
            .Build();

        var options = new DbContextOptionsBuilder<AppDbContext>()
            .UseSqlServer(config.GetConnectionString("Default"))
            .Options;

        return new AppDbContext(options);
    }
}
```

## Anti-Patterns

- Configuring entities in `OnModelCreating` directly (use separate configuration files)
- Missing concurrency tokens on entities that can be updated concurrently
- Not using `IsRequired()` / `HasMaxLength()` (relies on nullable annotations only)
- Forgetting to apply configurations from assembly
- Using `string` for enums in the database without explicit conversion

## Detect Existing Patterns

1. Search for `: DbContext` class inheritance
2. Look for `UseSqlServer` or `UseNpgsql` in `Program.cs`
3. Check for `IEntityTypeConfiguration<T>` implementations
4. Look for `Migrations/` folder
5. Check for `SaveChangesInterceptor` implementations

## Adding to Existing Project

1. **Create DbContext** with `ApplyConfigurationsFromAssembly`
2. **Create configuration files** — one per entity using `IEntityTypeConfiguration<T>`
3. **Add value converters** for strongly-typed IDs
4. **Enable retry on failure** in the connection configuration
5. **Add interceptors** for audit trail and domain event dispatch
6. **Create design-time factory** for CLI migrations

## Decision Guide

| Scenario | Approach |
|----------|----------|
| Strongly-typed ID | `HasConversion` with ValueConverter |
| Complex value object | `OwnsOne` owned entity |
| Soft delete | Global query filter |
| Concurrency | `IsRowVersion()` or `IsConcurrencyToken()` |
| Enum storage | `HasConversion<string>()` |

## References

- https://learn.microsoft.com/en-us/ef/core/
- https://learn.microsoft.com/en-us/ef/core/modeling/
