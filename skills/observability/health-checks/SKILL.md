---
name: health-checks
description: >
  ASP.NET Core health check endpoints, custom health checks,
  Kubernetes probes, and health check UI.
  Trigger: health check, liveness, readiness, probe, /health.
metadata:
  category: observability
  agent: devops-engineer
  when-to-use: "When configuring health check endpoints, Kubernetes probes, or health check UI"
---

# Health Checks

## Core Principles

- `/health/live` — liveness: is the process running? (no dependency checks)
- `/health/ready` — readiness: can the service handle requests? (all deps checked)
- `/health` — comprehensive: full status with details for monitoring dashboards
- Use tags to group checks for different endpoints
- Custom health checks for business-specific degradation detection

## Patterns

### Health Check Registration

```csharp
// Program.cs
builder.Services.AddHealthChecks()
    // Database
    .AddSqlServer(
        connectionString: builder.Configuration
            .GetConnectionString("Default")!,
        name: "sqlserver",
        tags: ["ready", "db"])
    // Redis cache
    .AddRedis(
        redisConnectionString: builder.Configuration
            .GetConnectionString("Redis")!,
        name: "redis",
        tags: ["ready", "cache"])
    // HTTP dependency
    .AddUrlGroup(
        uri: new Uri(builder.Configuration["PaymentService:Url"]!),
        name: "payment-service",
        tags: ["ready", "external"])
    // Custom business check
    .AddCheck<OrderProcessingHealthCheck>(
        name: "order-processing",
        tags: ["ready", "business"]);
```

### Endpoint Mapping with Tag Filtering

```csharp
// Liveness — no dependency checks
app.MapHealthChecks("/health/live", new HealthCheckOptions
{
    Predicate = _ => false // always healthy if process is running
});

// Readiness — check all dependencies
app.MapHealthChecks("/health/ready", new HealthCheckOptions
{
    Predicate = check => check.Tags.Contains("ready"),
    ResponseWriter = WriteDetailedResponse
});

// Full status — all checks with details
app.MapHealthChecks("/health", new HealthCheckOptions
{
    ResponseWriter = WriteDetailedResponse
});
```

### Detailed JSON Response Writer

```csharp
static Task WriteDetailedResponse(
    HttpContext context, HealthReport report)
{
    context.Response.ContentType = "application/json";

    var response = new
    {
        status = report.Status.ToString(),
        duration = report.TotalDuration.TotalMilliseconds,
        timestamp = DateTimeOffset.UtcNow,
        checks = report.Entries.Select(e => new
        {
            name = e.Key,
            status = e.Value.Status.ToString(),
            duration = e.Value.Duration.TotalMilliseconds,
            description = e.Value.Description,
            tags = e.Value.Tags,
            error = e.Value.Exception?.Message,
            data = e.Value.Data.Count > 0 ? e.Value.Data : null
        })
    };

    return context.Response.WriteAsJsonAsync(response);
}
```

### Custom Business Health Check

```csharp
public sealed class OrderProcessingHealthCheck(AppDbContext db)
    : IHealthCheck
{
    public async Task<HealthCheckResult> CheckHealthAsync(
        HealthCheckContext context,
        CancellationToken ct = default)
    {
        var stuckOrders = await db.Orders
            .CountAsync(o =>
                o.Status == OrderStatus.Processing &&
                o.UpdatedAt < DateTimeOffset.UtcNow.AddMinutes(-30),
                ct);

        var data = new Dictionary<string, object>
        {
            ["stuckOrderCount"] = stuckOrders
        };

        return stuckOrders switch
        {
            0 => HealthCheckResult.Healthy(
                "No stuck orders", data),
            < 5 => HealthCheckResult.Degraded(
                $"{stuckOrders} orders stuck > 30 min", data),
            _ => HealthCheckResult.Unhealthy(
                $"{stuckOrders} orders stuck > 30 min", data: data)
        };
    }
}
```

### Queue Depth Health Check

```csharp
public sealed class MessageQueueHealthCheck(
    IMessageQueueClient queueClient) : IHealthCheck
{
    public async Task<HealthCheckResult> CheckHealthAsync(
        HealthCheckContext context,
        CancellationToken ct = default)
    {
        var depth = await queueClient.GetQueueDepthAsync(ct);

        var data = new Dictionary<string, object>
        {
            ["queueDepth"] = depth
        };

        return depth switch
        {
            < 100 => HealthCheckResult.Healthy(
                $"Queue depth: {depth}", data),
            < 1000 => HealthCheckResult.Degraded(
                $"Queue depth high: {depth}", data),
            _ => HealthCheckResult.Unhealthy(
                $"Queue depth critical: {depth}", data: data)
        };
    }
}
```

### Kubernetes Probe Configuration

```yaml
# deployment.yaml
spec:
  containers:
    - name: order-service
      ports:
        - containerPort: 8080
      livenessProbe:
        httpGet:
          path: /health/live
          port: 8080
        initialDelaySeconds: 10
        periodSeconds: 30
        failureThreshold: 3
      readinessProbe:
        httpGet:
          path: /health/ready
          port: 8080
        initialDelaySeconds: 15
        periodSeconds: 10
        failureThreshold: 3
      startupProbe:
        httpGet:
          path: /health/live
          port: 8080
        initialDelaySeconds: 5
        periodSeconds: 5
        failureThreshold: 30
```

### Health Check UI (Optional)

```csharp
// Install: AspNetCore.HealthChecks.UI
// Install: AspNetCore.HealthChecks.UI.InMemory.Storage

builder.Services.AddHealthChecksUI(options =>
{
    options.SetEvaluationTimeInSeconds(30);
    options.MaximumHistoryEntriesPerEndpoint(100);
    options.AddHealthCheckEndpoint("API", "/health");
})
.AddInMemoryStorage();

app.MapHealthChecksUI(options =>
{
    options.UIPath = "/health-ui";
});
```

## Packages

```xml
<PackageReference Include="AspNetCore.HealthChecks.SqlServer" />
<PackageReference Include="AspNetCore.HealthChecks.Redis" />
<PackageReference Include="AspNetCore.HealthChecks.Uris" />
<PackageReference Include="AspNetCore.HealthChecks.NpgSql" />
<!-- Optional UI -->
<PackageReference Include="AspNetCore.HealthChecks.UI" />
<PackageReference Include="AspNetCore.HealthChecks.UI.InMemory.Storage" />
```

## Anti-Patterns

- Running expensive checks on the liveness endpoint (should be trivial)
- Not differentiating liveness from readiness (different purposes)
- Health checks that throw exceptions instead of returning Unhealthy
- Missing timeout on external dependency checks (blocks the endpoint)
- Not exposing health checks for Kubernetes probes

## Detect Existing Patterns

1. Search for `AddHealthChecks()` in `Program.cs`
2. Look for `MapHealthChecks` endpoint mapping
3. Check for `IHealthCheck` implementations
4. Look for `AspNetCore.HealthChecks.*` packages in `.csproj`
5. Check Kubernetes manifests for probe configuration

## Adding to Existing Project

1. **Add health check registration** in `Program.cs`
2. **Add built-in checks** for database, Redis, and HTTP dependencies
3. **Create custom checks** for business-specific health indicators
4. **Map three endpoints**: `/health/live`, `/health/ready`, `/health`
5. **Add detailed response writer** for monitoring dashboard integration
6. **Configure Kubernetes probes** in deployment manifests

## Decision Guide

| Endpoint | Purpose | Checks | Probe |
|----------|---------|--------|-------|
| `/health/live` | Is process alive? | None | Liveness |
| `/health/ready` | Can handle requests? | DB, cache, deps | Readiness |
| `/health` | Full status | All checks | Dashboard |

## References

- https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/health-checks
- https://github.com/Xabaril/AspNetCore.Diagnostics.HealthChecks
