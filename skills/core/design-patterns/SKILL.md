---
name: design-patterns

description: >
  Modern C# design pattern catalog with decision guidance, when to use each pattern,
  when NOT to use, and which GoF patterns are replaced by language features.
  Trigger: design pattern, factory, builder, strategy, decorator, observer, mediator, singleton.
metadata:
  category: core
  agent: dotnet-architect
  alwaysApply: true
---

# Design Patterns in Modern C#

## Core Principles

- Patterns solve recurring design problems — don't force them where none exist
- Always ask: "Does modern C# already solve this with a language feature or framework API?"
- Don't blindly apply GoF. Half of the original 23 patterns are obsoleted by delegates, generics, records, and DI containers
- Prefer the simplest solution: language feature > framework convention > lightweight pattern > full GoF pattern
- Every pattern adds indirection — only pay that cost when the benefit is clear

## When to Use

- Complex systems with clear recurring structural or behavioral problems
- Multiple implementations behind a single abstraction that vary at runtime
- Cross-cutting concerns that must be composed without modifying core logic
- Codebases with multiple teams where patterns enforce consistency
- Domain logic with genuinely complex state transitions or construction rules

## When NOT to Use

- **YAGNI** — don't add a pattern "just in case" future complexity arrives
- **Simple CRUD** — a controller calling a repository needs no Strategy, no Mediator, no Factory
- **Language features suffice** — delegates replace Strategy, events replace Observer, records replace Prototype
- **Only one implementation** — an interface with a single class is ceremony, not abstraction
- **Premature abstraction** — wait until you see duplication or variation before extracting a pattern

## Creational Patterns

### Factory Method

Use DI as the modern replacement. Keep Factory Method only for polymorphic creation where the type is chosen at runtime.

```csharp
// Modern: DI + factory delegate
services.AddScoped<Func<string, INotificationSender>>(sp => channel => channel switch
{
    "email" => sp.GetRequiredService<EmailSender>(),
    "sms"   => sp.GetRequiredService<SmsSender>(),
    _       => throw new ArgumentOutOfRangeException(nameof(channel))
});
```

- **Use when**: the concrete type depends on runtime data (user input, config, feature flags)
- **Skip when**: there is only one implementation — just register it directly in DI

### Builder

Modern C# `init` properties and record positional syntax eliminate most Builder needs. Keep Builder only for complex multi-step construction with validation.

```csharp
// Modern replacement: record with positional syntax
public sealed record OrderRequest(string CustomerId, List<LineItem> Items, string? CouponCode = null);

// Keep Builder when construction is complex and multi-step
public sealed class ReportBuilder
{
    private readonly List<ReportSection> _sections = [];
    public ReportBuilder AddSection(ReportSection section) { _sections.Add(section); return this; }
    public Report Build() => _sections.Count == 0
        ? throw new InvalidOperationException("Report must have at least one section")
        : new Report([.. _sections]);
}
```

- **Use when**: construction requires multiple steps, ordering constraints, or cross-field validation
- **Skip when**: a record or class with `init` properties covers all fields cleanly

### Singleton

Never use the classic double-lock singleton. The DI container owns object lifetime.

```csharp
// Modern: DI container manages the lifetime
services.AddSingleton<IDateTimeProvider, DateTimeProvider>();
services.AddSingleton<HybridCache>();
```

- **Use when**: you need exactly one instance — register it as `AddSingleton` in DI
- **Skip when**: always skip the manual `static Instance` pattern; let the DI container handle it

## Structural Patterns

### Adapter

Wraps an incompatible interface so it conforms to the one your code expects.

```csharp
public sealed class LegacyPaymentAdapter(LegacyPaymentApi legacy) : IPaymentGateway
{
    public async Task<PaymentResult> ChargeAsync(decimal amount, CancellationToken ct)
    {
        var code = await legacy.ProcessPaymentXml($"<amount>{amount}</amount>");
        return new PaymentResult(code == 0, code.ToString());
    }
}
```

- **Use when**: integrating a third-party or legacy API whose shape doesn't match your abstractions
- **Skip when**: you control both sides — just change the interface directly

### Decorator

Adds behavior to an object without modifying it. MediatR pipeline behaviors are the modern poster child.

```csharp
// MediatR pipeline behavior as Decorator
public sealed class LoggingBehavior<TRequest, TResponse>(
    ILogger<LoggingBehavior<TRequest, TResponse>> logger)
    : IPipelineBehavior<TRequest, TResponse> where TRequest : notnull
{
    public async Task<TResponse> Handle(TRequest request,
        RequestHandlerDelegate<TResponse> next, CancellationToken ct)
    {
        logger.LogInformation("Handling {Request}", typeof(TRequest).Name);
        return await next(ct);
    }
}
```

- **Use when**: adding cross-cutting concerns (logging, caching, validation) to existing services
- **Skip when**: only one concern and one service — inline it rather than adding a wrapper layer

### Facade

Provides a simplified API over a complex subsystem. Common in application services.

```csharp
public sealed class OrderFacade(
    IOrderRepository orders, IPaymentGateway payments, IInventoryService inventory)
{
    public async Task<OrderResult> PlaceOrderAsync(PlaceOrderCommand cmd, CancellationToken ct)
    {
        await inventory.ReserveAsync(cmd.Items, ct);
        var payment = await payments.ChargeAsync(cmd.Total, ct);
        return await orders.CreateAsync(cmd, payment.TransactionId, ct);
    }
}
```

- **Use when**: callers (controllers, handlers) need a single entry point into multi-step operations
- **Skip when**: the subsystem is already simple — a facade over one call is pointless indirection

### Proxy

Controls access to an object — commonly for lazy loading, caching, or authorization.

```csharp
public sealed class CachedProductService(
    IProductService inner, HybridCache cache) : IProductService
{
    public async Task<Product?> GetByIdAsync(Guid id, CancellationToken ct)
        => await cache.GetOrCreateAsync($"product:{id}",
            async token => await inner.GetByIdAsync(id, token), cancellationToken: ct);
}
```

- **Use when**: you need transparent caching, lazy initialization, or access control around an existing service
- **Skip when**: the concern can be handled at a higher level (e.g., response caching middleware)

## Behavioral Patterns

### Strategy

Delegates and `Func<T>` are the lightweight alternative. Use DI for injectable strategies.

```csharp
// Lightweight: Func<T> delegate
public sealed class PricingEngine(Func<Order, decimal> discountStrategy)
{
    public decimal Calculate(Order order) => order.SubTotal - discountStrategy(order);
}

// DI-based: keyed services (.NET 8+)
services.AddKeyedScoped<IShippingCalculator, StandardShipping>("standard");
services.AddKeyedScoped<IShippingCalculator, ExpressShipping>("express");
```

- **Use when**: behavior varies at runtime and you have 2+ concrete strategies
- **Skip when**: a single `Func<T>` or lambda covers the variation without needing a full interface

### Observer

C# events and MediatR notifications replace the classic Observer pattern.

```csharp
// Modern: MediatR notification (pub-sub)
public sealed record OrderPlacedEvent(Guid OrderId, decimal Total) : INotification;

public sealed class SendConfirmationEmail(IEmailSender email)
    : INotificationHandler<OrderPlacedEvent>
{
    public async Task Handle(OrderPlacedEvent e, CancellationToken ct)
        => await email.SendOrderConfirmationAsync(e.OrderId, ct);
}
```

- **Use when**: multiple independent handlers must react to the same event
- **Skip when**: only one subscriber exists — call it directly instead of adding pub-sub overhead

### Command

MediatR `IRequest` is the standard modern implementation.

```csharp
public sealed record CreateOrderCommand(string CustomerId, List<LineItem> Items)
    : IRequest<Guid>;

public sealed class CreateOrderHandler(IOrderRepository repo, IUnitOfWork uow)
    : IRequestHandler<CreateOrderCommand, Guid>
{
    public async Task<Guid> Handle(CreateOrderCommand cmd, CancellationToken ct)
    {
        var order = Order.Create(cmd.CustomerId, cmd.Items);
        repo.Add(order);
        await uow.SaveChangesAsync(ct);
        return order.Id;
    }
}
```

- **Use when**: you want to encapsulate operations as objects for queuing, logging, or undo
- **Skip when**: simple pass-through calls with no cross-cutting pipeline needs

### Mediator

MediatR itself implements this pattern — decouples senders from receivers.

```csharp
// Controller sends; handler receives — no direct dependency
app.MapPost("/orders", async (CreateOrderCommand cmd, ISender sender) =>
    Results.Created($"/orders/{await sender.Send(cmd)}", null));
```

- **Use when**: you want to decouple request handling from controllers and add pipeline behaviors
- **Skip when**: the project is small with few handlers — direct service calls are simpler

### Chain of Responsibility

ASP.NET Core middleware pipeline is the canonical modern example.

```csharp
// Custom middleware — chain of responsibility
app.Use(async (context, next) =>
{
    var sw = Stopwatch.StartNew();
    await next(context);
    context.Response.Headers.Append("X-Elapsed-Ms", sw.ElapsedMilliseconds.ToString());
});
```

- **Use when**: multiple processors must handle a request in sequence with optional short-circuiting
- **Skip when**: only one processing step is needed — use a simple method call

### State

Use enum-based state machines for simple cases. Reserve the full State pattern for complex transitions.

```csharp
// Simple: enum + switch
public sealed class Order
{
    public OrderState State { get; private set; } = OrderState.Draft;

    public void Submit() => State = State switch
    {
        OrderState.Draft => OrderState.Submitted,
        _ => throw new InvalidOperationException($"Cannot submit from {State}")
    };

    public void Approve() => State = State switch
    {
        OrderState.Submitted => OrderState.Approved,
        _ => throw new InvalidOperationException($"Cannot approve from {State}")
    };
}
```

- **Use when**: an entity has complex state transitions with different behavior per state
- **Skip when**: transitions are linear and simple — an enum with switch expressions suffices

## Patterns Replaced by Language Features

| GoF Pattern | Modern C# Replacement | Example |
|-------------|----------------------|---------|
| Strategy | `Func<T>`, delegates | `Func<Order, decimal>` passed to constructor |
| Observer | `event`, `INotification` | MediatR notifications or C# events |
| Template Method | `Func<T>` parameters | Pass steps as delegates instead of subclassing |
| Prototype | `record` with `with` | `order with { Status = "Shipped" }` |
| Iterator | `IEnumerable<T>`, LINQ | `yield return`, `foreach`, LINQ operators |
| Singleton | DI `AddSingleton` | Container-managed lifetime |
| Command | `record` + MediatR | `IRequest<T>` with pipeline behaviors |
| Visitor | Pattern matching | Switch expressions with type patterns |
| Null Object | Nullable reference types | `T?` with null-conditional operators |
| Bridge | Generics + interfaces | `IRepository<T>` with generic constraints |

## Decision Guide

| Problem | Recommended Pattern | Why |
|---------|-------------------|-----|
| Runtime type selection | Factory Method via DI delegate | Clean, testable, no `new` keywords |
| Complex object construction | Builder | Enforces step order and validation |
| Incompatible third-party API | Adapter | Isolates integration behind your interface |
| Cross-cutting concerns (logging, caching) | Decorator / MediatR behaviors | Composable without modifying core logic |
| Multiple handlers for one event | Observer via MediatR notifications | Decoupled pub-sub |
| Varying algorithm at runtime | Strategy via `Func<T>` or keyed DI | Lightweight, no interface explosion |
| Sequential request processing | Chain of Responsibility (middleware) | ASP.NET Core already provides the pipeline |
| Entity with complex lifecycle | State (enum-based first) | Prevents invalid transitions |
| Simplified entry point to subsystem | Facade | Reduces coupling for callers |

## Anti-Patterns

| Problem | Why It Hurts | Correct Approach |
|---------|-------------|-----------------|
| Applying every GoF pattern "just in case" | Massive over-engineering, hard to navigate | Add patterns only when a clear problem recurs |
| Classic `static Instance` singleton | Untestable, hides dependencies, threading issues | Use `AddSingleton` in DI container |
| Interface for every class | Empty abstractions, ceremony without benefit | Add interfaces when you have 2+ implementations or need testability |
| God Factory that creates everything | Single point of coupling, hard to extend | Separate factories per concern or use DI delegates |
| Repository pattern wrapping EF's DbSet | Double abstraction over an already-abstract ORM | Use DbContext directly or a thin specification pattern |
| Mediator for every call including simple queries | Indirection without benefit, harder debugging | Use Mediator for commands with pipeline needs; inject services directly for simple reads |
| Strategy interface with one implementation | YAGNI overhead | Use a concrete class; extract interface later if needed |
| Deep decorator chains | Hard to debug, unclear execution order | Limit to 2-3 decorators; prefer MediatR pipeline behaviors for ordering clarity |

## Detect Existing Patterns

1. Search for `IPipelineBehavior` — indicates MediatR decorator/pipeline usage
2. Search for `INotification` and `INotificationHandler` — Observer via MediatR
3. Search for `IRequest<T>` and `IRequestHandler` — Command via MediatR
4. Check `Program.cs` for `AddSingleton`, `AddScoped`, `AddTransient` patterns
5. Look for `AddKeyedSingleton` / `AddKeyedScoped` — keyed Strategy via DI
6. Search for classes implementing multiple interfaces of the same base — potential Adapter usage
7. Check for `app.Use(` middleware registrations — Chain of Responsibility

## References

- https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-design-patterns
- https://refactoring.guru/design-patterns/csharp
