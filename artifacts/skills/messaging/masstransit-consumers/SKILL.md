---
name: masstransit-consumers
description: "Implements MassTransit consumers with retry, redelivery, and dead-lettering across RabbitMQ and Azure Service Bus. Use when consuming messages through MassTransit's IConsumer pipeline, configuring transport endpoints, or tuning fault handling. Do NOT use for saga/state-machine workflows (use masstransit-sagas), and prefer wolverine-messaging when the MassTransit v9+ commercial license is a blocker."
metadata:
  category: "messaging"
  agent: "processor-architect"
---
# MassTransit Consumers

> **License note:** MassTransit **v8** is Apache-2.0; **v9+ is commercial**. For new license-safe work, prefer `wolverine-messaging`. Use these patterns when you are already on MassTransit or have a v9 license.

## Core Principles

- One `IConsumer<TMessage>` per message type — single responsibility.
- Retry handles *transient* faults in-process; redelivery defers *longer* outages; the error queue (`_error`) is the dead-letter of last resort.
- Configure retry/redelivery **per endpoint**, not globally, so a slow consumer cannot starve others.
- Always propagate the consume `CancellationToken`.

## Consumer + Endpoint Configuration

```csharp
namespace {Company}.{Domain}.Processor.Consumers;

public sealed record OrderSubmitted(Guid OrderId, decimal Total);

public sealed class OrderSubmittedConsumer(
    IOrderProjection projection,
    ILogger<OrderSubmittedConsumer> logger)
    : IConsumer<OrderSubmitted>
{
    public async Task Consume(ConsumeContext<OrderSubmitted> context)
    {
        var msg = context.Message;
        logger.LogInformation("Projecting order {OrderId}", msg.OrderId);
        await projection.ApplyAsync(msg.OrderId, msg.Total, context.CancellationToken);
    }
}

// Program.cs — pick ONE transport block.
builder.Services.AddMassTransit(x =>
{
    x.AddConsumer<OrderSubmittedConsumer>();

    // RabbitMQ
    x.UsingRabbitMq((ctx, cfg) =>
    {
        cfg.Host("rabbitmq://localhost", h => { h.Username("guest"); h.Password("guest"); });
        cfg.ReceiveEndpoint("order-submitted", e =>
        {
            // Transient faults: short, in-memory retries.
            e.UseMessageRetry(r => r.Interval(3, TimeSpan.FromSeconds(5)));
            // Longer outages: requeue with backoff (survives restarts).
            e.UseDelayedRedelivery(r => r.Intervals(
                TimeSpan.FromMinutes(1), TimeSpan.FromMinutes(5), TimeSpan.FromMinutes(15)));
            e.ConfigureConsumer<OrderSubmittedConsumer>(ctx);
        });
    });

    // Azure Service Bus — swap the block above for this one.
    // x.UsingAzureServiceBus((ctx, cfg) =>
    // {
    //     cfg.Host(builder.Configuration.GetConnectionString("ServiceBus"));
    //     cfg.ReceiveEndpoint("order-submitted", e =>
    //     {
    //         e.MaxDeliveryCount = 5;        // native ASB DLQ after N attempts
    //         e.UseMessageRetry(r => r.Interval(3, TimeSpan.FromSeconds(5)));
    //         e.ConfigureConsumer<OrderSubmittedConsumer>(ctx);
    //     });
    // });
});
```

## Retry vs Redelivery vs Dead-Letter

| Layer | Use for | Mechanism |
|-------|---------|-----------|
| `UseMessageRetry` | Transient blips (deadlock, timeout) | In-memory, immediate |
| `UseDelayedRedelivery` | Dependency down for minutes | Scheduler/requeue with backoff |
| Error queue / ASB DLQ | Poison messages | `_error` queue (Rabbit) or `MaxDeliveryCount` (ASB) |

## Idempotency

Consumers MAY run more than once (at-least-once delivery). Key writes by `context.MessageId` or a business key (e.g. `OrderId`) so reprocessing is a no-op.

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Catch-and-swallow inside `Consume` | Let it throw — retry/redelivery handle it |
| One giant consumer with `switch` on type | One `IConsumer<T>` per message type |
| Global retry policy only | Configure per receive endpoint |
| Assuming exactly-once delivery | Make consumers idempotent |
| Upgrading to MassTransit v9+ unaware | v9+ is commercial — confirm license or use Wolverine |

## Adding to an Existing Project

1. Add `MassTransit` + the transport package (`MassTransit.RabbitMQ` or `MassTransit.Azure.ServiceBus.Core`); confirm a v8 ceiling unless licensed for v9+.
2. Define the message contract (record) in a shared contracts assembly.
3. Add the `IConsumer<T>`; register with `AddConsumer<T>()`.
4. Map a receive endpoint with retry + (RabbitMQ) delayed redelivery, or set `MaxDeliveryCount` on ASB.
5. Make the consumer idempotent on `MessageId`/business key.

## References

- https://masstransit.io (note v9+ licensing)
