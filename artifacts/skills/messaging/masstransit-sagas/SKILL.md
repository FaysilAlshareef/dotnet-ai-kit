---
name: masstransit-sagas
description: "Implements MassTransit saga state machines with correlation and durable persistence to coordinate long-running, multi-message workflows. Use when orchestrating a process that spans several messages and needs persisted state (order fulfillment, payment, provisioning). Do NOT use for single-message handlers (use masstransit-consumers); prefer wolverine-messaging or dapr-workflow when the MassTransit v9+ commercial license is a concern."
metadata:
  category: "messaging"
  agent: "processor-architect"
---
# MassTransit Sagas (State Machines)

> **License note:** MassTransit **v8** is Apache-2.0; **v9+ is commercial**. For license-safe durable orchestration consider `dapr-workflow` or `wolverine-messaging`.

## Core Principles

- A saga is **persisted state + a state machine**: every message advances one instance.
- **Correlation** binds every event to one instance via a shared `CorrelationId` (usually the business key, e.g. `OrderId`).
- State lives in a `SagaStateMachineInstance` repository (EF Core, Redis, etc.) — never in memory for production.
- Model explicit `State`s and `Event`s; the machine is the single source of truth for "what happens next".

## State, Instance, and Machine

```csharp
namespace {Company}.{Domain}.Processor.Sagas;

// Persisted instance — one row per in-flight order.
public sealed class OrderState : SagaStateMachineInstance
{
    public Guid CorrelationId { get; set; }   // == OrderId
    public string CurrentState { get; set; } = default!;
    public decimal Total { get; set; }
    public DateTime SubmittedAtUtc { get; set; }
}

public sealed class OrderStateMachine : MassTransitStateMachine<OrderState>
{
    public State Submitted { get; private set; } = default!;
    public State Paid { get; private set; } = default!;

    public Event<OrderSubmitted> OrderSubmitted { get; private set; } = default!;
    public Event<PaymentReceived> PaymentReceived { get; private set; } = default!;

    public OrderStateMachine()
    {
        InstanceState(x => x.CurrentState);

        // Every event correlates by the same key.
        Event(() => OrderSubmitted, e => e.CorrelateById(m => m.Message.OrderId));
        Event(() => PaymentReceived, e => e.CorrelateById(m => m.Message.OrderId));

        Initially(
            When(OrderSubmitted)
                .Then(ctx => { ctx.Saga.Total = ctx.Message.Total; ctx.Saga.SubmittedAtUtc = DateTime.UtcNow; })
                .TransitionTo(Submitted));

        During(Submitted,
            When(PaymentReceived)
                .Publish(ctx => new OrderConfirmed(ctx.Saga.CorrelationId))
                .TransitionTo(Paid)
                .Finalize());

        SetCompletedWhenFinalized();   // remove the row once Paid + finalized
    }
}
```

## Registration with EF Core Persistence

```csharp
builder.Services.AddMassTransit(x =>
{
    x.AddSagaStateMachine<OrderStateMachine, OrderState>()
        .EntityFrameworkRepository(r =>
        {
            r.ConcurrencyMode = ConcurrencyMode.Optimistic;   // optimistic concurrency on the row
            r.ExistingDbContext<SagaDbContext>();
        });

    x.UsingRabbitMq((ctx, cfg) => cfg.ConfigureEndpoints(ctx));
});
```

## Correlation & Concurrency

| Concern | Rule |
|---------|------|
| Correlation | Same `CorrelationId` across all events; `CorrelateById` on the business key |
| Concurrency | Use `ConcurrencyMode.Optimistic` (or pessimistic row locks) — two events for one instance can race |
| Timeouts | Use `Schedule` + a timeout event to escape stuck states |
| Cleanup | `Finalize()` + `SetCompletedWhenFinalized()` to delete completed instances |

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| In-memory saga repository in production | Use EF Core / Redis durable persistence |
| Business logic in consumers instead of the machine | The state machine owns the workflow |
| No concurrency mode | Set Optimistic (or pessimistic) — events race |
| Forgetting to finalize | `Finalize()` so rows do not accumulate forever |
| Reaching v9+ unaware | v9+ is commercial — confirm license or use an alternative |

## Adding to an Existing Project

1. Add `MassTransit.EntityFrameworkCore` (confirm a v8 ceiling unless licensed for v9+).
2. Define the `SagaStateMachineInstance` and `MassTransitStateMachine<T>`.
3. Add a `SagaDbContext` mapping the instance table; create a migration.
4. Register with `AddSagaStateMachine<,>().EntityFrameworkRepository(...)`.
5. Correlate every event by the business key; set a concurrency mode.

## References

- https://masstransit.io/documentation/patterns/saga (note v9+ licensing)
