---
name: rate-limiting
description: >
  Use when adding rate limiting or throttling to .NET API endpoints.
metadata:
  category: api
  agent: api-designer
  when-to-use: "When implementing rate limiting policies or throttling for API endpoints"
---

# Rate Limiting

## Core Principles

- Protect backend resources from overload and abuse
- Ensure fair access across consumers — no single client starves others
- Return `429 Too Many Requests` with a `Retry-After` header when limits are exceeded
- Apply rate limiting as middleware early in the pipeline, before expensive work
- Use the built-in `System.Threading.RateLimiting` and `Microsoft.AspNetCore.RateLimiting` packages (.NET 7+)
- Combine global and per-endpoint policies for layered protection

## When to Use

- Public-facing APIs exposed to untrusted or semi-trusted clients
- Endpoints with expensive downstream operations (database writes, external API calls)
- Multi-tenant systems where one tenant's traffic must not degrade others
- Authentication endpoints to prevent brute-force attacks
- Any API that needs to enforce usage quotas or SLA tiers

## When NOT to Use

- Internal service-to-service calls behind a trusted network boundary (use circuit breakers instead)
- Static file serving already handled by a CDN or reverse proxy
- When an upstream API gateway (e.g., Azure API Management, Kong) already enforces limits
- Low-traffic admin endpoints where throttling adds complexity without benefit

## Patterns

### Setup

```csharp
// Program.cs
using System.Threading.RateLimiting;
using Microsoft.AspNetCore.RateLimiting;

builder.Services.AddRateLimiter(options =>
{
    options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;

    // Global limiter applied to all endpoints
    options.GlobalLimiter = PartitionedRateLimiter.Create<HttpContext, string>(
        context => RateLimitPartition.GetFixedWindowLimiter(
            partitionKey: "global",
            factory: _ => new FixedWindowRateLimiterOptions
            {
                PermitLimit = 1000,
                Window = TimeSpan.FromMinutes(1)
            }));
});

// Add middleware — place after authentication but before endpoint routing
app.UseRateLimiter();
```

### Fixed Window

Allows a fixed number of requests within a non-overlapping time window. Simplest algorithm but can cause burst traffic at window boundaries.

```csharp
builder.Services.AddRateLimiter(options =>
{
    options.AddFixedWindowLimiter("fixed", limiterOptions =>
    {
        limiterOptions.PermitLimit = 100;
        limiterOptions.Window = TimeSpan.FromMinutes(1);
        limiterOptions.QueueProcessingOrder = QueueProcessingOrder.OldestFirst;
        limiterOptions.QueueLimit = 10;
    });
});
```

### Sliding Window

Divides the window into segments for smoother traffic distribution. Avoids the boundary-burst problem of fixed windows.

```csharp
builder.Services.AddRateLimiter(options =>
{
    options.AddSlidingWindowLimiter("sliding", limiterOptions =>
    {
        limiterOptions.PermitLimit = 100;
        limiterOptions.Window = TimeSpan.FromMinutes(1);
        limiterOptions.SegmentsPerWindow = 6; // 10-second segments
        limiterOptions.QueueProcessingOrder = QueueProcessingOrder.OldestFirst;
        limiterOptions.QueueLimit = 5;
    });
});
```

### Token Bucket

Tokens replenish at a steady rate, allowing short bursts up to the bucket capacity while enforcing a long-term average rate.

```csharp
builder.Services.AddRateLimiter(options =>
{
    options.AddTokenBucketLimiter("token", limiterOptions =>
    {
        limiterOptions.TokenLimit = 100;
        limiterOptions.ReplenishmentPeriod = TimeSpan.FromSeconds(10);
        limiterOptions.TokensPerPeriod = 20;
        limiterOptions.QueueProcessingOrder = QueueProcessingOrder.OldestFirst;
        limiterOptions.QueueLimit = 10;
        limiterOptions.AutoReplenishment = true;
    });
});
```

### Concurrency Limiter

Limits the number of concurrent requests rather than requests per time window. Useful for protecting resources with limited parallelism.

```csharp
builder.Services.AddRateLimiter(options =>
{
    options.AddConcurrencyLimiter("concurrency", limiterOptions =>
    {
        limiterOptions.PermitLimit = 50;
        limiterOptions.QueueProcessingOrder = QueueProcessingOrder.OldestFirst;
        limiterOptions.QueueLimit = 25;
    });
});
```

### Per-Endpoint Policies

Apply named policies to specific endpoints or route groups.

```csharp
// Minimal API
app.MapGet("/api/orders", GetOrders)
    .RequireRateLimiting("sliding");

app.MapPost("/api/orders", CreateOrder)
    .RequireRateLimiting("token");

// Route group
var api = app.MapGroup("/api/reports")
    .RequireRateLimiting("fixed");

api.MapGet("/daily", GetDailyReport);
api.MapGet("/monthly", GetMonthlyReport);

// Disable rate limiting on a specific endpoint
app.MapGet("/api/health", GetHealth)
    .DisableRateLimiting();

// Controller attribute
[EnableRateLimiting("sliding")]
[ApiController]
[Route("api/[controller]")]
public sealed class OrdersController : ControllerBase
{
    [HttpGet]
    public async Task<IActionResult> GetOrders() { /* ... */ }

    [DisableRateLimiting]
    [HttpGet("count")]
    public async Task<IActionResult> GetOrderCount() { /* ... */ }
}
```

### Custom Partitioners

Partition rate limits by user identity, IP address, or API key so each consumer gets an independent quota.

```csharp
builder.Services.AddRateLimiter(options =>
{
    // Per authenticated user
    options.AddPolicy("per-user", context =>
        RateLimitPartition.GetFixedWindowLimiter(
            partitionKey: context.User?.Identity?.Name ?? "anonymous",
            factory: _ => new FixedWindowRateLimiterOptions
            {
                PermitLimit = 60,
                Window = TimeSpan.FromMinutes(1)
            }));

    // Per IP address
    options.AddPolicy("per-ip", context =>
        RateLimitPartition.GetSlidingWindowLimiter(
            partitionKey: context.Connection.RemoteIpAddress?.ToString() ?? "unknown",
            factory: _ => new SlidingWindowRateLimiterOptions
            {
                PermitLimit = 200,
                Window = TimeSpan.FromMinutes(1),
                SegmentsPerWindow = 4
            }));

    // Per API key with tiered limits
    options.AddPolicy("per-api-key", context =>
    {
        var apiKey = context.Request.Headers["X-Api-Key"].ToString();
        var tier = GetTierForApiKey(apiKey); // Your lookup logic

        return tier switch
        {
            "premium" => RateLimitPartition.GetTokenBucketLimiter(apiKey,
                _ => new TokenBucketRateLimiterOptions
                {
                    TokenLimit = 500,
                    ReplenishmentPeriod = TimeSpan.FromSeconds(10),
                    TokensPerPeriod = 100,
                    AutoReplenishment = true
                }),
            _ => RateLimitPartition.GetTokenBucketLimiter(apiKey,
                _ => new TokenBucketRateLimiterOptions
                {
                    TokenLimit = 50,
                    ReplenishmentPeriod = TimeSpan.FromSeconds(10),
                    TokensPerPeriod = 10,
                    AutoReplenishment = true
                })
        };
    });
});
```

### 429 Response

Customize the rejection response to include a `Retry-After` header and a structured error body.

```csharp
builder.Services.AddRateLimiter(options =>
{
    options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;

    options.OnRejected = async (context, cancellationToken) =>
    {
        context.HttpContext.Response.StatusCode = StatusCodes.Status429TooManyRequests;

        if (context.Lease.TryGetMetadata(MetadataName.RetryAfter, out var retryAfter))
        {
            context.HttpContext.Response.Headers.RetryAfter =
                ((int)retryAfter.TotalSeconds).ToString();
        }

        context.HttpContext.Response.ContentType = "application/problem+json";
        await context.HttpContext.Response.WriteAsJsonAsync(new
        {
            type = "https://tools.ietf.org/html/rfc6585#section-4",
            title = "Too Many Requests",
            status = 429,
            detail = "Rate limit exceeded. Please retry after the duration indicated in the Retry-After header."
        }, cancellationToken);
    };
});
```

## Decision Guide

| Scenario | Algorithm | Why |
|----------|-----------|-----|
| Simple request cap per minute | Fixed Window | Easy to understand and configure |
| Smooth traffic with no boundary spikes | Sliding Window | Distributes permits across segments |
| Allow short bursts with steady average | Token Bucket | Permits accumulate during quiet periods |
| Protect CPU/memory-bound operations | Concurrency Limiter | Caps parallel execution, not rate |
| Multi-tenant with per-user fairness | Custom Partitioner + any algorithm | Each partition tracks independently |
| Login / auth endpoints (brute force) | Fixed Window, low limit | Simple hard cap per IP |
| File upload endpoints | Concurrency Limiter | Prevent memory exhaustion from parallel uploads |
| Public search API | Sliding Window | Smooth throttling for variable traffic |

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| No `Retry-After` header on 429 | Clients retry immediately, worsening load | Use `OnRejected` to set the header from lease metadata |
| Rate limiting after expensive middleware | Work is already done before rejection | Place `UseRateLimiter()` early in the pipeline |
| Same limit for all endpoints | Health checks and admin routes get throttled | Use per-endpoint policies and `DisableRateLimiting()` |
| Global-only limits, no per-client partitioning | One abusive client exhausts the quota for everyone | Use `AddPolicy` with a partition key (user, IP, API key) |
| Unlimited queue depth | Memory grows under sustained overload | Set `QueueLimit` to a reasonable bound |
| Hardcoded limits with no configuration | Cannot adjust without redeployment | Bind limits from `IConfiguration` / `appsettings.json` |
| Rate limiting in every microservice independently | Inconsistent limits, hard to reason about | Centralize at the API gateway when possible |

## Detect Existing Patterns

1. Search for `Microsoft.AspNetCore.RateLimiting` package in `.csproj` files
2. Look for `AddRateLimiter` in `Program.cs` or startup configuration
3. Check for `UseRateLimiter()` in the middleware pipeline
4. Search for `RequireRateLimiting` or `EnableRateLimiting` on endpoints
5. Look for third-party packages like `AspNetCoreRateLimit` (migration candidate)

## Adding to Existing Project

1. **Verify** .NET 7 or later — rate limiting middleware is not available in earlier versions
2. **Install** `Microsoft.AspNetCore.RateLimiting` (included in the framework shared package)
3. **Register** `AddRateLimiter()` with at least one named policy
4. **Add middleware** `app.UseRateLimiter()` after authentication, before endpoint mapping
5. **Apply policies** to endpoints with `RequireRateLimiting("policy-name")`
6. **Configure `OnRejected`** to return `Retry-After` and a Problem Details body
7. **Test** with a load tool (e.g., `dotnet-httpie`, `bombardier`) to verify limits

## References

- https://learn.microsoft.com/en-us/aspnet/core/performance/rate-limit
- https://devblogs.microsoft.com/dotnet/announcing-rate-limiting-for-dotnet/
- https://learn.microsoft.com/en-us/dotnet/api/system.threading.ratelimiting
