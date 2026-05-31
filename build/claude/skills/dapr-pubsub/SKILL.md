---
name: dapr-pubsub
description: "Implements Dapr topic subscriptions with CloudEvents envelopes and dead-letter topics over a broker-agnostic pub-sub component. Use when publishing or subscribing to topics through the Dapr sidecar, handling the CloudEvents envelope, or routing failed messages to a DLQ. Do NOT use for state or service invocation (use dapr-building-blocks) or durable orchestration (use dapr-workflow)."
---
# Dapr Pub/Sub (Topics, CloudEvents, Dead-Letter)

Dapr pub-sub abstracts the broker (Redis, Kafka, Azure Service Bus, RabbitMQ) behind a **pubsub component**. Publishers and subscribers reference the component by name; Dapr wraps payloads in the **CloudEvents** envelope automatically.

## Core Principles

- Publish to a **topic** on a named pubsub component; never talk to the broker SDK directly.
- Dapr delivers a **CloudEvents** envelope — use `[Topic]`/`MapSubscribeHandler` so the SDK unwraps `data` into your type.
- Subscriptions are declared in code (attribute/endpoint) or in a subscription YAML; a `deadLetterTopic` captures messages that exhaust retries.
- Returning 200 ACKs the message; throwing (or 5xx) triggers retry, then dead-letter.

## Publish + Subscribe

```csharp
namespace {Company}.{Domain}.Service;

public sealed record OrderShipped(Guid OrderId, string Tracking);

// Publisher
public sealed class ShippingPublisher(DaprClient dapr)
{
    private const string PubSub = "orders-pubsub";   // == component metadata.name

    public Task PublishAsync(OrderShipped evt, CancellationToken ct) =>
        dapr.PublishEventAsync(PubSub, "order-shipped", evt, ct);
}

// Subscriber (ASP.NET Core minimal API) — Dapr unwraps the CloudEvent into OrderShipped.
app.MapPost("/events/order-shipped", [Topic("orders-pubsub", "order-shipped")]
    async (OrderShipped evt, IOrderProjection projection, CancellationToken ct) =>
{
    await projection.MarkShippedAsync(evt.OrderId, evt.Tracking, ct);
    return Results.Ok();   // 200 = ACK; throw/5xx = retry -> dead-letter
});

// Program.cs — AddDapr() enables CloudEvents model binding; MapSubscribeHandler exposes /dapr/subscribe.
builder.Services.AddControllers().AddDapr();
app.UseCloudEvents();
app.MapSubscribeHandler();
```

## Component + Dead-Letter Subscription

```yaml
# components/orders-pubsub.yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: orders-pubsub
spec:
  type: pubsub.redis
  version: v1
  metadata:
    - name: redisHost
      value: localhost:6379
---
# components/order-shipped-sub.yaml  — declarative subscription with DLQ
apiVersion: dapr.io/v2alpha1
kind: Subscription
metadata:
  name: order-shipped-sub
spec:
  pubsubname: orders-pubsub
  topic: order-shipped
  deadLetterTopic: order-shipped-dlq   # failed deliveries land here
  routes:
    default: /events/order-shipped
```

## Delivery Semantics

| Outcome | HTTP from handler | Dapr action |
|---------|-------------------|-------------|
| Success | 200 | ACK, remove from topic |
| Retryable failure | throw / 5xx | Retry per policy, then `deadLetterTopic` |
| Drop (poison, non-retryable) | return `Results.Ok()` after logging | ACK to avoid a hot loop |

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Binding to the raw CloudEvent JSON | `UseCloudEvents()` + typed handler unwraps `data` |
| No dead-letter topic | Set `deadLetterTopic`; add a DLQ subscriber |
| Returning 200 on a transient error | Throw so Dapr retries |
| Calling the broker SDK directly | Publish via `PublishEventAsync(component, topic, …)` |

## Adding to an Existing Project

1. Add `Dapr.AspNetCore`; call `AddDapr()`, `UseCloudEvents()`, `MapSubscribeHandler()`.
2. Add a pubsub component YAML for the broker.
3. Publish with `DaprClient.PublishEventAsync(component, topic, payload)`.
4. Add a subscribe endpoint (`[Topic]`) or a Subscription YAML with `deadLetterTopic`.
5. Add a subscriber for the DLQ topic to inspect/replay failures.

## References

- https://docs.dapr.io/developing-applications/building-blocks/pubsub/
