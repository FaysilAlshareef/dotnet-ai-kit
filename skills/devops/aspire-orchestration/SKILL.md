---
name: aspire-orchestration
description: >
  .NET Aspire for local development orchestration and service defaults. Covers
  AppHost configuration, service discovery, and local resource provisioning.
  Trigger: Aspire, orchestration, service defaults, local development, AppHost.
metadata:
  category: devops
  agent: devops-engineer
---

# Aspire Orchestration — Local Development

## Core Principles

- `.NET Aspire` orchestrates all microservices for local development
- `AppHost` project defines the service topology
- `ServiceDefaults` project provides shared configuration (OpenTelemetry, health checks)
- Service discovery replaces hardcoded URLs locally
- Aspire Dashboard provides observability out of the box
- Resource provisioning: SQL Server, Cosmos DB emulator, Service Bus emulator

## Key Patterns

### AppHost Project

```csharp
// {Company}.{Domain}.AppHost/Program.cs

var builder = DistributedApplication.CreateBuilder(args);

// Infrastructure resources
var sqlServer = builder.AddSqlServer("sql")
    .WithDataVolume("sql-data");

var commandDb = sqlServer.AddDatabase("command-db");
var queryDb = sqlServer.AddDatabase("query-db");

var serviceBus = builder.AddAzureServiceBus("servicebus")
    .RunAsEmulator();

// Command service
var commandService = builder.AddProject<Projects.{Company}_{Domain}_Command>("command")
    .WithReference(commandDb)
    .WithReference(serviceBus);

// Query service
var queryService = builder.AddProject<Projects.{Company}_{Domain}_Query>("query")
    .WithReference(queryDb)
    .WithReference(serviceBus);

// Processor service
var processor = builder.AddProject<Projects.{Company}_{Domain}_Processor>("processor")
    .WithReference(serviceBus)
    .WithReference(commandService)
    .WithReference(queryService);

// Gateway
var gateway = builder.AddProject<Projects.{Company}_{Domain}_Gateway>("gateway")
    .WithReference(commandService)
    .WithReference(queryService)
    .WithExternalHttpEndpoints();

builder.Build().Run();
```

### Service Defaults Project

```csharp
// {Company}.{Domain}.ServiceDefaults/Extensions.cs

public static class Extensions
{
    public static IHostApplicationBuilder AddServiceDefaults(
        this IHostApplicationBuilder builder)
    {
        builder.ConfigureOpenTelemetry();
        builder.AddDefaultHealthChecks();
        builder.Services.AddServiceDiscovery();

        builder.Services.ConfigureHttpClientDefaults(http =>
        {
            http.AddStandardResilienceHandler();
            http.AddServiceDiscovery();
        });

        return builder;
    }

    public static IHostApplicationBuilder ConfigureOpenTelemetry(
        this IHostApplicationBuilder builder)
    {
        builder.Logging.AddOpenTelemetry(logging =>
        {
            logging.IncludeFormattedMessage = true;
            logging.IncludeScopes = true;
        });

        builder.Services.AddOpenTelemetry()
            .WithMetrics(metrics =>
            {
                metrics.AddAspNetCoreInstrumentation()
                    .AddHttpClientInstrumentation()
                    .AddRuntimeInstrumentation();
            })
            .WithTracing(tracing =>
            {
                tracing.AddAspNetCoreInstrumentation()
                    .AddGrpcClientInstrumentation()
                    .AddHttpClientInstrumentation();
            });

        builder.AddOpenTelemetryExporters();
        return builder;
    }

    public static IHostApplicationBuilder AddDefaultHealthChecks(
        this IHostApplicationBuilder builder)
    {
        builder.Services.AddHealthChecks()
            .AddCheck("self", () => HealthCheckResult.Healthy());

        return builder;
    }
}
```

### Using ServiceDefaults in a Service

```csharp
// Program.cs of any service
var builder = WebApplication.CreateBuilder(args);

builder.AddServiceDefaults();

// ... service-specific configuration ...

var app = builder.Build();

app.MapDefaultEndpoints(); // Maps /health/ready and /health/live
```

### Cosmos DB with Aspire

```csharp
// In AppHost
var cosmos = builder.AddAzureCosmosDB("cosmos")
    .RunAsEmulator();

var cosmosDb = cosmos.AddDatabase("domain-db");

builder.AddProject<Projects.CosmosQuery>("cosmos-query")
    .WithReference(cosmosDb);
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Hardcoded connection strings locally | Use Aspire service discovery |
| Running infrastructure manually | Use Aspire to provision resources |
| Separate observability setup per service | Use ServiceDefaults project |
| Missing health endpoints | Call `AddServiceDefaults()` + `MapDefaultEndpoints()` |

## Detect Existing Patterns

```bash
# Find AppHost project
find . -name "*AppHost*" -type d

# Find ServiceDefaults
find . -name "*ServiceDefaults*" -type d

# Find Aspire references
grep -r "AddServiceDefaults\|DistributedApplication" --include="*.cs" src/

# Find Aspire packages
grep -r "Aspire" --include="*.csproj" src/
```

## Adding to Existing Project

1. **Check for existing AppHost** project before creating one
2. **Reference existing `ServiceDefaults`** project from new services
3. **Add new service** with `AddProject<T>` and appropriate references
4. **Use Aspire dashboard** for local observability and debugging
5. **Run emulators** for Service Bus and Cosmos DB locally
