---
name: integration-testing
description: >
  Integration testing with WebApplicationFactory, TestContainers, and test fixtures.
  Covers in-memory database setup, fixture sharing, and end-to-end test patterns.
  Trigger: integration test, WebApplicationFactory, TestContainers, fixture.
metadata:
  category: testing
  agent: test-engineer
---

# Integration Testing — WebApplicationFactory & TestContainers

## Core Principles

- `WebApplicationFactory<Program>` creates an in-process test server
- `IClassFixture<T>` shares expensive resources across tests
- TestContainers spin up real databases in Docker for realistic tests
- Respawn resets database state between tests (fast, preserves schema)
- Override services in `ConfigureTestServices` for test-specific behavior
- Integration tests verify the full pipeline: HTTP/gRPC -> Handler -> DB

## Key Patterns

### Custom WebApplicationFactory

```csharp
namespace {Company}.{Domain}.Tests.Integration;

public sealed class TestWebAppFactory : WebApplicationFactory<Program>
{
    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureTestServices(services =>
        {
            // Replace real DB with in-memory
            services.RemoveAll<DbContextOptions<ApplicationDbContext>>();
            services.AddDbContext<ApplicationDbContext>(options =>
                options.UseInMemoryDatabase("TestDb_" + Guid.NewGuid()));

            // Replace external services with fakes
            services.RemoveAll<IServiceBusPublisher>();
            services.AddSingleton<IServiceBusPublisher, FakeServiceBusPublisher>();
        });

        builder.UseEnvironment("Testing");
    }
}
```

### Test with Fixture

```csharp
namespace {Company}.{Domain}.Tests.Integration;

public sealed class OrderIntegrationTests(TestWebAppFactory factory)
    : IClassFixture<TestWebAppFactory>
{
    [Fact]
    public async Task CreateOrder_ShouldPersistAndReturnId()
    {
        // Arrange
        using var scope = factory.Services.CreateScope();
        var mediator = scope.ServiceProvider.GetRequiredService<IMediator>();

        var command = new CreateOrderCommand("Test Customer", 100m, []);

        // Act
        var result = await mediator.Send(command);

        // Assert
        result.Id.Should().NotBeEmpty();

        var db = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
        var events = await db.Set<Event<OrderEventData>>()
            .Where(e => e.AggregateId == result.Id)
            .ToListAsync();
        events.Should().HaveCount(1);
    }
}
```

### TestContainers for Real Database

```csharp
namespace {Company}.{Domain}.Tests.Integration;

public sealed class SqlServerFixture : IAsyncLifetime
{
    private readonly MsSqlContainer _container = new MsSqlBuilder()
        .WithImage("mcr.microsoft.com/mssql/server:2022-latest")
        .Build();

    public string ConnectionString => _container.GetConnectionString();

    public async Task InitializeAsync()
    {
        await _container.StartAsync();
    }

    public async Task DisposeAsync()
    {
        await _container.DisposeAsync();
    }
}

public sealed class RealDbWebAppFactory(SqlServerFixture sqlFixture)
    : WebApplicationFactory<Program>, IClassFixture<SqlServerFixture>
{
    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureTestServices(services =>
        {
            services.RemoveAll<DbContextOptions<ApplicationDbContext>>();
            services.AddDbContext<ApplicationDbContext>(options =>
                options.UseSqlServer(sqlFixture.ConnectionString));
        });
    }
}
```

### Database Reset with Respawn

```csharp
public sealed class DatabaseResetFixture : IAsyncLifetime
{
    private Respawner _respawner = null!;
    private string _connectionString = null!;

    public async Task InitializeAsync()
    {
        _respawner = await Respawner.CreateAsync(_connectionString, new RespawnerOptions
        {
            TablesToIgnore = ["__EFMigrationsHistory"],
            WithReseed = true
        });
    }

    public async Task ResetAsync()
    {
        await _respawner.ResetAsync(_connectionString);
    }

    public Task DisposeAsync() => Task.CompletedTask;
}
```

### gRPC Integration Test

```csharp
[Fact]
public async Task CreateOrder_ViaGrpc_ShouldSucceed()
{
    // Arrange
    using var channel = GrpcChannel.ForAddress(
        factory.Server.BaseAddress!,
        new GrpcChannelOptions { HttpHandler = factory.Server.CreateHandler() });

    var client = new OrderCommands.OrderCommandsClient(channel);

    // Act
    var response = await client.CreateOrderAsync(new CreateOrderRequest
    {
        CustomerName = "Test",
        Total = 100.0
    });

    // Assert
    response.OrderId.Should().NotBeNullOrEmpty();
    response.Sequence.Should().Be(1);
}
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Shared mutable database state | Use Respawn or unique DB per test |
| Real external services in tests | Replace with fakes via ConfigureTestServices |
| Testing only happy paths | Include error cases and edge cases |
| Slow test startup | Use IClassFixture for shared resources |

## Detect Existing Patterns

```bash
# Find WebApplicationFactory
grep -r "WebApplicationFactory" --include="*.cs" tests/

# Find TestContainers
grep -r "TestcontainersBuilder\|MsSqlContainer" --include="*.cs" tests/

# Find IClassFixture
grep -r "IClassFixture" --include="*.cs" tests/

# Find Respawn
grep -r "Respawner\|Respawn" --include="*.cs" tests/
```

## Adding to Existing Project

1. **Use existing `TestWebAppFactory`** — extend rather than creating new
2. **Follow fixture sharing** patterns with `IClassFixture<T>`
3. **Match database strategy** — in-memory vs TestContainers
4. **Add test helpers** for common operations (create, query, assert)
5. **Run integration tests separately** from unit tests (test categories)
