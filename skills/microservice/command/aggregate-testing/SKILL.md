---
name: dotnet-ai-aggregate-testing
description: >
  Testing patterns for event-sourced aggregates. Covers CustomConstructorFaker with Bogus,
  event faker patterns, assertion extensions, and integration test patterns with
  WebApplicationFactory, DbContextHelper, and GrpcClientHelper.
  Trigger: aggregate test, faker, test data, assertion, command testing.
category: microservice/command
agent: test-engineer
---

# Aggregate Testing -- CustomConstructorFaker and Test Patterns

## Core Principles

- `CustomConstructorFaker<T>` uses `RuntimeHelpers.GetUninitializedObject` to bypass private constructors
- Event fakers inherit from `CustomConstructorFaker<T>` and set properties via `RuleFor`
- Event data fakers also inherit from `CustomConstructorFaker<T>` for record types with constructors
- Assertion extensions compare protobuf requests to event data field-by-field
- Integration tests use `WebApplicationFactory<Program>`, `DbContextHelper`, and `GrpcClientHelper`
- Tests verify: events persisted in DB, outbox messages created, correct event data, exception behavior

## Key Patterns

### CustomConstructorFaker Base

```csharp
using Bogus;
using System.Runtime.CompilerServices;

namespace {Company}.{Domain}.Commands.Test.Fakers;

public class CustomConstructorFaker<T> : Faker<T> where T : class
{
    public CustomConstructorFaker()
    {
        CustomInstantiator(_ => Initialize());
    }

    private static T Initialize() =>
       RuntimeHelpers.GetUninitializedObject(typeof(T)) as T
           ?? throw new TypeLoadException();
}
```

Key details:
- Uses `RuntimeHelpers.GetUninitializedObject` to create instances without calling constructors
- This is necessary because event classes have primary constructors with required parameters
- The `Faker<T>` base class from Bogus then applies `RuleFor` to set properties

### Event Faker

Event fakers inherit from `CustomConstructorFaker<ConcreteEvent>` and compose a nested data faker.

```csharp
using {Company}.{Domain}.Commands.Domain.Enums;
using {Company}.{Domain}.Commands.Domain.Events.Orders;
using {Company}.{Domain}.Commands.Domain.Events.DataTypes;

namespace {Company}.{Domain}.Commands.Test.Fakers.EventsFakers.OrderEventsFakers;

public class OrderCreatedFaker : CustomConstructorFaker<OrderCreated>
{
    public OrderCreatedFaker(int itemsCount = 1)
    {
        RuleFor(r => r.AggregateId, f => f.Random.Guid());
        RuleFor(r => r.Sequence, 1);
        RuleFor(r => r.Version, 1);
        RuleFor(r => r.DateTime, DateTime.UtcNow);
        RuleFor(r => r.Data, new OrderCreatedDataFaker(itemsCount));
    }
}

public class OrderCreatedDataFaker : CustomConstructorFaker<OrderCreatedData>
{
    public OrderCreatedDataFaker(int itemsCount = 1)
    {
        RuleFor(r => r.CustomerName, r => r.Random.AlphaNumeric(20));
        RuleFor(r => r.Total, r => r.Finance.Amount(10, 10000));
        RuleFor(r => r.Status, OrderStatus.Pending);
        RuleFor(r => r.Items, GenerateList(itemsCount));
    }

    public static List<Guid> GenerateList(int count)
    {
        var items = new List<Guid>();
        for (int i = 0; i < count; i++)
        {
            items.Add(Guid.NewGuid());
        }
        return items;
    }
}
```

Key details:
- Fakers for **event data records** also use `CustomConstructorFaker` since records have constructors
- The event faker sets metadata (AggregateId, Sequence, Version, DateTime) plus a nested data faker
- Data fakers set each property of the record using `RuleFor`
- Helper methods like `GenerateList` create collection values

### Event Faker for Non-Creation Events

```csharp
public class OrderUpdatedFaker : CustomConstructorFaker<OrderUpdated>
{
    public OrderUpdatedFaker(Guid? aggregateId = null, int sequence = 2)
    {
        RuleFor(r => r.AggregateId, aggregateId ?? Guid.NewGuid());
        RuleFor(r => r.Sequence, sequence);
        RuleFor(r => r.Version, 1);
        RuleFor(r => r.DateTime, DateTime.UtcNow);
        RuleFor(r => r.Data, new OrderUpdatedDataFaker());
    }
}
```

### Assertion Extensions

Assert field-by-field equality between protobuf requests and persisted events.

```csharp
using {Company}.{Domain}.Commands.Domain.Entities;
using {Company}.{Domain}.Commands.Domain.Enums;
using {Company}.{Domain}.Commands.Domain.Events;
using {Company}.{Domain}.Commands.Domain.Events.Orders;
using {Company}.{Domain}.Commands.Domain.Events.DataTypes;
using {Company}.{Domain}.Commands.Test.Protos;

namespace {Company}.{Domain}.Commands.Test.Asserts;

public static class OrderAsserts
{
    public static void AssertEquality(
        this CreateOrderRequest request, OrderCreated? orderCreated)
    {
        Assert.NotNull(orderCreated);

        Assert.Equal(request.CustomerName, orderCreated.Data.CustomerName);
        Assert.Equal(request.Total, orderCreated.Data.Total);
        Assert.Equal(request.Items.Count(), orderCreated.Data.Items.Count());

        foreach (var item in request.Items.Select(Guid.Parse))
        {
            Assert.Contains(item, orderCreated.Data.Items);
        }

        Assert.Equal(DateTime.UtcNow, orderCreated.DateTime, TimeSpan.FromMinutes(1));
        Assert.Equal(EventType.OrderCreated, orderCreated.Type);
    }

    // Generic assertion for event-to-outbox relationship
    public static void AssertEquality<T, TData>(
        Event? @event,
        OutboxMessage? message
    ) where T : Event<TData>
      where TData : IEventData
    {
        Assert.NotNull(@event);
        Assert.NotNull(message);
        Assert.NotNull(message.Event);

        Assert.Equal(@event.Sequence, message.Event.Sequence);
        Assert.Equal(1, message.Event.Version);
        Assert.Equal(@event.Type, message.Event.Type);
        Assert.Equal(@event.DateTime, message.Event.DateTime, precision: TimeSpan.FromMinutes(1));
        Assert.Equal(@event.Id, message.Event.Id);
    }
}
```

### Integration Test -- Create Command

```csharp
using {Company}.{Domain}.Commands.Domain.Events.Orders;
using {Company}.{Domain}.Commands.Test.Asserts;
using {Company}.{Domain}.Commands.Test.Fakers.RequestFakers;
using {Company}.{Domain}.Commands.Test.Fakers.UserAccess;
using {Company}.{Domain}.Commands.Test.Helpers;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.EntityFrameworkCore;

namespace {Company}.{Domain}.Commands.Test.Tests.Orders;

public class CreateOrderTest : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly DbContextHelper _dbContextHelper;
    private readonly GrpcClientHelper _grpcClientHelper;

    public CreateOrderTest(WebApplicationFactory<Program> factory, ITestOutputHelper helper)
    {
        factory = factory.WithDefaultConfigurations(helper, services =>
        {
            services.SetUnitTestsDefaultEnvironment(factory);
        });

        _dbContextHelper = new DbContextHelper(factory.Services);
        _grpcClientHelper = new GrpcClientHelper(factory);
    }

    [Fact]
    public async Task CreateOrder_SendValidData_ReturnOrderCreated()
    {
        // Arrange
        var createOrderRequest = new CreateOrderRequestFaker().Generate();
        var accessClaims = new AccessClaimsFaker().Generate();

        // Act
        var response = await _grpcClientHelper.Send(
            r => r.CreateOrderAsync(createOrderRequest, accessClaims.GetMetadata()));

        var @event = await _dbContextHelper.Query(
            db => db.Events.OfType<OrderCreated>().SingleOrDefaultAsync());

        var outboxMessage = await _dbContextHelper.Query(
            db => db.OutboxMessages.Include(o => o.Event).SingleOrDefaultAsync());

        // Assert
        Assert.NotNull(@event);
        Assert.NotNull(outboxMessage);
        Assert.Equal(Phrases.OrderCreated, response.Message);

        createOrderRequest.AssertEquality(@event);
        Assert.Equal(@event.Id, outboxMessage.Event!.Id);
    }

    [Fact]
    public async Task CreateOrder_SendExistingOrder_ThrowAlreadyExist()
    {
        // Arrange -- insert existing event directly into DB
        var orderCreated = await _dbContextHelper.InsertAsync(
            new OrderCreatedFaker().Generate());

        var createOrderRequest = new CreateOrderRequestFaker()
            .RuleFor(r => r.Id, orderCreated.AggregateId.ToString())
            .Generate();

        var accessClaims = new AccessClaimsFaker().Generate();

        // Act
        var exception = await Assert.ThrowsAsync<RpcException>(
            async () => await _grpcClientHelper.Send(
                r => r.CreateOrderAsync(createOrderRequest, accessClaims.GetMetadata())));

        var @event = await _dbContextHelper.Query(
            db => db.Events.OfType<OrderCreated>().SingleOrDefaultAsync());

        // Assert
        Assert.NotNull(@event);
        Assert.Equal(Phrases.OrderAlreadyExist, exception.Status.Detail);
        Assert.Equal(StatusCode.AlreadyExists, exception.StatusCode);
    }
}
```

### Integration Test -- Update Command (Existing Aggregate)

```csharp
[Fact]
public async Task AddItems_SendValidData_ReturnItemsAdded()
{
    // Arrange -- create initial aggregate via event
    var orderCreated = await _dbContextHelper.InsertAsync(
        new OrderCreatedFaker(itemsCount: 2).Generate());

    var addItemsRequest = new AddItemsRequestFaker()
        .RuleFor(r => r.OrderId, orderCreated.AggregateId.ToString())
        .Generate();

    var accessClaims = new AccessClaimsFaker().Generate();

    // Act
    var response = await _grpcClientHelper.Send(
        r => r.AddItemsAsync(addItemsRequest, accessClaims.GetMetadata()));

    var events = await _dbContextHelper.Query(
        db => db.Events.Where(e => e.AggregateId == orderCreated.AggregateId)
                       .OrderBy(e => e.Sequence)
                       .ToListAsync());

    // Assert
    Assert.Equal(2, events.Count); // OrderCreated + OrderItemsAdded
    Assert.Equal(1, events[0].Sequence);
    Assert.Equal(2, events[1].Sequence);
}
```

### Test Helpers

```csharp
// DbContextHelper -- query the test database
public class DbContextHelper
{
    private readonly IServiceProvider _serviceProvider;

    public DbContextHelper(IServiceProvider serviceProvider)
    {
        _serviceProvider = serviceProvider;
    }

    public async Task<T?> Query<T>(Func<ApplicationDbContext, Task<T?>> query)
    {
        using var scope = _serviceProvider.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
        return await query(db);
    }

    public async Task<T> InsertAsync<T>(T entity) where T : class
    {
        using var scope = _serviceProvider.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
        await db.Set<T>().AddAsync(entity);
        await db.SaveChangesAsync();
        return entity;
    }
}
```

## Detect Existing Patterns

```bash
# Find CustomConstructorFaker
grep -r "CustomConstructorFaker" --include="*.cs" tests/

# Find assertion extensions
grep -r "AssertEquality" --include="*.cs" tests/Asserts/

# Find event fakers
grep -r "Faker.*:.*CustomConstructorFaker" --include="*.cs" tests/Fakers/

# Find integration tests
grep -r "IClassFixture<WebApplicationFactory" --include="*.cs" tests/
```

## Adding to Existing Project

1. **Locate `CustomConstructorFaker<T>`** -- should already exist in `Test/Fakers/`
2. **Create event faker** in `Test/Fakers/EventsFakers/{Entity}EventsFakers/`
3. **Create data faker** alongside the event faker (same file is fine)
4. **Add assertion extensions** in `Test/Asserts/{Entity}Asserts.cs`
5. **Create integration test** in `Test/Tests/{Entity}/{Action}Test.cs`
6. **Follow the Arrange-Act-Assert pattern** with `_dbContextHelper` and `_grpcClientHelper`
7. **Test both success and failure paths** (valid data, already exists, not found, invalid input)
