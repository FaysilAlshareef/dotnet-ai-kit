---
name: solid-principles

description: >
  SOLID principles with C# examples, decision guidance for when to apply each principle,
  anti-patterns for over-engineering, and practical trade-offs.
  Trigger: SOLID, single responsibility, open closed, liskov, interface segregation, dependency inversion.
metadata:
  category: core
  agent: dotnet-architect
  alwaysApply: true
---

# SOLID Principles in C#

SOLID is a refactoring guide, not a starting requirement. Write simply first. Extract abstractions when complexity demands it.

## Core Principles

- **S — Single Responsibility**: A class should have one reason to change. One actor, one job.
- **O — Open/Closed**: Open for extension, closed for modification. Add behavior without editing existing code.
- **L — Liskov Substitution**: Subtypes must be substitutable for their base types without breaking correctness.
- **I — Interface Segregation**: Clients should not depend on methods they do not use. Keep interfaces focused.
- **D — Dependency Inversion**: Depend on abstractions, not concretions. High-level modules define the contract.

## When to Use

| Principle | Apply When |
|-----------|------------|
| SRP | A class handles both business logic and infrastructure (e.g., validation + database calls) |
| OCP | You keep modifying the same switch/if-else chain to add new behavior |
| LSP | You have a class hierarchy and consumers use the base type polymorphically |
| ISP | Implementors are forced to throw `NotImplementedException` for methods they don't need |
| DIP | You need to test business logic without hitting databases, APIs, or file systems |

## When NOT to Use

- **Startup or prototype phase** — get it working first, then refactor toward SOLID when pain emerges
- **Simple CRUD with no business logic** — a single service class that maps DTOs to entities is fine
- **Internal utilities** — a helper class used in one place does not need an interface
- **Fewer than 50 lines** — if the entire class fits on one screen, splitting it adds noise
- **One implementation forever** — don't create `IOrderService` if `OrderService` is the only implementation and you have no testing seam requirement

## Patterns

### SRP — One MediatR Handler per Request

```csharp
// GOOD: Each handler has exactly one responsibility
public sealed record CreateOrderCommand(
    string CustomerName,
    List<OrderItemDto> Items) : IRequest<Result<Guid>>;

public sealed class CreateOrderHandler(
    IOrderRepository repository,
    IUnitOfWork unitOfWork,
    TimeProvider timeProvider) : IRequestHandler<CreateOrderCommand, Result<Guid>>
{
    public async Task<Result<Guid>> Handle(
        CreateOrderCommand request,
        CancellationToken ct)
    {
        var order = Order.Create(
            request.CustomerName,
            request.Items,
            timeProvider.GetUtcNow());

        repository.Add(order);
        await unitOfWork.SaveChangesAsync(ct);

        return Result.Success(order.Id);
    }
}

// BAD: One service doing everything — creating, updating, deleting, emailing, reporting
public class OrderService
{
    public Task CreateAsync(...) { /* ... */ }
    public Task UpdateAsync(...) { /* ... */ }
    public Task DeleteAsync(...) { /* ... */ }
    public Task SendConfirmationEmailAsync(...) { /* ... */ }
    public Task GenerateReportAsync(...) { /* ... */ }
}
```

### OCP — Strategy Pattern for Extension Without Modification

```csharp
// Define the contract
public interface IDiscountStrategy
{
    decimal Calculate(Order order);
}

// Add new strategies without modifying existing ones
public sealed class LoyaltyDiscount : IDiscountStrategy
{
    public decimal Calculate(Order order) =>
        order.Customer.LoyaltyYears >= 3 ? order.Total * 0.10m : 0m;
}

public sealed class BulkDiscount : IDiscountStrategy
{
    public decimal Calculate(Order order) =>
        order.Items.Count >= 10 ? order.Total * 0.05m : 0m;
}

public sealed class SeasonalDiscount : IDiscountStrategy
{
    public decimal Calculate(Order order) =>
        order.CreatedAt.Month is 11 or 12 ? order.Total * 0.15m : 0m;
}

// Consumer is closed for modification — new discounts need zero changes here
public sealed class DiscountCalculator(IEnumerable<IDiscountStrategy> strategies)
{
    public decimal CalculateTotal(Order order) =>
        strategies.Sum(s => s.Calculate(order));
}

// Registration — add new strategies by registering, not by editing
services.AddSingleton<IDiscountStrategy, LoyaltyDiscount>();
services.AddSingleton<IDiscountStrategy, BulkDiscount>();
services.AddSingleton<IDiscountStrategy, SeasonalDiscount>();
```

### LSP — Interface Contract Substitution

```csharp
// Base contract
public interface INotificationSender
{
    Task SendAsync(Notification notification, CancellationToken ct);
}

// Both implementations are fully substitutable
public sealed class EmailNotificationSender(
    IEmailClient emailClient) : INotificationSender
{
    public async Task SendAsync(Notification notification, CancellationToken ct)
    {
        await emailClient.SendAsync(notification.Recipient, notification.Body, ct);
    }
}

public sealed class SmsNotificationSender(
    ISmsGateway gateway) : INotificationSender
{
    public async Task SendAsync(Notification notification, CancellationToken ct)
    {
        await gateway.SendTextAsync(notification.Recipient, notification.Body, ct);
    }
}

// BAD — violates LSP: subtype changes behavior the caller doesn't expect
public sealed class LogOnlyNotificationSender : INotificationSender
{
    public Task SendAsync(Notification notification, CancellationToken ct)
    {
        // Silently does nothing — caller expects delivery
        Console.WriteLine($"Would send: {notification.Body}");
        return Task.CompletedTask;
    }
}
```

### ISP — Focused Interfaces

```csharp
// GOOD: Segregated interfaces — clients depend only on what they use
public interface IOrderReader
{
    Task<Order?> GetByIdAsync(Guid id, CancellationToken ct);
    Task<IReadOnlyList<Order>> GetByCustomerAsync(Guid customerId, CancellationToken ct);
}

public interface IOrderWriter
{
    void Add(Order order);
    void Remove(Order order);
}

// Query handlers only need IOrderReader
public sealed class GetOrderHandler(
    IOrderReader reader) : IRequestHandler<GetOrderQuery, OrderDto?>
{
    public async Task<OrderDto?> Handle(GetOrderQuery query, CancellationToken ct)
    {
        var order = await reader.GetByIdAsync(query.Id, ct);
        return order?.ToDto();
    }
}

// Command handlers get IOrderWriter (and IOrderReader if needed)
public sealed class DeleteOrderHandler(
    IOrderReader reader,
    IOrderWriter writer,
    IUnitOfWork unitOfWork) : IRequestHandler<DeleteOrderCommand, Result>
{
    public async Task<Result> Handle(DeleteOrderCommand command, CancellationToken ct)
    {
        var order = await reader.GetByIdAsync(command.Id, ct);
        if (order is null) return Result.NotFound();
        writer.Remove(order);
        await unitOfWork.SaveChangesAsync(ct);
        return Result.Success();
    }
}

// BAD: One bloated interface forces implementors to support everything
public interface IOrderRepository
{
    Task<Order?> GetByIdAsync(Guid id, CancellationToken ct);
    Task<IReadOnlyList<Order>> GetByCustomerAsync(Guid customerId, CancellationToken ct);
    Task<IReadOnlyList<Order>> GetPendingAsync(CancellationToken ct);
    Task<IReadOnlyList<Order>> SearchAsync(string query, CancellationToken ct);
    void Add(Order order);
    void Update(Order order);
    void Remove(Order order);
    Task BulkInsertAsync(IEnumerable<Order> orders, CancellationToken ct);
    Task ArchiveOlderThanAsync(DateTimeOffset cutoff, CancellationToken ct);
    Task<int> CountAsync(CancellationToken ct);
    // ... 10 more methods most consumers never call
}
```

### DIP — Constructor Injection with Interface

```csharp
// High-level module defines the contract
public interface IPaymentProcessor
{
    Task<PaymentResult> ChargeAsync(decimal amount, string currency, CancellationToken ct);
}

// Low-level module implements it
public sealed class StripePaymentProcessor(
    IOptions<StripeOptions> options,
    HttpClient httpClient) : IPaymentProcessor
{
    public async Task<PaymentResult> ChargeAsync(
        decimal amount, string currency, CancellationToken ct)
    {
        // Stripe-specific implementation
        var response = await httpClient.PostAsJsonAsync(
            "/v1/charges",
            new { amount, currency },
            ct);

        return response.IsSuccessStatusCode
            ? PaymentResult.Success()
            : PaymentResult.Failed("Charge declined");
    }
}

// Business logic depends on abstraction — testable, swappable
public sealed class CheckoutHandler(
    IPaymentProcessor paymentProcessor,
    IOrderWriter orderWriter,
    IUnitOfWork unitOfWork) : IRequestHandler<CheckoutCommand, Result>
{
    public async Task<Result> Handle(CheckoutCommand command, CancellationToken ct)
    {
        var payment = await paymentProcessor.ChargeAsync(
            command.Total, "usd", ct);

        if (!payment.Succeeded)
            return Result.Failure(payment.Error);

        orderWriter.Add(Order.CreatePaid(command));
        await unitOfWork.SaveChangesAsync(ct);
        return Result.Success();
    }
}
```

## When Over-Applying Hurts

### Interface Explosion

Don't create an interface for a class that will only ever have one implementation.

```csharp
// BAD: Interface exists only because "SOLID says so"
public interface IOrderValidator { ... }
public sealed class OrderValidator : IOrderValidator { ... }
// No other implementation. No mock needed (FluentValidation is testable directly).

// GOOD: Just use the concrete class
services.AddScoped<OrderValidator>();
```

### Class Proliferation

Too many tiny files for simple operations add navigation overhead without benefit.

```csharp
// BAD: 6 files for one simple operation
// CreateOrderCommand.cs, CreateOrderCommandValidator.cs,
// CreateOrderCommandHandler.cs, CreateOrderCommandResponse.cs,
// ICreateOrderService.cs, CreateOrderService.cs

// GOOD: Co-locate command + handler in one file when the handler is short
// CreateOrder.cs — contains the record, validator, and handler
```

### Premature Abstraction

Don't extract an interface before you have a genuine second use case or a testing seam that demands it.

```csharp
// BAD: Abstracting on day one with one implementation
public interface IDateTimeProvider { DateTimeOffset UtcNow { get; } }
public sealed class DateTimeProvider : IDateTimeProvider { ... }
// .NET 8+ has TimeProvider built in — no custom abstraction needed

// GOOD: Use the built-in TimeProvider abstract class
services.AddSingleton(TimeProvider.System);
```

## Decision Guide

| Scenario | Principle | Apply? | Why |
|----------|-----------|--------|-----|
| Service handles HTTP + business logic + DB | SRP | Yes | Split into handler + repository |
| Growing switch on `OrderType` for pricing | OCP | Yes | Strategy pattern eliminates the switch |
| Internal helper class, 30 lines | SRP | No | It already has one job |
| Repository used only by commands | ISP | Maybe | Split if query side exists separately |
| Class with one implementation, no tests | DIP | No | Add interface when you need a seam |
| Base class where subtypes skip methods | LSP | Yes | Subtypes must honor the full contract |
| 3+ implementations of same behavior | OCP | Yes | Add via registration, not modification |
| Simple CRUD API, no domain logic | All | No | SOLID adds overhead with no payoff |
| Shared library consumed by many teams | ISP | Yes | Consumers should not depend on unused methods |
| Unit testing a class with external deps | DIP | Yes | Interface enables mocking |

## Anti-Patterns

| Problem | Why It Hurts | Correct Approach |
|---------|-------------|-----------------|
| One interface per class, always | Doubles file count, adds indirection with no benefit | Create interfaces when you have 2+ implementations or need a test seam |
| God class with 500+ lines | Impossible to test, understand, or modify safely | Split by responsibility into focused classes |
| Deep inheritance hierarchies | Fragile base class problem, tight coupling | Prefer composition and interface implementation |
| Empty interface methods (`NotImplementedException`) | Violates LSP, callers cannot trust the contract | Segregate interfaces so each implementor uses all methods |
| Abstracting everything on day one | Premature abstraction slows development and obscures intent | Start concrete, extract when the second use case appears |
| Injecting 8+ dependencies in constructor | Signals SRP violation — class does too much | Split the class or introduce a facade/mediator |
| Creating `IMapper`, `ILogger` wrappers | Wrapping well-tested libraries adds no value | Use `AutoMapper`/`Mapster` and `ILogger<T>` directly |
| Refactoring stable, working code "for SOLID" | Risk of introducing bugs in code that works | Apply SOLID when you need to change the code, not before |

## Detect Existing Patterns

1. Search for large classes: files with 300+ lines may violate SRP
2. Search for `switch` or long `if-else` chains that grow with new types (OCP candidate)
3. Search for `NotImplementedException` — signals ISP or LSP violation
4. Search for classes with 5+ constructor parameters — possible SRP violation
5. Check if interfaces have exactly one implementation (possible interface explosion)

## Adding to Existing Project

1. **Audit pain points first** — don't refactor what isn't causing problems
2. **Start with DIP** — add interfaces where you need testability
3. **Apply SRP** — split god classes when you need to modify them
4. **Use OCP** — extract strategies when you see a third case added to a switch
5. **Apply ISP** — split interfaces when implementors leave methods empty
6. **Check LSP** — verify subtypes when you see unexpected behavior in polymorphic code
