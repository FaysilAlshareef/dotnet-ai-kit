---
name: coding-conventions
description: >
  Company-agnostic C# coding conventions. File-scoped namespaces, sealed classes,
  expression-bodied members, var usage, async naming, XML doc patterns.
category: core
agent: dotnet-architect
---

# Coding Conventions

## File Organization

```csharp
// 1. File-scoped namespace (always)
namespace {Company}.{Domain}.Application.Features;

// 2. One primary type per file, named to match filename
// 3. Ordering: constants → fields → constructors → properties → methods
```

## Class Conventions

```csharp
// Seal classes that are not designed for inheritance
public sealed class OrderService(IUnitOfWork unitOfWork) : IOrderService
{
    // Primary constructor for DI (.NET 8+)
    private readonly IUnitOfWork _unitOfWork = unitOfWork;

    // Expression-bodied members for single-line methods
    public Task<Order?> GetByIdAsync(Guid id, CancellationToken ct) =>
        _unitOfWork.Orders.FindAsync(id, ct);
}
```

## Naming Rules

| Element | Convention | Example |
|---------|-----------|---------|
| Classes | PascalCase | `OrderService` |
| Interfaces | I + PascalCase | `IOrderService` |
| Methods | PascalCase | `GetOrdersAsync` |
| Async methods | Suffix `Async` | `SaveChangesAsync` |
| Properties | PascalCase | `TotalAmount` |
| Private fields | `_camelCase` | `_unitOfWork` |
| Parameters | camelCase | `orderId` |
| Constants | PascalCase | `MaxRetryCount` |
| Enums | PascalCase (singular) | `OrderStatus` |

## Var Usage

```csharp
// ✅ Use var when type is obvious from right side
var order = new Order();
var orders = await _repository.GetAllAsync(ct);
var count = orders.Count;

// ❌ Don't use var when type is not obvious
decimal total = CalculateTotal(items);  // Not: var total = ...
IOrderService service = GetService();    // Not: var service = ...
```

## Records and DTOs

```csharp
// Use records for immutable data (commands, events, DTOs)
public sealed record CreateOrderCommand(
    string CustomerName,
    decimal Total,
    List<OrderItemDto> Items) : IRequest<Result<Guid>>;

// Use record for output DTOs
public sealed record OrderOutput(
    Guid Id,
    string CustomerName,
    decimal Total,
    string Status);
```

## Async Patterns

```csharp
// Always accept CancellationToken
public async Task<Result<Order>> Handle(
    CreateOrderCommand request,
    CancellationToken cancellationToken)
{
    // Always pass CancellationToken to async calls
    var order = await _repository.FindAsync(request.Id, cancellationToken);

    // Never use async void — always return Task
    // Never use .Result or .Wait() — always await
}
```

## Null Handling

```csharp
// Use nullable reference types
public Order? FindById(Guid id) => ...

// Use pattern matching for null checks
if (order is null)
    throw new NotFoundException(nameof(Order), id);

// Use null-conditional and null-coalescing
var name = order?.CustomerName ?? "Unknown";
```

## XML Documentation

```csharp
/// <summary>
/// Creates a new order with the specified items.
/// </summary>
/// <param name="command">The create order command.</param>
/// <param name="cancellationToken">Cancellation token.</param>
/// <returns>The created order ID wrapped in a Result.</returns>
/// <exception cref="ValidationException">When command validation fails.</exception>
public Task<Result<Guid>> Handle(CreateOrderCommand command, CancellationToken cancellationToken);
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| `public string Name { get; set; }` on domain entities | `public string Name { get; private set; }` |
| `async void` methods | Always return `Task` or `Task<T>` |
| `.Result` or `.Wait()` on tasks | Always `await` |
| Catching generic `Exception` | Catch specific exceptions |
| String concatenation for SQL | Parameterized queries |
| `DateTime.Now` | Injected `TimeProvider` or `ISystemClock` |

## Detect Existing Patterns

```bash
grep -r "namespace " --include="*.cs" | head -5   # Namespace style
grep -r "sealed class" --include="*.cs" | wc -l    # Sealed usage
grep -r "var " --include="*.cs" | head -10          # Var usage
```

## Adding to Existing Project

1. Follow whatever conventions the project already uses
2. Only apply these when no existing convention is detected
3. Check `.editorconfig` for project-specific overrides
