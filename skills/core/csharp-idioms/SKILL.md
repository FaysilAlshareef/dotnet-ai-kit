---
name: dotnet-ai-csharp-idioms
description: >
  Modern C# idioms and language features. File-scoped namespaces, records,
  pattern matching, primary constructors, collection expressions.
  Trigger: C# style, modern syntax, idioms, language features.
category: core
agent: dotnet-architect
---

# Modern C# Idioms

## Core Principles

- Prefer the latest stable C# features supported by the project's target framework
- Use file-scoped namespaces in all new files
- Prefer records for immutable data transfer objects and value objects
- Use pattern matching over chains of if-else or type checks
- Apply primary constructors to reduce boilerplate in DI-heavy classes
- Gate features by target framework: do not emit C# 14 syntax for .NET 8 projects

## Version Feature Matrix

| Feature | Minimum | C# Version |
|---------|---------|------------|
| File-scoped namespaces | .NET 6 | C# 10 |
| `required` modifier | .NET 7 | C# 11 |
| Primary constructors | .NET 8 | C# 12 |
| Collection expressions | .NET 8 | C# 12 |
| `field` keyword | .NET 10 | C# 14 |
| Extension types | .NET 10 | C# 14 |

## Patterns

### File-Scoped Namespaces

```csharp
// PREFER — file-scoped (one less indent level)
namespace {Company}.{Domain}.Features.Orders;

public sealed class OrderService { }
```

### Records for DTOs and Value Objects

```csharp
// Immutable DTO
public sealed record OrderResponse(Guid Id, string CustomerName, decimal Total);

// Value object with behavior
public sealed record Money(decimal Amount, string Currency)
{
    public Money Add(Money other)
    {
        if (Currency != other.Currency)
            throw new InvalidOperationException("Cannot add different currencies");
        return this with { Amount = Amount + other.Amount };
    }
}

// Record struct for lightweight value types
public readonly record struct OrderId(Guid Value)
{
    public static OrderId New() => new(Guid.NewGuid());
}
```

### Primary Constructors (.NET 8+ / C# 12)

```csharp
// Service with DI — no field declarations needed
public sealed class OrderService(
    IOrderRepository repository,
    ILogger<OrderService> logger)
{
    public async Task<Order?> GetAsync(Guid id, CancellationToken ct)
    {
        logger.LogInformation("Fetching order {OrderId}", id);
        return await repository.FindAsync(id, ct);
    }
}
```

### Collection Expressions (C# 12)

```csharp
int[] numbers = [1, 2, 3];
List<string> merged = [..existing, ..additional, "extra"];
ReadOnlySpan<byte> bytes = [0x01, 0x02, 0x03];

// Empty collection
List<Order> orders = [];
```

### Pattern Matching

```csharp
// Switch expression
string label = order.State switch
{
    OrderState.Pending when order.Total > 1000 => "Requires approval",
    OrderState.Pending => "Awaiting processing",
    OrderState.Shipped => "In transit",
    OrderState.Delivered => "Complete",
    _ => "Unknown"
};

// Property pattern
if (order is { Status: OrderStatus.Shipped, Total: > 500 })
    ApplyDiscount(order);

// List pattern (C# 12)
var result = args switch
{
    [var cmd, ..var rest] => ProcessCommand(cmd, rest),
    [] => ShowHelp()
};

// is null / is not null (prefer over == null)
if (order is not null)
    Process(order);
```

### Sealed Classes and Expression Bodies

```csharp
// Seal classes not designed for inheritance
public sealed class OrderValidator
{
    // Expression body for single-line methods
    public bool IsValid(Order order) => order.Items.Count > 0 && order.Total > 0;

    // Expression body for properties
    public string Name => nameof(OrderValidator);
}
```

### Naming Conventions

```csharp
namespace {Company}.{Domain}.Features.Orders;

public sealed class OrderService
{
    // PascalCase: types, methods, properties, constants
    private const string DefaultCurrency = "USD";

    // _camelCase: private fields
    private readonly IOrderRepository _repository;

    // camelCase: parameters and locals
    public async Task<OrderResponse?> GetOrderAsync(Guid orderId)
    {
        var order = await _repository.FindAsync(orderId);
        return order is null ? null : MapToResponse(order);
    }

    // Async suffix on async methods
    private static OrderResponse MapToResponse(Order order) => new(
        Id: order.Id,
        CustomerName: order.CustomerName,
        Total: order.Total);
}
```

### field Keyword (C# 14 / .NET 10)

```csharp
// Auto-property with validation — no backing field declaration
public string Name
{
    get => field;
    set => field = value?.Trim() ?? throw new ArgumentNullException(nameof(value));
}
```

## Anti-Patterns

- Using block-scoped namespaces in new files (wastes indentation)
- Mutable classes where a record would suffice
- Long if-else chains instead of switch expressions
- Using `== null` instead of `is null`
- String interpolation in log messages (loses structure)
- Emitting C# 14 syntax for projects targeting .NET 8

## Detect Existing Patterns

1. Check `<LangVersion>` in `.csproj` or `Directory.Build.props`
2. Check `<TargetFramework>` for `net8.0`, `net9.0`, `net10.0`
3. Scan `.cs` files for primary constructor usage
4. Look for `record` keyword usage in model/DTO files
5. Check `.editorconfig` for naming and style rules
6. Detect file-scoped vs block-scoped namespaces in existing files
7. Check private field naming convention (`_camelCase` vs `camelCase`)

## Adding to Existing Project

1. **Match existing style first** — if the project uses block-scoped namespaces, continue until a team-wide migration is agreed
2. **Adopt incrementally** — introduce records for new DTOs, primary constructors for new services
3. **Do not mix conventions** — all files in a project should follow the same naming rules
4. **Add `.editorconfig`** if missing to enforce style rules:

```ini
[*.cs]
csharp_style_namespace_declarations = file_scoped:warning
csharp_style_var_for_built_in_types = false:suggestion
csharp_style_prefer_pattern_matching = true:suggestion
dotnet_naming_rule.private_fields_should_be_camel_case.severity = warning
```

## Decision Guide

| Scenario | Recommendation |
|----------|---------------|
| New DTO / response type | Use `record` |
| Service class with DI | Use primary constructor (.NET 8+) |
| Multiple type checks | Use switch expression with patterns |
| Null check | Use `is null` / `is not null` |
| New file | Use file-scoped namespace |
| Lightweight ID type | Use `readonly record struct` |

## References

- https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/
- https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/coding-style/coding-conventions
