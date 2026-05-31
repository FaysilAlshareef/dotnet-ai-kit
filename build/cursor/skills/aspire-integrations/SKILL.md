---
name: aspire-integrations
description: "Configures .NET Aspire 13.1 hosting integration packages (Redis, Postgres, RabbitMQ, Azure Service Bus) and wires resources together with WithReference. Use when adding a backing service to the AppHost and injecting its connection into a project. Do NOT use for AppHost topology basics or service discovery (use aspire-orchestration), publishing/deployment (use aspire-deployment), or end-to-end graph tests (use aspire-testing)."
---
# Aspire Hosting Integrations

Add backing services to the AppHost as resources, then inject them into consuming projects with `WithReference`. Aspire writes connection strings/config into each consumer automatically — no hardcoded URLs.

## Conventions
- Install hosting packages in the **AppHost** project only: `Aspire.Hosting.Redis`, `Aspire.Hosting.PostgreSQL`, `Aspire.Hosting.RabbitMQ`, `Aspire.Hosting.Azure.ServiceBus`.
- Default to OSS containers (Redis, Postgres, RabbitMQ) for local dev; treat **Azure Service Bus** as the cloud opt-in via `.RunAsEmulator()` locally / managed in the cloud.
- Persist dev state with `.WithDataVolume()` so containers survive restarts.
- Every resource a project needs must be passed via `.WithReference(resource)`; add `.WaitFor(resource)` so the consumer starts only after the dependency is healthy.
- Name resources in lowercase-kebab (`cache`, `orders-db`, `bus`); the name becomes the connection-string key (`builder.AddRedisClient("cache")`).
- Read the injected connection in the consumer with the matching client integration package (`Aspire.StackExchange.Redis`, `Aspire.Npgsql`, etc.) — never parse env vars by hand.

## Example
```csharp
// AppHost/Program.cs
var builder = DistributedApplication.CreateBuilder(args);

var cache = builder.AddRedis("cache").WithDataVolume();
var ordersDb = builder.AddPostgres("pg").WithDataVolume().AddDatabase("orders-db");
var bus = builder.AddRabbitMQ("bus").WithDataVolume();          // OSS default
// var bus = builder.AddAzureServiceBus("bus").RunAsEmulator();  // cloud opt-in

builder.AddProject<Projects.Orders_Api>("orders-api")
    .WithReference(cache)
    .WithReference(ordersDb)
    .WithReference(bus)
    .WaitFor(ordersDb)
    .WaitFor(bus);

builder.Build().Run();

// Orders.Api/Program.cs — connection injected by name, not hardcoded
builder.AddRedisClient("cache");
builder.AddNpgsqlDataSource("orders-db");
```

## Anti-Patterns
- Adding the integration package to the consumer project instead of the AppHost.
- Hardcoding a connection string in `appsettings.json` that Aspire already injects.
- Referencing a resource without `WaitFor`, causing startup races against an unready dependency.
- Defaulting to a commercial/cloud broker when an OSS container covers local dev.

## References
- https://learn.microsoft.com/en-us/dotnet/aspire/fundamentals/integrations-overview
