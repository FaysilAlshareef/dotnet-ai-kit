---
name: aspire-testing
description: "Writes end-to-end tests over a running .NET Aspire application graph with Aspire.Hosting.Testing, spinning up the real AppHost and exercising resources through service discovery. Use when validating cross-service behaviour against the orchestrated topology. Do NOT use for single-service in-process tests (use integration-testing or unit-testing) or for wiring the integrations under test (use aspire-integrations)."
metadata:
  category: "devops"
  agent: "aspire-architect"
---
# Aspire End-to-End Testing

`Aspire.Hosting.Testing` boots the actual AppHost in a test, so tests run against the real topology (containers, service discovery, references) rather than mocks. Use it for the handful of high-value cross-service flows, not for every unit.

## Conventions
- Reference `Aspire.Hosting.Testing` (xUnit by default; NUnit/MSTest also work) and the AppHost project from the test project.
- Build the host with `DistributedApplicationTestingBuilder.CreateAsync<Projects.MyApp_AppHost>()`, then `await app.StartAsync()`.
- Get HTTP clients by **resource name** via `app.CreateHttpClient("orders-api")` — service discovery resolves the address; never hardcode ports.
- Gate on readiness before asserting: `await app.ResourceNotifications.WaitForResourceHealthyAsync("orders-api")` so containers/dependencies are up.
- Share one started host across a test class with a fixture/`IAsyncLifetime`; starting the graph per test is slow.
- Mark these tests as a separate "e2e" category/trait so unit runs stay fast and CI can opt in where Docker is available.

## Example
```csharp
public sealed class OrdersGraphTests : IAsyncLifetime
{
    private DistributedApplication _app = null!;

    public async Task InitializeAsync()
    {
        var builder = await DistributedApplicationTestingBuilder
            .CreateAsync<Projects.MyApp_AppHost>();
        _app = await builder.BuildAsync();
        await _app.StartAsync();
    }

    [Fact]
    public async Task CreateOrder_PersistsAndReturns201()
    {
        await _app.ResourceNotifications
            .WaitForResourceHealthyAsync("orders-api");

        var client = _app.CreateHttpClient("orders-api");
        var response = await client.PostAsJsonAsync("/orders",
            new { customerName = "Acme" });

        Assert.Equal(HttpStatusCode.Created, response.StatusCode);
    }

    public async Task DisposeAsync() => await _app.DisposeAsync();
}
```

## Anti-Patterns
- Hardcoding `http://localhost:5xxx` instead of `CreateHttpClient(name)`.
- Asserting before `WaitForResourceHealthyAsync`, causing flaky connection errors.
- Starting the full graph per `[Fact]` instead of once per class.
- Using e2e graph tests where a fast in-process integration test would do.

## References
- https://learn.microsoft.com/en-us/dotnet/aspire/testing/write-your-first-test
