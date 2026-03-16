---
name: serilog-structured
description: >
  Serilog configuration with two-stage bootstrap, structured logging,
  enrichers, Seq sink, and request logging middleware.
  Trigger: Serilog, structured logging, logging, Seq, enricher, log.
category: observability
agent: devops-engineer
---

# Serilog Structured Logging

## Core Principles

- Use two-stage bootstrap to capture startup errors
- Structured logging with `{PropertyName}` — never string interpolation
- Enrich logs with application name, machine name, and correlation IDs
- Use Seq for centralized log aggregation and querying
- Configure log levels per namespace to reduce noise

## Patterns

### Two-Stage Bootstrap

```csharp
// Program.cs
using Serilog;

// Stage 1: Bootstrap logger for startup errors
Log.Logger = new LoggerConfiguration()
    .MinimumLevel.Override("Microsoft", LogEventLevel.Information)
    .Enrich.FromLogContext()
    .WriteTo.Console()
    .CreateBootstrapLogger();

try
{
    var builder = WebApplication.CreateBuilder(args);

    // Stage 2: Full logger with configuration
    builder.Host.UseSerilog((context, services, configuration) =>
        configuration
            .ReadFrom.Configuration(context.Configuration)
            .ReadFrom.Services(services)
            .Enrich.FromLogContext()
            .Enrich.WithMachineName()
            .Enrich.WithProperty("Application", "{Domain}Service")
            .WriteTo.Console(outputTemplate:
                "[{Timestamp:HH:mm:ss} {Level:u3}] " +
                "{Message:lj} {Properties:j}" +
                "{NewLine}{Exception}")
            .WriteTo.Seq(
                context.Configuration["Seq:Url"]
                ?? "http://localhost:5341"));

    // Configure services...
    var app = builder.Build();

    // Request logging middleware
    app.UseSerilogRequestLogging(options =>
    {
        options.EnrichDiagnosticContext = (diagnosticContext,
            httpContext) =>
        {
            diagnosticContext.Set("UserId",
                httpContext.User.FindFirstValue(
                    ClaimTypes.NameIdentifier) ?? "anonymous");
            diagnosticContext.Set("ClientIp",
                httpContext.Connection.RemoteIpAddress?.ToString());
        };
    });

    app.Run();
}
catch (Exception ex)
{
    Log.Fatal(ex, "Application terminated unexpectedly");
}
finally
{
    Log.CloseAndFlush();
}
```

### appsettings.json Configuration

```json
{
  "Serilog": {
    "MinimumLevel": {
      "Default": "Information",
      "Override": {
        "Microsoft.AspNetCore": "Warning",
        "Microsoft.EntityFrameworkCore.Database.Command": "Warning",
        "Microsoft.EntityFrameworkCore.Infrastructure": "Warning",
        "System": "Warning"
      }
    }
  },
  "Seq": {
    "Url": "http://localhost:5341"
  }
}
```

### Structured Logging Best Practices

```csharp
// GOOD: Structured properties — queryable in Seq
logger.LogInformation(
    "Order {OrderId} created for customer {CustomerId} " +
    "with total {OrderTotal:C}",
    orderId, customerId, total);

// BAD: String interpolation — loses structure
logger.LogInformation(
    $"Order {orderId} created for customer {customerId}");

// GOOD: Object destructuring with @
logger.LogInformation(
    "Processing order {@OrderDetails}",
    new { orderId, customerId, ItemCount = items.Count });

// GOOD: Exception as first parameter
logger.LogError(ex,
    "Failed to process order {OrderId}", orderId);

// BAD: Exception in message template
logger.LogError(
    "Failed to process order {OrderId}: {Error}",
    orderId, ex.Message); // loses stack trace
```

### Scoped Logging with LogContext

```csharp
// Push properties for a scope — all logs within include them
using (LogContext.PushProperty("OrderId", orderId))
using (LogContext.PushProperty("CorrelationId",
    Activity.Current?.TraceId.ToString()))
{
    logger.LogInformation("Starting order processing");
    await ProcessItemsAsync(order, ct);
    logger.LogInformation("Order processing complete");
    // Both logs include OrderId and CorrelationId
}
```

### Custom Enricher

```csharp
public sealed class CorrelationIdEnricher(
    IHttpContextAccessor httpContextAccessor) : ILogEventEnricher
{
    public void Enrich(LogEvent logEvent,
        ILogEventPropertyFactory propertyFactory)
    {
        var correlationId =
            httpContextAccessor.HttpContext?
                .Request.Headers["X-Correlation-Id"]
                .FirstOrDefault()
            ?? Activity.Current?.TraceId.ToString()
            ?? Guid.NewGuid().ToString();

        logEvent.AddPropertyIfAbsent(
            propertyFactory.CreateProperty(
                "CorrelationId", correlationId));
    }
}

// Registration
builder.Host.UseSerilog((context, services, configuration) =>
    configuration
        .Enrich.With(
            services.GetRequiredService<CorrelationIdEnricher>())
        // ... rest of config
);
```

### Log Level Guidelines

```
Verbose    — Detailed debugging (not in production)
Debug      — Internal state useful for debugging
Information — Normal operation events (request handled, order created)
Warning    — Unexpected but handled (retry, degraded, slow query)
Error      — Failure that needs attention (exception, failed operation)
Fatal      — Application cannot continue (startup failure, data corruption)
```

### Performance: Conditional Logging

```csharp
// Check if level is enabled before expensive operations
if (logger.IsEnabled(LogLevel.Debug))
{
    var serialized = JsonSerializer.Serialize(complexObject);
    logger.LogDebug("Request payload: {Payload}", serialized);
}
```

## Packages

```xml
<PackageReference Include="Serilog.AspNetCore" />
<PackageReference Include="Serilog.Sinks.Seq" />
<PackageReference Include="Serilog.Sinks.Console" />
<PackageReference Include="Serilog.Enrichers.Environment" />
<PackageReference Include="Serilog.Enrichers.Thread" />
```

## Anti-Patterns

- String interpolation in log messages (`$"Order {id}"`)
- Missing `try/catch` around application startup
- Not calling `Log.CloseAndFlush()` in finally block
- Logging sensitive data (passwords, tokens, PII)
- Setting all namespaces to Debug/Verbose in production
- Not using request logging middleware (manual logging per endpoint)

## Detect Existing Patterns

1. Search for `Serilog.AspNetCore` package in `.csproj`
2. Look for `UseSerilog` in `Program.cs`
3. Check for `Log.Logger = new LoggerConfiguration()` initialization
4. Look for `WriteTo.Seq` or `WriteTo.Console` configuration
5. Check `appsettings.json` for `"Serilog"` section

## Adding to Existing Project

1. **Install packages** — `Serilog.AspNetCore`, `Serilog.Sinks.Seq`
2. **Set up two-stage bootstrap** in `Program.cs`
3. **Configure via appsettings** with level overrides per namespace
4. **Add request logging** middleware with enrichment
5. **Replace `ILogger` string interpolation** with structured templates
6. **Add Seq** or equivalent sink for centralized log aggregation

## Decision Guide

| Scenario | Sink |
|----------|------|
| Development | Console |
| Centralized logging | Seq, Elasticsearch, Datadog |
| Cloud native | Console (stdout) + aggregator |
| File-based | Rolling file (not recommended for containers) |

## References

- https://github.com/serilog/serilog-aspnetcore
- https://github.com/serilog/serilog/wiki/Structured-Data
- https://docs.datalust.co/docs/using-serilog
