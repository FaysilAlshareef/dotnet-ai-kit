---
name: notification-handlers
description: >
  Domain event dispatch using MediatR notifications. Multiple handlers per event,
  dispatch after persistence, and idempotent handling.
  Trigger: domain event, notification, INotification, event handler, publish.
category: cqrs
agent: ef-specialist
---

# Notification Handlers (Domain Events)

## Core Principles

- Domain events represent something that happened in the domain
- Multiple handlers can react to a single event (one-to-many)
- Dispatch events after successful persistence (not before SaveChanges)
- Handlers should be idempotent for at-least-once delivery
- Events are named in past tense: `OrderCreated`, `OrderShipped`

## Patterns

### Domain Event Interface

```csharp
public interface IDomainEvent : INotification
{
    DateTimeOffset OccurredAt { get; }
}

public abstract record DomainEvent : IDomainEvent
{
    public DateTimeOffset OccurredAt { get; } = DateTimeOffset.UtcNow;
}
```

### Concrete Domain Events

```csharp
public sealed record OrderCreatedEvent(
    Guid OrderId,
    string CustomerName) : DomainEvent;

public sealed record OrderSubmittedEvent(
    Guid OrderId,
    decimal Total) : DomainEvent;

public sealed record OrderCancelledEvent(
    Guid OrderId,
    string Reason) : DomainEvent;

public sealed record OrderItemAddedEvent(
    Guid OrderId,
    Guid ProductId,
    int Quantity) : DomainEvent;
```

### Raising Events from Aggregates

```csharp
public abstract class AggregateRoot
{
    private readonly List<IDomainEvent> _domainEvents = [];
    public IReadOnlyList<IDomainEvent> DomainEvents =>
        _domainEvents.AsReadOnly();

    protected void RaiseDomainEvent(IDomainEvent domainEvent)
        => _domainEvents.Add(domainEvent);

    public void ClearDomainEvents() => _domainEvents.Clear();
}

public sealed class Order : AggregateRoot
{
    public static Order Create(string customerName)
    {
        var order = new Order { CustomerName = customerName };
        order.RaiseDomainEvent(
            new OrderCreatedEvent(order.Id, customerName));
        return order;
    }

    public void Submit()
    {
        if (Status != OrderStatus.Draft)
            throw new DomainException("Only draft orders can submit");

        Status = OrderStatus.Submitted;
        RaiseDomainEvent(new OrderSubmittedEvent(Id, Total));
    }
}
```

### Notification Handlers

```csharp
// Handler 1: Send confirmation email
internal sealed class SendOrderConfirmationOnCreated(
    IEmailService emailService,
    ILogger<SendOrderConfirmationOnCreated> logger)
    : INotificationHandler<OrderCreatedEvent>
{
    public async Task Handle(
        OrderCreatedEvent notification, CancellationToken ct)
    {
        logger.LogInformation(
            "Sending confirmation for order {OrderId}",
            notification.OrderId);

        await emailService.SendOrderConfirmationAsync(
            notification.OrderId, notification.CustomerName, ct);
    }
}

// Handler 2: Update dashboard stats
internal sealed class UpdateDashboardOnOrderCreated(AppDbContext db)
    : INotificationHandler<OrderCreatedEvent>
{
    public async Task Handle(
        OrderCreatedEvent notification, CancellationToken ct)
    {
        var stats = await db.DashboardStats.SingleAsync(ct);
        stats.IncrementOrderCount();
        await db.SaveChangesAsync(ct);
    }
}

// Handler 3: Reserve inventory
internal sealed class ReserveInventoryOnOrderSubmitted(
    IInventoryService inventoryService)
    : INotificationHandler<OrderSubmittedEvent>
{
    public async Task Handle(
        OrderSubmittedEvent notification, CancellationToken ct)
    {
        await inventoryService.ReserveForOrderAsync(
            notification.OrderId, ct);
    }
}
```

### Dispatch After SaveChanges (Interceptor)

```csharp
public sealed class DomainEventDispatcher(IPublisher publisher)
    : SaveChangesInterceptor
{
    public override async ValueTask<int> SavedChangesAsync(
        SaveChangesCompletedEventData eventData,
        int result,
        CancellationToken ct = default)
    {
        var context = eventData.Context!;

        // Collect events from all aggregates
        var aggregates = context.ChangeTracker
            .Entries<AggregateRoot>()
            .Select(e => e.Entity)
            .Where(e => e.DomainEvents.Count > 0)
            .ToList();

        var events = aggregates
            .SelectMany(a => a.DomainEvents)
            .ToList();

        // Clear events before dispatch to prevent re-dispatch
        aggregates.ForEach(a => a.ClearDomainEvents());

        // Dispatch each event
        foreach (var domainEvent in events)
            await publisher.Publish(domainEvent, ct);

        return result;
    }
}

// Registration
builder.Services.AddSingleton<DomainEventDispatcher>();
builder.Services.AddDbContext<AppDbContext>((sp, options) =>
{
    options.AddInterceptors(
        sp.GetRequiredService<DomainEventDispatcher>());
});
```

### Idempotent Handler

```csharp
internal sealed class ProcessOrderPaymentOnSubmitted(
    AppDbContext db,
    IPaymentService paymentService)
    : INotificationHandler<OrderSubmittedEvent>
{
    public async Task Handle(
        OrderSubmittedEvent notification, CancellationToken ct)
    {
        // Idempotency check — skip if already processed
        var alreadyProcessed = await db.PaymentRecords
            .AnyAsync(p => p.OrderId == notification.OrderId, ct);

        if (alreadyProcessed)
            return;

        await paymentService.ChargeAsync(
            notification.OrderId, notification.Total, ct);

        db.PaymentRecords.Add(new PaymentRecord
        {
            OrderId = notification.OrderId,
            Amount = notification.Total,
            ProcessedAt = DateTimeOffset.UtcNow
        });

        await db.SaveChangesAsync(ct);
    }
}
```

### Manual Dispatch (Without Interceptor)

```csharp
// Alternative: dispatch events in the handler directly
internal sealed class SubmitOrderHandler(
    IOrderRepository repository,
    IUnitOfWork unitOfWork,
    IPublisher publisher)
    : IRequestHandler<SubmitOrderCommand, Result>
{
    public async Task<Result> Handle(
        SubmitOrderCommand request, CancellationToken ct)
    {
        var order = await repository.FindAsync(request.OrderId, ct);
        if (order is null)
            return Result.Failure(
                Error.NotFound("Order.NotFound", "Order not found"));

        order.Submit();
        await unitOfWork.SaveChangesAsync(ct);

        // Dispatch events after successful save
        foreach (var domainEvent in order.DomainEvents)
            await publisher.Publish(domainEvent, ct);
        order.ClearDomainEvents();

        return Result.Success();
    }
}
```

## Anti-Patterns

- Dispatching events before SaveChanges (data may not be persisted)
- Business logic in notification handlers (keep for side effects only)
- Non-idempotent handlers with at-least-once delivery
- Throwing exceptions in handlers that block other handlers
- Synchronous cross-service calls in notification handlers

## Detect Existing Patterns

1. Search for `INotification` and `INotificationHandler<` implementations
2. Look for `IDomainEvent` or `DomainEvent` base types
3. Check for `RaiseDomainEvent` or `AddDomainEvent` in entities
4. Look for `SaveChangesInterceptor` that dispatches events
5. Search for `IPublisher.Publish` calls

## Adding to Existing Project

1. **Define `IDomainEvent`** interface extending `INotification`
2. **Add event collection** to aggregate root base class
3. **Create concrete events** for key domain state changes
4. **Add dispatch interceptor** to DbContext configuration
5. **Create notification handlers** for side effects (email, analytics, etc.)
6. **Ensure idempotency** in all handlers

## References

- https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/domain-events-design-implementation
- https://github.com/jbogard/MediatR/wiki#notifications
