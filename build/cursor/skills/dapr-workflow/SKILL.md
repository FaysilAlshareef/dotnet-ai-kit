---
name: dapr-workflow
description: "Orchestrates durable, long-running workflows with the Dapr Workflow SDK using activities, timers, and external events. Use when you need replay-safe orchestration with built-in state persistence and retries across service restarts. Do NOT use for fire-and-forget pub-sub (use dapr-pubsub) or plain state/service-invocation calls (use dapr-building-blocks)."
---
# Dapr Workflow (Durable Orchestration)

The Dapr Workflow SDK provides **durable, replay-based orchestration**: the runtime persists progress and re-runs the orchestrator on each event, so a workflow survives crashes and restarts without you managing state.

## Core Principles

- The **orchestrator** is deterministic: it only schedules activities/timers and awaits them — no direct I/O, `DateTime.Now`, random, or `Guid.NewGuid()` (the runtime *replays* it).
- **Activities** do the real, non-deterministic work (DB, HTTP, sending messages) and are individually retried.
- Use `CreateTimer` for durable delays and `WaitForExternalEventAsync` to pause for an outside signal (approval, callback).
- State persistence rides on a Dapr **actor state store** — no extra schema to design.

## Orchestrator + Activity

```csharp
namespace {Company}.{Domain}.Service.Workflows;

public sealed class OrderWorkflow : Workflow<OrderInput, OrderResult>
{
    public override async Task<OrderResult> RunAsync(WorkflowContext ctx, OrderInput input)
    {
        // Deterministic: only schedule + await.
        await ctx.CallActivityAsync(nameof(ReserveStock), input.OrderId);

        // Durable timer instead of Task.Delay.
        await ctx.CreateTimer(TimeSpan.FromMinutes(5));

        // Pause until an external "PaymentApproved" event arrives (with timeout).
        var approval = await ctx.WaitForExternalEventAsync<bool>("PaymentApproved", TimeSpan.FromHours(1));
        if (!approval)
        {
            await ctx.CallActivityAsync(nameof(ReleaseStock), input.OrderId);
            return new OrderResult(input.OrderId, "Cancelled");
        }

        await ctx.CallActivityAsync(nameof(ShipOrder), input.OrderId);
        return new OrderResult(input.OrderId, "Shipped");
    }
}

public sealed class ReserveStock(IInventory inventory) : WorkflowActivity<Guid, bool>
{
    // Non-deterministic work lives here, not in the orchestrator.
    public override Task<bool> RunAsync(WorkflowActivityContext _, Guid orderId) =>
        inventory.ReserveAsync(orderId);
}

// Program.cs
builder.Services.AddDaprWorkflow(o =>
{
    o.RegisterWorkflow<OrderWorkflow>();
    o.RegisterActivity<ReserveStock>();
    o.RegisterActivity<ReleaseStock>();
    o.RegisterActivity<ShipOrder>();
});
```

## Start, Signal, Query

```csharp
// Inject DaprWorkflowClient.
await client.ScheduleNewWorkflowAsync(nameof(OrderWorkflow), instanceId: orderId.ToString(), input);
await client.RaiseEventAsync(orderId.ToString(), "PaymentApproved", true);   // resume the waiting workflow
var state = await client.GetWorkflowStateAsync(orderId.ToString());
```

## Orchestrator Rules

| Allowed in orchestrator | Move to an activity |
|-------------------------|---------------------|
| `CallActivityAsync`, `CreateTimer`, `WaitForExternalEventAsync` | DB / HTTP / file I/O |
| Pure logic on inputs/results | `DateTime.Now`, `Random`, `Guid.NewGuid()` |
| `CallChildWorkflowAsync` | Sending messages / calling other services |

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| I/O or `HttpClient` inside the orchestrator | Wrap it in a `WorkflowActivity` |
| `Task.Delay` for waits | Use `ctx.CreateTimer` (durable) |
| `DateTime.Now` / `Guid.NewGuid()` in orchestrator | Pass values in as input or compute in an activity |
| Polling a DB for a signal | `WaitForExternalEventAsync` + `RaiseEventAsync` |

## Adding to an Existing Project

1. Add `Dapr.Workflow`; call `AddDaprWorkflow(...)` and register workflows + activities.
2. Model the orchestrator as deterministic scheduling only; push I/O into activities.
3. Use `CreateTimer` / `WaitForExternalEventAsync` for delays and external signals.
4. Start instances with `ScheduleNewWorkflowAsync`; resume with `RaiseEventAsync`.
5. Run under the sidecar (workflow uses the actor state store).

## References

- https://docs.dapr.io/developing-applications/building-blocks/workflow/
