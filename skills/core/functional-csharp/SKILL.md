---
name: dotnet-ai-functional-csharp
description: >
  Functional programming patterns in C# — Result types, railway-oriented programming,
  pure functions, immutability, pattern matching, and OOP vs FP decision guidance.
  Trigger: functional, Result, Option, immutable, pure function, pattern matching, railway.
category: core
agent: dotnet-architect
---

# Functional Programming in C#

C# is a multi-paradigm language. Use FP where it shines, OOP where it fits. This skill covers practical functional patterns that integrate naturally with idiomatic .NET code -- not Haskell or F# transplants.

## Core Principles

- **Immutability** -- prefer data that cannot change after creation (records, init, readonly)
- **Pure functions** -- given the same inputs, always produce the same output with no side effects
- **Composition over inheritance** -- build complex behavior by chaining small functions, not deep class hierarchies
- **Expressions over statements** -- prefer switch expressions, ternary operators, and LINQ over imperative if/else blocks
- **Explicit error handling** -- use `Result<T>` to make failure a first-class return value, not an exception

## When to Use

- Data transformation pipelines (mapping, filtering, projecting)
- Error handling that must compose across multiple steps (validation, orchestration)
- Validation chains where each rule is independent and combinable
- LINQ query composition (Select, Where, Aggregate)
- Pure business logic that is easy to unit test without mocking
- Configuration builders and fluent APIs

## When NOT to Use

- Stateful UI component logic (Blazor components, WinForms) -- OOP fits better
- Complex mutation workflows where entities change through multiple lifecycle stages
- Teams unfamiliar with FP concepts -- the learning curve hurts more than the pattern helps
- Simple CRUD operations -- a service class with straightforward methods is clearer
- Performance-critical hot paths where allocations from closures and delegates matter
- EF Core tracking scenarios that rely on mutable entity state

## Patterns

### Result<T> Pattern

A lightweight discriminated union that makes success and failure explicit in the type system. No exceptions for expected failures.

```csharp
public sealed record Result<T>
{
    private readonly T? _value;
    private readonly string? _error;

    private Result(T value) { _value = value; IsSuccess = true; }
    private Result(string error) { _error = error; IsSuccess = false; }

    public bool IsSuccess { get; }
    public bool IsFailure => !IsSuccess;
    public T Value => IsSuccess ? _value! : throw new InvalidOperationException(_error);
    public string Error => IsFailure ? _error! : throw new InvalidOperationException("No error");

    public static Result<T> Success(T value) => new(value);
    public static Result<T> Failure(string error) => new(error);

    public TOut Match<TOut>(Func<T, TOut> onSuccess, Func<string, TOut> onFailure) =>
        IsSuccess ? onSuccess(_value!) : onFailure(_error!);
}
```

Usage:

```csharp
public Result<Order> CreateOrder(CreateOrderRequest request)
{
    if (string.IsNullOrWhiteSpace(request.CustomerName))
        return Result<Order>.Failure("Customer name is required");

    if (request.Items.Count == 0)
        return Result<Order>.Failure("Order must have at least one item");

    var order = new Order(Guid.NewGuid(), request.CustomerName, request.Items);
    return Result<Order>.Success(order);
}

// Caller uses Match to handle both paths
var response = CreateOrder(request).Match(
    onSuccess: order => Results.Created($"/orders/{order.Id}", order),
    onFailure: error => Results.BadRequest(error));
```

### Railway-Oriented Programming

Chain operations that each return `Result<T>`. If any step fails, the pipeline short-circuits and carries the error forward -- like a train switching to the failure track.

```csharp
public static class ResultExtensions
{
    public static Result<TOut> Map<TIn, TOut>(
        this Result<TIn> result, Func<TIn, TOut> map) =>
        result.IsSuccess ? Result<TOut>.Success(map(result.Value)) : Result<TOut>.Failure(result.Error);

    public static Result<TOut> Bind<TIn, TOut>(
        this Result<TIn> result, Func<TIn, Result<TOut>> bind) =>
        result.IsSuccess ? bind(result.Value) : Result<TOut>.Failure(result.Error);

    public static async Task<Result<TOut>> BindAsync<TIn, TOut>(
        this Result<TIn> result, Func<TIn, Task<Result<TOut>>> bind) =>
        result.IsSuccess ? await bind(result.Value) : Result<TOut>.Failure(result.Error);
}
```

Chaining a multi-step workflow:

```csharp
public async Task<Result<OrderConfirmation>> ProcessOrderAsync(CreateOrderRequest request)
{
    return ValidateRequest(request)
        .Bind(CalculatePricing)
        .Bind(CheckInventory)
        .Bind(ApplyDiscounts)
        .Map(order => new OrderConfirmation(order.Id, order.Total));
}
// If ValidateRequest fails, the rest never execute -- error propagates automatically.
```

### Pure Functions

A pure function has no side effects and always returns the same result for the same input. Pure functions are trivially testable and safe to parallelize.

```csharp
// PURE -- no side effects, deterministic, testable
public static decimal CalculateDiscount(decimal subtotal, CustomerTier tier) =>
    tier switch
    {
        CustomerTier.Gold when subtotal > 500 => subtotal * 0.15m,
        CustomerTier.Gold => subtotal * 0.10m,
        CustomerTier.Silver => subtotal * 0.05m,
        _ => 0m
    };

// IMPURE -- reads DateTime.Now, writes to database, throws exceptions
public decimal CalculateDiscount(Order order)
{
    var tier = _dbContext.Customers.Find(order.CustomerId)!.Tier;
    if (DateTime.Now.DayOfWeek == DayOfWeek.Friday)
        tier = CustomerTier.Gold; // surprise promotion
    _dbContext.SaveChanges();
    return order.Total * GetRate(tier);
}
```

Guidelines for pure functions:
- Accept all data as parameters -- do not read from fields, databases, or environment
- Return the result -- do not mutate input objects or external state
- Use `static` methods when possible to signal purity
- Push I/O to the edges: impure shell calls pure core

### Immutability

Immutable data eliminates entire categories of bugs: race conditions, unintended aliasing, and stale state.

```csharp
// Records are immutable by default
public sealed record OrderLine(string ProductName, int Quantity, decimal UnitPrice)
{
    public decimal Total => Quantity * UnitPrice;
}

// Use 'with' expressions to create modified copies
var updated = originalLine with { Quantity = 5 };

// Init-only properties on classes
public sealed class AppSettings
{
    public required string ConnectionString { get; init; }
    public required int MaxRetries { get; init; }
    public TimeSpan Timeout { get; init; } = TimeSpan.FromSeconds(30);
}

// Immutable collections from System.Collections.Immutable
using System.Collections.Immutable;

ImmutableList<OrderLine> lines = [..initialLines];
ImmutableList<OrderLine> withNew = lines.Add(new OrderLine("Widget", 2, 9.99m));
// 'lines' is unchanged -- 'withNew' is a new list

// ReadOnlyCollection for API boundaries
public IReadOnlyList<OrderLine> Lines => _lines.AsReadOnly();
```

When to use which immutable type:

| Type | Use When |
|------|----------|
| `record` | DTOs, value objects, command/query messages |
| `init` properties | Configuration objects, builder results |
| `ImmutableList<T>` | Collections that grow/shrink in pure pipelines |
| `IReadOnlyList<T>` | Public API surface to prevent external mutation |
| `ReadOnlySpan<T>` | High-performance slicing without allocation |
| `FrozenSet<T>` / `FrozenDictionary<K,V>` | Lookup collections built once, read many (.NET 8+) |

### Pattern Matching

Pattern matching replaces verbose type checks and conditional chains with concise, exhaustive expressions.

```csharp
// Switch expression with multiple pattern types
public static string Classify(object value) => value switch
{
    null => "nothing",
    int n when n < 0 => "negative integer",
    int n => $"integer: {n}",
    string { Length: 0 } => "empty string",
    string s => $"string: {s}",
    IEnumerable<int> nums => $"collection of {nums.Count()} ints",
    _ => $"unknown: {value.GetType().Name}"
};

// Property patterns for domain logic
public static decimal CalculateShipping(Order order) => order switch
{
    { Total: >= 100, ShippingAddress.Country: "US" } => 0m,      // free US shipping over $100
    { Total: >= 100 } => 9.99m,                                   // discounted international
    { ShippingAddress.Country: "US" } => 5.99m,                   // standard US
    _ => 19.99m                                                    // standard international
};

// Relational and logical patterns
public static string RateTemperature(double celsius) => celsius switch
{
    < 0 => "freezing",
    >= 0 and < 15 => "cold",
    >= 15 and < 25 => "comfortable",
    >= 25 and < 35 => "warm",
    >= 35 => "hot"
};

// List patterns (C# 11+)
public static string DescribeRoute(string[] segments) => segments switch
{
    ["api", var version, .. var rest] => $"API {version}: /{string.Join('/', rest)}",
    ["admin", ..] => "Admin area",
    [var single] => $"Root: {single}",
    [] => "Home"
};
```

### LINQ as Functional Composition

LINQ is the most natural FP surface in C#. Chain small, focused transformations instead of writing imperative loops.

```csharp
// Functional pipeline: filter, transform, aggregate
public static OrderSummary Summarize(IEnumerable<Order> orders)
{
    var completedOrders = orders
        .Where(o => o.Status == OrderStatus.Delivered)
        .Where(o => o.CompletedAt >= DateOnly.FromDateTime(DateTime.UtcNow).AddMonths(-3))
        .Select(o => new
        {
            o.Id,
            o.CustomerName,
            LineCount = o.Lines.Count,
            Total = o.Lines.Sum(l => l.Quantity * l.UnitPrice)
        })
        .OrderByDescending(o => o.Total)
        .ToList();

    return new OrderSummary(
        OrderCount: completedOrders.Count,
        TotalRevenue: completedOrders.Sum(o => o.Total),
        AverageOrderValue: completedOrders.Count > 0
            ? completedOrders.Average(o => o.Total)
            : 0m,
        TopCustomer: completedOrders.FirstOrDefault()?.CustomerName ?? "N/A");
}

// Aggregate for custom reductions
var csv = names.Aggregate(
    seed: new StringBuilder(),
    func: (sb, name) => sb.Length == 0 ? sb.Append(name) : sb.Append(',').Append(name),
    resultSelector: sb => sb.ToString());
```

## OOP vs FP Decision Matrix

| Scenario | Prefer OOP | Prefer FP | Why |
|----------|-----------|----------|-----|
| Error handling across steps | | X | `Result<T>` with Bind chains composes cleanly without try/catch nesting |
| Entity with rich behavior | X | | Domain entities encapsulate state + invariants in methods |
| Data transformation pipeline | | X | LINQ/Select chains express intent declaratively |
| State machine with transitions | X | | Class with methods and guards models lifecycle clearly |
| Validation pipeline | | X | Chain independent validators, collect all errors |
| UI component with lifecycle | X | | Stateful components need mutable properties and event handlers |
| Business rule calculation | | X | Pure functions are trivially testable and composable |
| Repository / data access | X | | Interfaces + DI fit the OOP service pattern naturally |
| Configuration building | | X | Immutable records with `with` expressions, init properties |
| Event sourcing projections | | X | Fold events into state with pure aggregate functions |

## Anti-Patterns

| Problem | Why It Hurts | Correct Approach |
|---------|-------------|-----------------|
| Wrapping every method in `Result<T>` | Noise -- not every operation can fail meaningfully | Use `Result<T>` for operations with expected domain failures; use exceptions for truly exceptional cases |
| Deeply nested `Match` calls | Unreadable pyramid of doom | Use `Bind`/`Map` railway chaining instead |
| Impure functions disguised as pure | Hidden database calls or DateTime.Now break testability | Extract I/O to parameters; inject time as `TimeProvider` |
| Mutable fields inside records | Records look immutable but mutate through reference fields | Use `ImmutableList<T>` or `IReadOnlyList<T>` for collection properties |
| Forcing FP on the entire codebase | Team confusion, inconsistent style | Apply FP to data pipelines and business logic; keep OOP for services and infrastructure |
| Using exceptions for control flow | Expensive, invisible flow, no composition | Return `Result<T>` from validation and business operations |
| Ignoring `Result.Error` | Silent failures that propagate bad state | Always `Match` or `Bind` -- never access `.Value` without checking |
| Reimplementing a full monad library | Over-engineering for C# -- not Haskell | Keep `Result<T>` simple; add Map/Bind/BindAsync and stop |

## Detect Existing Patterns

1. Search for `Result<` or `Result<T>` types in the codebase
2. Look for `OneOf`, `ErrorOr`, or `FluentResults` NuGet packages in `.csproj` files
3. Check for `record` usage in domain or DTO layers
4. Scan for LINQ chains in service/handler classes
5. Look for `ImmutableList`, `ImmutableDictionary` usage
6. Check for existing railway-style extension methods (Bind, Map, Then)
7. If a Result library exists, use it -- do not introduce a competing type

## Adding to Existing Project

1. **Start with Result<T>** -- introduce for new validation and business operations
2. **Convert DTOs to records** -- immutable by default, `with` expressions for copies
3. **Extract pure functions** -- pull calculation logic out of services into static methods
4. **Chain with LINQ** -- replace imperative loops with Select/Where/Aggregate pipelines
5. **Add Map/Bind extensions** -- enable railway-oriented composition on Result<T>
6. **Use ImmutableList<T>** where collections must not be modified after creation
7. **Keep services as classes** -- DI, logging, and I/O stay in OOP-style service classes
8. **Do not mix Result libraries** -- pick one (`ErrorOr`, `FluentResults`, or custom) and standardize

## References

- https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/functional/pattern-matching
- https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/
- https://learn.microsoft.com/en-us/dotnet/api/system.collections.immutable
