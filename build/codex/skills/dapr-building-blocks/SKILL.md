---
name: dapr-building-blocks
description: "Configures DaprClient for state management, secrets, and service invocation, backed by component YAML. Use when reading/writing keyed state, calling another service through the Dapr sidecar, or wiring a state-store/secret-store component. Do NOT use for topic/subscription detail (use dapr-pubsub) or durable orchestration (use dapr-workflow)."
---
# Dapr Building Blocks (State + Service Invocation)

Dapr (MIT, CNCF) exposes capabilities as **building blocks** over a sidecar, so your code talks to `DaprClient`/HTTP and never to a concrete broker or store. This skill covers **state management** and **service invocation**; pub-sub and workflow are separate skills.

## Core Principles

- One **component YAML** per backing resource (state store, secret store); the app references it by `metadata.name`, not by connection string.
- State is **keyed** and optionally namespaced per app-id; use ETags for optimistic concurrency.
- Service invocation targets a logical **app-id** — Dapr handles discovery, mTLS, and retries.
- Inject `DaprClient` from DI (`AddDaprClient()`); always pass the `CancellationToken`.

## State + Service Invocation

```csharp
namespace {Company}.{Domain}.Service;

public sealed class CartService(DaprClient dapr)
{
    private const string StoreName = "statestore";   // == component metadata.name

    public Task SaveAsync(string cartId, Cart cart, CancellationToken ct) =>
        dapr.SaveStateAsync(StoreName, cartId, cart, cancellationToken: ct);

    public Task<Cart?> GetAsync(string cartId, CancellationToken ct) =>
        dapr.GetStateAsync<Cart?>(StoreName, cartId, cancellationToken: ct);

    // Optimistic concurrency: read value + ETag, write only if unchanged.
    public async Task<bool> TryAddItemAsync(string cartId, CartItem item, CancellationToken ct)
    {
        var (cart, etag) = await dapr.GetStateAndETagAsync<Cart>(StoreName, cartId, cancellationToken: ct);
        cart ??= new Cart(cartId);
        cart.Items.Add(item);
        return await dapr.TrySaveStateAsync(StoreName, cartId, cart, etag, cancellationToken: ct);
    }

    // Service invocation: call the "pricing" app-id's GET /quotes/{id} endpoint.
    public Task<Quote> GetQuoteAsync(string cartId, CancellationToken ct) =>
        dapr.InvokeMethodAsync<Quote>(HttpMethod.Get, "pricing", $"quotes/{cartId}", ct);
}

// Program.cs
builder.Services.AddDaprClient();
```

## Component YAML (state store)

```yaml
# components/statestore.yaml  — metadata.name is the StoreName above
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
spec:
  type: state.redis
  version: v1
  metadata:
    - name: redisHost
      value: localhost:6379
    - name: keyPrefix          # scope keys per app-id
      value: appid
```

## Building Block Cheat-Sheet

| Block | DaprClient call | Component `type` |
|-------|-----------------|------------------|
| State | `SaveStateAsync` / `GetStateAsync` | `state.*` (redis, cosmosdb…) |
| State (concurrency) | `GetStateAndETagAsync` + `TrySaveStateAsync` | same |
| Secrets | `GetSecretAsync` | `secretstores.*` |
| Service invocation | `InvokeMethodAsync` | (no component — app-id based) |

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Connection string in app config | Put it in component YAML; reference by name |
| Blind overwrite of shared state | Use ETag (`GetStateAndETagAsync` + `TrySaveStateAsync`) |
| `HttpClient` to a hardcoded service URL | `InvokeMethodAsync` against the app-id |
| New `DaprClient()` per call | Inject the DI-registered singleton |

## Adding to an Existing Project

1. Add `Dapr.Client`; call `AddDaprClient()`.
2. Drop a component YAML per store/secret resource into `components/`.
3. Wrap state access in a service using the component `metadata.name`.
4. Replace direct service-to-service HTTP with `InvokeMethodAsync(app-id, …)`.
5. Run under the sidecar: `dapr run --app-id <id> --resources-path ./components -- dotnet run`.

## References

- https://docs.dapr.io/developing-applications/building-blocks/
