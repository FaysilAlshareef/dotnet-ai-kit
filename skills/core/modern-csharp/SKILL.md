---
name: modern-csharp
description: >
  Modern C# 12/13/14 language features: primary constructors, records, collection expressions,
  field keyword, pattern matching, file-scoped namespaces, required members, raw string literals.
  Trigger: C# features, primary constructor, record, collection expression, pattern matching, field keyword.
metadata:
  category: core
  agent: dotnet-architect
  alwaysApply: true
---

# Modern C# Features

## Core Principles

- Use the newest language features available for the project's target framework
- Gate features by C# language version -- never emit syntax the project cannot compile
- Prefer concise, expressive constructs over verbose boilerplate
- Use records for immutable DTOs, value objects, and command/query messages
- Prefer collection expressions `[..]` over explicit collection initializers
- Use pattern matching to replace complex if/else chains

## Version Availability Matrix

```
Feature                       C# Version   Min .NET
--------------------------------------------------
File-scoped namespaces        C# 10        .NET 6
Global usings                 C# 10        .NET 6
Required members              C# 11        .NET 7
Raw string literals           C# 11        .NET 7
List patterns [a, .., z]      C# 11        .NET 7
Primary constructors          C# 12        .NET 8
Collection expressions [..]   C# 12        .NET 8
Inline arrays                 C# 12        .NET 8
using aliases for generics    C# 12        .NET 8
params collections            C# 13        .NET 9
Lock object                   C# 13        .NET 9
field keyword                 C# 14        .NET 10
Extension types               C# 14        .NET 10
```

## Patterns

### Primary Constructors (.NET 8+ / C# 12)

```csharp
// Services -- capture DI parameters directly
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

// Records already had primary constructors -- still the best fit for DTOs
public sealed record OrderResponse(Guid Id, string CustomerName, decimal Total);

// Structs
public readonly record struct Money(decimal Amount, string Currency);
```

### Collection Expressions (C# 12)

```csharp
// Array, List, Span -- all use [..]
int[] numbers = [1, 2, 3];
List<string> names = ["Alice", "Bob"];
ReadOnlySpan<byte> bytes = [0x00, 0xFF];

// Spread operator
List<string> merged = [..existing, ..additional, "extra"];

// Empty collection (replaces Array.Empty<T>())
int[] empty = [];
```

### Records for Immutable DTOs and Messages

```csharp
// Command message
public sealed record Create{Entity}Command(
    string Name,
    string Description) : IRequest<Result<Guid>>;

// Value object
public sealed record Address(
    string Street,
    string City,
    string PostalCode,
    string Country);

// Record struct for small value types (no heap allocation)
public readonly record struct Coordinate(double Latitude, double Longitude);
```

### Pattern Matching

```csharp
// Switch expression with property pattern
string description = order switch
{
    { Status: OrderStatus.Pending, Total: > 1000 } => "Requires approval",
    { Status: OrderStatus.Pending }                 => "Awaiting processing",
    { Status: OrderStatus.Shipped }                 => "In transit",
    { Status: OrderStatus.Delivered }               => "Complete",
    _                                                => "Unknown"
};

// List patterns (C# 11)
var result = args switch
{
    []              => "No arguments",
    [var single]    => $"One argument: {single}",
    [var first, ..] => $"Multiple arguments, first: {first}"
};

// Relational and logical patterns
bool IsValidAge(int age) => age is >= 0 and <= 150;
```

### Raw String Literals (C# 11)

```csharp
// Multi-line SQL or JSON without escaping
var sql = """
    SELECT o.Id, o.CustomerName, o.Total
    FROM Orders o
    WHERE o.Status = @Status
    ORDER BY o.CreatedAt DESC
    """;

// Interpolated raw strings
var json = $$"""
    {
        "name": "{{name}}",
        "total": {{total}}
    }
    """;
```

### Required Members (C# 11)

```csharp
public sealed class {Company}.{Domain}.Models.ProductOptions
{
    public required string Name { get; init; }
    public required decimal Price { get; init; }
    public string? Description { get; init; }
}

// Caller must set required properties
var options = new ProductOptions
{
    Name = "Widget",   // required
    Price = 9.99m      // required
    // Description is optional
};
```

### Field Keyword (C# 14 / .NET 10+)

```csharp
// Auto-property with custom validation -- no backing field declaration needed
public string Name
{
    get => field;
    set => field = value?.Trim() ?? throw new ArgumentNullException(nameof(value));
}

public int Quantity
{
    get => field;
    set => field = value >= 0 ? value : throw new ArgumentOutOfRangeException(nameof(value));
}
```

### Using Aliases for Generic Types (C# 12)

```csharp
using OrderList = System.Collections.Generic.List<{Company}.{Domain}.Models.Order>;
using OrderDict = System.Collections.Generic.Dictionary<System.Guid, {Company}.{Domain}.Models.Order>;

// Then use the alias
OrderList orders = [new Order(), new Order()];
```

### File-Scoped Namespaces (C# 10)

```csharp
// PREFER: file-scoped (saves one level of indentation)
namespace {Company}.{Domain}.Features.Orders;

public sealed class OrderService { }

// AVOID: block-scoped
namespace {Company}.{Domain}.Features.Orders
{
    public sealed class OrderService { }
}
```

## Anti-Patterns

| Anti-Pattern | Problem | Correct Approach |
|---|---|---|
| Using `new List<int> { 1, 2, 3 }` on C# 12+ | Verbose, ignores collection expressions | `[1, 2, 3]` |
| Mutable class for DTO | Unintended mutation | `sealed record` |
| Long if/else chains for type checks | Hard to read, error-prone | Switch expression with patterns |
| `string.Format()` or `$""` for multi-line SQL | Escaping issues, poor readability | Raw string literals `"""` |
| `field` keyword on .NET 8/9 projects | Compilation error | Check `<LangVersion>` first |
| Primary constructors storing to `private readonly` | Redundant -- captured params are already fields | Use captured parameter directly |
| Block-scoped namespaces | Wastes indentation | File-scoped `namespace X;` |
| `== null` / `!= null` comparisons | Operator overloading can break intent | `is null` / `is not null` |

## Detect Existing Patterns

1. Check `<LangVersion>` in `.csproj` or `Directory.Build.props` (`preview`, `latest`, `12`, `13`, `14`)
2. Check `<TargetFramework>` for `net8.0`, `net9.0`, `net10.0`
3. Scan for existing primary constructor usage: `class Foo(` or `struct Foo(`
4. Look for `record` keyword usage in model/DTO files
5. Search for collection expressions `= [` in existing code
6. Check for `required` modifier on properties

## Adding to Existing Project

1. **Verify language version** -- check `Directory.Build.props` or `.csproj` for `<LangVersion>`
2. **Start with records** -- convert immutable DTOs and command/query messages to `sealed record`
3. **Adopt primary constructors** -- refactor services that only store injected dependencies
4. **Replace collection initializers** -- use `[..]` syntax on C# 12+ projects
5. **Introduce pattern matching** -- replace complex `if`/`switch` blocks with switch expressions
6. **Use raw string literals** -- for SQL queries, JSON templates, multi-line strings
7. **Add file-scoped namespaces** -- one-time bulk conversion via IDE or `dotnet format`
8. **Gate new features** -- only use `field` keyword or extension types on .NET 10+ projects

## Decision Guide

| Scenario | Recommendation |
|----------|---------------|
| .NET 8 project | C# 12: primary constructors, collection expressions, records |
| .NET 9 project | C# 13: all above + params collections, lock object |
| .NET 10+ project | C# 14: all above + field keyword, extension types |
| Shared library targeting multiple TFMs | Use lowest common C# version across targets |
| New greenfield project | Use `<LangVersion>latest</LangVersion>` and latest TFM |

## References

- https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-12
- https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-13
- https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-14
