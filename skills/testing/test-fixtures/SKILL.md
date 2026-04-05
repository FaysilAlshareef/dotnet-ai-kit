---
name: test-fixtures
description: >
  Test data generation with CustomConstructorFaker and Bogus. Covers faker patterns,
  assertion extensions, and test helper utilities for microservice testing.
  Trigger: test fixture, faker, Bogus, test data, assertion extension.
metadata:
  category: testing
  agent: test-engineer
  when-to-use: "When creating test data fakers, assertion extensions, or test helper utilities"
---

# Test Fixtures — Fakers, Assertions, Helpers

## Core Principles

- `CustomConstructorFaker<T>` bypasses private constructors for test data
- Bogus library generates realistic random data
- Assertion extensions compare entities field-by-field
- Test helpers reduce boilerplate for common operations
- Fakers are reusable across unit and integration tests

## Key Patterns

### CustomConstructorFaker Base

```csharp
namespace {Company}.{Domain}.Tests.Common;

public abstract class CustomConstructorFaker<T> : Faker<T> where T : class
{
    protected CustomConstructorFaker()
    {
        CustomInstantiator(_ =>
            (T)RuntimeHelpers.GetUninitializedObject(typeof(T)));
    }
}
```

### Entity Fakers

```csharp
namespace {Company}.{Domain}.Tests.Fakers;

public sealed class OrderFaker : CustomConstructorFaker<Order>
{
    public OrderFaker()
    {
        RuleFor(o => o.Id, f => f.Random.Guid());
        RuleFor(o => o.CustomerName, f => f.Person.FullName);
        RuleFor(o => o.Total, f => f.Finance.Amount(10, 10000));
        RuleFor(o => o.Sequence, _ => 1);
        RuleFor(o => o.Status, f => f.PickRandom<OrderStatus>());
    }

    public OrderFaker WithStatus(OrderStatus status)
    {
        RuleFor(o => o.Status, _ => status);
        return this;
    }

    public OrderFaker WithSequence(int sequence)
    {
        RuleFor(o => o.Sequence, _ => sequence);
        return this;
    }
}

public sealed class OrderItemFaker : CustomConstructorFaker<OrderItem>
{
    public OrderItemFaker()
    {
        RuleFor(i => i.Id, f => f.Random.Guid());
        RuleFor(i => i.ProductId, f => f.Random.Guid());
        RuleFor(i => i.ProductName, f => f.Commerce.ProductName());
        RuleFor(i => i.Quantity, f => f.Random.Int(1, 100));
        RuleFor(i => i.UnitPrice, f => f.Finance.Amount(1, 500));
    }
}
```

### Event Data Fakers

```csharp
namespace {Company}.{Domain}.Tests.Fakers;

public sealed class OrderCreatedDataFaker : Faker<OrderCreatedData>
{
    public OrderCreatedDataFaker()
    {
        CustomInstantiator(f => new OrderCreatedData(
            f.Person.FullName,
            f.Finance.Amount(10, 10000),
            new OrderItemDataFaker().Generate(f.Random.Int(1, 5))));
    }
}

public sealed class OrderItemDataFaker : Faker<OrderItemData>
{
    public OrderItemDataFaker()
    {
        CustomInstantiator(f => new OrderItemData(
            f.Random.Guid(),
            f.Commerce.ProductName(),
            f.Random.Int(1, 20),
            f.Finance.Amount(1, 500)));
    }
}
```

### Assertion Extensions

```csharp
namespace {Company}.{Domain}.Tests.Assertions;

public static class OrderAssertions
{
    public static void AssertCreatedFrom(
        this Order actual, Event<OrderCreatedData> @event)
    {
        actual.Id.Should().Be(@event.AggregateId);
        actual.CustomerName.Should().Be(@event.Data.CustomerName);
        actual.Total.Should().Be(@event.Data.Total);
        actual.Sequence.Should().Be(@event.Sequence);
    }

    public static void AssertUpdatedFrom(
        this Order actual, Event<OrderUpdatedData> @event, Order before)
    {
        actual.Id.Should().Be(before.Id);
        actual.Total.Should().Be(@event.Data.Total);
        actual.Sequence.Should().Be(@event.Sequence);

        if (@event.Data.CustomerName is not null)
            actual.CustomerName.Should().Be(@event.Data.CustomerName);
        else
            actual.CustomerName.Should().Be(before.CustomerName);
    }
}
```

### Test Helpers

```csharp
namespace {Company}.{Domain}.Tests.Helpers;

public static class DbContextHelper
{
    public static async Task<T?> QueryAsync<T>(
        IServiceProvider sp, Guid id) where T : class
    {
        var db = sp.GetRequiredService<ApplicationDbContext>();
        return await db.Set<T>().FindAsync(id);
    }

    public static async Task InsertAsync<T>(
        IServiceProvider sp, T entity) where T : class
    {
        var db = sp.GetRequiredService<ApplicationDbContext>();
        db.Set<T>().Add(entity);
        await db.SaveChangesAsync(cancellationToken);
    }
}

public static class EventHelper
{
    public static Event<T> CreateEvent<T>(T data, Guid? aggregateId = null,
        int sequence = 1) where T : IEventData => new()
    {
        AggregateId = aggregateId ?? Guid.NewGuid(),
        Sequence = sequence,
        Type = typeof(T).Name.Replace("Data", ""),
        DateTime = DateTime.UtcNow,
        Version = 1,
        Data = data
    };
}
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Manual test data construction | Use Bogus fakers for realistic data |
| Duplicating assertion logic | Create reusable assertion extensions |
| Fakers with hardcoded values | Use Bogus generators for randomness |
| Missing builder/fluent API on fakers | Add `WithXxx` methods for customization |

## Detect Existing Patterns

```bash
# Find CustomConstructorFaker
grep -r "CustomConstructorFaker" --include="*.cs" tests/

# Find Bogus fakers
grep -r ": Faker<\|: CustomConstructorFaker" --include="*.cs" tests/

# Find assertion extensions
grep -r "AssertCreatedFrom\|AssertEquality\|AssertUpdatedFrom" --include="*.cs" tests/

# Find test helpers
grep -r "DbContextHelper\|EventHelper" --include="*.cs" tests/
```

## Adding to Existing Project

1. **Locate `CustomConstructorFaker<T>`** base class and extend it
2. **Follow existing faker naming**: `{Entity}Faker`, `{EventData}Faker`
3. **Add assertion extensions** in `Assertions/` folder
4. **Reuse existing test helpers** for DB and event operations
5. **Add `WithXxx` fluent methods** for test-specific customization
