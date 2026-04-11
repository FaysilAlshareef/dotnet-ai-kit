---
name: opentelemetry
description: >
  Use when integrating OpenTelemetry for distributed tracing, metrics, or OTLP exporters.
metadata:
  category: observability
  agent: devops-engineer
  when-to-use: "When configuring OpenTelemetry tracing, metrics, or OTLP exporters"
---

# OpenTelemetry Traces & Metrics

## Core Principles

- Instrument all layers: HTTP requests, database calls, HTTP client calls
- Use custom `ActivitySource` for application-level tracing
- Use `IMeterFactory` for DI-friendly custom metrics
- Export to OTLP-compatible backends (Aspire Dashboard, Jaeger, Grafana, Seq)
- Set service name and version for clear identification in traces

## Patterns

### Full OpenTelemetry Setup

```csharp
// Program.cs
var serviceName = "{Domain}Service";
var serviceVersion = typeof(Program).Assembly
    .GetName().Version?.ToString() ?? "1.0.0";

builder.Services.AddOpenTelemetry()
    .ConfigureResource(resource => resource
        .AddService(serviceName, serviceVersion: serviceVersion))
    .WithTracing(tracing => tracing
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        .AddEntityFrameworkCoreInstrumentation()
        .AddSource(serviceName) // custom ActivitySource
        .AddOtlpExporter(options =>
        {
            options.Endpoint = new Uri(
                builder.Configuration["Otlp:Endpoint"]
                ?? "http://localhost:4317");
        }))
    .WithMetrics(metrics => metrics
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        .AddRuntimeInstrumentation()
        .AddMeter(serviceName) // custom Meter
        .AddOtlpExporter());
```

### Custom Tracing with ActivitySource

```csharp
public sealed class OrderService(
    IOrderRepository repository,
    ILogger<OrderService> logger)
{
    // Static ActivitySource per service
    private static readonly ActivitySource ActivitySource =
        new("{Domain}Service");

    public async Task<Order> CreateOrderAsync(
        CreateOrderCommand command, CancellationToken ct)
    {
        // Start a new activity (span)
        using var activity = ActivitySource.StartActivity(
            "CreateOrder", ActivityKind.Internal);

        // Add tags (attributes) for searchability
        activity?.SetTag("order.customer", command.CustomerName);
        activity?.SetTag("order.item_count", command.Items.Count);

        var order = Order.Create(command.CustomerName);

        foreach (var item in command.Items)
        {
            using var itemActivity = ActivitySource.StartActivity(
                "AddOrderItem");
            itemActivity?.SetTag("product.id",
                item.ProductId.ToString());
            order.AddItem(item.ProductId, item.Quantity);
        }

        repository.Add(order);

        activity?.SetTag("order.id", order.Id.ToString());
        activity?.SetTag("order.total", order.Total);
        activity?.SetStatus(ActivityStatusCode.Ok);

        logger.LogInformation(
            "Created order {OrderId}", order.Id);

        return order;
    }
}
```

### Custom Metrics with IMeterFactory

```csharp
public sealed class OrderMetrics
{
    private readonly Counter<long> _ordersCreated;
    private readonly Counter<long> _ordersFailed;
    private readonly Histogram<double> _processingDuration;
    private readonly UpDownCounter<long> _activeOrders;

    public OrderMetrics(IMeterFactory meterFactory)
    {
        var meter = meterFactory.Create("{Domain}Service");

        _ordersCreated = meter.CreateCounter<long>(
            "orders.created",
            unit: "orders",
            description: "Number of orders created");

        _ordersFailed = meter.CreateCounter<long>(
            "orders.failed",
            unit: "orders",
            description: "Number of failed order operations");

        _processingDuration = meter.CreateHistogram<double>(
            "orders.processing.duration",
            unit: "ms",
            description: "Order processing duration");

        _activeOrders = meter.CreateUpDownCounter<long>(
            "orders.active",
            unit: "orders",
            description: "Currently active orders");
    }

    public void OrderCreated(string status) =>
        _ordersCreated.Add(1,
            new KeyValuePair<string, object?>("status", status));

    public void OrderFailed(string reason) =>
        _ordersFailed.Add(1,
            new KeyValuePair<string, object?>("reason", reason));

    public void RecordProcessingDuration(double durationMs) =>
        _processingDuration.Record(durationMs);

    public void OrderActivated() => _activeOrders.Add(1);
    public void OrderCompleted() => _activeOrders.Add(-1);
}

// Register as singleton
builder.Services.AddSingleton<OrderMetrics>();
```

### Using Metrics in Handlers

```csharp
internal sealed class CreateOrderHandler(
    IOrderRepository repository,
    IUnitOfWork unitOfWork,
    OrderMetrics metrics)
    : IRequestHandler<CreateOrderCommand, Result<Guid>>
{
    public async Task<Result<Guid>> Handle(
        CreateOrderCommand request, CancellationToken ct)
    {
        var sw = Stopwatch.StartNew();

        try
        {
            var order = Order.Create(request.CustomerName);
            repository.Add(order);
            await unitOfWork.SaveChangesAsync(ct);

            metrics.OrderCreated("success");
            metrics.OrderActivated();

            return Result<Guid>.Success(order.Id);
        }
        catch (Exception ex)
        {
            metrics.OrderFailed(ex.GetType().Name);
            throw;
        }
        finally
        {
            metrics.RecordProcessingDuration(
                sw.Elapsed.TotalMilliseconds);
        }
    }
}
```

### Baggage Propagation

```csharp
// Set baggage for cross-service context propagation
Activity.Current?.SetBaggage("tenant.id", tenantId);
Activity.Current?.SetBaggage("user.id", userId);

// Read baggage in downstream service
var tenantId = Activity.Current?.GetBaggageItem("tenant.id");
```

### Aspire Dashboard (Development)

```csharp
// appsettings.Development.json
{
  "Otlp": {
    "Endpoint": "http://localhost:4317"
  }
}

// Run Aspire Dashboard locally
// docker run --rm -p 18888:18888 -p 4317:18889 \
//   mcr.microsoft.com/dotnet/aspire-dashboard:latest
```

### Exporter Configuration

```csharp
// OTLP (default — works with Jaeger, Grafana Tempo, Aspire Dashboard)
.AddOtlpExporter(options =>
{
    options.Endpoint = new Uri("http://localhost:4317");
    options.Protocol = OtlpExportProtocol.Grpc;
})

// Console (development debugging)
.AddConsoleExporter()

// Prometheus (metrics only)
.WithMetrics(metrics => metrics
    .AddPrometheusExporter());
app.MapPrometheusScrapingEndpoint();
```

## Packages

```xml
<PackageReference Include="OpenTelemetry.Extensions.Hosting" />
<PackageReference Include="OpenTelemetry.Instrumentation.AspNetCore" />
<PackageReference Include="OpenTelemetry.Instrumentation.Http" />
<PackageReference Include="OpenTelemetry.Instrumentation.EntityFrameworkCore" />
<PackageReference Include="OpenTelemetry.Instrumentation.Runtime" />
<PackageReference Include="OpenTelemetry.Exporter.OpenTelemetryProtocol" />
<!-- Development -->
<PackageReference Include="OpenTelemetry.Exporter.Console" />
```

## Anti-Patterns

- Not setting service name (traces are unidentifiable)
- Creating a new ActivitySource per request (use static field)
- Creating meters in transient services (use IMeterFactory + singleton)
- Too many custom spans (noise in trace view)
- Not recording errors on activities (`SetStatus(Error)`)

## Detect Existing Patterns

1. Search for `OpenTelemetry` packages in `.csproj`
2. Look for `AddOpenTelemetry()` in `Program.cs`
3. Check for `ActivitySource` usage in service classes
4. Look for `IMeterFactory` or `Meter` usage
5. Check for `AddOtlpExporter` configuration

## Adding to Existing Project

1. **Install OpenTelemetry packages** for hosting, instrumentation, and export
2. **Configure** `AddOpenTelemetry()` with tracing and metrics
3. **Add built-in instrumentation** for ASP.NET Core, HttpClient, EF Core
4. **Create custom `ActivitySource`** for application-level tracing
5. **Create metrics class** with `IMeterFactory` for business metrics
6. **Configure exporter** to Aspire Dashboard (dev) or OTLP backend (prod)

## Decision Guide

| Signal | Use |
|--------|-----|
| Traces | Request flow across services, latency analysis |
| Metrics | Counters (orders/sec), histograms (latency p99) |
| Logs | Detailed event context (already via Serilog) |
| Baggage | Cross-service context (tenant ID, user ID) |

## References

- https://learn.microsoft.com/en-us/dotnet/core/diagnostics/observability-with-otel
- https://opentelemetry.io/docs/languages/dotnet/
