---
name: caching-strategies
description: >
  Use when adding caching to .NET APIs or optimizing response times with distributed cache, output cache, or ETags.
metadata:
  category: api
  agent: api-designer
  when-to-use: "When implementing caching strategies, output caching, or distributed cache patterns"
---

# Caching Strategies

## Core Principles

- Cache as close to the consumer as possible (browser > CDN > reverse proxy > app)
- Always set an explicit TTL — unbounded caches lead to stale data and memory pressure
- Invalidate explicitly when underlying data changes — do not rely solely on expiry
- Avoid serving stale data for writes — cache reads aggressively, invalidate on mutations
- Use cache-aside pattern: check cache first, fall back to source, populate cache on miss

## When to Use

- Read-heavy endpoints where the same data is requested frequently
- Reference data that changes infrequently (catalogs, config, lookups)
- Expensive computations or aggregations (reports, dashboards)
- Responses that are identical for many users (public content, product listings)
- APIs behind rate-limited downstream services

## When NOT to Use

- User-specific data that changes on every request (real-time balances, live feeds)
- Endpoints with strong consistency requirements (payment processing, stock trading)
- Write-heavy workflows where invalidation cost exceeds cache benefit
- Data with regulatory constraints that prohibit caching (PII in some jurisdictions)
- Responses smaller than the cache overhead (trivial lookups)

## Patterns

### Output Caching

Server-side cache built into ASP.NET Core. Caches entire HTTP responses.

```csharp
// Program.cs — register and enable output caching
builder.Services.AddOutputCache(options =>
{
    // Default policy: cache all GET/HEAD responses for 60s
    options.AddBasePolicy(p => p.Expire(TimeSpan.FromSeconds(60)));

    // Named policy with tag for invalidation
    options.AddPolicy("Products", p => p
        .Expire(TimeSpan.FromMinutes(5))
        .Tag("products"));

    // Per-user policy using Authorization header variation
    options.AddPolicy("UserSpecific", p => p
        .SetVaryByHeader("Authorization")
        .Expire(TimeSpan.FromSeconds(30)));
});

app.UseOutputCache();
```

```csharp
// Minimal API — apply output cache policy
app.MapGet("/products", async (ISender sender, CancellationToken ct) =>
{
    var products = await sender.Send(new ListProductsQuery(), ct);
    return Results.Ok(products);
}).CacheOutput("Products");

// Controller — attribute-based
[HttpGet]
[OutputCache(Duration = 60, Tags = ["products"])]
public async Task<ActionResult<List<ProductResponse>>> GetAll(
    CancellationToken ct)
{
    var result = await sender.Send(new ListProductsQuery(), ct);
    return Ok(result);
}
```

```csharp
// Tag-based invalidation using IOutputCacheStore
app.MapPost("/products", async (
    CreateProductCommand command, ISender sender,
    IOutputCacheStore cache, CancellationToken ct) =>
{
    var id = await sender.Send(command, ct);
    await cache.EvictByTagAsync("products", ct);
    return Results.Created($"/products/{id}", new { id });
});
```

### Response Caching

Client-side caching via HTTP Cache-Control headers. The browser or CDN caches responses.

```csharp
// Program.cs
builder.Services.AddResponseCaching();
app.UseResponseCaching();
```

```csharp
// Controller with Cache-Control headers
[HttpGet]
[ResponseCache(Duration = 120, Location = ResponseCacheLocation.Any,
    VaryByHeader = "Accept")]
public async Task<ActionResult<List<CategoryResponse>>> GetCategories(
    CancellationToken ct)
{
    var result = await sender.Send(new ListCategoriesQuery(), ct);
    return Ok(result);
}

// No-cache for sensitive data
[HttpGet("me")]
[ResponseCache(Duration = 0, Location = ResponseCacheLocation.None,
    NoStore = true)]
public async Task<ActionResult<UserProfile>> GetProfile(
    CancellationToken ct)
{
    var result = await sender.Send(new GetProfileQuery(), ct);
    return Ok(result);
}
```

### Distributed Cache

`IDistributedCache` backed by Redis, SQL Server, or NCache. Shared across app instances.

```csharp
// Program.cs — Redis distributed cache
builder.Services.AddStackExchangeRedisCache(options =>
{
    options.Configuration =
        builder.Configuration.GetConnectionString("Redis");
    options.InstanceName = "MyApp:";
});
```

```csharp
// Service using IDistributedCache
public sealed class CachedProductService(
    IDistributedCache cache,
    IProductRepository repository)
{
    private static readonly DistributedCacheEntryOptions CacheOptions = new()
    {
        AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(10),
        SlidingExpiration = TimeSpan.FromMinutes(2)
    };

    public async Task<ProductResponse?> GetByIdAsync(
        Guid id, CancellationToken ct)
    {
        var cacheKey = $"product:{id}";

        // Try cache first
        var cached = await cache.GetStringAsync(cacheKey, ct);
        if (cached is not null)
        {
            return JsonSerializer.Deserialize<ProductResponse>(cached);
        }

        // Fall back to database
        var product = await repository.GetByIdAsync(id, ct);
        if (product is null) return null;

        var response = product.ToResponse();
        await cache.SetStringAsync(
            cacheKey, JsonSerializer.Serialize(response),
            CacheOptions, ct);

        return response;
    }

    public async Task InvalidateAsync(Guid id, CancellationToken ct)
    {
        await cache.RemoveAsync($"product:{id}", ct);
    }
}
```

### HybridCache (.NET 9+)

Two-tier cache: L1 in-process memory + L2 distributed. Built-in stampede protection.

```csharp
// Program.cs — register HybridCache with Redis L2
builder.Services.AddHybridCache(options =>
{
    options.MaximumPayloadBytes = 1024 * 1024; // 1 MB
    options.MaximumKeyLength = 256;
    options.DefaultEntryOptions = new HybridCacheEntryOptions
    {
        Expiration = TimeSpan.FromMinutes(10),
        LocalCacheExpiration = TimeSpan.FromMinutes(2)
    };
});

// Add Redis as the L2 backing store
builder.Services.AddStackExchangeRedisCache(options =>
{
    options.Configuration =
        builder.Configuration.GetConnectionString("Redis");
});
```

```csharp
// Service using HybridCache — stampede-safe GetOrCreateAsync
public sealed class ProductService(
    HybridCache cache, IProductRepository repository)
{
    public async Task<ProductResponse> GetByIdAsync(
        Guid id, CancellationToken ct)
    {
        return await cache.GetOrCreateAsync(
            $"product:{id}",
            async token =>
            {
                var product = await repository.GetByIdAsync(id, token)
                    ?? throw new NotFoundException(
                        $"Product {id} not found");
                return product.ToResponse();
            },
            new HybridCacheEntryOptions
            {
                Expiration = TimeSpan.FromMinutes(5),
                LocalCacheExpiration = TimeSpan.FromMinutes(1)
            },
            cancellationToken: ct);
    }

    public async Task InvalidateAsync(Guid id, CancellationToken ct)
    {
        await cache.RemoveAsync($"product:{id}", ct);
    }
}
```

### ETag / Conditional Requests

Return `304 Not Modified` when content has not changed, saving bandwidth.

```csharp
// ETag generation helper
public static class ETagHelper
{
    public static string Generate(object data)
    {
        var json = JsonSerializer.Serialize(data);
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(json));
        return $"\"{Convert.ToBase64String(bytes)}\"";
    }
}
```

```csharp
// Controller with ETag support
[HttpGet("{id:guid}")]
public async Task<ActionResult<ProductResponse>> GetById(
    Guid id, CancellationToken ct)
{
    var product = await sender.Send(new GetProductQuery(id), ct);
    if (product is null) return NotFound();

    var etag = ETagHelper.Generate(product);

    if (Request.Headers.IfNoneMatch.Contains(etag))
    {
        return StatusCode(StatusCodes.Status304NotModified);
    }

    Response.Headers.ETag = etag;
    Response.Headers.CacheControl = "private, max-age=60";
    return Ok(product);
}
```

### Cache Invalidation

Strategies to keep cached data consistent with the source of truth.

```csharp
// Tag-based invalidation (Output Cache)
app.MapPut("/products/{id:guid}", async (
    Guid id, UpdateProductCommand command, ISender sender,
    IOutputCacheStore cache, CancellationToken ct) =>
{
    await sender.Send(command with { Id = id }, ct);
    await cache.EvictByTagAsync("products", ct);
    return Results.NoContent();
});
```

```csharp
// Event-based invalidation with MediatR notification
public sealed record ProductUpdatedEvent(Guid ProductId) : INotification;

public sealed class InvalidateProductCacheHandler(
    HybridCache cache) : INotificationHandler<ProductUpdatedEvent>
{
    public async Task Handle(
        ProductUpdatedEvent notification, CancellationToken ct)
    {
        await cache.RemoveAsync(
            $"product:{notification.ProductId}", ct);
    }
}
```

Key invalidation approaches:
- **Tag-based** — group related entries, evict all at once via `EvictByTagAsync`
- **Event-based** — domain events trigger cache removal through MediatR handlers
- **TTL expiry** — set `AbsoluteExpiration` for automatic cleanup
- **Manual eviction** — call `RemoveAsync` directly in write endpoints

## Decision Guide

| Scenario | Cache Type | Why |
|----------|-----------|-----|
| Public GET, same response for all users | Output Cache | Server-side, zero client config |
| Static assets and CDN-friendly responses | Response Cache | Cache-Control for browser/CDN |
| Shared data across multiple app instances | Distributed Cache (Redis) | Centralized, survives restarts |
| High-throughput reads, local + shared needs | HybridCache (.NET 9+) | L1 speed + L2 consistency + stampede guard |
| Bandwidth-sensitive mobile clients | ETag / Conditional | 304 saves payload transfer |
| Reference data (countries, currencies) | HybridCache or Output Cache | Rarely changes, high read volume |
| User session or cart data | Distributed Cache | Per-user, shared across instances |
| Expensive aggregation queries | HybridCache with long TTL | Compute once, serve many |

## Anti-Patterns

| Problem | Why It Hurts | Correct Approach |
|---------|-------------|-----------------|
| No TTL on cache entries | Memory grows unbounded, stale data forever | Always set `AbsoluteExpiration` or `SlidingExpiration` |
| Caching behind auth without Vary | User A sees User B's data | `SetVaryByHeader("Authorization")` or skip output cache |
| Cache-then-write without invalidation | Reads return stale data after mutations | Invalidate or evict on every write path |
| Caching error responses | Errors served repeatedly from cache | Only cache successful (2xx) responses |
| In-memory cache in multi-instance deploy | Each instance has different cache state | Use `IDistributedCache` or `HybridCache` |
| Stampede on cache miss (thundering herd) | All requests hit DB simultaneously | Use `HybridCache.GetOrCreateAsync` with stampede protection |
| Over-caching volatile data | Users see outdated information | Match TTL to change frequency; skip real-time data |

## References

- https://learn.microsoft.com/en-us/aspnet/core/performance/caching/output
- https://learn.microsoft.com/en-us/aspnet/core/performance/caching/distributed
- https://learn.microsoft.com/en-us/aspnet/core/performance/caching/hybrid
- https://learn.microsoft.com/en-us/aspnet/core/performance/caching/response
