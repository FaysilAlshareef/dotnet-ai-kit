# Testing Patterns

Testing patterns for .NET microservice and generic architectures.
Covers CustomConstructorFaker, assertion extensions, WebApplicationFactory, full-cycle tests, and BenchmarkDotNet.

---

## Test Project Structure

```
tests/
├── {Company}.{Domain}.UnitTests/
│   ├── Domain/
│   │   ├── Aggregates/
│   │   └── ValueObjects/
│   ├── Application/
│   │   ├── Handlers/
│   │   └── Validators/
│   └── Fakers/
├── {Company}.{Domain}.IntegrationTests/
│   ├── Fixtures/
│   ├── Endpoints/
│   └── FullCycle/
└── {Company}.{Domain}.Benchmarks/
    └── Benchmarks/
```

---

## CustomConstructorFaker

Extends Bogus to support types with private setters and constructor-based initialization. Used for creating test data that matches the domain model constraints.

```csharp
using Bogus;

/// <summary>
/// Base faker that creates objects using a private parameterless constructor,
/// then sets properties via reflection. Useful for domain entities with
/// private setters that are normally constructed from events.
/// </summary>
public abstract class CustomConstructorFaker<T> : Faker<T> where T : class
{
    protected CustomConstructorFaker() : base()
    {
        CustomInstantiator(f =>
        {
            // Use reflection to invoke private parameterless constructor
            var instance = (T)Activator.CreateInstance(
                typeof(T),
                System.Reflection.BindingFlags.NonPublic |
                System.Reflection.BindingFlags.Instance,
                null, null, null)!;
            return instance;
        });
    }
}
```

### Domain Entity Fakers

```csharp
public sealed class OrderFaker : CustomConstructorFaker<Order>
{
    public OrderFaker()
    {
        RuleFor(o => o.Id, f => f.Random.Guid());
        RuleFor(o => o.CustomerName, f => f.Person.FullName);
        RuleFor(o => o.Total, f => f.Finance.Amount(10, 10000));
        RuleFor(o => o.Sequence, f => f.Random.Int(1, 100));
        RuleFor(o => o.Status, f => f.PickRandom<OrderStatus>());
    }
}

public sealed class OrderItemFaker : CustomConstructorFaker<OrderItem>
{
    public OrderItemFaker()
    {
        RuleFor(i => i.Id, f => f.Random.Guid());
        RuleFor(i => i.ProductName, f => f.Commerce.ProductName());
        RuleFor(i => i.Quantity, f => f.Random.Int(1, 50));
        RuleFor(i => i.UnitPrice, f => f.Finance.Amount(1, 500));
    }
}
```

### Event Data Fakers

```csharp
public sealed class OrderCreatedDataFaker : Faker<OrderCreatedData>
{
    public OrderCreatedDataFaker()
    {
        CustomInstantiator(f => new OrderCreatedData(
            CustomerName: f.Person.FullName,
            Total: f.Finance.Amount(10, 10000),
            Items: new OrderItemDataFaker().Generate(f.Random.Int(1, 5))
        ));
    }
}

public sealed class EventFaker<TData> : Faker<Event<TData>> where TData : IEventData
{
    public EventFaker(string eventType, Faker<TData> dataFaker)
    {
        RuleFor(e => e.AggregateId, f => f.Random.Guid());
        RuleFor(e => e.Sequence, f => f.Random.Int(1, 100));
        RuleFor(e => e.Type, eventType);
        RuleFor(e => e.DateTime, f => f.Date.Recent());
        RuleFor(e => e.Version, 1);
        RuleFor(e => e.Data, f => dataFaker.Generate());
    }
}
```

---

## Assertion Extensions

Typed assertion helpers that compare domain entities field by field with clear error messages.

```csharp
public static class OrderAssertions
{
    public static void AssertEquality(this Order actual, Order expected)
    {
        Assert.Equal(expected.Id, actual.Id);
        Assert.Equal(expected.CustomerName, actual.CustomerName);
        Assert.Equal(expected.Total, actual.Total);
        Assert.Equal(expected.Sequence, actual.Sequence);
        Assert.Equal(expected.Status, actual.Status);
    }

    public static void AssertCreatedFrom(this Order actual, Event<OrderCreatedData> @event)
    {
        Assert.Equal(@event.AggregateId, actual.Id);
        Assert.Equal(@event.Data.CustomerName, actual.CustomerName);
        Assert.Equal(@event.Data.Total, actual.Total);
        Assert.Equal(@event.Sequence, actual.Sequence);
    }

    public static void AssertUpdatedFrom(this Order actual, Event<OrderUpdatedData> @event)
    {
        Assert.Equal(@event.Sequence, actual.Sequence);
        if (@event.Data.CustomerName is not null)
            Assert.Equal(@event.Data.CustomerName, actual.CustomerName);
        Assert.Equal(@event.Data.Total, actual.Total);
    }
}
```

### Collection Assertion Extensions

```csharp
public static class CollectionAssertions
{
    public static void AssertEquivalent<T>(
        this IReadOnlyList<T> actual,
        IReadOnlyList<T> expected,
        Action<T, T> assertItem)
    {
        Assert.Equal(expected.Count, actual.Count);
        for (int i = 0; i < expected.Count; i++)
        {
            assertItem(actual[i], expected[i]);
        }
    }
}
```

---

## WebApplicationFactory

Custom factory for integration testing with in-memory database and mocked services.

### Base Test Fixture

```csharp
public sealed class {Domain}ApiFactory : WebApplicationFactory<Program>, IAsyncLifetime
{
    private readonly MsSqlContainer _dbContainer = new MsSqlBuilder()
        .WithImage("mcr.microsoft.com/mssql/server:2022-latest")
        .Build();

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureServices(services =>
        {
            // Replace SQL Server with test container
            services.RemoveAll<DbContextOptions<ApplicationDbContext>>();
            services.AddDbContext<ApplicationDbContext>(options =>
                options.UseSqlServer(_dbContainer.GetConnectionString()));

            // Replace Service Bus with in-memory stub
            services.RemoveAll<ServiceBusClient>();
            services.AddSingleton<ServiceBusClient>(new FakeServiceBusClient());

            // Replace background services
            services.RemoveAll<IHostedService>();
        });

        builder.UseEnvironment("Testing");
    }

    public async Task InitializeAsync()
    {
        await _dbContainer.StartAsync();

        // Apply migrations
        using var scope = Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
        await db.Database.MigrateAsync();
    }

    public new async Task DisposeAsync()
    {
        await _dbContainer.DisposeAsync();
    }
}
```

### Using the Factory

```csharp
public sealed class OrderEndpointTests(
    {Domain}ApiFactory factory) : IClassFixture<{Domain}ApiFactory>
{
    private readonly HttpClient _client = factory.CreateClient();

    [Fact]
    public async Task CreateOrder_ReturnsCreated()
    {
        // Arrange
        var request = new CreateOrderRequest("John Doe", 99.99m);

        // Act
        var response = await _client.PostAsJsonAsync("/api/v1/orders", request);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Created);
        var order = await response.Content.ReadFromJsonAsync<OrderResponse>();
        order.Should().NotBeNull();
        order!.CustomerName.Should().Be("John Doe");
    }
}
```

---

## Full-Cycle Tests (Microservice)

End-to-end tests that verify the complete event sourcing flow:
Command -> Event -> Outbox -> (simulated publish) -> Query Handler -> Verify Projection.

```csharp
public sealed class OrderFullCycleTests(
    {Domain}ApiFactory factory) : IClassFixture<{Domain}ApiFactory>
{
    [Fact]
    public async Task CreateOrder_ProducesEvent_UpdatesProjection()
    {
        using var scope = factory.Services.CreateScope();
        var mediator = scope.ServiceProvider.GetRequiredService<IMediator>();
        var db = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();

        // 1. Execute command
        var command = new CreateOrderCommand("Jane Smith", 150.00m);
        var output = await mediator.Send(command);

        // 2. Verify event was stored
        var events = await db.Events
            .Where(e => e.AggregateId == output.Id)
            .ToListAsync();
        Assert.Single(events);
        Assert.Equal(EventTypes.OrderCreated, events[0].Type);

        // 3. Verify outbox message was created
        var outboxMessages = await db.OutboxMessages
            .Where(m => m.EventId == output.Id)
            .ToListAsync();
        Assert.Single(outboxMessages);
        Assert.Null(outboxMessages[0].PublishedAt);

        // 4. Simulate query-side event processing
        var eventBody = outboxMessages[0].Body;
        var @event = JsonConvert.DeserializeObject<Event<OrderCreatedData>>(eventBody)!;

        // Use query-side handler to apply the event
        var queryHandler = new OrderCreatedHandler(db);
        var result = await queryHandler.Handle(@event, CancellationToken.None);
        Assert.True(result);

        // 5. Verify projection was updated
        var order = await db.Orders.FindAsync(output.Id);
        Assert.NotNull(order);
        Assert.Equal("Jane Smith", order.CustomerName);
        Assert.Equal(150.00m, order.Total);
        Assert.Equal(1, order.Sequence);
    }

    [Fact]
    public async Task UpdateOrder_WithSequenceCheck_MaintainsConsistency()
    {
        using var scope = factory.Services.CreateScope();
        var mediator = scope.ServiceProvider.GetRequiredService<IMediator>();
        var db = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();

        // Create initial order
        var createResult = await mediator.Send(
            new CreateOrderCommand("Alice", 100.00m));

        // Simulate creation event on query side
        var createOutbox = await db.OutboxMessages
            .FirstAsync(m => m.EventId == createResult.Id);
        var createEvent = JsonConvert.DeserializeObject<Event<OrderCreatedData>>(
            createOutbox.Body)!;
        await new OrderCreatedHandler(db).Handle(createEvent, CancellationToken.None);

        // Update the order
        var updateResult = await mediator.Send(
            new UpdateOrderCommand(createResult.Id, "Alice Updated", 200.00m));

        // Simulate update event on query side
        var updateOutbox = await db.OutboxMessages
            .OrderByDescending(m => m.CreatedAt)
            .FirstAsync(m => m.EventId == createResult.Id);
        var updateEvent = JsonConvert.DeserializeObject<Event<OrderUpdatedData>>(
            updateOutbox.Body)!;
        await new OrderUpdatedHandler(db).Handle(updateEvent, CancellationToken.None);

        // Verify final state
        var order = await db.Orders.FindAsync(createResult.Id);
        Assert.Equal("Alice Updated", order!.CustomerName);
        Assert.Equal(200.00m, order.Total);
        Assert.Equal(2, order.Sequence);
    }
}
```

---

## Unit Test Patterns

### Command Handler Tests

```csharp
public sealed class CreateOrderHandlerTests
{
    private readonly Mock<ICommitEventService<IOrderEventData>> _commitService = new();

    [Fact]
    public async Task Handle_ValidCommand_CommitsEventsAndReturnsOutput()
    {
        // Arrange
        var handler = new CreateOrderHandler(_commitService.Object);
        var command = new CreateOrderCommand("John", 99.99m);

        // Act
        var result = await handler.Handle(command, CancellationToken.None);

        // Assert
        Assert.NotEqual(Guid.Empty, result.Id);
        Assert.Equal(1, result.Sequence);

        _commitService.Verify(
            x => x.CommitAsync(
                It.IsAny<Guid>(),
                It.Is<IReadOnlyList<Event<IOrderEventData>>>(
                    events => events.Count == 1 &&
                              events[0].Type == EventTypes.OrderCreated),
                It.IsAny<CancellationToken>()),
            Times.Once);
    }
}
```

### Validator Tests

```csharp
public sealed class CreateOrderValidatorTests
{
    private readonly CreateOrderValidator _validator = new();

    [Fact]
    public void Validate_EmptyCustomerName_HasError()
    {
        var command = new CreateOrderCommand("", 99.99m);
        var result = _validator.Validate(command);

        Assert.False(result.IsValid);
        Assert.Contains(result.Errors,
            e => e.PropertyName == nameof(CreateOrderCommand.CustomerName));
    }

    [Theory]
    [InlineData(0)]
    [InlineData(-1)]
    public void Validate_InvalidTotal_HasError(decimal total)
    {
        var command = new CreateOrderCommand("John", total);
        var result = _validator.Validate(command);

        Assert.False(result.IsValid);
        Assert.Contains(result.Errors,
            e => e.PropertyName == nameof(CreateOrderCommand.Total));
    }

    [Fact]
    public void Validate_ValidCommand_NoErrors()
    {
        var command = new CreateOrderCommand("John", 99.99m);
        var result = _validator.Validate(command);

        Assert.True(result.IsValid);
    }
}
```

### Aggregate Tests

```csharp
public sealed class OrderAggregateTests
{
    [Fact]
    public void Create_ProducesOrderCreatedEvent()
    {
        var order = Order.Create("John", 99.99m);

        Assert.Single(order.UncommittedEvents);
        Assert.Equal(EventTypes.OrderCreated, order.UncommittedEvents[0].Type);
        Assert.Equal(1, order.Sequence);
        Assert.Equal("John", order.CustomerName);
    }

    [Fact]
    public void UpdateDetails_OnCancelledOrder_ThrowsDomainException()
    {
        var order = CreateCancelledOrder();

        var ex = Assert.Throws<DomainException>(
            () => order.UpdateDetails("New Name", 50m));
        Assert.Contains("cancelled", ex.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void LoadFromHistory_RestoresState()
    {
        // Arrange — create events
        var aggregateId = Guid.NewGuid();
        var events = new[]
        {
            new Event<OrderCreatedData>
            {
                AggregateId = aggregateId, Sequence = 1,
                Type = EventTypes.OrderCreated,
                Data = new OrderCreatedData("John", 100, [])
            },
            new Event<OrderUpdatedData>
            {
                AggregateId = aggregateId, Sequence = 2,
                Type = EventTypes.OrderUpdated,
                Data = new OrderUpdatedData("Jane", 200)
            }
        };

        // Act
        var order = new Order();
        order.LoadFromHistory(events);

        // Assert
        Assert.Equal(aggregateId, order.Id);
        Assert.Equal("Jane", order.CustomerName);
        Assert.Equal(200, order.Total);
        Assert.Equal(2, order.Sequence);
        Assert.Empty(order.UncommittedEvents); // Replayed, not new
    }
}
```

---

## BenchmarkDotNet

Performance benchmarks for critical paths.

```csharp
[MemoryDiagnoser]
[SimpleJob(RuntimeMoniker.Net90)]
public class EventSerializationBenchmarks
{
    private Event<OrderCreatedData> _event = null!;
    private string _serialized = null!;

    [GlobalSetup]
    public void Setup()
    {
        _event = new EventFaker<OrderCreatedData>(
            EventTypes.OrderCreated,
            new OrderCreatedDataFaker()).Generate();
        _serialized = JsonConvert.SerializeObject(_event, EventSerializerSettings.Default);
    }

    [Benchmark(Baseline = true)]
    public string Serialize_Newtonsoft()
    {
        return JsonConvert.SerializeObject(_event, EventSerializerSettings.Default);
    }

    [Benchmark]
    public Event<OrderCreatedData> Deserialize_Newtonsoft()
    {
        return JsonConvert.DeserializeObject<Event<OrderCreatedData>>(
            _serialized, EventSerializerSettings.Default)!;
    }
}

// Run: dotnet run -c Release --project tests/{Company}.{Domain}.Benchmarks
```

---

## Test Naming Convention

Follow the pattern: `{Method}_{Scenario}_{ExpectedBehavior}`

```
CreateOrder_ValidRequest_ReturnsCreated
CreateOrder_EmptyCustomerName_ReturnsBadRequest
Handle_DuplicateEvent_ReturnsTrue (idempotent)
Handle_SequenceGap_ReturnsFalse (retry)
LoadFromHistory_MultipleEvents_RestoresFinalState
```

---

## Related Documents

- `knowledge/event-sourcing-flow.md` — Patterns being tested
- `knowledge/concurrency-patterns.md` — Concurrency testing
- `knowledge/deployment-patterns.md` — CI/CD test integration
