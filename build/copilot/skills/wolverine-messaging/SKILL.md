---
name: wolverine-messaging
description: "Implements Wolverine (MIT) message handlers with the transactional outbox/inbox and mediator mode as the license-safe default bus. Use when you need in-process dispatch or a durable message bus without a commercial dependency, or when migrating off MediatR/MassTransit. Do NOT use for MassTransit-specific saga state machines (use masstransit-sagas) or Dapr-runtime pub-sub (use dapr-pubsub)."
---
# Wolverine Messaging (MIT, License-Safe Default)

Wolverine is **MIT-licensed** and covers both roles MediatR and MassTransit split between: an in-process **mediator** *and* a durable **message bus** with a built-in transactional outbox/inbox. It is the recommended default when license terms matter.

## Core Principles

- **Convention over interfaces:** a handler is a public class with a `Handle`/`Consume` method whose first parameter is the message — no marker interface required.
- One handler method per message type; dependencies are method-injected.
- The **outbox** makes "save state + publish message" atomic; the **inbox** dedupes inbound delivery.
- `IMessageBus` is the single dispatch seam — use it where you would use `ISender`.

## Handler + Mediator Mode

```csharp
namespace {Company}.{Domain}.Application.Orders;

public sealed record CreateOrder(string Customer, decimal Total);
public sealed record OrderCreated(Guid OrderId);

public static class CreateOrderHandler
{
    // Return value(s) become cascaded messages — published automatically.
    public static async Task<OrderCreated> Handle(
        CreateOrder command,
        IOrderRepository repository,   // method injection
        CancellationToken ct)
    {
        var order = Order.Create(command.Customer, command.Total);
        await repository.AddAsync(order, ct);
        return new OrderCreated(order.Id);
    }
}

// Endpoint uses IMessageBus instead of MediatR's ISender.
app.MapPost("/orders", async (CreateOrder cmd, IMessageBus bus) =>
{
    var created = await bus.InvokeAsync<OrderCreated>(cmd);   // mediator mode
    return Results.Created($"/orders/{created.OrderId}", created);
});
```

## Bootstrapping + Transactional Outbox

```csharp
// Program.cs
builder.Host.UseWolverine(opts =>
{
    // Durable transport (RabbitMQ shown); Azure Service Bus available too.
    opts.UseRabbitMq(builder.Configuration.GetConnectionString("rabbit"))
        .AutoProvision();

    // Persist outbox/inbox alongside your EF Core transaction.
    opts.PersistMessagesWithSqlServer(builder.Configuration.GetConnectionString("db"));
    opts.Policies.UseDurableOutboxOnAllSendingEndpoints();
    opts.Policies.AutoApplyTransactions();   // handler + outbox commit together

    // Retries / error handling.
    opts.OnException<TimeoutException>().RetryWithCooldown(
        TimeSpan.FromSeconds(1), TimeSpan.FromSeconds(5), TimeSpan.FromSeconds(15));
});
```

`AutoApplyTransactions` wraps the handler and the outbox in one transaction: the message is only sent if the state change commits, and only once.

## Mediator vs Bus

| Mode | Call | Use for |
|------|------|---------|
| Mediator (local) | `bus.InvokeAsync<T>(cmd)` | Request/response in-process (MediatR replacement) |
| Fire-and-forget | `bus.PublishAsync(evt)` | Domain events to local + remote subscribers |
| Cascading | `return`/`yield return` messages | Emit follow-up messages from a handler |

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Manual "save then publish" without outbox | `UseDurableOutboxOnAllSendingEndpoints` + `AutoApplyTransactions` |
| Marker interfaces / base classes for handlers | Convention: public class + `Handle` method |
| Constructor-injecting transient deps into static handler | Use method injection per `Handle` |
| Sharing one handler for many message types | One method per message type |

## Adding to an Existing Project

1. Add `WolverineFx` (+ `WolverineFx.RabbitMq` / `.AzureServiceBus`, `.EntityFrameworkCore` as needed).
2. `builder.Host.UseWolverine(...)`; configure transport + message persistence.
3. Enable `UseDurableOutboxOnAllSendingEndpoints()` and `AutoApplyTransactions()`.
4. Replace `ISender`/`IMediator` usage with `IMessageBus.InvokeAsync<T>`.
5. Convert handlers to convention-based `Handle` methods; return cascaded messages.

## References

- https://wolverinefx.net (MIT)
