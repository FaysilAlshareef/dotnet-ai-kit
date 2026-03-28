---
name: dotnet-ai-dependency-injection
alwaysApply: true
description: >
  DI registration patterns, service lifetimes, keyed services, Options pattern,
  decorator pattern, and factory delegates.
  Trigger: DI, dependency injection, services, registration, lifetime, singleton, scoped.
category: core
agent: dotnet-architect
---

# Dependency Injection

## Core Principles

- Use constructor injection exclusively — avoid service locator pattern
- Choose the correct lifetime: Singleton, Scoped, or Transient
- Organize registrations in `IServiceCollection` extension methods
- Use keyed services (.NET 8+) for multiple implementations of the same interface
- Validate registrations at startup where possible
- Never resolve scoped services from a singleton

## Patterns

### Service Registration Extension Methods

```csharp
// Organize by layer or feature
public static class DependencyInjection
{
    public static IServiceCollection AddApplicationServices(
        this IServiceCollection services)
    {
        services.AddMediatR(cfg =>
            cfg.RegisterServicesFromAssembly(typeof(DependencyInjection).Assembly));

        services.AddValidatorsFromAssembly(
            typeof(DependencyInjection).Assembly);

        return services;
    }

    public static IServiceCollection AddInfrastructureServices(
        this IServiceCollection services, IConfiguration configuration)
    {
        // Scoped — one instance per HTTP request
        services.AddScoped<IOrderRepository, OrderRepository>();
        services.AddScoped<IUnitOfWork, UnitOfWork>();

        // Open generics
        services.AddScoped(typeof(IRepository<>), typeof(EfRepository<>));

        // Singleton — one instance for the app lifetime
        services.AddSingleton<IDateTimeProvider, DateTimeProvider>();

        // Transient — new instance every time
        services.AddTransient<IEmailSender, SmtpEmailSender>();

        return services;
    }
}

// Program.cs
builder.Services
    .AddApplicationServices()
    .AddInfrastructureServices(builder.Configuration);
```

### Lifetime Decision Guide

```
Singleton  — stateless services, caches, configuration wrappers
             Example: IDateTimeProvider, HybridCache, IOptions<T>
             Warning: must be thread-safe

Scoped     — per-request state, DbContext, UnitOfWork, repositories
             Example: AppDbContext, ICurrentUserService
             Default choice for most services

Transient  — lightweight stateless services, factory output
             Example: IEmailSender, validators
             Warning: do not hold expensive resources
```

### Keyed Services (.NET 8+)

```csharp
// Registration
services.AddKeyedSingleton<IPaymentGateway, StripeGateway>("stripe");
services.AddKeyedSingleton<IPaymentGateway, PayPalGateway>("paypal");
services.AddKeyedSingleton<IPaymentGateway, SquareGateway>("square");

// Injection via attribute
public sealed class CheckoutService(
    [FromKeyedServices("stripe")] IPaymentGateway gateway)
{
    public Task ChargeAsync(decimal amount) => gateway.ChargeAsync(amount);
}

// Resolution from provider
public sealed class PaymentRouter(IServiceProvider provider)
{
    public IPaymentGateway GetGateway(string name)
        => provider.GetRequiredKeyedService<IPaymentGateway>(name);
}
```

### Decorator Pattern

```csharp
// Base service
services.AddScoped<IOrderService, OrderService>();

// Decorate with cross-cutting concerns (outermost last)
services.Decorate<IOrderService, CachedOrderService>();
services.Decorate<IOrderService, LoggingOrderService>();

// Decorator implementation
public sealed class CachedOrderService(
    IOrderService inner,
    HybridCache cache) : IOrderService
{
    public async Task<Order?> GetOrderAsync(Guid id, CancellationToken ct)
    {
        return await cache.GetOrCreateAsync(
            $"orders:{id}",
            async token => await inner.GetOrderAsync(id, token),
            cancellationToken: ct);
    }
}
```

### Factory Delegates

```csharp
services.AddScoped<IReportGenerator>(sp =>
{
    var config = sp.GetRequiredService<IOptions<ReportOptions>>().Value;
    return config.Format switch
    {
        "pdf" => sp.GetRequiredService<PdfReportGenerator>(),
        "csv" => sp.GetRequiredService<CsvReportGenerator>(),
        _ => throw new InvalidOperationException(
            $"Unknown report format: {config.Format}")
    };
});
```

### Background Service Scoping

```csharp
// Background services are singletons — create scopes for scoped deps
public sealed class OrderProcessor(
    IServiceScopeFactory scopeFactory,
    ILogger<OrderProcessor> logger) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            using var scope = scopeFactory.CreateScope();
            var repository = scope.ServiceProvider
                .GetRequiredService<IOrderRepository>();
            var unitOfWork = scope.ServiceProvider
                .GetRequiredService<IUnitOfWork>();

            await ProcessPendingOrdersAsync(repository, unitOfWork, ct);
            await Task.Delay(TimeSpan.FromSeconds(30), ct);
        }
    }
}
```

### Options Pattern Registration

```csharp
// Strongly-typed options with validation
services.AddOptions<DatabaseOptions>()
    .BindConfiguration(DatabaseOptions.SectionName)
    .ValidateDataAnnotations()
    .ValidateOnStart();

services.AddOptions<JwtOptions>()
    .BindConfiguration("Jwt")
    .ValidateDataAnnotations()
    .ValidateOnStart();
```

## Anti-Patterns

```csharp
// BAD: Service locator — hides dependencies
public class OrderService(IServiceProvider provider)
{
    public void Process()
    {
        var repo = provider.GetRequiredService<IOrderRepository>();
    }
}

// BAD: Captive dependency — scoped inside singleton
services.AddSingleton<MySingleton>(); // holds IOrderRepository (scoped)

// BAD: Resolving in constructor
public class OrderService(IServiceProvider provider)
{
    private readonly IOrderRepository _repo =
        provider.GetRequiredService<IOrderRepository>(); // resolves too early
}

// BAD: new-ing up services manually
public class OrderController
{
    private readonly OrderService _service = new OrderService(
        new OrderRepository(new AppDbContext())); // defeats DI
}
```

## Detect Existing Patterns

1. Search for `builder.Services.Add` calls in `Program.cs`
2. Look for `IServiceCollection` extension methods in the codebase
3. Check for `[FromKeyedServices]` usage (indicates .NET 8+ keyed DI)
4. Search for `AddScoped`, `AddTransient`, `AddSingleton` registration patterns
5. Look for `IServiceScopeFactory` usage in background services
6. Check for `Scrutor` package (provides `Decorate<>` extension)

## Adding to Existing Project

1. **Group registrations** — move scattered `builder.Services.Add*` calls into extension methods per layer
2. **Audit lifetimes** — verify no captive dependencies (scoped inside singleton)
3. **Add ValidateOnStart** — add `ValidateOnStart()` to all Options registrations
4. **Migrate to keyed services** — replace manual factory delegates with keyed services if on .NET 8+
5. **Use `Scrutor`** for decorator support if not already available:
   ```xml
   <PackageReference Include="Scrutor" />
   ```

## Decision Guide

| Scenario | Lifetime | Notes |
|----------|----------|-------|
| DbContext | Scoped | One per request |
| Repository | Scoped | Matches DbContext lifetime |
| HttpClient handler | Transient | Via IHttpClientFactory |
| Cache wrapper | Singleton | Thread-safe required |
| Options | Singleton | Via IOptions<T> |
| Current user | Scoped | Per-request context |
| Background service | Singleton | Use IServiceScopeFactory inside |

## References

- https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection
- https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection-guidelines
