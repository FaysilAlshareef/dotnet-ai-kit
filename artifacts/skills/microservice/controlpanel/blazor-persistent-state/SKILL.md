---
name: blazor-persistent-state
description: "Persists component state across prerender→interactive handoff and Interactive Server circuit reconnects using the .NET 10 [PersistentState] attribute (and PersistentComponentState). Use when a value fetched during prerender must survive into the interactive render, or must outlive a dropped SignalR circuit. Do NOT use for choosing where a component runs (use blazor-render-modes) or for general data-grid/dialog UI (use blazor-component)."
metadata:
  category: "microservice/controlpanel"
  agent: "controlpanel-architect"
---
# Blazor Persistent State ([PersistentState], .NET 10)

## Core Principles

- Two distinct problems: (1) the **prerender→interactive** double-fetch, and (2) **circuit reconnect** state loss. `[PersistentState]` addresses (1); circuit handling addresses (2).
- `.NET 10` `[PersistentState]` declaratively persists a property: its value is serialized into the prerendered page and rehydrated on the interactive render, so `OnInitializedAsync` does NOT have to re-fetch.
- The property type must be JSON-serializable; the framework persists it automatically — no manual `PersistentComponentState.RegisterOnPersisting` callback needed for the common case.
- For Interactive Server, configure circuit retention so a brief network drop reconnects to the **same** circuit (state intact) instead of starting fresh.
- Never persist secrets or large blobs — the payload is embedded in the page (prerender) or held in server memory (circuit).

## Example

```razor
@page "/orders/{Id:guid}"
@rendermode InteractiveServer
@inject OrdersGateway Gateway

@if (Order is null) { <MudProgressCircular Indeterminate /> }
else { <MudText>@Order.CustomerName</MudText> }

@code {
    [Parameter] public Guid Id { get; set; }

    // Value captured at prerender is restored here on the interactive render —
    // the guard below then skips the second fetch.
    [PersistentState]
    public OrderResponse? Order { get; set; }

    protected override async Task OnInitializedAsync()
    {
        if (Order is not null)
            return; // restored from persisted state; no refetch.

        var result = await Gateway.GetAsync(Id);
        result.Switch(
            onSuccess: o => Order = o,
            onFailure: _ => Order = null);
    }
}
```

```csharp
// Program.cs — keep a reconnecting circuit's state alive briefly.
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents(o =>
    {
        o.DisconnectedCircuitRetentionPeriod = TimeSpan.FromMinutes(3);
        o.DisconnectedCircuitMaxRetained = 100;
    });
```

## Gotchas

- `[PersistentState]` survives the *initial* prerender handoff, not arbitrary navigations — it is not a replacement for a cache or app state container.
- Server circuit memory is bounded by `DisconnectedCircuitMaxRetained`; under load, retained circuits are evicted and reconnects start fresh — design for graceful re-init.
- For `InteractiveAuto`/WASM, persisted state crosses the server→client boundary, so the persisted type must be serializable on both sides (no server-only types).
- Don't persist `DbContext`-bound entities; project to a DTO first or the serializer will pull in tracking/lazy-loaded graphs.

## References

- https://learn.microsoft.com/en-us/aspnet/core/blazor/components/prerender
- https://learn.microsoft.com/en-us/aspnet/core/blazor/fundamentals/signalr#circuit-handler-options
